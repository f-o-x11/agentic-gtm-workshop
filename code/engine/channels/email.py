"""Delegated Gmail send and exact Sent reconciliation, independent of legacy code."""
import base64
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses
import json
import os
import re
import time
from urllib.parse import quote, urlencode

from engine.http_client import HttpClient, ProviderError, outreach_action, recheck, require_enabled
from engine.database import digest, now

BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def delegated_token(http, mailbox, scope):
    path = os.environ.get("V5_GOOGLE_SERVICE_ACCOUNT_FILE")
    if not path and http.store:
        path=http.store.setting('credential_files',{}).get('google:'+mailbox.lower())
    from tools.setup import credential_path
    try: chosen=credential_path(path if path else http.credential_file('google'))
    except ValueError as exc: raise ProviderError(str(exc)) from None
    key = json.loads(chosen.read_text())
    if key.get('type') == 'authorized_user':
        if (key.get('email') or '').lower() != mailbox.lower():
            raise ProviderError('Google OAuth mailbox differs from the authorized sender')
        requested = set(scope.split()); granted = set(key.get('scopes', []))
        if not requested <= granted:
            raise ProviderError('Google OAuth permission missing: ' + ', '.join(sorted(requested - granted)))
        response = http.request('POST', 'https://oauth2.googleapis.com/token',
            headers={'Content-Type':'application/x-www-form-urlencoded'},
            data=urlencode({'grant_type':'refresh_token','client_id':key['client_id'],
                'client_secret':key['client_secret'],'refresh_token':key['refresh_token']}).encode())
        token = response.require().get('access_token')
        if not token: raise ProviderError('Google OAuth refresh did not return an access token')
        return token
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    def b64(value):
        return base64.urlsafe_b64encode(value).decode().rstrip("=")
    header = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    issued = int(time.time())
    claims = b64(json.dumps({"iss": key["client_email"], "sub": mailbox, "scope": scope,
        "aud": "https://oauth2.googleapis.com/token", "iat": issued, "exp": issued + 3600}).encode())
    unsigned = header + "." + claims
    private = serialization.load_pem_private_key(key["private_key"].encode(), password=None)
    signed = private.sign(unsigned.encode(), padding.PKCS1v15(), hashes.SHA256())
    response = http.request("POST", "https://oauth2.googleapis.com/token", headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": unsigned + "." + b64(signed)}).encode())
    token = response.require().get("access_token")
    if not isinstance(token, str) or not token:
        raise ProviderError("Delegated Google authentication unavailable")
    return token


class Mailbox:
    def __init__(self, store, mailbox, http=None):
        self.store, self.mailbox = store, mailbox.lower()
        self.http = http or HttpClient(store)
        self.access_token = None

    def _auth(self):
        if self.access_token:
            return {"Authorization": "Bearer " + self.access_token}
        token = delegated_token(self.http, self.mailbox, "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.send")
        self.access_token = token
        actual = self.http.request("GET", BASE + "/profile", headers={"Authorization": "Bearer " + token}).require()
        if actual.get("emailAddress", "").lower() != self.mailbox:
            self.access_token = None
            raise ProviderError("Actual Gmail mailbox differs from authorized sender")
        return {"Authorization": "Bearer " + token}

    def query(self, query):
        results, seen, cursor = [], set(), None
        while True:
            params = {"q": query, "maxResults": 100, "includeSpamTrash": "true"}
            if cursor:
                params["pageToken"] = cursor
            page = self.http.request("GET", BASE + "/messages", headers=self._auth(), params=params).require()
            if not isinstance(page, dict) or not isinstance(page.get("messages", []), list):
                raise ProviderError("Gmail message inventory schema differs")
            results.extend(page.get("messages", []))
            cursor = page.get("nextPageToken")
            if not cursor:
                return results
            if cursor in seen:
                raise ProviderError("Gmail pagination incomplete")
            seen.add(cursor)

    def message(self, message_id, format="raw"):
        actual = self.http.request("GET", BASE + "/messages/" + quote(str(message_id), safe=""),
            headers=self._auth(), params={"format": format}).require()
        if actual.get("id") != message_id:
            raise ProviderError("Gmail message identity differs")
        return actual


def mime(payload, recipient, sender, action_key):
    for field in (recipient, sender, payload.get("subject", "")):
        if not isinstance(field, str) or any(c in field for c in "\r\n"):
            raise ValueError("Invalid mail header")
    if not isinstance(payload.get("body"), str) or not payload["body"].strip():
        raise ValueError("Exact plain message body required")
    from engine.validation import format_email
    message = BytesParser(policy=policy.default).parsebytes(format_email(sender, recipient, payload["subject"], payload["body"], payload.get("html") or payload.get("body_html")))
    message["Message-ID"] = "<v5-" + action_key + "@" + sender.rsplit('@', 1)[-1] + ">"
    message['X-GTM-Action-Key'] = action_key
    message["List-Unsubscribe"] = "<mailto:" + sender + "?subject=unsubscribe>"
    return message


def send(store, person, payload, action_key, http=None):
    require_enabled(store)
    sender = payload.get("sender", "")
    message = mime(payload, person["email"], sender, action_key)
    box = Mailbox(store, sender, http)
    headers = box._auth()  # Resolve actual mailbox before reserving a send.
    action = outreach_action(store, "email", person, payload, action_key, sender)
    with store.db:
        store.event("gmail_transport", action_key, {"transport": "v5.gmail", "rfc_message_id": str(message["Message-ID"]), "mime_sha256": __import__("hashlib").sha256(message.as_bytes()).hexdigest()})
    try:
        recheck(store, action)
        response = box.http.request("POST", BASE + "/messages/send", headers=headers,
            json_body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()})
        receipt = response.receipt()
        native_id = response.body.get("id") if isinstance(response.body, dict) else None
        state = "accepted" if response.status == 200 and native_id else "uncertain"
        store.result(action_key, state, native_id, receipt)
    except Exception as exc:
        store.result(action_key, "uncertain", receipt={"error": type(exc).__name__})
        raise
    return reconcile(store, action_key, http)


