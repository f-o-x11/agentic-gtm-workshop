"""Gojiberry native tools and exact provider delivery, with no browser fallback."""
import json
import uuid
from datetime import datetime
from urllib.parse import quote, urlparse

from engine.http_client import HttpClient, ProviderError, outreach_action, recheck, require_enabled, rpc_result
from engine.database import now, digest

MCP = "https://mcp.gojiberry.ai"
REST = "https://ext.gojiberry.ai/v1"
READ_TOOLS = {"list_campaigns", "get_campaign", "get_list", "list_lists", "list_contacts", "get_contact", "get_campaign_logs", "get_unibox_for_contact"}


def profile(value):
    p = urlparse(value or "")
    if p.scheme != "https" or p.hostname not in ("linkedin.com", "www.linkedin.com") or not p.path.startswith("/in/") or len(p.path.strip("/").split("/")) != 2:
        raise ValueError("Exact LinkedIn person profile required")
    return "https://www.linkedin.com" + p.path.rstrip("/").lower()


class Social:
    def __init__(self, store, http=None):
        self.store, self.http = store, http or HttpClient(store)
        self.session_id = None
        self.initialized = False

    def headers(self):
        headers = {"Authorization": "Bearer " + self.http.credential("gojiberry"), "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        return headers

    def _rpc(self, method, params):
        request_id = uuid.uuid4().hex
        response = self.http.request("POST", MCP, headers=self.headers(), json_body={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        if response.headers.get("mcp-session-id"):
            self.session_id = response.headers["mcp-session-id"]
        result = rpc_result(response, request_id)
        return result, {"request_id": request_id, **response.receipt()}

    def _initialize(self):
        if self.initialized:
            return
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "v5", "version": "1"}})
        self.http.request("POST", MCP, headers=self.headers(), json_body={"jsonrpc": "2.0", "method": "notifications/initialized"}).require((200, 202, 204))
        self.initialized = True

    def _tool(self, name, arguments):
        self._initialize()
        result, receipt = self._rpc("tools/call", {"name": name, "arguments": arguments})
        values = [c for c in result.get("content", []) if c.get("type") == "text"]
        if len(values) != 1:
            raise ProviderError("Gojiberry tool response schema differs")
        try:
            actual = json.loads(values[0]["text"])
        except (ValueError, KeyError):
            raise ProviderError("Gojiberry native result unavailable") from None
        with self.store.db:
            self.store.record("gojiberry", receipt["request_id"], name, {"arguments": arguments, "receipt": receipt, "result": actual})
        self.last_source_key = receipt["request_id"]
        return actual

    def call_tool(self, name, arguments):
        if name not in READ_TOOLS:
            raise ValueError("Provider mutation requires the guarded send adapter")
        return self._tool(name, arguments)

    def provision(self, name, arguments):
        """Create inert resources. Ambiguous creation must never be replayed."""
        if name not in ("create_list", "create_contact", "update_contact", "add_contacts_to_list"):
            raise ValueError("Unsupported preparation capability")
        owned=list(self.store.setting('social_owned',{}).values())
        lists={v.get('list_id') for v in owned}; campaigns={v.get('campaign_id') for v in owned}
        if name=='create_list':
            raise ValueError('Create your isolated owned list in Gojiberry first, then configure its exact campaign, list and seat. Automatic list creation is disabled')
        if name in ('create_contact','add_contacts_to_list') and arguments.get('listId') not in lists:
            raise ValueError('Preparation must use your exact configured owned list')
        if name=='update_contact' and self.call_tool('get_contact',{'id':arguments.get('id')}).get('listId') not in lists:
            raise ValueError('Contact is not in your configured owned list')
        if name == "add_contacts_to_list":
            contacts=[self.call_tool('get_contact',{'id':key}) for key in arguments['contactIds']]
            if any(c.get('state')!='paused' or c.get('listId') not in lists for c in contacts):
                raise ValueError('Preparation cannot move an unpaused or foreign-list contact')
        if name == "update_contact" and (arguments.get("state") != "paused" or arguments.get("readyForCampaign") is not False):
            raise ValueError("Preparation cannot release a contact")
        if name == "create_contact":
            listing = self.call_tool("get_list", {"id": arguments.get("listId")})
            campaign = self.call_tool("get_campaign", {"id": listing.get("campaignId")})
            if campaign.get('id') not in campaigns or campaign.get("active") is not False or any(x.get("type") != "invitation" for x in campaign.get("steps", [])):
                raise ValueError("Contact preparation requires an inactive invitation-only campaign")
            arguments={**arguments,'state':'paused','readyForCampaign':False}
        key = "social_provision:" + digest([name, arguments])
        previous = self.store.setting(key)
        if previous:
            if previous.get("status") == "complete":
                return previous["result"]
            raise ValueError("Unknown native provisioning outcome requires reconciliation")
        with self.store.db:
            self.store.set(key, {"status": "attempting", "tool": name, "arguments": arguments, "at": now()})
        actual = self._tool(name, arguments)
        source=self.store.one("SELECT digest FROM source_records WHERE source='gojiberry' AND record_key=?",(self.last_source_key,))
        if not source: raise ValueError('Original native provisioning receipt is missing. Inspect Gojiberry; never recreate this contact')
        with self.store.db:
            self.store.set(key, {"status": "complete", "tool": name, "arguments": arguments, "result": actual, "at": now(),
                'provider_source_key':self.last_source_key,'provider_source_digest':source['digest']})
        return actual

    def provisioning(self, person, payload):
        """Only a completed adapter creation can establish this native contact's origin."""
        owned=self.store.setting('social_owned',{}).get(payload.get('sender'),{})
        if not owned or any(payload.get(k)!=owned.get(k) for k in ('campaign_id','list_id','seat_id')):
            raise ValueError('Use exact configured owned social resources')
        for setting in self.store.rows("SELECT data_json FROM settings WHERE name LIKE 'social_provision:%'"):
            value=json.loads(setting['data_json'])
            if value.get('status')!='complete' or value.get('tool')!='create_contact': continue
            row=self.store.one("SELECT * FROM source_records WHERE source='gojiberry' AND record_key=?",(value.get('provider_source_key',''),))
            raw=json.loads(row['data_json']) if row else {}; contact=raw.get('result',{}); arguments=raw.get('arguments',{})
            if contact.get('id')!=payload.get('contact_id'): continue
            if (not row or row['kind']!='create_contact' or digest(raw)!=row['digest'] or row['digest']!=value.get('provider_source_digest')
                    or raw.get('receipt',{}).get('http_status')!=200 or raw.get('receipt',{}).get('request_id')!=row['record_key']
                    or not __import__('re').fullmatch('[0-9a-f]{64}',str(raw.get('receipt',{}).get('response_sha256','')))
                    or value.get('result')!=contact or value.get('arguments')!=arguments
                    or arguments.get('listId')!=payload['list_id'] or arguments.get('state')!='paused' or arguments.get('readyForCampaign') is not False
                    or contact.get('listId')!=payload['list_id'] or contact.get('state')!='paused' or contact.get('readyForCampaign') is not False):
                raise ValueError('Original successful owned provisioning receipt differs or is incomplete')
            _identity(contact,person,payload['contact_id'])
            return {'source':'gojiberry','record_key':row['record_key'],'digest':row['digest']}
        raise ValueError('Import cannot adopt an arbitrary paused contact. Complete owned adapter provisioning first')

    def threads(self):
        rows, page = [], 1
        while True:
            result = self.http.request("GET", REST + "/unibox/threads", headers=self.headers(), params={"page": page, "limit": 100}).require()
            batch = result.get("data")
            if not isinstance(batch, list):
                raise ProviderError("LinkedIn thread inventory unavailable")
            rows.extend(batch)
            total_pages = result.get("totalPages")
            if total_pages is not None and page >= int(total_pages):
                if result.get("total") is not None and len(rows) != int(result["total"]):
                    raise ProviderError("LinkedIn thread coverage incomplete")
                return rows
            if total_pages is None and len(batch) < 100:
                return rows
            if not batch:
                raise ProviderError("LinkedIn thread pagination incomplete")
            page += 1

    def messages(self, thread_id):
        result = self.http.request("GET", REST + "/unibox/threads/" + quote(str(thread_id), safe="") + "/messages", headers=self.headers(), params={"limit": 200}).require()
        if not isinstance(result.get("data"), list) or result.get("totalPages") != 1 or result.get("total") != len(result["data"]):
            raise ProviderError("Exact LinkedIn thread history incomplete")
        return result["data"]


