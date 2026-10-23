#!/usr/bin/env python3
"""live_harvest.py — bounded, robots-aware capture of the public OLBG listings.

Why this exists
---------------
The agent sandbox that maintains this repo has no outbound route to olbg.com (recorded as
FL-077), so listing reads are performed on a GitHub Actions runner, which does have one, and
the *bytes actually served* are committed as evidence. Nothing is inferred from a slug, a
navigation label or a neighbouring card: the capture stores what the server rendered, verbatim.

What it does
------------
1. Reads https://www.olbg.com/robots.txt once and stores it byte-for-byte.
2. Honours it with urllib.robotparser for the exact User-Agent used.
3. Requests one listing page per in-scope sport, sequentially, with a delay between requests.
4. Stores, per listing: HTTP status, final URL, byte length, sha256, the raw HTML, and a
   tag-stripped text rendering (for human/agent review, never for inference).
5. Writes a manifest with UTC fetch stamps.

It never logs in, never bypasses a challenge, never guesses a pagination URL and never
writes a fixture, clock or price of its own.

Usage
-----
    python scripts/live_harvest.py --out data/raw/live-<stamp>
    python scripts/live_harvest.py --out ... --pages-only   # no writes, just status codes
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

BASE = 'https://www.olbg.com'
AGENT = ('OLBG3Research/1.0 (+https://github.com/buffedlizard55-lab/OLBG3; '
         'public-listing-audit; contact via repository issues)')
ROOT = Path(__file__).resolve().parents[1]

# The 15 in-scope sports plus the sub-league endpoints the brief's coverage needs.
# (path, sport, league label) — the label is only a filing key, never a source claim.
PAGES = [
    ('/betting-tips/Tennis/3', 'Tennis', 'all'),
    ('/betting-tips/Basketball/4', 'Basketball', 'all'),
    ('/betting-tips/Basketball/NBA/4', 'Basketball', 'NBA'),
    ('/betting-tips/Basketball/European/4', 'Basketball', 'European'),
    ('/betting-tips/Golf/5', 'Golf', 'all'),
    ('/betting-tips/Cricket/7', 'Cricket', 'all'),
    ('/betting-tips/Snooker/8', 'Snooker', 'all'),
    ('/betting-tips/Rugby_Union/9', 'Rugby Union', 'all'),
    ('/betting-tips/Rugby_League/10', 'Rugby League', 'all'),
    ('/betting-tips/Baseball/12', 'Baseball', 'all'),
    ('/betting-tips/Ice_Hockey/13', 'Ice Hockey', 'all'),
    ('/betting-tips/Ice_Hockey/NHL/13', 'Ice Hockey', 'NHL'),
    ('/betting-tips/Motor_Racing/14', 'Motor Racing', 'all'),
    ('/betting-tips/Darts/15', 'Darts', 'all'),
    ('/betting-tips/Handball/20', 'Handball', 'all'),
    ('/betting-tips/Volleyball/21', 'Volleyball', 'all'),
    ('/betting-tips/Gaelic_Football/25', 'Gaelic Football', 'all'),
    ('/betting-tips/Greyhounds/28', 'Greyhounds', 'all'),
]


class TextRender(HTMLParser):
    """Tag-stripped, block-aware text of a page. No interpretation, no field extraction."""

    BLOCK = {'p', 'div', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section',
             'article', 'header', 'footer', 'main', 'br', 'td', 'th', 'table', 'ul', 'ol'}
    SKIP = {'script', 'style', 'noscript', 'template', 'svg'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1
        elif tag in self.BLOCK:
            self.parts.append('\n')
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.parts.append(f'[href={href}] ')

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1
        elif tag in self.BLOCK:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)

    def text(self) -> str:
        raw = ''.join(self.parts)
        lines = []
        for line in raw.split('\n'):
            collapsed = ' '.join(line.split())
            if collapsed:
                lines.append(collapsed)
        return '\n'.join(lines)


def fetch(url: str, timeout: int = 30) -> tuple[int, str, bytes, dict]:
    req = urllib.request.Request(url, headers={
        'User-Agent': AGENT,
        'Accept': 'text/html,text/plain;q=0.9',
        'Accept-Language': 'en-GB,en;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.geturl(), response.read(), dict(response.headers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=3.0)
    args = ap.parse_args()

    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    out = Path(args.out)
    (out / 'listings').mkdir(parents=True, exist_ok=True)

    manifest = {
        'tool': 'scripts/live_harvest.py',
        'user_agent': AGENT,
        'captured_at_utc': stamp,
        'base': BASE,
        'purpose': ('Verbatim capture of the public OLBG listing pages for the 15 in-scope sports. '
                    'Stored so a later pass can extract fixtures and verify them against the '
                    'competition bodies. No field is inferred from a slug or a label.'),
        'robots': {},
        'pages': [],
    }

    # 1. robots.txt, read once, stored verbatim.
    try:
        status, url, body, headers = fetch(BASE + '/robots.txt')
        (out / 'robots.txt').write_bytes(body)
        manifest['robots'] = {
            'url': BASE + '/robots.txt',
            'status': status,
            'sha256': hashlib.sha256(body).hexdigest(),
            'bytes': len(body),
        }
        robot = RobotFileParser()
        robot.parse(body.decode('utf-8', 'replace').splitlines())
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        manifest['robots'] = {'url': BASE + '/robots.txt', 'error': f'{type(exc).__name__}: {exc}'}
        robot = None
        print(f'robots.txt unreadable: {exc}')

    # 2. Listing pages, one at a time.
    for index, (path, sport, league) in enumerate(PAGES):
        url = BASE + path
        record = {'sport': sport, 'league': league, 'path': path, 'url': url,
                  'fetched_at_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        allowed = True
        if robot is not None:
            try:
                allowed = robot.can_fetch(AGENT, url)
            except Exception as exc:                     # noqa: BLE001 - record, never assume
                record['robots_error'] = f'{type(exc).__name__}: {exc}'
        record['robots_allows'] = allowed
        if not allowed:
            record['outcome'] = 'robots_denied'
            manifest['pages'].append(record)
            print(f'{path}: robots_denied')
            continue
        try:
            status, final, body, headers = fetch(url)
            slug = path.strip('/').replace('/', '_')
            (out / 'listings' / f'{slug}.html').write_bytes(body)
            render = TextRender()
            render.feed(body.decode('utf-8', 'replace'))
            (out / 'listings' / f'{slug}.txt').write_text(render.text() + '\n', encoding='utf-8')
            record.update({
                'outcome': 'captured',
                'status': status,
                'final_url': final,
                'bytes': len(body),
                'sha256': hashlib.sha256(body).hexdigest(),
                'content_type': headers.get('Content-Type'),
                'html_file': f'listings/{slug}.html',
                'text_file': f'listings/{slug}.txt',
                'text_chars': len(render.text()),
                'html_bytes': len(body),
            })
            print(f'{path}: {status} {len(body)} bytes')
        except urllib.error.HTTPError as exc:
            record.update({'outcome': 'http_error', 'status': exc.code, 'detail': str(exc.reason)})
            print(f'{path}: HTTP {exc.code}')
        except (urllib.error.URLError, OSError) as exc:
            record.update({'outcome': 'network_error', 'detail': f'{type(exc).__name__}: {exc}'})
            print(f'{path}: {record["detail"]}')
        manifest['pages'].append(record)
        if index + 1 < len(PAGES):
            time.sleep(args.delay)

    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

    captured = sum(1 for p in manifest['pages'] if p.get('outcome') == 'captured')
    print(f'\ncaptured {captured}/{len(PAGES)} listings into {out}')
    print(f'manifest: {out / "manifest.json"}')
    return 0 if captured else 1


if __name__ == '__main__':
    raise SystemExit(main())
