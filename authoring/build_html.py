from pathlib import Path
import html, json, shutil, re

import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path)
parser.add_argument('--hosted',action='store_true')
args=parser.parse_args()
REPO=Path(__file__).resolve().parents[1]
OUT=args.output_dir or REPO
OUT.mkdir(parents=True,exist_ok=True)
WEB=REPO/'authoring/web'
for name in ['site.css','slides.css','slides.js','booklet.js','workshop-helpers.css','workshop-helpers.js']:
 shutil.copy2(WEB/name,OUT/name)
if not args.hosted:shutil.copy2(WEB/'audience.js',OUT/'audience.js')
part=json.loads((REPO/'course/course.json').read_text())['parts'][0]
E=lambda x:html.escape(str(x),quote=True)
chapter_exercises={c['number']:[s['id'] for s in part['slides'] if s['chapter']==c['number'] and s['type']=='exercise' and s['difficulty']!='Help'] for c in part['chapters']}
def rich(text,booklet=False,default_id='p1-install'):
 pattern=r'Participant-Booklet\.pdf|prompts\.html(?:#[a-z0-9-]+)?'
 out=[];last=0
 for m in re.finditer(pattern,str(text)):
  out.append(E(str(text)[last:m.start()]));label=m[0]
  if label=='Participant-Booklet.pdf':out.append('<a href="Participant-Booklet.pdf" target="_blank" rel="noopener">'+label+'</a>')
  else:
   ident=label.split('#',1)[-1] if '#' in label else default_id
   out.append(('<a href="#booklet-'+E(ident)+'" data-expand="booklet-'+E(ident)+'">' if booklet else '<a href="#'+E(ident)+'-prompt" data-open-prompt="'+E(ident)+'">')+'Open the embedded prompt'+'</a>')
  last=m.end()
 out.append(E(str(text)[last:]));return ''.join(out)
def listing(items):return '<ul>'+''.join('<li>'+rich(i)+'</li>' for i in items)+'</ul>' if items else ''
def company_fields(prefix):
 rows=[('website','Company website','https://your-company.com'),('buyer','Buyer segment','Who you sell to'),('offer','Your offer','What you want the buyer to do'),('targetOne','First target domain','first-company.com'),('targetTwo','Second target domain','second-company.com')]
 return '<details class="company-inputs"><summary>Add your company details</summary><p>Fill what you know. Your agent asks for the rest. These fields stay in your browser. Do not enter API keys.</p><div class="company-fields">'+''.join('<label for="'+prefix+'-'+key+'">'+E(label)+'<input id="'+prefix+'-'+key+'" data-company-field="'+key+'" placeholder="'+E(placeholder)+'" autocomplete="off"></label>' for key,label,placeholder in rows)+'</div></details>'
def target_fields(prefix,prompt=None):
 rows=[('targetOne','Target 1 domain','e.g. zuora.com','[TARGET_1_DOMAIN]'),('targetTwo','Target 2 domain','e.g. okta.com','[TARGET_2_DOMAIN]')]
 if prompt is not None:rows=[x for x in rows if x[3] in prompt]
 if not rows:return ''
 return '<div class="company-inputs target-inputs"><p class="target-input-title">'+('Enter your two target companies' if len(rows)==2 else 'Confirm the company for this page')+'</p><div class="company-fields">'+''.join('<label data-target-row="'+key+'" for="'+prefix+'-'+key+'">'+E(label)+'<input id="'+prefix+'-'+key+'" data-company-field="'+key+'" placeholder="'+E(placeholder)+'" autocomplete="off" spellcheck="false"></label>' for key,label,placeholder,_ in rows)+'</div><p class="target-input-hint">'+('Use company websites. These domains fill the research and page prompts below.' if len(rows)==2 else 'Saved from your target research. This domain fills the page prompt below.')+'</p><p class="target-input-error" data-input-error role="alert" hidden></p></div>'
