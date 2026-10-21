"""Prospective read-only capture and conservative paired comparison (stdlib only).

No scheduler or alerts. Raw odds and journal must remain private. See README.
"""
import argparse
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from file_lock import locked
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

UTC = timezone.utc

def iso(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.utcoffset() != timedelta(0):
        raise ValueError('UTC required')
    return d

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def variation(first, second):
    a, b = Decimal(str(first)), Decimal(str(second))
    if not a.is_finite() or not b.is_finite() or min(a, b) <= 1:
        raise ValueError('Finite decimal odds > 1 required')
    pct = 100 * (b - a) / a
    return {'percent': str(pct), 'threshold_reached': abs(pct) >= 20}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused')

def verify(root):
    previous = None
    count = 0
    journal = root / 'journal.jsonl'
    if not journal.exists():
        return 0
    for line in journal.read_text().splitlines():
        entry = json.loads(line)
        claimed = entry.pop('entry_sha256')
        if entry['previous'] != previous or digest(encoded(entry)) != claimed:
            raise ValueError('Journal chain mismatch')
        filename = entry['file']
        if Path(filename).name != filename:
            raise ValueError('Unsafe journal filename')
        if digest((root / filename).read_bytes()) != entry['sha256']:
            raise ValueError('Capture hash mismatch')
        previous = claimed
        count += 1
    return count

def store(root, envelope):
    with locked(root):
        verify(root)
        journal = root / 'journal.jsonl'
        lines = journal.read_text().splitlines() if journal.exists() else []
        previous = json.loads(lines[-1])['entry_sha256'] if lines else None
        filename = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ_') + uuid.uuid4().hex + '.json'
        raw = encoded(envelope)
        with (root / filename).open('xb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        entry = {'file': filename, 'sha256': digest(raw), 'previous': previous}
        entry['entry_sha256'] = digest(encoded(entry))
        with journal.open('a') as f:
            f.write(encoded(entry).decode() + '\n'); f.flush(); os.fsync(f.fileno())
        return filename

def capture(args):
    key = os.environ.get('THE_ODDS_API_KEY')
    if not key:
        raise ValueError('Missing THE_ODDS_API_KEY; obtain a free key yourself, no subscription needed')
    if not re.fullmatch(r'[a-z0-9_]+', args.sport) or not re.fullmatch(r'[a-z0-9_]+', args.bookmaker):
        raise ValueError('Invalid provider identifiers')
    # One sport, one market, one bookmaker: normally 1 credit / nonempty response.
    params = dict(apiKey=key, bookmakers=args.bookmaker, markets='h2h', oddsFormat='decimal', dateFormat='iso')
    base = 'https://api.the-odds-api.com/v4/sports/' + args.sport + '/odds/'
    started = datetime.now(UTC).isoformat()
    envelope = {'source': 'the-odds-api.com', 'sport': args.sport, 'bookmaker': args.bookmaker,
                'market': 'h2h', 'requested_at': started, 'endpoint': base,
                'anchor_type': 'scheduled_start_proxy', 'status': 'failed'}
    try:
        req = Request(base + '?' + urlencode(params), method='GET')
        with build_opener(NoRedirect()).open(req, timeout=30) as r:
            body = r.read()
            if key.encode() in body:
                raise ValueError('Credential echoed in response; storage refused')
            envelope.update(status='captured', received_at=datetime.now(UTC).isoformat(),
                            raw_utf8=body.decode(), body_sha256=digest(body),
                            quota={k: r.headers.get(k) for k in ('x-requests-used','x-requests-remaining','x-requests-last')})
            # Store exactly received body, including invalid JSON, before downstream analysis.
    except Exception as exc:
        # Never stringify HTTP errors: they may include a key-bearing URL.
        envelope.update(error_type=type(exc).__name__, received_at=datetime.now(UTC).isoformat())
    filename = store(args.output, envelope)
    print(json.dumps({'file': filename, 'status': envelope['status']}))
    return 0 if envelope['status'] == 'captured' else 1

def extract(envelope, event_id, bookmaker, rules_id):
    if envelope['status'] != 'captured':
        raise ValueError('Failed capture')
    raw = envelope['raw_utf8'].encode()
    if digest(raw) != envelope['body_sha256']:
        raise ValueError('Body hash mismatch')
    events = json.loads(raw)
    matches = [e for e in events if e['id'] == event_id]
    if len(matches) != 1:
        raise ValueError('Missing or duplicate event')
    event = matches[0]
    books = [b for b in event['bookmakers'] if b['key'] == bookmaker]
    if len(books) != 1:
        raise ValueError('Missing or duplicate bookmaker')
    markets = [m for m in books[0]['markets'] if m['key'] == 'h2h']
    if len(markets) != 1:
        raise ValueError('Missing or duplicate h2h')
    market = markets[0]
    outcomes = market['outcomes']
    if len(outcomes) != 2 or {o['name'] for o in outcomes} != {event['home_team'], event['away_team']}:
        raise ValueError('Not an unambiguous two-team binary market')
    prices = {o['name']: o['price'] for o in outcomes}
    if len(prices) != 2:
        raise ValueError('Duplicate outcomes')
    for price in prices.values():
        variation(price, price)
    return dict(source=envelope['source'], event=event_id, sport=event['sport_key'], bookmaker=bookmaker,
                market='h2h', rules_id=rules_id, anchor_type='scheduled_start_proxy',
                commence_time=event['commence_time'], requested_at=envelope['requested_at'],
                received_at=envelope['received_at'], last_update=market.get('last_update'),
                # Presence and last_update do NOT prove the bookmaker accepts bets.
                open_status='unknown', prices=prices)

def compare(a, b, *, tolerance_seconds=300, max_age_seconds=120):
    reasons = []
    for key in ('source','event','sport','bookmaker','market','rules_id','anchor_type','commence_time'):
        if a.get(key) != b.get(key):
            reasons.append('changed_' + key)
    if not a.get('rules_id') or not b.get('rules_id'):
        reasons.append('unverified_rules')
    if set(a['prices']) != set(b['prices']) or len(a['prices']) != 2:
        reasons.append('changed_or_nonbinary_outcomes')
    anchor = iso(a['commence_time'])  # Frozen J-1 anchor; never recompute from future start.
    for label, row, hours in [('J1', a, 24), ('H1', b, 1)]:
        start, end = iso(row['requested_at']), iso(row['received_at'])
        target = anchor - timedelta(hours=hours)
        if end < start or max(abs((start-target).total_seconds()), abs((end-target).total_seconds())) > tolerance_seconds:
            reasons.append(label + '_outside_window')
        if end >= anchor:
            reasons.append(label + '_event_started')
        updated = row.get('last_update')
        if not updated:
            reasons.append(label + '_missing_market_timestamp')
        elif not 0 <= (start - iso(updated)).total_seconds() <= max_age_seconds:
            reasons.append(label + '_stale_or_future_update')
        if row.get('open_status') != 'open':
            reasons.append(label + '_unconfirmed_open_status')
    if iso(b['requested_at']) <= iso(a['received_at']):
        reasons.append('duplicate_or_nonchronological')
    identity_changed = any(reason.startswith('changed_') for reason in reasons)
    changes = {} if identity_changed else {name: variation(a['prices'][name], b['prices'][name]) for name in sorted(set(a['prices']) & set(b['prices']))}
    valid = not reasons
    return {'valid': valid, 'exclusions': reasons, 'candidate_changes': changes,
            'alerts': [name for name, v in changes.items() if valid and v['threshold_reached']]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('capture')
    c.add_argument('--sport', required=True)
    c.add_argument('--bookmaker', required=True)
    c.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'private')
    v = sub.add_parser('verify')
    v.add_argument('directory', type=Path)
    a = sub.add_parser('compare')
    a.add_argument('j1', type=Path); a.add_argument('h1', type=Path)
    a.add_argument('--event', required=True); a.add_argument('--bookmaker', required=True)
    a.add_argument('--rules-id', default='')
    args = p.parse_args()
    try:
        if args.command == 'capture':
            return capture(args)
        if args.command == 'verify':
            with locked(args.directory):
                print(json.dumps({'verified_entries': verify(args.directory)}))
        else:
            rows = [extract(json.loads(path.read_text()), args.event, args.bookmaker, args.rules_id) for path in (args.j1, args.h1)]
            print(json.dumps(compare(*rows), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({'error_type': type(exc).__name__, 'status': 'blocked'}))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
