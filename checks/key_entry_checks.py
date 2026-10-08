import contextlib
import importlib.util
import io
import os
import warnings
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('save_api_key',HERE/'save-api-key.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class KeyHelperChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.repo=self.base/'repo';self.repo.mkdir()
        self.private=self.base/'private';self.private.mkdir(mode=0o700)
        self.config=self.private/'config.json'
        self.original={'company':{'name':'Test company'},'policy':{'senders':{'owner@example.test':11}},'credential_files':{},'settings':{'keep':'unchanged'},'grants':['preserve']}
        self.config.write_text(json.dumps(self.original));self.config.chmod(0o600)
    def tearDown(self):self.temp.cleanup()
    def test_save_private_key_and_preserve_configuration(self):
        target=module.save_key('zerobounce',self.config,'FAKE_TEST_VALUE_DO_NOT_USE',self.repo)
        self.assertEqual(target.read_text(),'FAKE_TEST_VALUE_DO_NOT_USE\n')
        self.assertEqual(target.stat().st_mode&0o777,0o600)
        self.assertEqual(target.parent.stat().st_mode&0o777,0o700)
        config=json.loads(self.config.read_text())
        for field in ('company','policy','settings','grants'):self.assertEqual(config[field],self.original[field])
        self.assertEqual(config['credential_files']['zerobounce'],str(target))
        self.assertNotIn('FAKE_TEST',self.config.read_text())
    def test_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError,'Unsupported provider'):module.save_key('../unapproved',self.config,'FAKE',self.repo)
    def test_reject_cloned_repository(self):
        with self.assertRaisesRegex(ValueError,'outside'):module.save_key('netlify',self.repo/'config.json','FAKE',self.repo)
    def test_reject_symlink(self):
        linked=self.private/'linked.json';linked.symlink_to(self.config)
        with self.assertRaisesRegex(ValueError,'symbolic'):module.save_key('netlify',linked,'FAKE',self.repo)
    def test_reject_key_path_in_repository(self):
        data=self.original.copy();data['credential_files']={'netlify':str(self.repo/'key')};self.config.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'outside'):module.save_key('netlify',self.config,'FAKE',self.repo)
    def test_key_cannot_overwrite_config_or_other_provider(self):
        for collision in (str(self.config), str(self.private/'shared.key')):
            data=dict(self.original);data['credential_files']={'netlify':collision,'zerobounce':collision}
            self.config.write_text(json.dumps(data));before=self.config.read_text()
            with self.assertRaisesRegex(ValueError,'replace the private config|own key file'):
                module.save_key('netlify',self.config,'FAKE',self.repo)
            self.assertEqual(self.config.read_text(),before)
    def test_hardlink_alias_cannot_replace_another_provider(self):
        first=self.private/'first.key'; first.write_text('ORIGINAL_TEST_KEY'); first.chmod(0o600)
        second=self.private/'second.key'; os.link(first,second)
        data=dict(self.original);data['credential_files']={'zerobounce':str(first),'netlify':str(second)}
        self.config.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'own key file'):module.save_key('netlify',self.config,'FAKE',self.repo)
        self.assertEqual(first.read_text(),'ORIGINAL_TEST_KEY');self.assertEqual(second.read_text(),'ORIGINAL_TEST_KEY')
    def test_copied_outer_whitespace_is_trimmed(self):
        target=module.save_key('netlify',self.config,'  \tCOPYKEYFIXTURE1234567890\r\n',self.repo)
        self.assertEqual(target.read_text(),'COPYKEYFIXTURE1234567890\n')
    def test_quote_wrapped_key_is_rejected_without_writing(self):
        for key in ('"COPYKEYFIXTURE"', "'COPYKEYFIXTURE'", '  "COPYKEYFIXTURE"  '):
            before=self.config.read_text()
            with self.assertRaisesRegex(ValueError,'quote marks'):module.save_key('netlify',self.config,key,self.repo)
            self.assertEqual(self.config.read_text(),before);self.assertFalse((self.private/'keys').exists())
    def test_config_hardlink_alias_cannot_be_overwritten(self):
        alias=self.private/'config-alias.key';os.link(self.config,alias)
        data=dict(self.original);data['credential_files']={'netlify':str(alias)}
        self.config.write_text(json.dumps(data));before=self.config.read_text()
        with self.assertRaisesRegex(ValueError,'private config'):module.save_key('netlify',self.config,'FAKE',self.repo)
        self.assertEqual(self.config.read_text(),before)
    def test_getpass_warning_stops_before_fallback_echo(self):
        def unsupported_echo(prompt):
            warnings.warn('Cannot disable echo',module.getpass.GetPassWarning)
            raise AssertionError('Echo fallback must never run')
        with patch('sys.argv',['save-api-key.py','--provider','netlify','--config',str(self.config)]),patch('sys.stdin.isatty',return_value=True),patch('getpass.getpass',side_effect=unsupported_echo),contextlib.redirect_stderr(io.StringIO()) as error:
            with self.assertRaises(SystemExit) as result:module.main()
        self.assertEqual(result.exception.code,2);self.assertIn('cannot hide key entry',error.getvalue())
        self.assertFalse((self.private/'keys').exists());self.assertEqual(json.loads(self.config.read_text()),self.original)
    def test_reject_shared_config_permissions(self):
        self.config.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'0600'):module.save_key('netlify',self.config,'FAKE',self.repo)
    def test_reject_multiline_or_empty_key(self):
        for key in ('','\n','fake\nkey','Bearer fake'):
            with self.assertRaises(ValueError):module.save_key('netlify',self.config,key,self.repo)
    def test_replace_requires_terminal_confirmation(self):
        target=module.save_key('netlify',self.config,'ORIGINAL_TEST_VALUE',self.repo)
        with patch('sys.argv',['save-api-key.py','--provider','netlify','--config',str(self.config)]),patch('sys.stdin.isatty',return_value=True),patch('builtins.input',return_value='n'),patch('getpass.getpass') as hidden,contextlib.redirect_stdout(io.StringIO()) as out:
            module.main()
        hidden.assert_not_called();self.assertEqual(target.read_text(),'ORIGINAL_TEST_VALUE\n');self.assertIn('Kept',out.getvalue())
    def test_no_key_in_terminal_output(self):
        with patch('sys.argv',['save-api-key.py','--provider','netlify','--config',str(self.config)]),patch('sys.stdin.isatty',return_value=True),patch('getpass.getpass',return_value='HIDDEN_TEST_VALUE'),contextlib.redirect_stdout(io.StringIO()) as out:
            module.main()
        self.assertNotIn('HIDDEN_TEST_VALUE',out.getvalue());self.assertIn('No provider was called',out.getvalue())
    def test_reject_noninteractive_entry(self):
        with patch('sys.argv',['save-api-key.py','--provider','netlify','--config',str(self.config)]),patch('sys.stdin.isatty',return_value=False),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:module.main()
        self.assertEqual(result.exception.code,2)

if __name__=='__main__':unittest.main()
