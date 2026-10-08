# Build your own Agentic GTM: Part 1

Use your company website and two target-company domains. No API keys are needed.

## Start here

```bash
git clone https://github.com/f-o-x11/agentic-gtm-workshop.git
```

Open this folder in local Codex or Claude Code. Open START-HERE.html. Add your website and copy its full prompt. Review the company brief before continuing. Keep prompts.html open to copy each complete exercise.

Program commands run from code/. Your company files live in company-motion/. Keys belong outside this repository.

## Finish with

- Your company facts and paused operating instructions.
- Two sourced target briefs and two reviewed pages.
- One saved page skill successfully reused.
- A progress record and the exact next setup task.

## Section 1: See Metadata's working examples

See one real Zuora page and two clearly labeled message drafts.


## Section 2: Set up your company

COMPANY.md, saved setup and local rules.


### Open START-HERE. Add your website once.

Reference: p1-install

Time: 12 minutes. Difficulty: Easy.

Tools: Local Codex or Claude Code; file and web access. No API credits..

1. Open your cloned folder in local Codex or Claude Code.
2. Open START-HERE.html in your browser.
3. Enter your website once. Copy the prompt as it is.
4. Paste it into your local agent. Open COMPANY.md.

Copy the complete prompt from prompts.html#p1-install.

```text
Help me build my company's GTM workflow one step at a time.
Website: [YOUR_COMPANY_WEBSITE]
I have cloned agentic-gtm-workshop and opened it as this local project. Read README.md, AGENTS.md and START-HERE.md. If my website is missing or a placeholder remains, ask for the actual URL first. Ask only for the buyer segment, offer or target domains that official sources cannot supply. Suggest real targets for my confirmation if needed.
Use this workshop folder as my local project. Keep runtime in code/ and outputs in company-motion/. Run commands from code/.
Read my official website and save company-motion/COMPANY.md with sourced facts, the segment, offer, proof and actual next-step link. Ask only for missing facts. If the site blocks access, use official text I paste.
After company-motion/COMPANY.md exists, run from code/:
python3 -B gtm.py bootstrap --company-brief ../company-motion/COMPANY.md
Use its saved verified Python executable for later commands and standalone scripts.
If Python needs installation, name the official installer and stop there. Do not install Homebrew.
Read company-motion/AUTHORITY.md and company-motion/AGENTS.md. Keep outreach and spending paused.
Save the confirmed target domains, if selected, and the actual bootstrap result in company-motion/SETUP.md. Append the completed step, actual file paths, checks and next task to company-motion/PROGRESS.md. Do not run later exercises.
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

Tools: Codex web access and your official website. No paid API required..

1. Read COMPANY.md. Check the buyer, offer and next-step link.
2. Open its proof sources. Resolve conflicting numbers or leave them out.
3. Confirm the brief. Use it for both account pages.

Copy the complete prompt from prompts.html#p1-company.

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

Tools: Prepared bootstrap and your saved company brief. No API..

1. Open AUTHORITY.md and AGENTS.md. Your local rules and sending limits.
2. Confirm sending and spending are paused.
3. Ask your agent to repair either missing file. Keep the existing company brief.

Copy the complete prompt from prompts.html#p1-authority.

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

Tools: Official target-company website. No paid API required..

1. Choose the first target website. Use a real company you want to sell to.
2. Save three useful facts. Record its product, buyers and a relevant current need.
3. Mark unsupported ideas as suggestions. A proposed campaign is not a known business problem.

Copy the complete prompt from prompts.html#p1-one-source.

```text
Before writing a target brief, open the supplied domain and confirm that it is the company I selected. If it is parked, for sale, redirected to an unrelated company or ambiguous, show the problem and ask me to confirm the correct domain. Do not silently substitute another company or use that page as buyer evidence.

Use the first target domain saved during setup.
Read its official website and my company brief.
Save company-motion/targets/ACTUAL-DOMAIN.md with its product, buyers and facts relevant to our offer. Use the actual domain in the path.
For each fact, include the source URL, exact supporting text and read date.
Keep ideas separate from facts. Do not invent revenue, spend, buying intent or a recent launch.
Show one sourced target fact and the page idea it supports.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: research the second target and save the target list.
```

You should have:

- One dated target brief.

Check before continuing:

- Each target fact has its exact source excerpt and read date.
- The page idea is labeled as a suggestion.
- The opened domain belongs to the selected company. Any correction was confirmed by the owner.

If blocked: Paste the target’s official source text into Codex. Keep the official URL and retrieval date.

Next: research the second target and save the target list.

### Save your two target companies

Reference: p1-target-fit

Time: 5 minutes. Difficulty: Easy.

Tools: Two real target domains and browser access. No paid API required..

1. Read the saved target domains. Use the two companies from setup.
2. Research the second company. Save its facts and one supported fit reason.
3. Save the two-company list. Keep uncertain fit visible for review.

Copy the complete prompt from prompts.html#p1-target-fit.

```text
Before writing a target brief, open the supplied domain and confirm that it is the company I selected. If it is parked, for sale, redirected to an unrelated company or ambiguous, show the problem and ask me to confirm the correct domain. Do not silently substitute another company or use that page as buyer evidence.

