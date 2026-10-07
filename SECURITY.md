# Security review

Reviewed October 7, 2026. This is a local workshop package, not a hosted service.

## Scan scope

- All three Git commits at the reviewed base, the tracked working tree, six PDFs and 13 unique embedded or raw images.
- PDF text, metadata, links and attachments. Images checked with OCR and reviewed examples inspected visually.
- Provider destinations, credential consumption, local authority, exact-copy approvals, repeated-action protection, GitHub Actions and authoring dependencies.
- Gitleaks 8.30.1, pip-audit 2.10.1 and Tesseract 5.5.2.

No real credential was found. Gitleaks initially flagged the literal workshop prose `authenticated sender, buyer/validation` in three source files and three PDF text exports. Each match was reviewed and excluded with that exact phrase only. Scans retain the standard credential rules.

The credential templates are blank. The distribution database has 16 empty tables. No private attendee list, recipient export, correspondence or populated working database is part of this repository.

## Fixes

| Issue | Current behavior | Verification |
|---|---|---|
| A credential path could be inside the repository root. | Config and credentials must be outside the repository. Symlinks are checked at their real destination. | Root and symlink rejection; external mode-0600 file accepted. |
| The live database was the tracked distribution template. | Working records use ignored company-motion/gtm.sqlite. The tracked template stays empty. | Fresh CLI keeps the template unchanged. Explicit migration preserves all records, archives the original and pauses execution. |
| GitHub Actions used movable version tags. | Checkout and Python setup use exact commit hashes. | Release validation rejects unpinned actions. |
| The authoring environment used pypdf 6.10.0, which had published advisories. | Authoring requirements now require pypdf 6.19.0 or newer within major version 6. | Current dependency resolution has no reported advisories. Version 6.19.0 reads all six PDFs and merges the 122 presentation pages. |

The fixed-source tests pass: 37 focused runtime checks, 20 startup checks and release validation. These are offline checks with temporary records and fake providers. They do not establish live delivery or a beginner's completion time.

## Public sharing

The materials intentionally contain Metadata branding, redacted teaching examples for Zuora, Forum One and Datarails, and dated aggregate company results. Public visibility would make these examples and the portable implementation available to anyone. No root license has been selected. The Rubik fonts retain their included SIL Open Font License.

## Limits

- Repository visibility does not launch a service or run outreach.
- Keys grant provider access. Exact recipient, message and spending authority is separate.
- The local agent can edit files. Prompt instructions are not an independent permission boundary against a compromised local machine or an agent that rewrites its own controls.
- Paid research has a separate enable switch. Sixtyfour has a credit ceiling. Other provider calls still require the owner's bounded scope and credit monitoring.
- Automatic reply sending, appointment creation, postal fulfillment, whole social campaign activation and ad launch/restart are not implemented by this package.
- Future edits, provider behavior, Windows and a human beginner trial remain separate checks. A scan reports what it detected; it is not a guarantee against every possible leak or vulnerability.

Keep filled credentials, participant records and raw provider receipts outside shared packages. Run release validation before distribution and review the staged Git diff before publishing changes.
