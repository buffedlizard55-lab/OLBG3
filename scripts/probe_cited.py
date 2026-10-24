#!/usr/bin/env python3
"""probe_cited.py — re-fetch the source pages behind current HIGH predictions.

The release gate expires an official clock observation 24 hours after it was read. Re-reading the
same cited page is the only honest way to renew that observation. Form/history sources can differ
from the clock source, so every non-OLBG link on a current HIGH write-up is captured too. Nothing is
copied forward, and a page that no longer states a fixture simply yields no supporting text.

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
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

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


def cited_urls(today: str) -> tuple[dict, dict[str, list[str]]]:
    """Return upcoming release records and every source behind a current HIGH write-up.

    A release URL establishes the clock only. The form, history and injury claims in a prediction
    often cite different official documents, so probing release URLs alone cannot support a
    line-by-line re-check of the prose. OLBG listing links are captured by live_harvest.py and are
    deliberately excluded here to avoid fetching the same page twice.
    """
    checks = json.loads((DATA / 'release_checks.json').read_text(encoding='utf-8'))['events']
    upcoming = {k: v for k, v in checks.items() if (v.get('date') or '') >= today and v.get('source')}
    refs: dict[str, set[str]] = defaultdict(set)
    for event_id, record in upcoming.items():
        refs[record['source']].add(f'release/{event_id}')

    prediction_files = (
        ('root', DATA / 'predictions.json', 'ref', 'body'),
        ('olbg', DATA / 'predictions-olbg.json', 'match_id', 'text'),
    )
    for track, path, id_key, _text_key in prediction_files:
        doc = json.loads(path.read_text(encoding='utf-8'))
        for piece in doc.get('predictions', []):
            if piece.get('status') != 'high':
                continue
            ref = piece.get(id_key) or '?'
            for source in piece.get('sources') or []:
                url = (source.get('url') or '').strip() if isinstance(source, dict) else ''
                parsed = urlsplit(url)
                if parsed.scheme not in ('http', 'https') or not parsed.hostname:
                    continue
                if parsed.hostname.lower() == 'www.olbg.com':
                    continue
                refs[url].add(f'{track}/{ref}')
    return upcoming, {url: sorted(values) for url, values in sorted(refs.items())}


def evidence_key(url: str) -> str:
    """Collision-resistant, reviewable filename stem for one cited URL."""
    readable = re.sub(r'[^A-Za-z0-9]+', '-', url.split('://', 1)[-1])[:78].strip('-')
    return f'{readable}-{hashlib.sha256(url.encode()).hexdigest()[:12]}'


def store_response(out: Path, key: str, final_url: str, content_type: str,
                   body: bytes) -> dict:
    """Persist one response without ever decoding binary evidence.

    The returned fields are copied into the manifest entry. Keeping this operation separate from
    networking makes byte fidelity directly testable and keeps future format handling honest.
    """
    pages = out / 'pages'
    pages.mkdir(parents=True, exist_ok=True)
    path_lower = urlsplit(final_url).path.lower()
    ctype_lower = content_type.lower()
    if 'json' in ctype_lower or path_lower.endswith('.json'):
        (pages / f'{key}.json').write_bytes(body)
        return {'file': f'pages/{key}.json', 'storage': 'verbatim_json'}
    if 'pdf' in ctype_lower or path_lower.endswith('.pdf'):
        (pages / f'{key}.pdf').write_bytes(body)
        return {'file': f'pages/{key}.pdf', 'storage': 'verbatim_pdf'}
    if ctype_lower.startswith(('image/', 'audio/', 'video/', 'application/octet-stream')):
        (pages / f'{key}.bin').write_bytes(body)
        return {'file': f'pages/{key}.bin', 'storage': 'verbatim_binary'}

    render = Render()
    render.feed(body.decode('utf-8', 'replace'))
    text = render.text()
    (pages / f'{key}.txt').write_text(text + '\n', encoding='utf-8')
    return {'file': f'pages/{key}.txt', 'storage': 'rendered_text',
            'text_chars': len(text)}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=2.0)
    args = ap.parse_args()

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    upcoming, source_refs = cited_urls(today)
    urls = sorted(source_refs)

    out = Path(args.out)
    (out / 'pages').mkdir(parents=True, exist_ok=True)
    doc = {'tool': 'scripts/probe_cited.py', 'user_agent': AGENT,
           'started_at_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'scope_policy': ('Upcoming exact-clock source pages plus every non-OLBG source linked '
                            'by a currently HIGH written prediction. A successful fetch records '
                            'what the URL served; it does not by itself certify every prose claim.'),
           'events_in_scope': sorted(upcoming),
           'prediction_source_references': source_refs,
           'pages': []}

    for index, url in enumerate(urls):
        key = evidence_key(url)
        entry = {'url': url, 'key': key, 'referenced_by': source_refs[url]}
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
            entry.update(store_response(out, key, final, ctype, body))
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
