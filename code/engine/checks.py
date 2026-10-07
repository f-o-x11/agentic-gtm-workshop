"""Current safety checks. Unknown evidence cannot authorize a provider commitment."""
from datetime import datetime, timezone
import hashlib
import json
import time
from engine import validation as copywriting
from engine import validation as identity
from engine.database import digest, encode, now

ALIASES = {'email': ('email', 'gmail', 'instantly', 'initial_email'),
           'gift': ('gift',), 'linkedin': ('linkedin', 'linkedin_invitation'),
           'linkedin_message': ('linkedin_message',)}
# Native scheduler_checks: outcomes 25 minutes, CRM 65, mailbox history 60.
SAFETY = {'suppressions': 65 * 60, 'customers': 65 * 60, 'open_deals': 65 * 60,
          'bookings': 25 * 60, 'history': 60 * 60}


def policy(store):
    authority = store.setting('policy', {})
    path = store.policy_path
    try:
        local = json.loads(path.read_text())
    except (OSError, ValueError):
        local = {}
    return authority if isinstance(authority, dict) else {}, local if isinstance(local, dict) else {}


def action_hash(action):
    return digest({k: action.get(k) for k in ('channel', 'recipient', 'domain', 'sender', 'payload', 'at')})


def make_action(channel, person, payload, sender=''):
    action = {'channel': channel, 'recipient': identity.email(person.get('email')),
              'domain': identity.domain(person.get('domain')), 'sender': sender,
              'payload': payload, 'at': now()}
    action['action_key'] = action_hash(action)
    return action


def unpack(action):
    row = dict(action)
    if 'payload' not in row:
        row['payload'] = identity.load(row.get('payload_json'))
    return row


def approved_scope(store, action):
    """An owner grant pins exact actions. New dates or changed people cannot widen it."""
    if not store.setting('portable_attendee', False): return {}, []
    key=action.get('action_key'); issues=[]
    for row in store.rows("SELECT record_key,data_json,digest FROM source_records WHERE source='owner.release'"):
        grant=identity.load(row['data_json']); pinned=grant.get('actions',{}).get(key)
        if not pinned: continue
        if store.setting('revoked_grant:'+row['record_key']) or store.one("SELECT event_id FROM events WHERE event_id=?",('release_revoked:'+row['record_key'],)):
            return {}, ['Exact owner grant was revoked. Its original keys and lifetime ceiling remain protected.']
        event=store.one("SELECT * FROM events WHERE event_id=?",('release_approved:'+row['record_key'],))
        if (digest(grant)!=row['digest'] or not event or identity.load(event['payload_json'])!={'grant_digest':row['digest']}
                or event['source_digest']!=digest({'at':event['at'],'kind':event['kind'],'entity':event['entity'],
                    'payload':identity.load(event['payload_json'])})):
            return {}, ['Exact release approval receipt changed or is missing.']
        actual={k:action.get(k) for k in ('action_key','channel','recipient','domain','sender','at')}
        actual['payload_digest']=digest(action.get('payload')); actual['controlled_test']=action.get('payload',{}).get('controlled_test') is True
        if pinned!=actual: issues.append('Action differs from the exact owner-approved release.')
        if actual['controlled_test'] and actual['recipient']!=actual['sender']:
            issues.append('Controlled self-test recipient must equal its exact sender mailbox.')
        if grant.get('kind')=='pilot' and key!=grant['controlled_action_key']:
            if not exact_email_sent(store,grant['controlled_action_key']):
                issues.append('Confirm the exact owned test email in Gmail Sent before releasing prospects.')
        return {**grant,'grant_id':row['record_key']}, issues
    return {}, ['Approve these exact actions with approve-pilot or approve-scope before release.']


