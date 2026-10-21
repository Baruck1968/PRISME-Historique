#!/usr/bin/env python3
"""Read-only documentary audit. No Football-Data fetch, API keys or paid API calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ODDS_COMMIT = 'dc344b7e93b70003d0fef35584c8edd78a4c40fb'
RESULTS_COMMIT = 'e6744429ee395bc86f247348c6184bb08d4eb361'
SOURCES = [
    ('historical_documentation','https://the-odds-api.com/historical-odds-data/'),
    ('v4_documentation','https://the-odds-api.com/liveapi/guides/v4/'),
    ('bookmaker_directory','https://the-odds-api.com/sports-odds-data/bookmaker-apis.html'),
    ('pricing','https://the-odds-api.com/#pricing'),
    ('terms','https://the-odds-api.com/terms-and-conditions.html'),
    ('anj_operators','https://www.anj.fr/offre-de-jeu-et-marche/operateurs-agrees'),
    ('official_historical_sample',f'https://raw.githubusercontent.com/the-odds-api/samples-python/{ODDS_COMMIT}/historical_odds.py'),
    ('official_event_sample',f'https://raw.githubusercontent.com/the-odds-api/samples-python/{ODDS_COMMIT}/historical_event_odds.py'),
    ('official_live_sample',f'https://raw.githubusercontent.com/the-odds-api/samples-python/{ODDS_COMMIT}/odds.py'),
    ('results_license',f'https://raw.githubusercontent.com/openfootball/football.json/{RESULTS_COMMIT}/README.md'),
    ('results_france_2023_24',f'https://raw.githubusercontent.com/openfootball/football.json/{RESULTS_COMMIT}/2023-24/fr.1.json'),
]
ALLOWED = {'raw.githubusercontent.com','the-odds-api.com','api.the-odds-api.com','www.anj.fr','anj.fr'}


def guard(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or p.hostname not in ALLOWED or p.username or p.password:
        raise PermissionError('Not an authorized documentary source; Football-Data is intentionally excluded')
    if any(k.lower().replace('_','') in ('apikey','token') for k,_ in urllib.parse.parse_qsl(p.query)):
        raise PermissionError('Credential-bearing request forbidden in documentary audit')
    if p.hostname=='api.the-odds-api.com':
        raise PermissionError('No live/paid odds endpoint is used in this audit')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'evidence'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    cache=HERE/'.cache'/args.output.name
    cache.mkdir(parents=True,exist_ok=False)
    checks=[];bodies={}
    for name,url in SOURCES:
        guard(url)
        row={'id':name,'url':url,'checked_utc':datetime.now(timezone.utc).isoformat(),'method':'GET'}
        try:
            with urllib.request.urlopen(url,timeout=30) as response:
                body=response.read();row['http_status']=response.status;row['final_url']=response.geturl()
            row.update(status='soft_404' if b'Four-Oh-Four' in body else 'retrieved',bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
            bodies[name]=body
            (cache/(name+'.raw')).write_bytes(body)
        except Exception as error:
            row.update(status='unavailable',error_type=type(error).__name__,error=str(error))
        checks.append(row)
    # Policy exclusion is explicit: no page, CSV or mirrored copy is fetched.
    checks.append({'id':'football_data','url':'https://www.football-data.co.uk/downloadm.php',
                   'status':'not_requested_due_to_reported_automation_AI_restriction',
                   'basis':'research/SPORTS_ODDS_SOURCE_FEASIBILITY.md; current terms require human/legal verification or explicit provider authorization'})
    results=None
    if 'results_license' in bodies and 'results_france_2023_24' in bodies:
        license_text=bodies['results_license'].decode()
        if 'dedicated to the public domain' not in license_text:
            raise RuntimeError('Expected permissive results-data statement absent')
        data=json.loads(bodies['results_france_2023_24']);rows=data['matches']
        results={'competition':data['name'],'matches':len(rows),
                 'with_ft_scores':sum('ft' in r.get('score',{}) for r in rows),
                 'with_time_field':sum('time' in r for r in rows),
                 'with_explicit_timezone_field':sum(any(k in r for k in ('timezone','utc_offset','time_zone')) for r in rows),
                 'interpretation':'Real community full-time results only, not odds, verified UTC kickoff or bookmaker settlements'}
        (args.output/'openfootball_france_2023_24.json').write_bytes(bodies['results_france_2023_24'])
    sample=bodies.get('official_historical_sample',b'').decode()
    official_sample_findings={'historical_paid_plan_statement_found':'only available on paid usage plans' in sample,
                              'historical_quota_formula_found':'10 x [number of markets specified] x [number of regions specified]' in sample,
                              'snapshot_timestamp_and_neighbors_fields_found':all(k in sample for k in ['previous_timestamp','next_timestamp',"['timestamp']"]),
                              'warning':'Code sample, not a purchased historical response or validated France coverage. No request example was executed.'}
    required=['historical_documentation','v4_documentation','bookmaker_directory','pricing','terms','anj_operators']
    blocked=[r['id'] for r in checks if r['id'] in required and r['status']!='retrieved']
    report={'checked_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'status':'documentary_audit_incomplete_access_blocked' if blocked else 'documentation_retrieved_data_coverage_still_unverified',
            'checks':checks,'required_documentary_sources_unavailable':blocked,
            'official_sample_findings':official_sample_findings,'real_results_check':results,
            'historical_odds_responses_obtained':0,'france_licensed_bookmakers_verified':None,
            'current_subscription_prices_verified':None,'statistical_results':None,
            'purchases':0,'subscriptions':0,'bets':0,'financial_transactions':0}
    (args.output/'access_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2,ensure_ascii=False))
    return int(bool(blocked))


if __name__=='__main__':raise SystemExit(main())