def personalizable(s):return any(token in s['prompt'] for token in ['[YOUR_COMPANY_WEBSITE]','[TARGET_1_DOMAIN]','[TARGET_2_DOMAIN]'])
def complete(s):
 button='<button class="result-complete" data-exercise-complete="'+E(s['id'])+'" aria-pressed="false">My result matches these checks ✓</button>'
 required=chapter_exercises[s['chapter']]
 if not required or s['id']!=required[-1]:return button
 return button+'<div class="chapter-complete-panel" data-chapter-checkpoint="'+str(s['chapter'])+'" data-required-exercises="'+E(json.dumps(required))+'"><p data-chapter-status role="status">Confirm each exercise’s result checks, then finish this chapter.</p><button class="button secondary" data-finish-chapter disabled>Finish chapter '+str(s['chapter'])+'</button></div>'
def prompt_box(s):
 return ('<div class="prompt-frame"><div class="prompt-frame-label"><span>Complete prompt</span><span>Local Codex or Claude Code</span></div><textarea class="full-prompt" id="prompt-'+E(s['id'])+'" readonly '+('data-personalize ' if personalizable(s) else '')+'aria-label="Complete prompt for '+E(s['title'])+'">'+E(s['prompt'])+'</textarea></div>')
def sequence(items):return '<div class="sequence">'+''.join('<div><span>'+str(n+1)+'</span><strong>'+E(x)+'</strong></div>' for n,x in enumerate(items))+'</div>'
def registrations():
 return '<div class="registrations">'+''.join('<a href="'+E(x['url'])+'" target="_blank" rel="noopener"><img src="'+E(x['qr'])+'" alt="QR code to register for '+E(x['title'])+'"><div><h3>'+E(x['title'])+'</h3><p>'+('Write and test outbound email.' if n==0 else 'Add channels and repeat the workflow.')+'</p><span>Register on Luma ↗</span></div></a>' for n,x in enumerate(part['slides'][-1]['registrations']))+'</div>'

tree='''<div class="operating-tree" aria-label="Research, prepare, check, execute each approved channel and read provider results"><div class="tree-node research"><span>01</span><strong>Read company and buyer facts</strong><small>Your agent researches the target.</small></div><div class="tree-arrow">↓</div><div class="tree-node prepare"><span>02</span><strong>Prepare the page and messages</strong><small>Use the sources and your offer.</small></div><div class="tree-arrow">↓</div><div class="tree-node gate"><span>03</span><strong>Check the recipient and limits</strong><small>Twelve checks before a real action.</small></div><div class="tree-arrow">↓</div><div class="channels"><div class="tree-node"><strong>Email</strong><small>Gmail Sent</small></div><div class="tree-node"><strong>Gift invitation</strong><small>Loop &amp; Tie</small></div><div class="tree-node"><strong>LinkedIn invitation</strong><small>Gojiberry</small></div></div><div class="tree-arrow">↓</div><div class="tree-node readback"><strong>Read the actual provider result</strong><small>Save the result. Check replies and bookings.</small></div></div>'''

