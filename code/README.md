# Run your own local GTM workflow

This is an attendee adaptation of the local v5 runtime. It has 20 files and an empty SQLite database. It contains no production records or credentials. The installed v5 source remains unchanged.

Working records are saved in ../company-motion/gtm.sqlite, outside the tracked runtime. The database in data/gtm.sqlite stays an empty distribution template. A previous version with saved records in that template will stop before using them. Run python3 -B gtm.py migrate-local-db once. It checks and preserves every record, keeps the original backup in company-motion/, restores the blank template and leaves execution paused. It refuses to overwrite another working database. Do not run both copies or clear uncertain attempts.

## What the code can do

| Motion | Supported result | Required setup |
|---|---|---|
| Email | Send exact approved plain text and HTML. Read the exact native Gmail Sent message. | Own Google mailbox, sender authority, current person evidence, valid email and exclusions. |
| Research | Exa search, SixtyFour search/email discovery, Apify runs/readback, Triguna, RocketReach, MoltSets, Instantly discovery and ZeroBounce validation. | Choose one source first. Add that key and approve paid research. |
| Gifts | Create one meeting-gated Loop & Tie gift. Read created and sent stages separately. | Own funded team, collection and actual numeric scheduler binding. |
| Social | Prepare inert contacts, release owned invitation-only contacts and read native delivery. | Own Gojiberry seat, campaign, list and verified person profile. |
| Replies | Read Gmail, configured Instantly and Gojiberry history. Recognize opt-outs and native thread-linked email replies. | Connected source and exact mailbox history boundary. |
| Bookings | Read configured Google Calendar, Calendly or HubSpot form records. | At least one actual booking source. Calendly needs owner identity and event types. |
| Pages | Publish one reviewed standalone HTML file to an owned Netlify site. Read exact hosted bytes. | Own Netlify token/site, exact content approval. Browser and form checks follow separately. |
| Advertising | Build audience/campaign drafts, create creative, read status and pause an authorized campaign. | Own Metadata token/account, bounded advertising authority and exact operation approval. Launch/restart stays in the owned UI. |

Reply collection does not send responses. One-email-per-recipient protection also blocks follow-up email. Attendance association, automated reply sends and physical postal fulfillment are not implemented. Netlify publishing, personal Google OAuth, Exa search and campaign operations are workshop additions. The original 20-file v5 had no standalone page upload or campaign activation adapter. Provider contract tests are local. They do not establish a successful live installation.

## Folder layout

1. Keep the downloaded `code/` folder as the 20-file runtime.
2. Create its sibling `company-motion/` for your company context, skills, accounts, private inputs and page outputs.
3. Keep credentials and private configuration in your own private credentials directory outside both folders. Filled configuration, OAuth client JSON and key files must use mode 0600. The code rejects credential paths inside code/ or company-motion/. Blank distribution templates contain no private values; copy and fill them outside both folders before use.

