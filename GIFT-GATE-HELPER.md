# Let the agent read your actual gift scheduler

You need your own Loop & Tie team, funded collection and configured meeting scheduler. The key connects the API. It does not create the meeting requirement or reveal its private numeric form ID.

Open your owned Loop & Tie account and sign in. Open the edit panel for the exact scheduler you will use. Keep it open while your coding agent reads that actual browser tab. Use the current provider form, not generated HTML or a remembered screenshot.

Copy this prompt:

```text
Read code/README.md and the gift-gate importer in code/tools/setup.py.
Use my actual signed-in Loop & Tie browser tab and configured owned team.
Read the intended scheduler's actual edit form. Save that exact current form HTML in private-workshop/.
Record the actual current HTTPS provider page URL and actual capture time. Do not invent either.
Extract numeric_id from its real edit_scheduler_ID form ID.
Read the external scheduler ID from an input inside that SAME form. Record that exact input name as external_id_field.
Read the enabled meeting-required input inside that SAME form. Record its exact input name as meeting_required_field.
Match the external ID, name and source to the actual authenticated native scheduler catalogue for my configured own team.
Write the private gift-gate JSON with the actual form_html_file, capture_url, captured_at and team_id. Set provider to loop_and_tie.
Set meeting_required:true only after the actual provider control is enabled.
Set private-workshop/ to mode 0700 and the actual saved HTML and JSON to mode 0600.
Show the two IDs, real input names, scheduler name, configured team and capture time. Keep tokens and unrelated recipients out of the output.
Import the actual gate within 65 minutes of capture. Do not create or send a gift.
If the tab is unsigned, the form cannot be read or the source is stale, name the missing browser access or capture. Keep my reviewed gift preview.
Do not fabricate a numeric ID, form, field name, source URL, login proof or timestamp. Do not use an external ID found outside this exact form.
```

Run from `code/`:

```sh
python3 -B gtm.py import --kind gift-gate --file /absolute/private/gift-gate.json
```

The private JSON follows [gift-gate.template.json](gift-gate.template.json). It needs these fields:

| Field | Read it from |
|---|---|
| `external_id` | Exact external-ID input value inside this numeric form |
| `numeric_id` | Integer from the actual `edit_scheduler_ID` form ID |
| `name`, `source` | The matching owned native scheduler catalogue entry |
| `meeting_required` | `true` only when the actual required control is enabled |
| `meeting_required_field` | Exact required-control input name inside this form |
| `external_id_field` | Exact external-ID input name inside this same form |
| `form_html_file` | Private path to the actual captured form HTML |
| `capture_url` | Actual current HTTPS `loopandtie.com` page or its real subdomain |
| `captured_at` | Actual browser capture time, including timezone |
| `provider` | Literal `loop_and_tie` |
| `team_id` | Your actual configured own team ID |

The template leaves IDs, field names, URL and capture time blank. It sets `meeting_required:false`. It is a structure to fill from the provider, not proof of a working gate.

Pass check: the import returns `gift_gate_saved:true`. Both the exact external-ID input and enabled required-control input occur inside the same numeric form. The importer performs authenticated read-only team and scheduler catalogue checks, then binds their receipt to the captured HTML and metadata. A capture older than 65 minutes or dated in the future holds. Sending rechecks freshness, owned resources, funding and the exact bounded gift grant.

These checks depend on a truthful capture from the actual signed-in browser. They do not authenticate fabricated HTML. Keep the original capture evidence privately. Do not replace a stale timestamp with the current time. Recapture the actual current form.

If browser access is unavailable, complete the gift preview. It still gives you the exact recipient, collection, value, copy and expiry to review. Sending stays held until the actual native gate is proved.

Gift creation, email sent, redemption and meeting booking remain separate outcomes. An imported scheduler binding proves none of them.