Read the two target domains saved during setup.
Research the second company from its official sources and save its target brief.
Save company-motion/TARGETS.md with both actual domains, products, buyers and one sourced reason our offer fits each.
Keep uncertain fit marked for review. Company fit supports a page idea, not eligibility for a gift or demo incentive. Use company and public professional facts, not private personal traits. This list is page-building input, not permission to contact a person.
Show both companies plainly, one row each.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: build the first account page.
```

You should have:

- Two reviewed target briefs and company-motion/TARGETS.md.

Check before continuing:

- Each company has one supported reason for the page.
- The opened domain belongs to the selected company. Any correction was confirmed by the owner.

If blocked: Use two named companies you already know, then paste their official product pages.

Next: build the first account page.

## Section 4: Build and check your first page

First HTML page and PAGE-REVIEW.md.


### Build the page for your first target

Reference: p1-build-page

Time: 10 minutes. Difficulty: Easy.

Tools: Codex file/browser access and the two saved briefs. No API credits..

1. Copy the page prompt. Codex reads the two saved briefs.
2. Open the generated page. View the HTML in your browser.
3. Check the headline and offer. They must refer to the correct seller and buyer.

Copy the complete prompt from prompts.html#p1-build-page.

```text
For browser review, use a local HTTP preview bound to 127.0.0.1. Serve only a dedicated folder containing this page and its required public assets, never the whole workshop or private files. Open the exact HTTP URL in the browser and view the page. If this browser cannot reach the preview, name the actual limitation and offer an existing app preview or manual browser check. A local preview is supported; do not call localhost prohibited. Keep source and claim checks separate from the browser check. After visual review, stop the preview process you started. If the attendee still needs it for review, record its actual process ID and exact cleanup command in company-motion/PAGE-REVIEW.md. Do not stop another application's server.

Build company-motion/pages/ACTUAL-DOMAIN/index.html for the first target using our company brief and its target brief.
Make one standalone responsive HTML file with styles, scripts and required graphics inside it.
Use our actual brand, one buyer-specific idea, our actual offer, supported proof and our real next-step link.
Keep suggestions distinct from facts. Do not invent a testimonial, logo, demo length, result or recent launch.
If proof is weak, use the supported product description or omit that proof block.
Save claim/source notes beside the page and open the actual file in a browser.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: check every claim and review desktop and phone layouts.
Use an unused port. If it is occupied, choose another port and report the exact URL. Never reuse an unrelated server. Record whether the phone check used device emulation, a real phone or a resized window. A resized window alone is a narrow-layout check, not proof of mobile-device behavior.
```

You should have:

- A real HTML page and source notes.

Check before continuing:

- The page opens.
- The seller, target and next step are correct.
- No unsupported proof appears.
- The exact account page opens in the local HTTP preview and is visually checked.

If blocked: If browsing fails, use the saved official-source text. If preview is unavailable, open the generated file from its path. If the preview tool cannot reach localhost, open the same HTTP URL in your own browser and save the actual manual result.

Next: check every claim and review desktop and phone layouts.

### Check every claim. Then check the page layout.

Reference: p1-page-review

Time: 10 minutes. Difficulty: Easy.

Tools: Browser and generated HTML. No paid API required..

1. Read each factual claim. Open its exact source and supporting text.
2. Remove unsupported promises. Check demo length, numbers, testimonials and words such as "just launched".
3. Check desktop and phone. Measure the browser viewport, not the Mac window.
4. Open the next-step link. Repair failed checks and rerun them.

Copy the complete prompt from prompts.html#p1-page-review.

```text
For browser review, use a local HTTP preview bound to 127.0.0.1. Serve only a dedicated folder containing this page and its required public assets, never the whole workshop or private files. Open the exact HTTP URL in the browser and view the page. If this browser cannot reach the preview, name the actual limitation and offer an existing app preview or manual browser check. A local preview is supported; do not call localhost prohibited. Keep source and claim checks separate from the browser check. After visual review, stop the preview process you started. If the attendee still needs it for review, record its actual process ID and exact cleanup command in company-motion/PAGE-REVIEW.md. Do not stop another application's server.

