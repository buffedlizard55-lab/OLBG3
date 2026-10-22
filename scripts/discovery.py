"""Bounded public OLBG discovery, not an official fixture feed or completeness claim.

One robots.txt and one public listing request per eligible sport, at most two
requests concurrently. No private API, location endpoint, login, challenge bypass
or guessed pagination URL is used. Only actual linked text + event URLs are
extracted. Clocks, participants' home status, markets and prices are NOT inferred
from slugs, adjacent cards or navigation. Dynamic/load-more content stays a flag.
"""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.olbg.com'
AGENT = 'OLBG3Research/1.0 (+https://github.com/buffedlizard55-lab/OLBG3; public-listing-audit)'
OFFICIAL_REFERENCES = {
    'Tennis': 'https://www.atptour.com/en/scores/current',
    'Basketball': 'https://www.nba.com/schedule',
    'Golf': 'https://www.pgatour.com/schedule',
    'Cricket': 'https://www.icc-cricket.com/fixtures-results',
    'Snooker': 'https://www.wst.tv/matches/',
    'Rugby Union': 'https://www.world.rugby/',
    'Rugby League': 'https://www.intrl.sport/',
    'Baseball': 'https://www.mlb.com/schedule',
    'Ice Hockey': 'https://www.nhl.com/schedule',
    'Motor Racing': 'https://www.formula1.com/en/racing/2026',
    'Darts': 'https://www.pdc.tv/',
    'Handball': 'https://www.eurohandball.com/en/calendar/',
    'Volleyball': 'https://www.volleyballworld.com/',
    'Gaelic Football': 'https://www.gaa.ie/fixtures-results',
    'Greyhounds': 'https://www.gbgb.org.uk/',
}


class EventLinks(HTMLParser):
    """Deduplicate event anchors within the actual requested sport ID."""
    def __init__(self, sport_id):
        super().__init__(convert_charrefs=True)
        self.sport_id = str(sport_id)
        self.anchor = None
        self.skip = 0
        self.events = {}
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template'):
            self.skip += 1
        if self.skip or tag != 'a':
            return
        href = dict(attrs).get('href') or ''
        url = urljoin(BASE, href)
        parsed = urlparse(url)
        ident = parse_qs(parsed.query).get('event_id', [''])[0]
        if (parsed.scheme == 'https' and parsed.hostname == 'www.olbg.com'
                and parsed.path.startswith('/betting-tips/')
                and parsed.path.rstrip('/').split('/')[-1] == self.sport_id
                and ident.isdigit()):
            self.anchor = [ident, url, []]
        else:
            self.anchor = None

    def handle_data(self, data):
        if self.skip:
            return
        self.text.append(data)
        if self.anchor is not None:
            self.anchor[2].append(data)

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template') and self.skip:
            self.skip -= 1
        if tag == 'a' and self.anchor is not None:
            ident, url, bits = self.anchor
            label = ' '.join(' '.join(bits).split())
            # Keep the first actual event heading, not the later selection link.
            if label and ident not in self.events:
                self.events[ident] = {'event_id': int(ident), 'title': label, 'olbg_url': url}
            self.anchor = None


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,text/plain'})
    with urllib.request.urlopen(req, timeout=12) as response:
        if urlparse(response.url).hostname != 'www.olbg.com':
            raise ValueError('Unexpected cross-host redirect; not followed for collection')
        raw = response.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError('Public listing exceeds 8 MB limit')
        return raw


def collect(now=None, fetch=get, archive=None, sports=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Discovery clock must include a timezone')
    stamp = now.astimezone(dt.timezone.utc).isoformat()
    if sports is None:
        sports = json.loads((ROOT/'data/meta.json').read_text())['allowed_sports_olbg_ids']
    # Taxonomy is an allowlist; an unexpected sport must not silently enter scope.
    for sport in sports:
        if sport.replace('_', ' ') not in OFFICIAL_REFERENCES:
            raise ValueError(f'Unapproved sport: {sport}')
    result = {'attempted_at': stamp, 'complete': False,
              'policy': 'Public HTML event-link discovery only. Not a complete or officially verified fixture list. '
                        'No clock, winner, odds, form or competition inferred; no API/pagination bypass.',
              'sources': [], 'events': []}
    robot = RobotFileParser(BASE+'/robots.txt')
    try:
        raw_robot = fetch(BASE+'/robots.txt')
        robot.parse(raw_robot.decode('utf-8', errors='replace').splitlines())
        result['robots'] = {'source': BASE+'/robots.txt', 'state': 'read',
                            'sha256': hashlib.sha256(raw_robot).hexdigest()}
    except Exception as error:
        # Robots access failure is not permission to crawl.
        result['robots'] = {'source': BASE+'/robots.txt', 'state': 'unverified',
                            'error': type(error).__name__+': '+str(error)}
        raw_robot = None

    def one(item):
        sport_slug, ident = item
        sport = sport_slug.replace('_', ' ')
        url = f'{BASE}/betting-tips/{sport_slug}/{ident}'
        source = {'sport': sport, 'url': url, 'attempted_at': stamp,
                  'fetched_at': None, 'sha256': None, 'count': 0,
                  'official_reference': OFFICIAL_REFERENCES[sport],
                  'complete': False, 'pagination': 'unverified'}
        if raw_robot is None:
            source.update(state='not_fetched', detail='Robots policy could not be retrieved; listing request not attempted.')
            return source, []
        if not robot.can_fetch(AGENT, url):
            source.update(state='robots_denied', detail='Robots policy disallows this collector. No request attempted.')
            return source, []
        try:
            raw = fetch(url)
            text = raw.decode('utf-8', errors='replace')
            parser = EventLinks(ident)
            parser.feed(text)
            visible_text = ' '.join(parser.text).lower()
            if not parser.events:
                # Empty HTML/challenge/SPA is NOT a verified "zero events" result.
                raise ValueError('No parseable event links; empty listing, client-side rendering or challenge unverified')
            digest = hashlib.sha256(raw).hexdigest()
            if archive is not None:
                archive.mkdir(parents=True, exist_ok=True)
                (archive/f'OLBG-{ident}.html').write_bytes(raw)
            source.update(state='observed_partial', fetched_at=stamp, sha256=digest,
                          count=len(parser.events),
                          pagination='load-more present' if 'load more' in visible_text else 'dynamic completeness unverified',
                          detail='Public event anchors observed. No official fixture/clock/price verification; not guaranteed upcoming. '
                                 'Load-more, personalized, hidden or dynamically added events may be missing.')
            events = [dict(e, sport=sport, observed_at=stamp, listing_url=url,
                           source_sha256=digest, official_reference=OFFICIAL_REFERENCES[sport],
                           verification='unverified', start_utc=None, competition=None,
                           winner=None, confidence=None, price=None, handicap=None, total=None)
                      for e in parser.events.values()]
            return source, events
        except Exception as error:
            source.update(state='unverified', detail=type(error).__name__+': '+str(error))
            return source, []

    with ThreadPoolExecutor(max_workers=2) as pool:
        for source, events in pool.map(one, sports.items()):
            result['sources'].append(source)
            result['events'].extend(events)
    return result


def main():
    result = collect(archive=ROOT/'data/evidence')
    (ROOT/'data/discovery.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f"OLBG public discovery: {len(result['events'])} event links; "
          f"{sum(s['state']=='observed_partial' for s in result['sources'])} readable sport listings. Coverage remains partial.")


if __name__ == '__main__':
    main()
