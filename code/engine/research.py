"""Native enrichment requests. Candidates never imply current identity or send consent."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import re
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo

from engine.http_client import HttpClient, ProviderError
from engine.database import digest, encode, now

APIFY = "https://api.apify.com/v2"
ACTORS = {"harvestapi~linkedin-profile-scraper", "harvestapi~linkedin-company", "pipelinelabs~leads-finder-with-emails-apollo-lusha-zoominfo", "harvestapi~linkedin-profile-posts", "harvestapi~linkedin-post-search"}
INSTANTLY = "https://api.instantly.ai/api/v2"
EMAIL_ACTIONS = {"bettercontact": "bettercontact_find_email", "contactout": "contactout_find_email", "findymail": "findymail_find_email", "icypeas": "icypeas_find_email", "leadmagic": "leadmagic_find_email", "prospeo": "prospeo_find_email", "wiza": "wiza_find_email"}
BASES = {"apify": APIFY, "instantly": INSTANTLY, "triguna": "https://api.triguna.ai/v1", "moltsets": "https://api.moltsets.com/api/v1/tools", "rocketreach": "https://api.rocketreach.co/api/v2", "sixtyfour": "https://api.sixtyfour.ai", "exa": "https://api.exa.ai"}


def require_research_enabled(store):
    if store.setting("research_enabled", False) is not True:
        raise ValueError("Paid research is disabled")


class Research:
    def __init__(self, store, http=None):
        self.store, self.http = store, http or HttpClient(store)

    def auth(self, provider):
        key = self.http.credential(provider)
        header = {"triguna": "ApiKey", "rocketreach": "Api-Key", "sixtyfour": "x-api-key", "exa": "x-api-key"}.get(provider)
        return {header: key} if header else {"Authorization": "Bearer " + key}

    def read(self, provider, url, params=None):
        self._destination(provider, url)
        response = self.http.request("GET", url, headers=self.auth(provider), params=params)
        response.require()
        with self.store.db:
            self.store.record(provider, digest([url, params]), "native_read", {"params": params, **response.receipt()})
        return response.body

    def _paid(self, provider, method, url, payload, *, credits=None, params=None):
        require_research_enabled(self.store)
        self._destination(provider, url)
        restriction = self.store.setting("provider_restriction:" + provider, {})
        until = restriction.get("retry_at")
        if restriction and (not until or datetime.now(timezone.utc) < datetime.fromisoformat(until)):
            raise ValueError("Actual provider restriction requires recovery: " + provider)
        matches = self.native_unresolved(provider, url, payload)
        if matches:
            identifiers = [str(r["provider_id"]) for r in matches if r.get("provider_id")]
            reason = "Reconcile same native handle " + ",".join(identifiers) if identifiers else "Native submission outcome unknown; preserve its original intent"
            raise ValueError(reason + "; never resubmit or reserve credits again")
        fingerprint = digest([provider, method, url, payload, params])
        channel = "research:" + provider
        previous = self.store.one("SELECT * FROM attempts WHERE channel=? AND recipient=?", (channel, fingerprint))
        if previous:
            if previous["status"] in ("complete", "not_found", "accepted"):
                return json.loads(previous["receipt_json"])
            raise ValueError("Existing paid request requires reconciliation, never automatic replay")
        action_key = digest([channel, fingerprint])
        headers = self.auth(provider) if provider != "zerobounce" else {}
        budget = None
        if provider == "sixtyfour":
            if credits is None or credits <= 0:
                raise ValueError("SixtyFour reservation ceiling required")
            month = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m")
            budget = (provider, month, credits)
        self.store.reserve(channel, fingerprint, "", "", {"method": method, "url": url, "input": payload, "params": params, "expected_credits": credits}, action_key, budget=budget)
        try:
            require_research_enabled(self.store)
            response = self.http.request(method, url, headers=headers, params=params,
                json_body=payload if method == "POST" else None, timeout=90)
            receipt = {"provider": provider, "request_key": action_key, "expected_credits": credits,
                "billed_credits": None, "send_authorized": False, **response.receipt()}
            if response.status in (401, 402, 403, 429):
                retry_at = None
                retry = response.headers.get("retry-after")
                if response.status == 429 and retry:
                    try:
                        retry_at = (datetime.now(timezone.utc) + timedelta(seconds=max(0, float(retry)))).isoformat()
                    except (TypeError, ValueError):
                        try:
                            parsed = parsedate_to_datetime(retry)
                            retry_at = parsed.isoformat() if parsed.tzinfo else None
                        except (TypeError, ValueError):
                            pass
                with self.store.db:
                    self.store.set("provider_restriction:" + provider, {"at": now(), "http_status": response.status, "retry_at": retry_at})
            body = response.body
            uncertain = response.status >= 500 or response.status == 202 or not isinstance(body, (dict, list))
            if isinstance(body, dict) and any(isinstance(v, dict) and str(v.get("status", "")).lower() in ("pending", "queued", "processing") for v in [body, *body.values()]):
                uncertain = True
            state = "uncertain" if uncertain else "complete" if response.status in (200, 201) else "rejected"
            provider_id = body.get("data", {}).get("id") if isinstance(body, dict) and isinstance(body.get("data"), dict) else None
            if provider == "rocketreach" and isinstance(body, dict) and body.get("id") and response.status in (200, 201, 202):
                provider_id = body["id"]
                state = "accepted" if body.get("status") != "complete" else "complete"
            self.store.result(action_key, state, str(provider_id) if provider_id else None, receipt)
            if state in ("uncertain", "rejected"):
                raise ProviderError("Native paid request " + state + "; HTTP " + str(response.status))
            return receipt
        except Exception as exc:
            actual = self.store.one("SELECT status FROM attempts WHERE idem_key=?", (action_key,))
            if actual and actual["status"] == "attempting":
                self.store.result(action_key, "uncertain", receipt={"error": type(exc).__name__, "send_authorized": False})
            raise

    def _destination(self, provider, url):
        base = BASES.get(provider)
        if not base or not url.startswith(base + "/") or urlparse(url).hostname != urlparse(base).hostname:
            raise ValueError("Provider credential destination differs")

    def native_unresolved(self, provider, url, payload):
        """Compare original native requests, never assume a new fingerprint means new work."""
        matches = []
        path = urlparse(url).path
        for resource in self.store.rows("SELECT * FROM resources WHERE provider=? AND kind='uncertain_paid_request'", (provider,)):
            native = json.loads(resource["data_json"])
            if provider == "apify":
                actor = path.removeprefix("/v2/acts/").removesuffix("/runs")
                original = native.get("input")
                if native.get("actor") != actor or not isinstance(original, dict):
                    continue
                same = original == payload
                left = {str(v).rstrip("/").lower() for v in original.get("urls", [])}
                right = {str(v).rstrip("/").lower() for v in payload.get("urls", [])}
                same = same or bool(left and right and left & right)
            elif provider == "sixtyfour":
                original = native.get("payload")
                if native.get("path") != path or not isinstance(original, dict):
                    continue
                same = original == payload
                before = original.get("lead", {}).get("linkedin")
                after = payload.get("lead", {}).get("linkedin")
                same = same or bool(before and after and before.rstrip("/").lower() == after.rstrip("/").lower())
            else:
                original = native.get("payload") or native.get("input")
                same = original == payload and native.get("path") in (None, path)
            if same:
                matches.append(resource)
        return matches

    def reconcile_resource(self, resource_key):
        resource = self.store.one("SELECT * FROM resources WHERE resource_key=? AND kind='uncertain_paid_request'", (resource_key,))
        if not resource:
            raise ValueError("Exact migrated paid request missing")
        if resource["provider"] == "apify" and resource.get("provider_id"):
            return self.apify_read(resource["provider_id"])
        return {"status": "uncertain", "resource_key": resource_key, "retry_allowed": False,
            "reason": "No supported native read handle or original status route is established"}

    def profile(self, profile_id):
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise ValueError("Exact native profile identifier required")
        params = {"profile_id": profile_id, "include_network_details": "false", "use_cache": "false"}
        return self._paid("triguna", "GET", "https://api.triguna.ai/v1/people/profile", params, credits=1, params=params)

    def company(self, company_id):
        if not isinstance(company_id, str) or not company_id.strip():
            raise ValueError("Exact native company identifier required")
        params = {"company_id": company_id, "use_cache": "false"}
        return self._paid("triguna", "GET", "https://api.triguna.ai/v1/companies/details", params, credits=1, params=params)

    def moltsets(self, operation, inputs):
        if operation not in ("search_people", "linkedin_to_business_email", "linkedin_to_mobile_phone"):
            raise ValueError("Unsupported MoltSets tool")
        receipt = self._paid("moltsets", "POST", "https://api.moltsets.com/api/v1/tools/" + operation, inputs)
        if receipt["body"].get("status") not in ("ok", "not_found"):
            raise ProviderError("MoltSets semantic result unavailable")
        return receipt

    def rocketreach(self, person):
        url = exact_profile(person)
        receipt = self._paid("rocketreach", "GET", "https://api.rocketreach.co/api/v2/person/lookup", {"linkedin_url": url}, params={"linkedin_url": url})
        body = receipt["body"]
        if not isinstance(body, dict) or not body.get("id"):
            raise ProviderError("RocketReach lookup handle missing")
        if body.get("status") not in ("complete", "completed"):
            check = self.read("rocketreach", "https://api.rocketreach.co/api/v2/person/checkStatus", {"ids": [body["id"]]})
            matches = [r for r in check if isinstance(r, dict) and r.get("id") == body["id"]] if isinstance(check, list) else []
            if len(matches) != 1 or matches[0].get("status") not in ("complete", "completed"):
                return {"status": "pending", "provider_id": body["id"], "send_authorized": False}
            body = matches[0]
        if (body.get("linkedin_url") or "").rstrip("/").lower() != url.rstrip("/").lower():
            raise ProviderError("RocketReach exact profile differs")
        return {**receipt, "body": body, "provider_id": body["id"]}

    def sixtyfour(self, operation, inputs):
        if operation == "search":
            size = inputs.get("page_size")
            if type(size) is not int or size <= 0 or inputs.get("max_results") != size or inputs.get("output_shape") != "raw" or inputs.get("mode") not in ("company", "people") or not isinstance(inputs.get("simple_filters"), dict):
                raise ValueError("Exact bounded SixtyFour search contract required")
            return self._paid("sixtyfour", "POST", "https://api.sixtyfour.ai/search/query", inputs, credits=size * 0.1)
        if operation == "find_email" and inputs.get("mode") == "PROFESSIONAL" and inputs.get("verify_emails") is False:
            return self._paid("sixtyfour", "POST", "https://api.sixtyfour.ai/find-email", inputs, credits=0.5)
        raise ValueError("Unsupported SixtyFour operation")

    def exa(self, inputs):
        if not isinstance(inputs.get('query'), str) or not inputs['query'].strip() or type(inputs.get('numResults')) is not int or not 1 <= inputs['numResults'] <= 10:
            raise ValueError('Exa needs a query and numResults from 1 to 10')
        return self._paid('exa', 'POST', 'https://api.exa.ai/search', inputs)

    def instantly_registry(self):
        body = self.read("instantly", INSTANTLY + "/supersearch-enrichment/integrations/providers")
        if not isinstance(body, list):
            raise ProviderError("Instantly integration registry schema differs")
        return {p["id"]: p for p in body if isinstance(p, dict) and p.get("id")}

    def instantly_email(self, person, provider_id, company=None):
        if provider_id not in EMAIL_ACTIONS:
            raise ValueError("Unsupported native email action")
        registry = self.instantly_registry()
        provider = registry.get(provider_id, {})
        action_id = EMAIL_ACTIONS[provider_id]
        actions = [a for a in provider.get("actions", []) if a.get("id") == action_id]
        if len(actions) != 1 or provider.get("requiresUserConnection") or provider.get("credentialSource") != "instantly_key":
            raise ValueError("Instantly-funded action unavailable")
        values = {"linkedin_url": exact_profile(person), "domain": person["domain"], "company_name": company or person.get("company")}
        # Actual source fields only. Full-name splitting is deliberately absent.
        projection = person.get("name_projection", {})
        if projection.get("status") == "projected" and projection.get("source_digest"):
            for field in ("first_name", "last_name"):
                value = person.get(field)
                if isinstance(value, str) and value.strip() and projection.get(field) == value:
                    values[field] = value
        action = actions[0]
        inputs = {i["key"]: values[i["key"]] for i in action.get("inputs", []) if values.get(i["key"])}
        if any(i.get("required") and i["key"] not in inputs for i in action.get("inputs", [])):
            return {"status": "projection_omitted", "reason": "Required native verified input unavailable", "provider_id": provider_id, "send_authorized": False}
        with self.store.db:
            self.store.event("research_consumer_inputs", person.get("person_key") or person["domain"], {"provider": provider_id, "action_id": action_id, "inputs": inputs, "name_projection": projection})
        plan = self.read("instantly", INSTANTLY + "/workspace-billing/plan-details")
        cost = provider.get("effectiveCostPerAction")
        available = plan.get("subscriptions", {}).get("credits", {}).get("available_credits")
        if available is None or not isinstance(cost, (int, float)) or available < cost:
            raise ValueError("Actual native account credit fields unavailable or insufficient")
        payload = {"provider_id": provider_id, "action_id": action_id, "inputs": inputs, "credential_source": "instantly_key"}
        receipt = self._paid("instantly", "POST", INSTANTLY + "/supersearch-enrichment/integrations/run", payload, credits=cost)
        if receipt["body"].get("success") is False:
            return {**receipt, "status": "not_found"}
        emails = work_emails(receipt["body"].get(action.get("outputColumn")), person["domain"])
        return {**receipt, "status": "found" if len(emails) == 1 else "identity_review" if len(emails) > 1 else "not_found", "emails": emails}

    def apify_start(self, actor, inputs):
        if actor not in ACTORS:
            raise ValueError("Unregistered Apify actor")
        receipt = self._paid("apify", "POST", APIFY + "/acts/" + actor + "/runs", inputs,
            params={"restartOnError": "false", "timeout": 1800})
        run = receipt["body"].get("data", {})
        if not run.get("id"):
            self.store.result(receipt["request_key"], "uncertain", receipt=receipt)
            raise ProviderError("Apify run ID missing, never resubmit")
        self.store.result(receipt["request_key"], "accepted", str(run["id"]), receipt)
        return run

    def apify_read(self, run_id):
        run = self.read("apify", APIFY + "/actor-runs/" + quote(str(run_id), safe="")).get("data", {})
        if run.get("id") != run_id:
            raise ProviderError("Apify run identity differs")
        if run.get("status") != "SUCCEEDED":
            return {"status": run.get("status", "unknown"), "run_id": run_id, "complete": False}
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            raise ProviderError("Apify dataset ID missing")
        items, offset, seen = [], 0, set()
        while True:
            batch = self.read("apify", APIFY + "/datasets/" + quote(dataset_id, safe="") + "/items", {"clean": "true", "format": "json", "offset": offset, "limit": 1000})
            if not isinstance(batch, list):
                raise ProviderError("Apify dataset schema differs")
            page_hash = digest(batch)
            if batch and page_hash in seen:
                raise ProviderError("Apify dataset pagination incomplete")
            seen.add(page_hash)
            items.extend(batch)
            if len(batch) < 1000:
                return {"status": "complete", "complete": True, "run_id": run_id, "dataset_id": dataset_id,
                    "source_started_at": run.get("startedAt"), "usage_usd": run.get("usageTotalUsd"), "items": items, "send_authorized": False}
            offset += len(batch)

    def validate_email(self, email):
        if not isinstance(email, str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Exact email required")
        # The API requires its private key in the query, but the durable payload excludes it.
        require_research_enabled(self.store)
        key = self.http.credential("zerobounce")
        prior=self.store.rows("SELECT * FROM attempts WHERE channel='research:zerobounce' AND (recipient=? OR json_extract(payload_json,'$.email')=?) ORDER BY rowid DESC",(email,email))
        if any(a['status']!='complete' for a in prior):
            raise ValueError('Unknown email validation requires reconciliation; do not renew or resubmit')
        latest=prior[0] if prior else None
        if latest:
            receipt=json.loads(latest['receipt_json'])
            from engine.validation import fresh
            if fresh(receipt.get('at'),7*86400): return receipt
        fingerprint = digest(["zerobounce", email, len(prior)])
        attempt = self.store.one("SELECT * FROM attempts WHERE idem_key=?", (fingerprint,))
        if attempt:
            if attempt['status']!='complete':
                raise ValueError("Unknown email validation requires reconciliation")
            return json.loads(attempt["receipt_json"])
        self.store.reserve("research:zerobounce", fingerprint, email.rsplit("@", 1)[-1], "", {"email": email}, fingerprint)
        try:
            require_research_enabled(self.store)
            response = self.http.request("GET", "https://api.zerobounce.net/v2/validate", params={"api_key": key, "email": email, "ip_address": ""})
            body = response.require()
            if not isinstance(body, dict) or (body.get("address") or "").lower() != email.lower():
                raise ProviderError("Email validation identity differs")
            receipt = {**response.receipt(), "email": email, "valid": body.get("status") == "valid", "native_status":body.get('status'),
                'native_sub_status':body.get('sub_status'), "send_authorized": False,'request_key':fingerprint}
            self.store.result(fingerprint, "complete", receipt=receipt)
            return receipt
        except Exception as exc:
            self.store.result(fingerprint, "uncertain", receipt={"error": type(exc).__name__})
            raise

    def validation_balance(self):
        response=self.http.request('GET','https://api.zerobounce.net/v2/getcredits',params={'api_key':self.http.credential('zerobounce')})
        raw=response.require(); credits=raw.get('Credits')
        if isinstance(credits,str) and credits.isdigit(): credits=int(credits)
        if type(credits) is not int or credits<0: raise ProviderError('ZeroBounce did not confirm a valid credit balance')
        return {'provider':'zerobounce','credits_remaining':credits,'observed_at':now(),'outreach_sent':0}


def exact_profile(person):
    value = person.get("profile") or person.get("linkedin")
    parsed = urlparse(value or "")
    if parsed.scheme != "https" or parsed.hostname not in ("linkedin.com", "www.linkedin.com") or not re.fullmatch(r"/in/[^/]+/?", parsed.path):
        raise ValueError("Exact sourced LinkedIn profile required")
    return "https://www.linkedin.com" + parsed.path.rstrip("/")


def work_emails(value, domain):
    found = set()
    if isinstance(value, str) and re.fullmatch(r"[^\s@]+@" + re.escape(domain), value.strip().lower()):
        found.add(value.strip().lower())
    elif isinstance(value, list):
        for item in value:
            found.update(work_emails(item, domain))
    elif isinstance(value, dict):
        for key in ("email", "emails", "work_email", "workEmail", "email_address", "address", "data", "result", "results"):
            if key in value:
                found.update(work_emails(value[key], domain))
    return sorted(found)


from datetime import datetime, timezone
import json
import re
from urllib.parse import urlparse

from engine.database import digest, encode, now


def tracked_input(profiles):
    if not profiles or any(not re.fullmatch(r"https://(?:www\.)?linkedin\.com/in/[^/?#]+/?", p) for p in profiles):
        raise ValueError("Explicit tracked public person profiles required")
    return {"targetUrls": profiles, "maxPosts": 0, "postedLimit": "month", "includeReposts": False,
        "includeQuotePosts": True, "scrapeComments": True, "maxComments": 100, "commentsPostedLimit": "24h", "scrapeReactions": False}


def keyword_input(queries):
    if not queries or any(not isinstance(q, str) or not q.strip() for q in queries):
        raise ValueError("Explicit configured relevance queries required")
    return {"searchQueries": queries, "maxPosts": 0, "postedLimit": "24h", "sortBy": "date", "profileScraperMode": "short",
        "scrapeReactions": False, "scrapeComments": True, "maxComments": 50, "commentsPostedLimit": "24h", "commentsProfileScraperMode": "short"}


class Signals:
    def __init__(self, store, http=None):
        self.store, self.research = store, Research(store, http)

    def start_scan(self, kind, values):
        if kind == "tracked":
            actor, payload = "harvestapi~linkedin-profile-posts", tracked_input(values)
        elif kind == "keywords":
            actor, payload = "harvestapi~linkedin-post-search", keyword_input(values)
        else:
            raise ValueError("Unsupported Radar scan source")
        run = self.research.apify_start(actor, payload)
        with self.store.db:
            self.store.set("radar_run:" + kind, {"run_id": run["id"], "actor": actor, "input": payload, "source_started_at": run.get("startedAt")})
        return {"status": "running", "run_id": run["id"], "outreach_authorized": False}

    def read_scan(self, run_id):
        receipt = self.research.apify_read(run_id)
        if receipt.get("complete") is not True:
            return receipt
        posts = {str(p.get("id")): p for p in receipt["items"] if isinstance(p, dict) and p.get("type") == "post"}
        accepted = []
        stamp = datetime.now(timezone.utc)
        for item in receipt["items"]:
            if not isinstance(item, dict) or item.get("type") != "comment":
                continue
            actor = item.get("actor") or {}
            url = actor.get("linkedinUrl") or ""
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in ("linkedin.com", "www.linkedin.com") or not re.fullmatch(r"/in/[^/]+/?", parsed.path):
                continue
            profile = "https://www.linkedin.com" + parsed.path.rstrip("/").lower()
            post = posts.get(str(item.get("postId")))
            if not post:
                continue  # Exact host/post binding is required.
            host = post.get("author", {}).get("publicIdentifier", "").lower()
            if host and profile.rsplit("/", 1)[-1] == host:
                continue
            text = item.get("commentary")
            if not isinstance(text, str) or len(text.strip()) < 12:
                continue
            try:
                created = datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00"))
                age = (stamp - created).total_seconds()
                if created.tzinfo is None or not 0 <= age <= 86400:
                    continue
            except (KeyError, TypeError, ValueError):
                continue
            if self.store.one("SELECT signal_key FROM signals WHERE kind='commenter_seen' AND signal_key=?", (digest(profile),)):
                continue
            source_key = str(item.get("id") or digest(item))
            value = {"provider": "apify", "run_id": run_id, "dataset_id": receipt["dataset_id"], "source_started_at": receipt.get("source_started_at"),
                "profile": profile, "name": actor.get("name"), "title_hint": actor.get("position"), "comment": text,
                "comment_id": source_key, "comment_created_at": item["createdAt"], "post_id": str(item["postId"]), "post_url": post.get("linkedinUrl"),
                "native_comment": item, "native_post": post, "status": "needs_relevance_and_identity", "outreach_authorized": False}
            with self.store.db:
                self.store.record("radar.apify", source_key, "comment", value)
                self.store.db.execute("INSERT OR REPLACE INTO signals VALUES (?,?,?,?,?)", ("radar:" + source_key, "", "public_comment", item["createdAt"], encode(value)))
            accepted.append(value)
        return {"status": "source_complete", "complete": True, "run_id": run_id, "comments": accepted, "observed_at": now(), "outreach_authorized": False}

    def accept_quote(self, signal_key, quote):
        row = self.store.one("SELECT * FROM signals WHERE signal_key=? AND kind='public_comment'", (signal_key,))
        if not row:
            raise ValueError("Exact native comment signal missing")
        value = json.loads(row["data_json"])
        if not isinstance(quote, str) or not 12 <= len(quote) <= 160 or "?" in quote or quote not in value["comment"]:
            raise ValueError("Exact substantive native quote required")
        return {"profile": value["profile"], "quote": quote, "comment_id": value["comment_id"], "outreach_authorized": False,
                "status": "requires_current_employer_role_email_and_suppression_checks"}

    def refresh(self):
        config = self.store.setting("radar", {})
        results = {}
        for kind in ("tracked", "keywords"):
            saved = self.store.setting("radar_run:" + kind, {})
            if saved.get("run_id"):
                results[kind] = self.read_scan(saved["run_id"])
            else:
                results[kind] = {"status": "not_started", "reason": "No accepted native run ID; scan launch is an explicit paid action"}
        receipt = {"observed_at": now(), "sources": results, "complete": all(r.get("complete") is True for r in results.values())}
        with self.store.db:
            self.store.set("radar_refresh", receipt)
        return receipt


def refresh(store, http=None):
    return Signals(store, http).refresh()