Review every factual claim in the saved HTML, including headings, buttons, captions and footer.
Save a claim ledger with the claim, exact source URL and supporting excerpt. Remove or rewrite unsupported demo length, results, testimonials and recency claims. Suggestions must be labeled.
Check the page in actual browser viewports at 1440 x 900 and 390 x 844. Read window.innerWidth and window.innerHeight before checking overflow; resizing a Mac window alone is not proof of the viewport.
If the browser cannot reach 390 pixels, record phone review as unverified and give a device-mode or phone check. Do not report false clipping.
Test the next-step link. Repair failures and rerun them.
Save company-motion/PAGE-REVIEW.md with the claim ledger, measured viewport sizes, screenshots and unresolved checks.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: save the checked page method as a skill.
Use an unused port. If it is occupied, choose another port and report the exact URL. Never reuse an unrelated server. Record whether the phone check used device emulation, a real phone or a resized window. A resized window alone is a narrow-layout check, not proof of mobile-device behavior.
```

You should have:

- Reviewed page plus company-motion/PAGE-REVIEW.md.

Check before continuing:

- Every factual claim has exact supporting text or is removed.
- Measured innerWidth matches the recorded viewport.
- Phone overflow is measured inside that viewport.
- Failed checks are rerun after repair.
- The exact account page opens in the local HTTP preview and is visually checked.

If blocked: If the agent cannot set a true phone viewport, record that check as unverified and use your browser's device mode or your phone. Do not label a Mac window-size limit as clipped page content. If the preview tool cannot reach localhost, open the same HTTP URL in your own browser and save the actual manual result.

Next: save the checked page method as a skill.

## Section 5: Save the skill. Build page two.

SKILL.md, second page and completed file check.


### Save your page-building instructions as a skill

Reference: p1-save-skill

Time: 6 minutes. Difficulty: Easy.

Tools: Reviewed first page and source notes. No API credits..

1. Copy the skill prompt. Use your checked page and source notes.
2. Read the saved SKILL.md. It must say what to read, build and check.
3. Keep company-motion/skills/account-page/SKILL.md. The next prompt reads this file by its path.

Copy the complete prompt from prompts.html#p1-save-skill.

```text
Create company-motion/skills/account-page/SKILL.md from the method that passed review.
Include the required company and target facts, standalone HTML output, source ledger, missing-proof rule, real next-step link and measured desktop/phone checks. Start the file with simple frontmatter: name: account-page and a one-line description. Use sections Inputs, Steps, Output and Checks. Read the saved file and check those fields and headings with local file tools or the Python standard library. No global validator, plugin installation or PyYAML package is needed.
Use the reviewed first page as the example. Make the instructions usable in a fresh local agent session.
Require each factual claim to have exact source support. Keep unsupported facts out.
Show the complete saved skill. Tell me that the next prompt reads company-motion/skills/account-page/SKILL.md directly. No slash command or skill installation is needed.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: use that skill for the second target.
```

You should have:

- company-motion/skills/account-page/SKILL.md.

Check before continuing:

- The skill names inputs, output and checks.
- A missing source has a defined response.
- The saved skill can be read by its exact file path.
- Frontmatter name/description and Inputs, Steps, Output and Checks are present without an extra installation.

If blocked: Use the complete skill prompt with the reviewed page and source notes. Save the skill in company-motion, then inspect it.

Next: use that skill for the second target.

### Use the skill for your second target

Reference: p1-repeat

Time: 8 minutes. Difficulty: Easy.

Tools: Saved account-page skill and second target brief. No paid API required..

1. Copy the next prompt. It reads the saved SKILL.md file.
2. Open both pages. Compare the fact, headline and campaign idea.
3. Save the result. Keep the first page unchanged.

Copy the complete prompt from prompts.html#p1-repeat.

```text
For browser review, use a local HTTP preview bound to 127.0.0.1. Serve only a dedicated folder containing this page and its required public assets, never the whole workshop or private files. Open the exact HTTP URL in the browser and view the page. If this browser cannot reach the preview, name the actual limitation and offer an existing app preview or manual browser check. A local preview is supported; do not call localhost prohibited. Keep source and claim checks separate from the browser check. After visual review, stop the preview process you started. If the attendee still needs it for review, record its actual process ID and exact cleanup command in company-motion/PAGE-REVIEW.md. Do not stop another application's server.