def _normalized(text):
    return re.sub(r"\s+", " ", text or "").strip()


def reconcile(store, action_key, http=None):
    attempt = store.one("SELECT * FROM attempts WHERE idem_key=? AND channel='email'", (action_key,))
    if not attempt:
        raise ValueError("Email attempt not found")
    payload = json.loads(attempt["payload_json"])
    transport = store.one("SELECT payload_json FROM events WHERE kind='gmail_transport' AND entity=?", (action_key,))
    if not transport:
        return {"status": "legacy_reconciliation_unavailable", "retry_allowed": False,
                "reason": "Imported email attempt retains its original native Message-ID and transport; no v5 readback claim"}
    box = Mailbox(store, attempt["sender"], http)
    stamp = datetime.fromisoformat(attempt["at"].replace("Z", "+00:00"))
    ids = box.query("in:sent to:" + attempt["recipient"] + " after:" + str(int(stamp.timestamp()) - 60))
    accepted = store.one("SELECT * FROM events WHERE kind='attempt_accepted' AND entity=?", (action_key,))
    positive_id = False
    if accepted:
        recorded = json.loads(accepted['payload_json'])
        proof = recorded.get('receipt', {})
        positive_id = (accepted['source_digest'] == digest({'at': accepted['at'], 'kind': accepted['kind'],
                       'entity': accepted['entity'], 'payload': recorded})
                       and proof.get('http_status') == 200 and recorded.get('provider_id') == attempt['provider_id']
                       and (proof.get('body') or {}).get('id') == attempt['provider_id'])
    if positive_id and not any(item['id'] == attempt['provider_id'] for item in ids):
        ids.append({'id': attempt['provider_id']})
    matches = []
    expected_html = mime(payload, attempt["recipient"], attempt["sender"], action_key).get_body(preferencelist=("html",)).get_content()
    for item in ids:
        if attempt["provider_id"] and item["id"] != attempt["provider_id"]:
            continue
        native = box.message(item["id"])
        raw = base64.urlsafe_b64decode(native.get("raw", "") + "===")
        message = BytesParser(policy=policy.default).parsebytes(raw)
        addresses = lambda field: [email.lower() for _, email in getaddresses(message.get_all(field, []))]
        expected_id = "<v5-" + action_key + "@" + attempt['sender'].rsplit('@', 1)[-1] + ">"
        bound = (message.get('X-GTM-Action-Key') == action_key or message.get('Message-ID') == expected_id
                 or positive_id and native['id'] == attempt['provider_id'])
        if ("SENT" not in native.get("labelIds", []) or not bound
                or addresses("From") != [attempt["sender"].lower()] or addresses("To") != [attempt["recipient"]]
                or addresses("Cc") or addresses("Bcc") or message.get("Subject") != payload["subject"]):
            continue
        plain = [p.get_content() for p in message.walk() if p.get_content_type() == "text/plain"]
        html = [p.get_content() for p in message.walk() if p.get_content_type() == "text/html"]
        if len(plain) != 1 or _normalized(plain[0]) != _normalized(payload["body"]):
            continue
        if len(html) != 1 or _normalized(html[0]) != _normalized(expected_html):
            continue
        actual_time = int(native.get("internalDate", 0)) / 1000
        if actual_time < stamp.timestamp() - 60:
            continue
        matches.append({"message_id": native["id"], "thread_id": native.get("threadId"),
            "mailbox": attempt["sender"], "sent_at": datetime.fromtimestamp(actual_time, timezone.utc).isoformat(),
            "mime_sha256": __import__("hashlib").sha256(raw).hexdigest(), "rfc_message_id": str(message.get('Message-ID')),
            'action_binding': 'accepted_native_id' if positive_id else 'action_header'})
    if len(matches) == 1:
        store.result(action_key, "sent", matches[0]["message_id"], matches[0])
        return {"status": "sent", **matches[0]}
    state = "uncertain" if not matches else "duplicate_review"
    store.result(action_key, state, receipt={"matches": matches, "retry_allowed": False})
    return {"status": state, "retry_allowed": False}


