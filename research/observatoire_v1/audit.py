"""Read-only public documentation audit. No API key, signup, or odds endpoint."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

SOURCES = {
    'hyphen_docs': 'https://the-odds-api.com/liveapi/guides/v4/',
    'hyphen_prices': 'https://the-odds-api.com/#pricing',
    'hyphen_terms': 'https://the-odds-api.com/terms-and-conditions.html',
    'hyphen_markets': 'https://the-odds-api.com/sports-odds-data/betting-markets.html',
    'hyphen_intervals': 'https://the-odds-api.com/sports-odds-data/update-intervals.html',
    'hyphen_history': 'https://the-odds-api.com/historical-odds-data/',
    'distinct_docs': 'https://theoddsapi.com/docs/',
    'distinct_terms': 'https://theoddsapi.com/terms',
    'distinct_about': 'https://theoddsapi.com/about',
    'distinct_faq': 'https://theoddsapi.com/faq',
    'distinct_schema': 'https://theoddsapi.com/openapi.json',
    'distinct_prices': 'https://theoddsapi.com/pricing',
}

def main():
    root = Path(__file__).resolve().parent
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    cache = root / '.cache' / stamp
    cache.mkdir(parents=True)
    rows = []
    for name, url in SOURCES.items():
        row = dict(name=name, url=url, attempted_at=datetime.now(timezone.utc).isoformat())
        try:
            with urlopen(url, timeout=25) as r:
                data = r.read()
                row.update(status=r.status, final_url=r.url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), soft_404=('Four-Oh-Four' in data.decode(errors='replace') or '/404.html' in r.url))
            (cache / (name + '.html')).write_bytes(data)
        except Exception as exc:
            row.update(error_type=type(exc).__name__, error=str(exc))
        rows.append(row)
    output = root / ('access_' + stamp + '.json')
    output.write_text(json.dumps(rows, indent=2) + '\n')
    print(output)

if __name__ == '__main__':
    main()
