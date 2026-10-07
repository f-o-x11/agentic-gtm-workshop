"""Check distribution files without reading credentials or contacting providers."""
from pathlib import Path
import json
import re
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
patterns = {
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'API key': r'sk-(?:or-v1-|proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
    'Google API key': r'AIza[\w-]{30,}',
    'Google token': r'(?:ya29\.|1//)[A-Za-z0-9_-]{25,}',
    'AWS key': r'(?:AKIA|ASIA)[A-Z0-9]{16}',
    'GitHub token': r'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,})',
    'JWT': r'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}',
    'Stripe key': r'(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}',
    'bearer token': r'Bearer\s+[A-Za-z0-9._-]{30,}',
}

def main():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
    files = [ROOT / name for name in result.stdout.decode().split('\0') if name]
    issues = []
    runtime = [p for p in files if p.relative_to(ROOT).parts[0] == 'code']
    if len(runtime) != 20:
        issues.append('Runtime must contain exactly 20 tracked files.')
    for path in files:
        relative = path.relative_to(ROOT)
        if any(part in ('private-author-reference', 'actual-source', '__pycache__', '.venv') for part in relative.parts):
            issues.append(str(relative) + ': private or generated directory')
        if relative.parts[0] == 'company-motion' and relative.name != '.gitkeep':
            issues.append(str(relative) + ': participant data must stay local')
        text = path.read_bytes().decode('utf-8', errors='ignore')
        for label, pattern in patterns.items():
            if re.search(pattern, text):
                issues.append(str(relative) + ': ' + label + ' signature')
        if ('/' + 'Users' + '/machine/') in text:
            issues.append(str(relative) + ': private author path')
    env = ROOT / 'api-templates/credentials.env.example'
    for line in env.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line and line.split('=', 1)[1].strip():
            issues.append('Credential environment template has a nonempty value.')
    oauth = json.loads((ROOT / 'api-templates/google-oauth.template.json').read_text())
    if any(oauth.get(key) for key in ('email', 'client_id', 'client_secret', 'refresh_token')):
        issues.append('OAuth template contains an identity or credential.')
    salesforce = (ROOT / 'api-templates/salesforce-oauth.template.txt').read_text()
    if any(line.split('=', 1)[1].strip() for line in salesforce.splitlines() if '=' in line and not line.lstrip().startswith('#')):
        issues.append('Salesforce template contains a nonempty value.')
    db = sqlite3.connect('file:' + str(ROOT / 'code/data/gtm.sqlite') + '?mode=ro', uri=True)
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    empty = len(tables) == 16 and all(db.execute('SELECT count(*) FROM "' + t.replace('"', '""') + '"').fetchone()[0] == 0 for t in tables)
    db.close()
    if not empty:
        issues.append('Distribution database must have 16 empty tables.')
    if 'company-motion/gtm.sqlite' in [str(p.relative_to(ROOT)) for p in files]:
        issues.append('The private working database must never be tracked.')
    workflow=(ROOT/'.github/workflows/workshop-checks.yml').read_text()
    for action in re.findall(r'uses:\s*([^\s#]+)',workflow):
        if not re.fullmatch(r'[^@]+@[0-9a-f]{40}',action):
            issues.append('Every workflow action must use an exact commit SHA.')
    print(json.dumps({'passed': not issues, 'tracked_files': len(files), 'runtime_files': len(runtime), 'empty_tables': len(tables) if empty else None, 'issues': issues}, indent=2))
    return 1 if issues else 0

if __name__ == '__main__':
    sys.exit(main())
