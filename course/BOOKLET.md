# Build your own Agentic GTM: Part 1

Use your company website and two target-company domains. No API keys are needed.

## Start here

```bash
git clone https://github.com/f-o-x11/agentic-gtm-workshop.git
```

Open this folder in local Codex or Claude Code. Keep this booklet open beside Zoom. Expand the first complete prompt here. Add your website, buyer segment, offer and two target domains, then copy it into your local agent. Review the company brief before continuing.

Program commands run from code/. Your company files live in company-motion/. Keys belong outside this repository.

## Words you may need

| Word | Meaning here |
|---|---|
| Coding agent | Codex or Claude Code, working with files on your computer. |
| Company brief | A saved description of your product, buyers, offer and source-backed proof. |
| Skill | A saved set of instructions your agent can reuse, such as building an account page. |
| Execution flow | The order of work and the conditions for continuing or stopping. |
| Runtime | The local program that checks prepared actions and records results. |
| API | A connection that lets a program use a tool, such as Loop & Tie. |
| API key | A private password for that connection. |
| MCP | A connection that lets your agent use an app’s tools from the conversation. |
| OAuth | A browser sign-in that grants specific account access. |
| Authority | The exact actions, recipients and spending you have approved. |
| Exclusion | A company or person the workflow must not contact. |
| Action key | The saved identifier for one exact prepared action. |
| Self-test | One exact email to your own authorized sender. |
| Receipt | A saved response or native record showing what actually happened. |
| Held | Stopped because a required fact, connection or approval is missing. |
| Reconcile | Read the original provider result without sending another copy. |
| Queued | Waiting with the provider. It has not yet been confirmed sent. |
| Booked | A meeting reservation. It does not show attendance. |


## Finish with

- Your company facts and paused operating instructions.
- Two sourced target briefs and two reviewed pages.
- One saved page skill successfully reused.
- A progress record and the exact next setup task.

## Section 1: See Metadata's working examples

See the actual page, email and gift examples.


## Section 2: Set up your company

COMPANY.md, saved setup and local rules.


### Open the cloned folder. Build your company brief.

Reference: p1-install

Time: 12 minutes. Difficulty: Easy.

Tools: Local Codex or Claude Code; file and web access. No API credits.

1. Open agentic-gtm-workshop in local Codex or Claude Code.
2. Open Participant-Booklet.pdf and the embedded prompt.
3. Copy the full startup prompt. Replace its five inputs. Your website, buyer segment, offer and two target domains.
4. Paste into your local agent. Review COMPANY.md when it stops.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Help me build my company's GTM workflow one step at a time.
Website: [YOUR_COMPANY_WEBSITE]
Buyer segment: [BUYER_SEGMENT]
Offer: [COLD_OFFER]
Targets: [TARGET_1_DOMAIN], [TARGET_2_DOMAIN]
I have cloned agentic-gtm-workshop and opened it as this local project. Read README.md, AGENTS.md and START-HERE.md. If an input is blank, ask only for what official sources cannot supply. Suggest real targets for my confirmation if needed.
Use this workshop folder as my local project. Keep runtime in code/ and outputs in company-motion/. Run commands from code/.
Read my official website and save company-motion/COMPANY.md with sourced facts, the segment, offer, proof and actual next-step link. Ask only for missing facts. If the site blocks access, use official text I paste.
After company-motion/COMPANY.md exists, run from code/:
python3 -B gtm.py bootstrap --company-brief ../company-motion/COMPANY.md
Use its saved verified Python executable for later commands and standalone scripts.
If Python needs installation, name the official installer and stop there. Do not install Homebrew.
Read company-motion/AUTHORITY.md and company-motion/AGENTS.md. Keep outreach and spending paused.
Save both target domains and the actual bootstrap result in company-motion/SETUP.md. Append the completed step, actual file paths, checks and next task to company-motion/PROGRESS.md. Do not run later exercises.
Show the output and success check. Stop. Next: review your company brief.
```

You should have:

- COMPANY.md, SETUP.md, AUTHORITY.md and AGENTS.md.

Check before continuing:

- Setup found a supported Python version.
- Sending and spending are paused.
- The agent stops and names the next task.

If blocked: If web access is blocked, paste your official website text. If Python is missing, use the launcher's named official installer, then rerun this same step.

Next: review your company brief.

### Check your company facts, buyers and offer

Reference: p1-company

Time: 8 minutes. Difficulty: Easy.

Tools: Codex web access and your official website. No paid API required.

1. Read COMPANY.md. Check the buyer, offer and next-step link.
2. Open its proof sources. Resolve conflicting numbers or leave them out.
3. Confirm the brief. Use it for both account pages.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Review company-motion/COMPANY.md with me.
Show the buyer segment, offer, next-step link and the source behind each proof claim.
If the website has conflicting numbers, show both URLs and exact excerpts. Do not choose a number without support.
Ask at most two short questions for missing company facts. Keep unsupported claims out of the brief.
Save my corrections and preserve the source URLs and read dates.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: review the operating instructions.
```

