#!/usr/bin/env python3
"""Read-only bounded as-of trade audit for a predefined real-data sample."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/prisme3'
HOUR = 3_600_000


def numeric(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def asof_proxy(bets, cutoff):
    """Only non-limit executed records wholly timestamped before cutoff.

    This is a last eligible trade probability, NOT a certified historical quote.
    """
    rejected = Counter()
    candidates = []
    for b in bets:
        if b.get('isAnte') or b.get('isRedemption') or b.get('limitProb') is not None:
            rejected['ante_redemption_or_resting_limit'] += 1
            continue
        if not numeric(b.get('amount')) or b['amount'] == 0:
            rejected['no_recorded_execution_amount'] += 1
            continue
        if not numeric(b.get('createdTime')) or not numeric(b.get('probAfter')) or not 0 <= b['probAfter'] <= 1:
            rejected['missing_or_invalid_time_probability'] += 1
            continue
        fills = b.get('fills') or []
        if any(not numeric(f.get('timestamp')) for f in fills):
            rejected['undated_fill'] += 1
            continue
        completed = max([b['createdTime']] + [f['timestamp'] for f in fills])
        if completed > cutoff:
            rejected['execution_after_cutoff'] += 1
            continue
        candidates.append((completed, b))
    candidates.sort(key=lambda item: item[0], reverse=True)
    base = {'raw_records': len(bets),
            'records_updated_after_cutoff': sum(numeric(b.get('updatedTime')) and b['updatedTime'] > cutoff for b in bets), 'rejected': dict(rejected), 'cutoff_ms': cutoff,
            'historical_quote_certified': False}
    if not candidates:
        return dict(base, status='no_eligible_trade' if len(bets) < 1000 else 'page_cap_inconclusive')
    when, b = candidates[0]
    if len({r['probAfter'] for ts, r in candidates if ts == when}) != 1:
        return dict(base, status='ambiguous_same_time_probabilities')
    if len(bets) == 1000 and min(r['createdTime'] for r in bets) >= when:
        return dict(base, status='page_boundary_inconclusive')
    return dict(base, status='fresh_trade_proxy' if cutoff-when <= 24*HOUR else 'stale_trade_proxy',
                trade_id=b['id'], executed_ms=when, probability=b['probAfter'], age_ms=cutoff-when)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    manual = json.loads((OUT / 'manual_audit_markets.json').read_text())
    sample = [v for i, v in enumerate(manual) if i < 4 or v['snapshot']['question'].startswith('NFL')]
    archive = OUT / 'price_probe_responses.zip'
    if args.offline:
        with zipfile.ZipFile(archive) as z:
            cached = {name: z.read(name) for name in z.namelist()}
    else:
        if archive.exists():
            raise RuntimeError('Existing response cache preserved: use --offline for replay')
        cached = {}
    reports, metadata = [], []
    for item in sample:
        r = item['observation']
        pair = {}
        for label, cutoff in [('t', r['t_ms']), ('t_minus_24h', r['previous_t_ms'])]:
            url = 'https://api.manifold.markets/v0/bets?' + urllib.parse.urlencode(
                sorted({'contractId': r['id'], 'beforeTime': cutoff+1, 'limit': 1000}.items()))
            key = hashlib.sha256(url.encode()).hexdigest()+'.json'
            if args.offline:
                raw = cached[key]
                meta = json.loads(cached[key+'.meta'])
            else:
                with urllib.request.urlopen(url, timeout=45) as response:
                    raw = response.read()
                meta = {'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                        'sha256': hashlib.sha256(raw).hexdigest()}
                cached[key] = raw
                cached[key+'.meta'] = json.dumps(meta).encode()
                # Persist each completed request. Never overwrite prior experiments.
                with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
                    for name, content in cached.items():
                        z.writestr(name, content)
            if hashlib.sha256(raw).hexdigest() != meta['sha256']:
                raise RuntimeError('Response checksum failure')
            bets = json.loads(raw)
            if not isinstance(bets, list) or any(b.get('contractId') != r['id'] for b in bets):
                raise RuntimeError('Unexpected trade response schema/market')
            pair[label] = asof_proxy(bets, cutoff)
            metadata.append(meta)
        reports.append({'market_id': r['id'], 't_ms': r['t_ms'], 'snapshots': pair,
                        'both_proxies_fresh': all(v['status'] == 'fresh_trade_proxy' for v in pair.values()),
                        'eligible_for_predictive_analysis': False})
    result = {'purpose': 'Bounded technical reconstruction probe, not predictive analysis',
              'selection': 'First four manual sample records and NFL titles in that sample',
              'markets_probed': len(reports), 'requests': len(metadata),
              'both_fresh_trade_proxies': sum(r['both_proxies_fresh'] for r in reports),
              'certified_complete_trajectories': 0,
              'limitations': ['Final API records may have changed since t; resting limit orders and post-cutoff fills rejected.',
                              'No full liquidity history, historical mechanism certification, or public-knowledge audit is supplied by a price.',
                              'The selected initiating trade is a probability proxy, not proof of the exact quote at cutoff.',
                              'API evidence does not establish coverage of the historical trade dump.'],
              'observations': reports, 'responses': metadata}
    (OUT / 'price_probe.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('responses','observations')}, indent=2))


if __name__ == '__main__':
    main()
