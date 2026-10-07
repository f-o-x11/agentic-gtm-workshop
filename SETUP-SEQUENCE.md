# Connect only what you will use

Part 1 needs your company website and an agent that can create files and read the web. It needs no paid research API. Part 2 adds your own Google mailbox, a current exclusion list and fresh email validation. Part 3 operates the same project. Extra channels are optional.

An API key is a private password for a tool. Google uses a browser sign-in instead. A saved key is not a working connection. Each tool must return your actual account or resource before you use it.

## 1. Finish Part 1 first

Open START-HERE.html and paste its complete starting prompt into Codex or Claude Code in the extracted package folder. It creates your sourced company brief before setup, then repairs missing AUTHORITY.md and company-motion/AGENTS.md and saves the verified Python interpreter.

Run commands from code/. Every `python3 -B gtm.py` command uses the saved interpreter through the launcher, even if your shell still points to Python 3.9. If none is available, use the official installer named by the error. No Homebrew is required.

Part 1 needs no provider key or private sender configuration. Keep sending paused.

Before Part 2, let the agent create your private config using code/evidence/workshop-config.example.json. Use your own sender, countries and exact limits. Keep filled config and token files outside code/ and company-motion/, with directory mode 0700 and file mode 0600. Do not share them.

```sh
python3 -B gtm.py init --config /absolute/private/workshop-config.json
python3 -B gtm.py status
```

Use init for the first private runtime configuration. Repeated init repairs documents without replacing existing settings or history. Use configure only for a later deliberate settings change.

The agent shows the normalized country names. US, USA and United States refer to the same country. Unknown countries remain visible and held. The source text is retained.

## 2. Connect your own mailbox

Complete this before Part 2:

