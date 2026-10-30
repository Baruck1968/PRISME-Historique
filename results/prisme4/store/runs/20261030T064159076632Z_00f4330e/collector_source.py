#!/usr/bin/env python3
"""PRISME 4 bounded read-only real-data capture, verification and offline replay."""
import argparse
import fcntl
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = 'https://api.manifold.markets/v0/'
UTC = timezone.utc


def now():
    return datetime.now(UTC)


def iso():
    return now().isoformat()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True).encode()


def numeric(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def save_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(raw)


def state_write(path, obj):
    temp = path.with_name(path.name + '.new.' + uuid.uuid4().hex)
    save_new(temp, encoded(obj))
    temp.replace(path)  # Mutable index only; immutable run directories are never overwritten.


def review_state(m, received, bets):
    t = int(datetime.fromisoformat(received).timestamp()*1000)
    candidates = []
    for b in bets:
        if b.get('isAnte') or b.get('isRedemption') or b.get('limitProb') is not None:
            continue
        if not numeric(b.get('createdTime')) or not numeric(b.get('amount')) or not b['amount']:
            continue
        fills = b.get('fills') or []
        if any(not numeric(f.get('timestamp')) for f in fills):
            continue
        executed = max([b['createdTime']]+[f['timestamp'] for f in fills])
        if executed <= t:
            candidates.append(executed)
    latest = max(candidates) if candidates else None
    open_proxy = (m.get('isResolved') is False and numeric(m.get('closeTime')) and m['closeTime'] > t
                  and m.get('outcomeType') == 'BINARY')
    p = m.get('probability')
    return {'market_id': m['id'], 'received_utc': received,
            'probability_captured': p if numeric(p) and 0 <= p <= 1 else None,
            'snapshot_open_binary': bool(open_proxy),
            'public_at_entry_evidence': 'anonymous_public_search_membership',
            'visibility_field_emitted': m.get('visibility'),
            'snapshot_isResolved': m.get('isResolved'), 'snapshot_resolution': m.get('resolution'),
            'snapshot_closeTime': m.get('closeTime'), 'snapshot_createdTime': m.get('createdTime'),
            'mechanism': m.get('mechanism'), 'question': m.get('question'),
            'recorded_lastBetTime': m.get('lastBetTime'),
            'latest_eligible_trade_in_bounded_page_ms': latest,
            'latest_trade_age_ms': t-latest if latest is not None else None,
            'last_trade_probe_records': len(bets),
            'fresh_trade_in_bounded_page': latest is not None and t-latest <= 86_400_000,
            'trade_page_is_complete_history': False,
            'outcome_unknown_verified': False, 'objective_rules_verified': False,
            'event_key_verified': False, 'predictive_eligible': False,
            'status': 'candidate_requires_external_and_manual_audit'}


class Fetch:
    def __init__(self, run):
        self.run = run
        self.calls = []
        self.errors = []
        self.raw = {}

    def get(self, label, endpoint, **params):
        if endpoint != 'search-markets' and endpoint != 'bets' and not endpoint.startswith('market/'):
            raise ValueError('Endpoint not in read-only allowlist')
        url = BASE + endpoint + ('?' + urllib.parse.urlencode(sorted(params.items())) if params else '')
        for attempt in range(1, 4):
            started = iso()
            try:
                time.sleep(.15)
                request = urllib.request.Request(url, method='GET', headers={'User-Agent':'PRISME4-readonly-research/1.0'})
                with urllib.request.urlopen(request, timeout=45) as response:
                    raw = response.read()
                    received = iso()
                    headers = {k.lower():v for k,v in response.headers.items()
                               if k.lower() in ('date','etag','last-modified','cache-control')}
                    status = response.status
                data = json.loads(raw)
                name = label + '.json'
                self.raw[name] = raw
                self.calls.append({'label':label, 'url':url, 'method':'GET', 'attempt':attempt,
                                   'request_started_utc':started, 'received_utc':received,
                                   'status':status, 'headers':headers, 'raw_member':name,
                                   'sha256':sha_bytes(raw), 'bytes':len(raw)})
                self.persist_raw()
                return data, received
            except Exception as error:
                entry = {'label':label, 'url':url, 'method':'GET', 'attempt':attempt,
                         'request_started_utc':started, 'error_utc':iso(),
                         'error_type':type(error).__name__, 'message':str(error)}
                self.errors.append(entry)
                state_write(self.run/'errors.json', self.errors)
                retry = (isinstance(error, urllib.error.HTTPError) and
                         (error.code == 429 or 500 <= error.code <= 599)) or isinstance(error, urllib.error.URLError)
                if not retry or attempt == 3:
                    raise
                time.sleep(2**attempt)
        raise RuntimeError('Unreachable')

    def persist_raw(self):
        # Raw archive belongs only to this new run; failed partial runs are retained.
        with zipfile.ZipFile(self.run/'raw.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for name, raw in self.raw.items():
                z.writestr(name, raw)


def verify_run(run):
    manifest = json.loads((run/'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        path = run/name
        if not path.resolve().is_relative_to(run.resolve()):
            raise RuntimeError('Unsafe manifest path')
        if sha_bytes(path.read_bytes()) != expected:
            raise RuntimeError('Integrity mismatch: '+str(path))
    for file, field in [('collection_plan.json','plan_sha256'),('collector_source.py','collector_sha256')]:
        if (run/file).exists() and sha_bytes((run/file).read_bytes()) != manifest[field]:
            raise RuntimeError('Embedded code/rules do not match manifest')
    with zipfile.ZipFile(run/'raw.zip') as z:
        if z.testzip() is not None:
            raise RuntimeError('Invalid ZIP CRC')
        for call in manifest['requests']:
            if call['method'] != 'GET' or not call['url'].startswith(BASE):
                raise RuntimeError('Non read-only provenance')
            raw = z.read(call['raw_member'])
            if sha_bytes(raw) != call['sha256']:
                raise RuntimeError('Raw response hash mismatch')
            if datetime.fromisoformat(call['received_utc']) < datetime.fromisoformat(call['request_started_utc']):
                raise RuntimeError('Clock moved backwards')
    return manifest


def replay(run):
    manifest = verify_run(run)
    if manifest['status'] != 'success':
        raise RuntimeError('Not a complete capture')
    with zipfile.ZipFile(run/'raw.zip') as z:
        calls = {r['label']:r for r in manifest['requests']}
        observations = []
        for market_id in manifest['cohort_ids']:
            label = 'market_'+market_id
            m = json.loads(z.read(calls[label]['raw_member']))
            bets = json.loads(z.read(calls['bets_'+market_id]['raw_member']))
            observations.append(review_state(m, calls[label]['received_utc'], bets))
    if observations != json.loads((run/'observations.json').read_text()):
        raise RuntimeError('Offline replay differs from stored observations')
    return observations


def verify_store(store):
    state = json.loads((store/'state.json').read_text())
    previous = None
    for relative in state['runs']:
        run = store/relative
        if not run.resolve().is_relative_to(store.resolve()):
            raise RuntimeError('Unsafe run path')
        m = verify_run(run)
        if m['status'] != 'success' or m['cohort_ids'] != state['cohort_ids'] or m['plan_sha256'] != state['plan_sha256']:
            raise RuntimeError('Run differs from frozen cohort/rules')
        if m['previous_manifest_sha256'] != previous:
            raise RuntimeError('Broken manifest chain')
        replay(run)
        previous = sha_bytes((run/'manifest.json').read_bytes())
    if previous != state['previous_manifest_sha256']:
        raise RuntimeError('Index does not match chain tip')
    return state


def capture(store, purpose):
    plan_raw = (HERE/'collection_plan.json').read_bytes()
    plan = json.loads(plan_raw)
    deployment = json.loads((HERE/'deployment.json').read_text())
    state_path = store/'state.json'
    state = verify_store(store) if state_path.exists() else None
    if state and state['plan_sha256'] != sha_bytes(plan_raw):
        raise RuntimeError('Rules changed: create a separate store/version, never rewrite this cohort')
    if state and now() >= datetime.fromisoformat(state['expires_utc']):
        print(json.dumps({'status':'pilot_expired_no_requests', 'expires_utc':state['expires_utc']}))
        return 0
    if purpose == 'daily':
        if not deployment['daily_enabled'] or deployment['confirmation'] != 'explicit_user_confirmation':
            raise RuntimeError('Daily capture is not authorized/enabled')
        if not state:
            raise RuntimeError('Initial successful capture is required before daily mode')
        slot = now().date().isoformat()
        if slot in state['completed_daily_slots']:
            print(json.dumps({'status':'daily_slot_already_complete_no_requests','slot':slot}))
            return 0
    stamp = now().strftime('%Y%m%dT%H%M%S%fZ')+'_'+uuid.uuid4().hex[:8]
    run = store/'runs'/stamp
    run.mkdir(parents=True, exist_ok=False)
    save_new(run/'collection_plan.json',plan_raw)
    save_new(run/'collector_source.py',Path(__file__).read_bytes())
    save_new(run/'deployment.json',(HERE/'deployment.json').read_bytes())
    fetch = Fetch(run)
    started = iso()
    cohort = list(state['cohort_ids']) if state else []
    observations = []
    status = 'failed'
    error_text = None
    try:
        if not state:
            discovered, received = fetch.get('discovery','search-markets', **plan['discovery_query'])
            if not isinstance(discovered, list):
                raise RuntimeError('Discovery schema changed')
            seen = set()
            for m in discovered:
                t = int(datetime.fromisoformat(received).timestamp()*1000)
                if (m.get('outcomeType') == 'BINARY' and m.get('isResolved') is False and
                    m.get('visibility') in (None, 'public') and numeric(m.get('closeTime')) and
                    m['closeTime'] > t and m['id'] not in seen):
                    cohort.append(m['id'])
                    seen.add(m['id'])
            if not cohort:
                raise RuntimeError('No admissible public open BINARY candidates found')
        for market_id in cohort:
            m, received = fetch.get('market_'+market_id,'market/'+urllib.parse.quote(market_id,safe=''))
            if m.get('id') != market_id:
                raise RuntimeError('Market identity mismatch')
            bets, _ = fetch.get('bets_'+market_id,'bets', contractId=market_id, limit=plan['latest_trade_probe_limit'])
            if not isinstance(bets,list) or any(b.get('contractId') != market_id for b in bets):
                raise RuntimeError('Trade schema or identity mismatch')
            observations.append(review_state(m, received, bets))
        status = 'success'
    except Exception as error:
        error_text = {'type':type(error).__name__,'message':str(error)}
    finished = iso()
    save_new(run/'observations.json',encoded(observations))
    if not (run/'errors.json').exists():
        save_new(run/'errors.json',encoded(fetch.errors))
    if not (run/'raw.zip').exists():
        fetch.persist_raw()
    files = {name:sha_bytes((run/name).read_bytes()) for name in ['raw.zip','observations.json','errors.json','collection_plan.json','collector_source.py','deployment.json']}
    manifest = {'schema_version':1,'status':status,'purpose':purpose,
                'request_window_started_utc':started,'request_window_finished_utc':finished,
                'actual_receipts_not_scheduled_instant':True,'cohort_ids':cohort,
                'rule_version':plan['rule_version'],'plan_sha256':sha_bytes(plan_raw),
                'collector_sha256':sha_bytes(Path(__file__).read_bytes()),
                'previous_manifest_sha256':state['previous_manifest_sha256'] if state else None,
                'requests':fetch.calls,'files_sha256':files,'error':error_text,
                'observations':len(observations),'predictive_eligible':0,
                'execution_environment': {'github_actions':os.environ.get('GITHUB_ACTIONS') == 'true',
                                          'github_run_id':os.environ.get('GITHUB_RUN_ID'),
                                          'github_run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
                                          'github_sha':os.environ.get('GITHUB_SHA')}}
    save_new(run/'manifest.json',encoded(manifest))
    if status != 'success':
        print(json.dumps({'status':status,'run':str(run),'error':error_text})); return 1
    replay(run)
    if not state:
        state = {'schema_version':1,'cohort_ids':cohort,'plan_sha256':sha_bytes(plan_raw),
                 'first_successful_capture_utc':finished,
                 'expires_utc':(datetime.fromisoformat(finished)+timedelta(days=plan['proposed_duration_days'])).isoformat(),
                 'runs':[], 'completed_daily_slots':[]}
    state['runs'].append(str(run.relative_to(store)))
    if purpose == 'daily':
        state['completed_daily_slots'].append(now().date().isoformat())
    state['previous_manifest_sha256'] = sha_bytes((run/'manifest.json').read_bytes())
    state_write(state_path,state)
    print(json.dumps({'status':'success','run':str(run),'cohort':len(cohort),
                      'requests':len(fetch.calls),'errors_recorded':len(fetch.errors),
                      'expires_utc':state['expires_utc'],'scheduled':False},indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['capture','verify','replay','window'])
    parser.add_argument('--store',type=Path,default=ROOT/'results/prisme4/store')
    parser.add_argument('--run',type=Path)
    parser.add_argument('--purpose',choices=['feasibility','validation','daily'],default='feasibility')
    args = parser.parse_args()
    if args.command == 'capture':
        args.store.mkdir(parents=True,exist_ok=True)
        with (args.store/'.capture.lock').open('a') as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another capture owns this store; retry later')
            return capture(args.store,args.purpose)
    if args.command == 'verify':
        s = verify_store(args.store)
        print(json.dumps({'status':'verified','runs':len(s['runs']),'cohort':len(s['cohort_ids'])}))
    elif args.command == 'replay':
        if not args.run:
            parser.error('--run required')
        print(json.dumps({'status':'replayed_without_network','observations':len(replay(args.run))}))
    else:
        s = verify_store(args.store)
        print('active' if now() < datetime.fromisoformat(s['expires_utc']) else 'expired')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
