"""Loop & Tie meeting-gated gifts with exact native creation and delivery receipts."""
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from urllib.parse import quote, urlparse

from engine.http_client import HttpClient, ProviderError, outreach_action, recheck, require_enabled
from engine.database import now, digest

def team_base(store):
    team = store.setting('loop_and_tie_team')
    if not isinstance(team, str) or not __import__('re').fullmatch(r'[A-Za-z0-9_-]+', team):
        raise ValueError('Your exact owned Loop & Tie team ID is not configured')
    return 'https://api.loopandtie.com/v1/teams/' + quote(team, safe='')


class Gifts:
    def __init__(self, store, http=None):
        self.store, self.http = store, http or HttpClient(store)
        self.base = team_base(store)

    def headers(self):
        return {"Authorization": "Bearer " + self.http.credential("loop_and_tie")}

    def read(self, path):
        if not path.startswith("/") or ".." in path:
            raise ValueError("Invalid gift resource path")
        response = self.http.request("GET", self.base + path, headers=self.headers())
        response.require()
        return response

    def inventory(self, path="/gifts"):
        rows, seen, url = [], set(), self.base + path
        while url:
            if url in seen or not url.startswith(self.base + "/"):
                raise ProviderError("Gift pagination identity differs")
            seen.add(url)
            page = self.http.request("GET", url, headers=self.headers()).require()
            if not isinstance(page, dict) or not isinstance(page.get("data"), list):
                raise ProviderError("Gift inventory incomplete")
            rows.extend(page["data"])
            next_url = (page.get("links") or {}).get("next")
            if isinstance(next_url, dict):
                next_url = next_url.get("href")
            if next_url and next_url.startswith("/"):
                next_url = "https://api.loopandtie.com" + next_url
            url = next_url
        return rows

    def catalogue(self):
        teams = self.http.request("GET", "https://api.loopandtie.com/v1/teams", headers=self.headers()).require()
        matching = [t for t in teams.get("data", []) if str(t.get("id")) == self.store.setting('loop_and_tie_team')]
        if len(matching) != 1:
            raise ProviderError("Owned gift team unavailable")
        return {"team": matching[0], "schedulers": self.inventory("/schedulers"), "at": now()}