1. Open Google Cloud Console. Use the menu, IAM & Admin, Create a Project. Give your workshop project a name and create it. Select that project. [Google project guide](https://developers.google.com/workspace/guides/create-project).
2. Use APIs & Services, Library. Find Gmail API and choose Enable. Repeat for Google Calendar API. Enable Google Sheets API if you will read a customer Sheet. [API setup guide](https://developers.google.com/workspace/guides/enable-apis).
3. Use Google Auth platform, Branding. Choose Get Started if the project is new. Enter the app name, support email, audience and contact email. Finish setup.
4. For an External app in Testing, use Audience, Test users, Add users. Add your actual sender address and save it. [Google consent setup](https://developers.google.com/workspace/guides/configure-oauth-consent).
5. Use Google Auth platform, Clients, Create Client. Choose Desktop app. Give the client a name and create it. Download its JSON to your private credentials directory. [Desktop client guide](https://developers.google.com/workspace/guides/create-credentials).
6. Run the command below. Sign in with the exact sender address in your private config. The helper checks the account and saves the private signed-in credential.

If your company blocks app access, name the actual administrator approval needed. Continue building the page and exact messages while that permission is repaired. Do not substitute an API key for Google sign-in.

Run:

```sh
python3 -B gtm.py setup-google --client-file /absolute/private/google-desktop-client.json
```

Sign in with the exact sender named in your config. The helper checks the Gmail account, saves the signed-in credential privately and connects it to the runtime. It requests Gmail modify/send, Calendar readonly and Sheets readonly. Enable Sheets API only if you will use a revenue sheet.

Expected result: `connected_mailbox` is your address and `outreach_sent` is zero. The downloaded client JSON is not the signed-in credential. The helper writes the saved path back to your private config, so later `configure` keeps the connection. It does not write token values into config.

Keep every Google OAuth or service-account credential file in the private sibling folder, mode `0600`. Credential consumption rejects files inside `code/` or `company-motion/`, and rejects a private file without mode `0600`. A company administrator may need to allow the app. Repeat browser consent for each additional authorized sender. Workspace delegation is a separate administrator-controlled option. Delegation can take up to 24 hours. Testing refresh tokens may expire after seven days. See [Google delegation](https://developers.google.com/workspace/guides/create-credentials) and [token expiration](https://developers.google.com/identity/protocols/oauth2#expiration).

## 3. Import people you must not contact

Ask your agent to combine your actual customer, open-deal, opt-out and relationship exports. Use [exclusions.template.json](exclusions.template.json) as the structure. Keep the result private.

Copy this prompt:

```text
Build my exclusion list from the current exports I selected.
Include customers, open deals, people who opted out and active relationships.
Use actual company domains or email addresses. Keep the reason for each row.
Keep the real time the sources were read. Do not change an old export's timestamp.
Show missing or ambiguous records. Mark complete only after I confirm the full source coverage.
Save the private JSON, then import it. Do not send anything.
```

Run:

```sh
python3 -B gtm.py import --kind exclusions --file /absolute/private/exclusions.json
python3 -B gtm.py ready
```

Expected result: the importer saves an exclusion receipt with coverage, actual timestamp and file hash. The source must be current within 65 minutes before live outreach. There is no `exclusions_file` config field. The importer remembers the file path.

An empty list is valid only when the owner actually checked all three sources and found no exclusions. The shipped template starts `complete:false`.

## 4. Add one research source

Use official company pages first. If they do not provide the people or work emails you need, connect one provider from [API-CONNECTIONS.md](API-CONNECTIONS.md). Sixtyfour supports company/person searches and professional-email discovery. Exa finds web sources. Do not connect every provider in the reference.

Save the provider token as plain text in your private folder. Add its absolute path to `credential_files` in your private config, then run `configure --config`.

Copy this prompt:

```text
Use the one research provider I connected.
Find at most ten companies that match my actual buyer criteria.
For each selected person, keep the current employer, title, source URL and source date.
Keep uncertain results separate. Do not invent an email or turn a search snippet into a verified fact.
Prepare the private import files. Show one real result before expanding the search.
Do not send outreach.
```

Research stays paused until you enable it with your own Sixtyfour credit ceiling. Zero is allowed when you use only another research source. This switch enables paid research, not email, gifts or invitations.

```sh
python3 -B gtm.py research-on --sixtyfour-credits 6
python3 -B gtm.py research --operation sixtyfour-search --input /absolute/private/company-search.json
python3 -B gtm.py research-off
```

The six-credit example is a ceiling, not a charge or a promise of ten qualified contacts. The source adapter reserves search at 0.1 credit per requested result and professional-email discovery at 0.5 credit per call. Confirm the live allowance in your provider account. See [Sixtyfour credit pricing](https://docs.sixtyfour.ai/guides/credits-and-pricing).

For Exa, the inspected portable command is:

```sh
python3 -B gtm.py research --operation exa --input /absolute/private/exa-search.json
```

Its input needs `query` and `numResults` from 1 to 10. Turn research on first. Read the returned page before using a claim.

## 5. Validate the exact work email

Connect your own ZeroBounce key. Read the actual balance before validation:

```sh
python3 -B gtm.py research --operation zerobounce-balance
```

It returns `credits_remaining`. Keep enough credits for the addresses you will check. It does not print the key or send outreach. Validate the exact work address. A valid result is separate from employer evidence.

```sh
python3 -B gtm.py research-on --sixtyfour-credits 6
python3 -B gtm.py research --operation validate-email --input /absolute/private/email-to-check.json
python3 -B gtm.py research-off
```

Keep the same Sixtyfour ceiling you already selected. The example uses six. Zero is allowed only when the project has no Sixtyfour reservations. Do not lower a ceiling below already reserved credits.

Input:

```json
{"email": "ACTUAL_SELECTED_WORK_EMAIL"}
```

Expected result: a native receipt for the exact address with its actual provider status. Only a fresh valid result passes. Unknown stays held. A fresh completed receipt is reused. A completed receipt older than seven days can renew through the same operation. An uncertain prior request cannot renew or replay.

## 6. Pin the eleven exact emails, then test your own mailbox

Follow the Part 2 workbook to prepare one exact self email and ten exact prospect emails for ten distinct companies. Prepare and import all eleven before approval. The self address must be your authorized sender, listed in `controlled_test_recipients`. Both the own person record and self-email payload must have `controlled_test:true`. Do not label a prospect as a test.

The importer requires actual employer and validation evidence. Import accounts before people, then import actions:

```sh
python3 -B gtm.py import --kind accounts --file ../company-motion/ACCOUNTS.json
python3 -B gtm.py import --kind people --file ../company-motion/PEOPLE.json
python3 -B gtm.py import --kind actions --file ../company-motion/ACTIONS.json
python3 -B gtm.py refresh
python3 -B gtm.py review
```

Read every exact recipient, sender, subject, body and held reason. Let the agent build a private approval manifest from the actual review keys. [pilot-approval.template.json](pilot-approval.template.json) shows its structure. You approve the real messages, not an empty template.

Copy this prompt:

```text
Show the exact own-sender test email and ten prospect emails for ten distinct company domains.
Use their actual prepared action keys. Do not invent a key or change an already reviewed message.
Create the private pilot approval JSON with my actual authority, controlled_action_key and ten prospect_action_keys.
After I approve these exact recipients and messages, run approve-pilot with that file.
Keep the prospect sends locked until my own exact Gmail Sent test passes.
Do not send a different ready action or reset the pilot on another day.
```

After the owner approves that manifest:

```sh
python3 -B gtm.py approve-pilot --input /absolute/private/pilot-approval.json
python3 -B gtm.py refresh
python3 -B gtm.py review
python3 -B gtm.py resume
python3 -B gtm.py run --action-key ACTUAL_CONTROLLED_ACTION_KEY --limit 1
python3 -B gtm.py reconcile ACTUAL_CONTROLLED_ACTION_KEY
python3 -B gtm.py pause
python3 -B gtm.py results
```

Expected result: the exact self email matches Gmail Sent. This unlocks only the ten pinned prospect actions. The test does not count as a prospect email. Accepted is not sent. Sent is not inbox placement, delivered, replied or booked. If the submit result is uncertain, reconcile the same action. Do not create a new copy to resend it.

## 7. Complete only the pinned ten-company pilot

Refresh the real exclusion source when needed. The approved manifest pins the exact copy and recipient keys across days. The eleven-message pilot limit is a lifetime limit, separate from daily sender caps. It cannot reset at midnight or expand to unrelated ready actions.

```sh
python3 -B gtm.py refresh
python3 -B gtm.py review
python3 -B gtm.py resume
python3 -B gtm.py run --action-key ACTUAL_PINNED_PROSPECT_ACTION_KEY --limit 1
python3 -B gtm.py pause
python3 -B gtm.py results
```

Repeat the exact-key command only for the remaining original pinned prospect keys. Your agent can pass all ten actual keys by repeating `--action-key` in one command with `--limit 10`. Read those keys from the existing approved manifest. Do not include unrelated approved actions.

Reconcile each accepted, queued or uncertain key using `reconcile`. `--limit` does not select a named stage or override a hold. Use `--action-key` to select the original approved action. No new approval or replacement import is needed. The pass check is the one exact owned Sent test plus ten exact prospect Sent messages across the approved ten distinct company domains. Fewer is a partial pilot. Exhausted authority stays exhausted.

Use `replies` and `bookings` to read their separate outcomes. They do not send automatic replies. No extra release is needed to prove repeat protection. Read the existing attempts and next-action holds.

## 8. Optional Part 3 channels

| Extension | Have ready | What you can prove |
|---|---|---|
| Loop & Tie | API access, owned team, funded collection, native meeting gate | Exact gift creation and native sent event |
| Gojiberry | Owned seat, inactive invitation-only campaign, paused exact contacts | Exact queued or sent invitation/message state |
| Netlify | Token, fresh owned workshop site, reviewed HTML hash | Exact deployment and HTTPS content |
| Calendly | Token and actual user/organization/event types | Bookings and cancellations |
| HubSpot or Salesforce | Your own permitted CRM connection | Supported current exclusion reads |
| Metadata | Your own token/account, connected ad accounts for ads | Brand kit, creative and guarded campaign operations |

Loop & Tie needs a native scheduler binding in addition to its key. Save the provider's actual scheduler form HTML privately. Use [GIFT-GATE-HELPER.md](GIFT-GATE-HELPER.md). The agent captures the actual authenticated current form, provider URL, owned team and actual capture time. It extracts both IDs and both actual input names from the same numeric form into [gift-gate.template.json](gift-gate.template.json). Import and send within 65 minutes of that real capture. A stale capture must be recaptured, not restamped. The importer also reads the owned native team and scheduler catalogue with your authenticated token. Then run:

```sh
python3 -B gtm.py import --kind gift-gate --file /absolute/private/gift-gate.json
```

Netlify publishing uploads one index.html for the selected site. Use a fresh workshop site. Let the agent read the exact reviewed file and site. The publish review computes the actual page hash and the approval hash. No extra Python command is needed.

Review the file and exact target site. Run the read-only publish review. Its approval hash binds the exact owned site, owner and page bytes:

```sh
python3 -B gtm.py resource --operation publish-review --file /absolute/private/account-page.html
```

After approving that exact destination and content, use the returned `approval_sha256`. The returned file hash alone is not the approval hash.

```sh
python3 -B gtm.py resume
python3 -B gtm.py resource --operation publish --file /absolute/private/account-page.html --approved-sha256 ACTUAL_PUBLISH_REVIEW_HASH
python3 -B gtm.py pause
```

Open the returned HTTPS URL on desktop and mobile. Inspect an owner-controlled test form in its actual destination. A content hash alone does not prove the form works.

### Give each extra channel its own exact scope

After preparing and reviewing a gift or social action, let the agent build the private [release-scope.template.json](release-scope.template.json) from actual action keys. Set exact channel counts. A gift needs its actual currency, a maximum per gift and a lifetime total. The provider collection price must fit both limits and available funding.

```sh
python3 -B gtm.py approve-scope --input /absolute/private/extension-approval.json
```

This authorizes only the reviewed keys. It does not authorize the entire gift balance or future recipients. Keep local execution paused while preparing the scope.

Dispatch the original exact approved gift or social key, then reconcile that same key:

```sh
python3 -B gtm.py refresh
python3 -B gtm.py review
python3 -B gtm.py resume
python3 -B gtm.py run --action-key ACTUAL_APPROVED_GIFT_OR_SOCIAL_ACTION_KEY --limit 1
python3 -B gtm.py pause
python3 -B gtm.py reconcile ACTUAL_APPROVED_GIFT_OR_SOCIAL_ACTION_KEY
```

The exact-key selector excludes other approved ready grants. It grants no permission and does not clear stage, freshness, budget or unknown-result holds. Queued remains queued. An uncertain original attempt is read through reconciliation, not replaced or dispatched again.

### Optional advertising setup

Metadata campaign operations are a portable workshop addition. Read your actual account and ad-platform integration status. Keep `policy.advertising.enabled` false until the owner approves the account, audience, draft copy and exact budget. `ads-review` shows the exact operation before `ads` can write a permitted draft or pause.

```sh
python3 -B gtm.py ads-review --operation get_integrations_status --input /absolute/private/empty-arguments.json
python3 -B gtm.py ads-review --operation check_campaign_launch_readiness --input /absolute/private/campaign-arguments.json
```

`empty-arguments.json` contains `{}`. `campaign-arguments.json` contains the actual `campaign_id`. The shipped package currently holds ad launch and restart until the existing campaign budget and native readiness response contracts are verified. Drafts, audiences, creative, reads and exact campaign pause remain available. Campaign draft channel fields support LinkedIn and Facebook only. A draft or provider response is not a running campaign. Local email pause does not cancel a native campaign or existing queue.

### Before unattended operation

Snapshot mode still needs the complete owner export from the past 65 minutes. For unattended native mode, connect a maintained complete customer Sheet, at least one real CRM, full history and actual booking sources. Follow [NATIVE-SOURCE-SETUP.md](NATIVE-SOURCE-SETUP.md). Native mode requires fresh complete positive receipts and holds when any required source is unavailable or unresolved. Observe two manual cycles before installing and observing the local schedule.

For an unknown creative, advertising or contact-provisioning result, follow [PROVIDER-RECOVERY.md](PROVIDER-RECOVERY.md). Save the original request ID when returned. Inspect the owned provider object before any new write. Generic `reconcile` does not handle these operations.

## 9. End with evidence

Copy this prompt:

```text
Read this project's actual receipts.
Show what I built, what I connected and what ran.
Separate prepared, accepted, queued, exact sent, delivered, replied, booked and completed.
Show the native evidence for every claimed result.
Give me the next one action needed for any held item.
Keep tokens, private recipients and filled config out of shared files.
```

Your final assets are your company context, reusable skill, execution flow, target accounts, exact approved messages and actual provider receipts. You can repeat the workflow with your own company and tools.
