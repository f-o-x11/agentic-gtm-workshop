"""Explicit native HTTPS transport. No retries, redirects or implicit credentials."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


def now():
    return datetime.now(timezone.utc).isoformat()


class ProviderError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class Response:
    status: int
    body: object
    raw: bytes
    headers: dict

    def require(self, codes=(200,)):
        if self.status not in codes:
            raise ProviderError("Provider HTTP " + str(self.status))
        return self.body

    def receipt(self):
        return {"at": now(), "http_status": self.status, "body": self.body,
                "response_sha256": hashlib.sha256(self.raw).hexdigest(),
                "retry_after": self.headers.get("retry-after")}


class HttpClient:
    def __init__(self, store=None):
        self.store = store
        self.opener = urllib.request.build_opener(_NoRedirect())

    def credential_file(self, provider):
        name = "V5_" + provider.upper().replace("-", "_") + "_FILE"
        paths = self.store.setting("credential_files", {}) if self.store else {}
        value = os.environ.get(name) or paths.get(provider)
        if not value:
            raise ProviderError("Credential not configured for " + provider)
        path=Path(value).expanduser().resolve()
        from tools.setup import credential_path
        try: return credential_path(path)
        except ValueError as exc: raise ProviderError(str(exc)) from None

    def credential(self, provider):
        name = "V5_" + provider.upper().replace("-", "_") + "_TOKEN"
        raw = os.environ.get(name)
        if not raw:
            raw = self.credential_file(provider).read_text().strip()
        if provider == "calendly":
            match = re.search(r"^CALENDLY_(?:ORG_)?TOKEN\s*=\s*(\S+)", raw, re.M)
            raw = match[1].strip('"\'') if match else raw
        if provider == "gojiberry" and "API Key:" in raw:
            match = re.search(r"API Key:\s*(\S+)", raw)
            raw = match[1] if match else ""
        if provider == "apify" and not re.fullmatch(r"apify_[A-Za-z0-9_]+", raw):
            matches = re.findall(r"apify_[A-Za-z0-9_]+", raw)
            raw = matches[0] if len(matches) == 1 else ""
        if provider == "instantly" and not re.fullmatch(r"[A-Za-z0-9_\-=]{30,}", raw):
            matches = re.findall(r"[A-Za-z0-9_\-=]{30,}", raw)
            raw = matches[0] if len(matches) == 1 else ""
        if provider == "rocketreach":
            match = re.search(r"^(?:ROCKETREACH_API_KEY|api_key|Key)\s*[:=]\s*(\S+)", raw, re.M)
            raw = match[1].strip('\"\'') if match else raw
        if provider == "hubspot" and not re.fullmatch(r"pat-[a-z0-9-]+", raw):
            matches = re.findall(r"pat-[a-z0-9-]+", raw)
            raw = matches[0] if len(matches) == 1 else ""
        if provider == "zerobounce" and not re.fullmatch(r"[A-Za-z0-9]{25,}", raw):
            matches = re.findall(r"[A-Za-z0-9]{25,}", raw)
            raw = matches[0] if len(matches) == 1 else ""
        if provider == "metadata" and "MCP_PAT=" in raw:
            values = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
            if values.get("MCP_URL", "").rstrip("/") != "https://mcp-server.metadata.io/mcp":
                raise ProviderError("Metadata credential destination differs")
            raw = values.get("MCP_PAT", "")
        if not raw or any(c in raw for c in "\r\n"):
            raise ProviderError("Credential format unsupported for " + provider)
        return raw

    def request(self, method, url, *, headers=None, params=None, json_body=None,
                data=None, timeout=45):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("An explicit HTTPS destination is required")
        if params:
            url += ("&" if parsed.query else "?") + urllib.parse.urlencode(params, doseq=True)
        request_headers = {"User-Agent": "Agentic-GTM-Workshop/1.0", "Accept": "application/json"}
        request_headers.update(headers or {})
        if json_body is not None:
            if data is not None:
                raise ValueError("Choose one request body")
            data = json.dumps(json_body, ensure_ascii=False).encode()
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            response = self.opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            response = exc
        except (OSError, urllib.error.URLError, TimeoutError):
            # The caller's durable attempt remains unresolved; never replay automatically.
            raise ProviderError("Transport outcome unknown") from None
        try:
            raw = response.read()
            response_headers = {k.lower(): v for k, v in response.headers.items()}
            try:
                body = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                body = None
            return Response(response.status, body, raw, response_headers)
        finally:
            response.close()


def rpc_result(response, request_id):
    response.require()
    messages = []
    if isinstance(response.body, dict):
        messages = [response.body]
    else:
        for line in response.raw.decode("utf-8").splitlines():
            if line.startswith("data:"):
                try:
                    messages.append(json.loads(line[5:].strip()))
                except ValueError:
                    pass
    matches = [m for m in messages if isinstance(m, dict) and m.get("id") == request_id]
    if len(matches) != 1 or matches[0].get("error") or "result" not in matches[0]:
        raise ProviderError("Exact native RPC response unavailable")
    result = matches[0]["result"]
    if isinstance(result, dict) and result.get("isError"):
        raise ProviderError("Native tool rejected the operation")
    return result


def require_enabled(store):
    from engine.checks import execution_issues
    issues = execution_issues(store)
    if issues:
        raise ValueError(' '.join(issues))


def outreach_action(store, channel, person, payload, action_key, sender="", reserve=True):
    from engine.checks import make_action, require_commit, action_hash
    action = make_action(channel, person, payload, sender)
    planned = store.one("SELECT * FROM actions WHERE action_key=?", (action_key,))
    if not planned or any(planned[k] != action[k] for k in ("channel", "recipient", "domain", "sender")) or json.loads(planned["payload_json"]) != payload:
        raise ValueError("Exact planned action differs from current recipient or payload")
    action["at"], action["action_key"] = planned["at"], action_key
    if action_key != action_hash(action):
        raise ValueError("Action key differs from exact guarded payload")
    require_enabled(store)
    require_commit(store, action)
    if reserve:
        store.reserve(channel, action["recipient"], action["domain"], sender, payload, action_key)
    return action


def recheck(store, action):
    from engine.checks import require_commit
    require_enabled(store)
    require_commit(store, action, allow_reserved=True)
