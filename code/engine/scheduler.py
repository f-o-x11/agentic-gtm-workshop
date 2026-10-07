"""One owner executes ready actions; attempts survive crashes before readback."""
import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone
import uuid
from zoneinfo import ZoneInfo
from engine.database import encode, now

MODULES = {'email': 'engine.channels.email', 'gift': 'engine.channels.gifts',
           'linkedin': 'engine.channels.social', 'linkedin_message': 'engine.channels.social'}
CHANNELS = {'email': 'email', 'gmail': 'email', 'instantly': 'email', 'initial_email': 'email',
            'gift': 'gift', 'linkedin': 'social', 'linkedin_invitation': 'social',
            'linkedin_message': 'social'}
ZONE = ZoneInfo('America/New_York')
HOURS = tuple(range(8, 18))


class UnrecordedDispatch(RuntimeError):
    """An adapter claimed success without the required durable reservation."""


def _clock():
    return datetime.now(timezone.utc).astimezone(ZONE)


def _timestamp(value):
    try:
        stamp = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return stamp.astimezone(ZONE) if stamp.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def _positive(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def _targets(store):
    from engine.checks import policy
    authority, local = policy(store)
    config = store.setting('hourly_pacing', local.get('hourly_pacing', {}))
    requested = config.get('daily_targets', {}) if isinstance(config, dict) else {}
    requested = requested if isinstance(requested, dict) else {}
    consent = {r['email'].strip().lower(): r for r in store.rows('SELECT * FROM sender_consent')}
    senders = {}
    authorized = authority.get('senders', {})
    for sender, cap in authorized.items() if isinstance(authorized, dict) else ():
        sender = sender.strip().lower()
        row = consent.get(sender, {})
        allowed = min(_positive(cap), _positive(row.get('daily_cap'))) if row.get('enabled') == 1 else 0
        if allowed:
            senders[sender] = allowed
    email_cap = min(sum(senders.values()), _positive(authority.get('daily_email_ceiling', sum(senders.values()))))
    targets = {'email': min(_positive(requested.get('email', email_cap)), email_cap),
               'gift': min(_positive(requested.get('gift', 0)), 20)
                       if authority.get('gift_fulfillment') == 'automatic' else 0,
               'social': _positive(requested.get('social', 0))
                         if authority.get('linkedin_dispatch') == 'automatic' else 0}
    return targets, senders


def _plan_name(at):
    return 'hourly_pacing:' + at.date().isoformat()


def _plan(store, at, create=False):
    targets, senders = _targets(store)
    plan = store.setting(_plan_name(at), {})
    if not plan and create:
        plan = {'date': at.date().isoformat(), 'timezone': 'America/New_York',
                'hours': list(HOURS), 'targets': targets, 'senders': senders, 'claims': {}}
        with store.db:
            store.set(_plan_name(at), plan)
            store.event('hourly_daily_plan', plan['date'], {'targets': targets, 'hours': list(HOURS)},
                        key='hourly_plan:' + plan['date'], at=at.isoformat())
    if not isinstance(plan, dict) or plan.get('date') != at.date().isoformat():
        return {}, {}, {}
    return plan, targets, senders


def _chunk(target, hour):
    index = hour - HOURS[0]
    return target * (index + 1) // 10 - target * index // 10


def attempt_clock(row, claim=None, store=None):
    """Only source-bound ledger facts can classify inbound events or date imports."""
    if claim and _timestamp(claim.get('at')):
        return claim['at'], 'v5_hourly_claim'
    if store and store.one('SELECT action_key FROM actions WHERE action_key=?', (row['idem_key'],)):
        return row.get('at'), 'v5_durable_reservation'
    source = store.one("SELECT data_json,digest FROM source_records WHERE source='postgres.touch_ledger' AND record_key=?",
                       (row['idem_key'],)) if store else None
    if not source:
        return row.get('at'), 'v5_durable_reservation'
    from engine.database import digest
    original = json.loads(source['data_json'])
    if digest(original) != source['digest'] or original.get('idem_key') != row['idem_key']:
        return None, 'undated_commitment_hold'
    if original.get('direction') == 'inbound':
        return None, 'inbound_event'
    if _timestamp(original.get('attempt_started_at')):
        return original['attempt_started_at'], 'canonical_attempt_started_at'
    payload = json.loads(row.get('payload_json') or '{}')
    native = payload.get('native')
    if isinstance(native, dict) and native.get('ledger_key') == row['idem_key']:
        bound = store.one("SELECT digest FROM source_records WHERE source LIKE 'native.%' AND digest=? LIMIT 1", (digest(native),))
        if bound:
            for field in ('attempted_at', 'at', 'sent_at', 'committed_at'):
                if _timestamp(native.get(field)):
                    return native[field], 'native.' + field
    proof = json.loads(row.get('receipt_json') or '{}').get('quota_clock', {})
    bound = store.one('SELECT data_json,digest FROM source_records WHERE source=? AND record_key=?',
                      (proof.get('source'), proof.get('record_key'))) if proof else None
    if bound:
        raw = json.loads(bound['data_json'])
        exact = digest(raw) == bound['digest'] == proof.get('digest') and _timestamp(proof.get('at'))
        canonical_gift = (proof.get('source') == 'postgres.gifts' and proof.get('field') == 'delivered_at'
                          and raw.get('gift_id') == row.get('provider_id')
                          and raw.get('delivered_at') == proof.get('at'))
        events = raw.get('attributes', {}).get('events', [])
        scheduled = [e for e in events if e.get('stage') == 'scheduled' and e.get('created-at') == proof.get('at')]
        native_gift = (proof.get('source') == 'live.loopandtie.gifts'
                       and proof.get('field') == 'attributes.events.scheduled.created-at'
                       and raw.get('id') == row.get('provider_id') and len(scheduled) == 1
                       and (raw.get('attributes', {}).get('email') or '').lower() == row.get('recipient'))
        if exact and (canonical_gift or native_gift):
            return proof['at'], 'exact_provider_commitment'
    return None, 'undated_commitment_hold'


def _usage(store, plan, at):
    records = {}
    claims = plan.get('claims', {})
    for key, claim in claims.items():
        if claim.get('status') != 'not_committed':
            records[key] = {'channel': claim['channel'], 'sender': claim['sender'], 'at': claim['at']}
    for row in store.rows('SELECT * FROM attempts'):
        key = row['idem_key']
        if row['status'] in ('aborted', 'cancelled'):
            records.pop(key, None)
        elif row['channel'] in CHANNELS:
            stamp, origin = attempt_clock(row, claims.get(key), store)
            if origin == 'inbound_event':
                records.pop(key, None)
                continue
            records[key] = {**row, 'at': stamp}
    daily, hourly, sender_daily, sender_hourly = {}, {}, {}, {}
    for row in records.values():
        channel = CHANNELS.get(row['channel'], row['channel'])
        if channel not in ('email', 'gift', 'social'):
            continue
        stamp = _timestamp(row['at'])
        if stamp is None or stamp.date() != at.date():
            continue
        daily[channel] = daily.get(channel, 0) + 1
        same_hour = stamp.hour == at.hour
        if same_hour:
            hourly[channel] = hourly.get(channel, 0) + 1
        if channel == 'email':
            sender = str(row['sender'] or '').strip().lower()
            sender_daily[sender] = sender_daily.get(sender, 0) + 1
            if same_hour:
                sender_hourly[sender] = sender_hourly.get(sender, 0) + 1
    return daily, hourly, sender_daily, sender_hourly


def quota_holds(store):
    holds = []
    for row in store.rows('SELECT * FROM attempts'):
        if row['channel'] not in CHANNELS or row['status'] in ('aborted', 'cancelled'):
            continue
        stamp, origin = attempt_clock(row, store=store)
        if origin == 'undated_commitment_hold':
            holds.append({'key': row['idem_key'], 'channel': row['channel'],
                          'provider_id': row['provider_id'], 'reason': origin})
    return holds


def _batch_usage(store, plan, batch_id):
    used = {}
    for key, claim in plan.get('claims', {}).items():
        if claim.get('force_batch_id') != batch_id or claim.get('status') == 'not_committed':
            continue
        attempt = store.one('SELECT status FROM attempts WHERE idem_key=?', (key,))
        if attempt and attempt['status'] in ('aborted', 'cancelled'):
            continue
        channel = claim['channel']
        used[channel] = used.get(channel, 0) + 1
    return used


def _force_batch(store, plan, claim):
    batch_id = claim.get('force_batch_id')
    batch = plan.get('force_batches', {}).get(batch_id)
    if not isinstance(batch, dict) or batch.get('status') != 'running':
        return None
    proof = store.one('SELECT payload_json FROM events WHERE event_id=?', ('force_release:' + str(batch_id),))
    lease = store.one("SELECT owner,expires_at FROM leases WHERE name='execution'")
    expected = {key: batch.get(key) for key in ('batch_id', 'date', 'at', 'quotas', 'owner')}
    if (not proof or json.loads(proof['payload_json']) != expected
            or batch.get('date') != plan.get('date')
            or batch.get('owner') != getattr(store, 'execution_owner', None)
            or not lease or lease['owner'] != batch.get('owner') or lease['expires_at'] <= time.time()):
        return None
    return batch


def _batch_quota(store, channel, limits):
    if store.setting('portable_attendee', False):
        return min(_positive(store.setting('batch_limits', {}).get(channel)), limits.get(channel, 0))
    return limits.get(channel, 0) // 10


def _start_force_batch(store, plan, at, limits, owner, limit=None):
    batch_id = uuid.uuid4().hex
    batch = {'batch_id': batch_id, 'date': at.date().isoformat(), 'at': at.isoformat(),
             'quotas': {channel: min(_batch_quota(store, channel, limits), limit) if limit else _batch_quota(store, channel, limits)
                        for channel in limits}, 'owner': owner}
    plan.setdefault('force_batches', {})[batch_id] = {**batch, 'status': 'running'}
    with store.db:
        store.set(_plan_name(at), plan)
        store.event('force_release', batch_id, batch, key='force_release:' + batch_id, at=at.isoformat())
    return batch_id


def forced_claim(store, action):
    """Only a matching durable force receipt authorizes ignoring internal allowances."""
    plan, _, _ = _plan(store, _clock())
    claim = plan.get('claims', {}).get(action.get('action_key'))
    return bool(claim and claim.get('status') == 'dispatching' and claim.get('force_batch_id')
                and claim.get('channel') == CHANNELS.get(action.get('channel'))
                and claim.get('sender') == str(action.get('sender') or '').strip().lower()
                and _force_batch(store, plan, claim))


def _force_warnings(store, action, claim, at, daily, sender_daily, limits, sender_limits):
    channel, sender = claim['channel'], claim['sender']
    boundaries = [('channel', channel, daily.get(channel, 0), limits.get(channel, 0))]
    if channel == 'email':
        boundaries.append(('sender', sender, sender_daily.get(sender, 0), sender_limits.get(sender, 0)))
    for scope, identity, used, limit in boundaries:
        if used <= limit:
            continue
        release = claim.get('force_batch_id') or (at.date().isoformat() + ':' + str(at.hour))
        key = 'allowance_warning:' + release + ':' + scope + ':' + identity
        if store.one('SELECT event_id FROM events WHERE event_id=?', (key,)):
            continue
        singular = {'email': 'email', 'gift': 'gift', 'social': 'social touch'}[channel]
        plural = {'email': 'emails', 'gift': 'gifts', 'social': 'social touches'}[channel]
        if scope == 'channel':
            message = "Warning: This " + singular + " would put today's recorded and reserved " + plural + ' at ' + str(used)
        else:
            message = 'Warning: This email would put ' + sender + ' at ' + str(used) + ' recorded or reserved emails today'
        message += ', above the ' + str(limit) + ' daily target. Continuing under your warning-only rule.'
        with store.db:
            store.event('force_allowance_warning', action['action_key'],
                        {'batch_id': claim.get('force_batch_id'), 'scope': scope, 'identity': identity,
                         'capacity_used': used, 'internal_allowance': limit, 'message': message},
                        key=key, at=at.isoformat())
        print(message, file=sys.stderr, flush=True)


def _capacity(store, plan, at, channel, sender, limits, sender_limits, batch_id=None):
    daily, hourly, sender_daily, sender_hourly = _usage(store, plan, at)
    available = limits.get(channel, 0) > 0
    if store.setting('portable_attendee', False):
        available = available and daily.get(channel, 0) < limits.get(channel, 0)
        if channel == 'email':
            available = available and sender_daily.get(sender, 0) < sender_limits.get(sender, 0)
    if batch_id:
        batch = plan['force_batches'][batch_id]
        quota = min(batch['quotas'].get(channel, 0), _batch_quota(store, channel, limits))
        available = available and _batch_usage(store, plan, batch_id).get(channel, 0) < quota
    else:
        available = available and hourly.get(channel, 0) < _chunk(limits.get(channel, 0), at.hour)
    if channel == 'email':
        available = available and sender_limits.get(sender, 0) > 0
    return available


def pacing_issues(store, action):
    """Recheck a durable hourly or explicit force claim before recipient-facing writes."""
    at = _clock()
    plan, limits, sender_limits = _plan(store, at)
    claim = plan.get('claims', {}).get(action.get('action_key'))
    channel = CHANNELS.get(action.get('channel'))
    sender = str(action.get('sender') or '').strip().lower()
    forced = bool(claim and claim.get('force_batch_id'))
    batch = _force_batch(store, plan, claim) if forced else None
    if forced and not batch:
        return ['Forced claim has no matching active batch receipt and execution owner.']
    if not forced and at.hour not in HOURS:
        return ['Outreach runs from 08:00 through 17:59 America/New_York.']
    if (not claim or claim.get('status') != 'dispatching' or (not forced and claim.get('hour') != at.hour)
            or claim.get('channel') != channel or claim.get('sender') != sender):
        return ['Action has no current hourly release claim.']
    daily, hourly, sender_daily, sender_hourly = _usage(store, plan, at)
    quota = min(batch['quotas'].get(channel, 0), _batch_quota(store, channel, limits)) if forced else _chunk(limits.get(channel, 0), at.hour)
    used = _batch_usage(store, plan, claim['force_batch_id']).get(channel, 0) if forced else hourly.get(channel, 0)
    if used > quota:
        return ['The hourly or manual batch allowance is exhausted.']
    if channel == 'email' and sender_limits.get(sender, 0) <= 0:
        return ['Sender consent is unavailable.']
    if store.setting('portable_attendee', False) and (daily.get(channel, 0) > limits.get(channel, 0)
            or channel == 'email' and sender_daily.get(sender, 0) > sender_limits.get(sender, 0)):
        return ['Your hard daily channel or sender cap is exhausted.']
    _force_warnings(store, action, claim, at, daily, sender_daily, limits, sender_limits)
    return []


def _claim(store, plan, at, action, status, batch_id=None):
    key = action['action_key']
    if key not in plan['claims'] or plan['claims'][key].get('status') == 'not_committed':
        plan['claims'][key] = {'at': at.isoformat(), 'hour': at.hour,
                               'channel': CHANNELS[action['channel']],
                               'owner': getattr(store, 'execution_owner', None),
                               'sender': str(action.get('sender') or '').strip().lower()}
        if batch_id:
            plan['claims'][key]['force_batch_id'] = batch_id
    plan['claims'][key]['status'] = status
    with store.db:
        store.set(_plan_name(at), plan)
        store.event('hourly_claim_' + status, key, {'hour': at.hour, 'channel': plan['claims'][key]['channel']},
                    key='hourly_claim:' + key + ':' + status, at=at.isoformat())


def pacing_status(store):
    """Inspect today's hourly allowances without creating a plan or claims."""
    at = _clock()
    plan, targets, senders = _plan(store, at)
    if not plan:
        targets, senders = _targets(store)
    daily, hourly, _, _ = _usage(store, plan, at)
    holds = quota_holds(store)
    undated = {channel: sum(CHANNELS[h['channel']] == channel for h in holds)
               for channel in ('email', 'gift', 'social')}
    inside = at.hour in HOURS
    slots = [{'hour': hour, 'allowances': {channel: _chunk(total, hour)
              for channel, total in targets.items()}} for hour in HOURS]
    return {'at': at.isoformat(), 'timezone': 'America/New_York', 'outreach_window': '08:00 to 18:00',
            'inside_outreach_window': inside, 'daily_targets': targets,
            'daily_attempts': {channel: daily.get(channel, 0) for channel in targets},
            'daily_capacity_used': daily, 'undated_commitment_holds': undated,
            'hourly_attempts': hourly, 'slot_allowances': slots,
            'current_hour_remaining': {channel: max(0,
                _chunk(total, at.hour) - hourly.get(channel, 0)) if inside else 0
                for channel, total in targets.items()},
            'sender_daily_targets': senders, 'daily_limits_blocking': store.setting('portable_attendee',False), 'missed_slot_catch_up': False,
            'quota_holds': holds,
            'usage_note': 'Dated outgoing commitments count toward hourly usage. Undated records retain recipient duplicate protection.'}

def preview(store, limit=20):
    from engine.checks import validate
    result = []
    for action in store.rows('SELECT * FROM actions WHERE status NOT IN (?,?) ORDER BY at LIMIT ?', ('completed', 'cancelled', limit)):
        issues = [action['reason']] if action['status'] == 'requires_refresh' else validate(store, action, committing=False)
        result.append({'key': action['action_key'], 'channel': action['channel'], 'recipient': action['recipient'],
                       'status': action['status'], 'issues': issues})
    return result

def dispatch(store, action):
    from engine.checks import require_commit
    require_commit(store, action)
    person = store.one('SELECT * FROM people WHERE email=? AND domain=? ORDER BY observed_at DESC LIMIT 1', (action['recipient'], action['domain']))
    if not person: raise ValueError('No verified person record for this action.')
    person = {**json.loads(person['data_json']), **person}
    module = importlib.import_module(MODULES[action['channel']])
    payload = json.loads(action['payload_json'])
    return module.send(store, person, payload, action['action_key'])

def prepare(store, channel, person, payload, sender=''):
    from engine.checks import make_action, validate
    action = make_action(channel, person, payload, sender)
    issues = validate(store, action, committing=False)
    status = 'held' if issues else 'ready'
    with store.db:
        store.db.execute('INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?)',
            (action['action_key'], channel, action['recipient'], action['domain'], sender, status,
             encode(payload), action['at'], '; '.join(issues)))
        store.event('action_prepared', action['action_key'], {'channel': channel, 'status': status, 'issues': issues})
    return {**action, 'status': status, 'issues': issues}

def cycle(store, force=False, before_send=None, limit=None, action_keys=None):
    from engine.checks import execution_issues, require_commit, recheck_actions, release_keys
    if type(force) is not bool:
        raise ValueError('Force must be an explicit boolean option.')
    if limit is not None and (type(limit) is not int or not 1 <= limit <= 100):
        raise ValueError('Choose an explicit release limit from 1 to 100')
    if action_keys is not None and (not isinstance(action_keys,list) or not 1<=len(action_keys)<=100
            or any(not isinstance(key,str) or not store.one('SELECT action_key FROM actions WHERE action_key=?',(key,)) for key in action_keys)):
        raise ValueError('Select existing original action keys only. No execution reservation was created')
    selected=set(action_keys) if action_keys is not None else None
    if execution_issues(store):
        return {'at': now(), 'provider_commitments': 0, 'reason': ' '.join(execution_issues(store))}
    at = _clock()
    if not force and at.hour not in HOURS:
        return {'at': at.isoformat(), 'provider_commitments': 0, 'reason': 'The next outreach cycle starts at 08:00 America/New_York.'}
    owner = str(os.getpid()) + ':' + uuid.uuid4().hex
    store.lease(owner, 3600)
    completed, held = [], []
    try:
        refreshed = before_send(store) if before_send else {}
        rechecked = recheck_actions(store)
        plan, limits, sender_limits = _plan(store, at, create=True)
        batch_id = _start_force_batch(store, plan, at, limits, owner, limit) if force else None
        quotas = (plan['force_batches'][batch_id]['quotas'] if force else
                  {channel: _chunk(target, at.hour) for channel, target in limits.items()})
        if not force:
            with store.db:
                store.event('hourly_release', plan['date'], {'hour': at.hour, 'quotas': quotas},
                            key='hourly_release:' + plan['date'] + ':' + str(at.hour), at=at.isoformat())
        allowed=release_keys(store)
        for row in store.rows("SELECT * FROM actions WHERE status='ready' ORDER BY at,action_key"):
            if selected is not None and row['action_key'] not in selected: continue
            if allowed is not None and row['action_key'] not in allowed: continue
            if limit is not None and len(completed) + len(held) >= limit:
                break
            current = _clock()
            if current.date() != at.date() or (not force and current.hour != at.hour):
                break
            channel = CHANNELS.get(row['channel'])
            sender = str(row['sender'] or '').strip().lower()
            previous = plan['claims'].get(row['action_key'], {})
            if channel is None or (previous and previous.get('status') != 'not_committed'):
                continue
            if not _capacity(store, plan, at, channel, sender, limits, sender_limits, batch_id):
                continue
            _claim(store, plan, at, row, 'dispatching', batch_id)
            try:
                issues = pacing_issues(store, row)
                if issues:
                    raise ValueError(' '.join(issues))
                require_commit(store, row)
                outcome = dispatch(store, row)
                attempt = store.one('SELECT status FROM attempts WHERE idem_key=?', (row['action_key'],))
                if not attempt:
                    raise UnrecordedDispatch('Adapter returned without a durable attempt. Preserve the hourly claim for reconciliation.')
                if attempt['status'] == 'aborted':
                    _claim(store, plan, at, row, 'not_committed')
                    with store.db:
                        store.db.execute("UPDATE actions SET status='held',reason=? WHERE action_key=?", (str(outcome.get('reason')), row['action_key']))
                    held.append({'key': row['action_key'], 'reason': outcome.get('reason')})
                    continue
                _claim(store, plan, at, row, 'committed')
                with store.db:
                    store.db.execute("UPDATE actions SET status='awaiting_readback',reason=? WHERE action_key=?", ('Provider submission recorded; verify delivery.', row['action_key']))
                completed.append({'key': row['action_key'], 'outcome': outcome})
            except Exception as exc:
                attempt = store.one('SELECT status FROM attempts WHERE idem_key=?', (row['action_key'],))
                uncertain = bool(attempt) or isinstance(exc, UnrecordedDispatch)
                _claim(store, plan, at, row, 'uncertain' if uncertain else 'not_committed')
                with store.db:
                    store.db.execute("UPDATE actions SET status='held',reason=? WHERE action_key=?", (str(exc)[:500], row['action_key']))
                    store.event('action_held', row['action_key'], {'reason': str(exc)[:500]})
                held.append({'key': row['action_key'], 'reason': str(exc)[:500]})
        daily, hourly, _, _ = _usage(store, plan, at)
        warnings = [json.loads(row['payload_json']) for row in store.rows(
                    "SELECT payload_json FROM events WHERE kind='force_allowance_warning' AND json_extract(payload_json,'$.batch_id')=?",
                    (batch_id,))] if force else []
        if force:
            plan['force_batches'][batch_id]['status'] = 'finished'
            with store.db:
                store.set(_plan_name(at), plan)
                store.event('force_finished', batch_id, {'submitted': len(completed), 'held': len(held)},
                            key='force_finished:' + batch_id, at=_clock().isoformat())
        return {'at': at.isoformat(), 'hour': at.hour, 'quotas': quotas, 'daily_targets': limits,
                'hourly_attempts': hourly, 'daily_attempts': daily,
                'submitted': completed, 'held': held, 'provider_commitments': len(completed),
                'rechecked': rechecked,
                'source_refresh': refreshed,
                'selected_action_keys':sorted(selected) if selected is not None else None,
                'forced': force, 'force_batch_id': batch_id, 'warnings': warnings}
    finally:
        store.release(owner)

def reconcile(store, action_key):
    row = store.one('SELECT * FROM attempts WHERE idem_key=?', (action_key,))
    if not row: raise ValueError('Attempt does not exist.')
    module = MODULES.get(row['channel'])
    if not module: raise ValueError('This channel has no delivery adapter. Preserve the recorded attempt.')
    result = importlib.import_module(module).reconcile(store, action_key)
    if result.get('status') in ('sent', 'queued'):
        status = 'confirmed' if result['status'] == 'sent' else 'awaiting_readback'
        reason = ('Provider confirmed the exact send.' if status == 'confirmed'
                  else 'Gojiberry accepted and queued the invitation. Actual send remains pending.')
        with store.db:
            store.db.execute('UPDATE actions SET status=?,reason=? WHERE action_key=?', (status, reason, action_key))
            for row in store.rows("SELECT name,data_json FROM settings WHERE name LIKE 'hourly_pacing:%'"):
                plan = json.loads(row['data_json']); claim = plan.get('claims', {}).get(action_key)
                if claim and claim.get('status') == 'uncertain':
                    claim['status'] = 'committed'; store.set(row['name'], plan)
                    store.event('submission_reconciled', action_key, {'status': result['status'], 'retry_allowed': False})
    return result