def exact_email_sent(store, key):
    attempt=store.one("SELECT * FROM attempts WHERE channel='email' AND idem_key=?",(key,))
    receipt=identity.load(attempt['receipt_json']) if attempt else {}
    sent=store.one("SELECT * FROM events WHERE kind='attempt_sent' AND entity=? ORDER BY rowid DESC LIMIT 1",(key,))
    return bool(attempt and attempt['status']=='sent' and __import__('re').fullmatch('[0-9a-f]{64}',str(receipt.get('mime_sha256','')))
        and receipt.get('message_id')==attempt['provider_id'] and receipt.get('action_binding') in ('action_header','accepted_native_id')
        and sent and identity.load(sent['payload_json']).get('receipt')==receipt and sent['source_digest']==digest(
            {'at':sent['at'],'kind':sent['kind'],'entity':sent['entity'],'payload':identity.load(sent['payload_json'])}))


def release_keys(store):
    if not store.setting('portable_attendee',False): return None
    keys=set()
    for row in store.rows("SELECT * FROM actions WHERE status='ready'"):
        grant,issues=approved_scope(store,unpack(row))
        if grant and not issues: keys.add(row['action_key'])
    return keys


def gift_budget_issues(store, action, cost, currency):
    grant,issues=approved_scope(store,action)
    budget=grant.get('gift_budget',{})
    from decimal import Decimal
    if not budget or currency!=budget.get('currency'):
        return issues+['Gift collection must expose the exact approved currency.']
    used=sum(Decimal(str(identity.load(row['payload_json'])['cost'])) for row in store.rows(
        "SELECT payload_json FROM events WHERE kind='gift_budget_reserved' AND json_extract(payload_json,'$.grant_id')=? AND entity!=?",
        (grant['grant_id'],action['action_key'])))
    if cost<=0 or cost>Decimal(str(budget['max_per_gift'])) or used+cost>Decimal(str(budget['max_total'])):
        issues.append('Gift exceeds the approved per-gift or lifetime total value.')
    return issues


def source_integrity(store, names=None):
    issues = []
    sources = store.rows('SELECT * FROM sources')
    if not sources:
        return ['Canonical source manifest is missing.']
    for source in sources:
        if names is not None and source['name'] not in names:
            continue
        rows = store.rows('SELECT record_key,data_json,digest FROM source_records WHERE source=? ORDER BY record_key', (source['name'],))
        keys, values = hashlib.sha256(), hashlib.sha256()
        valid = True
        for row in rows:
            try:
                value = json.loads(row['data_json'])
            except (TypeError, ValueError):
                valid = False
                break
            actual = digest(value)
            if actual != row['digest']:
                valid = False
                break
            keys.update((row['record_key'] + '\n').encode())
            values.update((row['record_key'] + '\0' + actual + '\n').encode())
        if (not valid or len(rows) != source['record_count'] or keys.hexdigest() != source['key_digest']
                or values.hexdigest() != source['data_digest']):
            issues.append('Canonical source hash or count differs: ' + source['name'] + '.')
    return issues


def refresh_issues(store, at, action=None):
    issues = []
    refresh = store.setting('safety_refresh', {})
    sources = refresh.get('sources', {}) if isinstance(refresh, dict) else {}
    for name, max_age in SAFETY.items():
        proof = sources.get(name) if isinstance(sources, dict) else None
        if (not isinstance(proof, dict) or proof.get('complete') is not True
                or (max_age is not None and not identity.fresh(proof.get('observed_at'), max_age, at))
                or (max_age is None and proof.get('canonical_current') is not True)):
            issues.append('Current ' + name.replace('_', ' ') + ' coverage is incomplete.')
            continue
        row = store.one('SELECT kind,data_json,digest FROM source_records WHERE source=? AND record_key=?',
                        (proof.get('source'), str(proof.get('record_key', ''))))
        raw = identity.load(row['data_json']) if row else {}
        if (not row or row['kind'] != 'safety_coverage' or row['digest'] != proof.get('digest')
                or digest(raw) != row['digest'] or raw.get('coverage') != name or raw.get('complete') is not True
                or raw.get('observed_at') != proof.get('observed_at')
                or (max_age is None and raw.get('canonical_current') is not True)):
            issues.append('Current ' + name.replace('_', ' ') + ' source receipt is missing or changed.')
        elif action and raw.get('domain_scope') is not None and not set(identity.account_domains(store, action['domain'])) <= set(raw['domain_scope']):
            issues.append('Current ' + name.replace('_', ' ') + ' checks do not cover this account.')
    return issues


