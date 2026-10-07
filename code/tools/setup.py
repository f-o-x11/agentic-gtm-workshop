"""Set up the attendee's own project. Inputs and credentials stay outside the code folder."""
import csv
import hashlib
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
import webbrowser
from engine.database import ROOT, Store, digest, encode, now
from engine.http_client import HttpClient, ProviderError
from engine.validation import domain, email, fresh, load, profile, country, COUNTRY_NAMES


def private_file(path):
    if not path: raise ValueError('Provide the actual private input file path')
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Keep private inputs and credentials outside this code folder')
    if not path.is_file(): raise ValueError('Input file is missing: ' + str(path))
    return path


def read_json(path):
    return json.loads(private_file(path).read_text())


def credential_path(path):
    value=Path(path).expanduser().resolve(); artifacts=ROOT.parent/'company-motion'
    project=ROOT.parent.resolve()
    repository_layout=(project/'.git').exists() or (project/'START-HERE.md').is_file()
    if repository_layout and (value==project or project in value.parents):
        raise ValueError('Keep configuration and credentials outside this cloned repository')
    if value==ROOT or ROOT in value.parents or value==artifacts or artifacts in value.parents:
        raise ValueError('Keep configuration and credentials outside code and company-motion')
    if value.exists() and (not value.is_file() or value.stat().st_mode & 0o777 != 0o600):
        raise ValueError('Private configuration and credential files must use mode 0600')
    return value


def init(store, path):
    if store.setting('portable_initialized'):
        from gtm import bootstrap_workspace
        return {**bootstrap_workspace(ROOT), 'initialized': True, 'existing_project_retained': True,
            'next': 'Existing settings and grants were kept. Continue at your next unfinished workshop step.'}
    configure(store, path)
    existing_accounts = store.one('SELECT count(*) AS n FROM accounts')['n']
    with store.db:
        store.set('portable_initialized', True)
        store.event('project_initialized', store.setting('company', {}).get('domain'), {'empty_start': existing_accounts == 0})
    return {'initialized':True,'execution':'paused','existing_accounts_preserved':existing_accounts,'provider_writes':0}


def configure(store, path):
    path=credential_path(path)
    config = read_json(path)
    company = config.get('company', {}); authority = config.get('policy', {})
    brief = Path(company.get('brief_file') or ROOT.parent / 'company-motion' / 'COMPANY.md').expanduser().resolve()
    if not brief.is_file() or not brief.read_text().strip():
        raise ValueError('Create company-motion/COMPANY.md from your actual website before setup. Run bootstrap after saving it.')
    employer = domain(company.get('domain') or company.get('website'))
    if not employer or not company.get('name'): raise ValueError('Your company name and website are required')
    if not authority.get('authority'): raise ValueError('Write your actual owner authority before configuring execution')
    senders = authority.get('senders', {})
    if not senders or any(email(k) != k or type(v) is not int or v < 1 for k,v in senders.items()):
        raise ValueError('Use your own exact sender email and positive daily cap')
    countries = authority.get('recipient_company_countries')
    if not isinstance(countries, list) or not countries or any(not isinstance(v, str) or not v.strip() for v in countries):
        raise ValueError('List your authorized recipient company countries')
    authority = {**authority, 'recipient_company_countries': sorted({country(v) for v in countries})}
    if any(v not in COUNTRY_NAMES for v in authority['recipient_company_countries']):
        raise ValueError('Use a recognized country name or documented alias. Unknown permitted countries cannot authorize outreach.')
    paths = config.get('credential_files', {})
    for name, value in paths.items():
        if value: paths[name] = str(credential_path(value))
    settings = config.get('settings', {})
    if not isinstance(settings, dict): raise ValueError('settings must be an object')
    allowed = {'loop_and_tie_team','gift_gate','social_owned','social_prepared','social_reply_grants',
        'calendly_identity','hubspot_demo_forms','google_calendars','booking_sources','salesforce_owner_email',
        'revenue','native_exclusions','exclusion_mode','history_sources','asset_hosts','form_contract','metadata_account_id','netlify_site_id',
        'netlify_owner_id','radar','attendance_since'}
    unknown = set(settings) - allowed
    if unknown: raise ValueError('Unknown settings: ' + ','.join(sorted(unknown)))
    history=settings.get('history_sources',{}); start=config.get('history_since_epoch',0)
    if not isinstance(history,dict) or type(start) is not int or start<0:
        raise ValueError('Use exact history_sources and nonnegative history_since_epoch')
    if ('gmail' in history and history['gmail']!=list(senders)) or ('gmail_start' in history and history['gmail_start']!=start):
        raise ValueError('history_sources cannot override authorized sender mailboxes or history_since_epoch')
    if settings.get('exclusion_mode')=='native' and start!=0: raise ValueError('Native mode requires history_since_epoch 0')
    policy_path = store.policy_path
    previous = json.loads(policy_path.read_text()) if policy_path.exists() else {}
    local = {'execution_enabled': False, 'file_limit':20,
        'hourly_pacing':{'enforced':True,'daily_targets':config.get('daily_targets', {'email':sum(senders.values()),'gift':0,'social':0})},
        'portable_attendee':True}
    from gtm import bootstrap_workspace
    workspace = bootstrap_workspace(ROOT, brief)
    with store.db:
        store.set('company', {**company,'domain':employer})
        store.set('policy', authority); store.set('credential_files', paths)
        store.set('internal_domains', sorted({employer,*[s.rsplit('@',1)[-1] for s in senders]}))
        store.set('portable_attendee', True)
        store.set('batch_limits', config.get('batch_limits', {'email':10,'gift':1,'social':2}))
        store.set('hourly_pacing', local['hourly_pacing'])
        store.set('history_sources', {**history,'gmail':list(senders),'gmail_start':int(config.get('history_since_epoch',0))})
        store.set('exclusion_mode',settings.get('exclusion_mode','snapshot'))
        store.set('booking_sources', settings.get('booking_sources',['google_calendar']))
        store.set('google_calendars', settings.get('google_calendars',{'mailboxes':list(senders),'since':'2020-01-01T00:00:00Z'}))
        store.set('research_enabled', False)
        for key,value in settings.items():
            if key!='history_sources': store.set(key,value)
        for sender,cap in senders.items():
            store.db.execute('INSERT OR REPLACE INTO sender_consent VALUES (?,?,?,?,?)',
                (sender,cap,1,'owner.private_config',encode({'authority':authority['authority']})))
        # Revocation in a newer config also disables the old sender row.
        for row in store.rows('SELECT email FROM sender_consent'):
            if row['email'] not in senders:
                store.db.execute('UPDATE sender_consent SET enabled=0 WHERE email=?',(row['email'],))
        store.set('private_config_path',str(private_file(path)))
    policy_path.parent.mkdir(parents=True,exist_ok=True)
    policy_path.write_text(json.dumps(local,indent=2)+'\n'); policy_path.chmod(0o600)
    return {'configured':True,'company':employer,'senders':list(senders),
        'recipient_company_countries':authority['recipient_company_countries'],
        'workspace':workspace,'research':'paused','provider_writes':0}