def _validate_payload(person, payload):
    gift = payload.get("gift")
    if not isinstance(gift, dict) or not isinstance(gift.get("recipients_attributes"), list) or len(gift["recipients_attributes"]) != 1:
        raise ValueError("One exact gift recipient required")
    recipient = gift["recipients_attributes"][0]
    if recipient.get("email", "").lower() != person["email"] or recipient.get("name") != person["name"] or recipient.get("delivery_method") != "email":
        raise ValueError("Gift recipient differs from verified identity")
    if date.fromisoformat(recipient["expires_on"]) <= datetime.now(timezone.utc).date():
        raise ValueError("Gift expiry is not future")
    stamp = datetime.fromisoformat(recipient["scheduled_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None or not all(isinstance(gift.get(k), str) and gift[k].strip() for k in ("collection", "message", "from", "subject")):
        raise ValueError("Exact gift copy, collection and aware schedule required")
    return gift, recipient


def send(store, person, payload, action_key, http=None):
    require_enabled(store)
    gift, recipient = _validate_payload(person, payload)
    client = Gifts(store, http)
    inventory = client.inventory()
    for native in inventory:
        email = (native.get("attributes", {}).get("email") or "").lower()
        if email == person["email"]:
            raise ValueError("Prior gift for this recipient")
    catalogue = client.catalogue()
    gate = store.setting("gift_gate", {})
    required = ("external_id", "numeric_id", "name", "source")
    if not all(gate.get(k) for k in required) or gift.get("scheduler_id") != gate["numeric_id"]:
        raise ValueError("Verified numeric gift meeting gate unavailable")
    proof = store.one("SELECT data_json,digest FROM source_records WHERE source=? AND record_key=?",
        (gate.get("binding_source"), str(gate.get("binding_key", ""))))
    binding = json.loads(proof["data_json"]) if proof else {}
    native_proof=store.one("SELECT * FROM source_records WHERE source='live.loopandtie.scheduler_catalogue' AND record_key=?",(gate.get('external_id'),))
    from engine.validation import fresh
    if (not proof or digest(binding) != proof["digest"] or proof["digest"] != gate.get("binding_digest")
            or any(binding.get(k) != gate.get(k) for k in required)
            or binding.get("meeting_required") is not True or type(gate["numeric_id"]) is not int
            or binding.get("form_id") != "edit_scheduler_" + str(gate["numeric_id"])
            or binding.get('provider')!='loop_and_tie' or binding.get('team_id')!=store.setting('loop_and_tie_team')
            or not fresh(binding.get('captured_at'),65*60) or not native_proof
            or digest(json.loads(native_proof['data_json']))!=native_proof['digest'] or native_proof['digest']!=binding.get('native_catalogue_digest')):
        raise ValueError("Native numeric scheduler binding receipt is absent or changed")
    matches = [s for s in catalogue["schedulers"] if s.get("id") == gate["external_id"]]
    if len(matches) != 1 or any(matches[0].get("attributes", {}).get(k) != gate[v] for k, v in (("external-id", "external_id"), ("name", "name"), ("source", "source"))):
        raise ValueError("Owned gift meeting gate differs")
    collection = client.read("/collections/" + quote(gift["collection"], safe="")).body
    if str(collection.get("data", {}).get("id")) != gift["collection"]:
        raise ProviderError("Gift collection identity differs")
    cost = Decimal(str(collection["data"]["attributes"]["price"]))
    team = catalogue["team"]["attributes"]
    if "free_shipping" not in team.get("permissions", []) or Decimal(str(team.get("account-balance", 0))) < cost:
        raise ValueError("Actual gift funding or free shipping unavailable")
    from engine.checks import unpack, approved_scope, gift_budget_issues
    draft=unpack(store.one('SELECT * FROM actions WHERE action_key=?',(action_key,)))
    currency=collection['data']['attributes'].get('currency') or collection['data']['attributes'].get('currency-code')
    if store.setting('portable_attendee',False):
        issues=gift_budget_issues(store,draft,cost,currency)
        if issues: raise ValueError(' '.join(issues))
    with store.db:
        if store.setting('portable_attendee',False):
            grant,_=approved_scope(store,draft)
            store.event('gift_budget_reserved',action_key,{'grant_id':grant['grant_id'],'cost':str(cost),'currency':currency},key='gift_cost:'+action_key)
        store.event("gift_preflight", action_key, {"catalogue": catalogue, "collection": collection,
            "inventory_complete": True, "inventory_count": len(inventory), "inventory_digest": digest(inventory), "gate": gate, "cost": str(cost)})
    action = outreach_action(store, "gift", person, payload, action_key, gift["from"])
    try:
        recheck(store, action)
        response = client.http.request("POST", client.base + "/bulk/gifts", headers=client.headers(), json_body=payload)
        receipt = response.receipt()
        values = response.body.get("data", []) if isinstance(response.body, dict) else []
        gift_id = str(values[0].get("id", "")) if len(values) == 1 else None
        state = ("aborted" if response.status in (400, 422) and response.body.get("errors") and not values else
                 "accepted" if response.status in (200, 201) and gift_id else "uncertain")
        store.result(action_key, state, gift_id, receipt)
    except Exception as exc:
        store.result(action_key, "uncertain", receipt={"error": type(exc).__name__})
        raise
    return {"status": state, "reason": response.body.get("errors")} if state == "aborted" else reconcile(store, action_key, http)


def _exact(native, payload, recipient):
    gift = payload["gift"]
    attrs = native.get("attributes", {})
    relationship = native.get("relationships", {}).get("collection", {}).get("data", {})
    return ((attrs.get("email") or "").lower() == recipient and attrs.get("expires-on") == gift["recipients_attributes"][0]["expires_on"]
            and all(attrs.get(k) == gift[k] for k in ("from", "subject", "message"))
            and str(relationship.get("id")) == gift["collection"])


def reconcile(store, action_key, http=None):
    attempt = store.one("SELECT * FROM attempts WHERE idem_key=? AND channel='gift'", (action_key,))
    if not attempt:
        raise ValueError("Gift attempt not found")
    payload = json.loads(attempt["payload_json"])
    client = Gifts(store, http)
    gift_id = attempt["provider_id"]
    if gift_id:
        native = client.read("/gifts/" + quote(gift_id, safe="")).body.get("data", {})
        matches = [native] if str(native.get("id")) == gift_id and _exact(native, payload, attempt["recipient"]) else []
    else:
        matches = [g for g in client.inventory() if _exact(g, payload, attempt["recipient"])]
    if len(matches) != 1:
        store.result(action_key, "uncertain", receipt={"exact_matches": len(matches), "retry_allowed": False})
        return {"status": "uncertain", "retry_allowed": False}
    native = matches[0]
    events = [e for e in native.get("attributes", {}).get("events", []) if e.get("stage") == "sent" and e.get("created-at")]
    state = "sent" if events else "created_verified"
    gate = store.one("SELECT event_id FROM events WHERE kind='gift_preflight' AND entity=?", (action_key,))
    receipt = {"at": now(), "gift": native, "sent_events": events, "meeting_gate_verified_at_creation": bool(gate), "native_scheduler_relationship_verified": False}
    store.result(action_key, state, str(native["id"]), receipt)
    return {"status": state, "gift_id": str(native["id"]), "stage": native.get("attributes", {}).get("stage")}