def visual(s):
 vd=s.get('visual_data',{});sid=s['id']
 if sid=='p1-v5-tree':return tree
 if sid=='p1-about':
  portrait='<a class="gil-portrait" href="'+E(vd['linkedin_url'])+'" target="_blank" rel="noopener"><img src="'+E(vd['portrait'])+'" alt="Gil Allouche’s LinkedIn profile portrait"></a>'
  bio='<div class="gil-bio"><h2>Gil Allouche</h2><p class="gil-role">Founder and CEO, Metadata.io</p><p class="gil-background">'+E(vd['background'])+'</p>'+''.join('<p class="body">'+E(line)+'</p>' for line in vd['bio_lines'])+'<a class="gil-follow" href="'+E(vd['linkedin_url'])+'" target="_blank" rel="noopener">Follow on LinkedIn ↗</a><p class="source-caption"><a href="'+E(vd['story_source'])+'" target="_blank" rel="noopener">My story</a></p></div>'
  qr='<a class="gil-follow-qr" href="'+E(vd['linkedin_url'])+'" target="_blank" rel="noopener"><img src="'+E(vd['linkedin_qr'])+'" alt="QR code for Gil Allouche’s LinkedIn profile"><span>Scan to follow</span></a>'
  logos='<div class="gil-logo-strip"><a class="source-caption" href="'+E(vd['logos_source'])+'" target="_blank" rel="noopener">Teams featured on metadata.io ↗</a><div class="gil-logos">'+''.join('<div><img src="'+E(logo['image'])+'" alt="'+E(logo['name'])+'"></div>' for logo in vd['logos'])+'</div></div>'
  return '<div class="gil-intro">'+portrait+bio+qr+'</div>'+logos
 if sid=='p1-you':return '<div class="audience-stage"><div class="heart-mosaic" id="heart-mosaic" aria-label="Workshop registrants"><p class="audience-loading" role="status">Loading the people in this workshop.</p></div><aside class="person-card" id="person-card" aria-label="Attendee professional profile" hidden></aside></div><p class="source-caption audience-caption" id="audience-caption">Hover or tap a portrait to meet the person.</p>'
 if sid=='p1-results':
  return '<div class="metrics">'+''.join('<div><strong>'+E(x['value'])+'</strong><span>'+E(x['label'])+'</span></div>' for x in vd['metrics'])+'</div><p class="source-caption">'+E(vd['scope'])+'</p><div class="clone-on-slide"><code>'+E(vd['first_instruction'])+'</code><button data-copy-text="'+E(vd['first_instruction'])+'">Copy command</button></div>'
 if sid=='p1-real-outputs':
  preview='<article class="zuora-browser"><div class="zuora-browser-bar"><span class="browser-dots" aria-hidden="true">● ● ●</span><a href="'+E(vd['page_url'])+'" target="_blank" rel="noopener">demo.metadata.io/zuora/ ↗</a><button data-scroll-toggle aria-pressed="false">Pause scroll</button></div><div class="zuora-scroll-window"><img class="zuora-scroll-image" src="'+E(vd['image'])+'" alt="Full screenshot of the live Zuora page, with audiences and ad concepts"></div><a class="zuora-live-link" href="'+E(vd['page_url'])+'" target="_blank" rel="noopener">Open the real page ↗</a></article>'
  email='<article class="zuora-email"><button class="zuora-email-open" data-open-email aria-label="Enlarge the redacted sent Zuora email"><img src="'+E(vd['email_image'])+'" alt="Redacted excerpt from Gil’s email to Zuora, sent August 16, 2026. Subject: 13 tools one gap."><span>Enlarge the sent email ↗</span></button></article>'
  gift='<article class="zuora-gift"><div class="gift-box" aria-hidden="true"><svg viewBox="0 0 100 110"><path d="M18 43h64v55H18z" fill="#ea5b2b"/><path d="M13 33h74v19H13z" fill="#f69367"/><path d="M44 33h12v65H44z" fill="#fff1d7"/><path d="M50 33C17 35 20 2 37 9c12 4 13 24 13 24Zm0 0C83 35 80 2 63 9c-12 4-13 24-13 24Z" fill="none" stroke="#fff1d7" stroke-width="7" stroke-linecap="round"/></svg></div><div><span class="gift-mock-label">'+E(vd['gift_label'])+'</span><h2>'+E(vd['gift_mock_copy']['heading'])+'</h2><p>'+E(vd['gift_mock_copy']['text'])+'</p><small>Example layout. No live redemption link.</small></div></article>'
  dialog='<dialog id="zuora-email-dialog" aria-labelledby="zuora-email-title"><div class="toc-head"><h2 id="zuora-email-title">The sent email, redacted</h2><button data-close-email>Back to the slide</button></div><p class="source-caption">Sent August 16, 2026. Personal details and tracking links removed.</p><h3>'+E(vd['email']['subject'])+'</h3><pre class="zuora-full-email">'+E(vd['email']['full_text'])+'</pre></dialog>'
  return '<div class="zuora-outputs">'+preview+'<div class="zuora-messages">'+email+gift+'</div></div><p class="source-caption">'+E(vd['caption'])+'</p>'+dialog
 if sid=='p1-page-example':return '<a class="wide-shot" href="assets/actual-zuora-page.png" target="_blank" rel="noopener"><img src="assets/actual-zuora-page.png" alt="Actual Metadata page: campaign ideas for Zuora"><span>Open the full screenshot ↗</span></a>'
 if sid=='p1-glossary':
  cards='<div class="glossary-cards">'+''.join('<article><h2>'+E(x['word'])+'</h2><p>'+E(x['meaning'])+'</p></article>' for x in vd['terms'] if x['word'] in vd['today'])+'</div>'
  table='<table class="glossary-table"><thead><tr><th>Word</th><th>Meaning here</th></tr></thead><tbody>'+''.join('<tr><td>'+E(x['word'])+'</td><td>'+E(x['meaning'])+'</td></tr>' for x in vd['terms'])+'</tbody></table>'
  return cards+'<button class="button secondary" data-open-glossary>Open the full glossary</button><dialog id="glossary-dialog" aria-labelledby="glossary-title"><div class="toc-head"><h2 id="glossary-title">Words you may need</h2><button data-close-glossary>Back to the slide</button></div>'+table+'</dialog>'
 if sid=='p1-tool-options':
  return '<div class="provider-options">'+''.join('<article><h2>'+E(x['name'])+'</h2><div class="provider-links">'+''.join('<a href="'+E(c['url'])+'" target="_blank" rel="noopener">'+E(c['name'])+' ↗</a>' for c in x['choices'])+'</div><p>'+E(x['detail'])+'</p><small>Needs: '+E(x['needs'])+'</small>'+('<small>'+E(x['note'])+'</small>' if x.get('note') else '')+'</article>' for x in vd['tool_options'])+'</div><p class="source-caption">Choose one provider per job. The starter’s sending adapters use Gmail and Loop &amp; Tie; alternatives need their own connection.</p>'
 if vd.get('teaser'):
  steps='<div class="teaser-steps">'+''.join('<div>'+E(x)+'</div>' for x in vd['steps'])+'</div>'
  if vd['teaser']=='email':art='<div class="teaser-email"><img src="'+E(vd['image'])+'" alt="Gil’s redacted sent Zuora email"><p class="source-caption">A real email, sent August 16, 2026. We’ll build yours from your company facts.</p></div>'
  else:art='<div class="teaser-orchestrator"><div class="teaser-node">Read replies and bookings</div><div class="teaser-arrow">↓</div><div class="teaser-branch"><div class="hold">Reply, booking or exclusion? Hold.</div><div>Eligible? Check the next action.</div></div><div class="teaser-arrow">↓</div><div class="teaser-channels"><div>Gift</div><div>LinkedIn</div><div>Ads</div></div><div class="teaser-arrow">↓</div><div class="teaser-node">Read the result. Save it. Repeat.</div></div>'
  return '<div class="teaser-layout">'+steps+art+'</div><p class="teaser-outcome">'+E(vd['outcome'])+'</p><div class="teaser-footer"><a href="'+E(vd['url'])+'" target="_blank" rel="noopener">Register on Luma ↗</a><span>The next registration slide has both QR codes.</span></div>'
 if sid=='p1-before-part2':return registrations()
 if s['type']=='break':return '<div class="break-art" aria-hidden="true"><svg viewBox="0 0 300 240"><path d="M70 90h136v72a48 48 0 0 1-48 48h-40a48 48 0 0 1-48-48Z" fill="#f4a773" stroke="#183e33" stroke-width="4"/><path d="M206 104h24a26 26 0 0 1 0 52h-24" fill="none" stroke="#183e33" stroke-width="5"/><path d="M58 219h172M102 67c-20-19 20-29 0-47M142 67c-20-19 20-29 0-47M182 67c-20-19 20-29 0-47" fill="none" stroke="#397565" stroke-width="4" stroke-linecap="round"/></svg><strong>5 minutes</strong></div>'
 if vd.get('stages'):return sequence(vd['stages'])
 if vd.get('checks'):return '<div class="review-list">'+''.join('<div><span>✓</span>'+E(x)+'</div>' for x in vd['checks'])+'</div>'
 if vd.get('cards'):return '<div class="target-cards">'+''.join('<article><span>'+E(x['label'])+'</span>'+listing(x['fields'])+'</article>' for x in vd['cards'])+'</div>'
 if vd.get('before'):return '<div class="target-cards"><article><span>First target</span>'+listing(vd['before'])+'</article><article><span>Second target</span>'+listing(vd['after'])+'</article></div>'
 if vd.get('artifacts'):return '<div class="artifact-list">'+''.join('<div><span>▤</span><strong>'+E(x)+'</strong></div>' for x in vd['artifacts'])+'</div>'
 return ''

