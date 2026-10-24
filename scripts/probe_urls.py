#!/usr/bin/env python3
"""probe_urls.py — fetch an explicit list of official URLs and store them byte-faithfully.

Added by session-9d520984 for the 2026-10-25 daily board. ``probe_cited.py`` only re-reads URLs
already recorded in ``data/release_checks.json``; a new day's fixtures need official pages that
nothing in the repo cites yet. This script takes the list from a plain text file (one URL per
line, ``#`` comments allowed) and, for each URL, records:

  * the exact response bytes (``pages/<key>.bin``) — never re-encoded, so a PDF or JSON can be
    re-parsed later exactly as served;
  * a tag-stripped text rendering for HTML (``pages/<key>.txt``) so a human can quote it;
  * HTTP status, final URL, content type, byte count, sha256 and fetch time in ``manifest.json``.

A failure is recorded as evidence (status / error), never silently skipped. Nothing is parsed or
derived here; downstream code reads the stored bytes.

Run on the CI runner (the agent sandbox has no outbound route to these hosts).

Usage
-----
    python scripts/probe_urls.py --list .harvest/urls-9d520984.txt --out data/raw/probe-9d520984-<stamp>
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from probe_cited import Render  # noqa: E402

AGENT = ('OLBG3Audit/1.0 (+https://github.com/buffedlizard55-lab/OLBG3; '
         'official-source research; contact via repository issues)')


def key_for(url: str) -> str:
    return re.sub(r'[^A-Za-z0-9]+', '-', url.split('://', 1)[-1])[:110].strip('-')


def read_list(path: Path) -> list[str]:
    urls = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line.startswith('http') and line not in urls:
            urls.append(line)
    return urls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=1.5)
    args = ap.parse_args()

    urls = read_list(Path(args.list))
    out = Path(args.out)
    (out / 'pages').mkdir(parents=True, exist_ok=True)
    doc = {'tool': 'scripts/probe_urls.py', 'list': args.list, 'user_agent': AGENT,
           'started_at_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'pages': []}
    for index, url in enumerate(urls):
        key = key_for(url)
        entry = {'url': url, 'key': key}
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': AGENT,
                'Accept': 'text/html,application/json,application/pdf,text/plain;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.9'})
            with urllib.request.urlopen(req, timeout=45) as response:
                body = response.read()
                status, final = response.status, response.geturl()
                ctype = response.headers.get('Content-Type', '')
            (out / 'pages' / f'{key}.bin').write_bytes(body)
            entry.update({'outcome': 'captured', 'status': status, 'final_url': final,
                          'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                          'content_type': ctype, 'file': f'pages/{key}.bin'})
            if 'html' in ctype:
                render = Render()
                render.feed(body.decode('utf-8', 'replace'))
                (out / 'pages' / f'{key}.txt').write_text(render.text() + '\n', encoding='utf-8')
                entry['text_file'] = f'pages/{key}.txt'
            print(f'{status} {len(body):>8}  {url}')
        except urllib.error.HTTPError as exc:
            entry.update({'outcome': 'http_error', 'status': exc.code, 'detail': str(exc.reason)[:160]})
            print(f'HTTP {exc.code}  {url}')
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
            entry.update({'outcome': 'network_error', 'detail': f'{type(exc).__name__}: {exc}'[:160]})
            print(f'ERR  {url}: {entry["detail"]}')
        entry['fetched_at_utc'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        doc['pages'].append(entry)
        if index + 1 < len(urls):
            time.sleep(args.delay)
    doc['finished_at_utc'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    (out / 'manifest.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    ok = sum(1 for p in doc['pages'] if p.get('outcome') == 'captured')
    print(f'\ncaptured {ok}/{len(urls)} listed URLs -> {out}/manifest.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
