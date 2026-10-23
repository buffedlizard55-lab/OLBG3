#!/usr/bin/env python3
"""official_probe.py — read official competition sources from a runner with outbound access.

Two kinds of probe, both recorded verbatim:

  structured  A governing body's own JSON endpoint. The payload is stored, hashed, and the
              fixture fields used by this project are copied out of it (team names, UTC start,
              game id). Nothing is derived: the field names are named in the output.

  text        A governing body's own public page, stored as tag-stripped text so a human or an
              agent can quote it. No value is extracted automatically from a text probe; it is
              evidence to be read, and a claim built on it must quote it.

Every probe records HTTP status, final URL, byte count and sha256 whether it succeeds or fails,
so a failure is visible evidence rather than a silent gap.

Usage
-----
    python scripts/official_probe.py --out data/raw/official-20261023T1800Z
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ('OLBG3Audit/1.0 (+https://github.com/buffedlizard55-lab/OLBG3; '
         'official-source research; contact via repository issues)')

STRUCTURED = [
    {
        'key': 'nhl_schedule',
        'sport': 'Ice Hockey',
        'source': 'NHL',
        'url': 'https://api-web.nhle.com/v1/schedule/{today}',
        'kind': 'json',
        'note': 'NHL official schedule endpoint; startTimeUTC is the league\'s own UTC start.',
    },
    {
        'key': 'nhl_standings',
        'sport': 'Ice Hockey',
        'source': 'NHL',
        'url': 'https://api-web.nhle.com/v1/standings/{today}',
        'kind': 'json',
        'note': 'NHL official standings; used as the current-form input.',
    },
    {
        'key': 'mlb_schedule',
        'sport': 'Baseball',
        'source': 'MLB',
        'url': ('https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={today}'
                '&endDate={plus2}&hydrate=team,linescore,probablePitcher'),
        'kind': 'json',
        'note': 'MLB official schedule; gameDate is the league\'s own UTC start.',
    },
    {
        'key': 'mlb_standings',
        'sport': 'Baseball',
        'source': 'MLB',
        'url': ('https://statsapi.mlb.com/api/v1/standings?leagueId=103,104'
                '&season={season}&date={today}&hydrate=team'),
        'kind': 'json',
        'note': 'MLB official standings; used as the current-form input.',
    },
    {
        'key': 'nba_schedule',
        'sport': 'Basketball',
        'source': 'NBA',
        'url': 'https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json',
        'kind': 'json',
        'note': 'NBA official season schedule; gameDateTimeUTC is the league\'s own UTC start.',
    },
]

TEXT = [
    ('Tennis', 'ATP Tour', 'https://www.atptour.com/en/scores/current'),
    ('Tennis', 'WTA Tour', 'https://www.wtatennis.com/scores'),
    ('Cricket', 'ICC', 'https://www.icc-cricket.com/fixtures-results'),
    ('Snooker', 'World Snooker Tour', 'https://www.wst.tv/matches/'),
    ('Rugby Union', 'United Rugby Championship', 'https://www.unitedrugby.com/fixtures'),
    ('Rugby League', 'Super League', 'https://www.superleague.co.uk/fixtures'),
    ('Darts', 'PDC', 'https://www.pdc.tv/tournaments'),
    ('Handball', 'EHF', 'https://www.eurohandball.com/en/calendar/'),
    ('Volleyball', 'Volleyball World', 'https://en.volleyballworld.com/volleyball/competitions/volleyball-national-leagues/schedule/'),
    ('Gaelic Football', 'GAA', 'https://www.gaa.ie/fixtures-results'),
    ('Motor Racing', 'Formula 1', 'https://www.formula1.com/en/racing/2026'),
    ('Golf', 'PGA Tour', 'https://www.pgatour.com/schedule'),
    ('Basketball', 'EuroLeague', 'https://www.euroleaguebasketball.net/en/euroleague/games/'),
    ('Greyhounds', 'GBGB', 'https://www.gbgb.org.uk/racecard'),
]


class TextRender:
    """Tag-stripped, block-aware text. Identical policy to scripts/live_harvest.py."""

    BLOCK = {'p', 'div', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'article',
             'header', 'footer', 'main', 'br', 'td', 'th', 'table', 'ul', 'ol'}
    SKIP = {'script', 'style', 'noscript', 'template', 'svg'}

    def __init__(self):
        from html.parser import HTMLParser
        self._parser = HTMLParser(convert_charrefs=True)
        self.parts: list[str] = []
        self.depth = 0
        render = self

        class _P(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag in render.SKIP:
                    render.depth += 1
                elif tag in render.BLOCK:
                    render.parts.append('\n')

            def handle_endtag(self, tag):
                if tag in render.SKIP and render.depth:
                    render.depth -= 1
                elif tag in render.BLOCK:
                    render.parts.append('\n')

            def handle_data(self, data):
                if not render.depth:
                    render.parts.append(data)

        self._p = _P(convert_charrefs=True)

    def feed(self, html: str) -> str:
        self._p.feed(html)
        lines = [' '.join(l.split()) for l in ''.join(self.parts).split('\n')]
        return '\n'.join(l for l in lines if l)


def fetch(url: str, timeout: int = 40) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={
        'User-Agent': AGENT,
        'Accept': 'application/json,text/html;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.geturl(), response.read()


def record(base: dict, *, outcome: str, status=None, final=None, body: bytes = b'', detail: str = '') -> dict:
    base.update({'outcome': outcome})
    if status is not None:
        base['status'] = status
    if final:
        base['final_url'] = final
    if body:
        base['bytes'] = len(body)
        base['sha256'] = hashlib.sha256(body).hexdigest()
    if detail:
        base['detail'] = detail
    base['fetched_at_utc'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=2.0)
    args = ap.parse_args()

    today = dt.datetime.now(dt.timezone.utc).date()
    subs = {
        'today': today.isoformat(),
        'plus2': (today + dt.timedelta(days=2)).isoformat(),
        'plus7': (today + dt.timedelta(days=7)).isoformat(),
        'season': str(today.year),
    }
    out = Path(args.out)
    (out / 'text').mkdir(parents=True, exist_ok=True)
    (out / 'json').mkdir(parents=True, exist_ok=True)

    doc = {
        'tool': 'scripts/official_probe.py',
        'user_agent': AGENT,
        'started_at_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'date_utc': today.isoformat(),
        'policy': ('Only the competition body\'s own endpoint or page is probed. A payload is stored '
                   'and hashed; a text page is stored as text for line-by-line reading. No fixture, '
                   'clock or price is inferred where a source does not state it.'),
        'structured': [],
        'text': [],
    }

    for probe in STRUCTURED:
        url = probe['url'].format(**subs)
        entry = {'key': probe['key'], 'sport': probe['sport'], 'source': probe['source'],
                 'url': url, 'kind': probe['kind'], 'note': probe['note']}
        try:
            status, final, body = fetch(url)
            entry = record(entry, outcome='captured', status=status, final=final, body=body)
            (out / 'json' / f"{probe['key']}.json").write_bytes(body)
            entry['file'] = f"json/{probe['key']}.json"
            try:
                parsed = json.loads(body)
                entry['parsed_keys'] = sorted(parsed)[:12] if isinstance(parsed, dict) else ['<list>']
            except json.JSONDecodeError as exc:
                entry['parse_error'] = str(exc)[:200]
            print(f"{probe['key']}: {status} {len(body)} bytes")
        except urllib.error.HTTPError as exc:
            entry = record(entry, outcome='http_error', status=exc.code, detail=str(exc.reason)[:200])
            print(f"{probe['key']}: HTTP {exc.code}")
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            entry = record(entry, outcome='network_error', detail=f'{type(exc).__name__}: {exc}'[:200])
            print(f"{probe['key']}: {entry['detail']}")
        doc['structured'].append(entry)
        time.sleep(args.delay)

    for sport, source, url in TEXT:
        entry = {'sport': sport, 'source': source, 'url': url, 'kind': 'text'}
        slug = f'{sport.lower().replace(" ", "-")}-{source.lower().replace(" ", "-")}'
        try:
            status, final, body = fetch(url)
            entry = record(entry, outcome='captured', status=status, final=final, body=body)
            text = TextRender().feed(body.decode('utf-8', 'replace'))
            (out / 'text' / f'{slug}.txt').write_text(text + '\n', encoding='utf-8')
            entry['file'] = f'text/{slug}.txt'
            entry['text_chars'] = len(text)
            print(f"{source:<26} {status} {len(body):>8} bytes  text {len(text):>7} chars")
        except urllib.error.HTTPError as exc:
            entry = record(entry, outcome='http_error', status=exc.code, detail=str(exc.reason)[:200])
            print(f'{source}: HTTP {exc.code}')
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            entry = record(entry, outcome='network_error', detail=f'{type(exc).__name__}: {exc}'[:200])
            print(f'{source}: {entry["detail"]}')
        doc['text'].append(entry)
        time.sleep(args.delay)

    doc['finished_at_utc'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    (out / 'manifest.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    ok = sum(1 for p in doc['structured'] + doc['text'] if p.get('outcome') == 'captured')
    print(f'\nprobes captured: {ok}/{len(STRUCTURED) + len(TEXT)} -> {out}/manifest.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
