"""Refresh primary-source schedules without laundering a failed fetch into fresh data.

`generated`/`attempted_at` describe this build, never the age of source evidence.
Each successful row has its own `verified_at` and payload SHA-256. Failed leagues
retain their original evidence only in `cached_matches`, not the upcoming feed.
A successful empty response is authoritative and removes that league's cache.
"""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ['soccer', 'boxing', 'ufc', 'mma', 'football', 'american football', 'gaelic football', 'hurling', 'horse racing', 'cycling', 'specials']
SOURCES = {
    'Ice hockey': ('NHL', 'https://api-web.nhle.com/v1/schedule/now'),
    'Baseball': ('MLB', 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start}&endDate={end}'),
    'Basketball': ('NBA', 'https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json'),
}
PENDING = {
    'Tennis': 'https://www.atptour.com/en/scores/current',
    'Cricket': 'https://www.icc-cricket.com/fixtures-results',
    'Rugby union': 'https://www.world.rugby/tournaments/fixtures',
    'Rugby league': 'https://www.intrl.sport/',
    'Golf': 'https://www.pgatour.com/schedule',
    'Darts': 'https://www.pdc.tv/tournaments/calendar',
    'Snooker': 'https://www.wst.tv/matches/',
    'Handball': 'https://www.eurohandball.com/en/calendar/',
    'Volleyball': 'https://www.volleyballworld.com/',
    'Badminton': 'https://bwfbadminton.com/calendar/',
    'Table tennis': 'https://www.ittf.com/',
    'Esports': 'https://lolesports.com/',
    'Motorsport': 'https://www.fia.com/events',
    'Other eligible sports': 'https://www.olbg.com/betting-tips',
}


def utc(value):
    """Reject zone-less dates. Attaching UTC to an unknown clock would invent a fact."""
    moment = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError('Source start must include an explicit UTC offset')
    return moment.astimezone(dt.timezone.utc)


def row(sport, league, ident, away, home, start, status, source):
    if not all([ident, away, home, start, source]):
        raise ValueError('Missing required official fixture fields')
    if not all(isinstance(n, str) and n.strip() for n in (away, home)):
        raise ValueError('Source team names must be non-empty text')
    utc(start)
    return dict(id=f'{league}-{ident}', sport=sport, league=league, away=away, home=home,
                start=start, status=status, source=source, verification='Official schedule',
                winner=None, confidence=None, line=None, handicap=None, total=None,
                prediction=None, form=None, history=None)


def parse(sport, league, payload, url):
    out = []
    if league == 'NHL':
        for day in payload['gameWeek']:
            for g in day['games']:
                def name(t):
                    return t['placeName']['default'] + ' ' + t['commonName']['default']
                out.append(row(sport, league, g['id'], name(g['awayTeam']), name(g['homeTeam']),
                               g['startTimeUTC'], g['gameState'], url))
    elif league == 'MLB':
        for day in payload['dates']:
            for g in day['games']:
                out.append(row(sport, league, g['gamePk'], g['teams']['away']['team']['name'],
                               g['teams']['home']['team']['name'], g['gameDate'],
                               g['status']['detailedState'], url))
    elif league == 'NBA':
        for day in payload['leagueSchedule']['gameDates']:
            for g in day['games']:
                def name(t):
                    return t['teamCity'] + ' ' + t['teamName']
                out.append(row(sport, league, g['gameId'], name(g['awayTeam']), name(g['homeTeam']),
                               g['gameDateTimeUTC'], str(g['gameStatus']), url))
    else:
        raise ValueError(f'No official parser for league {league}')
    return out


