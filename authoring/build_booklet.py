from pathlib import Path
import json,datetime
R=Path(__file__).resolve().parents[1];d=json.loads((R/'course/course.json').read_text())
lines=['# Build your own Agentic GTM','', 'Participant booklet. October 2026.','', 'Use one local project for all three sessions. The starter code is prepared. Your work is to adapt it to your company, inspect the outputs and run only the actions you approve.','', '## Begin with a useful file','', '1. Open the workshop folder in Codex or Claude Code. Unpack it first if you received a ZIP.','2. Open START-HERE.html in your browser and copy its complete prompt into the local agent.','3. Supply your website. Add your buyer segment, offer and two target domains if known.','4. Review company-motion/COMPANY.md before continuing.','5. Open prompts.html for the next exercise. The agent stops after each step.','', 'Program commands run inside code/. Your company files live in company-motion/, beside it. Filled credentials and configuration stay in a separate private folder. The startup launcher saves a verified Python 3.10 or newer executable and reuses it. If none exists, use the official installer it names. No Homebrew is required.','', '## What you can finish','', '| Session | Guided work | Outcome |','|---|---|---|','| Part 1 | 90 minutes plus30 minutes individual help | Company brief, two reviewed account pages and a reusable skill. No paid API. |','| Part 2 | 90 minutes plus30 minutes individual help | Exact email previews,own-sender Sent test,and bounded ten-company pilot when prerequisites pass. |','| Part 3 | 90 minutes plus30 minutes individual help | Actual outcomes, next bounded cycle, pause/recovery and a saved operating record. Extra channels optional. |','', 'If an account or source is blocked, keep useful drafts and record the missing connection. Prepared, queued, sent, replied and booked are different results. A failed connection does not become successful because a token file exists.','', '## Prepare only the tools you need','', 'Part 1 needs your local coding agent, file/web access, website and supported Python. Part 2 needs owned Google OAuth, fresh complete exclusions, actual employer evidence and fresh valid work-email evidence. A finder is optional. OAuth may need your Workspace administrator. Start that setup early. See PREWORK.md and SETUP-SEQUENCE.md.','', 'Part 3 uses the same core project. Gojiberry, Loop & Tie, Netlify, Calendly, CRM and Metadata are optional according to the extension you use. API-Setup-Guide.pdf and API-CONNECTIONS.md explain exact supported operations, credits, account ownership and proof.','']
for part in d['parts']:
 lines+=['# Part '+str(part['part'])+': '+part['title'],'',part.get('subtitle',''),'', '## Finish with','']
 for x in part.get('finish',[]):lines+=['- '+x]
 lines+=['','## Before this session','']
 for x in part.get('prerequisites',[]):lines+=['- '+x]
 lines+=['','## Five chapters','']
 for ch in part['chapters']:lines+=['- '+str(ch['number'])+'. '+ch['title']+': '+ch['outcome']]
 current_chapter=None
 for s in part['slides']:
  if s['chapter']!=current_chapter:
   current_chapter=s['chapter'];ch=part['chapters'][current_chapter-1]
   lines+=['','## Chapter '+str(current_chapter)+': '+ch['title'],'',ch['outcome'],'']
  lines+=['','### '+s['title'],'', 'Reference: '+s['id']+'. '+('Optional extension.' if s.get('route')=='optional' else 'Main workshop.'),'']
  if s.get('body'):lines +=[s['body'],'']
  if s.get('type') in ['break','pause']:
   lines +=['Follow the presenter. Keep your files open.',''];continue
  if s.get('prompt'):
   lines +=[('Optional after class. ' if s.get('route')=='optional' else 'Time: '+str(s.get('minutes',s.get('timing',0)))+' minutes. ')+ 'Difficulty: '+str(s.get('difficulty',''))+'.','', 'Tools: '+ '; '.join(s.get('tools',[]))+'.','', 'Do this:','']
   for i,st in enumerate(s.get('steps',[]),1):
    lines +=[str(i)+'. '+(st if isinstance(st,str) else st.get('title','')+' '+st.get('detail',''))]
   lines+=['','Copy the complete prompt from prompts.html#'+s['id']+'. Paste it into the same local Codex or Claude Code project.','', '```text',s['prompt'],'```','', 'You should have:','']
   expected=s.get('expected',[]);expected=[expected] if isinstance(expected,str) else expected
   lines +=['- '+x for x in expected]
   lines+=['','Check before continuing:','']
   checks=s.get('check',[]);checks=[checks] if isinstance(checks,str) else checks
   lines+=['- '+x for x in checks]
   if s.get('fallback'):lines+=['','If blocked: '+s['fallback']]
  elif s.get('steps'):
   for i,st in enumerate(s['steps'],1):lines+=[str(i)+'. '+(st if isinstance(st,str) else st.get('title','')+' '+st.get('detail',''))]
  if s.get('next_action'):lines+=['','Next: '+s['next_action']+'.']
 lines+=['']
lines += ['# Finish with an honest completion record', '', 'Core local work:', '']
for x in d.get('completion', {}).get('required', []): lines += ['- ' + x]
for key, title in [('conditional_email_results', 'When your email connections pass'), ('conditional_operation_results', 'When your operating connections pass'), ('optional_extensions', 'Optional extensions')]:
 lines += ['', '## ' + title, '']
 for x in d.get('completion', {}).get(key, []): lines += ['- ' + x]
lines += ['', '## Limits to keep visible', '']
for x in d.get('completion', {}).get('known_limits', []): lines += ['- ' + x]
lines+=['# Fix the first blocked step','','Copy this when a step fails. Keep tokens and private recipient records out of the error.','','```text',"Read my project instructions and company-motion/PROGRESS.md. Identify the current workshop step and first failed check. Read the actual error and existing files. Fix that one problem without replacing completed work, changing authority or resending an uncertain provider action. Rerun the check. Show the actual result and next exercise, then stop.\nError: [PASTE THE ERROR WITHOUT KEYS OR PRIVATE RECIPIENTS]",'```','','# Words you may need','',(R/'GLOSSARY.md').read_text().split('\n',2)[-1],'','# What the evidence supports','','The real redacted examples are Metadata account pages,email andgiftinvitation records. The September 30 company dashboard: 93 demo requests, 64 booked and 34 completed does not attribute all outcomes to this engine. The historical ten-account pilot matched ten exactGmail Sent records and blocked ten repeat attempts. See sources/V5-WORKSHOP-SOURCES.md for dates and denominators.','','A prior participant reported completing Part 1 in Claude Code. Software checks and model reviews on this revision are separate from an independent beginner trial. Do not claim live provider success from these checks.','','Automatic reply sending, meeting scheduling writes, physical post, whole social campaign activation and ad launch/restart are not implemented here. Scheduling requires maintained sources, two observed manual cycles, actual app support and explicit recurring authority. Otherwise leave it prepared and paused.']
# Plain language spacing in top-level text; do not modify prompt literals or required identifiers.
(R/'course/BOOKLET.md').write_text('\n'.join(lines))
print(json.dumps({'course_sha256':__import__('hashlib').sha256((R/'course/course.json').read_bytes()).hexdigest(),'prompts':sum(bool(s.get('prompt')) for p in d['parts'] for s in p['slides']),'bytes':(R/'course/BOOKLET.md').stat().st_size}))