You should have:

- company-motion/COMPANY.md with sourced company facts.

Check before continuing:

- Every proof claim has a supporting source.
- Buyer segment and offer match your answers.
- Conflicting website numbers are flagged, not silently selected.

If blocked: Paste text from your official product and proof pages. Codex saves the pasted source and labels it owner-provided.

Next: review the operating instructions.

### Check the saved rules. Keep sending paused.

Reference: p1-authority

Time: 4 minutes. Difficulty: Easy.

Tools: Prepared bootstrap and your saved company brief. No API.

1. Open AUTHORITY.md and AGENTS.md. Your local rules and sending limits.
2. Confirm sending and spending are paused.
3. Ask your agent to repair either missing file. Keep the existing company brief.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Open company-motion/AUTHORITY.md and company-motion/AGENTS.md.
If either is missing, rerun:
python3 -B gtm.py bootstrap --company-brief ../company-motion/COMPANY.md
Preserve my existing facts, instructions and history.
Show the company name, one-step-at-a-time rule, and paused outreach and spending rules.
If either file conflicts with my company brief, show the conflict for my correction. Do not grant a sender or live channel yet.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: research the first target company.
```

You should have:

- Present, readable AUTHORITY.md and AGENTS.md.

Check before continuing:

- Both files exist.
- No outreach, sender, spend or country authority is invented.

If blocked: Rerun bootstrap with the existing company brief. Preserve the brief and working pages.

Next: research the first target company.

## Section 3: Choose two target companies

Two target briefs and TARGETS.md.


### Research your first target company

Reference: p1-one-source

Time: 5 minutes. Difficulty: Easy.

Tools: Official target-company website. No paid API required.

1. Enter both target domains below. Use company websites. Your entries carry into the next exercises.
2. Copy the research prompt. Paste it into your local agent. Use the same Codex or Claude Code project.
3. Open the target brief your agent saves. Check the company name, facts and source links.

Expand the complete prompt below. Copy it into the same local agent project.

```text
My two target companies are [TARGET_1_DOMAIN] and [TARGET_2_DOMAIN].
Save these two domains in company-motion/SETUP.md. If they replace earlier choices, show the change and preserve earlier research.
Research [TARGET_1_DOMAIN] now. Read its official website and company-motion/COMPANY.md.
Save company-motion/targets/[TARGET_1_DOMAIN].md with its product, buyers and facts relevant to our offer.
For each fact, include the source URL, exact supporting text and read date.
Keep page ideas separate from facts. Do not invent revenue, spend, buying intent or a recent launch.
Show the saved brief and one page idea supported by a sourced fact. Do not research the second company yet.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: research the second target and save the target list.
```

You should have:

- One dated target brief.

Check before continuing:

- Each target fact has its exact source excerpt and read date.
- The page idea is labeled as a suggestion.

If blocked: Paste the target’s official source text into Codex. Keep the official URL and retrieval date.

Next: research the second target and save the target list.

### Save your two target companies

Reference: p1-target-fit

Time: 5 minutes. Difficulty: Easy.

Tools: Two real target domains and browser access. No paid API required.

1. Confirm both target domains below. Your entries are saved from the previous exercise.
2. Copy this prompt into the same local agent. It researches Target 2 and saves your two-company list.
3. Open TARGETS.md. Check both domains and the sourced reason to target each company.

Expand the complete prompt below. Copy it into the same local agent project.

```text
My two target companies are [TARGET_1_DOMAIN] and [TARGET_2_DOMAIN].
Read the saved brief for [TARGET_1_DOMAIN]. If it is missing or names another domain, stop and ask me to rerun the first-target research exercise.
Research [TARGET_2_DOMAIN] from its official sources. Save company-motion/targets/[TARGET_2_DOMAIN].md with exact source excerpts and read dates.
Save company-motion/TARGETS.md with both actual domains, products, buyers and one sourced reason our offer fits each.
Update the selected domains in company-motion/SETUP.md. Preserve earlier research if a domain changed.
Keep uncertain fit marked for review. This list is page-building input, not permission to contact a person.
Show both companies plainly, one row each.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: build the first account page.
```

You should have:

- Two reviewed target briefs and company-motion/TARGETS.md.

Check before continuing:

- Each company has one supported reason for the page.

If blocked: Use two named companies you already know, then paste their official product pages.

Next: build the first account page.

## Section 4: Build and check your first page

First HTML page and PAGE-REVIEW.md.


### Build the page for your first target

Reference: p1-build-page

Time: 10 minutes. Difficulty: Easy.

Tools: Codex file/browser access and the two saved briefs. No API credits.

1. Confirm the target domain below. This is Target 1, the company you researched first.
2. Copy the page prompt. Paste it into the same local agent. The prompt names your target and the exact file to create.
3. Open the page your agent creates. Check the company name, offer and button. Then review its claims and layout.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Build a landing page for [TARGET_1_DOMAIN].
Read company-motion/COMPANY.md and company-motion/targets/[TARGET_1_DOMAIN].md. If either is missing or names the wrong company, stop and name the earlier exercise to complete.
Save the page as company-motion/pages/[TARGET_1_DOMAIN]/index.html.
Create one HTML file that works on desktop and phone. Keep its styles, scripts and required graphics inside it.
Use our brand, an idea relevant to this company, our actual offer, supported proof and our real next-step link.
Keep suggestions distinct from facts. Do not invent a testimonial, logo, demo length, result or recent launch. If proof is weak, use supported product facts or omit that block.
Save claim/source notes beside the page. Open the page in a browser and show it to me.
If the browser blocks the local file, start a local HTTP preview on an unused 127.0.0.1 port. Serve only this page folder and its public assets. Open that preview, then stop it when browser checks are complete.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: check every claim and review desktop and phone layouts.
```

