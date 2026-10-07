"""Native booked demos, inbound forms and delegated calendar records; attendance is separate."""
from datetime import datetime, timedelta, timezone
import json
import re
from urllib.parse import quote, urlencode, urlparse

from engine.channels.email import delegated_token
from engine.http_client import HttpClient, ProviderError
from engine.database import encode, now


class Meetings:
    def __init__(self, store, http=None):
        self.store, self.http = store, http or HttpClient(store)

    def _paged(self, url, headers, params, field, cursor_kind="after"):
        rows, seen = [], set()
        current = dict(params)
        while True:
            body = self.http.request("GET", url, headers=headers, params=current).require()
            if not isinstance(body, dict) or not isinstance(body.get(field), list):
                raise ProviderError("Native booking inventory schema differs")
            rows.extend(body[field])
            if cursor_kind == "page_token":
                cursor = body.get("pagination", {}).get("next_page_token")
            elif cursor_kind == "pageToken":
                cursor = body.get("nextPageToken")
            else:
                cursor = body.get("paging", {}).get("next", {}).get("after")
            if not cursor:
                return rows
            if cursor in seen:
                raise ProviderError("Native booking pagination incomplete")
            seen.add(cursor)
            current[cursor_kind] = cursor

    def _save(self, source, key, recipient, stamp, state, native):
        recipient = (recipient or "").strip().lower()
        if "@" not in recipient:
            raise ProviderError("Native booking recipient is absent")
        domain = recipient.rsplit("@", 1)[-1]
        self.store.record(source, key, state, native)
        self.store.db.execute("INSERT OR REPLACE INTO bookings VALUES (?,?,?,?,?,?)", (key, recipient, domain, stamp, state, encode(native)))

    def calendly(self):
        config = self.store.setting("calendly_identity", {})
        if not all(config.get(k) for k in ("email", "user_uri", "organization_uri", "since", "event_type_uris")):
            raise ValueError("Exact owning Calendly identity and programme event types are not configured")
        headers = {"Authorization": "Bearer " + self.http.credential(config.get("credential", "calendly"))}
        account = self.http.request("GET", "https://api.calendly.com/users/me", headers=headers).require().get("resource", {})
        if (account.get("uri") != config["user_uri"] or account.get("email", "").lower() != config["email"].lower()
                or account.get("current_organization") != config["organization_uri"]):
            raise ProviderError("Actual Calendly user or organization differs")
        types = self._paged("https://api.calendly.com/event_types", headers, {"organization": config["organization_uri"], "count": 100}, "collection", "page_token")
        by_uri = {t.get("uri"): t for t in types}
        if not set(config["event_type_uris"]) <= set(by_uri):
            raise ProviderError("Required programme event type inventory incomplete")
        events = self._paged("https://api.calendly.com/scheduled_events", headers,
            {"organization": config["organization_uri"], "count": 100, "sort": "start_time:desc", "min_start_time": config["since"]}, "collection", "page_token")
        count = 0
        for event in events:
            if event.get("event_type") not in config["event_type_uris"]:
                continue
            uri = event.get("uri", "")
            if not re.fullmatch(r"https://api\.calendly\.com/scheduled_events/[A-Za-z0-9-]+", uri) or not event.get("start_time"):
                raise ProviderError("Exact Calendly event identity/time missing")
            invitees = self._paged(uri + "/invitees", headers, {"count": 100}, "collection", "page_token")
            for invitee in invitees:
                identity = invitee.get("uri", "")
                if not identity.startswith(uri + "/invitees/"):
                    raise ProviderError("Invitee belongs to a different event")
                state = "canceled" if event.get("status") == "canceled" or invitee.get("status") == "canceled" else "booked" if event.get("status") == "active" and invitee.get("status") == "active" else "unknown"
                value = {"provider": "calendly", "identity": identity, "event": event, "invitee": invitee,
                    "event_type": by_uri[event["event_type"]], "demo_proven": True, "attended": None, "source_observed_at": now()}
                with self.store.db:
                    self._save("calendly.bookings", identity, invitee.get("email"), event["start_time"], state, value)
                count += 1
        return {"complete": True, "observed_at": now(), "records": count, "owner": config["email"], "organization_uri": config["organization_uri"]}

    def forms(self):
        config = self.store.setting("hubspot_demo_forms", {})
        if not config.get("ids") or not config.get("since"):
            raise ValueError("Exact demo form IDs and baseline boundary are not configured")
        headers = {"Authorization": "Bearer " + self.http.credential("hubspot")}
        forms = self._paged("https://api.hubapi.com/marketing/v3/forms", headers, {"limit": 100}, "results")
        by_id = {f.get("id"): f for f in forms}
        if not set(config["ids"]) <= set(by_id):
            raise ProviderError("Required demo forms are missing from native inventory")
        lower = datetime.fromisoformat(config["since"].replace("Z", "+00:00"))
        count = 0
        for form_id in config["ids"]:
            rows = self._paged("https://api.hubapi.com/form-integrations/v1/submissions/forms/" + quote(form_id, safe=""), headers, {"limit": 50}, "results")
            for row in rows:
                stamp = datetime.fromtimestamp(row["submittedAt"] / 1000, timezone.utc)
                if stamp < lower:
                    continue
                if not row.get("conversionId"):
                    raise ProviderError("Native form submission ID missing")
                values = {f["name"]: f["value"] for f in row.get("values", [])}
                if not values.get("email"):
                    raise ProviderError("Native form submission email absent")
                value = {"provider": "hubspot", "form_id": form_id, "form": by_id[form_id], "native": row, "attended": None}
                with self.store.db:
                    self._save("hubspot.forms", "hubspot:form:" + row["conversionId"], values["email"], stamp.isoformat(), "demo_requested", value)
                count += 1
        return {"complete": True, "observed_at": now(), "records": count, "form_ids": config["ids"]}

    def calendars(self):
        config = self.store.setting("google_calendars", {})
        if not config.get("mailboxes") or not config.get("since"):
            raise ValueError("Delegated calendar mailbox scope is not configured")
        through = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        coverage = {}
        for mailbox in config["mailboxes"]:
            token = delegated_token(self.http, mailbox, config.get('oauth_scope', "https://www.googleapis.com/auth/calendar.readonly"))
            events = self._paged("https://www.googleapis.com/calendar/v3/calendars/primary/events",
                {"Authorization": "Bearer " + token}, {"timeMin": config["since"], "timeMax": through, "singleEvents": "true", "showDeleted": "true", "maxResults": 2500}, "items", "pageToken")
            for event in events:
                if not event.get("id"):
                    raise ProviderError("Native calendar event ID missing")
                prefix = "google:" + mailbox + ":" + event["id"] + ":"
                attendees = event.get("attendees", [])
                if event.get("status") == "cancelled" and not attendees:
                    prior = self.store.rows("SELECT * FROM bookings WHERE substr(booking_key,1,?)=?", (len(prefix), prefix))
                    with self.store.db:
                        for old in prior:
                            value = json.loads(old["data_json"])
                            value["cancellation"] = event
                            self._save("google.calendar", old["booking_key"], old["recipient"], old["at"], "canceled", value)
                    continue
                for attendee in attendees:
                    recipient = (attendee.get("email") or "").lower()
                    if "@" not in recipient or recipient.rsplit("@", 1)[-1] in self.store.setting("internal_domains", []):
                        continue
                    start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
                    if not start:
                        continue
                    state = "canceled" if event.get("status") == "cancelled" or attendee.get("responseStatus") == "declined" else "calendar_meeting"
                    with self.store.db:
                        self._save("google.calendar", prefix + recipient, recipient, start, state,
                            {"provider": "google_calendar", "mailbox": mailbox, "event": event, "attendee": attendee, "attended": None, "demo_proven": False})
            coverage[mailbox] = {"complete": True, "events": len(events)}
        return {"complete": True, "observed_at": now(), "since": config["since"], "through": through, "future_horizon_days": 365, "calendars": coverage}

    def _salesforce(self):
        values = {}
        for line in self.http.credential_file('salesforce').read_text().splitlines():
            match = re.match(r'^(client_id|client_secret|refresh_token|instance_url)\s*[:=]\s*(.+)$', line.strip())
            if match:
                values[match[1]] = match[2].strip('"\'')
        base = values.get('instance_url', '').rstrip('/')
        if not (urlparse(base).hostname or '').endswith('.salesforce.com'):
            raise ProviderError('Salesforce credential destination differs')
        form = {'grant_type': 'refresh_token', **{k: values[k] for k in ('client_id', 'client_secret', 'refresh_token') if values.get(k)}}
        auth = self.http.request('POST', base + '/services/oauth2/token',
            headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=urlencode(form).encode()).require()
        if auth.get('instance_url', '').rstrip('/') != base or not auth.get('access_token'):
            raise ProviderError('Salesforce authenticated instance differs')
        headers = {'Authorization': 'Bearer ' + auth['access_token']}
        identity_url = auth.get('id', '')
        parsed = urlparse(identity_url)
        if parsed.scheme != 'https' or not (parsed.hostname or '').endswith('.salesforce.com') or not parsed.path.startswith('/id/'):
            raise ProviderError('Salesforce identity destination differs')
        identity = self.http.request('GET', identity_url, headers=headers).require()
        expected = self.store.setting('salesforce_owner_email', '')
        if not expected or (identity.get('email') or '').lower() != expected.lower():
            raise ProviderError('Salesforce authenticated owner differs from your configured owner')
        with self.store.db:
            self.store.set('salesforce_identity', {'instance': base, 'email': identity['email'],
                'organization_id': identity.get('organization_id'), 'observed_at': now()})
        return base, headers

    def _sf_query(self, base, headers, query):
        rows, seen, url = [], set(), base + '/services/data/v61.0/query'
        params = {'q': query}
        expected = None
        while url:
            if url in seen or not url.startswith(base + '/services/data/'):
                raise ProviderError('Salesforce pagination identity differs')
            seen.add(url)
            body = self.http.request('GET', url, headers=headers, params=params).require()
            if not isinstance(body.get('records'), list) or not isinstance(body.get('done'), bool):
                raise ProviderError('Salesforce query schema differs')
            if expected is None:
                expected = body.get('totalSize')
            rows.extend(body['records'])
            if body['done']:
                if len(rows) != expected:
                    raise ProviderError('Salesforce query count differs')
                return rows
            cursor = body.get('nextRecordsUrl')
            if not isinstance(cursor, str) or not cursor.startswith('/services/data/'):
                raise ProviderError('Salesforce query cursor unavailable')
            url, params = base + cursor, None

    def salesforce_deals(self):
        from engine.validation import domain
        base, headers = self._salesforce()
        rows = self._sf_query(base, headers,
            'SELECT Id,Name,StageName,AccountId,Account.Name,Account.Website,LastModifiedDate FROM Opportunity WHERE IsClosed=false')
        observed, unmatched = now(), []
        with self.store.db:
            for row in rows:
                if not row.get('Id'):
                    raise ProviderError('Salesforce opportunity ID missing')
                account = row.get('Account') or {}
                employer = domain(account.get('Website'))
                value = {'id': row['Id'], 'name': account.get('Name'), 'domain': employer,
                         'observed_at': observed, 'native': row}
                self.store.record('live.salesforce.open_deals', row['Id'], 'open_deal', value)
                if employer:
                    self.store.db.execute('INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?,?,?)',
                        ('domain', employer, 'Current Salesforce open deal', 'live.salesforce.open_deals', observed, encode(value)))
                else:
                    unmatched.append(row['Id'])
            receipt = {'complete_inventory': True, 'observed_at': observed, 'records': len(rows),
                       'unresolved_domain_ids': unmatched, 'identity': self.store.setting('salesforce_identity')}
            self.store.set('salesforce_deals_refresh', receipt)
        return receipt

    def customers(self):
        from engine.validation import normalized, domain
        from engine.database import digest
        config = self.store.setting('revenue', {})
        if not all(config.get(k) for k in ('mailbox','sheet_id','range')):
            raise ValueError('Your current revenue mailbox, sheet and range are not configured')
        token = delegated_token(self.http, config['mailbox'], 'https://www.googleapis.com/auth/spreadsheets.readonly')
        sheet_id = config['sheet_id']
        body = self.http.request('GET', 'https://sheets.googleapis.com/v4/spreadsheets/' + sheet_id
            + '/values/' + quote(config['range'], safe=''),
            headers={'Authorization': 'Bearer ' + token}, params={'valueRenderOption': 'UNFORMATTED_VALUE'}).require()
        rows = body.get('values', [])
        if config.get('format')=='customer_domains':
            if not rows or rows[0] != ['name','domain','status']:
                raise ProviderError('Current customer sheet needs exact name,domain,status columns')
            observed=now(); customers=[]
            for row in rows[1:]:
                if not any(row): continue
                if len(row)!=3 or row[2] not in ('current_customer','former_customer'):
                    raise ProviderError('Current customer status is missing or unknown in your actual sheet')
                if row[2]=='former_customer': continue
                employer=domain(row[1])
                if not row[0] or not employer: raise ProviderError('Current customer identity needs actual name and domain')
                customers.append({'name':row[0],'domain':employer,'observed_at':observed,'native_row':row})
            with self.store.db:
                self.store.record('live.revenue.sheet',sheet_id,'current_customer_inventory',body)
                self.store.db.execute("DELETE FROM source_records WHERE source='live.revenue.customers'")
                for index,value in enumerate(customers):
                    self.store.record('live.revenue.customers',index,'customer',value)
                    self.store.db.execute('INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?,?,?)',
                        ('domain',value['domain'],'Current customer','live.revenue.customers',observed,encode(value)))
                receipt={'complete_inventory':True,'observed_at':observed,'source':config['range'],'sheet_id':sheet_id,
                    'rows_read':len(rows),'current_customers':len(customers),'unresolved_domain_rows':[],
                    'format':'customer_domains','current_source_note':'Actual configured customer-status sheet; no revenue inferred'}
                self.store.set('customers_refresh',receipt)
            return receipt
        if not rows or rows[0][:4] != ['Account', 'Previous ARR', 'ARR', 'MRR']:
            raise ProviderError('Current revenue sheet columns differ')
        from zoneinfo import ZoneInfo
        month = datetime.now(timezone.utc).astimezone(ZoneInfo('America/New_York')).strftime('%Y-%m')
        indices = [i for i, value in enumerate(rows[0]) if isinstance(value, (int, float))
                   and (datetime(1899, 12, 30) + timedelta(days=value)).strftime('%Y-%m') == month]
        if len(indices) != 1:
            raise ProviderError('Current recognized revenue month is missing or ambiguous')
        accounts = {}
        for account in self.store.rows('SELECT domain,name FROM accounts'):
            accounts.setdefault(normalized(account['name']), set()).add(account['domain'])
        observed, count, unmatched = now(), 0, []
        with self.store.db:
            self.store.record('live.revenue.sheet', sheet_id, 'revenue_inventory', body)
            self.store.db.execute("DELETE FROM source_records WHERE source='live.revenue.customers'")
            for index, row in enumerate(rows[1:], 2):
                mr = row[3] if len(row) > 3 else 0
                recognized = row[indices[0]] if len(row) > indices[0] else 0
                if not any(isinstance(v, (int, float)) and v > 0 for v in (mr, recognized)):
                    continue
                name = row[0]; domains = accounts.get(normalized(name), set())
                employer = next(iter(domains)) if len(domains) == 1 else ''
                value = {'name': name, 'domain': employer, 'observed_at': observed, 'month': month,
                         'row': index, 'mrr': mr, 'recognized_revenue': recognized, 'native_row': row}
                self.store.record('live.revenue.customers', index, 'customer', value)
                if employer:
                    self.store.db.execute('INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?,?,?)',
                        ('domain', domain(employer), 'Current revenue relationship', 'live.revenue.customers', observed, encode(value)))
                else:
                    unmatched.append(index)
                count += 1
            receipt = {'complete_inventory': True, 'observed_at': observed, 'source': config['range'],
                       'sheet_id': sheet_id, 'sheet_digest': digest(body), 'recognized_month': month,
                       'rows_read': len(rows), 'positive_revenue_relationships': count, 'unresolved_domain_rows': unmatched,
                       'current_customer_claims_require_churn_check': True}
            self.store.set('customers_refresh', receipt)
        return receipt

    def hubspot_deals(self):
        from engine.validation import domain
        headers = {'Authorization': 'Bearer ' + self.http.credential('hubspot')}
        pipelines = self.http.request('GET', 'https://api.hubapi.com/crm/v3/pipelines/deals', headers=headers).require()
        closed = {}
        for pipeline in pipelines.get('results', []):
            for stage in pipeline.get('stages', []):
                value = stage.get('metadata', {}).get('isClosed')
                if value in (True, False, 'true', 'false'):
                    closed[(pipeline['id'], stage['id'])] = value in (True, 'true')
        deals = self._paged('https://api.hubapi.com/crm/v3/objects/deals', headers,
            {'limit': 100, 'archived': 'false', 'properties': 'dealname,dealstage,pipeline', 'associations': 'companies'}, 'results')
        company_ids = sorted({str(company['id']) for deal in deals
            if closed.get((deal.get('properties', {}).get('pipeline'), deal.get('properties', {}).get('dealstage'))) is not True
            for company in deal.get('associations', {}).get('companies', {}).get('results', [])})
        companies = []
        for offset in range(0, len(company_ids), 100):
            ids = company_ids[offset:offset + 100]
            body = self.http.request('POST', 'https://api.hubapi.com/crm/v3/objects/companies/batch/read',
                headers=headers, json_body={'properties': ['name', 'domain'], 'inputs': [{'id': key} for key in ids]}).require()
            if body.get('status') != 'COMPLETE' or not isinstance(body.get('results'), list):
                raise ProviderError('HubSpot exact associated company batch is incomplete')
            if any(str(row.get('id')) not in ids for row in body['results']):
                raise ProviderError('HubSpot associated company identity differs')
            companies.extend(body['results'])
        by_id = {str(row['id']): row for row in companies}
        observed, linked, unmatched = now(), 0, []
        with self.store.db:
            for deal in deals:
                props = deal.get('properties', {})
                state = closed.get((props.get('pipeline'), props.get('dealstage')))
                if state is True:
                    continue
                associations = deal.get('associations', {}).get('companies', {})
                if associations.get('paging'):
                    unmatched.append(deal['id'])
                    continue
                company_rows = [by_id.get(str(row['id'])) for row in associations.get('results', [])]
                if not company_rows or any(row is None for row in company_rows):
                    unmatched.append(deal['id'])
                    continue
                for company in company_rows:
                    company_props = company.get('properties', {})
                    employer = domain(company_props.get('domain'))
                    value = {'id': deal['id'], 'name': company_props.get('name'), 'domain': employer,
                             'stage_verified_open': state is False, 'observed_at': observed,
                             'native_deal': deal, 'native_company': company}
                    self.store.record('live.hubspot.open_deals', deal['id'] + ':' + company['id'], 'open_deal', value)
                    if employer:
                        reason = 'Current HubSpot open deal' if state is False else 'Unclassified HubSpot deal'
                        self.store.db.execute('INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?,?,?)',
                            ('domain', employer, reason, 'live.hubspot.open_deals', observed, encode(value)))
                        linked += 1
                    else:
                        unmatched.append(deal['id'])
            receipt = {'complete_inventory': True, 'observed_at': observed, 'deals': len(deals),
                       'companies': len(companies), 'linked_exclusions': linked,
                       'unresolved_domain_ids': sorted(set(unmatched))}
            self.store.set('hubspot_deals_refresh', receipt)
        return receipt

    def attendance(self):
        """Read exact existing HubSpot meeting outcomes; no inferred attendance."""
        headers = {"Authorization": "Bearer " + self.http.credential("hubspot")}
        since = self.store.setting("attendance_since")
        if not since:
            raise ValueError("Actual attendance baseline boundary missing")
        payload = {"filterGroups": [{"filters": [{"propertyName": "hs_meeting_start_time", "operator": "GTE", "value": str(int(datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp() * 1000))}]}], "properties": ["hs_meeting_outcome", "hs_meeting_start_time", "hs_meeting_end_time", "hs_meeting_title"], "limit": 100}
        rows, seen = [], set()
        while True:
            result = self.http.request("POST", "https://api.hubapi.com/crm/v3/objects/meetings/search", headers=headers, json_body=payload).require()
            if not isinstance(result.get("results"), list):
                raise ProviderError("Native meeting outcome inventory unavailable")
            rows.extend(result["results"])
            cursor = result.get("paging", {}).get("next", {}).get("after")
            if not cursor:
                break
            if cursor in seen:
                raise ProviderError("HubSpot attendance pagination incomplete")
            seen.add(cursor)
            payload["after"] = cursor
        # Read outcomes durably, but no association join means attendance remains unknown.
        with self.store.db:
            for row in rows:
                if not row.get("id"):
                    raise ProviderError("Native HubSpot meeting ID missing")
                self.store.record("hubspot.attendance", row["id"], "meeting_outcome", row)
        return {"complete": False, "observed_at": now(), "native_meetings": len(rows), "reason": "Exact meeting/contact association and email/start join is not wired; attendance remains unknown"}

    def refresh(self):
        results, failures = {}, {}
        sources = self.store.setting('booking_sources', ['calendly', 'hubspot', 'google_calendar'])
        calls = {'calendly':self.calendly, 'hubspot':self.forms, 'google_calendar':self.calendars}
        if not sources or any(s not in calls for s in sources):
            return {'complete':False,'observed_at':now(),'reason':'Configure at least one actual booking source'}
        for source in sources:
            try:
                results[source] = calls[source]()
            except Exception as exc:
                failures[source] = type(exc).__name__
        receipt = {"complete": not failures and len(results) == len(sources), "observed_at": now(),
                   "sources": results, "failures": failures,
                   "coverage": "Configured booking sources only", 'configured_sources':sources}
        with self.store.db:
            self.store.set("bookings_refresh", receipt)
        return receipt


def refresh(store, http=None):
    return Meetings(store, http).refresh()
