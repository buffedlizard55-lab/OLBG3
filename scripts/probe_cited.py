#!/usr/bin/env python3
"""probe_cited.py — re-fetch the official pages this repo already cites for upcoming fixtures.

The release gate expires an official observation 24 hours after it was read. Re-reading the same
cited page is the only honest way to renew that observation: nothing is copied forward, and a page
that no longer states a fixture simply yields nothing.

Input : data/release_checks.json, data/matches.json
Output: <out>/manifest.json + <out>/pages/<key>.(txt|json)

Run on a CI runner (no outbound route to these hosts from the agent sandbox).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
AGENT = ('OLBG3Audit/1.0 (+https://github.com/buffedlizard55-lab/OLBG3; '
         'official-source re-verification; contact via repository issues)')

BLOCK = {'p', 'div', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'article',
         'header', 'footer', 'main', 'br', 'td', 'th', 'table', 'ul', 'ol'}
SKIP = {'script', 'style', 'noscript', 'template', 'svg'}


class Render(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.depth += 1
        elif tag in BLOCK:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in SKIP and self.depth:
            self.depth -= 1
        elif tag in BLOCK:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)

    def text(self) -> str:
        lines = [' '.join(l.split()) for l in ''.join(self.parts).split('\n')]
        return '\n'.join(l for l in lines if l)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=2.0)
    args = ap.parse_args()

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    checks = json.loads((DATA / 'release_checks.json').read_text())['events']
    upcoming = {k: v for k, v in checks.items() if (v.get('date') or '') >= today and v.get('source')}
    urls = sorted({v['source'] for v in upcoming.values()})

    out = Path(args.out)
    (out / 'pages').mkdir(parents=True, exist_ok=True)
    doc = {'tool': 'scripts/probe_cited.py', 'user_agent': AGENT,
           'started_at_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'events_in_scope': sorted(upcoming), 'pages': []}

    for index, url in enumerate(urls):
        key = re.sub(r'[^A-Za-z0-9]+', '-', url.split('://', 1)[-1])[:90].strip('-')
        entry = {'url': url, 'key': key}
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': AGENT,
                'Accept': 'text/html,application/json,text/plain;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.9'})
            with urllib.request.urlopen(req, timeout=45) as response:
                body = response.read()
                status, final = response.status, response.geturl()
                ctype = response.headers.get('Content-Type', '')
            entry.update({'outcome': 'captured', 'status': status, 'final_url': final,
                          'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                          'content_type': ctype})
            if 'json' in ctype or url.endswith('.json'):
                (out / 'pages' / f'{key}.json').write_bytes(body)
                entry['file'] = f'pages/{key}.json'
            else:
                render = Render()
                render.feed(body.decode('utf-8', 'replace'))
                (out / 'pages' / f'{key}.txt').write_text(render.text() + '\n', encoding='utf-8')
                entry['file'] = f'pages/{key}.txt'
            print(f'{status} {len(body):>8}  {url}')
        except urllib.error.HTTPError as exc:
            entry.update({'outcome': 'http_error', 'status': exc.code, 'detail': str(exc.reason)[:160]})
            print(f'HTTP {exc.code}  {url}')
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            entry.update({'outcome': 'network_error', 'detail': f'{type(exc).__name__}: {exc}'[:160]})
            print(f'ERR  {url}: {entry["detail"]}')
        entry['fetched_at_utc'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        doc['pages'].append(entry)
        if index + 1 < len(urls):
            time.sleep(args.delay)

    doc['finished_at_utc'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    (out / 'manifest.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    ok = sum(1 for p in doc['pages'] if p.get('outcome') == 'captured')
    print(f'\ncaptured {ok}/{len(urls)} cited pages -> {out}/manifest.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
