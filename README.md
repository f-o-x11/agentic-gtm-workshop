# Build your own Agentic GTM: Part 1

Build two unpublished pages for your own target companies. They stay on your computer. Save the instructions so your local agent can do it again.

## Start here

Run this in local Codex, Claude Code or your terminal:

```bash
git clone https://github.com/f-o-x11/agentic-gtm-workshop.git
```

Use macOS or Linux. On Windows, use Codex or Claude Code inside an installed WSL environment. Native Windows has not been verified.

Open agentic-gtm-workshop as your local project. If you downloaded the ZIP, unzip it and open that folder instead.

Open [Participant-Booklet.html](Participant-Booklet.html). Expand the first embedded prompt. Fill in your website, buyer segment, offer and two target domains, then copy it into your local agent. Read the company brief it creates. Continue with one exercise at a time.

## Keep these open

| File | Use |
|---|---|
| [Part-1-Presentation.html](Part-1-Presentation.html) | Follow the live workshop. Prompts are embedded. |
| [Part-1-Presentation.pdf](Part-1-Presentation.pdf) | Review or print the slides. |
| [Participant-Booklet.html](Participant-Booklet.html) | Instructions, checks, embedded prompts and repairs. |
| [Participant-Booklet.pdf](Participant-Booklet.pdf) | Print the booklet. |
| [Recordings.html](Recordings.html) | Full recorded replay, timestamp jumps and Gil's Zoom clips. Sign in to the workshop site to watch. |
| START-HERE.html | Optional helper for filling in the same startup prompt. |
| API-CONNECTIONS.html | Get and save one key at a time. Part 1 needs no key. |
| API-CONNECTIONS.md | Short key-saving reference. |
| PREWORK.md | The short setup checklist. |
| code/ | The prepared local program. Keep its 20 files together. |

## Five sections

1. See the working examples.
2. Set up your company.
3. Choose two target companies.
4. Build and check your first page.
5. Save the skill. Build page two.

Use your company website and two target-company domains. The agent asks for missing details. A website block can use official text you paste. Unsupported claims must be removed.

Your files go in company-motion/. Commands run from code/. The launcher saves and reuses a supported Python interpreter. If none exists, it gives the official installer. No Homebrew is required.

Part 1 has no paid API requirement and sends nothing. Publishing is not required for completion. Keys and filled configuration stay in a private folder outside this repository. The included credential templates are blank. The database has 16 empty tables.

Keep this project for [Part 2](https://luma.com/jd8tm0ij) and [Part 3](https://luma.com/wucyo6fw). Each session includes its own presentation and prompts.

## Rebuild this edition

Install authoring/requirements.txt in a separate authoring environment. Run authoring/build_booklet.py, then authoring/build_materials.py, authoring/build_html.py and authoring/build_recordings.py. The course contains only Part 1. A single-session build does not produce a complete-series presentation.

Local software checks use fake providers. They do not prove delivery or spending. Dated examples and attribution limits are in sources/V5-WORKSHOP-SOURCES.md.

## Final Part 1 edition

The current edition keeps the original five-section exercise order and all 12 complete prompts. It includes an early glossary, company fields, tool alternatives and previews for Parts 2 and 3. Confetti appears only after confirmed chapter checks.

The Agency Episode 1 precedes the glossary. The complete recorded build follows Episode 1, with all 54:51 of footage shown at twice speed and narration in Gil's AI voice. Episode 2 precedes target research. Episode 3 precedes the break. The Industrialist commercial precedes the first-page exercise. Episodes 4 to 7 and The Grind are reserved for Parts 2 and 3. The two-hour live plan includes 90 minutes of steps, ten minutes of Agency videos and twenty minutes of help. The full 27:26 walkthrough is an optional recording to watch before class or use for help.

Private recording files and attendee portraits are not in this repository or its ZIP. The recorded-build page links to the existing password-protected workshop site. `part1_v10_final` remains the earlier tagged snapshot.