Python 3.10 or newer is required for the engine. The launcher works with Python 3.9 and checks installed interpreters before importing the engine. It saves the verified executable in `../company-motion/.runtime.json`. Every later `python3 -B gtm.py` call reuses it, even when `python3` still points to 3.9. No Homebrew installation is required. If no supported Python is installed, the launcher stops with the [official installer](https://www.python.org/downloads/). It never installs software silently. Personal Google OAuth uses the Python standard library. The service-account alternative needs `cryptography` and Workspace admin delegation. Commands use `-B` to avoid extra bytecode files.

## Start with your own company

Open the whole workshop folder in Codex or Claude Code. It contains START-HERE.html, prompts.html, code/ and company-motion/. Bring your website, buyer segment, offer and two target domains. Copy the complete startup prompt from START-HERE.html. It creates the company brief first, checks local setup and stops. Review the company brief next, using prompts.html#p1-company. Do not open only code/ or ask the agent to run the entire ZIP.

Bootstrap requires the real company brief first. It creates missing `AUTHORITY.md` and `AGENTS.md` in company-motion and keeps existing documents unchanged. These files allow local work and keep external actions paused. Run the same bootstrap command to repair an incomplete start. Its result names the next step and stops.

Finish the account-page exercises before provider setup. For the later email exercise, copy the blank `evidence/workshop-config.example.json` outside both folders. Fill it with your actual company, sender, approved buyer countries and written authority. Set the filled file to mode 0600. Keep gifts, social, advertising and paid research off. Run `python3 -B gtm.py init --config [ABSOLUTE PRIVATE CONFIG PATH]`. Existing projects keep their settings, grants and history; use `configure` only for a deliberate settings change. Both setup commands require COMPANY.md first. `configure` pauses outreach. `history_sources` cannot override authorized Gmail senders or `history_since_epoch`. Native mode requires epoch zero.

Country aliases such as US, USA and United States all become United States. Imports and readiness show the canonical country. Unknown values stay unknown; normalization does not invent location evidence. Use the same names in your source records and owner scope.

For a removed Python installation, rerun bootstrap with `--reset-python`. To select an installed interpreter yourself, add `--python [ABSOLUTE EXECUTABLE PATH]`. The launcher checks its actual version before saving it.

## Connect Google

Create your own Google Cloud desktop OAuth client. Enable Gmail, Calendar and Sheets APIs. Download its client JSON to your private credentials directory. Set that file to mode 0600 before connecting. Add your mailbox as a test user if your consent app is in testing mode.

```sh
python3 -B gtm.py setup-google --client-file /ABSOLUTE/PRIVATE/google-desktop-client.json
python3 -B gtm.py ready
```

The first command opens actual Google consent. It verifies your Gmail address against your authorized sender and saves a private 0600 refresh-token file. It requests Gmail read/modify/send, Calendar read-only and Sheets read-only. It does not send mail. Google testing-mode refresh tokens can expire, so production operation needs the appropriate consent-app setup. Repeat the connection for each authorized mailbox. The runtime stores mailbox-specific credential paths.

Workspace delegation remains available through `credential_files.google` or `V5_GOOGLE_SERVICE_ACCOUNT_FILE`. Personal OAuth credentials use `type: authorized_user`, `email`, `client_id`, `client_secret`, `refresh_token` and `scopes`. Do not paste token values into a chat or a public form.

## Import actual records

All import files must be outside the code folder. CSV is accepted for accounts. JSON accepts a list or an object containing `records`.

1. Accounts need `domain`, `name`, `country`. Optional fields include `fit` and `source_url`.
2. People need `domain`, `email`, `name`, `title`, actual `identity` evidence and `email_verification` evidence. Add `profile` for social.
3. Actions need `channel`, `recipient`, `sender`, `payload`. Email payload includes the same `sender`, `subject`, `body` and optional identical `html`.

Person evidence has this shape. Every field must come from your actual source or provider read:

```json
{
  "identity": {
    "status": "confirmed_current",
    "domain": "ACTUAL EMPLOYER DOMAIN",
    "profile_url": "ACTUAL LINKEDIN PROFILE",
    "title": "ACTUAL CURRENT TITLE",
    "profile_name": "ACTUAL NAME",
    "observed_at": "ACTUAL ISO TIMESTAMP",
    "provider": "ACTUAL PROVIDER OR SOURCE"
  },
  "email_verification": {
    "email": "ACTUAL WORK EMAIL",
    "status": "valid",
    "provider": "ACTUAL VALIDATION PROVIDER",
    "checked_at": "ACTUAL ISO TIMESTAMP"
  }
}
```

Employment and deliverability evidence must be at most 7 days old. The employer, name, title, profile and work email must agree. If deliverability is unknown, store that actual status, then run ZeroBounce. Never replace an unknown result with `valid`.

```sh
python3 -B gtm.py import --kind accounts --file ../company-motion/ACCOUNTS.json
python3 -B gtm.py import --kind people --file ../company-motion/PEOPLE.json
python3 -B gtm.py import --kind actions --file ../company-motion/ACTIONS.json
```

For the self-message only, import your own company and current owner identity. Mark the own person and email payload `controlled_test: true`. The recipient must equal the exact sender mailbox and appear in `controlled_test_recipients`. A message between two owned mailboxes is not this self-test. It consumes capacity but is excluded from the ten-prospect result.

## Check customers, deals, opt-outs and prior conversations

Use one current owner-reviewed exclusion snapshot from your real CRM/customer/opt-out records. This is an explicit local-source fallback. It is not presented as an API inventory.

```json
{
  "complete": true,
  "observed_at": "ACTUAL REVIEW ISO TIMESTAMP",
  "source": "NAME OF THE REAL EXPORT AND OWNER REVIEW",
  "coverage": ["customers", "open_deals", "suppressions"],
  "records": [
    {"entity_type": "domain", "value": "ACTUAL CUSTOMER DOMAIN", "reason": "Current customer"},
    {"entity_type": "email", "value": "ACTUAL OPT-OUT EMAIL", "reason": "Opt-out"}
  ]
}
```

Use an empty `records` list only after actually verifying there are no exclusions. The owner must review the snapshot within 65 minutes of release. Each cycle rereads the private file and hashes its actual contents. Prior exclusions stay recorded. This importer does not remove them. Keep `settings.exclusion_mode: snapshot` for this owner-reviewed fallback. To replace it with complete native sources, use the explicit native setup below. Native mode never depends on an owner snapshot.

For the workshop rule check, choose an actual excluded company outside the ten-prospect cohort. Import its account and domain exclusion, then run:

```sh
python3 -B gtm.py rule-test --domain ACTUAL_EXCLUDED_DOMAIN
```

This command opens the existing database read only and runs the actual domain exclusion check. It creates no person or action. The result shows the hold reasons and unchanged action/attempt counts. A missing account is NOT_TESTED. NO_DOMAIN_HOLD does not mean a person or email is eligible.

```sh
python3 -B gtm.py import --kind exclusions --file ../company-motion/EXCLUSIONS.json
python3 -B gtm.py refresh
python3 -B gtm.py review
```

`refresh` reads configured calendar bookings and actual scoped Gmail history for prepared account domains. It binds the results to those accounts. Missing, stale or incomplete sources hold affected actions. The minimal setup uses your own Google calendar and complete owner snapshot. Other CRM, website-form and Calendly sources are required when you configure them.

For unattended operation, set `history_since_epoch: 0` and choose `settings.exclusion_mode: native` explicitly. Configure `native_exclusions` with `revenue` and at least one actual `salesforce` or `hubspot` source. Native mode reads the full configured mailbox history, current customers, current open deals and bookings. It does not use or retimestamp an owner snapshot. Failed, stale, partial or unresolved native inventories hold actions. They never fall back silently to a snapshot.

Your customer source can be an actual canonical Google Sheet. Set `revenue` to your own `mailbox`, `sheet_id`, `range` and `format: customer_domains`. Read every row with an all-column range such as `Customers!A:C`, not a selected row block. Its exact columns are `name`, `domain`, `status`. Use actual `current_customer` or `former_customer` values. Unknown status or missing current-customer identity holds the read. This source reads current customer status; it does not infer revenue. The original dated MRR sheet format is also supported. Configure Salesforce's exact authenticated owner email, or your own HubSpot private-app access, plus the sources your company uses. Native source configuration and current account identity must be verified before unattended scheduling.

## Approve all eleven messages, then send the test

Prepare and import all eleven exact email actions first. The first recipient is your own authorized sender mailbox. The other ten recipients work at ten distinct prospect companies. Read `review`, fix the holds, then create `../company-motion/PILOT-APPROVAL.json` with the exact action keys returned by import:

```json
{
  "authority": "I approve these exact recipients, sender and messages for my company",
  "controlled_action_key": "ACTUAL OWNED TEST ACTION KEY",
  "prospect_action_keys": ["TEN ACTUAL DISTINCT-COMPANY ACTION KEYS"]
}
```

Replace the example array with ten separate exact key strings. The following commands perform authorized live work:

```sh
python3 -B gtm.py approve-pilot --input ../company-motion/PILOT-APPROVAL.json
python3 -B gtm.py refresh
python3 -B gtm.py review
python3 -B gtm.py resume
python3 -B gtm.py run --action-key ACTUAL_OWNED_TEST_ACTION_KEY --limit 1
python3 -B gtm.py reconcile ACTUAL_OWNED_TEST_ACTION_KEY
python3 -B gtm.py results
```

The approval pins the sender, recipient, company, copy and preparation time for all eleven actions. Before an exact owned Gmail Sent receipt exists, only the test key can release. Own-company history and bookings do not block this approved self-test. Explicit recipient opt-outs and every prior channel attempt still block it. Gmail acceptance alone does not pass. The Sent receipt must match sender, recipient, subject, plain text, HTML and action binding.

After the exact test passes, release the ten pinned prospect keys:

```sh
python3 -B gtm.py run --limit 10 \
  --action-key ACTUAL_PROSPECT_KEY_1 --action-key ACTUAL_PROSPECT_KEY_2 \
  --action-key ACTUAL_PROSPECT_KEY_3 --action-key ACTUAL_PROSPECT_KEY_4 \
  --action-key ACTUAL_PROSPECT_KEY_5 --action-key ACTUAL_PROSPECT_KEY_6 \
  --action-key ACTUAL_PROSPECT_KEY_7 --action-key ACTUAL_PROSPECT_KEY_8 \
  --action-key ACTUAL_PROSPECT_KEY_9 --action-key ACTUAL_PROSPECT_KEY_10
python3 -B gtm.py results
```

`--action-key` selects only the original named approved action. Repeat the flag for an exact cohort. Ask your agent to use the ten original prospect keys from PILOT-APPROVAL.json. A limit alone is a global maximum and can include other approved grants. The selector never grants authority, repairs held copy or bypasses capacity. Unknown keys fail before reservation. Reconcile every accepted or uncertain key. The pilot can produce at most eleven unique attempts across all dates. A new day, edited person label or another ready action cannot expand this approval. `results` reports this exact cohort. Ten exact prospect Sent receipts at ten distinct companies complete the sending portion. Fewer than ten means a partial pilot. Inspect the protected attempts through `results` and `person`. Do not issue another live release to demonstrate duplicate protection. Delivery, replies, bookings and attendance remain separate outcomes.

## Approve a later bounded channel

A completed pilot does not authorize ongoing outreach or new spending. For a later gift, social contact or new email cohort, import the exact actions and create a separate explicit owner scope:

```json
{
  "authority": "I approve this exact later action and value for my company",
  "purpose": "One meeting-gated gift",
  "action_keys": ["ACTUAL GIFT ACTION KEY"],
  "limits": {"email": 0, "gift": 1, "social": 0},
  "gift_budget": {"currency": "USD", "max_per_gift": 50, "max_total": 50}
}
```

```sh
python3 -B gtm.py approve-scope --input ../company-motion/CHANNEL-APPROVAL.json
```

Use your own approved currency and values. Gift currency must be present in the actual native collection and match the grant. Unknown currency holds fulfillment. Counts and value limits apply for the grant's lifetime. Each key belongs to one approval only. Channel authority, current sources and hard daily caps still apply. Approval is a local owner action, not a provider connection or proof of success.

## Paid research

Add credential paths in your private config. The runtime reads them; it does not automatically load `.env`. Exported `V5_PROVIDER_TOKEN` and `V5_PROVIDER_FILE` variables are optional overrides. Use `loop_and_tie`, not `loop-and-tie`, as the provider setting.

```sh
python3 -B gtm.py research-on --sixtyfour-credits 20
python3 -B gtm.py research --operation exa --input ../company-motion/SEARCH.json
python3 -B gtm.py research --operation zerobounce-balance
python3 -B gtm.py research --operation validate-email --input ../company-motion/EMAIL-VALIDATION.json
python3 -B gtm.py research-off
```

`SEARCH.json` needs a real `query` and `numResults` from 1 to 10. Email validation needs `email`. The balance command reads remaining ZeroBounce credits. Validation reuses an actual receipt for seven days, then renews a completed stale check. Any prior unknown validation holds renewal; it cannot be replayed. SixtyFour search needs `mode`, `simple_filters`, `page_size`, matching `max_results` and `output_shape: raw`. SixtyFour email discovery needs `mode: PROFESSIONAL` and `verify_emails: false`, followed by separate validation. Credits are reserved before the paid request. Unknown outcomes retain reservations and are never replayed automatically. The attendee chooses their own ceiling up to 15,000 credits. Other providers bill their own accounts; this runtime does not impose a dollar budget on them.

Other operation names: `sixtyfour-search`, `sixtyfour-email`, `apify-start`, `apify-read`, `triguna-profile`, `triguna-company`, `rocketreach`, `moltsets`, `instantly-email`, `radar-start`, `radar-read`. Read the exact input checks in `tools/setup.py` and `engine/research.py` before calling them. A research candidate does not establish current employment or consent.

## Gifts, social, pages and advertising

Gifts need your funded owned team and meeting scheduler. Follow ../GIFT-GATE-HELPER.md. The current scheduler-edit-v1 contract matches the actual Edit URL and POST action, numeric form, enabled name and meeting URL inputs, and visible provider meeting requirement to authenticated owned native catalogue reads. The older contract requires actual external-ID and meeting-required controls in that same form. Capture the actual signed-in full HTML privately, with its real HTTPS provider URL and time, no more than 65 minutes before import and release. Missing, stale or mismatched evidence holds. A supplied HTML file alone does not prove authenticated origin. Sending rereads owned native team, scheduler, collection, funding and exact bounded approval.

Gojiberry private settings use `social_owned` keyed by your sender label. Each entry needs your `campaign_id`, `list_id`, `seat_id`, exact campaign `name` and exact `steps`. Prepare an inactive invitation-only campaign. `social-provision --operation NAME --input FILE` supports inert `create_contact`, `update_contact`, `add_contacts_to_list` in the configured owned list. Create the list in the owned UI first. New contacts are forced paused and not ready. Native uncertain provisioning cannot be replayed. Import a social action with actual contact/profile/resource IDs only after successful adapter create_contact provisioning. Import requires its original native receipt and binds its source digest to the action. An arbitrary paused contact cannot be adopted through import or a manually written social_prepared setting. Review every list in the isolated campaign and activate it in the owned UI with all contacts paused. The adapter never activates a whole campaign. It releases only the exact approved contact. A queue receipt remains pending until native delivery is read.

Pages need `credential_files.netlify` and `settings.netlify_site_id`. Review one standalone HTML file, then obtain approval for the exact owned site, authenticated owner and bytes:

```sh
python3 -B gtm.py resource --operation publish-review --file ../company-motion/PAGE.html
python3 -B gtm.py resource --operation publish --file ../company-motion/PAGE.html --approved-sha256 RETURNED_APPROVAL_SHA256
```

The code verifies authenticated owner/site, uploads once and reads the exact HTTPS deployment bytes. An accepted deployment may still be building. Repeat the same command to read the known deployment, without another upload. Known deployment readback works while outreach is paused. Changing the site, owner or bytes requires a new review. Run your browser checks afterward. Owned-byte verification does not prove a form works.

Metadata creative generation uses `resource --operation generate --input FILE`, where the input contains a supported `operation` and exact `arguments`. Advertising uses `ads-review --operation NAME --input FILE` to show the actual account and approval hash, then `ads` with the same operation/input and `--approved-sha256 HASH`. Use separate advertising policy caps and exact campaign IDs. Supported published tools are listed in `engine/assets.py`. Campaign drafts accept LinkedIn and Facebook only. Every configured channel needs an explicit daily budget within your cap. Other platform fields are rejected before a provider write until they have equivalent verified budget contracts. Launch and restart are disabled in this portable adapter until existing campaign budgets and readiness responses have a verified contract. Review the exact campaign, total/daily budget, audience, copy and native readiness in your owned Metadata UI before explicitly launching there. Read actual status afterward. A provider response is not proof of a running campaign. A queued native launch may execute later. Pausing an exact authorized campaign remains supported with a fresh review approval for each request.

## Run and recover

```sh
python3 -B gtm.py replies
python3 -B gtm.py bookings
python3 -B gtm.py pacing
python3 -B gtm.py pause
python3 -B gtm.py backup /ABSOLUTE/PRIVATE/FRESH-BACKUP
```

First run two manual cycles and inspect the receipts. Then ask your own Codex agent to schedule the full preparation workflow in `AGENTS.md`, followed by `run`. A terminal schedule alone will not choose recipients or write copy. Keep the machine awake, online and able to run Codex. Local hourly execution uses America/New_York from 8am through 5pm. Missed hours do not create catch-up bursts. Manual `run --limit` keeps hard daily caps.

If a source or permission is missing, repair only that source. If a provider write timed out, inspect the existing object and reconcile its exact key. Do not delete attempts, reset reservations or create another request to get around an unknown result.

Focused local tests run with `python3 -B checks/focused_checks.py`. They use temporary data and fake providers, with no live sends, paid lookups or fulfillment.


## Revoke a wrong approval

If approved copy or recipients are wrong, keep the original actions held. Do not reimport them, replace the pilot, edit timestamps or clear history. Permanently revoke that local approval:

```sh
python3 -B gtm.py revoke-grant --grant-id pilot --reason "The approved offer is wrong"
```

For a later scope, use its exact returned grant ID. Revocation preserves every original key, attempt and lifetime ceiling. It never creates replacement capacity or repairs the pilot. It stops future local release only. Already submitted provider queues need their own provider pause or cancellation. Further corrective outreach needs a separate explicit owner decision; it cannot be counted as completion of the original pilot.

## Read an unknown provider operation

`reconcile ACTION_KEY` handles recorded email, gift and social actions only. Do not call it for an advertising draft, creative request or contact provisioning operation.

1. Advertising: preserve the original request ID, operation, arguments and native object ID from `results`, attempt receipt or event. For a named campaign, use `ads-review --operation search_campaigns_by_names --input FILE` with the captured provider schema. Read its actual status and budget in the owned Metadata campaign UI. Use `ads-review --operation get_budget_group --input FILE` for a known budget group. An object without a returned ID or unique exact match remains held. Do not issue another create call.
2. Creative: preserve the original generation request and native result. Use the owned Metadata creative UI to inspect the original generated object. `search_ads_by_names` can read a known uniquely named ad through ads-review using its exact schema. An unnamed object with no native handle remains held; no generic creative reconcile adapter exists.
3. Gojiberry provisioning: preserve `events` and the original social_provision receipt. In the owned Gojiberry UI, open the exact configured campaign and list. Find the contact by the original exact email/profile and returned contact ID. The existing read tools are `get_contact`, `get_list`, `get_campaign` and `list_contacts` in `engine/channels/social.py`. They are read routes for an agent using the connected provider, not a new CLI command. Unknown provisioning remains held and cannot be adopted by importing an action. No CLI reconciliation repair is implemented for uncertain provisioning.
4. Netlify: rerun the original publish command with the same file and approval hash to read its known deployment ID. No new upload occurs. If no deployment ID was captured, inspect the exact owned site's deploy history in Netlify using the original submission time and HTML hash. Keep the unknown attempt; do not upload again.

## Restore and maintain exclusions

Pause local execution and separately pause any submitted provider queues before recovery. Make a fresh `backup` outside the runtime. To inspect a restore point, extract a fresh paused code copy in a separate folder, copy the backed-up database into its sibling company-motion/gtm.sqlite, and inspect integrity, original grants, attempts and native receipts before any execution. Never restore an older database into the active sending project to reset capacity or erase uncertain sends. No automatic restore command is supplied.

Exclusions are append-only through import. Incorrect exclusions require an owner-reviewed source correction and a fresh source read. Keep the original evidence and backup. This runtime has no suppression-delete command. Do not remove a native opt-out or relationship through direct SQL to complete the exercise.

For a single approved gift or social stage, use `python3 -B gtm.py run --action-key ACTUAL_ORIGINAL_ACTION_KEY --limit 1`. `--force` can be combined with the same selector; it changes timing only. All exact approval, freshness, current ownership, cap and uncertainty checks remain. Google mailbox-specific paths and V5_GOOGLE_SERVICE_ACCOUNT_FILE overrides are checked at consumption for private location and mode 0600, before OAuth refresh or signing.
