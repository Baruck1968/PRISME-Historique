"""Offline prospective planning and assessment. No network calls or scheduling."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pilot

SOURCE_CAPTURE = '20261021T151402747019Z_25530128b0074bab9bf37d4b567fdb26.json'
SOURCE_HASH = '934013a0ab589ddf8d3df7d1e29944f5422f61fe93c91539ba79f8543684e95e'

def build(envelope, asof):
    observed = pilot.iso(envelope['received_at'])
    decision = pilot.iso(asof)
    if decision < observed:
        raise ValueError('Planning cannot precede capture receipt')
    if envelope['status'] != 'captured' or envelope['body_sha256'] != pilot.digest(envelope['raw_utf8'].encode()):
        raise ValueError('Unverified capture')
    data = json.loads(envelope['raw_utf8'])
    if len({e['id'] for e in data}) != len(data):
        raise ValueError('Duplicate event identifiers')
    rows=[]
    for event in sorted(data,key=lambda e:(e['commence_time'],e['id'])):
        anchor=pilot.iso(event['commence_time'])
        j1,h1=anchor-timedelta(hours=24),anchor-timedelta(hours=1)
        row={'event_id':event['id'],'sport':event['sport_key'],'source':'the-odds-api.com',
             'commence_time':event['commence_time'],'anchor_type':'scheduled_start_proxy',
             'bookmaker':'fanduel','market':'h2h','outcomes':[],
             'J1':j1.isoformat(),'H1':h1.isoformat(),'rules_id':None,'open_status':'unknown',
             'exclusions':[]}
        try:
            extracted=pilot.extract(envelope,event['id'],'fanduel','')
            row['outcomes']=sorted(extracted['prices'])
            if not extracted['last_update']:
                row['exclusions'].append('missing_market_timestamp_at_discovery')
            else:
                age=(pilot.iso(envelope['requested_at'])-pilot.iso(extracted['last_update'])).total_seconds()
                if not 0<=age<=120:row['exclusions'].append('stale_or_future_discovery')
        except (ValueError,KeyError,TypeError):
            row['exclusions'].append('missing_or_nonbinary_fanduel_h2h_at_discovery')
        # Do not backfill a target already passed; require planning before target, not its tolerance tail.
        if j1 <= decision:row['exclusions'].append('J1_already_passed')
        if h1 <= decision:row['exclusions'].append('H1_already_passed')
        row['prospective_candidate']=not row['exclusions']
        rows.append(row)
    return {'version':1,'created_at':asof,'source_body_sha256':envelope['body_sha256'],
            'threshold_percent':'20','tolerance_seconds':300,'max_age_seconds':120,
            'rules_and_opening_verified':False,'rows':rows}

def assess(manifest,row,envelope,slot):
    """Assess one target, always indicative; return no prices or alerts."""
    if slot not in ('J1','H1'):raise ValueError('Invalid slot')
    reasons=[]
    if not row['prospective_candidate']:reasons.append('not_prospectively_enrolled')
    if envelope is None:
        return {'slot':slot,'status':'missing','reasons':['missing_capture'],'validated':False}
    try:
        e=pilot.extract(envelope,row['event_id'],row['bookmaker'],'')
        if e['source']!=row['source'] or e['sport']!=row['sport']:reasons.append('changed_source_or_sport')
        if e['commence_time']!=row['commence_time']:reasons.append('rescheduled')
        if sorted(e['prices'])!=row['outcomes']:reasons.append('changed_outcomes')
        start,end=pilot.iso(e['requested_at']),pilot.iso(e['received_at'])
        if start < pilot.iso(manifest['created_at']):reasons.append('capture_before_enrollment')
        target=pilot.iso(row[slot])
        if end<start or max(abs((start-target).total_seconds()),abs((end-target).total_seconds()))>manifest['tolerance_seconds']:
            reasons.append('outside_target_window')
        if end>=pilot.iso(row['commence_time']):reasons.append('event_started')
        if not e['last_update']:reasons.append('missing_market_timestamp')
        elif not 0 <= (start-pilot.iso(e['last_update'])).total_seconds() <= manifest['max_age_seconds']:
            reasons.append('stale_or_future_price')
    except (ValueError,KeyError,TypeError):reasons.append('missing_or_invalid_event_market')
    return {'slot':slot,'status':'excluded' if reasons else 'indicative',
            'reasons':reasons+['unverified_rules','unconfirmed_open_status'],'validated':False}

def compare_pair(manifest, row, j1, h1):
    checks=[assess(manifest,row,j1,'J1'),assess(manifest,row,h1,'H1')]
    if any(c['status']!='indicative' for c in checks):
        return {'checks':checks,'candidate_changes':{},'alerts':[],'validated':False}
    a,b=[pilot.extract(e,row['event_id'],row['bookmaker'],'') for e in (j1,h1)]
    result=pilot.compare(a,b,tolerance_seconds=manifest['tolerance_seconds'],max_age_seconds=manifest['max_age_seconds'])
    return {'checks':checks,'candidate_changes':result['candidate_changes'],'alerts':[],
            'validated':False,'exclusions':result['exclusions']}

def summarize(manifest):
    candidates=[r for r in manifest['rows'] if r['prospective_candidate']]
    slots=sorted({r[s] for r in candidates for s in ('J1','H1')})
    return {'created_at':manifest['created_at'],'source_body_sha256':manifest['source_body_sha256'],
            'events_examined':len(manifest['rows']),'prospective_candidates':len(candidates),
            'priced_binary_markets':sum(len(r['outcomes'])==2 for r in manifest['rows']),
            'J1_already_passed':sum('J1_already_passed' in r['exclusions'] for r in manifest['rows']),
            'missing_or_nonbinary':sum('missing_or_nonbinary_fanduel_h2h_at_discovery' in r['exclusions'] for r in manifest['rows']),
            'target_slots_utc':slots,'maximum_planned_odds_calls':len(slots),
            'validated_markets':0,'scheduled':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root',type=Path,default=Path(__file__).resolve().parents[1]/'private')
    args=parser.parse_args()
    source=args.private_root/SOURCE_CAPTURE
    envelope=json.loads(source.read_text())
    if envelope['body_sha256']!=SOURCE_HASH:raise ValueError('Wrong source capture')
    manifest=build(envelope,datetime.now(timezone.utc).isoformat())
    raw=pilot.encoded(manifest)
    # Immutable prospective enrollment; all 43 rows kept, including exclusions.
    dest=args.private_root/('manifest_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with dest.open('xb') as f:f.write(raw)
    public=summarize(manifest)
    public['manifest_sha256']=hashlib.sha256(raw).hexdigest()
    public['private_manifest_filename']=dest.name
    print(json.dumps(public,indent=2))

if __name__=='__main__':main()
