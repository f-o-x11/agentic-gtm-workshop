# Check that a meeting is required before gift redemption

You need your own API-enabled Loop & Tie account, funded collection and meeting scheduler. Open the intended scheduler's Edit page in your signed-in browser. The agent reads that page; it does not change its settings.

Copy this into your local Codex or Claude Code project:

```text
Read GIFT-GATE-HELPER.md and the gift-gate importer in code/tools/setup.py.
Read my configured owned team and its native scheduler catalogue.
Open the exact scheduler's Edit page in my signed-in Loop & Tie browser.
Save the actual full page HTML privately outside this entire repository, with mode 0600.
Save its actual HTTPS URL and capture time. Do not edit or manufacture the capture.
Read numeric_id from the real edit_scheduler_ID form.
For the current Edit Calendar page, use ui_contract:"scheduler-edit-v1".
Read external_id from the exact /schedulers/EXTERNAL_ID/edit URL and same-form POST action.
Match scheduler[name] and scheduler[url] inside that one form to the native scheduler name and source.
Confirm the page visibly says: Your recipient will need to schedule a meeting to redeem their gift.
Use the current provider text and controls. Hidden or script text is not proof.
Fill the private gift-gate JSON from api-templates/gift-gate.template.json.
Keep provider:"loop_and_tie", the exact owned team, name, source and actual capture metadata.
Set meeting_required:true only after the actual page check passes.
Import it from code/: python3 -B gtm.py import --kind gift-gate --file ACTUAL_PRIVATE_JSON_PATH
Replace ACTUAL_PRIVATE_JSON_PATH with the file you saved. Import within 65 minutes of capture.
Show the actual import result. Keep tokens and unrelated people private.
Do not create a gift. If any native page or catalogue check fails, keep the gift held and show that error.
```

The blank [gate template](api-templates/gift-gate.template.json) contains no IDs, capture or approval. Fill these from the actual provider:

| Field | Source |
|---|---|
| `ui_contract` | `scheduler-edit-v1` for the current Edit Calendar page |
| `external_id` | Exact scheduler ID in the Edit URL and matching POST form action |
| `numeric_id` | Integer in the actual `edit_scheduler_ID` form ID |
| `name`, `source` | Form name and meeting URL, matched to the owned native catalogue |
| `meeting_required` | `true` only after the visible provider statement is checked |
| `form_html_file` | Private path to the actual full HTML capture |
| `capture_url`, `captured_at` | Actual signed-in HTTPS page and capture time |
| `provider`, `team_id` | `loop_and_tie` and your configured owned team |

For a provider form that actually exposes an external-ID input and an enabled meeting-required input, the original contract remains available. Omit `ui_contract` and supply their exact names as `external_id_field` and `meeting_required_field`. Both controls must belong to the same numeric form. Do not invent missing inputs to use this older contract.

Pass check: import returns `gift_gate_saved:true` with zero provider writes. The importer matches the actual form to authenticated owned-team and scheduler reads, and saves a digest of that evidence. Missing, changed, future-dated or stale captures hold. Recapture the real page after 65 minutes; never refresh only its timestamp.

This depends on a truthful capture from the signed-in browser. Supplied HTML alone does not authenticate its origin. Keep the original capture private. If browser access is unavailable, finish the gift preview and leave sending paused.

Before creation, review the actual collection price, funded balance, shipping permission, recipient, copy, expiry and meeting terms. Approve an exact gift count plus per-gift and total cost. Loop & Tie credit pricing is USD, according to its [credit contract](https://guides.loopandtie.com/knowledge/what-is-lt-credit). Explicit provider currency is preserved and must match your approval.

A verified gate proves no gift was sent. Gift creation, sent email, redemption and completed meeting remain separate results.