You should have:

- A real HTML page and source notes.

Check before continuing:

- The page opens.
- The seller, target and next step are correct.
- No unsupported proof appears.

If blocked: If the browser blocks the file URL, use a local HTTP preview. Keep any browser check you could not run marked unverified.

Next: check every claim and review desktop and phone layouts.

### Check every claim. Then check the page layout.

Reference: p1-page-review

Time: 10 minutes. Difficulty: Easy.

Tools: Browser and generated HTML. No paid API required.

1. Read each factual claim. Open its exact source and supporting text.
2. Remove unsupported promises. Check demo length, numbers, testimonials and words such as "just launched".
3. Check desktop and phone. Measure the browser viewport, not the Mac window.
4. Open the next-step link. Repair failed checks and rerun them.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Review every factual claim in the saved HTML, including headings, buttons, captions and footer.
Save a claim ledger with the claim, exact source URL and supporting excerpt. Remove or rewrite unsupported demo length, results, testimonials and recency claims. Suggestions must be labeled.
Check the page in actual browser viewports at 1440 x 900 and 390 x 844. Read window.innerWidth and window.innerHeight before checking overflow; resizing a Mac window alone is not proof of the viewport.
If the browser cannot reach 390 pixels, record phone review as unverified and give a device-mode or phone check. Do not report false clipping.
Test the next-step link. Repair failures and rerun them.
Save company-motion/PAGE-REVIEW.md with the claim ledger, measured viewport sizes, screenshots and unresolved checks.
If the browser blocks a local file URL, start a local HTTP preview on an unused 127.0.0.1 port. Serve only this page folder and its public assets. Open the page through that preview, then stop the preview when the browser checks are complete.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: save the checked page method as a skill.
```

You should have:

- Reviewed page plus company-motion/PAGE-REVIEW.md.

Check before continuing:

- Every factual claim has exact supporting text or is removed.
- Measured innerWidth matches the recorded viewport.
- Phone overflow is measured inside that viewport.
- Failed checks are rerun after repair.

If blocked: If the browser blocks the file URL, use a local HTTP preview. Keep any browser check you could not run marked unverified.

Next: save the checked page method as a skill.

## Section 5: Save the skill. Build page two.

SKILL.md, second page and completed file check.


### Save your page-building instructions as a skill

Reference: p1-save-skill

Time: 6 minutes. Difficulty: Easy.

Tools: Reviewed first page and source notes. No API credits.

1. Copy the skill prompt. Use your checked page and source notes.
2. Read the saved SKILL.md. It must say what to read, build and check.
3. Use these instructions for the next page.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Create company-motion/skills/account-page/SKILL.md from the method that passed review.
Include the required company and target facts, standalone HTML output, source ledger, missing-proof rule, real next-step link and measured desktop/phone checks.
Use the reviewed first page as the example. Make the instructions usable in a fresh local agent session.
Require each factual claim to have exact source support. Keep unsupported facts out.
Show the complete saved skill.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: use that skill for the second target.
```

