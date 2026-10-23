#!/usr/bin/env python3
"""reverify.py — renew an expiring official clock only where the cited page still states it.

The release gate expires an official observation 24 h after it is read (scripts/release.py). This
script looks at the page that produced each observation, and re-certifies the record only when the
re-fetched page still contains, close together, the fixture's two sides, the recorded clock and the
recorded zone label. Anything else is reported for review and left untouched.

Every accepted record gets the new ``checked_at`` and the verbatim line it was read from. A quote
is never synthesised, and an event whose page has moved on keeps its old, expiring observation.

Usage
-----
    python scripts/reverify.py --probe data/raw/cited-20261023T1810Z                # report only
    python scripts/reverify.py --probe ... --apply                                  # write records
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
ZONE_LABEL = {'UTC': ['utc', 'gmt'], 'ET': ['et', 'eastern'], 'CEST': ['cest'], 'CET': ['cet'],
              'Irish time': ['irish', 'ire & uk', 'ireland'], 'BST': ['bst']}
NOISE = {'the', 'and', 'vs', 'v', 'at', 'de', 'of', 'w', 'women', 'men', 'fc', 'bc', 'club'}


def tokens(value: str) -> set[str]:
    return {t for t in re.split(r'[^a-z0-9]+', (value or '').lower()) if len(t) > 2 and t not in NOISE}


def window(lines: list[str], index: int, radius: int = 4) -> str:
    return ' | '.join(lines[max(0, index - radius): index + radius + 1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--probe', required=True)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--only', nargs='*', default=None)
    args = ap.parse_args()

    probe = Path(args.probe)
    if not probe.is_absolute():
        probe = ROOT / probe
    manifest = json.loads((probe / 'manifest.json').read_text())
    fetched_at = manifest.get('started_at_utc')
    pages = {p['url']: p for p in manifest['pages']}
    match_rows = json.loads((DATA / 'matches.json').read_text())
    matches = {m['id']: m for m in match_rows}
    prefix_by_event = {}
    for m in match_rows:
        found = re.search(r'event_id=(\d+)', m.get('olbg_url') or '')
        if found:
            prefix_by_event[found.group(1)] = m['id'].rsplit('-', 1)[0]
    rc_path = DATA / 'release_checks.json'
    rc = json.loads(rc_path.read_text())
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    renewed, reviewed = [], []
    for event_id, record in sorted(rc['events'].items()):
        if (record.get('date') or '') < today:
            continue
        if args.only and event_id not in args.only:
            continue
        page = pages.get(record.get('source'))
        if not page or page.get('outcome') != 'captured' or not page.get('file'):
            reviewed.append((event_id, 'source page not captured', record.get('source')))
            continue
        path = probe / page['file']
        body = (path.read_text(encoding='utf-8', errors='replace') if path.suffix == '.txt'
                else json.dumps(json.loads(path.read_text())))
        lines = [l for l in body.splitlines() if l.strip()]
        row = matches.get(f"{prefix_by_event.get(event_id, '')}-{event_id}", {})
        sides = tokens(row.get('home', '')) | tokens(row.get('away', ''))
        if not sides:
            reviewed.append((event_id, 'no fixture names on the row', record.get('source')))
            continue
        clock = record.get('time') or ''
        zone = (record.get('timezone') or '').lower()
        zone_words = ZONE_LABEL.get(record.get('timezone'), [zone] if zone else [])
        hit = None
        for index, line in enumerate(lines):
            if clock and clock not in line:
                continue
            context = window(lines, index)
            low = context.lower()
            if len(sides & tokens(context)) < 2:
                continue
            if zone_words and not any(w in low for w in zone_words):
                # A page that no longer prints the zone label cannot renew a zone-derived clock.
                continue
            hit = (context, index)
            break
        if hit:
            renewed.append((event_id, record.get('source'), hit[0][:400]))
        else:
            reviewed.append((event_id, f'no line with both sides + {clock} + zone label', record.get('source')))

    print(f'RENEWABLE {len(renewed)}   NEEDS REVIEW {len(reviewed)}')
    for event_id, source, quote in renewed:
        print(f'\nRENEW {event_id}  {source}\n      {quote}')
    for event_id, why, source in reviewed:
        print(f'\nHOLD  {event_id}  {why}\n      {source}')

    if not args.apply:
        print('\n(report only; re-run with --apply to write the renewed records)')
        return 0

    applied = 0
    for event_id, source, quote in renewed:
        record = rc['events'][event_id]
        record['checked_at'] = fetched_at
        record['quote'] = quote.replace(' | ', ' ')
        record['renewed_from'] = source
        record['renewed_at'] = fetched_at
        applied += 1
    rc['checked_at'] = max([rc.get('checked_at') or '', fetched_at])
    rc['session'] = 'session-22dbc477 (2026-10-23 cited re-read)'
    rc_path.write_text(json.dumps(rc, indent=1) + '\n')
    print(f'\napplied {applied} renewed record(s); checked_at now {fetched_at}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
