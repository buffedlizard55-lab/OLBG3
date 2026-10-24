#!/usr/bin/env python3
"""verify_live.py — turn an official probe into cited verification and clock evidence.

Only two kinds of match are written:

  * a fixture that appears in a governing body's own payload, with both sides matched and the
    league's own UTC start within 90 minutes of the OLBG card's startDate, is recorded as
    ``verified`` with the payload URL and a quote of the exact field values used;
  * everything else is left alone. It is not marked unverified here (it already is), and no
    partial name match is ever promoted.

The output merges into the existing evidence files rather than replacing them, and every entry
records the probe it came from so a later pass can tell one session's reading from another's.

Usage
-----
    python scripts/verify_live.py --probe data/raw/official-20261023T1628Z \
                                  --harvest data/raw/olbg-harvest-20261023T1700Z.tsv
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
TOLERANCE = dt.timedelta(minutes=90)


def norm(value: str) -> set[str]:
    return {t for t in re.split(r'[^a-z0-9]+', (value or '').lower()) if t}


def load_harvest(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('|') + [''] * 18
        rows.append(dict(zip(
            ('sport', 'league_label', 'path_prefix', 'slug', 'event_id', 'date_label',
             'time_label', 'market', 'consensus', 'tips', 'note', 'start_utc', 'odds_decimal',
             'odds_american', 'odds_fractional', 'tip_share_pct', 'event_name', 'listing_url'),
            parts[:18])))
    return rows


def parse_utc(value: str):
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(dt.timezone.utc)
    except (ValueError, AttributeError):
        return None


def nhl_games(payload: dict) -> list[dict]:
    games = []
    for day in payload.get('gameWeek', []):
        for game in day.get('games', []):
            home, away = game.get('homeTeam', {}), game.get('awayTeam', {})
            games.append({
                'id': str(game.get('id')),
                'start_utc': game.get('startTimeUTC'),
                'home': (home.get('commonName') or {}).get('default') or home.get('name', {}).get('default') or '',
                'away': (away.get('commonName') or {}).get('default') or away.get('name', {}).get('default') or '',
                'tokens': (norm(home.get('abbrev')) | norm((home.get('commonName') or {}).get('default'))
                           | norm((home.get('name') or {}).get('default'))
                           | norm(away.get('abbrev')) | norm((away.get('commonName') or {}).get('default'))
                           | norm((away.get('name') or {}).get('default'))),
                'label': f"{away.get('abbrev')} {(away.get('commonName') or {}).get('default','')} @ "
                         f"{home.get('abbrev')} {(home.get('commonName') or {}).get('default','')}".strip(),
                'competition': 'NHL',
                'source': 'https://api-web.nhle.com/v1/schedule/',
                'payload_key': 'startTimeUTC',
            })
    return games


def mlb_games(payload: dict) -> list[dict]:
    games = []
    for day in payload.get('dates', []):
        for game in day.get('games', []):
            home, away = game['teams']['home']['team'], game['teams']['away']['team']
            games.append({
                'id': str(game.get('gamePk')),
                'start_utc': game.get('gameDate'),
                'home': home.get('teamName') or home.get('name', ''),
                'away': away.get('teamName') or away.get('name', ''),
                'tokens': norm(home.get('name')) | norm(away.get('name')) | norm(home.get('teamName')) | norm(away.get('teamName')),
                'label': f"{away.get('name')} @ {home.get('name')}",
                'competition': 'MLB',
                'source': 'https://statsapi.mlb.com/api/v1/schedule',
                'payload_key': 'gameDate',
            })
    return games


SESSION_NOTE = 'session-a30d9bdb (2026-10-24T17:09Z NHL/MLB clock probe)'


def _append_session(doc: dict, note: str) -> None:
    """Record who re-read the clocks without erasing who read them before.

    This script used to overwrite ``session`` with one hard-coded string, which silently deleted
    the provenance of every earlier probe (session-b322f52e's F1/URC/EHF reads, session-784afe97's
    Top 14 holds). The field is a merge history, so it may only ever grow, and it must grow
    exactly once per run so a re-run stays byte-identical.
    """
    current = (doc.get('session') or '').strip()
    if note in current:
        return
    doc['session'] = f'{current} + {note}' if current else note


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--probe', required=True)
    ap.add_argument('--harvest', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    probe = Path(args.probe)
    if not probe.is_absolute():
        probe = ROOT / probe
    harvest = Path(args.harvest)
    if not harvest.is_absolute():
        harvest = ROOT / harvest

    manifest = json.loads((probe / 'manifest.json').read_text())
    checked_at = manifest.get('started_at_utc')
    rows = load_harvest(harvest)

    candidates: list[dict] = []
    sources: list[dict] = []

    if (probe / 'json/nhl_schedule.json').exists():
        payload = json.loads((probe / 'json/nhl_schedule.json').read_text())
        games = nhl_games(payload)
        url = next((p['url'] for p in manifest['structured'] if p['key'] == 'nhl_schedule'), '')
        for game in games:
            game['source'] = url
        candidates += games
        sources.append({'id': 'S-NHL-API-20261023', 'class': 'official',
                        'name': 'NHL official schedule endpoint (gameWeek payload)',
                        'url': url, 'probe_file': 'json/nhl_schedule.json',
                        'sha256': next((p.get('sha256') for p in manifest['structured'] if p['key'] == 'nhl_schedule'), None)})
        print(f'NHL payload: {len(games)} games, {sum(1 for g in games if g["start_utc"])} with startTimeUTC')

    if (probe / 'json/mlb_schedule.json').exists():
        payload = json.loads((probe / 'json/mlb_schedule.json').read_text())
        games = mlb_games(payload)
        url = next((p['url'] for p in manifest['structured'] if p['key'] == 'mlb_schedule'), '')
        for game in games:
            game['source'] = url
        candidates += games
        sources.append({'id': 'S-MLB-API-20261023', 'class': 'official',
                        'name': 'MLB official schedule endpoint',
                        'url': url, 'probe_file': 'json/mlb_schedule.json',
                        'sha256': next((p.get('sha256') for p in manifest['structured'] if p['key'] == 'mlb_schedule'), None)})
        print(f'MLB payload: {len(games)} games, {sum(1 for g in games if g["start_utc"])} with gameDate')

    verified: list[dict] = []
    unmatched = {'Ice Hockey': 0, 'Baseball': 0}
    for row in rows:
        if row['sport'] not in unmatched:
            continue
        tokens = norm(row['event_name'])
        start = parse_utc(row['start_utc'])
        hits = []
        for game in candidates:
            if not (tokens and game['tokens']):
                continue
            # Both sides must be represented: at least two distinct token overlaps.
            overlap = tokens & game['tokens']
            if len(overlap) < 2:
                continue
            game_start = parse_utc(game['start_utc'])
            if not start or not game_start or abs(game_start - start) > TOLERANCE:
                continue
            hits.append((game, game_start, overlap))
        if len(hits) != 1:
            unmatched[row['sport']] += 1
            continue
        game, game_start, overlap = hits[0]
        verified.append({'row': row, 'game': game, 'start': game_start, 'overlap': sorted(overlap)})

    print(f'matched fixtures: {len(verified)}  (unmatched: {unmatched})')
    for item in verified:
        row, game = item['row'], item['game']
        print(f"  {row['event_id']:<8} {row['event_name']:<38} OLBG {row['start_utc'][:16]}  "
              f"official {game['start_utc'][:16]}  {game['competition']}")

    if args.dry_run or not verified:
        return 0

    # ---- merge into data/verifications.json -------------------------------------------
    vpath = DATA / 'verifications.json'
    ver = json.loads(vpath.read_text())
    existing_ids = {s['id'] for s in ver.get('sources', [])}
    for source in sources:
        if source['id'] not in existing_ids:
            ver.setdefault('sources', []).append(source)
            existing_ids.add(source['id'])
    for item in verified:
        row, game = item['row'], item['game']
        source_id = 'S-NHL-API-20261023' if game['competition'] == 'NHL' else 'S-MLB-API-20261023'
        ver.setdefault('event_verifications', {})[row['event_id']] = {
            'competition': game['competition'],
            'venue': None,
            'start_local': None,
            'start_utc': game['start_utc'],
            'status': 'verified',
            'sources': [source_id],
            'facts': [f"{game['payload_key']} = {game['start_utc']} for {game['label']} "
                      f"(game id {game['id']}) in the payload stored at {game['source']}"],
            'note': ('Fixture and UTC start read from the league\'s own schedule payload at '
                     f'{checked_at}; OLBG printed {row["date_label"]} {row["time_label"]} and its own '
                     f'startDate attribute said {row["start_utc"]}.'),
        }
    ver['retrieved_at'] = checked_at
    _append_session(ver, SESSION_NOTE)
    vpath.write_text(json.dumps(ver, indent=1, ensure_ascii=False) + '\n')
    print(f'verifications.json: {len(verified)} event(s) added/updated')

    # ---- merge into data/release_checks.json ------------------------------------------
    rpath = DATA / 'release_checks.json'
    rc = json.loads(rpath.read_text())
    for item in verified:
        row, game = item['row'], item['game']
        start = dt.datetime.fromisoformat(game['start_utc'].replace('Z', '+00:00'))
        rc['events'][row['event_id']] = {
            'date': start.strftime('%Y-%m-%d'),
            'time': start.strftime('%H:%M'),
            'timezone': 'UTC',
            'kind': 'exact',
            'source': game['source'],
            'quote': (f'"{game["payload_key"]}": "{game["start_utc"]}" — game id {game["id"]}, '
                      f'{game["label"]}'),
            'checked_at': checked_at,
        }
    rc['checked_at'] = max([rc.get('checked_at') or '', checked_at])
    _append_session(rc, SESSION_NOTE)
    # Idempotent: a re-run must produce a byte-identical file, so this note is a fixed key rather
    # than a sentence appended to the policy on every pass.
    rc['policy_20261023'] = ('Exact UTC starts read directly from the league schedule payloads '
                             '(api-web.nhle.com/v1/schedule, statsapi.mlb.com). Both payloads state '
                             'the start in UTC, so no zone is inferred.')
    if rc.get('policy', '').find(' 2026-10-23: exact UTC starts') != -1:
        rc['policy'] = rc['policy'].split(' | 2026-10-23: exact UTC starts')[0]
    rpath.write_text(json.dumps(rc, indent=1, ensure_ascii=False) + '\n')
    print(f"release_checks.json: {len(verified)} exact-clock record(s) added/updated")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