def execution_issues(store):
    _, local = policy(store)
    issues = []
    if local.get('execution_enabled') is not True:
        issues.append('Outreach is paused in config/policy.json.')
    return issues


def refresh_batch(store):
    """Refresh the selected accounts, then bind real reads to account-scoped receipts."""
    from engine.channels.meetings import Meetings
    from engine.channels.email import Replies
    if store.setting('portable_attendee', False):
        from tools.setup import refresh_portable
        return refresh_portable(store)
    rows = store.rows("SELECT * FROM actions WHERE status IN ('ready','held')")
    domains = sorted({d for row in rows for d in identity.account_domains(store, row['domain'])})
    if not domains:
        return {'refreshed': [], 'failures': {}, 'reason': 'No prepared actions. The Codex skill must select and prepare recipients.'}
    at, calls, failures = datetime.now(timezone.utc), {}, {}
    meetings = Meetings(store)
    for name, call in (('customers_refresh', meetings.customers), ('salesforce_deals_refresh', meetings.salesforce_deals),
                       ('hubspot_deals_refresh', meetings.hubspot_deals), ('bookings_refresh', meetings.refresh)):
        cached = store.setting(name, {})
        complete = cached.get('complete_inventory') is True if name != 'bookings_refresh' else cached.get('complete') is True
        seconds = SAFETY['bookings'] if name == 'bookings_refresh' else SAFETY['customers']
        if complete and identity.fresh(cached.get('observed_at'), seconds, at):
            calls[name] = cached
            continue
        try:
            calls[name] = call()
            if calls[name].get('complete', calls[name].get('complete_inventory')) is not True:
                failures[name] = calls[name].get('failures') or 'The configured source did not finish.'
        except Exception as exc:
            failures[name] = str(exc)
    configured = store.setting('history_sources', {})
    authority, _ = policy(store)
    configured['domains'] = domains
    configured['gmail'] = sorted(email for email, cap in authority.get('senders', {}).items()
                                  if isinstance(cap, int) and not isinstance(cap, bool) and cap > 0)
    with store.db:
        store.set('history_sources', configured)
    cached = store.setting('history_refresh', {})
    if (cached.get('complete') is True and set(cached.get('domain_scope', [])) >= set(domains)
            and set(cached.get('sources', {})) >= set(configured['gmail'])
            and all(not configured.get(name) or name in cached.get('sources', {}) for name in ('instantly', 'linkedin'))
            and identity.fresh(cached.get('observed_at'), SAFETY['history'], at)):
        calls['history_refresh'] = cached
    else:
        try:
            calls['history_refresh'] = Replies(store).refresh()
            if calls['history_refresh'].get('complete') is not True:
                failures['history_refresh'] = calls['history_refresh'].get('failures')
        except Exception as exc:
            failures['history_refresh'] = str(exc)
    requirements = {'customers': ['customers_refresh'], 'open_deals': ['salesforce_deals_refresh', 'hubspot_deals_refresh'],
                    'bookings': ['bookings_refresh'], 'history': ['history_refresh'],
                    'suppressions': ['history_refresh', 'customers_refresh', 'salesforce_deals_refresh', 'hubspot_deals_refresh']}
    # Keep an existing fresh, scoped exclusion read when an unrelated refresh fails.
    proofs = dict(store.setting('safety_refresh', {}).get('sources', {}))
    with store.db:
        for name, dependencies in requirements.items():
            if any(key not in calls or key in failures for key in dependencies):
                continue
            stamp = min(calls[key]['observed_at'] for key in dependencies)
            if not identity.fresh(stamp, SAFETY[name]):
                failures[name] = 'The source read is too old. Refresh this source.'
                continue
            value = {'coverage': name, 'complete': True, 'observed_at': stamp, 'domain_scope': domains,
                     'dependencies': {key: calls[key] for key in dependencies},
                     'coverage_note': 'Selected account domains and configured providers only; other accounts remain unchecked.'}
            store.record('v5.batch_checks', name, 'safety_coverage', value)
            proofs[name] = {**{k: value[k] for k in ('complete', 'observed_at')},
                           'source': 'v5.batch_checks', 'record_key': name, 'digest': digest(value)}
        store.set('safety_refresh', {'sources': proofs, 'domain_scope': domains})
        store.event('batch_checked', ','.join(domains), {'checked': list(proofs), 'failures': failures})
    return {'refreshed': list(proofs), 'domain_scope': domains, 'failures': failures}


