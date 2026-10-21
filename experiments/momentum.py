#!/usr/bin/env python3
"""Read-only exploratory Manifold study; Python 3.12+, standard library only."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time
import urllib.parse
import urllib.request

BASE = 'https://api.manifold.markets/v0/'
HOUR = 3_600_000


class Source:
    def __init__(self, root, offline):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.offline = offline
        self.used = {}

    def get(self, endpoint, **params):
        url = BASE + endpoint + '?' + urllib.parse.urlencode(sorted(params.items()))
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.root / (key + '.json')
        if not path.exists():
            if self.offline:
                raise RuntimeError('Missing cached response: ' + url)
            time.sleep(0.15)
            request = urllib.request.Request(url, headers={'User-Agent': 'PRISME-Historique-research/0.1'})
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
            json.loads(raw)  # Never cache an invalid JSON response.
            path.write_bytes(raw)
            path.with_suffix('.meta.json').write_text(json.dumps({
                'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(raw).hexdigest()}, indent=2))
        raw = path.read_bytes()
        meta = json.loads(path.with_suffix('.meta.json').read_text())
        if hashlib.sha256(raw).hexdigest() != meta['sha256']:
            raise RuntimeError('Cache integrity failure: ' + str(path))
        self.used[key] = meta
        return json.loads(raw)


def finite_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def snapshot(source, market_id, cutoff, max_age):
    """Latest recorded executed trade before cutoff; reject timestamp ties."""
    before = None
    for _ in range(20):
        params = dict(contractId=market_id, beforeTime=int(cutoff) + 1, limit=1000)
        if before:
            params['before'] = before
        bets = source.get('bets', **params)
        if not isinstance(bets, list):
            raise RuntimeError('Unexpected bets schema')
        candidates = []
        for b in bets:
            # Resting limit-order records may accumulate future fills. Use only
            # initiating non-limit trades and their actual execution completion.
            if b.get('limitProb') is not None or b.get('isRedemption', False):
                continue
            if not finite_number(b.get('amount')) or b['amount'] == 0:
                continue
            if not finite_number(b.get('probAfter')) or not 0 <= b['probAfter'] <= 1:
                continue
            if not finite_number(b.get('createdTime')):
                raise RuntimeError('Executed trade without timestamp')
            fills = b.get('fills') or []
            if any(not finite_number(f.get('timestamp')) for f in fills):
                raise RuntimeError('Fill without timestamp')
            event_time = max([b['createdTime']] + [f['timestamp'] for f in fills])
            if event_time <= cutoff:
                candidates.append(dict(b, event_time=event_time))
        candidates.sort(key=lambda b: b['event_time'], reverse=True)
        if candidates:
            b = candidates[0]
            # A page boundary at the selected time cannot prove ordering.
            if len(bets) == 1000 and min(x['createdTime'] for x in bets) >= b['event_time']:
                raise ValueError('ambiguous_timestamp')
            tied = [x for x in candidates if x['event_time'] == b['event_time']]
            if len({x['probAfter'] for x in tied}) != 1:
                raise ValueError('ambiguous_timestamp')
            if cutoff - b['event_time'] > max_age:
                raise ValueError('stale_snapshot')
            return b['probAfter'], b['event_time']
        if len(bets) < 1000:
            raise ValueError('missing_snapshot')
        cursor = bets[-1]['id']
        if cursor == before:
            raise RuntimeError('Pagination did not advance')
        before = cursor
    raise RuntimeError('History page cap reached; no inference from truncated history')


def analyse(rows, permutations, seed):
    groups = defaultdict(list)
    for row in rows:
        if row['direction']:
            groups[min(19, int(row['p_final'] * 20))].append(row)
    strata = [g for g in groups.values() if {r['direction'] for r in g} == {-1, 1}]
    def statistic(labels):
        total = weight_sum = 0
        for g, signs in zip(strata, labels):
            up = [r['outcome'] - r['p_final'] for r, s in zip(g, signs) if s == 1]
            down = [r['outcome'] - r['p_final'] for r, s in zip(g, signs) if s == -1]
            weight = len(up) * len(down) / (len(up) + len(down))
            total += weight * (sum(up) / len(up) - sum(down) / len(down))
            weight_sum += weight
        return total / weight_sum
    n = sum(map(len, strata))
    if not strata:
        return {'status': 'no_probability_stratum_with_both_directions', 'n_overlap': 0}
    labels = [[r['direction'] for r in g] for g in strata]
    effect = statistic(labels)
    rng = random.Random(seed)
    extreme = 0
    for _ in range(permutations):
        shuffled = [rng.sample(s, len(s)) for s in labels]
        extreme += abs(statistic(shuffled)) >= abs(effect)
    return {'status': 'exploratory', 'n_overlap': n, 'strata': len(strata),
            'adjusted_residual_difference': effect,
            'permutation_p_two_sided': (extreme + 1) / (permutations + 1),
            'stratum_diagnostics': [dict(
                bin_lower=min(19, int(g[0]['p_final'] * 20)) / 20,
                **{label: dict(n=len(part),
                               mean_probability=sum(r['p_final'] for r in part) / len(part),
                               outcome_rate=sum(r['outcome'] for r in part) / len(part))
                   for label, sign in [('rise', 1), ('fall', -1)]
                   for part in [[r for r in g if r['direction'] == sign]]})
                for g in strata],
            'warning': 'Approximate conditioning; exchangeability and independent markets are unverified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('results/pilot'))
    parser.add_argument('--cache', type=Path, default=Path('data/cache'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--limit', type=int, default=200, choices=range(1, 1001), metavar='1..1000')
    parser.add_argument('--permutations', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=20261021)
    args = parser.parse_args()
    if args.permutations < 1:
        parser.error('--permutations must be positive')
    args.output.mkdir(parents=True, exist_ok=True)
    source = Source(args.cache, args.offline)
    started = datetime.now(timezone.utc).isoformat()
    try:
        markets = source.get('search-markets', term='', filter='resolved', sort='newest',
                             contractType='BINARY', limit=args.limit)
        if not isinstance(markets, list):
            raise RuntimeError('Unexpected market list schema')
        rows, excluded, seen = [], Counter(), set()
        for m in markets:
            if m['id'] in seen:
                continue
            seen.add(m['id'])
            m = source.get('market/' + urllib.parse.quote(m['id'], safe=''))
            if m.get('outcomeType') != 'BINARY' or m.get('resolution') not in ('YES', 'NO') or not m.get('isResolved'):
                excluded['not_unambiguous_binary_resolution'] += 1
                continue
            resolution = m.get('resolutionTime')
            created = m.get('createdTime')
            if not finite_number(resolution) or not finite_number(created):
                excluded['missing_times'] += 1
                continue
            # Retrospective event-time design: explicitly not a deployable decision time.
            final = resolution - 24 * HOUR
            previous = final - 24 * HOUR
            if created > previous:
                excluded['market_younger_than_48h_at_resolution'] += 1
                continue
            try:
                p, tp = snapshot(source, m['id'], final, 24 * HOUR)
                p0, tp0 = snapshot(source, m['id'], previous, 24 * HOUR)
            except ValueError as error:
                excluded[str(error)] += 1
                continue
            delta = p - p0
            rows.append(dict(id=m['id'], question=m.get('question'), creator=m.get('creatorId'),
                             resolution_time=resolution, final_cutoff=final, previous_cutoff=previous,
                             p_final=p, p_previous=p0, final_trade_time=tp, previous_trade_time=tp0,
                             delta=delta, direction=1 if delta >= .02 else -1 if delta <= -.02 else 0,
                             outcome=int(m['resolution'] == 'YES')))
        result = {'status': 'completed', 'started_utc': started, 'arguments': {
            k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
            'source': BASE, 'markets_returned': len(markets), 'unique_markets': len(seen),
            'exclusions': dict(excluded), 'n_eligible': len(rows),
            'directions': dict(Counter(r['direction'] for r in rows)),
            'analysis': analyse(rows, args.permutations, args.seed)}
        (args.output / 'observations.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        code = 0
    except Exception as error:
        result = {'status': 'blocked_or_failed', 'started_utc': started,
                  'error_type': type(error).__name__, 'error': str(error),
                  'scientific_result': None}
        code = 1
    result['responses'] = source.used
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.output / 'report.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in result.items() if k != 'responses'}, indent=2, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
