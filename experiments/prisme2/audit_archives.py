#!/usr/bin/env python3
"""Read-only PRISME 2 feasibility audit. Never fits a predictive model."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile
import base64

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'experiments/prisme2/sampling_plan.json'
CUTOFF = 1720051200000  # 2024-07-04T00:00:00Z, conservative common coverage.


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def records(stream):
    """Stream a single JSON array; reject truncated input and trailing content."""
    decoder = json.JSONDecoder()
    text, pos, eof = '', 0, False
    def refill():
        nonlocal text, pos, eof
        text = text[pos:]
        pos = 0
        block = stream.read(1024 * 1024)
        eof = not block
        text += block
    def whitespace():
        nonlocal pos
        while True:
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos < len(text) or eof:
                return
            refill()
    refill()
    whitespace()
    if text[pos:pos+1] != '[':
        raise ValueError('Expected JSON array')
    pos += 1
    whitespace()
    if text[pos:pos+1] != ']':
        while True:
            while True:
                try:
                    obj, end = decoder.raw_decode(text, pos)
                    break
                except json.JSONDecodeError:
                    if eof:
                        raise
                    refill()
            if not isinstance(obj, dict):
                raise ValueError('Non-object archive record')
            pos = end
            yield obj
            whitespace()
            token = text[pos:pos+1]
            if token == ']':
                break
            if token != ',':
                raise ValueError('Expected comma or closing bracket')
            pos += 1
            whitespace()
    pos += 1
    whitespace()
    if pos != len(text):
        raise ValueError('Trailing content')


def fetch_metadata(url):
    with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=60) as r:
        return {'url': url, 'status': r.status, 'headers': {
            k.lower(): v for k, v in r.headers.items()
            if k.lower() in ('content-length', 'last-modified', 'etag', 'x-goog-generation', 'x-goog-hash')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / 'data/prisme2/markets.zip')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/prisme2')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plan = json.loads(PLAN.read_text())
    doc = (ROOT / 'results/source-check/data.md').read_text()
    urls = {kind: re.search(r'\[' + label + r'[^\]]*\]\(([^)]+)', doc).group(1)
            for kind, label in [('markets', 'Markets data'), ('bets', 'Bets data')]}
    metadata_path = args.output / 'source_metadata.json'
    if args.offline:
        metadata = json.loads(metadata_path.read_text())
    else:
        metadata = {kind: fetch_metadata(url) for kind, url in urls.items()}
        metadata_path.write_text(json.dumps(metadata, indent=2))
    if not args.archive.exists():
        if args.offline:
            raise RuntimeError('Archive absent in offline mode')
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urls['markets'], timeout=120) as r, args.archive.open('xb') as f:
            while block := r.read(1024 * 1024):
                f.write(block)
    headers = metadata['markets']['headers']
    if args.archive.stat().st_size != int(headers['content-length']):
        raise RuntimeError('Archive size does not match source')
    # Verify published MD5 for transport integrity, plus local SHA-256 provenance.
    match = re.search(r'md5=([^,]+)', headers.get('x-goog-hash', ''))
    if not match:
        raise RuntimeError('Source does not supply expected MD5')
    md5 = hashlib.md5(usedforsecurity=False)
    with args.archive.open('rb') as f:
        while block := f.read(1024 * 1024):
            md5.update(block)
    if base64.b64encode(md5.digest()).decode() != match.group(1):
        raise RuntimeError('Published archive checksum mismatch')
    digest = sha(args.archive)
    lock = json.loads((PLAN.parent / 'source_lock.json').read_text())
    if digest != lock['markets_sha256'] or headers['x-goog-generation'] != lock['markets_generation']:
        raise RuntimeError('Source changed relative to the frozen PRISME 2 archive')
    counts, fields, candidate_fields, mechanisms, resolutions = [Counter() for _ in range(5)]
    selected, audit, ids = [], [], set()
    min_created, max_created = None, None
    with zipfile.ZipFile(args.archive) as z:
        members = [m for m in z.infolist() if not m.is_dir()]
        if len(members) != 1 or not members[0].filename.endswith('.json'):
            raise RuntimeError('Unexpected archive members')
        member = members[0]
        with z.open(member) as raw, io.TextIOWrapper(raw, encoding='utf-8') as stream:
            for m in records(stream):
                counts['all_markets'] += 1
                if m['id'] in ids:
                    raise RuntimeError('Duplicate market ID')
                ids.add(m['id'])
                fields.update(m.keys())
                for k in m:
                    if any(s in k.lower() for s in ('close', 'deadline', 'history', 'initial', 'original', 'event', 'edit')):
                        candidate_fields[k] += 1
                created = m.get('createdTime')
                if isinstance(created, (float, int)):
                    min_created = created if min_created is None else min(min_created, created)
                    max_created = created if max_created is None else max(max_created, created)
                if m.get('outcomeType') != 'BINARY':
                    counts['excluded_nonbinary'] += 1
                    continue
                counts['binary'] += 1
                if not m.get('isResolved') or m.get('resolution') not in ('YES', 'NO'):
                    counts['excluded_not_yes_no_resolved'] += 1
                    continue
                rt = m.get('resolutionTime')
                if not isinstance(rt, (int, float)) or rt >= CUTOFF:
                    counts['excluded_resolution_outside_common_coverage'] += 1
                    continue
                counts['candidate_population'] += 1
                mechanisms[str(m.get('mechanism'))] += 1
                resolutions[m['resolution']] += 1
                ct = m.get('closeTime')
                if isinstance(ct, (int, float)):
                    counts['candidates_with_closeTime'] += 1
                    counts['closeTime_equals_resolutionTime'] += int(ct == rt)
                    counts['closeTime_before_resolutionTime'] += int(ct < rt)
                    counts['closeTime_after_resolutionTime'] += int(ct > rt)
                # A snapshot timestamp or a textual date is NOT proof of ex-ante publication.
                selected.append({'id': m['id'], 'createdTime': created,
                                 'closeTime': ct, 'resolutionTime': rt,
                                 'deadline_provenance': 'not_verified',
                                 'event_key': None, 'predictive_eligible': False})
                key = hashlib.sha256(m['id'].encode()).hexdigest()
                if len(audit) < 12 or key < audit[-1][0]:
                    audit.append((key, m))
                    audit.sort(key=lambda pair: pair[0])
                    audit = audit[:12]
        # Reaching end of member also validates its ZIP CRC.
    observed_temporal_fields = set(candidate_fields)
    reviewed_snapshot_fields = {'closeTime', 'closeEmailsSent', 'initialProbability'}
    if observed_temporal_fields != reviewed_snapshot_fields:
        raise RuntimeError('Unexpected provenance schema: manual re-audit required')
    report = {
        'status': 'non_conclusive_predictive_test_not_run',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'sampling_plan_sha256': sha(PLAN), 'source_lock_sha256': sha(PLAN.parent / 'source_lock.json'), 'script_sha256': sha(Path(__file__)),
        'archive': {'path': 'data/prisme2/markets.zip', 'sha256': digest,
                    'md5_matches_published_source': True, 'zip_crc_validated': True,
                    'compressed_bytes': args.archive.stat().st_size,
                    'member': member.filename, 'uncompressed_bytes': member.file_size},
        'counts': dict(counts), 'fields': dict(sorted(fields.items())),
        'deadline_or_history_or_event_fields': dict(sorted(candidate_fields.items())),
        'candidate_mechanisms': dict(mechanisms), 'candidate_resolutions': dict(resolutions),
        'created_time_range_ms': [min_created, max_created],
        'verified_ex_ante_deadlines': 0, 'predictive_eligible': 0,
        'deadline_verification_coverage': 0.0,
        'model_fits': 0, 'permutations_executed': 0, 'statistical_result': None,
        'blockers': ['No timestamped creation-time deadline or complete edit history verified in this snapshot.',
                     'No audited common-event mapping; market IDs are not independent event IDs.',
                     'Snapshot liquidity and uniqueBettorCount are post-observation fields, not admissible ex-ante covariates.'],
        'trade_archive_downloaded': False,
        'trade_archive_note': 'Separate bounded prefix probe available in trade_probe.json. Full download deferred because the deadline gate failed.',
        'coverage_note': 'Market archive July 6 vs transaction archive July 4. July 4 00:00 UTC is a conservative label-based bound, not proof of full transaction coverage.',
        'manual_audit_sample': [m['id'] for _, m in audit]}
    (args.output / 'feasibility.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (args.output / 'manual_audit_markets.json').write_text(json.dumps([m for _, m in audit], indent=2, ensure_ascii=False))
    with (args.output / 'candidate_deadline_audit.jsonl').open('w') as f:
        for row in selected:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('fields',)}, indent=2))


if __name__ == '__main__':
    main()
