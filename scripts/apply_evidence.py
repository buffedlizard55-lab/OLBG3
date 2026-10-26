#!/usr/bin/env python3
"""apply_evidence.py — turn a committed, derived official-source read into release evidence.

Why this exists
---------------
``scripts/verify_live.py`` can only certify fixtures that appear in an *official probe* payload
(NHL / MLB JSON). Several in-scope competitions publish their fixture clocks only as a PDF or a
server-rendered table, so a prior session had to transcribe them by hand — which is how a clock
can drift from its source without anyone noticing. This script keeps that transcription honest:

  1. the bytes are fetched by the CI runner into ``data/raw/cited-*`` / ``urls-*`` (committed);
  2. a derived text sidecar is produced once from those bytes (``data/raw/derived-<session>/``);
  3. every record in ``fixture-quotes.json`` is a **literal slice** of that sidecar, re-derived
     here from the stored markers before anything is written.

If a slice no longer matches the committed bytes, the record is refused and the run fails: no
release clock is renewed off a quote that the evidence does not contain. Nothing is inferred —
the only arithmetic is the zone conversion the record itself names (CET = UTC+1).

What it writes
--------------
* ``data/release_checks.json``  → one ``events[<olbg event id>]`` exact-clock record per fixture;
* ``data/verifications.json``   → the matching ``event_verifications`` entry.

Both files are append-only in spirit: an existing record is only replaced when the new
observation is at least as new as the one it replaces.

Usage
-----
    python scripts/apply_evidence.py                       # apply everything under data/raw/derived-*/
    python scripts/apply_evidence.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
UTC = dt.timezone.utc


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(UTC)


def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    return json.loads(text)


def rederive(record: dict, text: str) -> str:
    """Rebuild the quote from the record's own markers and prove it matches the stored slice."""
    team, date_line, time_line = record['team_line'], record['date_line'], record['time_line']
    start = text.find(team)
    if start < 0:
        raise SystemExit(f"refused: fixture line not found in derived text: {team!r}")
    date_at = text.find(date_line, start)
    if date_at < 0:
        raise SystemExit(f"refused: date {date_line!r} not found after {team!r}")
    time_at = text.find(time_line, date_at)
    if time_at < 0:
        raise SystemExit(f"refused: time {time_line!r} not found after {date_line!r} for {team!r}")
    return text[start:time_at + len(time_line)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--derived', default=None, help='one derived-* directory; default: all')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    base = DATA / 'raw'
    dirs = ([Path(args.derived)] if args.derived else
            sorted(p for p in base.glob('derived-*') if (p / 'fixture-quotes.json').exists()))
    if not dirs:
        print('apply_evidence: no derived evidence directories found')
        return 0

    releases_path = DATA / 'release_checks.json'
    verifications_path = DATA / 'verifications.json'
    releases = load_manifest(releases_path)
    verifications = load_manifest(verifications_path)
    applied, refused = 0, []

    for directory in dirs:
        doc = load_manifest(directory / 'fixture-quotes.json')
        manifest = load_manifest(ROOT / doc['derived_manifest'])
        derived_path = ROOT / doc['derived_text']
        text = derived_path.read_text(encoding='utf-8')
        expected = manifest.get('text_sha256')
        actual = __import__('hashlib').sha256(derived_path.read_bytes()).hexdigest()
        if expected and expected != actual:
            raise SystemExit(f'refused: derived text {derived_path} does not match its manifest sha256')
        checked_at = doc['checked_at']
        if parse_utc(checked_at) > dt.datetime.now(UTC):
            raise SystemExit('refused: an observation stamp cannot be later than the clock that records it')

        for record in doc['records']:
            quote = rederive(record, text)
            if quote != record['quote']:
                refused.append((record['event_id'], 'quote does not re-derive from the committed bytes'))
                continue
            if record['zone_quote'] not in text:
                refused.append((record['event_id'], 'zone header not present in the derived text'))
                continue
            start = parse_utc(record['start_utc'])
            local = dt.datetime.fromisoformat(record['date'] + 'T' + record['time_local'] + ':00')
            offset = {'CET': 1, 'CEST': 2, 'UTC': 0}.get(record['timezone'])
            if offset is None:
                refused.append((record['event_id'], f"unknown zone {record['timezone']!r}"))
                continue
            if (local - dt.timedelta(hours=offset)).replace(tzinfo=UTC) != start:
                refused.append((record['event_id'], 'declared zone conversion does not equal start_utc'))
                continue

            existing = releases['events'].get(record['event_id'])
            if existing and parse_utc(existing.get('checked_at', '1970-01-01T00:00:00Z')) > parse_utc(checked_at):
                continue  # an observation that has already been superseded is never restored
            releases['events'][record['event_id']] = {
                'date': record['date'],
                'time': record['time_local'],
                'timezone': record['timezone'],
                'kind': 'exact',
                'source': doc['source_url'],
                'quote': record['quote'],
                'checked_at': checked_at,
                'note': (f"Read again on {checked_at} from the EHF Champions League Men 2026/27 group-phase "
                         f"playing-times PDF fetched that minute ({manifest['derived_from']['pdf_sha256'][:16]}…); "
                         f"the quoted slice is reproduced from the committed bytes by scripts/apply_evidence.py. "
                         f"{record['time_local']} {record['timezone']} = {record['start_utc']}."),
            }
            entry = verifications.setdefault('event_verifications', {}).setdefault(record['event_id'], {})
            entry.update({
                'competition': record['competition'],
                'start_local': record['time_local'],
                'start_utc': record['start_utc'],
                'status': 'verified',
                'sources': [doc['source_url']],
                'facts': [f"{record['team_line']} — {record['date_line']} {record['time_line']} "
                          f"({record['timezone']}) in the EHF group-phase playing-times document"],
                'note': f'scripts/apply_evidence.py re-derived this quote from the committed PDF text at {checked_at}.',
            })
            applied += 1

    for event_id, why in refused:
        print(f'  REFUSED {event_id}: {why}')
    if refused:
        print(f'apply_evidence: {len(refused)} record(s) refused; nothing was written for them.')
        return 1

    if not args.dry_run and applied:
        releases['checked_at'] = max(releases.get('checked_at') or '', checked_at)
        releases_path.write_text(json.dumps(releases, indent=1, ensure_ascii=False) + '\n')
        verifications_path.write_text(json.dumps(verifications, indent=1, ensure_ascii=False) + '\n')
    print(f'apply_evidence: {applied} exact-clock record(s) written from committed source bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