import base64
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
import json
import re

from engine.http_client import HttpClient, ProviderError
from engine.channels.social import Social
from engine.database import digest, encode, now


def _addresses(value):
    return [address.strip().lower() for _, address in getaddresses([value or ""]) if "@" in address]


def _classify(message, body):
    headers = (str(message.get("From", "")) + " " + str(message.get("Subject", ""))).lower()
    if any(term in headers for term in ("mailer-daemon", "postmaster", "delivery status notification", "undeliverable")):
        return "bounce"
    if str(message.get("Auto-Submitted", "")).lower() not in ("", "no") or any(term in headers for term in ("automatic reply", "out of office")):
        return "automated_reply"
    if re.search(r"\b(?:unsubscribe|remove me|do not (?:email|contact)|stop (?:emailing|contacting))\b", body, re.I):
        return "opt_out"
    return "inbound_unattributed"


class Replies:
    def __init__(self, store, http=None):
        self.store, self.http = store, http or HttpClient(store)

    def _domain(self, recipient):
        row = self.store.one("SELECT domain FROM people WHERE email=?", (recipient,))
        return row["domain"] if row else recipient.rsplit("@", 1)[-1]

    def _save(self, source, key, recipient, stamp, kind, value):
        domain = self._domain(recipient)
        self.store.record(source, key, kind, value)
        self.store.db.execute("INSERT OR REPLACE INTO history VALUES (?,?,?,?,?,?)", (key, recipient, domain, stamp, kind, encode(value)))
        if kind == "opt_out":
            self.store.db.execute("INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?,?,?)", ("email", recipient, "Native inbound opt-out", source, stamp, encode(value)))

    def gmail(self, mailbox, query):
        box = Mailbox(self.store, mailbox, self.http)
        # Gmail lists newest first. Save every outgoing reference before classifying incoming replies.
        items = box.query(query+' in:sent') + box.query(query+' -in:sent')
        observations = []
        for item in items:
            native = box.message(item["id"])
            raw = base64.urlsafe_b64decode(native.get("raw", "") + "===")
            message = BytesParser(policy=policy.default).parsebytes(raw)
            stamp = datetime.fromtimestamp(int(native["internalDate"]) / 1000, timezone.utc).isoformat()
            sender = _addresses(message.get("From"))
            destinations = _addresses(message.get("To")) + _addresses(message.get("Cc")) + _addresses(message.get("Bcc"))
            body = "\n".join(p.get_content() for p in message.walk() if p.get_content_type() == "text/plain")
            outgoing = "SENT" in native.get("labelIds", [])
            rfc = str(message.get("Message-ID", "")).strip()
            value = {"provider": "gmail", "native_id": native["id"], "mailbox": mailbox, "thread_id": native.get("threadId"), "rfc_message_id": rfc,
                "in_reply_to": str(message.get("In-Reply-To", "")), "references": str(message.get("References", "")), "from": sender,
                "to": destinations, "subject": str(message.get("Subject", "")), "body": body, "outbound": outgoing, "at": stamp, "mime_sha256": digest(native.get("raw"))}
            kind = "sent" if outgoing else _classify(message, body)
            for peer in destinations if outgoing else sender:
                if peer == mailbox or peer.rsplit("@", 1)[-1] in self.store.setting("internal_domains", []):
                    continue
                # A response is attributed only through exact earlier native thread/reference evidence.
                prior = self.store.rows("SELECT data_json FROM history WHERE recipient=? AND kind='sent' AND at<?", (peer, stamp))
                linked = []
                for row in prior:
                    before = json.loads(row["data_json"])
                    message_id = before.get("rfc_message_id")
                    if ((before.get("mailbox") == mailbox and before.get("thread_id") == value["thread_id"])
                            or message_id and message_id in (value["in_reply_to"] + " " + value["references"])):
                        linked.append(before.get("native_id"))
                actual_kind = "reply_received" if kind == "inbound_unattributed" and linked else kind
                value["prior_outbound_ids"] = linked
                key = digest([rfc or "gmail:" + mailbox + ":" + native["id"], peer])
                with self.store.db:
                    self._save("gmail.history", key, peer, stamp, actual_kind, value)
                observations.append(key)
        return {"provider": "gmail", "mailbox": mailbox, "query": query, "complete": True, "messages": len(items), "observations": len(observations), "observed_at": now()}

    def instantly(self):
        headers = {"Authorization": "Bearer " + self.http.credential("instantly")}
        cursor, seen, count = None, set(), 0
        while True:
            params = {"limit": 100}
            if cursor:
                params["starting_after"] = cursor
            body = self.http.request("GET", "https://api.instantly.ai/api/v2/emails", headers=headers, params=params).require()
            if not isinstance(body, dict) or not isinstance(body.get("items"), list):
                raise ProviderError("Instantly message inventory unavailable")
            for native in body["items"]:
                if not native.get("id"):
                    raise ProviderError("Instantly native message ID missing")
                sender = (native.get("from_address_email") or native.get("from_address") or "").lower().strip()
                destinations = _addresses(native.get("to_address_email_list"))
                outgoing = native.get("ue_type") == 1
                stamp = native.get("timestamp_email") or native.get("timestamp_created") or native.get("created_at")
                if not stamp or not sender:
                    raise ProviderError("Instantly native message identity/time incomplete")
                rfc = native.get("message_id")
                value = {"provider": "instantly", "native_id": native["id"], "mailbox": native.get("eaccount"), "rfc_message_id": rfc,
                    "thread_id": native.get("thread_id"), "at": stamp, "outbound": outgoing, "native": native}
                for peer in destinations if outgoing else [sender]:
                    if "@" not in peer or peer.rsplit("@", 1)[-1] in self.store.setting("internal_domains", []):
                        continue
                    key = digest([rfc or "instantly:" + native["id"], peer])
                    prior = self.store.one("SELECT history_key FROM history WHERE history_key=?", (key,))
                    with self.store.db:
                        if prior:
                            self.store.record("instantly.history", key, "corroboration", value)
                        else:
                            self._save("instantly.history", key, peer, stamp, "sent" if outgoing else "inbound_unattributed", value)
                count += 1
            cursor = body.get("next_starting_after")
            if not cursor:
                return {"provider": "instantly", "complete": True, "messages": count, "observed_at": now()}
            if cursor in seen or not body["items"]:
                raise ProviderError("Instantly history pagination incomplete")
            seen.add(cursor)

    def linkedin(self):
        client = Social(self.store, self.http)
        count = 0
        for thread in client.threads():
            contact_id, thread_id = thread.get("contactId"), thread.get("id")
            if contact_id is None or thread_id is None:
                raise ProviderError("Native LinkedIn thread binding incomplete")
            contact = client.call_tool("get_contact", {"id": contact_id})
            if contact.get("id") != contact_id or not contact.get("email"):
                raise ProviderError("Native LinkedIn reply contact identity incomplete")
            for native in client.messages(thread_id):
                if not native.get("id"):
                    raise ProviderError("Native LinkedIn message ID missing")
                stamp = native.get("deliveredAt") or native.get("createdAt")
                if not stamp:
                    raise ProviderError("Native LinkedIn message timestamp missing")
                kind = "social_sent" if native.get("senderIsSelf") and native.get("deliveredAt") else "social_reply" if native.get("senderIsSelf") is False else "social_unknown"
                value = {"provider": "gojiberry", "native_id": native["id"], "thread_id": thread_id, "contact_id": contact_id, "native": native}
                with self.store.db:
                    self._save("gojiberry.history", "gojiberry:" + str(native["id"]), contact["email"].lower(), stamp, kind, value)
                count += 1
        return {"provider": "gojiberry", "complete": True, "messages": count, "observed_at": now()}

    def refresh(self):
        configured = self.store.setting("history_sources", {})
        mailboxes = configured.get("gmail", [])
        start = configured.get("gmail_start")
        if not mailboxes or not isinstance(start, int):
            return {"complete": False, "reason": "Explicit mailbox history scope and baseline boundary are missing"}
        results, failures = {}, {}
        for mailbox in mailboxes:
            try:
                query = "after:" + str(start) + " -in:drafts"
                domains = configured.get("domains", [])
                if domains:
                    if any(not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}', d) for d in domains):
                        raise ValueError("Exact employer domains required for scoped history")
                    query += " {" + " ".join("from:" + d + " to:" + d for d in domains) + "}"
                results[mailbox] = self.gmail(mailbox, query)
            except Exception as exc:
                failures[mailbox] = type(exc).__name__
        for name in ("instantly", "linkedin"):
            if configured.get(name):
                try:
                    results[name] = getattr(self, name)()
                except Exception as exc:
                    failures[name] = type(exc).__name__
        receipt = {"complete": not failures, "observed_at": now(), "sources": results, "failures": failures, "domain_scope": configured.get("domains", []),
                   "coverage": "configured sources and domains only"}
        with self.store.db:
            self.store.set("history_refresh", receipt)
        return receipt


def refresh(store, http=None):
    return Replies(store, http).refresh()