slides=[]
def add(id,title,ch,content,kind=''):
 slides.append({'id':id,'title':title,'chapter':ch,'html':content,'kind':kind})
current=1
for s in part['slides']:
 ch=s['chapter']
 if ch!=current:
  current=ch;c=part['chapters'][ch-1]
  tasks={2:['Open your cloned project.','Paste the startup prompt.','Review the company brief.'],3:['Read both target websites.','Save facts with their sources.','Save your two-company list.'],4:['Create your first HTML page.','Check every claim against its source.','Open it on desktop and phone.'],5:['Save the page instructions as a skill.','Use it for the second company.','Check both pages and saved files.']}[ch]
  add(c['id'],c['title'],ch,'<p class="eyebrow">Section '+str(ch)+' of 5</p><h1>'+E(c['title'])+'</h1>'+sequence(tasks)+'<p class="chapter-outcome">'+E(c['outcome'])+'</p><p class="chapter-time">'+str(c['guided_minutes'])+' minutes'+(' + 30 minutes for individual help' if c['help_minutes'] else '')+'</p>','chapter-slide')
 if s['type']=='cover':
  content='<div class="cover-copy"><p class="eyebrow">Part 1</p><h1>Build your own<br><span>Agentic GTM.</span></h1><p>Build two pages for your<br>target companies.</p><p class="byline">Gil Allouche<br>CEO, Metadata.io</p></div>'
  add(s['id'],s['title'],ch,content,'cover-slide');continue
 heading='<p class="eyebrow">'+('Exercise' if s['prompt'] else 'Section '+str(ch)+' of 5')+'</p><h1>'+E(s['title'])+'</h1>'
 if s['prompt']:
  steps='<ol class="instruction-list">'+''.join('<li><strong>'+rich(x['title'],default_id=s['id'])+'</strong>'+('<p>'+rich(x['detail'],default_id=s['id'])+'</p>' if x.get('detail') else '')+'</li>' for x in s['steps'])+'</ol>'
  expected='<div class="expected"><strong>You should have</strong>'+listing(s['expected'])+'</div><details class="check"><summary>Open the '+str(len(s['check']))+' checks before moving on</summary>'+listing(s['check'])+'</details>'+complete(s)
  next_button='<div class="exercise-next"><button class="button" data-open-prompt="'+E(s['id'])+'">View and copy the complete prompt</button><span>Copy it here. The next slide also shows it.</span></div>'
  content=heading+'<p class="exercise-meta">'+E(str(s['timing']))+' minutes · '+E(s['difficulty'])+' · '+E(' '.join(s['tools']))+'</p><div class="exercise-grid"><div>'+steps+target_fields('exercise-'+s['id'],s['prompt'] if s['id']!='p1-install' else '')+next_button+'</div><div class="exercise-result">'+visual(s)+expected+'</div></div>'
  add(s['id'],s['title'],ch,content,'exercise-slide')
  repair='<label for="repair-'+E(s['id'])+'">Copy this repair prompt into the same local agent.</label><textarea class="repair-prompt" id="repair-'+E(s['id'])+'" readonly>'+E(s.get('repair_prompt',''))+'</textarea><button class="button secondary" data-copy="repair-'+E(s['id'])+'">Copy repair prompt</button>' if s.get('repair_prompt') else ''
  content='<p class="eyebrow">Copy and paste into your local agent</p><h1>'+E(s['title'])+'</h1><div class="prompt-actions"><button class="button" data-copy="prompt-'+E(s['id'])+'">Copy the full prompt</button><span>Paste into local Codex or Claude Code.</span></div>'+(company_fields('slide-'+s['id']) if '[YOUR_COMPANY_WEBSITE]' in s['prompt'] else target_fields('slide-'+s['id'],s['prompt']))+prompt_box(s)+'<p class="next-action">'+E(s.get('next_action',''))+'</p><details class="fallback"><summary>If you get stuck</summary><p>'+rich(s['fallback'])+'</p>'+repair+'</details>'
  add(s['id']+'-prompt','Prompt: '+s['title'],ch,content,'prompt-slide')
 else:
  content=heading
  if s['id']=='p1-results':content+=visual(s)
  elif s['id']=='p1-v5-tree':content+='<div class="tree-grid">'+visual(s)+'<div><p class="body">'+E(s['body'])+'</p><p class="today">Today: build the page and save the instructions that made it.</p><details><summary>See the twelve checks</summary>'+listing(s['visual_data']['inline_checks'])+'</details></div></div>'
  elif s['id']=='p1-about':content+=visual(s)
  elif s['id']=='p1-you':content+=visual(s)
  elif s['id']=='p1-real-outputs':content+=visual(s)
  else:content+='<p class="body">'+rich(s['body'])+'</p>'+visual(s)
  if s.get('expected'):content+='<div class="compact-outcomes">'+listing(s['expected'])+'</div>'
  add(s['id'],s['title'],ch,content,'show-slide '+('tree-slide' if s['id']=='p1-v5-tree' else ''))