def _identity(contact, person, contact_id):
    if (contact.get("id") != contact_id or profile(contact.get("profileUrl")) != profile(person.get("profile") or person.get("linkedin"))
            or (contact.get("email") or "").lower() != person["email"]):
        raise ProviderError("Native social contact identity differs")
    if any(contact.get(k) for k in ("unsubscribed", "redListed", "blocked", "rejectedAt")) or contact.get("state") in ("excluded", "answered"):
        raise ValueError("Native social suppression or reply")


def _owned(client, payload):
    owned = client.store.setting("social_owned", {}).get(payload.get("sender"), {})
    if not owned or any(payload.get(k) != owned.get(k) for k in ("campaign_id", "list_id", "seat_id")):
        raise ValueError("Actual owned social resources unavailable")
    campaign = client.call_tool("get_campaign", {"id": owned["campaign_id"]})
    listing = client.call_tool("get_list", {"id": owned["list_id"]})
    if (campaign.get("id") != owned["campaign_id"] or campaign.get("linkedinSeatId") != owned["seat_id"]
            or campaign.get("name") != owned.get("name") or campaign.get("active") not in (True, False)
            or campaign.get("steps") != owned.get("steps") or listing.get("id") != owned["list_id"]
            or listing.get("campaignId") != owned["campaign_id"]):
        raise ValueError("Social campaign, seat, exact steps or list changed")
    return owned


