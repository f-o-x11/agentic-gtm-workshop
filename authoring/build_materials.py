from pathlib import Path
import json,re,html,shutil,math
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,Color
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted,Table,TableStyle,KeepTogether,Image,Flowable
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader,PdfWriter

R=Path(__file__).resolve().parents[1]
ROOT=R
OUT=R
OUT.mkdir(parents=True,exist_ok=True)
for weight,label in [(400,'Rubik'),(600,'RubikMedium'),(700,'RubikBold')]:
 pdfmetrics.registerFont(TTFont(label,str(R/f'assets/Rubik-{weight}.ttf')))
pdfmetrics.registerFontFamily('Rubik',normal='Rubik',bold='RubikBold',italic='Rubik',boldItalic='RubikBold')
BLACK=HexColor('#111827');ORANGE=HexColor('#ea580c');GREEN=HexColor('#1a7a69');CREAM=HexColor('#f8f7f5');GRAY=HexColor('#4b5563');LINE=HexColor('#d1d5db')
W,H=1280,720
CHECKS=[]
CURRENT_SECTION=1
PART_ONE_SECTIONS=['Examples','Your company','Target companies','First page','Saved skill']

def plain(s):
 if isinstance(s,list):s='; '.join(plain(x) for x in s)
 return str('' if s is None else s).replace('\u2014',', ').replace('\u2013','-').replace('\u2011','-').replace('\u00a0',' ')

def paragraph(c,s,x,top,width,size=26,color=BLACK,font='Rubik',leading=None):
 s=escape(plain(s)).replace('\n','<br/>')
 p=Paragraph(s,ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.3,textColor=color,spaceAfter=0))
 _,hh=p.wrap(width,H)
 p.drawOn(c,x,top-hh)
 CHECKS.append({'text':plain(s)[:65],'top':top,'bottom':top-hh,'width':width,'size':size})
 return hh

def pic(c,path,x,y,w,h):
 p=Path(path)
 if not p.exists():return False
 im=ImageReader(str(p));iw,ih=im.getSize();sc=min(w/iw,h/ih)
 c.drawImage(im,x+(w-iw*sc)/2,y+(h-ih*sc)/2,iw*sc,ih*sc,mask='auto')
 return True

def line(c,x,y,w):
 c.setStrokeColor(LINE);c.setLineWidth(1);c.line(x,y,x+w,y)

def header(c,title,num,part,source=''):
 c.setFillColor(CREAM);c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(ORANGE);c.rect(0,H-8,W,8,fill=1,stroke=0)
 pic(c,R/'assets/metadata-icon.jpeg',54,H-62,30,30)
 paragraph(c,'Metadata',95,H-35,200,18,font='RubikBold')
 paragraph(c,'Part '+str(part),1100,H-37,120,16,color=GRAY)
 if part==1:
  for i,label in enumerate(PART_ONE_SECTIONS,1):
   x=56+(i-1)*239
   paragraph(c,str(i)+'. '+label,x,650,225,12,color=ORANGE if i==CURRENT_SECTION else GRAY,font='RubikBold' if i==CURRENT_SECTION else 'Rubik')
 paragraph(c,title,56,620,1168,40 if len(title)<65 else 35,font='RubikBold')
 line(c,56,58,1168)
 paragraph(c,source,56,42,1060,10,color=GRAY)
 paragraph(c,str(num),1165,42,60,13,color=GRAY)

def node(c,text,x,y,w=245,h=67,orange=False):
 c.setFillColor(ORANGE if orange else HexColor('#ffffff'));c.setStrokeColor(ORANGE if orange else LINE)
 c.rect(x,y,w,h,fill=1,stroke=1)
 paragraph(c,text,x+18,y+h-15,w-36,20,color=HexColor('#ffffff') if orange else BLACK,font='RubikMedium')

def arrow(c,x1,y1,x2,y2):
 c.setStrokeColor(GRAY);c.setLineWidth(2);c.line(x1,y1,x2,y2)
 ang=math.atan2(y2-y1,x2-x1);l=8
 c.line(x2,y2,x2-l*math.cos(ang-.4),y2-l*math.sin(ang-.4));c.line(x2,y2,x2-l*math.cos(ang+.4),y2-l*math.sin(ang+.4))

def tree(c,s):
 node(c,'Codex researches, selects and writes',90,429,445,76,True)
 node(c,'Exact prepared action in your database',745,429,445,76)
 arrow(c,535,467,745,467)
 node(c,'Local program refreshes history, exclusions and bookings. Checks the exact recipient and action.',90,285,1100,90)
 arrow(c,970,429,970,375)
 for x,label in [(90,'Email. Read Gmail Sent.'),(490,'Gift. Read its provider stage.'),(890,'LinkedIn. Read event or queue.')]:
  node(c,label,x,150,300,74,True);arrow(c,x+150,285,x+150,224)
 paragraph(c,'Paused, excluded or uncertain: hold the action and read the existing provider record.',90,111,1100,21,color=GRAY)

def four(c,s):
 labels=['1. Build one skill','2. Put skills in order','3. Choose target accounts','4. Test ten accounts']
 for i,label in enumerate(labels):
  node(c,label,65+i*300,340,265,110,i==0)
  if i<3:arrow(c,330+i*300,395,365+i*300,395)
 outs=['Company context and a page','Rules for the next action','Evidence for each buyer','Sent records and a repeat check']
 for i,t in enumerate(outs):paragraph(c,t,65+i*300,295,265,23)