assert len(slides)==len(part['slides'])+len(part['chapters'])-1+sum(bool(s.get('prompt')) for s in part['slides']), len(slides)
slide_total=len(slides)
nav=''.join('<button data-index="'+str(n)+'"><span>'+str(n+1).zfill(2)+'</span>'+E(s['title'])+'</button>' for n,s in enumerate(slides))
sections=''.join('<section class="slide '+s['kind']+'" id="'+s['id']+'" data-chapter="'+str(s['chapter'])+'" aria-label="Slide '+str(n+1)+' of '+str(slide_total)+': '+E(s['title'])+'"'+(' hidden' if n else '')+'>'+s['html']+'</section>' for n,s in enumerate(slides))
OUT.joinpath('Part-1-Presentation.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Agentic GTM | Part 1 live slides</title><link rel="stylesheet" href="site.css"><link rel="stylesheet" href="slides.css"><link rel="stylesheet" href="workshop-helpers.css"><link rel="icon" href="assets/metadata-icon.jpeg"></head><body class="deck"><header class="deck-header"><a class="brand" href="/gtm-part1/">metadata<span>.</span></a><div class="deck-tools"><a href="Participant-Booklet.html" target="_blank" rel="noopener">Participant booklet ↗</a><a href="Part-1-Presentation.pdf" target="_blank" rel="noopener">PDF ↗</a><button id="contents">Contents</button><button id="fullscreen" aria-label="Enter fullscreen">Fullscreen</button></div></header><main id="slides">'''+sections+'''</main><footer class="deck-footer"><div><span id="chapter-label">Section 1 of 5</span><span class="keys">← → to move</span></div><div class="slide-controls"><button id="prev" aria-label="Previous slide">←</button><span id="slide-count" aria-live="polite">1 / '''+str(slide_total)+'''</span><button id="next" aria-label="Next slide">→</button></div></footer><div class="progress"><div id="progress-bar"></div></div><p id="copy-message" role="status" aria-live="polite"></p><dialog id="toc"><div class="toc-head"><h2>Workshop contents</h2><button id="close-contents">Close</button></div><nav aria-label="All slides">'''+nav+'''</nav></dialog><dialog id="prompt-dialog" aria-labelledby="prompt-title"><div class="toc-head"><h2 id="prompt-title">Complete prompt</h2><button data-close-dialog>Back to the slide</button></div><p>Paste this into your local Codex or Claude Code project.</p>'''+company_fields('modal')+target_fields('modal-targets')+'''<textarea id="modal-prompt" class="full-prompt" readonly aria-label="Complete exercise prompt"></textarea><button class="button" data-copy="modal-prompt">Copy the full prompt</button></dialog><p class="workshop-success" id="workshop-success" role="status" aria-live="polite"></p><script src="workshop-helpers.js"></script><script src="slides.js"></script><script src="audience.js"></script></body></html>''')