def recheck_actions(store):
    """Release repaired, unattempted drafts without rebuilding their exact copy."""
    changed = []
    with store.db:
        for row in store.rows("SELECT * FROM actions WHERE status IN ('ready','held')"):
            issues = validate(store, row)
            status, reason = ('held' if issues else 'ready'), '; '.join(issues)
            if row['status'] != status or row['reason'] != reason:
                store.db.execute('UPDATE actions SET status=?,reason=? WHERE action_key=?', (status, reason, row['action_key']))
                store.event('action_rechecked', row['action_key'], {'status': status, 'issues': issues})
                changed.append({'key': row['action_key'], 'status': status, 'issues': issues})
    return changed


def consent_issues(store, action, authority, at, enforce_limits=True):
    channel, sender = action['channel'], action.get('sender') or ''
    issues = []
    if not authority.get('authority'):
        issues.append('Actual standing execution authority is missing.')
    if channel == 'email':
        sender = identity.email(sender)
        cap = authority.get('senders', {}).get(sender)
        consent = store.one('SELECT * FROM sender_consent WHERE email=?', (sender,))
        if not sender or not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0 or not consent or consent['enabled'] != 1:
            issues.append('Sender has no current consent and policy cap.')
        for row in store.rows("SELECT data_json FROM source_records WHERE source='postgres.sender_consent'"):
            raw = identity.load(row['data_json'])
            if identity.email(raw.get('email')) == sender and (raw.get('state') != 'granted' or raw.get('revoked_at')):
                issues.append('Actual sender consent was revoked or is not granted.')
    elif channel == 'gift':
        if authority.get('gift_fulfillment') != 'automatic':
            issues.append('Actual automatic gift authority is unavailable.')
    elif channel in ('linkedin', 'linkedin_message'):
        resource = store.setting('social_owned', {}).get(sender)
        if not isinstance(resource, dict) or not all(resource.get(k) for k in ('campaign_id', 'list_id', 'seat_id')):
            issues.append('Actual owned LinkedIn seat, list and campaign are missing.')
        if authority.get('linkedin_dispatch') != 'automatic':
            issues.append('Actual LinkedIn execution authority is unavailable.')
    return issues


def history_issue(store, row, action):
    """A send in another channel or to another colleague is not a duplicate."""
    raw, kind = identity.load(row['data_json']), row['kind']
    if kind.endswith('_coverage'):
        return None
    same_person = row['recipient'] == action['recipient']
    if kind == 'gift_rows':
        return 'A gift already exists for this recipient.' if same_person and action['channel'] == 'gift' else None
    if kind in ('sent', 'email_rows') or raw.get('outbound') is True:
        if same_person and action['channel'] == 'email':
            return 'An email already exists for this recipient.'
        native_id = raw.get('native_id') or raw.get('id')
        recorded = bool(native_id and store.one('SELECT idem_key FROM attempts WHERE provider_id=? AND recipient=?',
                                               (str(native_id), row['recipient'])))
        if raw.get('auto') is False or (raw.get('auto') is not True and not recorded):
            return 'Existing manual account conversation excludes cold outreach.'
        return None
    if kind in ('real', 'relationship_contacts', 'social_reply') or raw.get('relationship'):
        return 'Existing account relationship or human reply excludes cold outreach.'
    if kind == 'reply_rows' and raw.get('auto') is False:
        return 'Existing human account reply excludes cold outreach.'
    if same_person and kind not in ('auto', 'social_sent'):
        return 'This recipient has unresolved incoming history or an identity exclusion.'
    if same_person and kind == 'social_sent' and action['channel'] == 'linkedin_message':
        return 'A social message already exists for this recipient.'
    return None


