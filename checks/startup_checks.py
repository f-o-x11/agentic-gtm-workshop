"""Offline regression checks for Henry's startup failures. No production imports or API calls."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import hashlib, json, tempfile, unittest, os, shutil, subprocess
from unittest.mock import patch
from engine import validation as identity
from engine.database import Store, encode, now

class StartupRepairs(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='workshop-start-'); self.folder=Path(self.temp.name)
        self.code=self.folder/'code'; self.code.mkdir(); self.motion=self.folder/'company-motion'; self.motion.mkdir()
        self.brief=self.motion/'COMPANY.md'; self.brief.write_text('Our actual product, buyers and source-backed offer.\n')
    def tearDown(self): self.temp.cleanup()
    def test_launcher_parses_under_python39_and_discovers_current_python(self):
        import ast,gtm
        ast.parse(Path(gtm.__file__).read_text(), feature_version=(3,9))
        actual=gtm.probe_python(sys.executable); self.assertGreaterEqual(tuple(actual['version'][:2]),(3,10))
        with patch.object(gtm,'probe_python',side_effect=lambda p: actual if p=='new' else None):
            self.assertEqual(gtm.select_python(self.code,candidates=['python39','new']),actual)
    def test_python39_command_reexecutes_saved_interpreter_before_engine_work(self):
        import gtm
        selected={'executable':sys.executable,'version':[3,12,0]}
        with patch.object(gtm,'select_python',return_value=selected),patch.object(gtm.sys,'version_info',(3,9,0)),patch.object(gtm.os,'execv') as execute,patch.object(gtm.sys,'argv',['gtm.py','ready']):
            gtm.launch_runtime()
            self.assertEqual(execute.call_args.args,(sys.executable,[sys.executable,'-B',str(gtm.RUNTIME_ROOT/'gtm.py'),'ready']))
    def test_saved_python_wins_over_old_default_and_invalid_pin_stops(self):
        import gtm
        actual=gtm.probe_python(sys.executable); pin=self.motion/'.runtime.json'; pin.write_text(encode(actual))
        with patch.object(gtm,'probe_python',return_value=actual) as probe:
            self.assertEqual(gtm.select_python(self.code,candidates=['python39']),actual); probe.assert_called_once_with(actual['executable'])
        with patch.object(gtm,'probe_python',return_value=None),self.assertRaisesRegex(ValueError,'reset-python'): gtm.select_python(self.code)
        pin.unlink()
        with patch.object(gtm,'probe_python',return_value=None),self.assertRaisesRegex(ValueError,'python.org'): gtm.select_python(self.code,candidates=['python39'])
        self.assertFalse(pin.exists())
    def test_company_brief_is_required_before_authority_or_database_setup(self):
        import gtm
        self.brief.unlink()
        with self.assertRaisesRegex(ValueError,'company website first'): gtm.bootstrap_workspace(self.code)
        self.assertFalse((self.motion/'AUTHORITY.md').exists()); self.assertFalse((self.motion/'.runtime.json').exists())
        self.brief.write_text(' \n')
        with self.assertRaisesRegex(ValueError,'company website first'): gtm.bootstrap_workspace(self.code)
        self.assertFalse((self.motion/'AUTHORITY.md').exists())
        from tools.setup import configure
        store=Store(self.folder/'test.sqlite'); config=self.folder/'private.json'; config.write_text('{}'); config.chmod(0o600)
        try:
            with patch('tools.setup.ROOT',self.code),self.assertRaisesRegex(ValueError,'before setup'): configure(store,config)
            self.assertEqual(store.one('SELECT count(*) AS n FROM settings')['n'],0)
        finally: store.close()
    def test_bootstrap_repairs_only_missing_files_and_preserves_owner_facts(self):
        import gtm
        before=self.brief.read_bytes(); result=gtm.bootstrap_workspace(self.code)
        self.assertEqual(result['created'],['AUTHORITY.md','AGENTS.md']); self.assertEqual(result['database_writes'],0)
        self.assertEqual(result['provider_writes'],0); self.assertTrue(result['stop']); self.assertEqual(self.brief.read_bytes(),before)
        authority=self.motion/'AUTHORITY.md'; authority.write_text('My specific existing scope. Do not overwrite.\n')
        self.assertIn('PROGRESS.md',(self.motion/'AGENTS.md').read_text())
        self.assertIn('explicitly requests the full local build',(self.motion/'AGENTS.md').read_text())
        self.assertIn('Keep all authority, source and private-data checks',(self.motion/'AGENTS.md').read_text())
        instructions=self.motion/'AGENTS.md'; instructions.write_text('My existing company instructions.\n'); saved=instructions.read_bytes()
        second=gtm.bootstrap_workspace(self.code); self.assertEqual(second['created'],[]); self.assertEqual(instructions.read_bytes(),saved)
        authority.unlink(); third=gtm.bootstrap_workspace(self.code); self.assertEqual(third['created'],['AUTHORITY.md'])
        self.assertEqual(instructions.read_bytes(),saved); self.assertFalse((self.code/'data').exists())
    def test_repeated_init_repairs_documents_without_changing_grants_or_history(self):
        from tools.setup import init
        store=Store(self.folder/'test.sqlite')
        try:
            with store.db:
                store.set('portable_initialized',True); store.set('policy',{'authority':'Existing actual owner scope'})
                store.set('pilot_approval',{'digest':'keep'}); store.event('owner_grant','owner',{'keep':True})
                store.record('owner.release','pilot','approved_release',{'authority':'Keep existing grant'})
                store.db.execute('INSERT INTO history VALUES (?,?,?,?,?,?)',('past','buyer@example.org','example.org',now(),'sent','{}'))
                store.db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)',('unknown','email','buyer@example.org','example.org','owner@example.org','uncertain',None,now(),'{}','{}'))
            tables=('settings','events','history','attempts','source_records')
            before={table:store.rows('SELECT * FROM '+table) for table in tables}
            with patch('tools.setup.ROOT',self.code): result=init(store,self.folder/'unused-config.json')
            self.assertTrue(result['existing_project_retained'])
            for table in tables: self.assertEqual(store.rows('SELECT * FROM '+table),before[table])
            self.assertTrue((self.motion/'AUTHORITY.md').exists())
        finally: store.close()
    def test_country_aliases_match_existing_records_and_keep_unknowns_held(self):
        for short in ('US','USA','U.S.',' united states '):
            self.assertEqual(identity.country(short),'United States')
            account={'data_json':encode({'country':short})}
            self.assertEqual(identity.account_issues(account,{'recipient_company_countries':['United States']}),[])
            self.assertEqual(identity.account_issues({'data_json':encode({'country':'United States'})},{'recipient_company_countries':[short]}),[])
        self.assertEqual(identity.country('Atlantis'),'Atlantis')
        self.assertIn('outside authorized scope',identity.account_issues({'data_json':encode({'country':'Atlantis'})},{'recipient_company_countries':['US']})[0])
    def test_matching_unknown_country_cannot_authorize_account_and_valid_iso_names_work(self):
        for value in ('Atlantis','Unknown','N/A'):
            self.assertTrue(identity.account_issues({'data_json':encode({'country':value})},{'recipient_company_countries':[value]}))
        for value in ('India','Italy','Spain'):
            self.assertEqual(identity.account_issues({'data_json':encode({'country':value.lower()})},{'recipient_company_countries':[value]}),[])
        from tools.setup import configure
        store=Store(self.folder/'test.sqlite'); config=self.folder/'private.json'
        config.write_text(encode({'company':{'name':'Owned','domain':'owned.example'},
            'policy':{'authority':'Actual offline scope','senders':{'owner@owned.example':11},'recipient_company_countries':['Atlantis']}})); config.chmod(0o600)
        try:
            with patch('tools.setup.ROOT',self.code),self.assertRaisesRegex(ValueError,'recognized country'): configure(store,config)
            self.assertEqual(store.one('SELECT count(*) AS n FROM settings')['n'],0)
            self.assertFalse(store.policy_path.exists())
        finally: store.close()
    def test_imported_account_does_not_claim_initialized_or_skip_private_config(self):
        from tools.setup import init
        store=Store(self.folder/'test.sqlite'); config=self.folder/'private.json'
        config.write_text(encode({'company':{'name':'Owned','domain':'owned.example'},
            'policy':{'authority':'Actual offline scope','senders':{'owner@owned.example':11},'recipient_company_countries':['US']}})); config.chmod(0o600)
        try:
            with store.db:
                store.db.execute('INSERT INTO accounts VALUES (?,?,?,?,?,?,?)',('target.example','Target','catalog',None,'offline',now(),encode({'country':'US'})))
            before=store.rows('SELECT * FROM accounts')
            with patch('tools.setup.ROOT',self.code): result=init(store,config)
            self.assertTrue(result['initialized']); self.assertEqual(result['existing_accounts_preserved'],1)
            self.assertTrue(store.setting('portable_initialized')); self.assertEqual(store.setting('company')['domain'],'owned.example')
            self.assertEqual(store.rows('SELECT * FROM accounts'),before)
            self.assertEqual(store.one('SELECT count(*) AS n FROM sender_consent')['n'],1)
        finally: store.close()
    def test_bootstrap_next_task_and_restart_contract_match_startup_prompt(self):
        import gtm
        result=gtm.bootstrap_workspace(self.code)
        self.assertEqual(result['next'],'Review your company brief. Continue only when you choose the next exercise.')
        instructions=(self.motion/'AGENTS.md').read_text()
        self.assertIn('After restart or context compaction, reread PROGRESS.md',instructions)
        self.assertIn('If documents and runtime authority disagree, keep external actions paused',instructions)
    def test_import_reports_canonical_country_and_retains_original_input(self):
        from tools.setup import import_records
        store=Store(self.folder/'test.sqlite'); path=self.folder/'accounts.json'
        path.write_text(encode([{'domain':'owned.example','name':'Owned','country':'USA'}]))
        try:
            result=import_records(store,'accounts',path); self.assertEqual(result['countries'][0]['country'],'United States')
            row=identity.load(store.one('SELECT data_json FROM accounts')['data_json'])
            self.assertEqual(row['country_input'],'USA'); self.assertEqual(row['country'],'United States')
        finally: store.close()
    def test_configured_US_scope_matches_United_States_record_and_reports_readiness(self):
        from tools.setup import configure,readiness
        store=Store(self.folder/'test.sqlite'); config=self.folder/'private.json'
        config.write_text(encode({'company':{'name':'Owned','domain':'owned.example'},
            'policy':{'authority':'Actual offline scope','senders':{'owner@owned.example':11},'recipient_company_countries':['US','USA']}})); config.chmod(0o600)
        try:
            with patch('tools.setup.ROOT',self.code):
                result=configure(store,config); ready=readiness(store)
            self.assertEqual(result['recipient_company_countries'],['United States']); self.assertEqual(ready['recipient_company_countries'],['United States'])
            self.assertEqual(identity.account_issues({'data_json':encode({'country':'United States'})},store.setting('policy')),[])
            self.assertTrue(identity.account_issues({'data_json':encode({'country':'Canada'})},store.setting('policy')))
        finally: store.close()
    def test_fresh_copy_bootstrap_and_repeat_have_twenty_files_and_empty_database(self):
        import gtm
        root=Path(gtm.__file__).parent; fresh=self.folder/'fresh'; shutil.copytree(root,fresh/'code'); motion=fresh/'company-motion'; motion.mkdir()
        (motion/'COMPANY.md').write_text(self.brief.read_text()); db=fresh/'code/data/gtm.sqlite'; before=hashlib.sha256(db.read_bytes()).hexdigest()
        command=[sys.executable,'-B',str(fresh/'code/gtm.py'),'bootstrap','--company-brief',str(motion/'COMPANY.md')]
        first=subprocess.run(command,cwd=fresh/'code',capture_output=True,text=True,timeout=20,check=True)
        self.assertEqual(json.loads(first.stdout)['created'],['AUTHORITY.md','AGENTS.md'])
        second=subprocess.run(command,cwd=fresh/'code',capture_output=True,text=True,timeout=20,check=True)
        self.assertEqual(json.loads(second.stdout)['created'],[]); self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(),before)
        self.assertEqual(len([p for p in (fresh/'code').rglob('*') if p.is_file()]),20)
    def test_readonly_store_cannot_create_or_write_database(self):
        import sqlite3
        missing=self.folder/'missing'/'new.sqlite'
        with self.assertRaisesRegex(ValueError,'missing'): Store(missing,read_only=True)
        self.assertFalse(missing.parent.exists())
        path=self.folder/'saved.sqlite'; writable=Store(path); writable.close(); before=path.read_bytes()
        readonly=Store(path,read_only=True)
        try:
            self.assertEqual(readonly.one('PRAGMA query_only')['query_only'],1)
            with self.assertRaises(sqlite3.OperationalError): readonly.set('forbidden',True)
        finally: readonly.close()
        self.assertEqual(path.read_bytes(),before)
    def test_rule_test_uses_saved_domain_without_person_or_action(self):
        import gtm
        path=self.folder/'saved.sqlite'; writable=Store(path)
        with writable.db:
            writable.db.execute('INSERT INTO accounts VALUES (?,?,?,?,?,?,?)',('excluded.example','Excluded','catalog',None,'offline',now(),encode({'country':'US'})))
            writable.db.execute('INSERT INTO suppressions VALUES (?,?,?,?,?,?)',('domain','excluded.example','Owner exclusion','offline',now(),'{}'))
        writable.close(); before=path.read_bytes(); readonly=Store(path,read_only=True)
        try:
            result=gtm.rule_test(readonly,'excluded.example')
            self.assertEqual(result['decision'],'HOLD'); self.assertEqual(result['matching_exclusions'][0]['reason'],'Owner exclusion')
            self.assertEqual(result['before_counts'],{'actions':0,'attempts':0,'people':0}); self.assertEqual(result['before_counts'],result['after_counts'])
            self.assertFalse(result['database_changed']); self.assertFalse(result['person_or_email_tested'])
        finally: readonly.close()
        self.assertEqual(path.read_bytes(),before)
    def test_actual_fresh_cli_rule_test_is_readonly_and_missing_account_is_not_tested(self):
        import gtm
        fresh=self.folder/'rule-copy'; shutil.copytree(Path(gtm.__file__).parent,fresh/'code')
        db=fresh/'company-motion/gtm.sqlite'; store=Store(db)
        with store.db:
            store.db.execute('INSERT INTO accounts VALUES (?,?,?,?,?,?,?)',('excluded.example','Excluded','catalog',None,'offline',now(),encode({'country':'US'})))
            store.db.execute('INSERT INTO suppressions VALUES (?,?,?,?,?,?)',('domain','excluded.example','Owner exclusion','offline',now(),'{}'))
        store.close(); before=db.read_bytes()
        command=[sys.executable,'-B',str(fresh/'code/gtm.py'),'rule-test','--domain']
        held=subprocess.run(command+['excluded.example'],cwd=fresh/'code',capture_output=True,text=True,timeout=20,check=True)
        value=json.loads(held.stdout); self.assertEqual(value['decision'],'HOLD'); self.assertFalse(value['database_changed'])
        missing=subprocess.run(command+['missing.example'],cwd=fresh/'code',capture_output=True,text=True,timeout=20,check=True)
        self.assertEqual(json.loads(missing.stdout)['decision'],'NOT_TESTED'); self.assertEqual(db.read_bytes(),before)
        self.assertEqual(len([p for p in (fresh/'code').rglob('*') if p.is_file()]),20)
    def test_repository_credentials_reject_root_and_symlink_destinations(self):
        from tools.setup import credential_path
        (self.folder/'.git').mkdir(); secret=self.folder/'private-api-key.txt'; secret.write_text('offline'); secret.chmod(0o600)
        with patch('tools.setup.ROOT',self.code):
            with self.assertRaisesRegex(ValueError,'outside this cloned repository'): credential_path(secret)
            with tempfile.TemporaryDirectory(prefix='outside-workshop-') as outside:
                outside=Path(outside); link=outside/'linked-key.txt'; link.symlink_to(secret)
                with self.assertRaisesRegex(ValueError,'outside this cloned repository'): credential_path(link)
                allowed=outside/'private-key.txt'; allowed.write_text('offline'); allowed.chmod(0o600)
                self.assertEqual(credential_path(allowed),allowed.resolve())
    def test_default_records_stay_outside_the_tracked_template(self):
        import gtm
        from engine import database
        fresh=self.folder/'private-db-copy'; shutil.copytree(Path(gtm.__file__).parent,fresh/'code')
        template=fresh/'code/data/gtm.sqlite'; before=template.read_bytes()
        command=[sys.executable,'-B',str(fresh/'code/gtm.py'),'status']
        subprocess.run(command,cwd=fresh/'code',capture_output=True,text=True,timeout=20,check=True)
        private=fresh/'company-motion/gtm.sqlite'; self.assertTrue(private.is_file()); self.assertEqual(private.stat().st_mode & 0o777,0o600)
        self.assertEqual(template.read_bytes(),before); self.assertEqual(len([p for p in (fresh/'code').rglob('*') if p.is_file()]),20)
    def test_explicit_migration_preserves_all_records_and_holds_duplicate_databases(self):
        import gtm
        from engine import database
        fresh=self.folder/'legacy-copy'; shutil.copytree(Path(gtm.__file__).parent,fresh/'code')
        root=fresh/'code'; legacy=root/'data/gtm.sqlite'; target=fresh/'company-motion/gtm.sqlite'; store=Store(legacy)
        with store.db:
            store.set('policy',{'authority':'Actual offline owner authority'}); store.set('pilot_approval',{'digest':'preserve'})
            store.record('owner.release','pilot','approved_release',{'authority':'Preserve this exact grant'})
            store.db.execute('INSERT INTO history VALUES (?,?,?,?,?,?)',('old','buyer@example.org','example.org',now(),'sent','{}'))
            store.db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)',('pending','email','buyer@example.org','example.org','owner@example.org','uncertain',None,now(),'{}','{}'))
        store.close(); before=database.database_snapshot(legacy); original=legacy.read_bytes()
        with patch.object(database,'LEGACY_DB',legacy),patch.object(database,'DEFAULT_DB',target),patch.object(database,'ROOT',root):
            with self.assertRaisesRegex(ValueError,'migrate-local-db'): Store()
            result=database.migrate_legacy_database(root)
            self.assertEqual(database.database_snapshot(target),before); self.assertEqual(Path(result['original_backup']).read_bytes(),original)
            self.assertFalse(any(database.database_snapshot(legacy)['counts'].values()))
            self.assertFalse(json.loads((root/'config/policy.json').read_text())['execution_enabled'])
            migrated=Store(); self.assertEqual(migrated.setting('pilot_approval'),{'digest':'preserve'}); migrated.close()
            self.assertFalse(database.migrate_legacy_database(root)['migration_needed'])
            replacement=Store(legacy); replacement.set('do-not-reset',True); replacement.db.commit(); replacement.close()
            with self.assertRaisesRegex(ValueError,'already exists'): database.migrate_legacy_database(root)
            self.assertEqual(database.database_snapshot(target),before)
    @unittest.skipUnless(Path('/usr/bin/python3').is_file(),'Mac system Python is unavailable')
    def test_actual_mac_python39_bootstrap_reuses_saved_newer_python(self):
        import gtm
        version=subprocess.run(['/usr/bin/python3','--version'],capture_output=True,text=True,check=True).stdout.strip()
        if not version.startswith('Python 3.9.'): self.skipTest('This host does not have system Python 3.9')
        fresh=self.folder/'legacy'; shutil.copytree(Path(gtm.__file__).parent,fresh/'code'); motion=fresh/'company-motion'; motion.mkdir()
        (motion/'COMPANY.md').write_text(self.brief.read_text()); before=(fresh/'code/data/gtm.sqlite').read_bytes()
        command=['/usr/bin/python3','-B',str(fresh/'code/gtm.py'),'bootstrap','--company-brief',str(motion/'COMPANY.md')]
        first=subprocess.run(command+['--python',sys.executable],capture_output=True,text=True,timeout=20,check=True)
        pin=json.loads(first.stdout)['python']; self.assertGreaterEqual(tuple(pin['version'][:2]),(3,10))
        second=subprocess.run(command,capture_output=True,text=True,timeout=20,check=True)
        self.assertEqual(json.loads(second.stdout)['python'],pin); self.assertEqual((fresh/'code/data/gtm.sqlite').read_bytes(),before)
        failed=self.folder/'unsupported'; shutil.copytree(Path(gtm.__file__).parent,failed/'code')
        old=['/usr/bin/python3','-B',str(failed/'code/gtm.py'),'bootstrap','--python','/usr/bin/python3']
        result=subprocess.run(old,capture_output=True,text=True,timeout=20)
        self.assertNotEqual(result.returncode,0); self.assertIn('https://www.python.org/downloads/',result.stderr)
        self.assertFalse((failed/'company-motion').exists()); self.assertEqual((failed/'code/data/gtm.sqlite').read_bytes(),before)
if __name__ == '__main__': unittest.main(verbosity=2)