def inline(s,reference=None):
 parts=re.split(r'(\[[^\]]+\]\([^)]+\))',str(s));out=[]
 for piece in parts:
  m=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',piece)
  if m:
   url=m[2];local=url.startswith('prompts.html#')
   ident=url.split('#')[-1]
   out.append(('<a href="#booklet-'+E(ident)+'" data-expand="booklet-'+E(ident)+'">' if local else '<a href="'+E(url)+'" target="_blank" rel="noopener">')+E(m[1])+'</a>')
  else:
   text=rich(piece,booklet=True,default_id=reference or 'p1-install')
   text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
   text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
   out.append(text)
 return ''.join(out)
def markdown(text):
 out=[];code=[];in_code=False;ul=False;ol=False;reference=None;table=False
 def close():
  nonlocal ul,ol,table
  if ul:out.append('</ul>');ul=False
  if ol:out.append('</ol>');ol=False
  if table:out.append('</table></div>');table=False
 for line in text.splitlines():
  if line.startswith('Reference: p1-'):reference=line.split(': ',1)[1]
  if line.startswith('```'):
   if in_code:
    value=E('\n'.join(code))
    if reference:
     lesson=next((s for s in part['slides'] if s['id']==reference),{})
     target_inputs=target_fields('booklet-'+reference,lesson.get('prompt','')) if reference!='p1-install' else ''
     out.append(target_inputs+'<details class="booklet-prompt" id="booklet-'+E(reference)+'"><summary>Open the complete prompt</summary><div class="prompt-actions"><button class="button secondary" data-copy-code>Copy the full prompt</button><span>Paste into local Codex or Claude Code.</span></div>'+ (company_fields('booklet-'+reference) if reference=='p1-install' else '')+'<pre '+('data-personalize ' if lesson.get('prompt') and personalizable(lesson) else '')+'>'+value+'</pre></details>')
     if lesson.get('prompt'):out.append(complete(lesson))
     if lesson.get('repair_prompt'):out.append('<details class="booklet-prompt repair" id="booklet-'+E(reference)+'-repair"><summary>If you get stuck: copy the repair prompt</summary><div class="prompt-actions"><button class="button secondary" data-copy-code>Copy repair prompt</button></div><pre>'+E(lesson['repair_prompt'])+'</pre></details>')
    else:out.append('<div class="booklet-prompt command"><button class="button secondary" data-copy-code>Copy command</button><pre>'+value+'</pre></div>')
    code=[];in_code=False
   else:close();in_code=True
   continue
  if in_code:code.append(line);continue
  if not line.strip():close();continue
  m=re.match(r'^(#{1,6}) (.*)',line)
  if m:close();out.append('<h'+str(len(m[1]))+'>'+inline(m[2],reference)+'</h'+str(len(m[1]))+'>');continue
  if line.startswith('|'):
   cells=[x.strip() for x in line.strip().strip('|').split('|')]
   if all(re.fullmatch(r'[:\- ]+',x) for x in cells):continue
   if not table:close();out.append('<div class="booklet-table"><table>');table=True
   out.append('<tr>'+''.join('<td>'+inline(x,reference)+'</td>' for x in cells)+'</tr>');continue
  if line.startswith('- '):
   if ol:close()
   if not ul:out.append('<ul>');ul=True
   out.append('<li>'+inline(line[2:],reference)+'</li>');continue
  m=re.match(r'^\d+\. (.*)',line)
  if m:
   if ul:close()
   if not ol:out.append('<ol>');ol=True
   out.append('<li>'+inline(m[1],reference)+'</li>');continue
  close();out.append('<p>'+inline(line,reference)+'</p>')
 close();return '\n'.join(out)
