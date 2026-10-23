#!/usr/bin/env python3
"""extract_listings.py — turn a committed live capture into the v3 harvest TSV.

Input : data/raw/live-<stamp>/  (produced by scripts/live_harvest.py: manifest.json + listings/*.html)
Output: data/raw/olbg-harvest-<stamp>.tsv, format v3

Everything written here is copied out of the served HTML of one capture. No value is
computed, converted or guessed:

  * ``start_utc`` is the value of the card's own ``<time itemprop="startDate" datetime="…">``
    attribute — OLBG's machine-readable start, copied verbatim.
  * ``printed_clock`` is the clock OLBG printed next to it, copied verbatim.
  * ``odds_decimal`` / ``odds_american`` are the card's ``data-decimal`` / ``data-american``
    attributes. They are OLBG's displayed price for that selection, not a bookmaker sheet
    read by this project and not our own line.
  * ``tips`` is the literal ``n/m Win Tips`` text; ``tip_share_pct`` is the literal
    percentage the same card prints.

A card whose fields cannot all be read from its own markup is emitted with the unreadable
fields blank and named in ``parse_gaps``; nothing is back-filled from a neighbouring card.

An empty capture is evidence, not a harvest
-------------------------------------------
OLBG's public listing pages carry no tip cards overnight: the 2026-10-23T21:30Z capture took
all 18 in-scope listings at HTTP 200 (220-309 KB each) and found **zero** cards on every one.
Before this guard, that capture still produced ``data/raw/olbg-harvest-<stamp>.tsv`` — six
comment lines and no data rows — because ``write_tsv()`` was called unconditionally. Two
consequences followed: the archive pin in ``tests/test_live_20261023.py`` (which asserts the
newest harvest filename) went red, and any step that resolves "the newest harvest TSV" rather
than ``data/meta.json["harvest_file"]`` would have replaced all 180 published rows with
nothing. So by default a zero-row capture writes its ``extract-report.json`` (the evidence that
the listings really were empty) and exits ``3`` **without** writing a harvest file. Pass
``--allow-empty`` only when the empty TSV is itself the artifact you want.

Usage
-----
    python scripts/extract_listings.py --capture data/raw/live-20261023T1700Z
    python scripts/extract_listings.py --capture ... --allow-empty   # keep a zero-row TSV
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Exit code for "the capture was readable but carried no tip cards, so no harvest was written".
#: Distinct from 1 so callers (scripts/live_refresh.py) can tell an empty listing from a failure.
EMPTY_CAPTURE = 3

CARD = '<div class="grd tip content-visibility-auto">'
EVENT_HREF = re.compile(r'href="(https://www\.olbg\.com/betting-tips/([^"?]*)/\d+\?event_id=(\d+))"')
NAME = re.compile(r'<h5[^>]*itemprop="name">([^<]*)</h5>')
START = re.compile(r'itemprop="startDate" datetime="([^"]*)"')
PRINTED = re.compile(r'itemprop="startDate"[^>]*>(.*?)</time>', re.S)
MARKET = re.compile(r'<p class="truncate text-sm">([^<]*)</p>')
SELECTION = re.compile(r'<h4[^>]*>\s*([^<]*?)\s*</h4>')
ODDS = re.compile(r'data-decimal="([^"]*)"\s+data-american="([^"]*)"\s+data-fractional="([^"]*)"')
TIPS = re.compile(r'<b class="text-xs truncate">([^<]*)</b>')
SHARE = re.compile(r'--confidence:\s*(\d+)%')

SPORT_SLUG = {
    'Tennis': 'Tennis', 'Basketball': 'Basketball', 'Golf': 'Golf', 'Cricket': 'Cricket',
    'Snooker': 'Snooker', 'Rugby Union': 'Rugby_Union', 'Rugby League': 'Rugby_League',
    'Baseball': 'Baseball', 'Ice Hockey': 'Ice_Hockey', 'Motor Racing': 'Motor_Racing',
    'Darts': 'Darts', 'Handball': 'Handball', 'Volleyball': 'Volleyball',
    'Gaelic Football': 'Gaelic_Football', 'Greyhounds': 'Greyhounds',
}


def display_path(path: Path) -> str:
    """Repo-relative for paths inside the repo, absolute otherwise.

    The capture path already guarded itself with ``is_relative_to``; the harvest path did not, so
    ``--out /tmp/whatever.tsv`` wrote the file and then died with ``ValueError`` on the summary
    line, exiting 1 — which ``scripts/live_refresh.py`` reads as "extraction failed". One helper
    used for both paths removes the inconsistency.
    """
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def clean_printed(raw: str) -> tuple[str, str]:
    """Return (date_label, time_label) from the <time> element's inner text."""
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = ' '.join(text.split())
    m = re.match(r'^(.*?)\s+(\d{1,2}:\d{2})$', text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return text, ''


def parse_capture(capture: Path) -> tuple[list[dict], dict]:
    manifest = json.loads((capture / 'manifest.json').read_text())
    rows: list[dict] = []
    report = {
        'capture': display_path(capture),
        'captured_at_utc': manifest.get('captured_at_utc'),
        'listings': [],
        'parse_gaps': {},
        'render_offsets': {},
    }
    for page in manifest['pages']:
        entry = {'path': page['path'], 'sport': page['sport'], 'league': page['league'],
                 'outcome': page.get('outcome'), 'cards': 0, 'rows': 0}
        if page.get('outcome') != 'captured':
            report['listings'].append(entry)
            continue
        html = (capture / page['html_file']).read_text(encoding='utf-8', errors='replace')
        chunks = html.split(CARD)[1:]
        entry['cards'] = len(chunks)
        for chunk in chunks:
            href = EVENT_HREF.search(chunk)
            name = NAME.search(chunk)
            start = START.search(chunk)
            printed = PRINTED.search(chunk)
            market = MARKET.search(chunk)
            selection = SELECTION.search(chunk)
            odds = ODDS.search(chunk)
            tips = TIPS.search(chunk)
            share = SHARE.search(chunk)
            if not href:
                report['parse_gaps'].setdefault('no_event_link', 0)
                report['parse_gaps']['no_event_link'] += 1
                continue
            date_label, time_label = clean_printed(printed.group(1)) if printed else ('', '')
            row = {
                'sport': page['sport'],
                'league_label': page['league'],
                'path_prefix': href.group(2),
                'slug': href.group(2).split('/')[-1],
                'event_id': href.group(3),
                'date_label': date_label,
                'time_label': time_label,
                'market': market.group(1).strip() if market else '',
                'consensus': selection.group(1).strip() if selection else '',
                'tips': tips.group(1).strip() if tips else '',
                'note': '',
                'start_utc': start.group(1).strip() if start else '',
                'odds_decimal': odds.group(1).strip() if odds else '',
                'odds_american': odds.group(2).strip() if odds else '',
                'odds_fractional': odds.group(3).strip() if odds else '',
                'tip_share_pct': share.group(1).strip() if share else '',
                'event_name': name.group(1).strip() if name else '',
                'listing_url': page['url'],
                'listing_path': page['path'],
                'captured_at_utc': page.get('fetched_at_utc') or manifest.get('captured_at_utc'),
            }
            for field in ('market', 'consensus', 'tips', 'start_utc', 'odds_decimal'):
                if not row[field]:
                    key = f"{page['sport']}:{field}"
                    report['parse_gaps'][key] = report['parse_gaps'].get(key, 0) + 1
            rows.append(row)
            entry['rows'] += 1
        # Cross-check OLBG's ISO startDate against the clock it printed. Recorded, never applied.
        offsets = set()
        for row in rows:
            if row['listing_path'] != page['path'] or not row['start_utc'] or not row['time_label']:
                continue
            try:
                utc = dt.datetime.fromisoformat(row['start_utc'].replace('Z', '+00:00'))
            except ValueError:
                continue
            if row['date_label'].lower() in ('today', 'tomorrow') or re.match(r'^\d{1,2} \w{3}$', row['date_label']):
                base = utc.replace(tzinfo=None)
                printed_day = row['date_label'].lower()
                hh, mm = (int(x) for x in row['time_label'].split(':'))
                delta_h = (hh - base.hour) % 24
                offsets.add(delta_h)
        if offsets:
            report['render_offsets'][page['path']] = sorted(offsets)
        report['listings'].append(entry)
    return rows, report


def dedupe(rows: list[dict]) -> list[dict]:
    """One row per OLBG event_id. The first listing in manifest order wins."""
    seen: dict[str, dict] = {}
    for row in rows:
        keep = seen.get(row['event_id'])
        if keep is None:
            seen[row['event_id']] = row
            continue
        # Same event on two endpoints: keep the first, record that the other also listed it.
        other = f"{row['sport']}/{row['league_label']}"
        note = keep['note']
        keep['note'] = (note + '; ' if note else '') + f'also listed on {other}'
    return list(seen.values())


def write_tsv(rows: list[dict], report: dict, out: Path, capture_name: str) -> None:
    header = [
        f"# OLBG3 live harvest {capture_name} — format v3",
        "# Columns: sport|league_label|path_prefix|slug|event_id|date_label|time_label|market|consensus|tips|note|start_utc|odds_decimal|odds_american|odds_fractional|tip_share_pct|event_name|listing_url",
        "# start_utc is OLBG's own <time itemprop=startDate datetime> attribute, copied verbatim.",
        "# odds_* are the prices OLBG printed for that selection; they are NOT our line and NOT a bookmaker sheet read by this project.",
        f"# captured_at_utc: {report.get('captured_at_utc')}",
        "# Every value below is copied from the served HTML of the capture named above. Blank means unreadable, never inferred.",
    ]
    lines = list(header)
    for row in rows:
        lines.append('|'.join(str(row[k]) for k in (
            'sport', 'league_label', 'path_prefix', 'slug', 'event_id', 'date_label', 'time_label',
            'market', 'consensus', 'tips', 'note', 'start_utc', 'odds_decimal', 'odds_american',
            'odds_fractional', 'tip_share_pct', 'event_name', 'listing_url')))
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--allow-empty', action='store_true',
                    help='write a zero-row harvest TSV when the capture carries no tip cards '
                         '(default: write the extract-report only and exit 3)')
    args = ap.parse_args()

    capture = Path(args.capture)
    if not capture.is_absolute():
        capture = ROOT / capture
    stamp = capture.name.replace('live-', '')
    out = Path(args.out) if args.out else ROOT / 'data/raw' / f'olbg-harvest-{stamp}.tsv'

    rows, report = parse_capture(capture)
    rows = dedupe(rows)
    rows.sort(key=lambda r: (r['sport'], r['start_utc'], r['event_name']))

    # The extract-report is written on both paths: it is the evidence that the listings were
    # genuinely empty, which is a different claim from "we failed to read them".
    (capture / 'extract-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    if not rows:
        captured = [p for p in report['listings'] if p['outcome'] == 'captured']
        if not args.allow_empty:
            # Idempotence: a previous run under the old behaviour may have left a zero-row TSV
            # here. Removing only a file that has no data rows keeps a re-run byte-stable and
            # can never delete a real harvest.
            if out.exists():
                stale = [l for l in out.read_text(encoding='utf-8').splitlines()
                         if l.strip() and not l.startswith('#')]
                if not stale:
                    out.unlink()
                    print(f'removed the zero-row {out.name} left by an earlier run')
            print(f'{capture.name}: {len(captured)} listings captured, 0 tip cards found — '
                  f'no harvest written ({out.name} not created).')
            print('The capture is kept as evidence; extract-report.json records the empty state. '
                  'This is what OLBG serves overnight, not a read failure.')
            return EMPTY_CAPTURE
        print(f'{capture.name}: 0 tip cards; writing an empty harvest because --allow-empty was given.')

    write_tsv(rows, report, out, capture.name)

    by_sport: dict[str, int] = {}
    for row in rows:
        by_sport[row['sport']] = by_sport.get(row['sport'], 0) + 1
    print(f'rows: {len(rows)} across {len(by_sport)} sports -> {display_path(out)}')
    for sport, count in sorted(by_sport.items()):
        print(f'  {sport:<16} {count}')
    empty = [p for p in report['listings'] if p['outcome'] == 'captured' and not p['cards']]
    if empty:
        print('listings with zero tip cards:', [p['path'] for p in empty])
    if report['parse_gaps']:
        print('parse gaps:', report['parse_gaps'])
    if report['render_offsets']:
        print('printed clock minus startDate (hours):', report['render_offsets'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