def read_records(path):
    path = private_file(path)
    if path.suffix.lower()=='.csv':
        with path.open(newline='') as stream: return list(csv.DictReader(stream))
    data = json.loads(path.read_text())
    return data['records'] if isinstance(data,dict) and isinstance(data.get('records'),list) else data


def approve_release(store, path, pilot=False):
    from engine.checks import unpack, action_hash
    value=read_json(path); authority=value.get('authority')
    if not isinstance(authority,str) or not authority.strip(): raise ValueError('Write your actual approval of the exact recipients and copy')
    keys=([value.get('controlled_action_key')]+value.get('prospect_action_keys',[])) if pilot else value.get('action_keys',[])
    if not isinstance(keys,list) or not keys or len(set(keys))!=len(keys): raise ValueError('Approve unique existing exact action keys')
    if pilot and len(keys)!=11: raise ValueError('Pilot needs one owned test and ten prospect action keys')
    actions={}; counts={'email':0,'gift':0,'social':0}; policy=store.setting('policy',{})
    for key in keys:
        row=store.one('SELECT * FROM actions WHERE action_key=?',(key,)); action=unpack(row) if row else {}
        if not row or action_hash(action)!=key or store.one('SELECT idem_key FROM attempts WHERE idem_key=?',(key,)):
            raise ValueError('Approve unchanged, unattempted prepared actions only')
        controlled=action['payload'].get('controlled_test') is True
        if pilot and (action['channel']!='email' or controlled!=(key==keys[0])): raise ValueError('Pilot actions must be one labeled email test and ten prospect emails')
        if controlled and (action['recipient']!=action['sender'] or action['recipient'] not in policy.get('senders',{}) or action['recipient'] not in policy.get('controlled_test_recipients',[])):
            raise ValueError('Owned self-test recipient must equal its exact authorized sender and controlled test mailbox')
        if not controlled and action['domain'] in store.setting('internal_domains',[]): raise ValueError('Prospect approval cannot include your own company')
        actions[key]={k:action[k] for k in ('action_key','channel','recipient','domain','sender','at')}
        actions[key].update(payload_digest=digest(action['payload']),controlled_test=controlled)
        counts[{'linkedin':'social','linkedin_message':'social'}.get(action['channel'],action['channel'])]+=1
    if pilot and len({actions[k]['domain'] for k in keys[1:]})!=10: raise ValueError('Pilot needs ten distinct prospect company domains')
    limits={'email':11,'gift':0,'social':0} if pilot else value.get('limits',{})
    if any(type(limits.get(k)) is not int or not 0<=counts[k]<=limits[k]<=100 for k in counts): raise ValueError('Set explicit positive bounded channel counts covering these exact actions')
    grant={'kind':'pilot' if pilot else 'scope','authority':authority,'purpose':value.get('purpose','ten-account workshop pilot'),
        'actions':actions,'limits':limits,'approved_at':now()}
    if pilot: grant.update(controlled_action_key=keys[0],prospect_action_keys=keys[1:])
    if counts['gift']:
        b=value.get('gift_budget',{})
        if (not __import__('re').fullmatch('[A-Z]{3}',str(b.get('currency',''))) or
                any(type(b.get(k)) not in (int,float) or b[k]<=0 for k in ('max_per_gift','max_total')) or b['max_per_gift']>b['max_total']):
            raise ValueError('Gift grant needs currency, positive max_per_gift and lifetime max_total')
        grant['gift_budget']=b
    grant_id='pilot' if pilot else digest(grant)
    if pilot and store.setting('pilot_approval'): raise ValueError('The pilot grant is already pinned. It cannot be replaced or reset across days')
    for key in keys:
        for row in store.rows("SELECT data_json FROM source_records WHERE source='owner.release'"):
            if key in load(row['data_json']).get('actions',{}): raise ValueError('This action is already assigned to an approved release')
    with store.db:
        store.record('owner.release',grant_id,'approved_release',grant)
        store.event('release_approved',grant_id,{'grant_digest':digest(grant)},key='release_approved:'+grant_id)
        if pilot: store.set('pilot_approval',{'record_key':grant_id,'digest':digest(grant)})
    return {'approved_grant':grant_id,'exact_actions':len(keys),'lifetime_limits':limits,'provider_writes':0}


