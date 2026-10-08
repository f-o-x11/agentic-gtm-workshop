#!/usr/bin/env python3
"""Save one provider key privately. No network calls or provider actions."""
import argparse
import getpass
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import warnings

PROVIDERS = ('zerobounce', 'sixtyfour', 'exa', 'apify', 'triguna', 'moltsets',
             'rocketreach', 'instantly', 'calendly', 'hubspot', 'loop_and_tie',
             'gojiberry', 'metadata', 'netlify')
DEFAULT_CONFIG = Path.home() / '.local/share/agentic-gtm/workshop-private/config.json'


def private_path(raw, repository):
    repository = Path(repository).resolve()
    candidate = Path(raw).expanduser()
    if candidate.is_symlink():
        raise ValueError('Use an actual private file, not a symbolic link.')
    path = candidate.resolve()
    if path == repository or repository in path.parents:
        raise ValueError('Keep the file outside this workshop folder.')
    if path.exists() and (not path.is_file() or path.stat().st_mode & 0o777 != 0o600):
        raise ValueError('Private files must have permissions 0600.')
    return path


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.stat().st_mode & 0o777 != 0o700:
        raise ValueError('Use a private folder with permissions 0700; existing permissions were kept.')
    fd, temporary = tempfile.mkstemp(prefix='.workshop-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_key(provider, config_path, key, repository):
    if provider not in PROVIDERS:
        raise ValueError('Unsupported provider name.')
    config_path = private_path(config_path, repository)
    if not config_path.is_file():
        raise ValueError('First use the Prepare private folder prompt in API-CONNECTIONS.html.')
    config = json.loads(config_path.read_text())
    if not isinstance(config, dict) or not isinstance(config.get('credential_files', {}), dict):
        raise ValueError('The private config must contain a credential_files object.')
    if not config.get('company', {}).get('name') or not config.get('policy', {}).get('senders'):
        raise ValueError('First complete private setup for your company and sender.')
    if not isinstance(key, str):
        raise ValueError('Paste only the single key value.')
    key = key.strip()
    if not key or any(c.isspace() for c in key):
        raise ValueError('Paste the single key value, without a label or extra lines.')
    if key[0] in ('"', "'") or key[-1] in ('"', "'"):
        raise ValueError('Remove the surrounding quote marks and paste only the key value.')
    keys = config.setdefault('credential_files', {})
    target = private_path(keys.get(provider) or config_path.parent / 'keys' / (provider + '.key'), repository)
    if target == config_path or (target.exists() and os.path.samefile(target, config_path)):
        raise ValueError('A key file cannot replace the private config.')
    for name, value in keys.items():
        if name != provider and value:
            other = private_path(value, repository)
            if other == target or (other.exists() and target.exists() and os.path.samefile(other, target)):
                raise ValueError('Each provider needs its own key file; another provider already uses this path.')
    atomic_write(target, key.strip() + '\n')
    keys[provider] = str(target)
    atomic_write(config_path, json.dumps(config, indent=2) + '\n')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=PROVIDERS, required=True)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.exit(2, 'Open your own terminal for this command. Do not paste a key into your agent chat.\n')
    repository = Path(__file__).resolve().parent
    try:
        config_path = private_path(args.config, repository)
        if not config_path.is_file():
            raise ValueError('First use the Prepare private folder prompt in API-CONNECTIONS.html.')
        config = json.loads(config_path.read_text())
        existing = config.get('credential_files', {}).get(args.provider)
        if existing and Path(existing).expanduser().exists():
            if input('A saved key exists. Replace only this provider key? [y/N] ').strip().lower() != 'y':
                print('Kept the existing key.')
                return
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            key = getpass.getpass('Paste your ' + args.provider + ' key here (hidden), then press Enter: ')
        target = save_key(args.provider, config_path, key, repository)
        print('Saved privately: ' + str(target))
        print('Now ask your local agent to run this from code/:')
        print('python3 -B gtm.py configure --config ' + shlex.quote(str(config_path)))
        print('No provider was called. Nothing was sent. Check the connection next.')
    except getpass.GetPassWarning:
        parser.exit(2, 'This terminal cannot hide key entry. Nothing was saved. Use a normal terminal and try again.\n')
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
