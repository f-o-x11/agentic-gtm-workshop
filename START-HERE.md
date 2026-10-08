# Start here

1. Run this command in Codex, Claude Code or your terminal:

```bash
git clone https://github.com/f-o-x11/agentic-gtm-workshop.git
```

2. Open agentic-gtm-workshop as your local Claude Code or Codex project. It contains `START-HERE.html`, `prompts.html` and the `code` folder. The agent runs program commands from `code/`.
3. Open `Participant-Booklet.pdf` and `prompts.html`. Copy the first full prompt. Replace the website, buyer segment, offer and two target domains, then paste it into the local agent.
4. Review the saved company brief before the next exercise. Keep the same project for the next session.

You do not need API keys for Part 1. The starter uses an existing supported Python version, or gives you the official installer link.

The browser shows prompts. Your local agent works with the files. Never enter API keys in a browser helper.

## Full startup prompt

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

## Next step

review your company brief. Open `prompts.html#p1-company`.

## Build your Part 1 page workflow

For an owner-requested build outside the guided exercises, paste:

```text
Read BUILD-MY-GTM.md and follow its Build my workflow instructions. Ask me one question at a time, use my answers to adapt this project, and complete all local preparation that does not need another answer. Start with my company website. Keep external actions paused until I review their exact recipients, messages and costs.
```

Full instructions: BUILD-MY-GTM.md. External actions stay paused until their exact scope is approved.