Read company-motion/skills/account-page/SKILL.md. Follow that saved file to build a page for the second target in company-motion/TARGETS.md. Do not assume a slash command exists.
Keep the first page unchanged.
Run the skill's full claim/source review and measured desktop/phone checks. A missing browser check stays unverified.
Show a three-row comparison of the two pages: one sourced target fact, the headline, and the campaign idea. The second page must have a supported fact about the second company and an idea built around that fact. If only the name changed, revise it. Remove first-company facts and copied proof that does not fit. Show that the first page stayed unchanged.
Save company-motion/SKILL-TEST.md with both page paths, review evidence and remaining issues.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: check the Part 1 files after the break.
Use an unused port. If it is occupied, choose another port and report the exact URL. Never reuse an unrelated server. Record whether the phone check used device emulation, a real phone or a resized window. A resized window alone is a narrow-layout check, not proof of mobile-device behavior.
```

You should have:

- Second reviewed page and company-motion/SKILL-TEST.md.

Check before continuing:

- Each page addresses its own buyer.
- The first page remains intact.
- The saved skill produced both outputs.
- The exact account page opens in the local HTTP preview and is visually checked.
- The second page changes a sourced target fact, the headline and the campaign idea, not just the company name.

If blocked: If the second website blocks access, use its saved official-source text. Label that source path. If the preview tool cannot reach localhost, open the same HTTP URL in your own browser and save the actual manual result.

Next: check the Part 1 files after the break.

### Check your files. Repair only a failed check.

Reference: p1-checkpoint

Time: 5 minutes. Difficulty: Easy.

Tools: Your generated files and actual browser results. No new credits..

1. Copy the checkpoint prompt. Your agent opens each required file.
2. Repair a failed check, if one exists. If all checks passed, skip repair.
3. Read PROGRESS.md. Check the result and your next task.

Copy the complete prompt from prompts.html#p1-checkpoint.

```text
Open our company brief, setup receipt, company-motion/AUTHORITY.md, company-motion/AGENTS.md, target list, two target briefs, two pages, page review, saved skill and skill test.
If company-motion/AUTHORITY.md or company-motion/AGENTS.md is missing, rerun bootstrap with the existing company brief. Preserve all working outputs and history.
Append actual paths and passed or missing checks to company-motion/PROGRESS.md.
Keep created, reviewed and published separate. If a check failed, repair the first actual local issue and rerun that check. If every required check passes, write Part 1 complete and skip repair. Do not invent an error or manufacture extra work.
Name one exact next action for each remaining gap.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: use individual help for a real failed check, or save your completed project and register for the next workshop.
```

You should have:

- PROGRESS.md with actual paths and passed or missing checks.

Check before continuing:

- Required files are actually opened.
- Missing authority/instruction files can be repaired in place.
- Created, reviewed and published remain separate labels.
- An all-pass result skips repair and is recorded as complete.

If blocked: Share the failed file or error with the repair prompt. Continue from the same project.

Next: use help for a real gap, or save your completed project.

### Individual help, if you need it

Reference: p1-help

Time: 30 minutes. Difficulty: Help.

Tools: Codex and your workshop project..

1. Open PROGRESS.md. Check for a real unfinished item.
2. If one exists, copy that task's repair prompt.
3. If all checks passed, save your work. No repair needed.

Copy the complete prompt from prompts.html#p1-help.

```text
Read company-motion/PROGRESS.md. If all required Part 1 checks already pass, record Part 1 complete, name the saved brief, both pages and skill, then stop. Do not invent a failed check. Otherwise find the first real unfinished Part 1 check.
Repair that local cause in this same project. Preserve working pages, source notes and the saved skill.
Rerun its success check and update company-motion/PROGRESS.md.
If only phone review is missing, show the exact manual device-mode or phone check instead of inventing a pass.
Append this step, actual artifact, check and next task to company-motion/PROGRESS.md. Show the output. Stop. Next: save your project and register for the next workshop.
```

You should have:

- A repaired actual gap, or a saved all-pass completion record.

Check before continuing:

- A real failed check is rerun, or an all-pass result skips repair.

If blocked: Save the unresolved error and named missing setup. Do not reset the project.

Next: save your project and register for the next workshop.

# Keep your project

Save your brief, target list, reviewed pages, skill and PROGRESS.md. Your files are the starting point for the next workshop.

[Register for Part 2](https://luma.com/jd8tm0ij). [Register for Part 3](https://luma.com/wucyo6fw).

# Words you may need

| Word | Meaning here |
|---|---|
| Coding agent | Codex or Claude Code, working with files on your computer. |
| Company brief | A saved description of your product, buyers, offer and source-backed proof. |
| Skill | A saved set of instructions your agent can reuse, such as building an account page. |
| Execution flow | The order of work and the conditions for continuing or stopping. |
| Runtime | The local program that checks prepared actions and records results. |
| API | A connection that lets a program use a tool, such as Loop & Tie. |
| API key | A private password for that connection. |
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