def files(c,s):
 groups=s['visual_data'].get('groups',[])
 for i,g in enumerate(groups):
  title=g['name'];items=g['files'];x=56+(i%3)*403;top=520-(i//3)*180
  paragraph(c,title,x,top,377,21,font='RubikBold',color=ORANGE)
  y=top-59
  for item in items:
   hh=paragraph(c,item,x,y,365,16);y-=hh+3
 paragraph(c,'Actual v5 source: 20 files. Accounts, messages and provider results are rows in one database.',56,87,1150,16)

def metrics(c,s):
 labels=[('93','Demo requests'),('64','Booked demos'),('34','Completed demos')]
 for i,(v,t) in enumerate(labels):
  x=66+i*403
  paragraph(c,v,x,475,350,105,color=ORANGE,font='RubikBold')
  paragraph(c,t,x,335,350,27,font='RubikMedium')
 paragraph(c,'Metadata company-wide dashboard, September 30. Since August 17. These counts do not establish engine attribution.',66,230,1100,22,color=GRAY)
 paragraph(c,'Engine pilot, September 16: 10 emails matched Gmail Sent. 10 repeat attempts blocked.',66,168,1100,23,font='RubikMedium')
 paragraph(c,'Gil Allouche, CEO of Metadata. You will build this workflow for your company.',66,117,1100,23)

def part_one_example(c,s):
 vd=s.get('visual_data',{});ident=s['id']
 if ident=='p1-results':
  for i,(value,label) in enumerate([('93','Demo requests'),('64','Booked demos'),('34','Completed demos')]):
   x=66+i*403
   paragraph(c,value,x,518,350,82,color=ORANGE,font='RubikBold')
   paragraph(c,label,x,408,350,27,font='RubikMedium')
  paragraph(c,'Company totals since August 17, measured September 30, 2026. This workflow\'s share is unverified.',66,345,1125,18,color=GRAY)
  paragraph(c,'Engine test: 10 emails confirmed in Gmail Sent. 10 repeat sends blocked.',66,291,1125,24,font='RubikMedium')
  paragraph(c,'First instruction. Run this in Codex, Claude Code or your terminal.',66,230,1125,22,font='RubikBold',color=ORANGE)
  c.setFillColor(HexColor('#ffffff'));c.setStrokeColor(LINE);c.roundRect(56,139,1168,62,8,fill=1,stroke=1)
  paragraph(c,'git clone https://github.com/f-o-x11/agentic-gtm-workshop.git',76,183,1128,25,font='RubikMedium')
  paragraph(c,'Open the folder in local Codex or Claude Code. Keep the booklet and prompts.html open.',66,112,1125,21)
  c.linkURL('https://github.com/f-o-x11/agentic-gtm-workshop',(56,139,1224,201),relative=0)
  return True
 if ident=='p1-about':
  paragraph(c,'Gil Allouche',56,504,530,58,font='RubikBold')
  paragraph(c,'CEO, Metadata.io',56,418,530,30,color=ORANGE,font='RubikMedium')
  paragraph(c,'I built the workflow our marketing team uses.',56,346,530,30)
  paragraph(c,'I use Codex to run it.',56,244,530,30)
  paragraph(c,'Today, build two pages for your target companies.',56,193,530,28,font='RubikMedium')
  pic(c,R/'assets/actual-zuora-page.png',645,185,565,333)
  paragraph(c,'Metadata\'s actual page for Zuora',645,149,565,18,color=GRAY)
  return True
 if ident=='p1-v5-tree':
  node(c,'Read company and buyer facts',56,431,350,76,True)
  node(c,'Write the page, email or offer',462,431,350,76)
  node(c,'Check recipient and limits',868,431,350,76)
  arrow(c,406,468,462,468);arrow(c,812,468,868,468)
  for x,label,result in [(56,'Email','Read Gmail Sent'),(462,'Gift invitation','Read Loop & Tie status'),(868,'LinkedIn invitation','Read Gojiberry status')]:
   node(c,label,x,283,350,72,True)
   arrow(c,1043,431,x+175,355)
   node(c,result,x,163,350,70)
   arrow(c,x+175,283,x+175,233)
  paragraph(c,'Today: create the account page. Save the instructions. Use them for a second company.',56,114,1168,21,font='RubikMedium')
  return True
 if ident=='p1-real-outputs':
  pic(c,R/'assets/actual-zuora-page.png',56,150,695,383)
  paragraph(c,'Zuora: an account-specific page',56,126,695,20,font='RubikMedium')
  paragraph(c,'Forum One / Email',804,514,410,25,color=ORANGE,font='RubikBold')
  paragraph(c,'"May I send you campaign ideas for reaching prospective Forum One clients?"',804,462,410,24)
  paragraph(c,'Gmail Sent. September 30, 2026.',804,338,410,16,color=GRAY)
  line(c,804,304,410)
  paragraph(c,'Datarails / Gift invitation',804,279,410,25,color=ORANGE,font='RubikBold')
  paragraph(c,'$150 offer. Loop & Tie reported sent.',804,221,410,23)
  paragraph(c,'September 30, 2026. Redemption and meeting attendance are not shown.',804,155,410,16,color=GRAY)
  return True
 if ident=='p1-finish':
  for i,(label,artifact) in enumerate([('Set up your company','Company brief'),('Choose two companies','Two target briefs'),('Build and check page one','Reviewed HTML page'),('Save the skill. Build page two.','Saved instructions + second page')]):
   x=56+(i%2)*608;top=511-(i//2)*191
   node(c,str(i+2)+'. '+label,x,top-86,558,86,i==0)
   paragraph(c,artifact,x+16,top-112,526,25)
  paragraph(c,'Use your own company and targets. No API keys needed for Part 1.',56,132,1168,21,color=GRAY)
  paragraph(c,'Open Participant-Booklet.pdf for instructions. Open prompts.html to copy each full prompt.',56,91,1168,17,color=ORANGE,font='RubikMedium')
  c.linkURL('Participant-Booklet.pdf',(56,63,680,95),relative=1)
  c.linkURL('prompts.html',(683,63,1224,95),relative=1)
  return True
 if ident=='p1-page-example':
  pic(c,R/'assets/actual-zuora-page.png',56,134,858,398)
  for i,label in enumerate(['Name the buyer','Show useful ideas','Give a clear next step']):
   top=487-i*112
   paragraph(c,str(i+1),949,top,45,28,color=ORANGE,font='RubikBold')
   paragraph(c,label,1000,top,225,25,font='RubikMedium')
  return True
 return False

def ads(c,s):
 vd=s.get('visual_data',{});rows=vd.get('metrics',[]);primary=vd.get('primary',[])
 qualified=next((r for r in primary+rows if 'mql' in r.get('label','').lower()),None)
 if not qualified:
  values=re.search(r'MQLs:\s*(\d+)\s*(?:to|→)\s*(\d+)',vd.get('qualification',''))
  if not values:raise ValueError('Advertising slide needs sourced MQL before/after values')
  qualified={'label':'Recorded MQLs','before':values[1],'after':values[2]}
 paragraph(c,'Prior period',620,516,270,18,color=GRAY)
 paragraph(c,'Latest period',922,516,270,18,color=GRAY)
 paragraph(c,qualified['label'],56,469,520,30,font='RubikBold')
 paragraph(c,qualified['before'],620,480,270,62,font='RubikBold',color=ORANGE)
 paragraph(c,qualified['after'],922,480,270,62,font='RubikBold',color=ORANGE)
 line(c,56,392,1168)
 pipeline=next((r for r in primary if 'pipeline' in r.get('label','').lower()),None)
 pipeline_text=pipeline['label']+': '+pipeline['value'].lower()+'.' if pipeline else vd.get('pipeline','Pipeline impact unverified.')
 paragraph(c,pipeline_text,56,376,1168,23,font='RubikMedium',color=GRAY)
 secondary=[r for r in rows if r is not qualified and 'mql' not in r.get('label','').lower()]
 for i,row in enumerate(secondary[:4]):
  top=334-i*45
  paragraph(c,row['label'],56,top,520,23,font='RubikMedium')
  paragraph(c,row['before'],620,top,270,23)
  paragraph(c,row['after'],922,top,270,23)
 paragraph(c,vd.get('decision',''),56,155,1168,22,color=BLACK,font='RubikMedium')
 paragraph(c,vd.get('period',vd.get('scope','')),56,85,1168,14,color=GRAY)

def comparison(c,s):
 vd=s.get('visual_data',{}); before=vd.get('before',[]);after=vd.get('after',[])
 if not before or not after:
  before=['A marketer chooses accounts.','Research, writing and checks happen by hand.','Someone confirms what actually happened.']
  after=['Codex prepares a bounded queue.','The local program checks and acts.','Provider records confirm each result.']
 if isinstance(before,str):before=[before]
 if isinstance(after,str):after=[after]
 for x,label,arr,col in [(56,'Before',before,GRAY),(682,'With your workflow',after,ORANGE)]:
  paragraph(c,label,x,505,535,31,font='RubikBold',color=col);line(c,x,455,535)
  y=420
  for t in arr:
   hh=paragraph(c,t,x,y,530,26);y-=hh+23

def generic(c,s):
 body=s.get('body','');vd=s.get('visual_data',{});key=(s['id']+' '+s.get('visual_type','')+' '+s['title']).lower()
 if s['id']=='p1-v5-tree':tree(c,s);return
 if s['id']=='p1-build-journey':
  four(c,s)
  paragraph(c,'August 7 foundation. Claude Code v1/v2. Codex v3. Kimi handoff. Codex v4. Local v5 on October 4 to 5.',56,110,1160,18,color=GRAY);return
 if 'file_map' in key or '20-file' in key:files(c,s);return
 if ('results' in key or 'proof' in key) and s['part']==1 and s.get('type')!='exercise':metrics(c,s);return
 if s['id']=='p3-ad-results':
  ads(c,s);return
 if s['id']=='p3-gift-before-after':
  paragraph(c,'Before',56,516,520,28,color=GRAY,font='RubikBold')
  paragraph(c,'Choose the recipient, collection and terms. Check the result by hand.',56,459,520,25)
  paragraph(c,'With your workflow',56,348,520,28,color=ORANGE,font='RubikBold')
  paragraph(c,'Prepare the exact offer. Check funding and meeting terms. Submit once. Read its provider stage.',56,290,520,25)
  pic(c,ROOT/'assets/gift-message-preview-redacted.png',635,157,580,390)
  paragraph(c,vd.get('caption',''),56,107,1160,17,color=GRAY);return
 if 'before_after' in key or 'comparison' in key:comparison(c,s);return
 if s['id']=='p2-counts':
  for x,label,value,explain in [(56,'Your own test email','1','Excluded from the prospect count.'),(682,'Ten prospect companies','10','Each exact Gmail Sent match counts.')]:
   paragraph(c,label,x,510,535,29,font='RubikBold')
   paragraph(c,value,x,425,535,110,color=ORANGE,font='RubikBold')
   paragraph(c,explain,x,235,535,25)
  paragraph(c,'Total email limit: 11. The limit stays in place across days.',56,123,1160,24,color=GRAY)
  return
 if s['id']=='p2-real-email':
  paragraph(c,'Forum One / September 30, 2026 / Sent',56,520,1150,19,color=ORANGE,font='RubikMedium')
  paragraph(c,vd['excerpt'],56,455,1150,30)
  paragraph(c,vd['caption'],56,120,1140,19,color=GRAY);return
 if vd.get('events'):
  for i,row in enumerate(vd['events']):
   y=480-i*95;node(c,row['event'],56,y-65,380,65,i==0);arrow(c,436,y-31,524,y-31)
   paragraph(c,row['next'],545,y-10,660,26)
  return
 if vd.get('rows') and len(vd['rows'])>5:
  for i,row in enumerate(vd['rows']):
   x=56+(i%2)*608;top=520-(i//2)*110
   paragraph(c,row.get('job',row.get('label','')),x,top,545,20,font='RubikBold',color=ORANGE)
   paragraph(c,row.get('stage',''),x,top-34,545,19)
  return
 if vd.get('rows'):
  rows=vd['rows'];y=514
  for row in rows:
   left=row.get('job',row.get('label',''));right=row.get('stage',str(row.get('allowed',''))+' allowed, '+str(row.get('pilot_count',''))+' pilot count')
   h1=paragraph(c,left,56,y,320,25,font='RubikMedium',color=ORANGE);h2=paragraph(c,right,420,y,780,23);hh=max(h1,h2);line(c,56,y-hh-12,1160);y-=hh+30
  return
 if vd.get('items'):
  for i,row in enumerate(vd['items']):
   y=495-i*110;paragraph(c,row['provider'],56,y,340,29,font='RubikBold',color=ORANGE);paragraph(c,row['resource'],435,y,775,27)
  paragraph(c,body,56,140,1160,23,color=GRAY);return
 if vd.get('artifacts'):
  paragraph(c,body,56,520,1160,27)
  for i,a in enumerate(vd['artifacts']):
   x=56+(i%3)*407;y=333-(i//3)*107;node(c,a,x,y,362,80,i==0)
  return
 if vd.get('required'):
  paragraph(c,'After class' if s['id']=='p1-before-part2' else 'Required',56,510,560,27,color=ORANGE,font='RubikBold')
  y=460
  for t in vd['required']:
   hh=paragraph(c,t,56,y,730,24);y-=hh+16
  regs=vd.get('registrations')
  if regs:
   for i,r in enumerate(regs):
    paragraph(c,r['title'],854+i*184,510,170,21,font='RubikMedium')
    pic(c,R/'assets'/Path(r['qr']).name,854+i*184,272,162,162)
    c.linkURL(r['url'],(854+i*184,272,1016+i*184,434),relative=0)
    paragraph(c,r['url'],854+i*184,257,170,13,color=GRAY)
  else:paragraph(c,'Optional',854,510,354,27,color=ORANGE,font='RubikBold');paragraph(c,vd.get('optional',[]),854,450,354,25)
  return
 if vd.get('registrations'):
  paragraph(c,body,56,520,1160,30)
  for i,r in enumerate(vd['registrations']):
   x=120+i*608;paragraph(c,r['title'],x,416,420,29,font='RubikBold',color=ORANGE)
   pic(c,R/'assets'/Path(r['qr']).name,x,133,220,220)
   c.linkURL(r['url'],(x,133,x+220,353),relative=0)
   paragraph(c,r['url'],x,115,420,20,color=GRAY)
  return
 image=vd.get('image') or vd.get('path') or vd.get('asset')
 known={'zuora':'actual-zuora-page.png','gift':'gift-message-preview-redacted.png','skill-map':'actual-skill-map.png'}
 if image:
  p=ROOT/image
  if not p.exists():p=ROOT/'assets'/Path(image).name
  if pic(c,p,56,158,1168,375):
   paragraph(c,body,56,133,1168,21);return
 if 'zuora' in key:
  pic(c,ROOT/'assets/actual-zuora-page.png',56,135,870,390)
  paragraph(c,body,958,510,268,22);return
 if s.get('type') in ('break','pause','comic_relief'):
  if s['id']=='p1-break':
   pic(c,R/'assets/workshop-cover.png',620,90,620,460);paragraph(c,body,56,440,530,37,font='RubikMedium')
  else:paragraph(c,body,110,450,1050,43,font='RubikMedium')
  paragraph(c,vd.get('caption','Save your work before continuing.'),56,185,560,24,color=GRAY);return
 steps=s.get('steps') or []
 if steps:
  y=514
  for i,st in enumerate(steps):
   if isinstance(st,str):st={'title':st,'detail':''}
   paragraph(c,str(i+1).zfill(2),56,y,70,30,color=ORANGE,font='RubikBold')
   hh=paragraph(c,st.get('title',''),140,y,1080,27,font='RubikMedium');y-=hh+8
   if st.get('detail'):hh=paragraph(c,st['detail'],140,y,1060,22,color=GRAY);y-=hh+20
  if body and y>220:paragraph(c,body,140,y-8,1045,23)
 else:
  chunks=re.split(r'\n\n|\n',body)
  y=500
  for chunk in chunks:
   hh=paragraph(c,chunk,56,y,1168,32);y-=hh+26
  # Functional sequence, grounded in the slide's supplied labels.
  seq=vd.get('nodes') or vd.get('sequence') or vd.get('stages') or vd.get('labels')
  if seq and isinstance(seq,list) and len(seq)<=5:
   width=1168/len(seq)-20
   for i,t in enumerate(seq):
    label=t.get('label',str(t)) if isinstance(t,dict) else str(t)
    node(c,label,56+i*(width+20),140,width,90,i==0)

def slide(c,s,num,part):
 global CURRENT_SECTION
 CURRENT_SECTION=s.get('chapter',1)
 if part==1 and s['id']=='p1-cover':
  c.setFillColor(CREAM);c.rect(0,0,W,H,fill=1,stroke=0)
  pic(c,R/'assets/workshop-cover.png',0,0,W,H)
  c.setFillColor(ORANGE);c.rect(0,H-8,W,8,fill=1,stroke=0)
  paragraph(c,'metadata.',56,670,330,25,font='RubikBold')
  paragraph(c,'Build your own\nAgentic GTM',56,566,395,54,font='RubikBold',leading=62)
  paragraph(c,'Part 1\nBuild two pages for your\ntarget companies.',56,331,405,27,leading=38)
  paragraph(c,'Gil Allouche\nCEO, Metadata',56,177,395,22,font='RubikMedium')
  paragraph(c,'Booklet, full prompts and starter code included.',56,52,800,16,color=GRAY)
  c.linkURL('https://github.com/f-o-x11/agentic-gtm-workshop',(56,27,610,55),relative=0)
  c.showPage();return
 source='; '.join(plain(x) if not isinstance(x,dict) else x.get('label',x.get('path',str(x))) for x in (s.get('sources') or []))
 if part==1 and s.get('prompt'):source='Full prompt: prompts.html#'+s['id']
 source=source.replace(str(ROOT),'')
 if len(source)>180:source=source[:177]+'...'
 header(c,s['title'],num,part,source)
 if part==1 and part_one_example(c,s):pass
 elif s.get('type')=='cover':
  pic(c,R/'assets/workshop-cover.png',620,105,620,445)
  paragraph(c,s.get('body',''),56,490,540,32)
  paragraph(c,'Gil Allouche\nCEO, Metadata',56,290,500,25,font='RubikMedium')
 elif s.get('type')=='exercise':
  timing='Optional after class' if s.get('route')=='optional' else plain(s.get('timing',''))+' min'
  paragraph(c,timing+'   /   '+plain(s.get('difficulty',''))+'   /   '+', '.join(s.get('tools',[])),56,507,1168,17,color=ORANGE,font='RubikMedium')
  steps=s.get('steps',[]);y=451
  clone_first=False
  if clone_first:
   c.setFillColor(HexColor('#ffffff'));c.setStrokeColor(LINE);c.roundRect(56,419,1168,70,8,fill=1,stroke=1)
   paragraph(c,'git clone https://github.com/f-o-x11/agentic-gtm-workshop.git',76,469,1128,25,font='RubikMedium')
   y=388
  prepared=[]
  for i,st in enumerate(steps[:4]):
   if isinstance(st,str):st={'title':st,'detail':''}
   txt=st.get('title','').rstrip('.')+(('. '+st['detail']) if st.get('detail') else '')
   prepared.append((i,st,txt))
  def step_height(txt):
   p=Paragraph(escape(plain(txt)),ParagraphStyle('step',fontName='Rubik',fontSize=25,leading=32.5));return p.wrap(1090,H)[1]+15
  compact=sum(step_height(txt) for _,_,txt in prepared)>216
  for i,st,txt in prepared:
   if compact or clone_first:txt=st.get('title','')
   paragraph(c,str(i+1),56,y,55,27,color=ORANGE,font='RubikBold')
   hh=paragraph(c,txt,112,y,1090,21 if clone_first else 25);y-=hh+(13 if clone_first else 15)
  if not steps:y-=paragraph(c,s.get('body',''),56,y,1168,28)
  seq=s.get('visual_data',{}).get('stages',[])
  if seq and len(seq)<=5 and y>350:
   width=1168/len(seq)-18
   for i,t in enumerate(seq):
    x=56+i*(width+18);node(c,plain(t),x,252,width,61,i==0)
    if i<len(seq)-1:arrow(c,x+width,281,x+width+18,281)
  outcome_height=paragraph(c,'You should have: '+plain(s.get('expected','')),56,216,1168,20,font='RubikMedium')
  paragraph(c,'Check: '+plain(s.get('check','')),56,min(145,216-outcome_height-15),1168,17,color=GRAY)
  if s.get('prompt'):paragraph(c,'Full prompt on the next page and at prompts.html#'+s['id'],56,75,1168,10,color=ORANGE)
 else:generic(c,s)
 c.showPage()

def prompt_slide(c,s,num,part):
 txt=plain(s['prompt']);size=21
 while size>17:
  p=Paragraph(escape(txt).replace('\n','<br/>'),ParagraphStyle('measure',fontName='Rubik',fontSize=size,leading=size*1.3))
  if p.wrap(1155,H)[1]<=400:break
  size-=1
 p=Paragraph(escape(txt).replace('\n','<br/>'),ParagraphStyle('measure',fontName='Rubik',fontSize=size,leading=size*1.3))
 header(c,'Prompt: '+s['title'],num,part,'Complete copy source: prompts.html#'+s['id'])
 if p.wrap(1155,H)[1]<=400:
  paragraph(c,txt,62,517,1155,size,font='Rubik',leading=size*1.3)
 else:
  # A long prompt remains whole in its copy source. Never print a partial prompt.
  paragraph(c,'Open prompts.html',62,477,1155,49,font='RubikBold',color=ORANGE)
  paragraph(c,'Find "'+s['title']+'". Click Copy prompt.',62,388,1155,32)
  paragraph(c,'Paste it into the local Claude Code or Codex project you opened for this workshop.',62,313,1155,28)
  paragraph(c,'The copy source includes the full instructions. This slide contains no partial prompt.',62,220,1155,22,color=GRAY)
 c.linkURL('prompts.html#'+s['id'],(62,66,1220,112),relative=1)
 paragraph(c,'Copy full prompt: prompts.html#'+s['id'],62,104,1155,19,color=ORANGE,font='RubikMedium')
 if s.get('next_id'):
  paragraph(c,'Next: '+s.get('next_action',s['next_id'])+' ('+s['next_id']+')',62,77,1155,14,color=GRAY)
 c.showPage()
 return 1

def chapter_slide(c,ch,num,part):
 global CURRENT_SECTION
 CURRENT_SECTION=ch['number']
 if part==1:
  header(c,'Section '+str(ch['number'])+' of 5',num,part)
  paragraph(c,ch['title'],56,503,1160,48,font='RubikBold')
  tasks={2:['Open your cloned project.','Paste the startup prompt.','Review the company brief.'],3:['Read both target websites.','Save facts with their sources.','Save your two-company list.'],4:['Create your first HTML page.','Check every claim against its source.','Open it on desktop and phone.'],5:['Save the page instructions as a skill.','Use it for the second company.','Check both pages and saved files.']}[ch['number']]
  for i,task in enumerate(tasks):
   paragraph(c,str(i+1),56,392-i*69,50,29,color=ORANGE,font='RubikBold')
   paragraph(c,task,114,392-i*69,1095,28)
  paragraph(c,ch['outcome'],56,172,1160,21,color=GRAY)
  timing=str(ch['guided_minutes'])+' minutes'
  if ch['help_minutes']:timing+=' + '+str(ch['help_minutes'])+' minutes for individual help'
  paragraph(c,timing,56,108,1160,21,font='RubikMedium',color=ORANGE)
  c.showPage();return
 header(c,'Chapter '+str(ch['number'])+' of 5',num,part)
 paragraph(c,ch['title'],56,490,1160,56,font='RubikBold')
 paragraph(c,ch['outcome'],56,328,1120,30)
 timing=str(ch['guided_minutes'])+' guided minutes'
 if ch['help_minutes']:timing+=' + '+str(ch['help_minutes'])+' minutes for help'
 paragraph(c,timing,56,186,1160,22,color=GRAY)
 paragraph(c,'Open the next full prompt. Review the result before moving on.',56,128,1160,22,color=GRAY)
 c.showPage()

def make_decks(data):
 counts={}; allpdf=[]
 for part in data['parts']:
  n=part['part'];dest=OUT/f'Part-{n}-Presentation.pdf';c=canvas.Canvas(str(dest),pagesize=(W,H));c.setTitle(part['title']);c.setAuthor('Gil Allouche, Metadata')
  num=0;current_chapter=None
  for s in part['slides']:
   if s['chapter']!=current_chapter:
    current_chapter=s['chapter'];ch=part['chapters'][current_chapter-1]
    c.bookmarkPage(ch['id']);c.addOutlineEntry('Chapter '+str(current_chapter)+': '+ch['title'],ch['id'],0)
    if current_chapter>1:
     num+=1;CHECKS.clear();chapter_slide(c,ch,num,n)
   num+=1;c.bookmarkPage(s['id']);c.addOutlineEntry(s['title'],s['id'],1)
   CHECKS.clear();slide(c,s,num,n)
   bad=[x for x in CHECKS if x['bottom']<64 and x['size']>16]
   if bad:raise ValueError('Slide overflow '+s['id']+' '+str(bad))
   if s.get('prompt'):
    num+=1;CHECKS.clear();num+=prompt_slide(c,s,num,n)-1
    bad=[x for x in CHECKS if x['bottom']<64 and x['size']>16]
    if bad:raise ValueError('Prompt overflow '+s['id']+' '+str(bad))
  c.save();counts[str(part['id'])]=num;allpdf.append(dest)
 writer=PdfWriter()
 for part,p in zip(data['parts'],allpdf):writer.append(str(p),outline_item=part['title'])
 with open(OUT/'Complete-Presentation.pdf','wb') as f:writer.write(f)
 return counts

ST=getSampleStyleSheet()
for name in ['Normal','BodyText']:
 ST[name].fontName='Rubik';ST[name].fontSize=10.8;ST[name].leading=15.3;ST[name].textColor=BLACK;ST[name].spaceAfter=7
for name,size,col in [('Title',29,BLACK),('Heading1',22,BLACK),('Heading2',16,ORANGE),('Heading3',12,BLACK)]:
 ST[name].fontName='RubikBold';ST[name].fontSize=size;ST[name].leading=size*1.2;ST[name].textColor=col;ST[name].spaceBefore=12;ST[name].spaceAfter=10
 ST[name].keepWithNext=True
ST.add(ParagraphStyle('CodeWrap',fontName='Rubik',fontSize=10.4,leading=14.1,textColor=BLACK,backColor=HexColor('#f1f1ee'),borderPadding=8,spaceBefore=4,spaceAfter=10))

def rich(s):
 s=escape(plain(s))
 s=re.sub(r'\[([^]]+)\]\((https?[^)]+)\)',r'<link href="\2" color="#1a7a69">\1</link>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'`([^`]+)`',r'<font name="Courier">\1</font>',s)
 return s

def footer(c,doc):
 c.setFillColor(ORANGE);c.rect(0,doc.pagesize[1]-6,doc.pagesize[0],6,fill=1,stroke=0)
 c.setFillColor(GRAY);c.setFont('Rubik',8);c.drawString(43,24,'Metadata | Agentic GTM v5 workshop | October 2026');c.drawRightString(doc.pagesize[0]-43,24,str(doc.page))

class ChapterFlow(Flowable):
 def __init__(self,labels):
  super().__init__();self.labels=labels;self.width=508;self.height=72
 def draw(self):
  c=self.canv;bw=115
  for i,label in enumerate(self.labels):
   x=i*131;c.setFillColor(ORANGE if i==0 else HexColor('#ffffff'));c.setStrokeColor(LINE);c.rect(x,14,bw,48,fill=1,stroke=1)
   p=Paragraph(escape(label),ParagraphStyle('flow',fontName='RubikMedium',fontSize=10,leading=13,textColor=HexColor('#ffffff') if i==0 else BLACK))
   _,hh=p.wrap(bw-14,48);p.drawOn(c,x+7,38-hh/2)
   if i<3:arrow(c,x+bw,38,x+131,38)

def markdown_pdf(src,out,title):
 from reportlab.lib.pagesizes import A4
 doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=42,bottomMargin=43,title=title,author='Gil Allouche, Metadata')
 story=[Paragraph(title,ST['Title']),Spacer(1,12)]
 picpath=R/'assets/workshop-cover.png'
 im=Image(str(picpath),width=508,height=285);story.extend([im,Spacer(1,15),Paragraph('Three individual workshops. Your company, your accounts, your results.',ST['BodyText']),PageBreak()])
 lines=plain(src).splitlines();i=0
 while i<len(lines):
  l=lines[i].strip()
  if not l:i+=1;continue
  if l.startswith('```'):
   code=[];i+=1
   while i<len(lines) and not lines[i].strip().startswith('```'):code.append(lines[i]);i+=1
   # Keep a complete prompt together whenever it fits on one readable page.
   text='\n'.join(code);block=Paragraph(escape(text).replace('\n','<br/>'),ST['CodeWrap'])
   _,block_height=block.wrap(492,756)
   if block_height<=730:story.append(KeepTogether([block]))
   else:
    # The authoritative copy source is always a whole prompt in prompts.html.
    story.append(Paragraph('Copy the complete prompt from <b>prompts.html</b>. The full text below is a reading reference.',ST['BodyText']))
    story.append(block)
   i+=1;continue
  if l.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r'[:\- ]+',x) for x in row):rows.append(row)
    i+=1
   n=max(len(row) for row in rows);widths=[508/n]*n
   ps=ParagraphStyle('tb',parent=ST['BodyText'],fontSize=8.5,leading=11.5,spaceAfter=0)
   cells=[[Paragraph(rich(x),ps) for x in (row+['']*(n-len(row)))] for row in rows]
   t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#fff7ed')),('LINEBELOW',(0,0),(-1,0),1,ORANGE),('LINEBELOW',(0,1),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([t,Spacer(1,10)]);continue
  m=re.match(r'^(#{1,4})\s+(.+)',l)
  if m:
   level=len(m[1]);style=ST['Heading1' if level<2 else 'Heading2' if level==2 else 'Heading3']
   if re.match(r'Part [123]:',m[2]):
    story.append(PageBreak())
   story.append(Paragraph(rich(m[2]),style))
   if m[2].startswith('Part 1:'):story.append(ChapterFlow(['Company facts','Account research','Reviewed page','Saved skill']))
   elif m[2].startswith('Part 2:'):story.append(ChapterFlow(['Ten companies','Eleven approved emails','Your own Sent test','Ten prospect results']))
   elif m[2].startswith('Part 3:'):story.append(ChapterFlow(['Replies and bookings','Prior attempts','Next bounded cycle','Pause and recovery']))
   i+=1;continue
  if re.match(r'^[-*]\s+',l):l='• '+l[2:]
  # Keep real paragraphs together without concatenating numbered instructions.
  if not re.match(r'^\d+\.|^•',l):
   while i+1<len(lines) and lines[i+1].strip() and not re.match(r'^(#|\||```|[-*]\s|\d+\.)',lines[i+1].strip()):
    i+=1;l+=' '+lines[i].strip()
  story.append(Paragraph(rich(l),ST['BodyText']));i+=1
 doc.build(story,onFirstPage=footer,onLaterPages=footer)

HELPER_STYLE = """
@font-face{font-family:Rubik;src:url('assets/Rubik-400.ttf')}@font-face{font-family:Rubik;src:url('assets/Rubik-700.ttf');font-weight:700}
:root{--ink:#132033;--orange:#f05a28;--paper:#fbf9f6;--gray:#536072;--line:#ddd9d4}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:84px}body{margin:0;font:18px/1.55 Rubik,Arial,sans-serif;color:var(--ink);background:var(--paper)}
a{color:#ae3911;text-underline-offset:4px}a:hover{color:#132033}header{position:sticky;top:0;background:rgba(251,249,246,.96);border-bottom:1px solid var(--line);z-index:2;padding:15px 28px;display:flex;justify-content:space-between;align-items:center;gap:20px}header a{text-decoration:none}.brand{font-size:19px;font-weight:700;letter-spacing:-.7px}.brand span{color:var(--orange)}main{max-width:1120px;margin:auto;padding:42px 28px 90px}.eyebrow{color:var(--orange);text-transform:uppercase;letter-spacing:2px;font-size:13px;font-weight:700}h1{font-size:clamp(40px,5vw,66px);line-height:1.08;letter-spacing:-2px;max-width:920px;margin:17px 0 24px}h2{font-size:31px;line-height:1.2;letter-spacing:-.7px;margin:0 0 15px}h3{font-size:21px;margin:20px 0 10px}.intro{font-size:22px;max-width:750px;color:var(--gray)}.path{padding:14px 0 22px;border-bottom:2px solid var(--ink);font-size:16px;color:var(--gray)}.path strong{color:var(--ink)}.part-title{margin-top:64px}.chapter{padding:34px 0 24px;border-bottom:2px solid var(--orange);margin-top:24px}.toc{display:flex;flex-wrap:wrap;gap:10px 22px;padding:20px 0;margin:24px 0;border-block:1px solid var(--line);font-size:16px}.exercise{padding:42px 0;border-bottom:1px solid var(--line);scroll-margin-top:90px}.meta{font-size:15px;color:var(--gray);margin:10px 0}.expected{margin:16px 0;padding-left:22px}.expected li{margin:5px 0}.prompt-label{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:24px}.prompt-label p{margin:0;font-size:14px;color:var(--gray)}textarea{display:block;box-sizing:border-box;width:100%;min-height:310px;max-height:650px;resize:vertical;font:16px/1.55 Rubik,Arial,sans-serif;padding:22px;border:1px solid #c9c6c1;background:#fff;color:var(--ink);border-radius:8px;white-space:pre-wrap}textarea:focus,input:focus{outline:3px solid #f3c0a5;outline-offset:2px}button,.button{display:inline-block;margin:15px 12px 10px 0;background:#c34314;color:white;border:0;border-radius:6px;padding:13px 20px;font:700 16px Rubik,Arial,sans-serif;cursor:pointer;text-decoration:none;transition:transform .15s,background .15s;min-height:48px}button:hover,.button:hover{background:#9f2c0b;color:white;transform:translateY(-2px)}button:active{transform:translateY(0)}button:focus-visible,.button:focus-visible{outline:3px solid #132033;outline-offset:3px}.copy-status{font-size:14px;color:#2b6552;min-height:25px}.hint{font-size:15px;color:var(--gray)}.next{margin-top:20px;font-size:17px}.note{border-left:3px solid var(--orange);padding:4px 0 4px 18px;margin:25px 0;color:var(--gray)}.steps{list-style:none;padding:0;counter-reset:step;margin:36px 0}.steps li{position:relative;padding:0 0 23px 53px;counter-increment:step}.steps li:before{content:counter(step);position:absolute;left:0;top:-4px;color:var(--orange);font-size:30px;font-weight:700}.steps strong{display:block;font-size:22px}.steps p{margin:4px 0;max-width:760px;color:var(--gray)}.helper{border-top:1px solid var(--line);padding-top:30px;margin-top:24px}label{display:block;font-size:15px;margin:15px 0 7px}input{width:100%;font:18px Rubik,Arial,sans-serif;min-height:48px;border:1px solid #c9c6c1;border-radius:6px;background:white;padding:12px}details{margin:17px 0}summary{cursor:pointer;font-size:16px;color:var(--gray)}.field-pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}.stop{font-size:18px;font-weight:700;margin-top:26px}.legend{font-size:14px;color:var(--gray)}code{font:14px/1.4 monospace;background:#eeebe7;padding:3px 5px;border-radius:3px}footer{border-top:1px solid var(--line);margin-top:45px;padding-top:20px;font-size:14px;color:var(--gray)}@media(max-width:650px){header{padding:13px 18px}header a{font-size:14px}main{padding:28px 18px 65px}h1{letter-spacing:-1.2px}h2{font-size:27px}.intro{font-size:19px}.field-pair{grid-template-columns:1fr;gap:0}.prompt-label{display:block}textarea{padding:15px;font-size:15px}.exercise{padding:32px 0}.toc{gap:8px 16px}.steps li{padding-left:44px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}button,.button{transition:none}}
"""
COPY_JS = """
async function copyPrompt(id,button){
 const area=document.getElementById(id);const status=document.getElementById('status-'+id);let ok=false;
 try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(area.value);ok=true;}}catch(error){}
 if(!ok){area.focus();area.select();try{ok=document.execCommand('copy');}catch(error){ok=false;}}
 if(ok){button.textContent='Copied';button.dataset.copied='true';if(status)status.textContent=id==='clone-command'?'Clone command copied. Run it in Codex, Claude Code or your terminal.':'Full prompt copied. Paste it into your local Claude Code or Codex project.';}
 else{button.textContent='Select and copy';if(status)status.textContent='The browser blocked copying. The full prompt is selected. Press Command+C on Mac or Ctrl+C on Windows.';}
}
"""

def expected_html(value):
 values=value if isinstance(value,list) else [value]
 return '<ul class="expected">'+''.join('<li>'+html.escape(plain(v))+'</li>' for v in values if v)+'</ul>'

def helper_assets():
 assets=OUT/'assets';assets.mkdir(exist_ok=True)
 for weight in (400,700):
  source=R/f'assets/Rubik-{weight}.ttf';target=assets/f'Rubik-{weight}.ttf'
  if source.resolve()!=target.resolve():shutil.copyfile(source,target)

def page_html(title,body,js=''):
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+HELPER_STYLE+'</style></head><body><header><a class="brand" href="START-HERE.html">metadata<span>.</span></a><a href="prompts.html">Workshop prompts</a></header><main>'+body+'<footer>Your company, your local project, your accounts. API keys stay in your private local credentials file.</footer></main><script>'+COPY_JS+js+'</script></body></html>'

def prompt_html(data):
 helper_assets();content=['<p class="eyebrow">Agentic GTM workshop</p><h1>Your workshop prompts.</h1><p class="intro">Copy into the same local Claude Code or Codex project each time. Read the result, check it, then take the next step.</p><p class="path"><strong>First time here?</strong> <a href="START-HERE.html">Start here</a>. The browser is your prompt reader. Your local agent works with the files.</p>']
 exercises=[s for p in data['parts'] for s in p['slides'] if s.get('prompt')]
 content.append('<nav class="toc" aria-label="Workshop parts">'+''.join('<a href="#part-'+str(p['part'])+'">Part '+str(p['part'])+'</a>' for p in data['parts'])+'</nav>')
 for p in data['parts']:
  content.append('<h1 class="part-title" id="part-'+str(p['part'])+'">'+html.escape(p['title'])+'</h1>')
  content.append('<nav class="toc" aria-label="Five chapters">'+''.join('<a href="#'+ch['id']+'">'+str(ch['number'])+'. '+html.escape(ch['title'])+'</a>' for ch in p['chapters'])+'</nav>')
  current_chapter=None
  for index,s in enumerate(p['slides']):
   if s['chapter']!=current_chapter:
    current_chapter=s['chapter'];ch=p['chapters'][current_chapter-1]
    content.append('<section class="chapter" id="'+ch['id']+'"><p class="eyebrow">Chapter '+str(current_chapter)+' of 5</p><h2>'+html.escape(ch['title'])+'</h2><p>'+html.escape(ch['outcome'])+'</p></section>')
   if not s.get('prompt'):
    ident=html.escape(s['id']);title=html.escape(s['title'])
    content.append('<section class="exercise reading-step" id="'+ident+'"><h2>'+title+'</h2><p>'+html.escape(plain(s.get('body',''))).replace('\n','<br>')+'</p>')
    next_id=s.get('next_id') or (p['slides'][index+1]['id'] if index+1<len(p['slides']) else None)
    if next_id:
     action=s.get('next_action') or ('When the presenter resumes: next step' if s.get('type') in ('break','pause') else 'Next step')
     content.append('<p class="next"><a class="next-step" href="#'+html.escape(next_id)+'">'+html.escape(action)+'</a></p>')
    content.append('</section>');continue
   ident=html.escape(s['id']);title=html.escape(s['title']);q=html.escape(s['prompt'])
   timing='Optional after class. ' if s.get('route')=='optional' else plain(s.get('timing',''))+' minutes. '
   meta=timing+plain(s.get('difficulty',''))+'. Tools: '+', '.join(s.get('tools',[]))+'.'
   content.append('<section class="exercise" id="'+ident+'"><h2>'+title+'</h2><p class="meta">'+html.escape(meta)+'</p><h3>You should have</h3>'+expected_html(s.get('expected',''))+'<p class="hint"><strong>Check:</strong> '+html.escape(plain(s.get('check','')))+'</p><div class="prompt-label"><h3>Full prompt</h3><p>Paste into local Claude Code or Codex.</p></div><textarea id="p-'+ident+'" readonly aria-label="Full prompt for '+title+'">'+q+'</textarea><button data-copy-for="p-'+ident+'" onclick="copyPrompt(this.dataset.copyFor,this)">Copy full prompt</button><p class="copy-status" id="status-p-'+ident+'" aria-live="polite"></p>')
   if s.get('fallback') or s.get('repair_prompt'):
    content.append('<details class="repair"><summary>If you get stuck</summary><p>'+html.escape(plain(s.get('fallback','')))+'</p>')
    if s.get('repair_prompt'):
     repair=html.escape(s['repair_prompt'])
     content.append('<h3>Repair this step</h3><p class="hint">Replace the error placeholder in your local agent. Remove credentials from the error first.</p><textarea id="r-'+ident+'" readonly aria-label="Repair prompt for '+title+'">'+repair+'</textarea><button data-copy-for="r-'+ident+'" onclick="copyPrompt(this.dataset.copyFor,this)">Copy repair prompt</button><p class="copy-status" id="status-r-'+ident+'" aria-live="polite"></p>')
    content.append('</details>')
   if s.get('next_id'):content.append('<p class="next">After the check passes: <a class="next-step" href="#'+html.escape(s['next_id'])+'">'+html.escape(s.get('next_action','Next step'))+'</a></p>')
   else:content.append('<p class="next">Save the result. Stop here and follow the presenter.</p>')
   content.append('</section>')
 (OUT/'prompts.html').write_text(page_html('Metadata workshop prompts',''.join(content)))
 # The generated helper is at the project root.

def starter_html(data):
 setup=next(s for p in data['parts'] for s in p['slides'] if s['id']=='p1-install')
 prompt=setup['prompt'];q=html.escape(prompt)
 body='<p class="eyebrow">Start here</p><h1>Your first result:<br>a company brief.</h1><p class="intro">You already have the starter code. Tell your local agent about your company. It will prepare the project and stop after the first step.</p><ol class="steps"><li><strong>Clone the workshop.</strong><p>Run this in Codex, Claude Code or your terminal.</p><textarea id="clone-command" readonly aria-label="Clone command" style="min-height:70px">git clone https://github.com/f-o-x11/agentic-gtm-workshop.git</textarea><button data-copy-for="clone-command" onclick="copyPrompt(this.dataset.copyFor,this)">Copy clone command</button><p class="copy-status" id="status-clone-command" aria-live="polite"></p></li><li><strong>Open the workshop folder in Claude Code or Codex.</strong><p>Choose <code>agentic-gtm-workshop</code>. It contains <code>START-HERE.html</code>, <code>prompts.html</code> and the <code>code</code> folder. Keep using this same project for all three parts.</p></li><li><strong>Copy the prompt below.</strong><p>Paste it into that local project. The agent reads your website, saves a company brief, prepares the missing setup files and pauses.</p></li></ol><p class="note">Open the folder as a local project. Paste one prompt, review its result and stop before the next exercise.</p><div class="helper"><h2>Use your own company</h2><p class="hint">Your website is enough to start. If you know the other answers, add them now. These fields stay in this page. Do not enter API keys.</p><label for="company-site">Company website</label><input id="company-site" type="url" placeholder="https://your-company.com" autocomplete="url"><details><summary>Optional: buyer, offer and two target companies</summary><label for="buyer">Who do you want to reach?</label><input id="buyer" placeholder="For example: CMOs at B2B software companies"><label for="offer">What can you offer them?</label><input id="offer" placeholder="Use your actual offer, without inventing terms"><div class="field-pair"><div><label for="target-one">First target domain</label><input id="target-one" placeholder="company-one.com"></div><div><label for="target-two">Second target domain</label><input id="target-two" placeholder="company-two.com"></div></div></details><div class="prompt-label"><h3>Full startup prompt</h3><p>Local Claude Code or Codex.</p></div><textarea id="startup-prompt" readonly aria-label="Full startup prompt">'+q+'</textarea><button id="copy-startup" data-copy-for="startup-prompt" onclick="copyPrompt(this.dataset.copyFor,this)">Copy full prompt</button><p class="copy-status" id="status-startup-prompt" aria-live="polite"></p><h3>You should have</h3>'+expected_html(setup.get('expected',''))+'<p class="hint"><strong>Check:</strong> '+html.escape(plain(setup.get('check','')))+'</p><p class="stop">Read the company brief. Then continue to the next exercise.</p><a class="button next-step" href="prompts.html#'+html.escape(setup.get('next_id','p1-company'))+'">'+html.escape(setup.get('next_action','Review your company brief'))+'</a><p class="legend">Python setup is automatic when a supported version exists. If it is missing, the agent gives you the official installer link and pauses. No API account is needed for Part 1.</p></div>'
 js='const sourcePrompt='+json.dumps(prompt).replace('</','<\\/')+';const tokens={"company-site":"[YOUR_COMPANY_WEBSITE]","buyer":"[BUYER_SEGMENT]","offer":"[COLD_OFFER]","target-one":"[TARGET_1_DOMAIN]","target-two":"[TARGET_2_DOMAIN]"};function updateStartup(){let p=sourcePrompt;for(const [id,token] of Object.entries(tokens)){const value=document.getElementById(id).value.trim();if(value)p=p.split(token).join(value);}document.getElementById("startup-prompt").value=p;document.getElementById("copy-startup").textContent="Copy full prompt";document.getElementById("status-startup-prompt").textContent="";}for(const id of Object.keys(tokens))document.getElementById(id).addEventListener("input",updateStartup);'
 builder_prompt='Read BUILD-MY-GTM.md and follow its Build my workflow instructions. Ask me one question at a time, use my answers to adapt this project, and complete all local preparation that does not need another answer. Start with my company website. Keep external actions paused until I review their exact recipients, messages and costs.'
 resources='<section class="helper" id="class-materials"><h2>Keep these open during class</h2><p><a href="Participant-Booklet.pdf">Participant booklet</a>: instructions and checks. <a href="prompts.html">Full prompts</a>: copy one exercise at a time.</p><p>Before class, sign in to local Codex or Claude Code and check that it can open your workshop folder and read your company website. Part 1 needs no API keys.</p><p><a href="PREWORK.md">Check the short setup list</a>.</p></section>'
 body=body.replace('<div class="helper"><h2>Use your own company</h2>',resources+'<div class="helper"><h2>Use your own company</h2>')
 body += '<section class="helper" id="build-my-workflow"><h2>Build the full local workflow</h2><p>Use this outside the guided exercises. Your agent asks questions, prepares your project and checks each available connection.</p><textarea id="builder-prompt" readonly aria-label="Build my workflow prompt">'+html.escape(builder_prompt)+'</textarea><button data-copy-for="builder-prompt" onclick="copyPrompt(this.dataset.copyFor,this)">Copy build prompt</button><p class="copy-status" id="status-builder-prompt" aria-live="polite"></p><p><a href="BUILD-MY-GTM.md">Read the full build instructions</a></p></section>'
 doc=page_html('Start your Agentic GTM workshop',body,js)
 (OUT/'START-HERE.html').write_text(doc)
 md='# Start here\n\n1. Run this command in Codex, Claude Code or your terminal:\n\n```bash\ngit clone https://github.com/f-o-x11/agentic-gtm-workshop.git\n```\n\n2. Open agentic-gtm-workshop as your local Claude Code or Codex project. It contains `START-HERE.html`, `prompts.html` and the `code` folder. The agent runs program commands from `code/`.\n3. Open `START-HERE.html` in your browser. Add your company website. Copy the full startup prompt and paste it into the local agent.\n4. Review the saved company brief before the next exercise. Keep the same project for all three parts.\n\nYou do not need API keys for Part 1. The starter uses an existing supported Python version, or gives you the official installer link.\n\nThe browser shows prompts. Your local agent works with the files. Never enter API keys in a browser helper.\n\n## Full startup prompt\n\n```text\n'+prompt+'\n```\n\n## Next step\n\n'+setup.get('next_action','Review your company brief')+'. Open `prompts.html#'+setup.get('next_id','p1-company')+'`.\n'
 md += '\n## Build the full local workflow\n\nFor an owner-requested build outside the guided exercises, paste:\n\n```text\n'+builder_prompt+'\n```\n\nFull instructions: BUILD-MY-GTM.md. External actions stay paused until their exact scope is approved.\n'
 (OUT/'START-HERE.md').write_text(md)

if __name__=='__main__':
 data=json.loads((R/'course/course.json').read_text())
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--startup-only',action='store_true');parser.add_argument('--preserve-pdf',action='append',default=[]);args=parser.parse_args()
 preserve_names=('Part-2-Presentation.pdf','Part-3-Presentation.pdf','API-Setup-Guide.pdf') if args.startup_only else args.preserve_pdf
 if any(name not in ('Part-1-Presentation.pdf','Part-2-Presentation.pdf','Part-3-Presentation.pdf','API-Setup-Guide.pdf') for name in preserve_names):parser.error('Only unchanged workshop PDFs can be preserved.')
 preserved={name:(OUT/name).read_bytes() for name in preserve_names}
 counts=make_decks(data)
 markdown_pdf((R/'course/BOOKLET.md').read_text(),OUT/'Participant-Booklet.pdf','Build your own Agentic GTM')
 markdown_pdf((R/'API-CONNECTIONS.md').read_text(),OUT/'API-Setup-Guide.pdf','Connect your own tools')
 prompt_html(data)
 starter_html(data)
 for name,blob in preserved.items(): (OUT/name).write_bytes(blob)
 (R/'authoring/pdf-manifest.json').write_text(json.dumps({'parts':counts,'all_pdfs':[{ 'file':p.name,'pages':len(PdfReader(p).pages),'bytes':p.stat().st_size} for p in sorted(OUT.glob('*.pdf'))]},indent=2))
 print(json.dumps(counts))
