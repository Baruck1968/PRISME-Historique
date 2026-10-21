#!/usr/bin/env python3
"""Reproduce a limited external schedule check; no exchange-state certificate."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/prisme3'


def main():
    source = OUT / 'source_checks/nfl_games.csv'
    metadata = json.loads((OUT / 'source_checks/nfl_source.json').read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != metadata['sha256']:
        raise RuntimeError('Schedule source changed')
    # Mappings follow the two explicitly named games in the frozen manual sample.
    mapping = {'6G7Hcqq3a2XTAv1sTmhI': '2023_04_PIT_HOU',
               'wrMLxLV0yRCRB7fyOaVp': '2023_02_MIA_NE'}
    schedules = {r['game_id']:r for r in csv.DictReader(source.open()) if r['game_id'] in mapping.values()}
    sample = json.loads((OUT / 'manual_audit_markets.json').read_text())
    rows = []
    for item in sample:
        obs = item['observation']
        if obs['id'] not in mapping:
            continue
        event = mapping[obs['id']]
        record = schedules[event]
        # The saved nflreadr dictionary explicitly documents Eastern time.
        start = datetime.fromisoformat(record['gameday'] + 'T' + record['gametime']).replace(tzinfo=ZoneInfo('America/New_York'))
        start_ms = int(start.timestamp() * 1000)
        rows.append({'market_id':obs['id'], 'event_key':'nflverse:'+event,
                     'schedule_date':record['gameday'], 'schedule_time_eastern':record['gametime'],
                     'scheduled_start_utc':start.astimezone(ZoneInfo('UTC')).isoformat(),
                     'observation_t_ms':obs['t_ms'], 'schedule_start_ms':start_ms,
                     'hours_until_scheduled_start':(start_ms - obs['t_ms'])/3_600_000,
                     'schedule_start_after_t':start_ms > obs['t_ms'],
                     'exchange_open_at_t_verified':False,
                     'public_outcome_unknown_at_t_certified':False})
    result = {'source_sha256':metadata['sha256'],
              'interpretation':'Both scheduled games are later than t. Supporting temporal plausibility only: schedule is a current historical table, not a version published before t; no historical trading or public-information certificate.',
              'event_mapping_scope':'Two manually identified markets only, not a corpus-wide partition.',
              'records':rows}
    (OUT / 'external_schedule_check.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