def revoke_release(store, grant_id, reason):
    if not reason.strip() or not store.one("SELECT record_key FROM source_records WHERE source='owner.release' AND record_key=?",(grant_id,)):
        raise ValueError('Name an existing grant and actual owner revocation reason')
    with store.db:
        store.set('revoked_grant:'+grant_id,{'at':now(),'reason':reason})
        store.event('release_revoked',grant_id,{'reason':reason},key='release_revoked:'+grant_id)
    return {'revoked_grant':grant_id,'history_retained':True,'replacement_pilot_allowed':False,'provider_writes':0}


def snapshot(store, path, commit=True):
    path = private_file(path); value = json.loads(path.read_text())
    required = {'customers','open_deals','suppressions'}
    if value.get('complete') is not True or not required <= set(value.get('coverage',[])):
        raise ValueError('Owner snapshot must explicitly cover customers, open deals and opt-outs/relationships')
    if not value.get('source') or not fresh(value.get('observed_at'),65*60):
        raise ValueError('Use an actual owner-reviewed source with a timestamp from the last 65 minutes')
    records = value.get('records')
    if not isinstance(records,list): raise ValueError('Snapshot records must be a list. An empty list means explicitly verified no exclusions')
    parsed=[]
    for row in records:
        kind=row.get('entity_type'); canonical=email(row.get('value')) if kind=='email' else domain(row.get('value')) if kind=='domain' else ''
        if not canonical or not row.get('reason'): raise ValueError('Each exclusion needs entity_type, value and reason')
        parsed.append({**row,'value':canonical})
    receipt={'complete':True,'observed_at':value['observed_at'],'source':value['source'],'coverage':sorted(required),
        'records':len(parsed),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'method':'owner-reviewed local snapshot; not a native API inventory'}
    if commit:
        with store.db:
            # Prior exclusions remain until the owner separately reviews removal.
            for row in parsed:
                store.db.execute('INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?,?,?)',
                    (row['entity_type'],row['value'],row['reason'],'owner.snapshot',value['observed_at'],encode(row)))
            store.record('owner.snapshot','current','exclusion_inventory',receipt)
            store.set('exclusion_snapshot_path',str(path))
    return receipt


