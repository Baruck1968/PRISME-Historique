#!/usr/bin/env python3
"""Bounded GET range probe of the real trade ZIP; no inference from sample."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import urllib.request
import zlib

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/prisme2'


def main():
    meta = json.loads((OUT / 'source_metadata.json').read_text())['bets']
    request = urllib.request.Request(meta['url'], headers={'Range': 'bytes=0-65535'})
    with urllib.request.urlopen(request, timeout=60) as r:
        if r.status != 206 or not r.headers.get('Content-Range', '').startswith('bytes 0-65535/'):
            raise RuntimeError('Server did not honor bounded range; not downloading full archive')
        body = r.read(65537)
        headers = {k.lower(): v for k, v in r.headers.items()
                   if k.lower() in ('content-range', 'etag', 'x-goog-generation')}
    if len(body) != 65536 or body[:4] != b'PK\x03\x04':
        raise RuntimeError('Unexpected range or ZIP header')
    header = struct.unpack('<4s5H3I2H', body[:30])
    method, name_length, extra_length = header[3], header[-2], header[-1]
    name = body[30:30+name_length].decode()
    if method != 8:
        raise RuntimeError('Expected deflated ZIP member')
    offset = 30 + name_length + extra_length
    plain = zlib.decompressobj(-15).decompress(body[offset:], 262144).decode('utf-8', errors='strict')
    decoder = json.JSONDecoder()
    pos = 1
    rows = []
    if not plain.startswith('['):
        raise RuntimeError('Expected trade JSON array')
    for _ in range(10):
        while pos < len(plain) and plain[pos] in ' \r\n\t,':
            pos += 1
        row, pos = decoder.raw_decode(plain, pos)
        rows.append(row)
    (OUT / 'trade_archive_prefix.bin').write_bytes(body)
    (OUT / 'trade_archive_sample.json').write_text(json.dumps(rows, indent=2))
    report = {'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'url': meta['url'], 'headers': headers, 'zip_member': name,
              'range_bytes': len(body), 'range_sha256': hashlib.sha256(body).hexdigest(),
              'records_examined': len(rows), 'fields': sorted(set().union(*(r.keys() for r in rows))),
              'with_createdTime': sum(isinstance(r.get('createdTime'), (int, float)) for r in rows),
              'with_probAfter': sum(isinstance(r.get('probAfter'), (int, float)) for r in rows),
              'complete_zip_checksum_verified': False,
              'limitations': 'Prefix probe only; no full archive CRC/MD5, temporal coverage or representativeness claim. No statistical use.'}
    (OUT / 'trade_probe.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
