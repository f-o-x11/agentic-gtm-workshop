#!/usr/bin/env python3
"""Operate your own local GTM project. Exact receipts stay in SQLite."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
import os
import shutil
import subprocess

RUNTIME_ROOT = Path(__file__).resolve().parent
MINIMUM_PYTHON = (3, 10)


def probe_python(executable):
    """Read the actual interpreter version without importing project code."""
    try:
        result = subprocess.run([str(executable), '-I', '-S', '-c',
            'import json,sys; print(json.dumps({"executable":sys.executable,"version":list(sys.version_info[:3])}))'],
            capture_output=True, text=True, timeout=10, check=True)
        value = json.loads(result.stdout)
        if tuple(value['version'][:2]) >= MINIMUM_PYTHON and Path(value['executable']).is_absolute():
            return value
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        pass
    return None


def select_python(root=RUNTIME_ROOT, requested=None, reset=False, candidates=None):
    pin = Path(root).parent / 'company-motion' / '.runtime.json'
    if pin.exists() and not reset and not requested:
        try:
            saved = json.loads(pin.read_text())
            selected = probe_python(saved['executable'])
        except (OSError, ValueError, KeyError, TypeError):
            selected = None
        if not selected:
            raise ValueError('The saved Python interpreter is unavailable. Run bootstrap --reset-python to select a verified replacement.')
        return selected
    choices = [requested] if requested else (candidates if candidates is not None else [sys.executable,
        *[shutil.which('python3.' + str(v)) for v in range(16, 9, -1)], shutil.which('python3'),
        *[str(p) for p in sorted(Path('/Library/Frameworks/Python.framework/Versions').glob('*/bin/python3'), reverse=True)]])
    for candidate in dict.fromkeys(str(p) for p in choices if p):
        selected = probe_python(candidate)
        if selected:
            return selected
    raise ValueError('Python 3.10 or newer was not found. Install Python from https://www.python.org/downloads/ . Then run this same command again. No files were initialized and no software was installed.')


def launch_runtime():
    startup = len(sys.argv) > 1 and sys.argv[1] == 'bootstrap'
    requested = None
    if '--python' in sys.argv:
        pos = sys.argv.index('--python')
        if pos + 1 >= len(sys.argv):
            raise ValueError('Provide the exact Python executable after --python.')
        requested = sys.argv[pos + 1]
    selected = select_python(requested=requested, reset=startup and '--reset-python' in sys.argv)
    # Keep a virtual environment's executable path instead of resolving its symlink.
    if (tuple(sys.version_info[:2]) < MINIMUM_PYTHON or
            os.path.abspath(sys.executable) != os.path.abspath(selected['executable'])):
        os.execv(selected['executable'], [selected['executable'], '-B', str(RUNTIME_ROOT / 'gtm.py'), *sys.argv[1:]])


def bootstrap_workspace(root=RUNTIME_ROOT, company_brief=None, requested=None, reset=False):
    root = Path(root).resolve()
    folder = root.parent / 'company-motion'
    brief = Path(company_brief).expanduser().resolve() if company_brief else folder / 'COMPANY.md'
    if not brief.is_file() or not brief.read_text().strip():
        raise ValueError('Create company-motion/COMPANY.md from your actual company website first. Include the product, buyers, offer, proof and source links. Then run bootstrap again. No authority was created.')
    if folder != brief.parent or brief.name != 'COMPANY.md':
        raise ValueError('Keep the company brief at the sibling company-motion/COMPANY.md path.')
    selected = select_python(root, requested=requested, reset=reset)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    authority = '''# What this agent may do

Create and review local company briefs, skills and account pages.
Outreach, paid research, gifts, publishing, advertising and schedules remain paused.
An API key gives access. It does not approve recipients, messages or spending.
Ask the owner before any external action. Keep exact approvals and provider receipts.
The owner's private configuration and saved grants define later scope. Do not invent or expand it.
'''
    instructions = '''# Build my company GTM workflow

Read COMPANY.md before each task. Use my actual offer, buyers and source-backed proof.
After restart or context compaction, reread PROGRESS.md before choosing the next task.
If documents and runtime authority disagree, keep external actions paused and ask the owner to resolve the exact conflict.
Work on one requested workshop step. Show the output, name the next step and stop.
If the owner explicitly requests the full local build, follow ../BUILD-MY-GTM.md instead of this single-exercise stop rule. Continue local preparation between questions. Keep all authority, source and private-data checks.
After each task, append its actual step, artifact path, check result and next step to PROGRESS.md. Keep earlier entries. Record a failed check as failed.
Do not run the whole ZIP or jump ahead. Each founder or marketer works in their own project.
Use the Python executable in .runtime.json for standalone scripts. The code/gtm.py launcher also reuses it.
Keep runtime files in ../code/ and company files in this folder. Keep credentials outside both folders.
Create local files and use public official sources. Ask only for missing facts that change the output.
Check every factual claim against its source. Remove claims with no source, including invented demo lengths or recent launches.
Show mismatches between sources. Ask the owner which claim to use. Do not silently choose one.
Keep source links and claim checks with each target brief and page. Keep the first approved page unchanged when reusing its skill.
Read AUTHORITY.md before external action. Do not send, spend, publish or schedule until the owner approves exact scope.
Preserve existing company facts, instructions, approvals, attempts, exclusions and unknown provider results.
Never print keys or share recipient records. Reconcile unknown submissions before another attempt.
Use short, direct sentences. Explain unfamiliar tool names through the output they create.
'''
    created, preserved = [], []
    for name, content in [('AUTHORITY.md', authority), ('AGENTS.md', instructions)]:
        target = folder / name
        if target.exists():
            preserved.append(name)
        else:
            with target.open('x') as stream:
                stream.write(content)
            target.chmod(0o600)
            created.append(name)
    pin = folder / '.runtime.json'
    if not pin.exists() or reset or requested:
        pin.write_text(json.dumps(selected, indent=2) + '\n')
        pin.chmod(0o600)
    return {'setup_ready': True, 'company_brief': str(brief), 'python': selected,
        'python_receipt': str(pin), 'created': created, 'preserved': preserved,
        'outreach': 'paused; no authority added', 'database_writes': 0, 'provider_writes': 0,
        'next': 'Review your company brief. Continue only when you choose the next exercise.', 'stop': True}


def rule_test(store, actual_domain):
    """Inspect one saved domain exclusion, with no person or prepared action."""
    from datetime import datetime, timezone
    from engine.checks import exclusion_issues
    from engine.validation import domain, account_domains
    employer = domain(actual_domain)
    if not employer:
        raise ValueError('Use the actual saved company domain.')
    if store.one('PRAGMA query_only')['query_only'] != 1:
        raise ValueError('Rule test requires a read-only, query-only database connection.')
    store.db.execute('BEGIN')
    count = lambda: {table: store.one('SELECT count(*) AS n FROM ' + table)['n'] for table in ('actions','attempts','people')}
    before = count()
    account = store.one('SELECT * FROM accounts WHERE domain=?', (employer,))
    domains = account_domains(store, employer)
    matches = store.rows("SELECT entity_type,value,reason,source,observed_at FROM suppressions WHERE entity_type='domain' AND value IN (" +
        ','.join('?' for _ in domains) + ')', tuple(domains))
    issues = exclusion_issues(store, {'domain': employer, 'recipient': '', 'channel': 'email', 'payload': {}},
        account, datetime.now(timezone.utc)) if account else []
    after = count()
    return {'domain': employer, 'account_found': bool(account),
        'decision': 'NOT_TESTED' if not account else 'HOLD' if issues else 'NO_DOMAIN_HOLD',
        'domain_hold': bool(account and issues), 'reasons': issues if account else ['Import this actual account first.'],
        'matching_exclusions': matches,
        'domain_only': True, 'person_or_email_tested': False, 'provider_writes': 0,
        'before_counts': before, 'after_counts': after, 'database_changed': before != after or store.db.total_changes != 0,
        'note': 'This checks saved domain exclusions only. It does not prove a person or email is eligible.'}


if __name__ == '__main__':
    try:
        launch_runtime()
    except ValueError as exc:
        raise SystemExit(str(exc))

from engine.database import Store, ROOT
from engine import database as metrics

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status'); sub.add_parser('files'); sub.add_parser('check'); sub.add_parser('pacing')
    sub.add_parser('workflow'); sub.add_parser('pause'); sub.add_parser('resume')
    sub.add_parser('ready'); sub.add_parser('refresh'); sub.add_parser('review'); sub.add_parser('results')
    sub.add_parser('replies'); sub.add_parser('bookings'); sub.add_parser('research-off')
    sub.add_parser('migrate-local-db',help='Preserve old local records privately and pause execution. No provider calls.')
    rule = sub.add_parser('rule-test', help='Read one saved domain exclusion. No person or action is created.')
    rule.add_argument('--domain', required=True)
    bootstrap = sub.add_parser('bootstrap', help='Repair local workshop setup, then stop. No API keys needed.')
    bootstrap.add_argument('--company-brief', type=Path)
    bootstrap.add_argument('--python', help='Use this exact installed Python executable.')
    bootstrap.add_argument('--reset-python', action='store_true', help='Select a verified replacement interpreter.')
    for command in ('init','configure'):
        step=sub.add_parser(command); step.add_argument('--config',required=True,type=Path)
    connect=sub.add_parser('setup-google'); connect.add_argument('--client-file',required=True,type=Path)
    for command in ('approve-pilot','approve-scope'):
        approve=sub.add_parser(command); approve.add_argument('--input',required=True,type=Path)
    revoke=sub.add_parser('revoke-grant'); revoke.add_argument('--grant-id',required=True); revoke.add_argument('--reason',required=True)
    imp=sub.add_parser('import'); imp.add_argument('--kind',choices=['accounts','people','exclusions','actions','gift-gate'],required=True)
    imp.add_argument('--file',required=True,type=Path)
    paid=sub.add_parser('research-on'); paid.add_argument('--sixtyfour-credits',type=float,required=True)
    research=sub.add_parser('research'); research.add_argument('--operation',required=True); research.add_argument('--input',type=Path)
    resource=sub.add_parser('resource'); resource.add_argument('--operation',choices=['inspect','publish','publish-review','generate'],required=True)
    resource.add_argument('--key'); resource.add_argument('--input',type=Path); resource.add_argument('--file',type=Path)
    resource.add_argument('--approved-sha256')
    provision=sub.add_parser('social-provision'); provision.add_argument('--operation',required=True); provision.add_argument('--input',type=Path,required=True)
    for command in ('ads-review','ads'):
        ad=sub.add_parser(command); ad.add_argument('--operation',required=True); ad.add_argument('--input',type=Path,required=True)
        ad.add_argument('--approved-sha256')
    run = sub.add_parser('run', aliases=['orchestrate'])
    run.add_argument('--force', action='store_true',
                     help='Run one manual batch anytime, within your own hard channel and sender caps.')
    run.add_argument('--limit',type=int,help='Send at most this many prepared actions, within your hard daily caps.')
    run.add_argument('--action-key',dest='action_keys',action='append',help='Select this original approved action only. Repeat for an exact cohort; all release guards remain.')
    a = sub.add_parser('account'); a.add_argument('domain')
    p = sub.add_parser('person'); p.add_argument('email')
    e = sub.add_parser('events'); e.add_argument('--limit', type=int, default=10)
    r = sub.add_parser('reconcile'); r.add_argument('action_key')
    b = sub.add_parser('backup'); b.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.command == 'bootstrap':
        print(json.dumps(bootstrap_workspace(company_brief=args.company_brief, requested=args.python,
            reset=args.reset_python), indent=2))
        return
    if args.command == 'migrate-local-db':
        print(json.dumps(metrics.migrate_legacy_database(),indent=2))
        return
    store = Store(initialize=False, read_only=True) if args.command == 'rule-test' else Store()
    try:
        if args.command == 'status': return metrics.print_status(store)
        from tools import setup
        if args.command == 'rule-test': result=rule_test(store,args.domain)
        elif args.command in ('init','configure'): result=getattr(setup,args.command)(store,args.config)
        elif args.command=='setup-google': result=setup.setup_google(store,args.client_file)
        elif args.command in ('approve-pilot','approve-scope'): result=setup.approve_release(store,args.input,args.command=='approve-pilot')
        elif args.command=='revoke-grant': result=setup.revoke_release(store,args.grant_id,args.reason)
        elif args.command=='import': result=setup.import_records(store,args.kind,args.file)
        elif args.command=='ready': result=setup.readiness(store)
        elif args.command=='refresh':
            from engine.checks import refresh_batch
            result=refresh_batch(store)
        elif args.command=='review':
            from engine.checks import validate
            result=[{'key':r['action_key'],'channel':r['channel'],'recipient':r['recipient'],'sender':r['sender'],
                'payload':json.loads(r['payload_json']),'issues':validate(store,r)} for r in store.rows("SELECT * FROM actions WHERE status IN ('ready','held')")]
        elif args.command=='results': result=setup.results(store)
        elif args.command=='replies':
            from engine.channels.email import Replies
            result=Replies(store).refresh()
        elif args.command=='bookings':
            from engine.channels.meetings import Meetings
            result=Meetings(store).refresh()
        elif args.command in ('research-on','research-off'):
            from datetime import datetime
            from zoneinfo import ZoneInfo
            from engine.database import encode
            enabled=args.command=='research-on'
            with store.db:
                if enabled:
                    if not 0 <= args.sixtyfour_credits <= 15000: raise ValueError('Set your own monthly SixtyFour ceiling from 0 to 15000 credits')
                    month=datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m')
                    old=store.one("SELECT * FROM budgets WHERE provider='sixtyfour' AND month=?",(month,))
                    reserved=old['reserved_credits'] if old else 0
                    if args.sixtyfour_credits<reserved: raise ValueError('New budget cannot erase existing reservations')
                    store.db.execute('INSERT OR REPLACE INTO budgets VALUES (?,?,?,?,?)',('sixtyfour',month,args.sixtyfour_credits,reserved,encode({'owner_enabled':True})))
                store.set('research_enabled',enabled)
            result={'paid_research':enabled,'outreach_authorized':False,'sixtyfour_ceiling':args.sixtyfour_credits if enabled else None}
        elif args.command=='research': result=setup.research(store,args.operation,args.input)
        elif args.command=='resource':
            from engine.assets import Assets
            client=Assets(store)
            if args.operation=='inspect': result=client.inspect(args.key)
            elif args.operation in ('publish','publish-review'): result=client.publish_file(args.file,args.approved_sha256,review=args.operation=='publish-review')
            else:
                data=setup.read_json(args.input); result=client.generate(data['operation'],data['arguments'])
        elif args.command=='social-provision':
            from engine.channels.social import Social
            result=Social(store).provision(args.operation,setup.read_json(args.input))
        elif args.command in ('ads-review','ads'):
            from engine.assets import Assets
            result=Assets(store).advertising(args.operation,setup.read_json(args.input),
                approved_sha256=args.approved_sha256,review=args.command=='ads-review')
        elif args.command == 'files': result = metrics.file_inventory()
        elif args.command == 'account':
            from engine.validation import country, load
            row = store.one('SELECT domain,name,state,fit,source,observed_at,data_json FROM accounts WHERE domain=?', (args.domain.lower(),))
            if row:
                data = load(row.pop('data_json')); row.update(country=country(data.get('country')), country_input=data.get('country_input',data.get('country')))
            result = {'account': row, 'exclusions': store.rows('SELECT reason,source FROM suppressions WHERE entity_type=? AND value=?', ('domain', args.domain.lower())), 'attempts': store.rows('SELECT channel,status,provider_id,at FROM attempts WHERE domain=?', (args.domain.lower(),))}
        elif args.command == 'person':
            result = {'records': store.rows('SELECT person_key,email,profile,domain,name,title,state,source,observed_at FROM people WHERE email=?', (args.email.lower(),)), 'attempts': store.rows('SELECT channel,status,provider_id,at FROM attempts WHERE recipient=?', (args.email.lower(),)), 'exclusions': store.rows('SELECT reason,source FROM suppressions WHERE entity_type=? AND value=?', ('email', args.email.lower()))}
        elif args.command == 'events': result = store.rows('SELECT event_id,at,kind,entity FROM events ORDER BY rowid DESC LIMIT ?', (max(1, min(args.limit, 100)),))
        elif args.command == 'check':
            from engine import scheduler as scheduler
            result = {'database': store.one('PRAGMA integrity_check'), 'file_budget': metrics.file_inventory(), 'next_actions': scheduler.preview(store)}
        elif args.command in ('run', 'orchestrate'):
            from engine import scheduler as scheduler
            from engine.checks import refresh_batch
            result = scheduler.cycle(store, force=args.force or args.limit is not None, before_send=refresh_batch,limit=args.limit,action_keys=args.action_keys)
            result['workflow'] = metrics.workflow(store)
        elif args.command == 'workflow': result = metrics.workflow(store)
        elif args.command in ('pause', 'resume'): result = metrics.set_execution(store, args.command == 'resume')
        elif args.command == 'pacing':
            from engine import scheduler
            result = scheduler.pacing_status(store)
        elif args.command == 'reconcile':
            from engine import scheduler as scheduler
            result = scheduler.reconcile(store, args.action_key)
        elif args.command == 'backup':
            destination = args.destination.expanduser().resolve()
            if destination == ROOT or ROOT in destination.parents: raise ValueError('Backups belong outside the active folder.')
            destination.mkdir(parents=True, exist_ok=True, mode=0o700)
            target = destination / 'gtm.sqlite'
            if target.exists(): raise ValueError('Keep the existing restore point. Choose a fresh destination.')
            backup = sqlite3.connect(target)
            store.db.backup(backup); backup.close(); target.chmod(0o600)
            hasher = hashlib.sha256()
            with target.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''): hasher.update(block)
            sha = hasher.hexdigest()
            result = {'database': str(target), 'sha256': sha, 'source_files': metrics.file_inventory()['count']}
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    finally: store.close()

if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError) as exc: raise SystemExit(str(exc))
