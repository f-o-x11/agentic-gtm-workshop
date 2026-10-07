"""One transactional store. Business records and events create rows, not files."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DB = ROOT / "data" / "gtm.sqlite"
DEFAULT_DB = ROOT.parent / "company-motion" / "gtm.sqlite"
SCHEMA = ROOT / "config" / "schema.sql"

def now():
    return datetime.now(timezone.utc).isoformat()

def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)

def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()

def database_snapshot(path):
    """Read the actual saved records without changing the source database."""
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('Saved database integrity failed. Keep execution paused.')
        tables=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts={name:db.execute('SELECT count(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in tables}
        return {'counts':counts,'records_sha256':hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest()}

def migrate_legacy_database(root=ROOT):
    """Explicitly preserve old records privately and leave execution paused."""
    import secrets
    root=Path(root).resolve(); source=root/'data/gtm.sqlite'; folder=root.parent/'company-motion'
    target=folder/'gtm.sqlite'; policy_path=root/'config/policy.json'
    if not source.is_file(): raise ValueError('No old saved database exists.')
    before=database_snapshot(source)
    if not any(before['counts'].values()):
        return {'migration_needed':False,'provider_writes':0,'reason':'The tracked database is an empty template.'}
    if target.exists(): raise ValueError('A private working database already exists. Do not overwrite or combine saved histories.')
    original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    archive=folder/('legacy-gtm-'+original_hash+'.sqlite')
    if archive.exists(): raise ValueError('An original database backup already exists. Inspect the existing migration before proceeding.')
    config=json.loads(policy_path.read_text()); config['execution_enabled']=False; config.pop('commits_enabled',None)
    policy_path.write_text(json.dumps(config,indent=2)+'\n'); policy_path.chmod(0o600)
    pending=folder/('.migration-'+secrets.token_hex(12)+'.sqlite')
    descriptor=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.close(descriptor)
    try:
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as old,closing(sqlite3.connect(pending)) as saved:
            old.backup(saved)
            saved.commit()
        if database_snapshot(pending)!=before or hashlib.sha256(source.read_bytes()).hexdigest()!=original_hash:
            raise ValueError('The complete saved record check failed. Original records remain in place.')
        os.replace(pending,target)
        os.replace(source,archive); archive.chmod(0o600)
        descriptor=os.open(source,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.close(descriptor)
        with closing(sqlite3.connect(source)) as blank: blank.executescript((root/'config/schema.sql').read_text())
    finally:
        pending.unlink(missing_ok=True)
    return {'migration_needed':True,'database':str(target),'original_backup':str(archive),
            'original_sha256':original_hash,'records_sha256':before['records_sha256'],
            'preserved_counts':before['counts'],'execution':'paused','provider_writes':0}

class Store:
    def __init__(self, path=None, initialize=True, read_only=False):
        self.path = Path(path).resolve() if path else DEFAULT_DB
        if path is None and LEGACY_DB.is_file() and any(database_snapshot(LEGACY_DB)['counts'].values()):
            raise ValueError('Saved records exist in the old tracked database. Run python3 -B gtm.py migrate-local-db once. It preserves all records privately and pauses execution. Do not copy, reset or run both databases.')
        if read_only and not self.path.is_file():
            raise ValueError('The saved attendee database is missing. No database was created.')
        if not read_only:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.policy_path = (ROOT / "config" / "policy.json" if self.path == DEFAULT_DB
                            else self.path.parent / "policy.json")
        self.db = (sqlite3.connect(self.path.as_uri() + '?mode=ro', timeout=30, uri=True)
                   if read_only else sqlite3.connect(self.path, timeout=30))
        self.active_attempts = {}
        self.execution_owner = None
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        if read_only:
            self.db.execute('PRAGMA query_only=ON')
            return
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA journal_mode=DELETE")
        if initialize:
            self.db.executescript(SCHEMA.read_text())
            os.chmod(self.path, 0o600)
    def close(self):
        self.db.close()
    def one(self, sql, args=()):
        r = self.db.execute(sql, args).fetchone()
        return dict(r) if r is not None else None
    def rows(self, sql, args=()):
        return [dict(r) for r in self.db.execute(sql, args)]
    def setting(self, name, default=None):
        row = self.one("SELECT data_json FROM settings WHERE name=?", (name,))
        return json.loads(row["data_json"]) if row else default
    def set(self, name, value):
        self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (name, encode(value)))
    def record(self, source, key, kind, value):
        self.db.execute("INSERT OR REPLACE INTO source_records VALUES (?,?,?,?,?)",
                        (source, str(key), kind, encode(value), digest(value)))
    def event(self, kind, entity, payload, key=None, at=None):
        value = {"at": at or now(), "kind": kind, "entity": entity, "payload": payload}
        event_key = key or digest(value)
        self.db.execute("INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?)",
                        (event_key, value["at"], kind, entity, encode(payload), digest(value)))
    def reserve(self, channel, recipient, domain, sender, payload, action_key, budget=None):
        """A committed intent exists before any recipient-facing request."""
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.one("SELECT idem_key FROM attempts WHERE channel=? AND recipient=? AND status NOT IN ('aborted','cancelled')", (channel, recipient)):
                raise ValueError("Existing attempt. Reconcile its result before planning another action.")
            if budget:
                provider, month, credits = budget
                if credits <= 0:
                    raise ValueError('A positive known credit reservation is required.')
                row = self.one('SELECT * FROM budgets WHERE provider=? AND month=?', (provider, month))
                if not row or row['reserved_credits'] + credits > row['limit_credits']:
                    raise ValueError('The authorized monthly credit allowance is unavailable.')
                self.db.execute('UPDATE budgets SET reserved_credits=reserved_credits+? WHERE provider=? AND month=?', (credits, provider, month))
            self.db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (action_key, channel, recipient, domain, sender, "attempting", None, now(), encode(payload), "{}"))
            self.event("attempt_reserved", recipient, {"channel": channel, "key": action_key})
        self.active_attempts[action_key] = digest(payload)
        return action_key
    def result(self, key, status, provider_id=None, receipt=None):
        self.active_attempts.pop(key, None)
        with self.db:
            self.db.execute("UPDATE attempts SET status=?,provider_id=COALESCE(?,provider_id),receipt_json=? WHERE idem_key=?",
                            (status, provider_id, encode(receipt or {}), key))
            self.event("attempt_" + status, key, {"provider_id": provider_id, "receipt": receipt or {}})
    def lease(self, owner, seconds=120):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.one("SELECT * FROM leases WHERE name='execution'")
            if row and row["expires_at"] > time.time() and row["owner"] != owner:
                raise ValueError("Another process owns execution.")
            self.db.execute("INSERT OR REPLACE INTO leases VALUES ('execution',?,?)", (owner, time.time() + seconds))
        self.execution_owner = owner
    def release(self, owner):
        with self.db:
            self.db.execute("DELETE FROM leases WHERE name='execution' AND owner=?", (owner,))
        if self.execution_owner == owner:
            self.execution_owner = None


import json
from pathlib import Path

def file_inventory(root=ROOT):
    files = sorted(p for p in Path(root).rglob('*') if (p.is_file() or p.is_symlink()) and '__pycache__' not in p.parts)
    return {'count': len(files), 'bytes': sum(p.stat().st_size for p in files),
            'files': [{'name': str(p.relative_to(root)), 'bytes': p.stat().st_size} for p in files],
            'within_limit': len(files) <= 20, 'symlinks': sum(p.is_symlink() for p in files)}

def report(store):
    from engine.checks import policy
    _, local = policy(store)
    counts = {t: store.one('SELECT COUNT(*) AS n FROM ' + t)['n'] for t in
              ('accounts', 'people', 'attempts', 'suppressions', 'bookings', 'events', 'actions')}
    attempts = store.rows('SELECT channel,status,count(*) AS records FROM attempts GROUP BY channel,status ORDER BY channel,status')
    budget = store.rows('SELECT provider,month,reserved_credits,limit_credits FROM budgets ORDER BY provider,month')
    imported = store.setting('migration_receipt', {})
    return {'execution_enabled': local.get('execution_enabled') is True,
            'commits_enabled': local.get('execution_enabled') is True,
            'migration_verified': store.setting('migration_complete', False),
            'runtime_accepted': store.setting('runtime_accepted', False),
            'counts': counts, 'attempt_states': attempts, 'budgets': budget,
            'original_counts': imported.get('critical_original_counts', {}),
            'files': file_inventory(),
            'provider_gaps': store.setting('provider_capabilities', {}),
            'old_tree_deleted': False}

def print_status(store):
    value = report(store)
    print('v5: ' + str(value['files']['count']) + ' files. Limit: 20. ' + str(round(value['files']['bytes'] / 1024 / 1024, 1)) + ' MiB.')
    print('Execution: ' + ('enabled' if value['execution_enabled'] and value['commits_enabled'] else 'paused'))
    print('Provider success is shown by exact receipts, separately from prepared work.')
    print('Accounts: ' + str(value['counts']['accounts']) + '. People records: ' + str(value['counts']['people']) + '.')
    print('Event records: ' + str(value['counts']['events']) + '. Exclusions: ' + str(value['counts']['suppressions']) + '.')
    for row in value['budgets']:
        print(row['provider'] + ' ' + row['month'] + ': ' + str(row['reserved_credits']) + '/' + str(row['limit_credits']) + ' credits reserved.')
    print('Use backup before changing your live policy.')


def set_execution(store, enabled):
    """One owner switch in policy.json. Database copies are reporting mirrors."""
    from engine.checks import policy
    authority, config = policy(store)
    if enabled and not authority.get('authority'):
        raise ValueError('Standing authority is required before resuming outreach.')
    config['execution_enabled'] = enabled
    config.pop('commits_enabled', None)
    config['file_limit'] = 20
    import tempfile
    store.policy_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=store.policy_path.parent, delete=False) as stream:
        json.dump(config, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        temporary = Path(stream.name)
    temporary.chmod(0o600)
    try:
        os.replace(temporary, store.policy_path)
    finally:
        temporary.unlink(missing_ok=True)
    with store.db:
        for key in ('execution_enabled', 'commits_enabled'):
            store.set(key, enabled)
        store.event('outreach_resumed' if enabled else 'outreach_paused', 'owner', {'control': str(store.policy_path)})
    return {'outreach': 'enabled' if enabled else 'paused', 'control': str(store.policy_path)}


def workflow(store):
    from engine.checks import execution_issues, validate
    from engine.scheduler import CHANNELS, _targets, _batch_quota
    targets, _ = _targets(store)
    channels = {name: {'prepared': 0, 'eligible': 0, 'blocked': [], 'maximum': _batch_quota(store,name,targets)}
                for name, target in targets.items()}
    for row in store.rows("SELECT * FROM actions WHERE status IN ('ready','held')"):
        name = CHANNELS.get(row['channel'])
        if name not in channels:
            continue
        issues = validate(store, row)
        channel = channels[name]; channel['prepared'] += 1
        if issues:
            channel['blocked'].append({'recipient': row['recipient'], 'reasons': issues})
        else:
            channel['eligible'] += 1
    if not store.setting('gift_gate'):
        channels['gift']['setup'] = 'Loop&Tie gift redemption is missing its verified meeting scheduler ID.'
    elif not channels['gift']['prepared']:
        channels['gift']['setup'] = 'No exact gift recipients and gift payloads have been prepared.'
    owned = store.setting('social_owned', {})
    if not owned:
        channels['social']['setup'] = 'No owned Gojiberry seat, campaign and list are configured.'
    elif all(any(step.get('type') == 'message' for step in value.get('steps', [])) for value in owned.values()):
        channels['social']['setup'] = 'Gojiberry campaigns also send automatic messages. Prepare an invitation-only campaign first.'
    elif not channels['social']['prepared']:
        channels['social']['setup'] = 'No verified owned Gojiberry contacts have been prepared for release.'
    return {'outreach_blocks': execution_issues(store), 'channels': channels,
            'steps': ['The Codex skill selects recipients and prepares exact email, gift and social actions.',
                      'The terminal command refreshes customer, deal, booking and conversation checks for those accounts.',
                      'Recheck held drafts automatically. Keep only currently eligible actions.',
                      'Claim one execution owner and one bounded batch using your configured channel maxima.',
                      'Recheck consent, identity, exclusions, copy and duplicates. Warn before exceeding daily targets.',
                      'Save each exact attempt before Gmail, Loop&Tie or Gojiberry receives the request.',
                      'Read the provider result. Reconcile unknown results without sending again.'],
            'force': 'Manual execution can run outside hours. Your hard daily caps and recipient protections remain.' if store.setting('portable_attendee',False)
                     else 'Ignore hours and internal daily limits. Keep the batch maximum and essential recipient protections.',
            'no_preparation_note': 'The terminal command cannot invent recipients or copy. Preparation belongs to the Codex skill.'}
