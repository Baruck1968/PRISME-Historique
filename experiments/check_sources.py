#!/usr/bin/env python3
"""Probe official archive documentation, archive HEAD, API and timestamped trades."""
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from datetime import datetime, timezone

ROOT = 'https://raw.githubusercontent.com/manifoldmarkets/manifold/main/docs/docs/'


def main():
    output = Path('results/source-check')
    output.mkdir(parents=True, exist_ok=True)
    report = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'checks': []}
    def request(label, url, method='GET', save=None):
        entry = {'label': label, 'url': url, 'method': method}
        report['checks'].append(entry)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method=method), timeout=30) as r:
                body = r.read() if method == 'GET' else b''
                entry.update(status=r.status, bytes=len(body))
            if save:
                (output / save).write_bytes(body)
                entry['sha256'] = hashlib.sha256(body).hexdigest()
            return body
        except Exception as error:
            entry.update(error_type=type(error).__name__, error=str(error))
            return None
    doc = request('official_archive_documentation', ROOT + 'data.md', save='data.md')
    request('official_api_documentation', ROOT + 'api.md', save='api.md')
    if doc:
        for label, url in re.findall(r'\[(Markets data[^\]]*|Bets data[^\]]*)\]\(([^)]+)\)', doc.decode()):
            request(label, url, 'HEAD')
    raw = request('resolved_binary_markets', 'https://api.manifold.markets/v0/search-markets?filter=resolved&contractType=BINARY&sort=newest&limit=10', save='markets.json')
    if raw:
        markets = json.loads(raw)
        if markets:
            mid = markets[0]['id']
            bets = request('timestamped_history', 'https://api.manifold.markets/v0/bets?contractId=' + mid + '&limit=10', save='bets.json')
            if bets:
                records = json.loads(bets)
                report['history_records_with_time_and_probability'] = sum(
                    isinstance(b.get('createdTime'), (int, float)) and
                    isinstance(b.get('probAfter'), (int, float)) for b in records)
    (output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    # Report each independent access result; no success claim from docs alone.
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return int(any('error' in x for x in report['checks']))


if __name__ == '__main__':
    raise SystemExit(main())
