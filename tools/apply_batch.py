#!/usr/bin/env python3
"""apply_batch.py — apply one reviewable fixture batch to the board inputs.

A "batch" is a JSON file written by an agent session that has just read the sources it
cites. It is deliberately explicit: every fixture row, every official confirmation, every
release check, every pricing table and every written piece is spelled out, so a reviewer can
diff the batch against the source pages rather than reverse-engineer a pipeline run.

The script only *writes* the batch into the existing inputs; it never invents a value:

  * data/sports/<sport>.json   — upsert the fixture rows (keyed by ``ref``)
  * data/official.json         — upsert ``fixture_confirmations[ref]`` and ``form_data[key]``
  * data/release_checks.json   — upsert ``events[str(event_id)]``
  * data/predictions.json      — upsert the written pieces (keyed by ``ref``)

Everything downstream (scripts/model.py, scripts/build_site.py, the checkers) is unchanged.

Usage
-----
    python tools/apply_batch.py data/batches/20261024-a30d9bdb.json
    python tools/apply_batch.py <batch> --check   # report what would change, write nothing
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

SPORT_FILES = {
    'Tennis': 'tennis', 'Basketball': 'basketball', 'Golf': 'golf', 'Cricket': 'cricket',
    'Snooker': 'snooker', 'Rugby Union': 'rugby_union', 'Rugby League': 'rugby_league',
    'Baseball': 'baseball', 'Ice Hockey': 'ice_hockey', 'Motor Racing': 'motor_racing',
    'Darts': 'darts', 'Handball': 'handball', 'Volleyball': 'volleyball',
    'Gaelic Football': 'gaelic_football', 'Greyhounds': 'greyhounds',
}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('batch')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    spec = load(Path(args.batch))
    changes = []

    # ---- fixture rows ----
    for sport, rows in (spec.get('sports') or {}).items():
        slug = SPORT_FILES.get(sport)
        if slug is None:
            raise SystemExit(f'unknown sport {sport!r}; add it to SPORT_FILES rather than guessing a file')
        path = DATA / 'sports' / f'{slug}.json'
        blob = load(path)
        by_ref = {r['ref']: r for r in blob['events']}
        for row in rows:
            for key in ('ref', 'home', 'away', 'start', 'market', 'olbg_pick', 'event_url', 'event_id'):
                if not row.get(key):
                    raise SystemExit(f'{sport}: row is missing {key}: {row}')
            if 'olbg.com' not in row['event_url'] or 'event_id=' not in row['event_url']:
                raise SystemExit(f"{row['ref']}: event_url must be the OLBG page carrying the event id")
            new = row['ref'] not in by_ref or by_ref[row['ref']] != row
            if new:
                changes.append(f"event {row['ref']} ({sport})")
            if row['ref'] in by_ref:
                blob['events'][blob['events'].index(by_ref[row['ref']])] = row
            else:
                blob['events'].append(row)
            by_ref[row['ref']] = row
        if not args.check:
            save(path, blob)

    # ---- official confirmations + pricing tables ----
    off_path = DATA / 'official.json'
    off = load(off_path)
    for ref, conf in (spec.get('confirmations') or {}).items():
        if off['fixture_confirmations'].get(ref) != conf:
            changes.append(f'confirmation {ref}')
        off['fixture_confirmations'][ref] = conf
    for key, table in (spec.get('form_tables') or {}).items():
        if off['form_data'].get(key) != table:
            changes.append(f'form table {key}')
        off['form_data'][key] = table
    if not args.check:
        save(off_path, off)

    # ---- release checks (official, timezone-qualified clocks only) ----
    rc_path = DATA / 'release_checks.json'
    rc = load(rc_path)
    for event_id, record in (spec.get('release_checks') or {}).items():
        if record.get('kind') != 'exact' or not record.get('timezone'):
            raise SystemExit(f'release check {event_id}: only exact, timezone-qualified clocks may be recorded')
        if rc['events'].get(str(event_id)) != record:
            changes.append(f'release check {event_id}')
        rc['events'][str(event_id)] = record
    if not args.check:
        rc['checked_at'] = max([rc.get('checked_at') or ''] +
                               [r.get('checked_at') or '' for r in (spec.get('release_checks') or {}).values()])
        save(rc_path, rc)

    # ---- written pieces ----
    pr_path = DATA / 'predictions.json'
    pr = load(pr_path)
    by_ref = {p['ref']: p for p in pr['predictions']}
    for piece in (spec.get('predictions') or []):
        if piece.get('status') not in ('high', 'analysis'):
            raise SystemExit(f"{piece.get('ref')}: status must be 'high' or 'analysis'")
        if len(piece.get('body', '').split()) < 30:
            raise SystemExit(f"{piece.get('ref')}: body is under the 30-word minimum")
        if by_ref.get(piece['ref']) != piece:
            changes.append(f"prediction {piece['ref']}")
        if piece['ref'] in by_ref:
            pr['predictions'][pr['predictions'].index(by_ref[piece['ref']])] = piece
        else:
            pr['predictions'].append(piece)
        by_ref[piece['ref']] = piece
    if not args.check:
        save(pr_path, pr)

    print(f'{len(changes)} change(s)')
    for line in changes:
        print('  ', line)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