def send(store, person, payload, action_key, http=None):
    """Release an already owned paused contact; provisioning is a separate capability."""
    require_enabled(store)
    client = Social(store, http)
    _owned(client, payload)
    channel = payload.get("channel", "linkedin")
    owned = store.setting("social_owned", {}).get(payload.get("sender"), {})
    steps = owned.get("steps", [])
    if channel == "linkedin" and any(step.get("type") == "message" for step in steps):
        raise ValueError("Invitation release also schedules an unreserved message; native step isolation is required")
    if client.call_tool('get_campaign',{'id':payload['campaign_id']}).get('active') is not True:
        raise ValueError('Review every list in your isolated owned campaign and activate it in Gojiberry first. The runtime will not activate other unreserved contacts')
    if channel not in ("linkedin", "linkedin_message"):
        raise ValueError("Unsupported social channel")
    contact_id = payload.get("contact_id")
    if not contact_id:
        raise ValueError("Native contact provisioning is not wired; no contact creation fallback")
    contact = client.call_tool("get_contact", {"id": contact_id})
    _identity(contact, person, contact_id)
    if contact.get("state") != "paused" or contact.get("listId") != payload["list_id"]:
        raise ValueError("Exact owned paused contact required")
    ownership = store.setting("social_prepared", {}).get(str(contact_id), {})
    if ownership.get("action_key") != action_key or ownership.get("payload") != payload:
        raise ValueError("Manual pauses cannot be adopted as v5 prepared work")
    if ownership.get('provisioning')!=client.provisioning(person,payload):
        raise ValueError('Prepared action is not bound to its original successful provisioning receipt')
    if client.call_tool("get_unibox_for_contact", {"contactId": contact_id}):
        raise ValueError("Existing social conversation requires an individual reply")
    if channel == "linkedin" and not payload.get("plain_invitation"):
        raise ValueError("Only native plain invitation contract is supported")
    if channel == "linkedin_message":
        messages = contact.get("personalizedMessages")
        if not isinstance(messages, list) or len(messages) != 1 or messages[0].get("content") != payload.get("body") or messages[0].get("stepNumber") != payload.get("step_number") or messages[0].get("stepId") != payload.get("step_id"):
            raise ValueError("Exact native personalized message or step differs")
        if not any(e.get("campaignId") == payload["campaign_id"] and e.get("type") == "invitation" and e.get("state") == "accepted" for e in contact.get("campaignStatus", [])):
            raise ValueError("Native invitation acceptance required")
    action = outreach_action(store, channel, person, payload, action_key, payload["sender"])
    try:
        recheck(store, action)
        campaign = client.call_tool("get_campaign", {"id": payload["campaign_id"]})
        if campaign.get("active") is not True: raise ValueError('Owned campaign was paused before contact release')
        released = client._tool("update_contact", {"id": contact_id, "state": None, "readyForCampaign": True})
        _identity(released, person, contact_id)
        if released.get("state") is not None or released.get("readyForCampaign") is not True:
            raise ProviderError("Exact native contact release was not verified")
        source = store.one("SELECT digest FROM source_records WHERE source='gojiberry' AND record_key=?", (client.last_source_key,))
        store.result(action_key, "queued", str(contact_id), {"at": now(), "campaign_id": payload["campaign_id"],
            "acceptance_source": {"record_key": client.last_source_key, "digest": source["digest"]}, "retry_allowed": False})
    except Exception as exc:
        store.result(action_key, "uncertain", str(contact_id), {"error": type(exc).__name__})
        raise
    return reconcile(store, action_key, http)