def download(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'OLBG3-source-audit/2.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        # A bounded public JSON request, not a crawler or an authentication bypass.
        raw = response.read(25_000_001)
        if len(raw) > 25_000_000:
            raise ValueError('Official response exceeds 25 MB safety limit')
        return raw


def refresh(previous=None, now=None, fetch=download, archive=None):
    previous = previous or {}
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Refresh clock must be timezone-aware')
    now = now.astimezone(dt.timezone.utc)
    end = now + dt.timedelta(days=7)
    stamp = now.isoformat()
    data = dict(schema_version=2, generated=stamp, attempted_at=stamp,
                window_start=stamp, window_end=end.isoformat(), matches=[], cached_matches=[],
                coverage=[], excluded=EXCLUDED)
    old_coverage = {c['league']: c for c in previous.get('coverage', []) if c.get('league')}
    old_rows = previous.get('matches', []) + previous.get('cached_matches', [])

    def in_window(r):
        try:
            return now <= utc(r['start']) <= end
        except (TypeError, ValueError, KeyError):
            return False

    def collect(item):
        sport, (league, template) = item
        url = template.format(start=now.date(), end=end.date())
        result = dict(sport=sport, league=league, source=url, attempted_at=stamp,
                      last_success_at=None, evidence_sha256=None, count=0, cached_count=0)
        try:
            raw = fetch(url)
            rows = parse(sport, league, json.loads(raw), url)
            digest = hashlib.sha256(raw).hexdigest()
            rows = [dict(r, verified_at=stamp, evidence_sha256=digest, freshness='fresh')
                    for r in rows if in_window(r)]
            if archive is not None:
                archive.mkdir(parents=True, exist_ok=True)
                (archive / f'{league}.json').write_bytes(raw)
            result.update(state='ok', last_success_at=stamp, evidence_sha256=digest, count=len(rows),
                          status=f'Fetched official {league} schedule; {len(rows)} upcoming records in window. '
                                 'Limited to returned league schedule; not entire sport.')
            return result, rows, []
        except Exception as error:
            # Preserve provenance, NOT the previous success message. Isolate failed leagues
            # even when another source succeeds, and never call a reused row freshly verified.
            old = old_coverage.get(league, {})
            last_success = old.get('last_success_at')
            if not last_success and old.get('status', '').startswith('Fetched official'):
                last_success = previous.get('generated')  # legacy schema migration, not new verification
            cached = []
            for r in old_rows:
                if r.get('league') == league and in_window(r):
                    copy = dict(r, freshness='cached', verification='Unverified now — cached official schedule')
                    copy['verified_at'] = r.get('verified_at') or last_success
                    copy['evidence_sha256'] = r.get('evidence_sha256')  # never invent a legacy hash
                    cached.append(copy)
            result.update(state='error', last_success_at=last_success,
                          evidence_sha256=old.get('evidence_sha256'), cached_count=len(cached),
                          status=f'Unverified — fetch or schema failed: {type(error).__name__}: {error}. '
                                 'Cached rows are withheld from the current feed.')
            return result, [], cached

    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        for coverage, rows, cached in pool.map(collect, SOURCES.items()):
            data['coverage'].append(coverage)
            data['matches'].extend(rows)
            data['cached_matches'].extend(cached)
    for sport, url in PENDING.items():
        data['coverage'].append(dict(sport=sport, league='', source=url, state='not_implemented',
                                     attempted_at=None, last_success_at=None, evidence_sha256=None,
                                     count=0, cached_count=0,
                                     status='Unverified — official connector not implemented; no completeness claim. '
                                            'Reference link, not fixture verification.'))
    for key in ('matches', 'cached_matches'):
        data[key] = sorted({r['id']: r for r in data[key]}.values(), key=lambda r: r['start'])
    return data


def main():
    path = ROOT / 'data/current.json'
    previous = json.loads(path.read_text()) if path.exists() else {}
    data = refresh(previous, archive=ROOT / 'data/evidence')
    path.write_text(json.dumps(data, indent=2) + '\n')
    print(f"Official feed: {len(data['matches'])} fresh, {len(data['cached_matches'])} cached/withheld; "
          f"{sum(c['state'] == 'error' for c in data['coverage'])} failed sources")


if __name__ == '__main__':
    main()
