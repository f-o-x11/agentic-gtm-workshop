"""Focused offline checks. Temporary examples are never production acceptance."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta, timezone
from email import policy as email_policy
from email.parser import BytesParser
import hashlib, json, tempfile, unittest, os
from engine import checks, scheduler
from unittest.mock import patch
from tools.setup import approve_release
from engine.assets import Assets
from engine.http_client import Response, ProviderError
prepare=scheduler.prepare
from engine import validation as copywriting
from engine import validation as identity
from engine.database import Store, digest, encode, now
class OfflineFixture:
    def __init__(self, folder):
        self.folder, self.path = Path(folder), Path(folder) / 'offline.sqlite'; self.store = Store(self.path)
        self.authority = {'authority': 'Offline example only', 'senders': {'owner@example.org': 2}, 'timezone': 'America/New_York', 'recipient_company_countries': ['United States'], 'account_cooldown_days': 30}
        self.person = {'email': 'buyer@prospect.example', 'domain': 'prospect.example', 'profile': 'https://www.linkedin.com/in/offline-example', 'name': 'Offline Buyer', 'title': 'VP Marketing'}; self.payload = {'subject': 'Your advertising workflow', 'body': 'Could I send the details?\n\nOwner\nowner@example.org'}
        stamp = now(); proof = {'status': 'confirmed_current', 'outreach_ready': True, 'domain': self.person['domain'], 'profile_url': self.person['profile'], 'title': self.person['title'], 'profile_name': self.person['name'], 'profile_fetched_at': stamp, 'provider': 'offline-example'}
        raw = {**self.person, 'identity': proof, 'zb_status': 'valid', 'zb_checked_at': stamp}; s = self.store
        s.db.execute('INSERT INTO accounts VALUES (?,?,?,?,?,?,?)', ('prospect.example', 'Offline Company', 'ready', 'B2B', 'offline', stamp, encode({'country': 'United States'})))
        s.db.execute('INSERT INTO people VALUES (?,?,?,?,?,?,?,?,?,?)', ('offline:buyer', self.person['email'], self.person['profile'], self.person['domain'], self.person['name'], self.person['title'], 'active', 'offline', stamp, encode(raw)))
        s.db.execute('INSERT INTO sender_consent VALUES (?,?,?,?,?)', ('owner@example.org', 2, 1, 'offline', '{}')); s.set('policy', self.authority)
        for field in ('migration_complete', 'execution_enabled', 'commits_enabled'):
            s.set(field, True)
        s.set('migration_receipt', {'sources': {'offline': {'records': 1}}}); self.folder.joinpath('policy.json').write_text(encode({'migration_complete': True, 'execution_enabled': True, 'commits_enabled': True, 'offline_fixture': True}))
        coverage = {}
        for name, max_age in checks.SAFETY.items():
            row = {'coverage': name, 'complete': True, 'observed_at': stamp, 'canonical_current': max_age is None, 'offline_fixture': True}
            s.record('offline.coverage', name, 'safety_coverage', row)
            coverage[name] = {**row, 'source': 'offline.coverage', 'record_key': name, 'digest': digest(row)}
        s.set('safety_refresh', {'complete': True, 'sources': coverage}); self.manifest('offline.coverage')
        s.db.commit(); s.lease('offline-owner')
    def manifest(self, source):
        keys, values = hashlib.sha256(), hashlib.sha256(); rows = self.store.rows('SELECT record_key,digest FROM source_records WHERE source=? ORDER BY record_key', (source,))
        for row in rows:
            keys.update((row['record_key'] + '\n').encode())
            values.update((row['record_key'] + '\0' + row['digest'] + '\n').encode())
        self.store.db.execute('INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?)', (source, len(rows), keys.hexdigest(), values.hexdigest(), now()))
    def action(self):
        return checks.make_action('email', self.person, dict(self.payload), 'owner@example.org')
    def reserve(self, action):
        return self.store.reserve(action['channel'], action['recipient'], action['domain'], action['sender'], action['payload'], action['action_key'])
    def close(self):
        self.store.close()
class FocusedChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='v5-offline-'); self.f = OfflineFixture(self.temp.name)
    def tearDown(self):
        self.f.close(); self.temp.cleanup()
    def test_source_hash_tampering_is_detected_explicitly(self):
        s = self.f.store; self.assertEqual(checks.source_integrity(s), [])
        s.db.execute("UPDATE source_records SET data_json='{}' WHERE record_key='history'"); self.assertIn('Canonical source hash or count differs: offline.coverage.', checks.source_integrity(s))
        self.assertTrue(any('source receipt' in issue for issue in checks.validate(s, self.f.action())))
    def test_first_reserved_request_can_pass_but_duplicate_cannot(self):
        s, action = self.f.store, self.f.action(); checks.require_commit(s, action)
        self.f.reserve(action)
        with self.assertRaisesRegex(ValueError, 'Existing channel attempt'):
            checks.require_commit(s, action)
        checks.require_commit(s, action, allow_reserved=True); changed = {**action, 'payload': {**action['payload'], 'body': 'Changed copy'}}
        changed['action_key'] = checks.action_hash(changed)
        with self.assertRaises(ValueError):
            checks.require_commit(s, changed, allow_reserved=True)
        s.result(action['action_key'], 'uncertain')
        with self.assertRaisesRegex(ValueError, 'Existing channel attempt'):
            checks.require_commit(s, action, allow_reserved=True)
    def test_provider_success_then_local_crash_never_authorizes_retry(self):
        action = self.f.action(); accepted = []
        def intercepted_dispatch():
            checks.require_commit(self.f.store, action)
            self.f.reserve(action)
            checks.require_commit(self.f.store, action, allow_reserved=True)
            accepted.append('offline-provider-id')
            raise RuntimeError('Local crash after provider acceptance, before saving result')
        with self.assertRaisesRegex(RuntimeError, 'Local crash'):
            intercepted_dispatch()
        self.assertEqual(len(accepted), 1); self.f.store.close()
        self.f.store = Store(self.f.path); self.f.store.lease('offline-owner')
        with self.assertRaisesRegex(ValueError, 'Existing channel attempt'):
            checks.require_commit(self.f.store, action, allow_reserved=True)
        with self.assertRaisesRegex(ValueError, 'Existing attempt'):
            self.f.reserve(action)
        with self.assertRaisesRegex(ValueError, 'Existing channel attempt'):
            intercepted_dispatch()
        self.assertEqual(len(accepted), 1); self.assertEqual(self.f.store.one('SELECT status FROM attempts')['status'], 'attempting')
    def test_execution_lease_belongs_to_exact_store_owner(self):
        other = Store(self.f.path)
        try:
            with self.assertRaisesRegex(ValueError, 'Another process'):
                other.lease('other-owner')
            with self.assertRaisesRegex(ValueError, 'single-owner'):
                checks.require_commit(other, self.f.action())
            checks.require_commit(self.f.store, self.f.action())
        finally:
            other.close()
    def test_retries_add_no_files_and_preserve_one_attempt(self):
        action = self.f.action(); self.f.reserve(action)
        before = {p.name for p in self.f.folder.rglob('*') if p.is_file()}
        for _ in range(100):
            with self.assertRaises(ValueError):
                self.f.reserve(action)
        after = {p.name for p in self.f.folder.rglob('*') if p.is_file()}; self.assertEqual(after, before)
        self.assertLessEqual(len(after), 50); self.assertEqual(self.f.store.one('SELECT count(*) AS n FROM attempts')['n'], 1)
    def test_current_evidence_consent_and_exclusions_are_required(self):
        s, action = self.f.store, self.f.action(); self.assertEqual(checks.validate(s, action), [])
        s.set('migration_complete', False); self.assertEqual(checks.validate(s, action), [])
        s.set('migration_complete', True); original = s.setting('safety_refresh')
        refresh = json.loads(encode(original)); refresh['sources']['history']['observed_at'] = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
        s.set('safety_refresh', refresh); self.assertTrue(any('history coverage' in v for v in checks.validate(s, action)))
        s.set('safety_refresh', original); local = json.loads(s.policy_path.read_text())
        local['execution_enabled'] = False; s.policy_path.write_text(encode(local))
        with self.assertRaisesRegex(ValueError, 'Outreach is paused'):
            checks.require_commit(s, action)
        local['execution_enabled'] = True; s.policy_path.write_text(encode(local))
        raw = identity.load(s.one('SELECT data_json FROM people')['data_json']); raw['identity']['domain'] = 'different.example'
        s.db.execute('UPDATE people SET data_json=?', (encode(raw),)); self.assertTrue(any('evidence differs' in v for v in checks.validate(s, action)))
        raw['identity']['domain'] = self.f.person['domain']; s.db.execute('UPDATE people SET data_json=?', (encode(raw),))
        s.record('postgres.sender_consent', 'owner@example.org', 'sender_consent', {'email': 'owner@example.org', 'state': 'revoked', 'revoked_at': now()}); self.assertTrue(any('revoked' in v for v in checks.validate(s, action)))
        s.db.execute("DELETE FROM source_records WHERE source='postgres.sender_consent'")
        # The current policy is stricter than the earlier normalized consent row.
        authority = s.setting('policy'); authority['senders']['owner@example.org'] = 1
        s.set('policy', authority); s.db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)', ('other-send', 'email', 'other@different.example', 'different.example', 'owner@example.org', 'sent', 'offline-id', now(), '{}', '{}'))
        self.assertFalse(any('daily cap is exhausted' in v for v in checks.validate(s, action))); self.assertFalse(any('daily cap is exhausted' in v for v in checks.validate(s, action, committing=True)))
        s.db.execute("DELETE FROM attempts WHERE idem_key='other-send'"); authority['senders']['owner@example.org'] = 2
        s.set('policy', authority); s.record('postgres.outbox', 'queued', 'outbox', {'domain': action['domain'], 'email': action['recipient'], 'status': 'scheduled', 'sent_at': None})
        self.assertTrue(any('queued or sent' in v for v in checks.validate(s, action))); s.db.execute("DELETE FROM source_records WHERE source='postgres.outbox'")
        s.db.execute('INSERT INTO history VALUES (?,?,?,?,?,?)', ('native-email-row', action['recipient'], action['domain'], now(), 'email_rows', encode({'status': 'sent'}))); self.assertTrue(any('email already exists' in v.lower() for v in checks.validate(s, action)))
        s.db.execute('DELETE FROM history'); account = s.one('SELECT * FROM accounts')
        account['data_json'] = encode({'country': 'United States', 'source_aliases': { 'postgres': [{'domain': 'www.prospect.example', 'state': 'held'}]}}); self.assertEqual(identity.account_issues(account, self.f.authority), [])
        s.db.execute('INSERT INTO resources VALUES (?,?,?,?,?,?)', ('job', 'uncertain_paid_request', 'apify', None, None, encode({'domain': action['domain'], 'state': 'started'}))); self.assertFalse(any('paid lookup' in v for v in checks.validate(s, action)))
    def test_action_hash_binds_exact_copy_sender_and_time(self):
        action = self.f.action()
        for field, value in (('sender', 'other@example.org'), ('at', '2020-01-01T00:00:00+00:00'), ('payload', {'subject': 'Changed', 'body': 'Changed'})):
            changed = {**action, field: value}
            self.assertTrue(any('action hash' in v for v in checks.validate(self.f.store, changed)))
    def test_mime_copy_is_exact_and_first_email_has_no_links(self):
        plain = 'Could I send details?\n\nOwner\nowner@example.org'; self.assertEqual(copywriting.validate({'subject': 'Workflow', 'body': plain}, initial_email=True), [])
        raw = copywriting.format_email('owner@example.org', 'buyer@prospect.example', 'Workflow', plain); message = BytesParser(policy=email_policy.default).parsebytes(raw)
        parts = list(message.iter_parts()); self.assertEqual([p.get_content_type() for p in parts], ['text/plain', 'text/html'])
        self.assertEqual(parts[0].get_content().replace('\r\n', '\n').strip(), plain); self.assertEqual(copywriting.validate({'body': plain, 'html': parts[1].get_content()}, initial_email=True), [])
        for body in ('Visit https://example.org', 'We leverage your work.', 'Hello\u2014there'):
            self.assertTrue(copywriting.validate({'body': body}, initial_email=True))
        self.assertTrue(copywriting.validate({'body': plain, 'html': '<p>Different</p>'}))
    def test_quota_dates_require_bound_sources_and_claims_precede_inbound(self):
        from engine.scheduler import attempt_clock
        s = self.f.store; key, stamp = 'quota-example', '2026-10-04T12:00:00Z'
        original = {'idem_key': key, 'direction': 'inbound', 'event_type': 'reply_received'}
        with s.db:
            s.record('postgres.touch_ledger', key, 'touch_ledger', original)
        row = {'idem_key': key, 'at': stamp, 'payload_json': encode(original), 'receipt_json': '{}', 'provider_id': 'gift-example'}; self.assertEqual(attempt_clock(row, store=s)[1], 'inbound_event')
        self.assertEqual(attempt_clock(row, {'at': stamp}, s), (stamp, 'v5_hourly_claim'))
        with s.db:
            s.db.execute('INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?)', (key, 'email', 'buyer@prospect.example', 'prospect.example', 'owner@example.org', 'ready', '{}', stamp, ''))
        self.assertEqual(attempt_clock(row, store=s), (stamp, 'v5_durable_reservation'))
        with s.db:
            s.db.execute('DELETE FROM actions WHERE action_key=?', (key,))
            original.update(direction='outbound', observed_at=stamp)
            s.record('postgres.touch_ledger', key, 'touch_ledger', original)
        self.assertEqual(attempt_clock(row, store=s), (None, 'undated_commitment_hold')); gift = {'gift_id': 'gift-example', 'delivered_at': stamp}
        proof = {'source': 'postgres.gifts', 'record_key': 'gift-example', 'digest': digest(gift), 'field': 'delivered_at', 'at': stamp}
        with s.db:
            s.record('postgres.gifts', 'gift-example', 'gifts', gift)
        row['receipt_json'] = encode({'quota_clock': proof}); self.assertEqual(attempt_clock(row, store=s), (stamp, 'exact_provider_commitment'))
        proof['digest'] = 'unsupported'; row['receipt_json'] = encode({'quota_clock': proof})
        self.assertEqual(attempt_clock(row, store=s), (None, 'undated_commitment_hold'))
    def test_invitation_cannot_release_an_unreserved_automatic_message(self):
        from engine.channels import social
        s = self.f.store
        with s.db:
            s.set('execution_enabled', True)
            s.set('commits_enabled', True)
            s.set('social_owned', {'Owner': {'steps': [{'type': 'invitation'}, {'type': 'message'}]}})
        with patch.object(social, '_owned'), patch.object(social, 'Social') as provider:
            with self.assertRaisesRegex(ValueError, 'unreserved message'):
                social.send(s, {}, {'sender': 'Owner', 'channel': 'linkedin'}, 'example')
            provider.return_value._tool.assert_not_called()
    def test_fresh_email_evidence_is_bound_to_the_exact_person_and_digest(self):
        s = self.f.store; person = s.one('SELECT * FROM people WHERE person_key=?', ('offline:buyer',))
        raw = json.loads(person['data_json']); raw.pop('zb_status')
        raw.pop('zb_checked_at'); person['data_json'] = encode(raw)
        evidence = {'email': person['email'], 'domain': person['domain'], 'linkedin_url': person['profile'], 'zb_status': 'valid', 'zb_checked_at': now(), 'email_ok': True}
        with s.db:
            s.record('postgres.contacts', person['email'], 'contacts', evidence)
        issues = identity.person_issues(s, person, person['domain']); self.assertFalse(any('deliverability' in issue for issue in issues))
        with s.db:
            s.db.execute("UPDATE source_records SET digest='unsupported' WHERE source='postgres.contacts'")
        issues = identity.person_issues(s, person, person['domain']); self.assertTrue(any('deliverability' in issue for issue in issues))
    def test_old_draft_needs_current_sources_not_a_fifteen_minute_rebuild(self):
        action = self.f.action(); action['at'] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        action['action_key'] = checks.action_hash(action)
        refresh = self.f.store.setting('safety_refresh'); refresh.pop('complete')
        self.f.store.set('safety_refresh', refresh); self.assertEqual(checks.validate(self.f.store, action), [])
        refresh['sources']['history']['observed_at'] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(); self.f.store.set('safety_refresh', refresh)
        self.assertTrue(any('history coverage' in value for value in checks.validate(self.f.store, action)))
    def test_repaired_hold_sends_once_and_unsafe_claim_cannot_resume_tomorrow(self):
        s = self.f.store
        authority = s.setting('policy'); authority['senders']['owner@example.org'] = 30
        s.set('policy', authority); s.db.execute('UPDATE sender_consent SET daily_cap=30')
        s.set('hourly_pacing', {'enforced': True, 'daily_targets': {'email': 30}})
        action = self.f.action(); action['at'] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        action['action_key'] = checks.action_hash(action); s.db.execute('INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?)', (action['action_key'], 'email', action['recipient'], action['domain'], action['sender'], 'held', encode(action['payload']), action['at'], 'Old construction hold'))
        s.db.commit(); s.release('offline-owner')
        def intercepted(store, row):
            exact = checks.unpack(row); checks.require_commit(store, exact)
            store.reserve('email', exact['recipient'], exact['domain'], exact['sender'], exact['payload'], exact['action_key'])
            checks.require_commit(store, exact, allow_reserved=True)
            store.result(exact['action_key'], 'submitted', 'offline-provider-id')
            return {'offline_provider': True}
        with patch.object(scheduler, 'dispatch', side_effect=intercepted) as provider:
            self.assertEqual(scheduler.cycle(s, force=True)['provider_commitments'], 1)
            self.assertEqual(scheduler.cycle(s, force=True)['provider_commitments'], 0)
            self.assertEqual(provider.call_count, 1)
        self.assertEqual(s.one('SELECT count(*) AS n FROM attempts')['n'], 1)
        fresh = self.f.action(); fresh['payload']['subject'] = 'A different new draft'; fresh['action_key'] = checks.action_hash(fresh)
        s.set('hourly_pacing:2020-01-01', {'claims': {fresh['action_key']: {'status': 'uncertain', 'owner': 'crashed-owner'}}}); self.assertTrue(any('earlier release' in value for value in checks.validate(s, fresh)))
    def test_one_owner_switch_and_account_scope_are_enforced(self):
        s, action = self.f.store, self.f.action()
        s.set('execution_enabled', False); s.set('commits_enabled', False)
        self.assertEqual(checks.execution_issues(s), [])
        refresh = s.setting('safety_refresh'); value = identity.load(s.one("SELECT data_json FROM source_records WHERE record_key='history'")['data_json'])
        value['domain_scope'] = ['other.example']; s.record('offline.coverage', 'history', 'safety_coverage', value)
        refresh['sources']['history']['digest'] = digest(value); s.set('safety_refresh', refresh)
        self.assertTrue(any('do not cover this account' in issue for issue in checks.validate(s, action)))
    def test_gmail_changed_message_id_uses_exact_accepted_id_and_content(self):
        import base64
        from engine.channels import email
        s, action = self.f.store, self.f.action(); self.f.reserve(action)
        s.event('gmail_transport', action['action_key'], {'transport': 'v5.gmail'}); s.result(action['action_key'], 'accepted', 'offline-gmail-id', {'http_status': 200, 'body': {'id': 'offline-gmail-id'}})
        message = email.mime(action['payload'], action['recipient'], action['sender'], action['action_key'])
        message.replace_header('Message-ID', '<gmail-generated@example.org>'); del message['X-GTM-Action-Key']
        native = {'id': 'offline-gmail-id', 'labelIds': ['SENT'], 'internalDate': int(datetime.now(timezone.utc).timestamp()*1000), 'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        with patch.object(email, 'Mailbox') as mailbox:
            mailbox.return_value.query.return_value = [{'id': native['id']}]
            mailbox.return_value.message.return_value = native
            self.assertEqual(email.reconcile(s, action['action_key'])['status'], 'sent')
            message.replace_header('To', 'wrong@elsewhere.example')
            native['raw'] = base64.urlsafe_b64encode(message.as_bytes()).decode()
            self.assertEqual(email.reconcile(s, action['action_key'])['status'], 'uncertain')
            s.db.execute("UPDATE events SET source_digest='tampered' WHERE kind='attempt_accepted'")
            message.replace_header('To', action['recipient']); native['raw'] = base64.urlsafe_b64encode(message.as_bytes()).decode()
            self.assertEqual(email.reconcile(s, action['action_key'])['status'], 'uncertain')
    def test_failed_provider_read_before_reservation_can_retry_safely(self):
        from engine.http_client import ProviderError
        s = self.f.store
        authority = s.setting('policy'); authority['senders']['owner@example.org'] = 30
        s.set('policy', authority); s.db.execute('UPDATE sender_consent SET daily_cap=30')
        s.set('hourly_pacing', {'enforced': True, 'daily_targets': {'email': 30}}); action = scheduler.prepare(s, 'email', self.f.person, self.f.payload, 'owner@example.org')
        s.release('offline-owner')
        with patch.object(scheduler, 'dispatch', side_effect=ProviderError('Read-only inventory HTTP503')):
            self.assertEqual(scheduler.cycle(s, force=True)['provider_commitments'], 0)
        self.assertEqual(s.one('SELECT count(*) AS n FROM attempts')['n'], 0); plan = s.setting(scheduler._plan_name(scheduler._clock()))
        self.assertEqual(plan['claims'][action['action_key']]['status'], 'not_committed')
        def intercepted(store, row):
            exact = checks.unpack(row); checks.require_commit(store, exact)
            store.reserve('email', exact['recipient'], exact['domain'], exact['sender'], exact['payload'], exact['action_key'])
            store.result(exact['action_key'], 'sent', 'offline-provider-id')
            return {'offline_provider': True}
        with patch.object(scheduler, 'dispatch', side_effect=intercepted):
            self.assertEqual(scheduler.cycle(s, force=True)['provider_commitments'], 1)
    def test_paid_research_does_not_block_outreach(self):
        s, action = self.f.store, self.f.action(); s.db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)', ('offline-check', 'research:zerobounce', action['recipient'], action['domain'], '', 'complete', None, now(), '{}', '{}'))
        self.assertEqual(checks.validate(s, action), []); s.db.execute('INSERT INTO resources VALUES (?,?,?,?,?,?)', ('unknown-lookup', 'uncertain_paid_request', 'offline-example', None, None, encode({'email': action['recipient'], 'domain': action['domain']})))
        self.assertFalse(any('paid lookup' in issue for issue in checks.validate(s, action)))
class PortableChecks(unittest.TestCase):
    setUp=FocusedChecks.setUp
    tearDown=FocusedChecks.tearDown
    def test_init_and_private_config_never_import_production_records(self):
        from tools.setup import init
        empty=Store(self.f.folder/'new.sqlite'); config=self.f.folder/'private-config.json'
        config.write_text(encode({'company':{'name':'Actual Owner Company','website':'https://owner.example'},'policy':self.f.authority})); config.chmod(0o600)
        workspace=self.f.folder/'company-motion'; workspace.mkdir(); (workspace/'COMPANY.md').write_text('Actual offline company brief')
        try:
            with patch('tools.setup.ROOT',self.f.folder/'code'): self.assertTrue(init(empty,config)['initialized'])
            self.assertEqual(empty.one('SELECT count(*) AS n FROM people')['n'],0)
            self.assertEqual(checks.execution_issues(empty),['Outreach is paused in config/policy.json.'])
            with patch('tools.setup.ROOT',self.f.folder/'code'): self.assertTrue(init(empty,config)['existing_project_retained'])
        finally: empty.close()
    def test_snapshot_actual_hash_and_expiry_bind_exclusions(self):
        from tools.setup import snapshot
        path=self.f.folder/'exclusions.json'; value={'complete':True,'observed_at':now(),'source':'Owner reviewed actual export', 'coverage':['customers','open_deals','suppressions'],'records':[{'entity_type':'domain','value':'prospect.example','reason':'Customer'}]}
        path.write_text(encode(value)); result=snapshot(self.f.store,path)
        self.assertEqual(result['source_sha256'],hashlib.sha256(path.read_bytes()).hexdigest()); self.assertTrue(any('suppression' in s for s in checks.validate(self.f.store,self.f.action())))
        value['observed_at']=(datetime.now(timezone.utc)-timedelta(minutes=66)).isoformat(); path.write_text(encode(value))
        with self.assertRaisesRegex(ValueError,'65 minutes'): snapshot(self.f.store,path)
    def test_google_oauth_refresh_checks_mailbox_and_scope_without_send(self):
        from engine.channels.email import delegated_token
        key=self.f.folder/'oauth.json'; key.write_text(encode({'type':'authorized_user','email':'owner@example.org', 'client_id':'offline-client','client_secret':'offline-secret','refresh_token':'offline-refresh','scopes':['gmail.test']}))
        key.chmod(0o600); self.f.store.set('credential_files',{'google':str(key)})
        class HTTP:
            store=self.f.store
            def credential_file(self,p): return key
            def request(self,*args,**kwargs): return Response(200,{'access_token':'offline-token'},b'{}',{})
        self.assertEqual(delegated_token(HTTP(),'owner@example.org','gmail.test'),'offline-token')
        with self.assertRaisesRegex(ProviderError,'mailbox differs'):
            delegated_token(HTTP(),'different@example.org','gmail.test')
    def test_portable_manual_batch_keeps_hard_daily_cap(self):
        s=self.f.store; s.set('portable_attendee',True); s.set('batch_limits',{'email':10})
        authority=s.setting('policy'); authority['senders']['owner@example.org']=1; s.set('policy',authority)
        s.db.execute('UPDATE sender_consent SET daily_cap=1'); s.set('hourly_pacing',{'enforced':True,'daily_targets':{'email':1}})
        action=scheduler.prepare(s,'email',self.f.person,self.f.payload,'owner@example.org')
        approval=self.f.folder/'scope.json'; approval.write_text(encode({'authority':'Offline exact release','purpose':'cap test','action_keys':[action['action_key']],'limits':{'email':1,'gift':0,'social':0}}))
        approve_release(s,approval); s.release('offline-owner')
        def provider(store,row):
            exact=checks.unpack(row); checks.require_commit(store,exact)
            store.reserve('email',exact['recipient'],exact['domain'],exact['sender'],exact['payload'],exact['action_key'])
            store.result(exact['action_key'],'sent','offline-id'); return {'status':'sent'}
        with patch.object(scheduler,'dispatch',side_effect=provider) as native:
            self.assertEqual(scheduler.cycle(s,force=True,limit=10)['provider_commitments'],1)
            self.assertEqual(scheduler.cycle(s,force=True,limit=10)['provider_commitments'],0); self.assertEqual(native.call_count,1)
    def test_controlled_test_cannot_adopt_a_prospect(self):
        action=self.f.action(); action['payload']['controlled_test']=True; action['action_key']=checks.action_hash(action)
        self.assertTrue(any('Controlled test' in i for i in checks.validate(self.f.store,action)))
    def test_owned_page_upload_is_once_and_readback_is_exact(self):
        s=self.f.store; s.set('netlify_site_id','offline-site'); html=self.f.folder/'page.html'; html.write_text('<html>Actual owner page</html>')
        s.db.commit()
        sha=hashlib.sha256(html.read_bytes()).hexdigest(); calls=[]
        class HTTP:
            def credential(self,p): return 'offline-token'
            def request(self,method,url,**kwargs):
                calls.append((method,url)); data={'id':'offline-owner'} if url.endswith('/user') else {'id':'offline-site','user_id':'offline-owner'} if url.endswith('/sites/offline-site') else {'id':'offline-deploy','site_id':'offline-site','state':'ready','deploy_ssl_url':'https://offline.netlify.app'}
                raw=html.read_bytes() if url=='https://offline.netlify.app' else encode(data).encode()
                return Response(200,data,raw,{})
        client=Assets(s,HTTP()); sha=client.publish_file(html,review=True)['approval_sha256']
        self.assertTrue(client.publish_file(html,sha)['published']); client.publish_file(html,sha)
        from engine.database import set_execution
        set_execution(s,False); self.assertTrue(client.publish_file(html,sha)['published'])
        self.assertEqual(sum(method=='POST' for method,url in calls),1)
        with self.assertRaisesRegex(ValueError,'Approve this exact'): client.publish_file(html,'wrong')
    def test_native_reads_replace_snapshot_and_failed_reads_hold(self):
        from tools.setup import refresh_portable
        s=self.f.store; s.set('exclusion_mode','native'); s.set('native_exclusions',['revenue','hubspot']); s.set('revenue',{'range':'Customers!A:C'})
        prepare(s,'email',self.f.person,self.f.payload,'owner@example.org')
        with patch('engine.channels.meetings.Meetings') as native,patch('engine.channels.email.Replies') as history,patch('tools.setup.snapshot') as snapshot:
            good={'complete':True,'complete_inventory':True,'observed_at':now(),'unresolved_domain_ids':[],'unresolved_domain_rows':[]}
            native.return_value.customers.return_value=good; native.return_value.hubspot_deals.return_value=good
            native.return_value.refresh.return_value=good; history.return_value.refresh.return_value=good
            self.assertEqual(set(refresh_portable(s)['refreshed']),set(checks.SAFETY)); snapshot.assert_not_called()
            native.return_value.customers.return_value={**good,'complete_inventory':False}
            self.assertNotIn('customers',refresh_portable(s)['refreshed']); snapshot.assert_not_called()
    def pilot(self):
        s=self.f.store; s.set('portable_attendee',True); s.set('internal_domains',['example.org'])
        a=s.setting('policy'); a['controlled_test_recipients']=['owner@example.org']; a['senders']['owner@example.org']=11; s.set('policy',a)
        s.db.execute('UPDATE sender_consent SET daily_cap=11'); s.set('batch_limits',{'email':10}); s.set('hourly_pacing',{'enforced':True,'daily_targets':{'email':11}})
        actions=[]
        for i in range(11):
            d='example.org' if i==0 else 'prospect'+str(i)+'.example'; recipient='owner@example.org' if i==0 else 'buyer@'+d
            raw=json.loads(s.one('SELECT data_json FROM people LIMIT 1')['data_json']); raw.update(email=recipient,domain=d,controlled_test=i==0)
            raw['identity']['domain']=d; raw['identity']['profile_url']=raw['profile']
            s.db.execute('INSERT OR REPLACE INTO accounts VALUES (?,?,?,?,?,?,?)',(d,d,'ready','B2B','offline',now(),encode({'country':'United States'})))
            s.db.execute('INSERT OR REPLACE INTO people VALUES (?,?,?,?,?,?,?,?,?,?)',('person:'+recipient,recipient,raw['profile'],d,raw['name'],raw['title'],'active','offline',now(),encode(raw)))
            payload={**self.f.payload,'sender':'owner@example.org','controlled_test':i==0}
            actions.append(prepare(s,'email',raw,payload,'owner@example.org'))
        approval=self.f.folder/'pilot.json'; approval.write_text(encode({'authority':'Offline owner exact recipients and copy','controlled_action_key':actions[0]['action_key'],'prospect_action_keys':[a['action_key'] for a in actions[1:]]}))
        approve_release(s,approval,True); s.db.commit(); return actions,approval
    def test_portable_result_excludes_canary_and_requires_exact_sent(self):
        from tools.setup import results
        actions,_=self.pilot(); s=self.f.store; action=actions[1]
        self.f.reserve(action); s.result(action['action_key'],'accepted','offline-id')
        self.assertEqual(results(s)['prospect_email_exact_sent'],0); s.result(action['action_key'],'sent','offline-id',{'message_id':'offline-id','mime_sha256':'a'*64,'action_binding':'action_header'})
        self.assertEqual(results(s)['prospect_email_exact_sent'],1); s.db.execute("UPDATE people SET data_json=json_set(data_json,'$.controlled_test',1)")
        self.assertEqual(results(s)['prospect_email_exact_sent'],1)
    def test_pilot_exact_canary_gates_lifetime_cohort_and_unapproved_actions(self):
        from tools.setup import approve_release,results
        actions,path=self.pilot(); s=self.f.store; s.release('offline-owner')
        s.db.execute('INSERT INTO history VALUES (?,?,?,?,?,?)',('own-manual','colleague@example.org','example.org',now(),'sent',encode({'auto':False}))); s.db.commit()
        external={**actions[0],'payload':{**actions[0]['payload'],'controlled_test':False}}; self.assertTrue(any('manual account' in i for i in checks.exclusion_issues(s,external,{'name':'Owner'},datetime.now(timezone.utc))))
        def native(store,row):
            exact=checks.unpack(row); checks.require_commit(store,exact); self.f.reserve(exact)
            receipt={'message_id':'native-'+exact['action_key'],'mime_sha256':'a'*64,'action_binding':'action_header'}
            store.result(exact['action_key'],'sent',receipt['message_id'],receipt); return {'status':'sent'}
        with patch.object(scheduler,'dispatch',side_effect=native) as provider:
            self.assertEqual(scheduler.cycle(s,force=True,limit=10)['provider_commitments'],1)
            self.assertEqual(scheduler.cycle(s,force=True,limit=10)['provider_commitments'],10)
            tomorrow=scheduler._clock()+timedelta(days=1)
            with patch.object(scheduler,'_clock',return_value=tomorrow): self.assertEqual(scheduler.cycle(s,force=True,limit=10)['provider_commitments'],0)
            self.assertEqual(provider.call_count,11); self.assertTrue(results(s)['prospect_pilot_complete'])
        with self.assertRaisesRegex(ValueError,'unattempted|already pinned'): approve_release(s,path,True)
        self.assertTrue(checks.approved_scope(s,self.f.action())[1]); changed={**actions[1],'sender':'other@example.org'}
        self.assertTrue(checks.approved_scope(s,changed)[1])
    def test_validation_renews_only_stale_complete_and_preserves_unknown(self):
        from engine.research import Research
        s=self.f.store; s.set('research_enabled',True); s.db.commit(); calls=[]
        class HTTP:
            def credential(self,p): return 'offline-key'
            def request(self,*args,**kwargs):
                calls.append(args); return Response(200,{'address':self.f.person['email'],'status':'valid'},b'{}',{})
        http=HTTP(); http.f=self.f; client=Research(s,http)
        first=client.validate_email(self.f.person['email']); client.validate_email(self.f.person['email']); self.assertEqual(len(calls),1)
        old={**first,'at':(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()}; s.db.execute('UPDATE attempts SET receipt_json=?',(encode(old),)); s.db.commit()
        client.validate_email(self.f.person['email']); self.assertEqual(len(calls),2)
        s.db.execute("UPDATE attempts SET status='uncertain'"); s.db.commit()
        with self.assertRaisesRegex(ValueError,'Unknown'): client.validate_email(self.f.person['email'])
        self.assertEqual(len(calls),2)
    def test_native_mode_holds_partial_history_or_customer_range(self):
        from tools.setup import refresh_portable
        s=self.f.store; s.set('exclusion_mode','native'); s.set('native_exclusions',['revenue','hubspot']); s.set('history_sources',{'gmail_start':123}); s.set('revenue',{'range':'Customers!A1:C10'})
        prepare(s,'email',self.f.person,self.f.payload,'owner@example.org')
        with patch('engine.channels.meetings.Meetings'),patch('engine.channels.email.Replies'):
            self.assertNotIn('customers',refresh_portable(s)['refreshed'])
    def test_gift_grant_bounds_native_currency_and_lifetime_value(self):
        from decimal import Decimal
        s=self.f.store; s.set('portable_attendee',True)
        action=prepare(s,'gift',self.f.person,{'gift':{}},'Owner')
        p=self.f.folder/'gift.json'; p.write_text(encode({'authority':'Offline gift','purpose':'one gift','action_keys':[action['action_key']],'limits':{'email':0,'gift':1,'social':0},'gift_budget':{'currency':'USD','max_per_gift':50,'max_total':50}})); approve_release(s,p)
        self.assertEqual(checks.gift_budget_issues(s,action,Decimal('50'),'USD'),[])
        self.assertTrue(checks.gift_budget_issues(s,action,Decimal('51'),'USD')); self.assertTrue(checks.gift_budget_issues(s,action,Decimal('50'),None))
    def test_ad_draft_rejects_over_cap_and_unsupported_channels_before_write(self):
        s=self.f.store; s.set('policy',{'advertising':{'enabled':True,'max_daily_budget':100}}); client=Assets(s)
        with patch.object(client,'account',return_value={'account_id':7}),patch.object(client,'_tool') as provider:
            for channel,budget in (('linkedin',101),('facebook',101),('google',1)):
                arguments={'campaign_data':{'name':'Own draft','budgetGroup':'Own group',channel:{'dailyBudget':budget}}}
                with self.assertRaisesRegex(ValueError,'Unsupported draft channel|approved daily budget'):
                    client.advertising('create_campaign',arguments,approved_sha256='unused')
            provider.assert_not_called(); self.assertEqual(s.one('SELECT count(*) AS n FROM attempts')['n'],0)
    def test_cross_mailbox_owned_controlled_test_is_rejected_before_reservation(self):
        from tools.setup import approve_release
        s=self.f.store; authority=s.setting('policy'); authority.update(senders={'owner@example.org':2,'second@example.org':2},controlled_test_recipients=['owner@example.org','second@example.org']); s.set('policy',authority)
        person={**self.f.person,'email':'second@example.org'}; payload={**self.f.payload,'sender':'owner@example.org','controlled_test':True}
        action=prepare(s,'email',person,payload,'owner@example.org'); approval=self.f.folder/'cross-mailbox.json'
        approval.write_text(encode({'authority':'Offline owned test','purpose':'self','action_keys':[action['action_key']],'limits':{'email':1,'gift':0,'social':0}}))
        with self.assertRaisesRegex(ValueError,'recipient must equal'): approve_release(s,approval)
        self.assertEqual(s.one('SELECT count(*) AS n FROM attempts')['n'],0)
    def test_config_history_cannot_override_canonical_scope_and_private_paths(self):
        from tools.setup import configure,credential_path
        from engine.database import ROOT
        s=self.f.store; path=self.f.folder/'private.json'; value={'company':{'name':'Owned','domain':'owned.example'},'policy':self.f.authority,'settings':{'history_sources':{'instantly':True}},'history_since_epoch':0}
        workspace=self.f.folder/'company-motion'; workspace.mkdir(); (workspace/'COMPANY.md').write_text('Actual offline company brief')
        path.write_text(encode(value)); path.chmod(0o600)
        with patch('tools.setup.ROOT',self.f.folder/'code'): configure(s,path)
        self.assertEqual(s.setting('history_sources'),{'instantly':True,'gmail':['owner@example.org'],'gmail_start':0})
        value['settings']['history_sources']['gmail_start']=99; path.write_text(encode(value))
        with patch('tools.setup.ROOT',self.f.folder/'code'), self.assertRaisesRegex(ValueError,'cannot override'): configure(s,path)
        with self.assertRaisesRegex(ValueError,'outside this cloned repository'): credential_path(ROOT.parent/'company-motion'/'key.txt')
        secret=self.f.folder/'key.txt'; secret.write_text('offline'); secret.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'0600'): credential_path(secret)
        secret.chmod(0o600); self.assertEqual(credential_path(secret),secret.resolve())
    def test_social_import_requires_original_successful_provisioning(self):
        from tools.setup import import_records
        from engine.channels.social import Social
        s=self.f.store; s.set('social_owned',{'Owner':{'campaign_id':2,'list_id':1,'seat_id':3}})
        payload={'sender':'Owner','campaign_id':2,'list_id':1,'seat_id':3,'contact_id':7,'profileUrl':self.f.person['profile'],'plain_invitation':True}
        path=self.f.folder/'social.json'; path.write_text(encode([{'channel':'linkedin','recipient':self.f.person['email'],'sender':'Owner','payload':payload}])); s.db.commit()
        with self.assertRaisesRegex(ValueError,'cannot adopt'): import_records(s,'actions',path)
        self.assertEqual(s.setting('social_prepared',{}),{})
        def native(client,name,args):
            if name=='get_list': return {'id':1,'campaignId':2}
            if name=='get_campaign': return {'id':2,'active':False,'steps':[{'type':'invitation'}]}
            result={'id':7,'listId':1,'email':self.f.person['email'],'profileUrl':self.f.person['profile'],'state':'paused','readyForCampaign':False}
            with s.db: s.record('gojiberry','original-create','create_contact',{'arguments':args,'result':result,'receipt':{'http_status':200,'request_id':'original-create','response_sha256':'a'*64}})
            client.last_source_key='original-create'; return result
        with patch.object(Social,'_tool',new=native): Social(s).provision('create_contact',{'listId':1})
        result=import_records(s,'actions',path); self.assertEqual(result['imported'],1)
        self.assertEqual(s.setting('social_prepared')['7']['provisioning']['record_key'],'original-create'); s.db.execute("UPDATE source_records SET digest='changed' WHERE record_key='original-create'")
        with self.assertRaisesRegex(ValueError,'differs'): Social(s).provisioning(self.f.person,payload)
    def test_gift_capture_binds_same_form_owned_provider_and_actual_time(self):
        from tools.setup import import_records
        s=self.f.store; s.set('loop_and_tie_team','owned-team'); html=self.f.folder/'gate.html'; path=self.f.folder/'gate.json'
        good='<form id="edit_scheduler_42"><input name="external" value="owned-gate"><input name="required" type="checkbox" checked></form>'
        html.write_text(good); value={'external_id':'owned-gate','numeric_id':42,'name':'Gate','source':'Native source','meeting_required':True,'form_html_file':str(html),'meeting_required_field':'required','external_id_field':'external','capture_url':'https://app.loopandtie.com/schedulers/owned-gate/edit','captured_at':now(),'provider':'loop_and_tie','team_id':'owned-team'}
        native={'team':{'id':'owned-team'},'schedulers':[{'id':'owned-gate','attributes':{'external-id':'owned-gate','name':'Gate','source':'Native source'}}],'at':now()}
        with patch('engine.channels.gifts.Gifts') as provider:
            provider.return_value.catalogue.return_value=native
            html.write_text('<input name="external" value="owned-gate">'+good.replace('<input name="external" value="owned-gate">','')); path.write_text(encode(value))
            with self.assertRaisesRegex(ValueError,'same numeric form'): import_records(s,'gift-gate',path)
            html.write_text(good); value['captured_at']=(datetime.now(timezone.utc)-timedelta(minutes=66)).isoformat(); path.write_text(encode(value))
            with self.assertRaisesRegex(ValueError,'fresh authenticated'): import_records(s,'gift-gate',path)
            provider.return_value.catalogue.assert_not_called(); value['captured_at']=now(); path.write_text(encode(value))
            self.assertTrue(import_records(s,'gift-gate',path)['gift_gate_saved'])
            self.assertEqual(s.setting('gift_gate')['observed_at'],value['captured_at'])
    def test_revoked_pilot_cannot_release_reset_or_replace_its_grant(self):
        from tools.setup import revoke_release
        actions,path=self.pilot(); s=self.f.store; before=s.setting('pilot_approval'); revoke_release(s,'pilot','Wrong approved copy')
        self.assertTrue(any('revoked' in i for i in checks.approved_scope(s,actions[0])[1])); self.assertEqual(s.setting('pilot_approval'),before)
        with self.assertRaisesRegex(ValueError,'already pinned'): approve_release(s,path,True)
        self.assertEqual(s.one('SELECT count(*) AS n FROM attempts')['n'],0)
    def test_google_chosen_paths_are_checked_at_consumption_before_refresh(self):
        from engine.channels.email import delegated_token
        from engine.database import ROOT
        s=self.f.store; bad=self.f.folder/'oauth.json'; bad.write_text('{}'); bad.chmod(0o644)
        http=type('HTTP',(),{'store':s,'request':lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('Provider called'))})()
        for path in (bad,ROOT/'key.json',ROOT.parent/'company-motion'/'key.json'):
            s.set('credential_files',{'google:owner@example.org':str(path)})
            with patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(ProviderError,'0600|outside this cloned repository'):
                delegated_token(http,'owner@example.org','gmail.test')
            with patch.dict(os.environ,{'V5_GOOGLE_SERVICE_ACCOUNT_FILE':str(path)},clear=True),self.assertRaisesRegex(ProviderError,'0600|outside this cloned repository'):
                delegated_token(http,'owner@example.org','gmail.test')
    def test_exact_selection_never_dispatches_another_approved_grant(self):
        foreign=prepare(self.f.store,'email',self.f.person,self.f.payload,'owner@example.org'); path=self.f.folder/'other-grant.json'
        path.write_text(encode({'authority':'Offline second grant','purpose':'other','action_keys':[foreign['action_key']],'limits':{'email':1,'gift':0,'social':0}})); approve_release(self.f.store,path)
        actions,_=self.pilot(); s=self.f.store; s.release('offline-owner'); selected=actions[0]['action_key']
        def native(store,row):
            exact=checks.unpack(row); checks.require_commit(store,exact); self.f.reserve(exact); store.result(exact['action_key'],'accepted','native-id'); return {'status':'accepted'}
        with patch.object(scheduler,'dispatch',side_effect=native) as provider:
            self.assertEqual(scheduler.cycle(s,force=True,limit=1,action_keys=[selected])['provider_commitments'],1)
            self.assertEqual(provider.call_args.args[1]['action_key'],selected); self.assertIsNone(s.one('SELECT idem_key FROM attempts WHERE idem_key=?',(foreign['action_key'],)))
        with self.assertRaisesRegex(ValueError,'existing original'): scheduler.cycle(s,force=True,limit=1,action_keys=['unknown'])
        self.assertEqual(s.one('SELECT count(*) AS n FROM attempts')['n'],1)
if __name__ == '__main__': unittest.main(verbosity=2)
