# Your local GTM workflow

Use this runtime for the attendee's own company and accounts in Codex or Claude Code. Keep these 20 runtime files together. Store company documents, skills, pages and private JSON inputs in the sibling `../company-motion/` folder. Store credentials and the private configuration outside both folders.

Start by reading the attendee's actual website and writing `../company-motion/COMPANY.md`. Ask only for the buyer segment and offer if the sources do not answer them. Then run `python3 -B gtm.py bootstrap --company-brief ../company-motion/COMPANY.md`. Show the company brief and setup result, name the next step and stop. Do one requested exercise at a time. Opening the ZIP is not permission to run every exercise.

If the owner explicitly requests the full local build, follow `../BUILD-MY-GTM.md` instead of the single-exercise stop rule. Bootstrap's stop result belongs to classroom mode. In full-build mode, continue local preparation between questions, preserve progress and keep every external-action approval and source check.

After each task, append its actual step, artifact path, check result and next step to `../company-motion/PROGRESS.md`. Keep earlier entries. Record a failed check as failed. Save the initial setup result and the attendee's two target domains in `../company-motion/SETUP.md`.

The launcher checks Python before importing the engine. It saves a verified Python 3.10 or newer executable in `../company-motion/.runtime.json` and reuses that executable on later `python3 -B gtm.py` calls. Use the same saved executable for standalone Python scripts. If no supported interpreter is installed, show the official Python installer link and stop. Do not silently install software or assume Homebrew is available.

Bootstrap creates missing `../company-motion/AUTHORITY.md` and `../company-motion/AGENTS.md` only after the company brief exists. It adds no sender or spending authority and makes no database or provider writes. Keep existing files unchanged. Rerun bootstrap to repair missing files. Do not delete attempts, grants or exclusions to repair setup.

Read `README.md`, the attendee's company context and execution flow before working. The empty database contains no accounts, people, history, consent or provider credentials. Never use another company's sender names, IDs, recipients, approval scope or spend limits.

Build in this order:

1. Create one useful output for the attendee's real company. Save its instructions as a skill.
2. Write the decisions that connect skills. Include exclusions, exact copy, caps and unknown outcomes.
3. Add the attendee's actual target accounts and current people. Keep source evidence.
4. Prepare all eleven exact messages and call approve-pilot. Run one approved message to the owner's own mailbox. Inspect its exact Gmail Sent receipt. Then run the approved ten-account pilot.

Use current website and professional evidence. Check every page claim against its exact source. Remove unsupported demo lengths, recent-launch statements, percentages and quotations. Show contradictions between source pages and ask the owner which claim is current. Reuse a quotation only when it fits; omit proof that the source cannot support. Unknown email, employer, role or source means hold that person. Do not make up identities, validation receipts, provider results, gifts, bookings or revenue. A provider key grants access. It does not grant outreach or spending authority.

For each cycle:

1. Read current records and reconcile earlier unknown submissions for these recipients.
2. Read the owner's current complete exclusion snapshot, configured CRM sources, sender calendar and scoped mailbox history.
3. Select eligible accounts and people. Create exact new copy from the attendee's offer and proof.
4. Import exact actions. Pin their owner approval with approve-pilot or approve-scope. Show `review` and fix every hold. Confirm the approved recipient, sender, copy and spending scope.
5. Run one bounded batch. The database reserves an exact attempt before the provider write.
6. Read the provider result. Report prepared, accepted, queued, sent, replied and booked separately.
7. Reconcile pending or unknown results. Never resend them automatically.
8. Save one useful next step. Change one copy variable when actual results support it.

`gtm.py run` dispatches existing prepared actions. It cannot research recipients, write copy or choose the next play. A scheduled Codex task must perform steps 1 to 4 before calling it. Keep the local computer awake and online. Do not install a schedule until two manual cycles produce correct receipts and repeat protection.

One pause lives in `config/policy.json`. The attendee's daily channel and sender caps are hard limits. Pilot approval permits one owned test and ten exact prospect keys for its lifetime, across all dates. New channels and ongoing cohorts need explicit bounded approve-scope grants. Manual runs change the time of execution, while caps, consent, exclusions, actual provider restrictions and duplicate protection still apply. Paid research has a separate switch and its own budget.

Preserve exact first-email text and HTML. Keep first emails link-free and permission-based. Do not send a gift with an invented value, expiry or meeting requirement. Verify owned social campaigns, lists, seats and paused contacts before releasing them. Native queued social activity is not a confirmed send.

Reply collection and booking reads are implemented. Automatic existing-thread reply sends, attendance attribution and postal fulfillment require further adapters. Metadata campaign operations and Netlify publishing are workshop additions. They require the attendee's own verified account, exact approval and provider readback. Advertising launch/restart and automatic whole social campaign activation are disabled; use an explicitly reviewed owned UI operation. Keep these limits visible when teaching or reporting.

Keep credentials, private recipient records and correspondence off slides and out of shared packages. Run focused local tests with fake providers when changing code. Do not call live outreach or paid fulfillment from tests. Write short, direct English. Use the humanizer editing pass for prose.

Filled configuration and key files must stay outside code and company-motion with mode 0600. Preserve canonical sender/history settings. Social imports require original successful own provisioning, and gifts require fresh owned UI evidence bound to native scheduler reads. Revoke wrong grants without replacing the pilot or clearing commitments. Provider queues need separate native controls.