def exclusion_issues(store, action, account, at):
    recipient, employer = action['recipient'], action['domain']
    domains = identity.account_domains(store, employer)
    slots = ','.join('?' for _ in domains)
    issues = []
    authority,_=policy(store)
    candidate=store.one('SELECT data_json FROM people WHERE email=? AND domain=?',(recipient,employer))
    controlled=(action.get('payload',{}).get('controlled_test') is True
        and candidate and identity.load(candidate['data_json']).get('controlled_test') is True
        and recipient==action.get('sender') and recipient in authority.get('controlled_test_recipients',[]) and recipient in authority.get('senders',{}))
    if controlled and store.setting('portable_attendee',False):
        grant,guard=approved_scope(store,action)
        controlled=bool(grant and not guard and grant['actions'][action['action_key']]['controlled_test'])
    if action.get('payload',{}).get('controlled_test') is True and not controlled:
        issues.append('Controlled test must use an explicitly authorized owned sender mailbox and labeled person record.')
    if recipient.rsplit('@', 1)[-1] in store.setting('internal_domains', []) and not controlled:
        issues.append('Internal recipients are excluded.')
    if controlled:
        if store.one("SELECT value FROM suppressions WHERE entity_type='email' AND value=?",(recipient,)):
            issues.append('The owned test mailbox has an explicit recipient opt-out.')
        return issues
    if store.one("SELECT value FROM suppressions WHERE (entity_type='email' AND value=?) OR (entity_type='domain' AND value IN (" + slots + '))', (recipient, *domains)):
        issues.append('Current opt-out, customer, deal, relationship or suppression excludes this target.')
    for row in store.rows("SELECT data_json FROM source_records WHERE source IN ('postgres.customer_account','postgres.open_deal','live.salesforce.open_deals','live.hubspot.open_deals','live.revenue.customers')"):
        raw = identity.load(row['data_json'])
        name = identity.normalized(raw.get('name') or raw.get('company'))
        if identity.domain(raw.get('domain')) in domains or (name and name == identity.normalized(account.get('name'))):
            issues.append('Current customer or open deal matches the exact account.')
            break
    if store.one("SELECT booking_key FROM bookings WHERE (recipient=? OR domain IN (" + slots + ")) AND COALESCE(state,'unknown') NOT IN ('cancelled','canceled','rejected')", (recipient, *domains)):
        issues.append('Current booking or inbound request excludes cold outreach.')
    for row in store.rows('SELECT * FROM history WHERE recipient=? OR domain IN (' + slots + ')', (recipient, *domains)):
        issue = history_issue(store, row, action)
        if issue:
            issues.append(issue)
            break
    for row in store.rows("SELECT data_json FROM source_records WHERE source='postgres.outbox' AND json_extract(data_json,'$.email')=?", (recipient,)):
        raw = identity.load(row['data_json'])
        if action['channel'] == 'email' and raw.get('status') not in ('cancelled', 'canceled', 'aborted'):
            issues.append('An existing queued or sent email duplicates this recipient.')
            break
    return issues


def _reservation_allowed(store, action, row, allow_reserved):
    return bool(allow_reserved and row['idem_key'] == action.get('action_key')
                and getattr(store, 'active_attempts', {}).get(row['idem_key']) == digest(action.get('payload'))
                and row['status'] == 'attempting' and row['payload_json'] == encode(action.get('payload'))
                and row['recipient'] == action.get('recipient') and row['domain'] == action.get('domain')
                and row['sender'] == action.get('sender') and row['channel'] == action.get('channel'))


def attempt_issues(store, action, at, authority, allow_reserved=False):
    issues = []
    aliases = ALIASES.get(action['channel'], (action['channel'],))
    for row in store.rows('SELECT * FROM attempts WHERE recipient=?', (action['recipient'],)):
        if row['channel'] not in aliases:
            continue
        if row['status'] in ('aborted', 'cancelled'):
            continue
        if _reservation_allowed(store, action, row, allow_reserved):
            continue
        issues.append('Existing channel attempt requires reconciliation, never another send.')
    return issues