body=markdown((REPO/'course/BOOKLET.md').read_text())+registrations()
OUT.joinpath('Participant-Booklet.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Your Agentic GTM build booklet</title><link rel="stylesheet" href="site.css"><link rel="stylesheet" href="workshop-helpers.css"></head><body><header class="nav"><a class="brand" href="/gtm-part1/">metadata<span>.</span></a><nav class="nav-links"><a href="#booklet-p1-install" data-expand="booklet-p1-install">First prompt</a><a href="Participant-Booklet.pdf" target="_blank" rel="noopener">PDF booklet ↗</a><a href="Part-1-Presentation.html" target="_blank" rel="noopener">Slides ↗</a></nav></header><main class="booklet-main"><p class="eyebrow">Part 1 · Participant booklet</p><p class="booklet-stay">Keep Zoom and this booklet open. Expand each prompt here, copy it, and paste it into your local agent. Close any resource tab when finished to return here.</p>'''+body+'''<p id="booklet-status" role="status" aria-live="polite"></p></main><p class="workshop-success" id="workshop-success" role="status" aria-live="polite"></p><script src="workshop-helpers.js"></script><script src="booklet.js"></script></body></html>''')
if OUT.resolve()!=REPO.resolve() and (REPO/'sources/V5-WORKSHOP-SOURCES.md').exists():
 (OUT/'sources').mkdir(exist_ok=True);shutil.copy2(REPO/'sources/V5-WORKSHOP-SOURCES.md',OUT/'sources/V5-WORKSHOP-SOURCES.md')