def send_existing_thread(store, person, payload, action_key, http=None):
    require_enabled(store)
    client = Social(store, http)
    threads = [t for t in client.threads() if str(t.get("id")) == str(payload.get("thread_id")) and t.get("contactId") == payload.get("contact_id")]
    if len(threads) != 1:
        raise ValueError("Exact native thread/contact binding unavailable")
    contact = client.call_tool("get_contact", {"id": payload["contact_id"]})
    _identity(contact, person, payload["contact_id"])
    before = client.messages(payload["thread_id"])
    if any(m.get("senderIsSelf") and m.get("content") == payload.get("body") for m in before):
        raise ValueError("Exact message already exists; reconcile")
    # Root policy must authorize this exact existing conversation, not a reused old reply.
    grants = store.setting("social_reply_grants", {})
    if grants.get(action_key) != {"thread_id": payload["thread_id"], "body": payload["body"], "contact_id": payload["contact_id"]}:
        raise ValueError("Exact existing-thread reply authorization unavailable")
    action = outreach_action(store, "linkedin_message", person, payload, action_key, payload["sender"])
    with store.db:
        store.event("social_before_send", action_key, {"message_ids": [m.get("id") for m in before], "thread_id": payload["thread_id"]})
    boundary = "v5-" + uuid.uuid4().hex
    parts = []
    for key, value in (("chatId", payload["thread_id"]), ("message", payload["body"])):
        parts.append(("--" + boundary + '\r\nContent-Disposition: form-data; name="' + key + '"\r\n\r\n' + str(value) + "\r\n").encode())
    body = b"".join(parts) + ("--" + boundary + "--\r\n").encode()
    try:
        recheck(store, action)
        response = client.http.request("POST", REST + "/unibox/messages/send-message", headers={**client.headers(), "Content-Type": "multipart/form-data; boundary=" + boundary}, data=body)
        store.result(action_key, "accepted" if 200 <= response.status < 300 else "uncertain", receipt=response.receipt())
    except Exception as exc:
        store.result(action_key, "uncertain", receipt={"error": type(exc).__name__})
        raise
    return reconcile(store, action_key, http)