You should have:

- company-motion/skills/account-page/SKILL.md.

Check before continuing:

- The skill names inputs, output and checks.
- A missing source has a defined response.

If blocked: Use the complete skill prompt with the reviewed page and source notes. Save the skill in company-motion, then inspect it.

Next: use that skill for the second target.

### Use the skill for your second target

Reference: p1-repeat

Time: 8 minutes. Difficulty: Easy.

Tools: Saved account-page skill and second target brief. No paid API required.

1. Run the account-page skill. Use the second saved target brief.
2. Open both pages. Compare buyer names and ideas.
3. Save the repeat result. Keep the first page intact.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Use our saved account-page skill to build a landing page for [TARGET_2_DOMAIN].
Read company-motion/targets/[TARGET_2_DOMAIN].md. If it is missing or names another company, stop and ask me to complete the second-target research exercise.
Save the page as company-motion/pages/[TARGET_2_DOMAIN]/index.html.
Keep the first page unchanged.
Run the skill's full claim/source review and measured desktop/phone checks. A missing browser check stays unverified.
Show what changed between the two targets. Remove facts or generic copy carried over from the first company.
Save company-motion/SKILL-TEST.md with both page paths, review evidence and remaining issues.
If the browser blocks a local file URL, start a local HTTP preview on an unused 127.0.0.1 port. Serve only this page folder and its public assets. Open the page through that preview, then stop the preview when the browser checks are complete.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: check the Part 1 files after the break.
```

You should have:

- Second reviewed page and company-motion/SKILL-TEST.md.

Check before continuing:

- Each page addresses its own buyer.
- The first page remains intact.
- The saved skill produced both outputs.

If blocked: If the second website blocks access, use its saved official-source text. Label that source path.

Next: check the Part 1 files after the break.

### Check the files. Fix anything missing.

Reference: p1-checkpoint

Time: 5 minutes. Difficulty: Easy.

Tools: Your generated files and actual browser results. No new credits.

1. Copy the checkpoint prompt. Your agent opens each required file.
2. Fix the first failed check. Keep both pages and the saved skill.
3. Read PROGRESS.md. Check the result and your next task.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Open our company brief, setup receipt, company-motion/AUTHORITY.md, company-motion/AGENTS.md, target list, two target briefs, two pages, page review, saved skill and skill test.
If company-motion/AUTHORITY.md or company-motion/AGENTS.md is missing, rerun bootstrap with the existing company brief. Preserve all working outputs and history.
Append actual paths and passed or missing checks to company-motion/PROGRESS.md.
Keep created, reviewed and published separate. Repair the first available local issue and rerun its check.
Name one exact next action for each remaining gap.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: finish the first remaining issue with individual help.
```

You should have:

- PROGRESS.md with actual paths and passed or missing checks.

Check before continuing:

- Required files are actually opened.
- Missing authority/instruction files can be repaired in place.
- Created, reviewed and published remain separate labels.

If blocked: Share the failed file or error with the repair prompt. Continue from the same project.

Next: finish the first remaining issue with individual help.

### Fix your first unfinished task

Reference: p1-help

Time: 30 minutes. Difficulty: Help.