for filename in ['PREWORK','BUILD-MY-GTM']:
 text=(REPO/(filename+'.md')).read_text()
 body=markdown(text)+'<p class=\"return-actions\"><button class=\"button secondary\" onclick=\"window.close();location.href=\'Participant-Booklet.html\'\">Close this tab and return to the booklet</button></p>'
 OUT.joinpath(filename+'.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(filename.replace('-',' ').title())+' | Metadata workshop</title><link rel="stylesheet" href="site.css"><link rel="stylesheet" href="workshop-helpers.css"></head><body><header class="nav"><a class="brand" href="/gtm-part1/">metadata<span>.</span></a><nav class="nav-links"><a href="START-HERE.html">First prompt ↗</a><a href="Participant-Booklet.html">Participant booklet ↗</a></nav></header><main class="booklet-main">'+body+'</main></body></html>')
start=OUT/'START-HERE.html'
start.write_text(start.read_text().replace('href="PREWORK.md"','href="PREWORK.html"').replace('href="BUILD-MY-GTM.md"','href="BUILD-MY-GTM.html"'))
helper=OUT/'prompts.html'
text=helper.read_text()
text=re.sub(r'<details class="repair">(?:(?!</details>).)*?id="r-([^\"]+)"',lambda m:m[0].replace('<details class="repair">','<details class="repair" id="'+m[1]+'-repair">',1),text,flags=re.S)
if 'function revealWorkshopRepair' not in text:
 text=text.replace('</body>','<script>function revealWorkshopRepair(){const x=document.getElementById(location.hash.slice(1));if(x?.matches("details.repair"))x.open=true;}window.addEventListener("hashchange",revealWorkshopRepair);revealWorkshopRepair();</script></body>')
helper.write_text(text)
if not args.hosted:
 for name in ['Part-1-Presentation.html','Participant-Booklet.html']:
  path=OUT/name;path.write_text(path.read_text().replace('href="/gtm-part1/"','href="START-HERE.html"'))
print(f'Built {slide_total} HTML slides with the original exercise order.')