def _queued_verified(store, attempt, contact, payload):
    receipt = json.loads(attempt["receipt_json"])
    proof = receipt.get("acceptance_source", {})
    row = store.one("SELECT * FROM source_records WHERE source='gojiberry' AND record_key=?", (proof.get("record_key"),))
    native = json.loads(row["data_json"]) if row else {}
    result, arguments = native.get("result", {}), native.get("arguments", {})
    from engine.validation import timestamp
    accepted_at = timestamp(native.get("receipt", {}).get("at"))
    reserved_at = timestamp(attempt.get("at"))
    owner = store.setting("social_prepared", {}).get(str(payload["contact_id"]), {})
    return bool(row and row["kind"] == "update_contact" and digest(native) == row["digest"] == proof.get("digest")
        and native.get("receipt", {}).get("http_status") == 200 and accepted_at and reserved_at and accepted_at >= reserved_at
        and owner.get("action_key") == attempt["idem_key"] and owner.get("payload") == payload
        and arguments == {"id": payload["contact_id"], "state": None, "readyForCampaign": True}
        and all(result.get(k) == contact.get(k) for k in ("id", "email", "profileUrl", "listId"))
        and contact.get("id") == payload["contact_id"] and contact.get("listId") == payload["list_id"]
        and result.get("state") is None and result.get("readyForCampaign") is True
        and contact.get("state") is None and contact.get("readyForCampaign") is True)


def reconcile(store, action_key, http=None):
    attempt = store.one("SELECT * FROM attempts WHERE idem_key=? AND channel IN ('linkedin','linkedin_message')", (action_key,))
    if not attempt:
        raise ValueError("Social attempt not found")
    payload = json.loads(attempt["payload_json"])
    client = Social(store, http)
    from engine.validation import find_person
    person, issues = find_person(store, attempt["recipient"], attempt["domain"], profile(payload.get("profileUrl")))
    if not person or issues:
        raise ValueError("Current social recipient missing")
    contact = client.call_tool("get_contact", {"id": payload["contact_id"]})
    _identity(contact, person, payload["contact_id"])
    if payload.get("thread_id"):
        before_event = store.one("SELECT payload_json FROM events WHERE kind='social_before_send' AND entity=? ORDER BY at DESC LIMIT 1", (action_key,))
        if not before_event:
            raise ValueError("Durable pre-send thread snapshot missing")
        before = json.loads(before_event["payload_json"])["message_ids"]
        matches = [m for m in client.messages(payload["thread_id"]) if m.get("id") not in before and m.get("senderIsSelf") and m.get("content") == payload["body"] and m.get("deliveredAt") and m.get("linkedinMessageBackendUrn")]
    else:
        kind = "invitation" if attempt["channel"] == "linkedin" else "message"
        matches = []
        for e in contact.get("campaignStatus") or []:
            if e.get("campaignId") != payload["campaign_id"] or e.get("type") != kind or e.get("state") != "sent":
                continue
            try:
                sent = datetime.fromisoformat(e["createdAt"].replace("Z", "+00:00"))
                reserved = datetime.fromisoformat(attempt["at"].replace("Z", "+00:00"))
                if sent.tzinfo is not None and sent >= reserved:
                    matches.append(e)
            except (KeyError, TypeError, ValueError):
                continue
    if len(matches) != 1:
        if not matches and not payload.get("thread_id") and _queued_verified(store, attempt, contact, payload):
            _owned(client, payload)
            receipt = {**json.loads(attempt["receipt_json"]), "queue_verified_at": now(),
                "native_queue_contact": contact, "sent_verified": False, "retry_allowed": False}
            store.result(action_key, "queued", str(payload["contact_id"]), receipt)
            return {"status": "queued", "contact_id": payload["contact_id"], "sent_verified": False, "retry_allowed": False}
        store.result(action_key, "uncertain", receipt={"exact_delivery_matches": len(matches), "retry_allowed": False})
        return {"status": "uncertain", "retry_allowed": False}
    actual = matches[0]
    store.result(action_key, "sent", str(actual.get("id") or payload["contact_id"]), {"native_delivery": actual, "contact_id": payload["contact_id"]})
    return {"status": "sent", "native_delivery": actual}
