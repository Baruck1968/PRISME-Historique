#!/usr/bin/env python3
"""PRISME 3 calendar feasibility, real snapshot only; never fits a model."""
import argparse
import bisect
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
HOUR = 3_600_000
spec = importlib.util.spec_from_file_location('archive_parser', ROOT / 'experiments/prisme2/audit_archives.py')
archive_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive_parser)


def sha(path):
    return archive_parser.sha(path)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def calendar(plan):
    start = datetime.fromisoformat(plan['grid_start_utc'])
    end = datetime.fromisoformat(plan['grid_end_utc_inclusive'])
    step = timedelta(days=plan['grid_step_days'])
    if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0) or step.days < 1:
        raise ValueError('UTC increasing grid required')
    out = []
    while start <= end:
        out.append(int(start.timestamp() * 1000))
        start += step
    return out


def state_proxy(m, t):
    if not number(m.get('createdTime')) or m['createdTime'] >= t:
        return 'not_created_or_missing_creation'
    resolution = m.get('resolutionTime')
    if number(resolution):
        if resolution <= t:
            return 'already_resolved_proxy'
    elif m.get('isResolved') is not False:
        return 'resolution_chronology_unknown'
    close = m.get('closeTime')
    if not number(close):
        return 'closure_chronology_unknown'
    if close <= t:
        return 'closed_in_final_snapshot_proxy'
    return 'open_unresolved_proxy_only'


def primary_time(m, grid):
    created = m.get('createdTime')
    if not number(created):
        return None
    index = bisect.bisect_left(grid, created + 48 * HOUR)
    return grid[index] if index < len(grid) else None


def title_key(title):
    return ' '.join(unicodedata.normalize('NFKC', title).casefold().split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / 'data/prisme2/markets.zip')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/prisme3')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plan = json.loads((HERE / 'sampling_plan.json').read_text())
    grid = calendar(plan)
    lock = json.loads((ROOT / 'experiments/prisme2/source_lock.json').read_text())
    if sha(args.archive) != lock['markets_sha256']:
        raise RuntimeError('Unrecognized market archive: stop rather than change corpus')
    flows = [Counter() for _ in grid]
    total, fields = Counter(), Counter()
    rows, manual, groups = [], [], defaultdict(list)
    ids = set()
    with zipfile.ZipFile(args.archive) as z:
        members = [m for m in z.infolist() if not m.is_dir()]
        if len(members) != 1:
            raise RuntimeError('Unexpected archive structure')
        with z.open(members[0]) as raw, io.TextIOWrapper(raw, encoding='utf-8') as stream:
            for m in archive_parser.records(stream):
                if m['id'] in ids:
                    raise RuntimeError('Duplicate market ID')
                ids.add(m['id'])
                total['all_markets'] += 1
                fields.update(m.keys())
                if m.get('outcomeType') != 'BINARY':
                    total['excluded_nonbinary'] += 1
                    continue
                total['binary'] += 1
                for t, flow in zip(grid, flows):
                    flow[state_proxy(m, t)] += 1
                t = primary_time(m, grid)
                if t is None:
                    total['no_primary_grid_date'] += 1
                    continue
                total['with_primary_grid_date'] += 1
                state = state_proxy(m, t)
                total[state] += 1
                if state != 'open_unresolved_proxy_only':
                    continue
                total['final_yes_no_labels_available'] += int(m.get('isResolved') is True and m.get('resolution') in ('YES', 'NO'))
                total['snapshot_still_unresolved'] += int(m.get('isResolved') is False)
                total['with_conversion_time'] += int(number(m.get('cfmmConversionTime')))
                total['with_topic_links'] += int(bool(m.get('groupLinks') or m.get('groupSlugs')))
                row = {'id': m['id'], 'question': m.get('question', ''),
                       't_ms': t, 'previous_t_ms': t - 24 * HOUR,
                       'createdTime': m.get('createdTime'),
                       'snapshot_closeTime': m.get('closeTime'),
                       'snapshot_resolutionTime': m.get('resolutionTime'),
                       'snapshot_isResolved': m.get('isResolved'),
                       'snapshot_mechanism': m.get('mechanism'),
                       'cfmmConversionTime': m.get('cfmmConversionTime'),
                       'state': state, 'historical_tradability': 'unverified',
                       'outcome_unknown_at_t': 'unverified',
                       'historical_prices_certified': False,
                       'event_key_verified': False,
                       'title_candidate_key': title_key(m.get('question', ''))}
                rows.append(row)
                groups[row['title_candidate_key']].append(m['id'])
                rank = hashlib.sha256(m['id'].encode()).hexdigest()
                if len(manual) < 20 or rank < manual[-1][0]:
                    manual.append((rank, {'observation': row, 'snapshot': m}))
                    manual.sort(key=lambda pair: pair[0])
                    manual = manual[:20]
    # The entire archive member was consumed, including ZIP CRC verification.
    output = args.output
    def write(name, data):
        (output / name).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    write('calendar_flow.json', [{'t_ms': t, 't_utc': datetime.fromtimestamp(t/1000, timezone.utc).isoformat(),
                                'counts': dict(flow)} for t, flow in zip(grid, flows)])
    write('manual_audit_markets.json', [item for _, item in manual])
    repeated = {key: members for key, members in groups.items() if len(members) > 1}
    write('event_grouping_audit.json', {
        'rule': plan['grouping_audit'],
        'candidate_markets': len(rows), 'distinct_normalized_titles': len(groups),
        'repeated_title_groups': len(repeated),
        'markets_in_repeated_title_groups': sum(map(len, repeated.values())),
        'verified_common_event_keys': 0,
        'warning': 'Equal titles can mean different dates/events; different titles can mean the same event. No predictive split uses these links.',
        'groups': repeated})
    # Store all primary proxy observations; no current snapshot probability or final Y is a feature.
    with zipfile.ZipFile(output / 'calendar_candidates.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        content = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)
        z.writestr('calendar_candidates.jsonl', content)
    write('feasibility.json', {
        'status': 'stopped_before_predictive_test',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'archive_sha256': lock['markets_sha256'], 'zip_crc_validated': True,
        'script_sha256': sha(Path(__file__)), 'parser_sha256': sha(Path(archive_parser.__file__)),
        'plan_sha256': sha(HERE / 'sampling_plan.json'),
        'grid_dates': len(grid), 'primary_observation_rule_uses_outcomes': False,
        'counts': dict(total), 'snapshot_fields': sorted(fields),
        'verified_tradable_unknown_outcome_observations': 0,
        'complete_verified_price_trajectories': 0,
        'price_trajectory_coverage_assessed_for_full_corpus': False,
        'event_keys_verified_from_snapshot': 0, 'corpus_event_partition_verified': False, 'model_fits': 0, 'statistical_result': None,
        'blockers': ['Historical close/reopen and resolution edit histories are absent from the snapshot.',
                     'Unresolved at t does not establish that the outcome was not already public.',
                     'Price and liquidity history and DPM/CPMM changes require point-in-time reconstruction, not final snapshot probabilities.',
                     'Common-event partition has not been verified; normalized titles and topics are insufficient.'],
        'not_measured': ['p(t) distribution', 'delta distribution', 'full-corpus price freshness',
                         'direction overlap', 'Brier', 'log-loss', 'confidence intervals', 'p-values']})
    print(json.dumps({'grid_dates': len(grid), 'counts': dict(total),
                      'manual_sample': [item['observation']['id'] for _, item in manual],
                      'repeated_title_groups': len(repeated)}, indent=2))


if __name__ == '__main__':
    main()
