#!/usr/bin/env python3
"""Inspect one freely published provider sample; never call a keyed odds endpoint.

Raw provider data remain in ignored local cache, not in the public report.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

HERE=Path(__file__).resolve().parent
URL='https://public-odds-api-sample-data.s3.amazonaws.com/historical-bundesliga.json'
FR_KEYS={'betclic_fr','netbet_fr','pmu_fr','unibet_fr','winamax_fr'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'evidence/public_sample_checks'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'))
    args=parser.parse_args()
    if args.output.exists():raise RuntimeError('Output exists; choose a new file, never overwrite an audit')
    report={'url':URL,'checked_utc':datetime.now(timezone.utc).isoformat(),
            'provenance':'Public sample linked from official historical-odds documentation; not a newly purchased API response',
            'raw_publication':False,'statistical_test_performed':False}
    try:
        with urllib.request.urlopen(URL,timeout=30) as r:raw=r.read();report['http_status']=r.status
        obj=json.loads(raw);events=obj['data'] if isinstance(obj,dict) else obj
        if not isinstance(events,list):raise RuntimeError('Unexpected sample schema')
        keys=sorted({b['key'] for e in events for b in e.get('bookmakers',[])})
        stamp=obj.get('timestamp') if isinstance(obj,dict) else None
        report.update(status='inspected_provider_sample',sha256=hashlib.sha256(raw).hexdigest(),
                      bytes=len(raw),snapshot_timestamp=stamp,events=len(events),bookmaker_keys=keys,
                      exact_current_fr_keys_present=sorted(FR_KEYS.intersection(keys)),
                      first_commence_time=min(e['commence_time'] for e in events) if events else None,
                      last_commence_time=max(e['commence_time'] for e in events) if events else None,
                      limitation='One static snapshot, not a 3-snapshot pre-event trajectory or proof of France historical continuity. Old keys are not mapped to France without evidence.')
        cache=HERE/'.cache/public_samples';cache.mkdir(parents=True,exist_ok=True)
        path=cache/(report['sha256']+'.json')
        if not path.exists():path.write_bytes(raw)
    except Exception as error:
        report.update(status='unavailable',error_type=type(error).__name__,error=str(error))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:f.write(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return int(report['status']=='unavailable')


if __name__=='__main__':raise SystemExit(main())