def scheduler_edit_binding(html, gate, capture_url):
    """Bind the observed scheduler edit page without inventing provider inputs."""
    statement='Your recipient will need to schedule a meeting to redeem their gift.'
    class Page(HTMLParser):
        def __init__(self):
            super().__init__(); self.nodes=[]; self.stack=[]
        def handle_starttag(self,tag,attrs):
            node={'tag':tag,'attrs':dict(attrs),'duplicate_attrs':len(attrs)!=len(dict(attrs)),
                'parent':self.stack[-1] if self.stack else None,'children':[],'order':len(self.nodes)}
            if node['parent'] is not None: node['parent']['children'].append(node)
            self.nodes.append(node)
            if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
                self.stack.append(node)
        def handle_startendtag(self,tag,attrs):
            self.handle_starttag(tag,attrs)
            if self.stack and self.stack[-1]['tag']==tag: self.stack.pop()
        def handle_endtag(self,tag):
            for index in range(len(self.stack)-1,-1,-1):
                if self.stack[index]['tag']==tag:
                    self.stack=self.stack[:index]; break
        def handle_data(self,text):
            if self.stack: self.stack[-1]['children'].append(text)
    page=Page(); page.feed(html); page.close()
    def ancestors(node):
        while node is not None:
            yield node; node=node['parent']
    def parent_class(node,name):
        return next((n for n in ancestors(node) if n['tag']=='div' and name in n['attrs'].get('class','').split()),None)
    def visible(node):
        for n in ancestors(node):
            a=n['attrs']; style=a.get('style','').lower(); classes=set(a.get('class','').lower().split())
            if (n['tag'] in {'head','script','style','template','noscript'} or 'hidden' in a or 'inert' in a
                    or a.get('aria-hidden','').strip().lower()=='true' or classes & {'hidden','hide','d-none','sr-only','visually-hidden'}
                    or re.search(r'(?:display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)|content-visibility\s*:\s*hidden|opacity\s*:\s*0(?:\s|;|$))',style)):
                return False
        return True
    def text(node):
        return ''.join(child if isinstance(child,str) else text(child) if visible(child) else '' for child in node['children'])
    url=urlparse(capture_url); route='/schedulers/'+str(gate['external_id'])
    if (not re.fullmatch(r'[A-Za-z0-9_-]+',str(gate['external_id'])) or url.path!=route+'/edit' or url.query or url.fragment
            or any(sum(n['tag']==tag for n in page.nodes)!=1 for tag in ('html','head','body'))):
        raise ValueError('scheduler-edit-v1 needs the complete actual scheduler edit page and exact capture route')
    forms=[n for n in page.nodes if n['tag']=='form' and re.fullmatch(r'edit_scheduler_[0-9]+',n['attrs'].get('id',''))]
    if len(forms)!=1 or forms[0]['attrs']['id']!='edit_scheduler_'+str(gate['numeric_id']) or not visible(forms[0]):
        raise ValueError('scheduler-edit-v1 needs exactly one visible matching numeric edit form')
    form=forms[0]; a=form['attrs']; action=urlparse(urljoin(capture_url,a.get('action','')))
    if (a.get('method','').lower()!='post' or a.get('target') not in (None,'','_self') or form['duplicate_attrs']
            or action.scheme!=url.scheme or action.hostname!=url.hostname or (action.port or 443)!=(url.port or 443)
            or action.username or action.password or action.path!=route or action.query or action.fragment):
        raise ValueError('scheduler-edit-v1 POST action must identify the same provider origin and scheduler')
    for field,key,kind in (('scheduler[name]','name','text'),('scheduler[url]','source','url')):
        fields=[n for n in page.nodes if n['tag']=='input' and n['attrs'].get('name')==field and next((p for p in ancestors(n) if p['tag']=='form'),None) is form]
        if (len(fields)!=1 or fields[0]['duplicate_attrs'] or fields[0]['attrs'].get('type','text').lower()!=kind
                or 'disabled' in fields[0]['attrs'] or any(n['tag']=='fieldset' and 'disabled' in n['attrs'] for n in ancestors(fields[0]))
                or not visible(fields[0]) or fields[0]['attrs'].get('value')!=gate[key]
                or fields[0]['attrs'].get('form') not in (None,a['id'])):
            raise ValueError('scheduler-edit-v1 needs unique enabled same-form scheduler name and URL matching native values')
    source=urlparse(gate['source'])
    if source.scheme!='https' or not source.hostname or source.username or source.password:
        raise ValueError('scheduler-edit-v1 native scheduler source must be its actual HTTPS URL')
    panel=parent_class(form,'panel'); body=parent_class(form,'panel-body')
    statements=[n for n in page.nodes if n['tag']=='p' and 'font-paragraph' in n['attrs'].get('class','').split()
        and visible(n) and ' '.join(text(n).split())==statement and parent_class(n,'panel') is panel
        and parent_class(n,'panel-title') is not None and parent_class(n,'panel-heading') is not None
        and body is not None and n['order']<body['order']]
    if panel is None or body is None or len(statements)!=1:
        raise ValueError('scheduler-edit-v1 needs the exact visible meeting requirement in this scheduler panel heading')
    return {'ui_contract':'scheduler-edit-v1','form_action':action.geturl(),'name_field':'scheduler[name]',
        'source_field':'scheduler[url]','meeting_required_text':statement,'meeting_required_source':'same_panel_visible_provider_statement'}