Tools: Codex and your workshop project.

1. Open PROGRESS.md. Find the first unfinished check.
2. Copy that task's repair prompt from the embedded prompt.
3. Add your error. Rerun the check. Save the result.

Expand the complete prompt below. Copy it into the same local agent project.

```text
Read company-motion/PROGRESS.md and find the first unfinished Part 1 check.
Repair that local cause in this same project. Preserve working pages, source notes and the saved skill.
Rerun its success check and update company-motion/PROGRESS.md.
If only phone review is missing, show the exact manual device-mode or phone check instead of inventing a pass.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: prepare the single email connection before Part 2.
```

You should have:

- One repaired task and updated progress.

Check before continuing:

- The previously failed check is rerun.

If blocked: Save the unresolved error and named missing setup. Do not reset the project.

Next: prepare the single email connection before Part 2.

### Keep building. Join Parts 2 and 3.

Reference: p1-before-part2

Time: 0 minutes. Difficulty: Setup.

Tools: Your saved Part 1 project. Choose later connections before the next session.


Expand the complete prompt below. Copy it into the same local agent project.

```text
Read API-CONNECTIONS.html, API-CONNECTIONS.md and SETUP-SEQUENCE.md for the single email channel.
Prepare my own sender, primary calendar, permitted countries and current customer/deal/opt-out exclusions.
Follow the Google Cloud sign-in guide. It must initialize this fresh email configuration from code/ using python3 -B gtm.py init --config and the actual private path before treating email setup as ready; bootstrap alone is local file setup. Use the project launcher and the actual private client-file path. Record the authenticated sender and calendar; name any Workspace-admin blocker.
Prepare ten distinct target domains and current buyer contacts plus my own self-test address.
Read the actual ZeroBounce balance and show the validation cost. Ask for my bounded paid-validation approval before spending credits. Keep original pending request IDs.
Save company-motion/CONNECTION-CHECK.md with each actual result or blocker. Keep outreach paused.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: keep this project and prepare your email before Part 2.
```

You should have:

- CONNECTION-CHECK.md with ready or blocked email prerequisites.

Check before continuing:

- Own Google profile and calendar reads succeed.
- Actual ZeroBounce credits and paid validation scope are known.
- Current exclusions and permitted countries are ready.

If blocked: Without sender authorization, Part 2 can prepare messages. It cannot prove live sending.

Next: keep this project and prepare your email before Part 2.

## Tools for the next sessions

Use the tools you already have. Part 1 needs none of these connections.

### Enrich company and buyer facts

[Sixtyfour](https://www.sixtyfour.ai/), [RocketReach](https://rocketreach.co/api), [MoltSets](https://moltsets.com/), [Triguna](https://triguna.ai/), [Adyntel](https://www.adyntel.com/)

People and company data. Adyntel adds advertising activity.

Needs: Your provider account, API access and lookup credits.

### Send email

[Google directly](https://developers.google.com/gmail/api), [Instantly.ai](https://developer.instantly.ai/), [Apollo.io](https://docs.apollo.io/reference/apollo-api)

An already connected Instantly or Apollo mailbox can avoid a new Google API setup. Company permissions still apply.

Needs: A connected sender and a plan with API access.

### Send a gift invitation

[Loop & Tie](https://docs.loopandtie.com/reference/oauth-20-api-access), [Sendoso](https://www.sendoso.com/platform/features/mcp)

Create gift invitations and read the provider’s result.

Needs: API or MCP access and your approved gift budget.

### Run advertising

[Metadata.io MCP](https://metadata.io/developers)

Build audiences, creatives and campaigns. Manage 12 channels through one platform.

Needs: A Metadata account and connected ad accounts.

The supplied sending adapters use Gmail and Loop & Tie. Other providers need their own connection. Company permissions and account policies still apply.


# Keep your project

Save your brief, target list, reviewed pages, skill and PROGRESS.md. Your files are the starting point for the next workshop.

Part 2: choose ten accounts, check buyer data, preview your emails, then send and verify one approved self-test.

Part 3: check replies and bookings, add gift and LinkedIn actions, connect advertising, then repeat within your limits.

[Register for Part 2](https://luma.com/jd8tm0ij). [Register for Part 3](https://luma.com/wucyo6fw).
