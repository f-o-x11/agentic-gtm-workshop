# Build my workflow

Use this after running:

```bash
git clone https://github.com/f-o-x11/agentic-gtm-workshop.git
```

Open `agentic-gtm-workshop` in local Codex or Claude Code. Paste:

```text
Read BUILD-MY-GTM.md and follow its Build my workflow instructions. Ask me one question at a time, use my answers to adapt this project, and complete all local preparation that does not need another answer. Start with my company website. Keep external actions paused until I review their exact recipients, messages and costs.
```

## Instructions for the local agent

The owner has asked for the whole supported local workflow. Follow this sequence instead of stopping after one classroom exercise. Keep this repository's authority and source checks. Resume from company-motion/PROGRESS.md when work already exists.

### 1. Learn the company

Ask for the company website first. Read its official product and proof pages. Save source URLs and dates. Explain what the company sells and suggest a buyer segment and offer from those sources. Ask the owner to confirm or correct them. Show conflicting claims; keep unsupported claims out of the work.

Ask one short question at a time. Use answers already given. Complete useful local work between questions. The owner chooses the buyer, offer, countries, first play and spending limits. Suggest a practical default with each choice. Pages plus email are the default when no preference is stated. Read the API guide only for the chosen tools.

Save company-motion/COMPANY.md and PREFERENCES.md. Never use Metadata's senders, prospects, resources or budgets for this company.

### 2. Prepare the local project

Read README.md, AGENTS.md and code/AGENTS.md. Save the company brief before running this from code/:

```bash
python3 -B gtm.py bootstrap --company-brief ../company-motion/COMPANY.md
```

Verify its actual interpreter and generated AUTHORITY.md and AGENTS.md. Use that saved interpreter for later commands. If Python is missing, name the official installer and resume after installation. Keep company files in company-motion/. Keep filled configuration and credentials in an owner-only directory outside the entire repository. Ask for private file paths, never keys in chat.

### 3. Build something useful

Ask for two real target-company domains, or suggest two for confirmation. Use the Part 1 prompts in course/course.json to research those companies, build one account page, check every claim against its source, check desktop and phone layout, save a reusable page skill and build page two from it. Preserve page one's hash. Open both pages for the owner to review.

Then use the Part 2 flow and target-list prompts to save EXECUTION-FLOW.md and TARGETS.csv. Prepare ten confirmed companies if the owner wants a pilot. Save actual exclusions and recipient evidence before marking any contact ready. Targets may remain company-only while contacts are researched.

### 4. Connect only the selected tools

Ask which supported accounts the owner can connect now. Read API-CONNECTIONS.md, SETUP-SEQUENCE.md and code/README.md for those exact operations. Use the supplied blank configuration template and the CLI's actual help. Initialize from code/ with the owner's private configuration path. Confirm each provider's returned owner and selected resource. Save private receipts locally; summarize status in CONNECTION-CHECK.md.

No keys are needed for local page building. Email needs owned Google access, current exclusions and valid-email evidence. Loop & Tie also needs a funded owned team, exact collection, fresh authenticated meeting-gate proof and approved gift terms. Gojiberry needs a separate owned campaign and list, its sender seat and a confirmed recipient. A successful login or catalogue read does not prove delivery.

Before a paid lookup, show its actual balance, cost and bounded research scope. Before any send, gift, public page or campaign change, show the exact recipient, content, resource and cost for approval. A key grants access; it does not grant spending or sending authority. Store approved scope through the existing runtime, not just in a note.

### 5. Prove the chosen play

Prepare the exact messages and page previews. With the owner's exact approval, run one controlled canary through the supplied runtime. Read back the actual native result. Then repeat the same action key and verify no duplicate. Continue to the approved pilot only when the canary and every recipient check pass. Keep uncertain actions held and reconcile them; never resend them to find out what happened.

For gifting, distinguish creation, delivery, redemption and meeting completion. For Gojiberry, distinguish queued, invitation sent, accepted and message sent. Delivery may finish after this turn. Read native status later without recreating the action. Scheduling needs separate recurring authority and two observed manual cycles.

Save READY.md with each actual artifact, tested operation and remaining blocker. A disconnected channel stays paused while other local work continues. Finish with clickable page previews, the saved skill, workflow, target list, connection status and the exact next action. Do not call the whole engine replicated when a channel has only been prepared or read.

Automatic reply sending, meeting-write automation, physical mail and advertising launch/restart are not implemented by this package. Mark these as unsupported extensions instead of claiming success.