def validate(store, action, committing=False, allow_reserved=False):
    action = unpack(action)
    at = datetime.now(timezone.utc)
    issues = []
    authority, local = policy(store)
    if action.get('channel') not in ALIASES:
        issues.append('Channel is not an authorized outreach action.')
    if action.get('action_key') != action_hash(action):
        issues.append('Exact action hash changed or is missing.')
    prepared = identity.timestamp(action.get('at'))
    if prepared is None or prepared > at:
        issues.append('Action preparation has no valid timestamp.')
    if not isinstance(action.get('payload'), dict):
        issues.append('Action payload is not an object.')
        return issues
    issues.extend(approved_scope(store,action)[1])
    recipient, employer = identity.email(action.get('recipient')), identity.domain(action.get('domain'))
    if not recipient or not employer:
        return issues + ['Actual recipient or employer domain is invalid.']
    action.update(recipient=recipient, domain=employer)
    if committing:
        issues.extend(execution_issues(store))
        pacing = store.setting('hourly_pacing', local.get('hourly_pacing', {}))
        if isinstance(pacing, dict) and pacing.get('enforced') is True:
            from engine.scheduler import pacing_issues
            issues.extend(pacing_issues(store, action))
    issues.extend(refresh_issues(store, at, action))
    account = store.one('SELECT * FROM accounts WHERE domain=?', (employer,))
    grant,guard=approved_scope(store,action)
    owned=store.one('SELECT data_json FROM people WHERE email=? AND domain=?',(recipient,employer))
    test=(grant and not guard and action['payload'].get('controlled_test') is True and owned
        and identity.load(owned['data_json']).get('controlled_test') is True and recipient in authority.get('senders',{})
        and recipient==action.get('sender') and recipient in authority.get('controlled_test_recipients',[]))
    own_country=identity.load(account.get('data_json')).get('country') if account else None
    account_policy={**authority,'recipient_company_countries':[own_country]} if test and own_country else authority
    issues.extend(identity.account_issues(account, account_policy))
    wanted = identity.profile(action.get('payload', {}).get('profileUrl') or action.get('payload', {}).get('profile_url'))
    person, person_errors = identity.find_person(store, recipient, employer, wanted)
    issues.extend(person_errors)
    issues.extend(identity.person_issues(store, person, employer, at,
                                       require_profile=action['channel'] in ('linkedin', 'linkedin_message')))
    if person:
        action['profile'] = identity.profile(person.get('profile'))
    issues.extend(consent_issues(store, action, authority, at, enforce_limits=committing))
    issues.extend(exclusion_issues(store, action, account or {}, at))
    issues.extend(attempt_issues(store, action, at, authority, allow_reserved))
    for row in store.rows("SELECT data_json FROM settings WHERE name LIKE 'hourly_pacing:%'"):
        claim = identity.load(row['data_json']).get('claims', {}).get(action['action_key'], {})
        if claim and claim.get('status') != 'not_committed':
            own = committing and claim.get('status') == 'dispatching' and claim.get('owner') == getattr(store, 'execution_owner', None)
            if not own:
                issues.append('An earlier release has an unresolved or completed submission. Reconcile it before retrying.')
    issues.extend(copywriting.validate(action['payload'], initial_email=action['channel'] == 'email' and not action['payload'].get('reply_to')))
    if committing:
        lease = store.one("SELECT * FROM leases WHERE name='execution'")
        if (not lease or lease['expires_at'] <= time.time()
                or lease['owner'] != getattr(store, 'execution_owner', None)):
            issues.append('A current single-owner execution lease is required.')
    return sorted(set(issues))


def require_commit(store, action, allow_reserved=False):
    issues = validate(store, action, committing=True, allow_reserved=allow_reserved)
    if issues:
        raise ValueError(' '.join(issues))
