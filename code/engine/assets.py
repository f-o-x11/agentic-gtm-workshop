"""External hosted assets and Metadata native creative receipts, without bundled media."""
import hashlib
import json
import re
import uuid
import io
from pathlib import Path
import zipfile
from urllib.parse import urlparse

from engine.http_client import HttpClient, ProviderError, require_enabled, rpc_result
from engine.database import digest, encode, now

MCP = "https://mcp-server.metadata.io/mcp"


class Assets:
    def __init__(self, store, http=None):
        self.store, self.http = store, http or HttpClient(store)

    def inspect(self, resource_key):
        resource = self.store.one("SELECT * FROM resources WHERE resource_key=?", (resource_key,))
        if not resource:
            raise ValueError("Existing hosted resource missing")
        data = json.loads(resource["data_json"])
        url = resource["url"]
        p = urlparse(url or "")
        allowed = set(self.store.setting("asset_hosts", []))
        if p.scheme != "https" or p.hostname not in allowed or p.username or p.password:
            raise ValueError("Hosted asset destination is not owned or verified")
        expected = data.get("sha256") or data.get("content_sha256") or data.get("index_sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            return {"status": "unverified", "reason": "Source content hash is absent", "url": url}
        response = self.http.request("GET", url, headers={"Cache-Control": "no-cache", "Accept": "*/*"})
        response.require()
        actual = hashlib.sha256(response.raw).hexdigest()
        receipt = {"at": now(), "url": url, "http_status": response.status, "sha256": actual,
            "status": "bytes_verified" if actual == expected else "content_changed", "browser_acceptance": False}
        with self.store.db:
            self.store.record("asset.readback", resource_key, resource["kind"], receipt)
        return receipt

    def form_contract(self):
        config = self.store.setting('form_contract', {})
        if not all(config.get(k) for k in ('source_url','form_id','portal_id')):
            raise ValueError('Configure your actual website form source URL, portal and form ID')
        source, form_id, portal = config['source_url'], config['form_id'], str(config['portal_id'])
        script = self.http.request("GET", source, headers={"Accept": "*/*"})
        script.require()
        if form_id not in script.raw.decode() or portal not in script.raw.decode():
            raise ProviderError("Current website form identity differs")
        response = self.http.request("GET", "https://forms.hsforms.com/embed/v3/form/" + portal + "/" + form_id,
            params={"callback": "formCheck"}, headers={"Accept": "*/*"})
        response.require()
        text = response.raw.decode().removeprefix("formCheck(").removesuffix(";").removesuffix(")")
        form = json.loads(text)["form"]
        fields = {f["name"] for g in form.get("formFieldGroups", []) for f in g.get("fields", [])}
        if str(form.get("portalId")) != portal or form.get("guid") != form_id or not {"email", "firstname", "lastname", "company"} <= fields:
            raise ProviderError("Actual HubSpot form contract differs")
        receipt = {"at": now(), "portal_id": portal, "form_id": form_id, "source_url": source,
            "source_sha256": hashlib.sha256(script.raw).hexdigest(), "fields": sorted(fields), "browser_submission_verified": False}
        with self.store.db:
            self.store.record("asset.form", form_id, "native_form", receipt)
        return receipt

    def _tool(self, name, arguments):
        request_id = uuid.uuid4().hex
        response = self.http.request("POST", MCP, headers={"Authorization": self.http.credential("metadata"), "Accept": "application/json, text/event-stream"},
            json_body={"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, timeout=600)
        result = rpc_result(response, request_id)
        return result, {"request_id": request_id, **response.receipt()}

    def account(self):
        result, receipt = self._tool("get_account_details", {})
        text = [json.loads(c["text"]) for c in result.get("content", []) if c.get("type") == "text"]
        def find(value):
            if isinstance(value, dict):
                if value.get("accountId") is not None:
                    return value["accountId"]
                for v in value.values():
                    found = find(v)
                    if found is not None:
                        return found
            if isinstance(value, list):
                for v in value:
                    found = find(v)
                    if found is not None:
                        return found
            return None
        account_id = find(text)
        expected = self.store.setting("metadata_account_id")
        if expected is None or str(account_id) != str(expected):
            raise ProviderError("Actual Metadata creative account differs or is not configured")
        return {"account_id": account_id, "receipt": receipt}

    def generate(self, operation, arguments):
        require_enabled(self.store)
        if operation not in ("generate_brand_kit", "generate_brand_creative", "edit_brand_creative"):
            raise ValueError("Unsupported Metadata creative operation")
        domain = arguments.get("domain")
        if not isinstance(domain, str) or not self.store.one("SELECT domain FROM accounts WHERE domain=?", (domain,)):
            raise ValueError("Exact current account required")
        if operation == "generate_brand_kit" and arguments != {"domain": domain, "force_regenerate": False}:
            raise ValueError("Exact existing brand kit contract required")
        owner = self.account()
        fingerprint = digest([operation, arguments, owner["account_id"]])
        previous = self.store.one("SELECT * FROM attempts WHERE idem_key=?", (fingerprint,))
        if previous:
            if previous["status"] == "complete":
                return json.loads(previous["receipt_json"])
            raise ValueError("Existing creative request uncertain, never render again automatically")
        self.store.reserve("research:metadata", fingerprint, domain, "", {"operation": operation, "arguments": arguments, "account_id": owner["account_id"]}, fingerprint)
        try:
            require_enabled(self.store)
            result, receipt = self._tool(operation, arguments)
            value = {"status": "generated_pending_review", "domain": domain, "account_id": owner["account_id"], "result": result, "receipt": receipt,
                "visual_review_verified": False, "published": False}
            self.store.result(fingerprint, "complete", receipt=value)
            return value
        except Exception as exc:
            self.store.result(fingerprint, "uncertain", receipt={"error": type(exc).__name__})
            raise

    def publish(self, resource_key):
        return {"status": "unavailable", "reason": "Standalone page upload and desktop/mobile form acceptance are not wired", "resource_key": resource_key}

    def publish_file(self, path, approved_sha256=None, review=False):
        """Publish one reviewed HTML file to the attendee's verified owned Netlify site."""
        from engine.database import ROOT
        path = Path(path).expanduser().resolve()
        if ROOT in path.parents: raise ValueError('Keep page output outside the 20 file runtime')
        content = path.read_bytes(); expected = hashlib.sha256(content).hexdigest()
        if path.suffix.lower() != '.html': raise ValueError('Review one exact HTML file')
        site_id = self.store.setting('netlify_site_id')
        if not isinstance(site_id,str) or not re.fullmatch(r'[A-Za-z0-9-]+',site_id):
            raise ValueError('Your owned Netlify site ID is required')
        headers={'Authorization':'Bearer '+self.http.credential('netlify')}
        base='https://api.netlify.com/api/v1'
        owner=self.http.request('GET',base+'/user',headers=headers).require()
        site=self.http.request('GET',base+'/sites/'+site_id,headers=headers).require()
        if (site.get('id') != site_id or not owner.get('id') or site.get('user_id') != owner['id']
                or self.store.setting('netlify_owner_id',owner['id']) != owner['id']):
            raise ProviderError('Netlify site is not owned by the authenticated participant')
        packet={'site_id':site_id,'owner_id':owner['id'],'sha256':expected,'filename':'index.html'}
        approved=digest(packet)
        if review: return {**packet,'approval_sha256':approved,'provider_write':False}
        if approved_sha256!=approved: raise ValueError('Approve this exact site, owner and HTML SHA256 with publish-review')
        fingerprint=digest(['netlify',site_id,expected]); key='page:'+fingerprint
        prior=self.store.one('SELECT * FROM attempts WHERE idem_key=?',(fingerprint,))
        deploy_id=prior['provider_id'] if prior else None
        if prior and prior['status']=='complete': return json.loads(prior['receipt_json'])
        if prior and not deploy_id: raise ValueError('Page submission is uncertain. Reconcile in Netlify before another upload')
        if not prior:
            require_enabled(self.store)
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive: archive.writestr('index.html',content)
            payload={**packet,'approved_sha256':approved_sha256}
            self.store.reserve('asset:netlify',fingerprint,self.store.setting('company',{}).get('domain',''),'',payload,fingerprint)
            try:
                require_enabled(self.store)
                response=self.http.request('POST',base+'/sites/'+site_id+'/deploys',
                    headers={**headers,'Content-Type':'application/zip'},data=buffer.getvalue(),timeout=120)
                native=response.require((200,201,202)); deploy_id=native.get('id')
                if not deploy_id or native.get('site_id') != site_id: raise ProviderError('Exact Netlify deployment identity missing')
                self.store.result(fingerprint,'accepted',str(deploy_id),response.receipt())
            except Exception as exc:
                self.store.result(fingerprint,'uncertain',receipt={'error':type(exc).__name__,'retry_allowed':False})
                raise
        native=self.http.request('GET',base+'/deploys/'+str(deploy_id),headers=headers).require()
        if native.get('id') != deploy_id or native.get('site_id') != site_id:
            raise ProviderError('Deployment readback identity differs')
        if native.get('state') != 'ready':
            return {'status':'accepted_pending_host','deploy_id':deploy_id,'retry_allowed':False}
        url=native.get('deploy_ssl_url') or native.get('ssl_url')
        parsed=urlparse(url or '')
        if parsed.scheme!='https' or not (parsed.hostname or '').endswith('.netlify.app'):
            raise ProviderError('Exact hosted deployment HTTPS URL unavailable')
        response=self.http.request('GET',url,headers={'Accept':'text/html','Cache-Control':'no-cache'})
        response.require(); actual=hashlib.sha256(response.raw).hexdigest()
        if actual!=expected:
            self.store.result(fingerprint,'uncertain',str(deploy_id),{'actual_sha256':actual,'expected_sha256':expected,'retry_allowed':False})
            raise ProviderError('Hosted page bytes differ. Inspect this deployment; do not upload again')
        receipt={'status':'bytes_verified','at':now(),'url':url,'deploy_id':deploy_id,'site_id':site_id,
            'sha256':actual,'browser_acceptance':False,'form_submission_verified':False,'published':True}
        with self.store.db:
            self.store.db.execute('INSERT OR REPLACE INTO resources VALUES (?,?,?,?,?,?)',
                (key,'account_page','netlify',deploy_id,url,encode(receipt)))
            hosts=set(self.store.setting('asset_hosts',[])); hosts.add(parsed.hostname); self.store.set('asset_hosts',sorted(hosts))
        self.store.result(fingerprint,'complete',str(deploy_id),receipt)
        return receipt

    def advertising(self, operation, arguments, approved_sha256=None, review=False):
        """Call a published Metadata tool for the participant's verified account."""
        reads={'get_account_details','get_integrations_status','search_campaigns_by_names',
            'search_ads_by_names','get_budget_group','check_campaign_launch_readiness'}
        writes={'upload_account_list_csv_audience','create_budget_group','create_campaign',
            'create_update_offer','launch_campaign','manage_campaign'}
        if operation not in reads|writes or not isinstance(arguments,dict):
            raise ValueError('Unsupported advertising operation or argument object')
        owner=self.account(); packet={'operation':operation,'arguments':arguments,'account_id':owner['account_id']}
        pause=operation=='manage_campaign' and arguments.get('action')=='pause'
        if pause:
            prior_pauses=[r for r in self.store.rows("SELECT * FROM attempts WHERE channel='asset:metadata'")
                if json.loads(r['payload_json']).get('operation')=='manage_campaign' and
                    json.loads(r['payload_json']).get('arguments')==arguments]
            if any(r['status']!='complete' for r in prior_pauses): raise ValueError('Previous campaign pause outcome is uncertain. Read its provider state before another request')
            packet['approval_round']=len(prior_pauses)
        exact=digest(packet)
        if operation in reads:
            result,receipt=self._tool(operation,arguments)
            with self.store.db: self.store.record('metadata.read',exact,operation,{'packet':packet,'result':result,'receipt':receipt})
            return {'operation':operation,'result':result,'receipt':receipt,'provider_write':False}
        authority=self.store.setting('policy',{}).get('advertising',{})
        pause=operation=='manage_campaign' and arguments.get('action')=='pause'
        if not pause and authority.get('enabled') is not True:
            raise ValueError('Advertising writes need your separate advertising authority')
        if operation in ('launch_campaign','manage_campaign'):
            campaign_id=arguments.get('campaign_id')
            if type(campaign_id) is not int or campaign_id not in authority.get('authorized_campaign_ids',[]):
                raise ValueError('Authorize this exact campaign ID in your private advertising policy')
            if operation=='manage_campaign' and arguments.get('action') not in ('pause','restart'):
                raise ValueError('Campaign action must be pause or restart')
            if not pause:
                raise ValueError('Campaign launch and restart remain disabled until existing campaign budgets and readiness contracts are verified. Use the owned Metadata UI after exact budget review')
        if operation=='create_budget_group':
            data=arguments.get('data',{})
            cap=authority.get('max_total_budget',0)
            if not cap or type(data.get('monthlyCap')) not in (int,float) or not 0<data['monthlyCap']<=cap:
                raise ValueError('Budget group exceeds your authorized total budget')
            if data.get('totalBudget') is not None and (type(data['totalBudget']) not in (int,float) or not 0<data['totalBudget']<=cap):
                raise ValueError('Budget group totalBudget exceeds your authorized total budget')
            if data.get('autoApplyBudget') is not False or data.get('autopauseMonthlyCap') is not True:
                raise ValueError('Require explicit budget application and native monthly-cap pause')
        if operation=='create_campaign':
            data=arguments.get('campaign_data',{})
            allowed={'budgetGroup','campaignType','endDate','startDate','name','linkedin','facebook'}
            if not isinstance(data,dict) or set(data)-allowed:
                raise ValueError('Unsupported draft channel or field. Only LinkedIn and Facebook have verified budget guards')
            if not data.get('name') or not data.get('budgetGroup'):
                raise ValueError('Campaign needs an exact name and owned budget group')
            for channel in ('linkedin','facebook'):
                settings=data.get(channel,{})
                daily=settings.get('dailyBudget') if isinstance(settings,dict) else None
                if settings and (type(daily) not in (int,float) or not 0<daily<=authority.get('max_daily_budget',0)):
                    raise ValueError('Every campaign channel needs an explicit approved daily budget')
        if review:
            return {**packet,'approval_sha256':exact,'provider_write':False,
                'note':'Review the exact account, budget, audience, copy and provider readiness before approving this hash'}
        if approved_sha256!=exact:
            raise ValueError('Use ads-review, then approve the exact operation SHA256')
        previous=self.store.one('SELECT * FROM attempts WHERE idem_key=?',(exact,))
        if previous:
            if previous['status']=='complete': return json.loads(previous['receipt_json'])
            raise ValueError('Advertising outcome is uncertain. Read the existing provider object before another request')
        if operation in ('launch_campaign','manage_campaign') and not pause:
            proof_key=digest({'operation':'check_campaign_launch_readiness','arguments':{'campaign_id':arguments['campaign_id']},'account_id':owner['account_id']})
            proof=self.store.one("SELECT data_json,digest FROM source_records WHERE source='metadata.read' AND record_key=?",(proof_key,))
            from engine.validation import fresh
            raw=json.loads(proof['data_json']) if proof else {}
            if not proof or digest(raw)!=proof['digest'] or not fresh(raw.get('receipt',{}).get('at'),300):
                raise ValueError('Read this exact campaign launch readiness within the last 5 minutes and inspect the native result')
            def verdicts(value):
                found=[]
                if isinstance(value,dict):
                    for key,item in value.items():
                        if key in ('ready','isReady','canLaunch','isReadyToLaunch') and type(item) is bool: found.append(item)
                        else: found.extend(verdicts(item))
                elif isinstance(value,list):
                    for item in value: found.extend(verdicts(item))
                elif isinstance(value,str):
                    try: found.extend(verdicts(json.loads(value)))
                    except ValueError: pass
                return found
            native_verdicts=verdicts(raw.get('result'))
            if not native_verdicts or not all(native_verdicts):
                raise ValueError('Native readiness did not expose a confirmed positive launch verdict. Inspect or adapt the verified response schema before launch')
        if not pause: require_enabled(self.store)
        self.store.reserve('asset:metadata',exact,'','',packet,exact)
        try:
            if not pause: require_enabled(self.store)
            result,receipt=self._tool(operation,arguments)
            value={'status':'provider_response_pending_review','operation':operation,'account_id':owner['account_id'],
                'result':result,'receipt':receipt,'campaign_running_verified':False,
                'note':'Provider response is retained. Read the named campaign and confirm its actual status; queued launch may execute later'}
            self.store.result(exact,'complete',receipt=value)
            return value
        except Exception as exc:
            self.store.result(exact,'uncertain',receipt={'error':type(exc).__name__,'retry_allowed':False})
            raise


def inspect(store, resource_key, http=None):
    return Assets(store, http).inspect(resource_key)
