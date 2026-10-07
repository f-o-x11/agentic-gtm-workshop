# Agentic GTM workshop

Build your company brief, two account pages and a reusable skill. Then connect one email channel and operate the same project. Each of the three workshops has five chapters,90 guided minutes and30 minutes for help.

## Get the entire workshop

```bash
git clone https://github.com/f-o-x11/agentic-gtm-workshop.git
```

This public repository needs no GitHub account, collaborator invitation or workshop API key. The command retrieves the PDFs, booklet, prompt helpers, editable course, illustrations and 20-file program together. You can also [download the workshop ZIP](https://github.com/f-o-x11/agentic-gtm-workshop/archive/refs/heads/main.zip), then unpack it.

Open the cloned folder as your local project in Codex or Claude Code. Open START-HERE.html, copy its one complete prompt and add your website. The agent writes the company brief, checks setup and stops. If you received a ZIP instead, unpack it before opening the folder.

## Five chapters per workshop

### Part 1

1. What you will build.
2. Start your company project.
3. Choose two target companies.
4. Build and check your first page.
5. Save the skill and build page two.

### Part 2

1. Connect your email account.
2. Set the rules and choose ten companies.
3. Find buyers and write the emails.
4. Review and send your own test.
5. Run the ten-company pilot.

### Part 3

1. Read replies and bookings.
2. Check one complete play.
3. Repeat without duplicating work.
4. Prepare a schedule when ready.
5. Record results and choose the next play.

## Files to use

| File | Use |
|---|---|
| START-HERE.html | One complete startup prompt, then stop. |
| prompts.html | Full exercise prompts, repair prompts and next steps. |
| Complete-Presentation.pdf | All three workshops, with chapter bookmarks. |
| Part-1-Presentation.pdf | Company context, pages and skill reuse. |
| Part-2-Presentation.pdf | Exact message review and conditional email pilot. |
| Part-3-Presentation.pdf | Outcomes, repeat operation and optional channels. |
| Participant-Booklet.pdf | Full prompts, expected files, checks and fallbacks. |
| API-Setup-Guide.pdf | Required connections by session and optional tools. |
| CHAPTERS.md | Fifteen chapters, outcomes and time budget. |
| PREWORK.md | Prepare account access before its session. |
| GLOSSARY.md | Short definitions. |
| SECURITY.md | Independent security scan, fixes and publication limits. |
| code/ | The 20 runtime files. |
| course/ | Editable slide data and booklet source. |

## Your files and keys

Part 1 requires no paid API. Put company files in company-motion/. Your working database is company-motion/gtm.sqlite, which Git ignores. The tracked code/data/gtm.sqlite remains an empty template. Keep filled credentials and configuration in a private folder outside this cloned repository. The program rejects paths and symlinks inside this repository. Never paste keys into HTML helpers or commit recipient files or provider receipts. The supplied template has 16 empty tables; every credential template is blank.

Python 3.10 or newer is needed for the local program. The launcher can start from Python 3.9 and selects a verified newer interpreter. If python3 is not installed, the agent finds another installed compatible executable or links the official installer: https://www.python.org/downloads/. No Homebrew is required.

Runtime commands run from code/. Missing interpreter receipt triggers rediscovery. An unusable saved interpreter requires bootstrap --reset-python. Existing company facts, authority and history stay intact during repair.

Part 2 live email needs an owned sender, current exclusions, current employer and valid-email evidence, exact owner approval and Gmail Sent proof. Provider waits can continue after class. Part 3 extra channels are optional. Prepared, queued, sent, delivered, replied and booked are different results.

The portable package does not implement automatic replies, meeting-write automation, physical postal fulfillment or advertising launch/restart. Core completion is your local framework and reviewed page play. Do not claim another channel works until its native result is observed.

## Inspect or rebuild the materials

Attendees use the existing PDFs and HTML. Authors can install authoring/requirements.txt in a separate environment, run python3 authoring/build_booklet.py, then python3 authoring/build_materials.py. The build reads only this repository.

Offline runtime checks:

```text
Run code/checks/focused_checks.py and checks/startup_checks.py with the verified Python executable saved in company-motion/.runtime.json. Show both actual results. Do not contact providers.
```

The saved interpreter must be Python 3.10 or newer. The test uses temporary fixtures and fake providers. It does not send real email or use paid API credits. Software tests and AI replay do not establish human beginner completion.

Dated teaching examples and attribution limits are in sources/V5-WORKSHOP-SOURCES.md.
