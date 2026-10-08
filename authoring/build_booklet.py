from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'course/course.json').read_text())
assert len(d['parts'])==1 and d['parts'][0]['part']==1
p=d['parts'][0]
lines=['# Build your own Agentic GTM: Part 1','','Use your company website and two target-company domains. No API keys are needed.','','## Start here','','```bash','git clone https://github.com/f-o-x11/agentic-gtm-workshop.git','```','','Open this folder in local Codex or Claude Code. Keep this booklet open beside Zoom. Expand the first complete prompt here. Add your website, buyer segment, offer and two target domains, then copy it into your local agent. Review the company brief before continuing.','', 'Program commands run from code/. Your company files live in company-motion/. Keys belong outside this repository.','', '## Finish with','']
glossary=(R/'GLOSSARY.md').read_text().split('\n',2)[-1]
position=lines.index('## Finish with')
lines[position:position]=['## Words you may need','',glossary,'']
lines += ['- '+x for x in p.get('finish',[])]
for ch in p['chapters']:
    lines += ['', '## Section '+str(ch['number'])+': '+ch['title'],'',ch['outcome'],'']
    for s in [s for s in p['slides'] if s['chapter']==ch['number']]:
        if not s.get('prompt'):continue
        lines += ['', '### '+s['title'],'', 'Reference: '+s['id'],'','Time: '+str(s.get('timing',0))+' minutes. Difficulty: '+s.get('difficulty','')+'.','', 'Tools: '+'; '.join(x.rstrip('.') for x in s.get('tools',[]))+'.','']
        for i,st in enumerate(s.get('steps',[]),1):
            lines += [str(i)+'. '+(st if isinstance(st,str) else st.get('title','')+' '+st.get('detail',''))]
        lines += ['', 'Expand the complete prompt below. Copy it into the same local agent project.','', '```text',s['prompt'],'```','','You should have:','']
        value=s.get('expected',[])
        lines += ['- '+x for x in (value if isinstance(value,list) else [value])]
        lines += ['', 'Check before continuing:','']
        value=s.get('check',[])
        lines += ['- '+x for x in (value if isinstance(value,list) else [value])]
        if s.get('fallback'):lines += ['', 'If blocked: '+s['fallback']]
        if s.get('next_action'):lines += ['', 'Next: '+s['next_action']+'.']
tools=next(x['visual_data']['tool_options'] for x in p['slides'] if x['id']=='p1-tool-options')
lines += ['', '## Tools for the next sessions','', 'Use the tools you already have. Part 1 needs none of these connections.','']
for t in tools:
 lines += ['### '+t['name'],'', ', '.join('['+x['name']+']('+x['url']+')' for x in t['choices']), '',t['detail'],'','Needs: '+t['needs'],'']
lines += ['The supplied sending adapters use Gmail and Loop & Tie. Other providers need their own connection. Company permissions and account policies still apply.','']
lines += ['', '# Keep your project','','Save your brief, target list, reviewed pages, skill and PROGRESS.md. Your files are the starting point for the next workshop.','','Part 2: choose ten accounts, check buyer data, preview your emails, then send and verify one approved self-test.','','Part 3: check replies and bookings, add gift and LinkedIn actions, connect advertising, then repeat within your limits.','','[Register for Part 2](https://luma.com/jd8tm0ij). [Register for Part 3](https://luma.com/wucyo6fw).']
(R/'course/BOOKLET.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(lines).splitlines()).rstrip()+'\n')
print(json.dumps({'parts':1,'exercises':sum(bool(s.get('prompt')) for s in p['slides'])}))
