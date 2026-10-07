# Read the first request. Do not send a second one.

An unknown result means the first write may have worked. Keep execution paused. Keep the original attempt key, exact account, operation, arguments, send time, any provider object ID and any returned request ID in your private folder. A timeout may return no ID. Record that absence. Do not invent one.

For the first dispatch of an unattempted, already approved named action, use `run --action-key ACTUAL_ORIGINAL_APPROVED_ACTION_KEY --limit 1`. A limit alone is global and can choose another approved action. The selector grants no new authority and does not bypass holds. Once the original attempt exists, use its read route. Do not replace, reapprove or resend it.

`reconcile ACTION_KEY` handles prepared email, gift and social outreach actions. It does not handle every paid search, creative, advertising, publishing or contact-preparation request.

## 1. Metadata campaign, budget and ad requests

Read the owned Metadata account and use the read-only operations below. Run these from `code/`. Fill the private input with the original exact name. Search can return partial matches, so inspect the actual object ID, account, copy and native state. A missing result is not proof that creation failed.

```sh
python3 -B gtm.py ads-review --operation search_campaigns_by_names --input /absolute/private/campaign-search.json
python3 -B gtm.py ads-review --operation search_ads_by_names --input /absolute/private/ad-search.json
python3 -B gtm.py ads-review --operation get_budget_group --input /absolute/private/budget-search.json
```

The private inputs use these actual fields:

```json
{"campaign_names":["ACTUAL_ORIGINAL_CAMPAIGN_NAME"]}
```

```json
{"ad_names":["ACTUAL_ORIGINAL_AD_NAME"],"page":0,"size":25,"status":"all"}
```

```json
{"name":"ACTUAL_ORIGINAL_BUDGET_GROUP_NAME"}
```

For an audience, offer, missing campaign or unidentified object, inspect your owned Metadata UI and the original request receipt. Ask provider support to investigate the original ID if needed. Keep its exact budget and state visible. This package has no general ads reconciliation command. Do not repeat upload, create, pause, launch or restart to discover the first outcome. Campaign launch and restart remain held in the shipped adapter. Campaign draft fields support LinkedIn and Facebook only.

## 2. Metadata creative requests

Open the existing result URL when the original response supplies one. Inspect the existing brand kit or creative in the same owned Metadata account. Save its actual asset ID, rendered result and visual review privately.

A complete response can be read from the saved attempt. An unknown generation request has no dedicated CLI reconciliation operation. Use the owned Metadata UI or provider support with the original request ID when available. Do not regenerate or edit a new creative to bypass the original unknown request.

## 3. Gojiberry contact preparation

Open the exact owned list and inactive invitation-only campaign in Gojiberry. Read the existing contact by its actual returned ID. If no ID was returned, inspect the list for the exact original LinkedIn profile and payload. Confirm whether there is exactly one match and whether it is paused and not ready for campaign.

The provider exposes `get_contact`, `get_list`, `list_contacts`, `get_campaign` and `get_campaign_logs`. The portable CLI has no `social-read` or provisioning-reconcile command. Let your agent use an already connected read-only provider tool, or inspect the owned UI. Do not call `social-provision` again to investigate an unknown creation. Keep release held until the original preparation receipt and exact contact are verified.

A queued invitation is separate from a sent invitation. An accepted connection and a sent message are later stages. Campaign activation stays in the owned provider UI after inspecting every included list and contact.

## 4. Netlify deployment

When the original request has a deployment ID, the same exact file and approved review hash can read that existing deployment. It does not create a second deployment. Inspect its post-processing state and exact HTTPS bytes, then check the browser and form separately.

If the submission returned no deployment ID, inspect the owned Netlify site's deployment list for the original request time and exact content. Use provider support when the result cannot be resolved. Keep the original attempt and hold. Do not change the filename, file bytes or review hash to force another upload.

## 5. Paid research

An Apify run with an actual run ID uses `research --operation apify-read` with `{"run_id":"ACTUAL_ORIGINAL_RUN_ID"}`. Radar scans use `radar-read` with the original run ID. Those reads follow the original provider job.

For a paid lookup or validation request without a known completed receipt, inspect the original provider job, usage record or support case. Fresh completed email validation can be reused. Stale completed validation can renew through its guarded operation. An uncertain request cannot renew or replay.

## 6. Record the result

Copy this prompt:

```text
Read the original private attempt and provider receipt.
Keep execution paused. Do not write, resend, regenerate, import a replacement or change the old timestamp.
Preserve the original attempt key, account, operation, arguments and any returned object or request ID.
Use the documented read route or the actual owned provider UI to inspect that original object.
Check exact identity, copy, cost and state. A partial match or missing search result is not success or permission to retry.
Save the actual evidence privately. Name one missing read or support action when the result stays unknown.
```
