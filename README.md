# Build your own Agentic GTM: Part 1

Build two pages for your own target companies. Save the instructions so your local agent can do it again.

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

Part 1 has no paid API requirement and sends nothing. Keys and filled configuration stay in a private folder outside this repository. The included credential templates are blank. The database has 16 empty tables.

Keep this project for [Part 2](https://luma.com/jd8tm0ij) and [Part 3](https://luma.com/wucyo6fw). Each session includes its own presentation and prompts.

## Rebuild this edition

Install authoring/requirements.txt in a separate authoring environment. Run authoring/build_booklet.py, then authoring/build_materials.py, then authoring/build_html.py. The course contains only Part 1. A single-session build does not produce a complete-series presentation.

Local software checks use fake providers. They do not prove delivery or spending. Dated examples and attribution limits are in sources/V5-WORKSHOP-SOURCES.md.

## Final Part 1 edition

`part1_v10_final` keeps the original five-section exercise order and all 12 complete prompts. It adds an early glossary, company fields, copy and result-check celebrations, tool alternatives and previews for Parts 2 and 3.
