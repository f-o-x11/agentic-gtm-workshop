"""Build the separate workshop connection reference. No provider calls."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / 'api-guide.json').read_text())
lines = ['# Connect your own tools', '', 'Reviewed October 6, 2026.', '', data['summary'], '',
         'You supply your own accounts. The shipped templates contain no keys, recipients or production account IDs.', '',
         'The runtime does not consume an OpenAI, Anthropic or OpenRouter model key. Your separate AI coding agent uses its own signed-in account. Do not buy every provider in this reference.', '',
         '## 1. What you need for each part', '', '| Part | Have ready | Paid API needed? |', '|---|---|---|']
for part in data['parts']:
    lines.append('| ' + str(part['part']) + ': ' + part['name'] + ' | ' + '; '.join(part['connections']) + ' | ' + ('; '.join(part['paid_apis']) if part['paid_apis'] else 'No.') + ' |')
lines.extend(['', '## 2. Where credentials go', '',
              'Keep company context, skills, pages and private recipient inputs in company-motion/, beside code/. Keep filled config and tokens in a private directory outside both folders. Add their file paths under `credential_files` in your private config.', '',
              'Set the private directory to mode 0700 and each actual config or token file to mode 0600. Use the package\'s `code/evidence/workshop-config.example.json` as the config contract. Keep filled config and credential files out of the participant ZIP.', '',
              '`credentials.env.example` is an optional export-name reference. The adapter does not load `.env` files. A file that sits on disk does nothing until the process receives its variables or its private config references the token paths.', '',
              'A secret unlocks an account connection. It does not prove ownership, grant an outreach budget, populate recipients, or remove a hold.', '',
              '## 3. Connection sequence', '',
              '1. Build and open your local company page. You need no provider key for this.',
              '2. Connect your own Google mailbox and primary calendar. Inspect the returned mailbox identity.',
              '3. Import your complete, current customer, deal, opt-out and relationship exclusions.',
              '4. Add one research source only when you need it. Inspect current employer evidence.',
              '5. Validate exact work emails. Confirm credit balance before paid calls.',
              '6. Prepare the own-sender test and ten prospect emails for ten distinct companies. Read all eleven exact messages and pin their actual keys with approve-pilot.',
              '7. Select the original approved self-test key with run --action-key KEY --limit 1. Read its exact Gmail Sent match. Then select only the ten pinned prospect keys. The eleven-message limit applies across days.',
              '8. Optionally connect Gojiberry or Loop & Tie for the chosen extension. Confirm owned resources and funding. Dispatch each original approved channel key with --action-key, then reconcile that same key.',
              '9. Connect existing Calendly, CRM and website-form sources when your company uses them.',
              '10. Add Metadata creative generation or the supported Netlify publish method after the core email path works.', '',
              '## 4. Read-only connection prompt', '', 'Copy this into the same workshop project:', '', '```text',
              'Read the package README and my private config. Check only the connections needed for the current lesson.',
              'Do not print tokens or send email, invitations, gifts, form submissions, or ad campaigns.',
              'Read the provider account and the exact configured resources. Check that they belong to my company.',
              'Show a short table: tool, what it enables, actual proof, and one missing setup item.',
              'Keep failed and unused connections separate. Do not claim a connection from a saved file name.',
              'Save the real read receipts privately. Continue building the lesson artifact when a provider is unavailable.',
              '```', '', '## 5. Provider reference', ''])
for index, p in enumerate(data['providers'], 1):
    lines.extend(['### 5.' + str(index) + '. ' + p['name'], '',
                  '**When:** ' + p['priority'] + '. Parts ' + ', '.join(map(str, p['parts'])) + '.', '',
                  '**Code support:** ' + p['status'] + '.', '',
                  '**Entering it enables:** ' + p['enables'], '',
                  '**Limits:** ' + p['does_not_enable'], '',
                  '**Credential:** ' + p['secret_type'] + '.', '',
                  '**Config, input or setup fields:** ' + ', '.join('`' + s + '`' for s in p['settings']) + '.', '',
                  '**Minimum account or credits:** ' + p['minimum'], '', 'Setup:', ''])
    lines.extend(str(i) + '. ' + s for i, s in enumerate(p['steps'], 1))
    lines.extend(['', '**Connection proof:** ' + p['proof'], '', '**Provider wait:** ' + p['wait'], '',
                  '**Fallback:** ' + p['fallback'], '', '**Blank or structural example:**', '', '```json',
                  json.dumps(p['schema'], ensure_ascii=False, indent=2), '```', ''])
    if p['env']:
        lines.extend(['**Optional exported variable names:** ' + ', '.join('`' + name + '`' for name in p['env']) + '.', ''])
    if p['notes']:
        lines.extend(['Checks:', ''])
        lines.extend(str(i) + '. ' + s for i, s in enumerate(p['notes'], 1))
        lines.append('')
    if p['source']:
        lines.extend(['Official sources: ' + ', '.join('[' + s['label'] + '](' + s['url'] + ')' for s in p['source']) + '.', ''])
    lines.extend(['Local contract: ' + ', '.join('`' + s + '`' for s in p['code']) + '.', ''])
lines.extend(['## 6. What a key cannot solve', '', '| Outcome | Current package status | What remains |', '|---|---|---|'])
for m in data['missing_integrations']:
    lines.append('| ' + m['name'] + ' | ' + m['state'].replace('_', ' ') + ' | ' + m['effect'] + ' |')
lines.extend(['', 'An adapter that exists is not a verified live result. The attendee must connect their own account and inspect the native outcome.', '',
              '## 7. Completion checks', '',
              '1. Your page opens with your actual company facts and offer.',
              '2. Your mailbox identity and primary-calendar read match your private config.',
              '3. Your exclusions come from a complete current source, with no invented empty coverage.',
              '4. Every selected person has current employer evidence and fresh valid work-email evidence.',
              '5. The eleven exact pilot actions are pinned. The own-sender Sent test unlocks only the ten approved prospect actions.',
              '6. Every claimed send has an exact native Sent match. Prepared, accepted and queued stay separate.',
              '7. The second cycle reads prior attempts and does not submit the same uncertain or completed action again.',
              '8. Gift and social extensions have their own provider readbacks. Recipient waits stay visible.',
              '9. Unimplemented outcomes are named. They are not counted as completed because a key was entered.', '',
              '## 8. Unknown provider outcomes', '',
              'For exact email, gift and social outreach keys, use reconcile. Creative, advertising and contact preparation do not have that generic reconciliation route. Follow [PROVIDER-RECOVERY.md](PROVIDER-RECOVERY.md). Preserve original request IDs when returned and never submit a duplicate to learn whether the first request worked.', ''])
(ROOT / 'API-CONNECTIONS.md').write_text('\n'.join(lines))
matrix = ['# API status matrix', '', 'Source code reviewed October 6, 2026. Live attendee connections have not been run by this guide.', '',
          '| Tool | What entering it enables | Required when | Local support | Key alone is insufficient because |', '|---|---|---|---|---|']
for p in data['providers']:
    matrix.append('| ' + p['name'] + ' | ' + p['enables'] + ' | ' + p['priority'] + ' | ' + p['status'] + ' | ' + p['does_not_enable'] + ' |')
(ROOT / 'API-STATUS-MATRIX.md').write_text('\n'.join(matrix) + '\n')
env = ['# Blank optional process overrides for the portable v5 workshop.', '# The application does not auto-load this file.', '# Prefer credential_files paths in your private workshop config.', '# Keep filled values outside code, screenshots, prompts and shared ZIPs.', '# Google uses a private OAuth or service-account JSON file, not an API-key string.', 'V5_GOOGLE_FILE=', 'V5_GOOGLE_SERVICE_ACCOUNT_FILE=']
for p in data['providers']:
    for name in p['env']:
        if name not in ('V5_GOOGLE_FILE', 'V5_GOOGLE_SERVICE_ACCOUNT_FILE'):
            env.append(name + '=')
(ROOT / 'credentials.env.example').write_text('\n'.join(env) + '\n')
(ROOT / 'google-oauth.template.json').write_text(json.dumps(data['providers'][0]['schema'], indent=2) + '\n')
(ROOT / 'salesforce-oauth.template.txt').write_text('client_id=\nclient_secret=\nrefresh_token=\ninstance_url=\n')
(ROOT / 'exclusions.template.json').write_text(json.dumps(data['providers'][1]['schema'], indent=2) + '\n')
(ROOT / 'gift-gate.template.json').write_text(json.dumps(next(p for p in data['providers'] if p['id'] == 'loop_and_tie')['schema'], indent=2) + '\n')
print(json.dumps({'providers': len(data['providers']), 'reference_bytes': (ROOT / 'API-CONNECTIONS.md').stat().st_size, 'filled_credentials': 0}))