def import_records(store, kind, path):
    if kind=='exclusions': return snapshot(store,path)
    if kind=='gift-gate':
        value=read_json(path); html=private_file(value['form_html_file']).read_text()
        gate={k:value.get(k) for k in ('external_id','numeric_id','name','source')}
        if (type(gate['numeric_id']) is not int or gate['numeric_id']<=0 or not all(isinstance(gate[k],str) and gate[k].strip() for k in ('external_id','name','source')) or value.get('meeting_required') is not True
                or 'edit_scheduler_'+str(gate['numeric_id']) not in html or gate['external_id'] not in html):
            raise ValueError('Use the actual owned scheduler form HTML with its external ID and numeric edit_scheduler_ID')
        url=urlparse(value.get('capture_url','')); host=url.hostname or ''
        if (url.scheme!='https' or url.port not in (None,443) or not (host=='loopandtie.com' or host.endswith('.loopandtie.com')) or url.username or url.password
                or value.get('provider')!='loop_and_tie' or value.get('team_id')!=store.setting('loop_and_tie_team') or not fresh(value.get('captured_at'),65*60)):
            raise ValueError('Use fresh authenticated owned Loop & Tie UI capture URL, provider, team and actual capture timestamp')
        if value.get('ui_contract')=='scheduler-edit-v1':
            gate.update(scheduler_edit_binding(html,gate,value['capture_url']))
        elif value.get('ui_contract') in (None,'','input-fields-v1'):
            class GateForm(HTMLParser):
                inside=False; required=False; external=False; forms=0
                def handle_starttag(self,tag,attrs):
                    attributes=dict(attrs)
                    if tag=='form':
                        self.inside=attributes.get('id')=='edit_scheduler_'+str(gate['numeric_id'])
                        if self.inside: self.forms+=1
                    if self.inside and tag=='input' and value.get('external_id_field') and attributes.get('name')==value['external_id_field']:
                        self.external=attributes.get('value')==gate['external_id']
                    if self.inside and tag=='input' and value.get('meeting_required_field') and attributes.get('name')==value['meeting_required_field']:
                        self.required=('disabled' not in attributes and ('checked' in attributes if attributes.get('type')=='checkbox' else attributes.get('value') in ('true','1')))
                def handle_endtag(self,tag):
                    if tag=='form': self.inside=False
            form=GateForm(); form.feed(html)
            if form.forms!=1 or not form.required or not form.external: raise ValueError('Exact same numeric form must contain external_id_field with its native value and enabled meeting_required_field')
            gate.update({k:value[k] for k in ('meeting_required_field','external_id_field')})
        else:
            raise ValueError('Unknown gift scheduler UI contract')
        from engine.channels.gifts import Gifts
        native=Gifts(store).catalogue(); matches=[s for s in native['schedulers'] if s.get('id')==gate['external_id']]
        if (str(native.get('team',{}).get('id'))!=store.setting('loop_and_tie_team') or not fresh(native.get('at'),65*60)
                or len(matches)!=1 or any(matches[0].get('attributes',{}).get(k)!=gate[v] for k,v in (('external-id','external_id'),('name','name'),('source','source')))):
            raise ValueError('Authenticated owned native scheduler differs from captured form')
        gate['form_id']='edit_scheduler_'+str(gate['numeric_id']); gate['meeting_required']=True
        gate.update({k:value[k] for k in ('capture_url','captured_at','provider','team_id')})
        gate['native_catalogue_digest']=digest(native)
        gate['evidence_sha256']=hashlib.sha256(html.encode()).hexdigest(); gate['observed_at']=value['captured_at']
        with store.db:
            store.record('live.loopandtie.scheduler_catalogue',gate['external_id'],'owned_scheduler_catalogue',native)
            store.record('owner.gift_scheduler',gate['external_id'],'native_ui_binding',gate)
            store.set('gift_gate',{**gate,'binding_source':'owner.gift_scheduler','binding_key':gate['external_id'],'binding_digest':digest(gate)})
        return {'gift_gate_saved':True,'numeric_id':gate['numeric_id'],'provider_writes':0}
    rows=read_records(path)
    if not isinstance(rows,list) or not rows: raise ValueError('Import a nonempty list of actual records')
    count=0; outcomes=[]; source='owner.import.'+kind; stamp=now()
    with store.db:
        for row in rows:
            if not isinstance(row,dict): raise ValueError('Each record must be an object')
            if kind=='accounts':
                d=domain(row.get('domain'))
                if not d or not row.get('name') or not row.get('country'):
                    raise ValueError('Account fields: domain, name, country; optional fit and source_url')
                row = {**row, 'country_input': row['country'], 'country': country(row['country'])}
                store.db.execute('INSERT OR REPLACE INTO accounts VALUES (?,?,?,?,?,?,?)',
                    (d,row['name'],'catalog',row.get('fit'),source,stamp,encode(row)))
                store.record(source,d,'account',row)
                outcomes.append({'domain':d,'country':row['country'],'country_input':row['country_input']})
            elif kind=='people':
                d=domain(row.get('domain')); recipient=email(row.get('email'))
                if not d or not recipient or not row.get('name') or not row.get('title'):
                    raise ValueError('Person fields: domain,email,name,title,identity,email_verification; optional profile and controlled_test')
                if not store.one('SELECT domain FROM accounts WHERE domain=?',(d,)): raise ValueError('Import this account first')
                identity=load(row.get('identity')); verification=load(row.get('email_verification'))
                if not identity or not verification:
                    raise ValueError('Retain actual employment source evidence and email validation receipt')
                key='person:'+recipient; person={**row,'profile':profile(row.get('profile'))}
                store.db.execute('INSERT OR REPLACE INTO people VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (key,recipient,person['profile'],d,row['name'],row['title'],'catalog',source,stamp,encode(person)))
                store.record(source,key,'person',person)
            elif kind=='actions':
                from engine.scheduler import prepare
                recipient=email(row.get('recipient')); person=store.one('SELECT * FROM people WHERE email=?',(recipient,))
                if not person: raise ValueError('Import the actual verified person before preparing an action')
                channel=row.get('channel'); payload=row.get('payload'); sender=row.get('sender','')
                if channel not in ('email','gift','linkedin','linkedin_message') or not isinstance(payload,dict):
                    raise ValueError('Action fields: channel,recipient,sender,payload')
                if channel=='email' and payload.get('sender') != sender: raise ValueError('Payload sender differs from action sender')
                provenance=None
                if channel in ('linkedin','linkedin_message'):
                    from engine.channels.social import Social
                    provenance=Social(store).provisioning(person,payload)
                result=prepare(store,channel,person,payload,sender); outcomes.append(result)
                if channel in ('linkedin','linkedin_message') and payload.get('contact_id'):
                    ownership=store.setting('social_prepared',{})
                    ownership[str(payload['contact_id'])]={'action_key':result['action_key'],'payload':payload,'provisioning':provenance}
                    store.set('social_prepared',ownership)
            else: raise ValueError('Unsupported import kind')
            count+=1
    return {'imported':count,'kind':kind,'actions':outcomes if kind=='actions' else [],
        'countries':outcomes if kind=='accounts' else [],'provider_writes':0}


def refresh_portable(store):
    from engine.checks import SAFETY
    from engine.channels.email import Replies
    from engine.channels.meetings import Meetings
    from engine.validation import account_domains
    rows=store.rows("SELECT * FROM actions WHERE status IN ('ready','held')")
    domains=sorted({d for row in rows for d in account_domains(store,row['domain'])})
    if not domains: return {'refreshed':[],'failures':{},'reason':'Prepare exact actions first'}
    calls={}; failures={}; meetings=Meetings(store); mode=store.setting('exclusion_mode','snapshot')
    native=store.setting('native_exclusions',[])
    if mode not in ('snapshot','native'): raise ValueError('Choose explicit snapshot or native exclusion mode')
    if mode=='snapshot':
        try: calls['snapshot']=snapshot(store,store.setting('exclusion_snapshot_path'))
        except Exception as exc: failures['snapshot']=str(exc)
    elif 'revenue' not in native or not set(native)&{'salesforce','hubspot'}:
        failures['native_scope']='Native mode needs actual current revenue and at least one configured CRM inventory'
    configured=store.setting('history_sources',{}); configured['domains']=[] if mode=='native' else domains
    if mode=='native' and configured.get('gmail_start',0)!=0:
        failures['native_scope']='Native mode requires complete mailbox history from epoch 0; an old opt-out cannot be omitted'
    if mode=='native':
        sheet=store.setting('revenue',{}).get('range','')
        if not __import__('re').fullmatch(r"(?:'[^']+'|[^!]+)![A-Z]+:[A-Z]+",sheet):
            failures['native_scope']='Native customer inventory must read all rows in the owned canonical sheet columns, such as Customers!A:C'
    with store.db: store.set('history_sources',configured)
    for key,call in (('bookings',meetings.refresh),('history',Replies(store).refresh)):
        try:
            calls[key]=call()
            if calls[key].get('complete') is not True: failures[key]=calls[key].get('failures') or calls[key].get('reason')
        except Exception as exc: failures[key]=type(exc).__name__
    for key in native:
        call={'salesforce':meetings.salesforce_deals,'hubspot':meetings.hubspot_deals,'revenue':meetings.customers}.get(key)
        if not call: failures[key]='Unknown native exclusion source'; continue
        try:
            calls[key]=call()
            if calls[key].get('complete_inventory') is not True: failures[key]='Native inventory incomplete'
            if mode=='native' and (calls[key].get('unresolved_domain_ids') or calls[key].get('unresolved_domain_rows')):
                failures[key]='Native inventory contains unresolved company identities. Resolve them before unattended operation'
        except Exception as exc: failures[key]=type(exc).__name__
    proofs={}; dependencies={'customers':['snapshot'],'open_deals':['snapshot'],
        'suppressions':['snapshot','history'],'bookings':['bookings'],'history':['history']}
    if mode=='native':
        dependencies={'customers':['revenue'],'open_deals':[k for k in native if k in ('salesforce','hubspot')],
            'suppressions':list(native)+['history'],'bookings':['bookings'],'history':['history']}
        if 'native_scope' in failures:
            for key in ('customers','open_deals','suppressions'): dependencies[key].append('native_scope')
    else:
        for key in ('customers','open_deals','suppressions'): dependencies[key]+=native
    with store.db:
        for name,required in dependencies.items():
            if any(key not in calls or key in failures for key in required): continue
            stamp=min(calls[key]['observed_at'] for key in required)
            if not fresh(stamp,SAFETY[name]): failures[name]='Actual source read is too old'; continue
            value={'coverage':name,'complete':True,'observed_at':stamp,'domain_scope':domains,
                'dependencies':{key:calls[key] for key in required},'coverage_note':'Your configured sources and owner snapshot only'}
            store.record('attendee.batch_checks',name,'safety_coverage',value)
            proofs[name]={'complete':True,'observed_at':stamp,'source':'attendee.batch_checks','record_key':name,'digest':digest(value)}
        store.set('safety_refresh',{'sources':proofs,'domain_scope':domains})
        store.event('batch_checked',','.join(domains),{'checked':list(proofs),'failures':failures})
    from engine.checks import recheck_actions
    return {'refreshed':list(proofs),'domain_scope':domains,'exclusion_mode':mode,'failures':failures,'rechecked':recheck_actions(store)}


def setup_google(store, client_file, timeout=180):
    client=read_json(credential_path(client_file)).get('installed')
    if not client or not all(client.get(k) for k in ('client_id','client_secret')):
        raise ValueError('Use your own Google desktop OAuth client JSON')
    state=secrets.token_urlsafe(32); callback={}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query=parse_qs(urlparse(self.path).query)
            if query.get('state') != [state]: self.send_error(400); return
            callback.update({k:v[0] for k,v in query.items()})
            self.send_response(200); self.end_headers(); self.wfile.write(b'Google connected. Return to your workshop terminal.')
        def log_message(self,*args): pass
    server=HTTPServer(('127.0.0.1',0),Handler); server.timeout=1
    redirect='http://127.0.0.1:'+str(server.server_port)+'/'
    scopes=['https://www.googleapis.com/auth/gmail.modify','https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/spreadsheets.readonly']
    auth='https://accounts.google.com/o/oauth2/v2/auth?'+urlencode({'client_id':client['client_id'],
        'redirect_uri':redirect,'response_type':'code','scope':' '.join(scopes),'access_type':'offline','prompt':'consent','state':state})
    print('Open this Google consent URL in your browser:\n'+auth,flush=True); webbrowser.open(auth)
    deadline=time.time()+timeout
    try:
        while not callback and time.time()<deadline: server.handle_request()
    finally: server.server_close()
    if not callback.get('code'): raise ValueError('Google consent did not finish. No credentials were saved')
    http=HttpClient(store)
    token=http.request('POST','https://oauth2.googleapis.com/token',headers={'Content-Type':'application/x-www-form-urlencoded'},
        data=urlencode({'code':callback['code'],'client_id':client['client_id'],'client_secret':client['client_secret'],
            'redirect_uri':redirect,'grant_type':'authorization_code'}).encode()).require()
    if not token.get('refresh_token'): raise ProviderError('Google did not return a refresh token; request offline consent')
    account=http.request('GET','https://gmail.googleapis.com/gmail/v1/users/me/profile',
        headers={'Authorization':'Bearer '+token['access_token']}).require()
    mailbox=email(account.get('emailAddress'))
    if mailbox not in store.setting('policy',{}).get('senders',{}): raise ValueError('Google account is not an authorized sender in your config')
    saved={'type':'authorized_user','email':mailbox,'client_id':client['client_id'],'client_secret':client['client_secret'],
        'refresh_token':token['refresh_token'],'scopes':token.get('scope',' '.join(scopes)).split()}
    folder=Path.home()/'.local/share/agentic-gtm/credentials'; folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    path=folder/(mailbox.replace('@','_')+'.json'); path.write_text(json.dumps(saved,indent=2)); path.chmod(0o600)
    with store.db:
        paths=store.setting('credential_files',{}); paths['google']=str(path); paths['google:'+mailbox]=str(path); store.set('credential_files',paths)
    config_path=private_file(store.setting('private_config_path'))
    config=json.loads(config_path.read_text()); config['credential_files']={**config.get('credential_files',{}),**paths}
    config_path.write_text(json.dumps(config,indent=2)+'\n'); config_path.chmod(0o600)
    return {'connected_mailbox':mailbox,'credential_file':str(path),'credential_values_printed':False,'outreach_sent':0}


def readiness(store):
    authority=store.setting('policy',{}); paths=store.setting('credential_files',{})
    issues=[]
    folder=ROOT.parent/'company-motion'
    missing=[name for name in ('COMPANY.md','AUTHORITY.md','AGENTS.md') if not (folder/name).is_file() or not (folder/name).read_text().strip()]
    if missing: issues.append('Missing workshop files: '+', '.join(missing)+'. Run bootstrap after saving COMPANY.md')
    if not store.setting('portable_initialized'): issues.append('Run init with your private config')
    if not paths.get('google') or not Path(paths['google']).is_file(): issues.append('Connect your Google mailbox')
    if store.setting('exclusion_mode','snapshot')=='snapshot':
        try: snapshot(store,store.setting('exclusion_snapshot_path'),commit=False)
        except Exception: issues.append('Import your current complete exclusions snapshot')
    if not authority.get('authority'): issues.append('Write owner authority')
    return {'local_setup_ready':not issues,'issues':issues,
        'recipient_company_countries':[country(v) for v in authority.get('recipient_company_countries',[])],
        'repair_command':'python3 -B gtm.py bootstrap --company-brief ../company-motion/COMPANY.md',
        'provider_connections_verified':False,
        'next':'Run refresh after importing exact actions. Read every held reason','provider_writes':0}


def results(store):
    from engine.checks import exact_email_sent
    proof=store.setting('pilot_approval',{})
    record=store.one("SELECT data_json,digest FROM source_records WHERE source='owner.release' AND record_key=?",(proof.get('record_key',''),))
    grant=load(record['data_json']) if record else {}
    if not record or digest(grant)!=record['digest'] or record['digest']!=proof.get('digest'):
        return {'prospect_pilot_complete':False,'reason':'No unchanged exact pilot approval','provider_writes':0}
    pilot=[]; controlled=[]; attempts=[]
    for key,pinned in grant['actions'].items():
        row=store.one('SELECT * FROM attempts WHERE idem_key=?',(key,))
        if row:
            attempts.append(row); (controlled if pinned['controlled_test'] else pilot).append(row)
    sent=[row for row in pilot if exact_email_sent(store,row['idem_key'])]
    canary=sum(exact_email_sent(store,r['idem_key']) for r in controlled)
    distinct=sorted({r['domain'] for r in sent})
    return {'approved_exact_keys':list(grant['actions']),'lifetime_limit':11,'attempt_states':[{'key':r['idem_key'],'status':r['status']} for r in attempts],
        'prospect_email_exact_sent':len(sent),'controlled_test_exact_sent':canary,
        'prospect_exact_sent_accounts':len(distinct),'prospect_pilot_complete':len(distinct)==10 and canary==1,
        'all_email_attempts':[{'key':r['idem_key'],'recipient':r['recipient'],'domain':r['domain'],'status':r['status'],
            'provider_id':r['provider_id'],'controlled_test':r in controlled,'receipt':load(r['receipt_json'])} for r in pilot+controlled],
        'held_actions':[r for r in store.rows("SELECT action_key,channel,recipient,domain,status,reason FROM actions WHERE status='held'") if r['action_key'] in grant['actions']],
        'exact_sent_receipts':[{'key':r['idem_key'],'recipient':r['recipient'],
            'status':r['status'],'provider_id':r['provider_id'],'receipt':load(r['receipt_json'])} for r in sent],
        'note':'Sent confirms Gmail records. Delivery, reply, booked and attended are separate outcomes'}


def research(store, operation, path=None):
    from engine.research import Research,Signals
    inputs=read_json(path) if path else {}; client=Research(store)
    if operation=='exa': return client.exa(inputs)
    if operation in ('sixtyfour-search','sixtyfour-email'): return client.sixtyfour('search' if operation.endswith('search') else 'find_email',inputs)
    if operation=='validate-email':
        receipt=client.validate_email(inputs['email']); recipient=email(inputs['email'])
        with store.db:
            for row in store.rows('SELECT person_key,data_json FROM people WHERE email=?',(recipient,)):
                data=load(row['data_json']); data['email_verification']={'email':recipient,'status':receipt.get('native_status') or receipt.get('body',{}).get('status','unknown'),
                    'provider':'zerobounce','checked_at':receipt['at'],'request_key':receipt.get('request_key')}
                store.db.execute('UPDATE people SET data_json=? WHERE person_key=?',(encode(data),row['person_key']))
        return receipt
    if operation=='zerobounce-balance': return client.validation_balance()
    if operation=='apify-start': return client.apify_start(inputs['actor'],inputs['input'])
    if operation=='apify-read': return client.apify_read(inputs['run_id'])
    if operation=='triguna-profile': return client.profile(inputs['profile_id'])
    if operation=='triguna-company': return client.company(inputs['company_id'])
    if operation=='rocketreach': return client.rocketreach(inputs)
    if operation=='moltsets': return client.moltsets(inputs['operation'],inputs['inputs'])
    if operation=='instantly-email': return client.instantly_email(inputs['person'],inputs['provider_id'],inputs.get('company'))
    if operation=='radar-start': return Signals(store).start_scan(inputs['kind'],inputs['values'])
    if operation=='radar-read': return Signals(store).read_scan(inputs['run_id'])
    raise ValueError('Unsupported research operation')
