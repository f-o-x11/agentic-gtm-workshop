# Keep the source checks current

Use snapshot mode for the classroom pilot. It reads a complete owner-reviewed export from the past 65 minutes. Use native mode for repeated operation only when your actual company systems can provide complete current coverage.

Native mode replaces that snapshot with actual fresh reads. It requires a current customer Sheet, at least one CRM, full relied-on conversation history and actual booking sources. Missing, partial, unknown or stale sources hold outreach. Native mode does not fall back to an old snapshot.

## 1. Connect the complete customer source

Use a maintained customer source that actually covers your whole company. Give the agent read access to the exact private Sheet. Its first row must contain these exact columns:

| name | domain | status |
|---|---|---|
| Actual company name | Actual company domain | Actual current or former status |

The only accepted statuses are `current_customer` and `former_customer`. These are field values, not invented teaching records. Do not infer customer status from a logo or an old invoice. Use the actual Sheet name and an all-column range such as A:C. Native mode rejects row-bounded ranges. Include every row in that source. A filtered ten-account list cannot prove full customer coverage.

Private settings:

```json
{
  "revenue": {
    "mailbox": "ACTUAL_AUTHORIZED_GOOGLE_MAILBOX",
    "sheet_id": "ACTUAL_PRIVATE_SHEET_ID",
    "range": "ACTUAL_CUSTOMER_SHEET_NAME!A:C",
    "format": "customer_domains"
  }
}
```

The key remains `revenue` for compatibility. This format contains customer status, not revenue. The code reads Sheets with readonly permission. It does not update your source.

## 2. Connect actual deals, history and bookings

Connect your own Salesforce or HubSpot account. Read complete open-deal inventories and resolve every relevant company identity. Connect every actual booking source you rely on. Native history must cover your full mailbox and any additional relied-on outreach sources.

Set `history_since_epoch:0` in the private config for full Gmail history. This is a root config field. `settings.history_sources` can enable actual Instantly and Gojiberry history. Do not enable a source that your company does not use.

## 3. Select native mode explicitly

For a company that actually uses the customer Sheet and HubSpot:

```json
{
  "exclusion_mode": "native",
  "native_exclusions": ["revenue", "hubspot"]
}
```

Those are `settings` fields. Substitute Salesforce only when that is the actual source. This is a config structure, not a claim that your accounts are connected.

Copy this prompt:

```text
Read the native source contract in code/tools/setup.py and code/engine/channels/meetings.py.
Use my actual complete customer source, CRM, conversation history and booking sources.
Check the actual source coverage, fields, status meanings, permissions and complete pagination.
Keep history_since_epoch at zero for full Gmail history.
Set native mode only when all required sources exist. Keep execution paused while configuring.
Run refresh for my prepared actions. Show each actual source identity, current read time, completeness and unresolved record count.
Hold outreach if a source fails, is partial, has an unknown status or cannot resolve company domains.
Do not create an empty source, change an old timestamp or switch back to a snapshot to hide a failed native read.
```

Run from `code/`:

```sh
python3 -B gtm.py configure --config /absolute/private/workshop-config.json
python3 -B gtm.py refresh
python3 -B gtm.py review
```

Pass check: the actual customer, deal, suppression, history and booking receipts are fresh and complete. Missing evidence stays held. A local test of this code does not prove that your particular provider setup works.

## 4. Observe two manual cycles first

Inspect the actual first cycle. Reconcile its exact sent, accepted, queued or uncertain provider objects. Run a second manual cycle and check that completed or uncertain actions are not submitted again.

Then configure the supported local agent schedule from the workbook. Keep the computer awake, online and signed in. The agent must do preparation and source checks before the terminal sends a reviewed action. A timer alone cannot select accounts or write correct messages.

Observe actual scheduled wakes. An installed schedule is not an observed run, and a successful read is not a new send. Exhausted pilot authority must stay exhausted until the owner grants another exact reviewed scope.
