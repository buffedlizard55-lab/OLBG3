#!/usr/bin/env python3
"""live_refresh.py — run the extraction and verification steps against the newest committed capture.

Keeping the two steps behind one entry point means CI does not need to know which capture
directory an agent committed last. The newest capture by name is tried first, but "newest" no
longer means "wins": a capture whose listings carried no tip cards is skipped as a harvest and
the walk continues back to the newest capture that actually has rows. OLBG serves empty listing
pages overnight — the 2026-10-23T21:30Z capture took all 18 in-scope listings at HTTP 200 and
found zero cards on every one — and an empty capture used to become a zero-row harvest file that
broke the archive pin in tests/test_live_20261023.py. If there is no capture, or none of them has
cards, the step says so and changes nothing.

Usage
-----
    python scripts/live_refresh.py            # newest capture + newest official probe
    python scripts/live_refresh.py --check    # report what would be used, change nothing
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
sys.path.insert(0, str(ROOT / 'scripts'))
from extract_listings import EMPTY_CAPTURE  # noqa: E402


def candidates(pattern: str, marker: str = 'manifest.json') -> list[Path]:
    """Committed capture/probe directories, newest first by name."""
    return sorted((p for p in RAW.glob(pattern) if (p / marker).exists()),
                  key=lambda p: p.name, reverse=True)


def newest(pattern: str, marker: str = 'manifest.json') -> Path | None:
    found = candidates(pattern, marker)
    return found[0] if found else None


def cards_in(capture: Path) -> int | None:
    """Tip cards a capture yielded, from its committed extract-report. None if not yet extracted."""
    report = capture / 'extract-report.json'
    if not report.exists():
        return None
    try:
        doc = json.loads(report.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    listings = doc.get('listings') or []
    return sum(int(p.get('cards') or 0) for p in listings)


def live_primary_capture() -> str | None:
    """Capture directory name behind data/meta.json["harvest_file"], e.g. 'live-20261023T1700Z'.

    None when the pinned harvest is not one of the committed live captures (an agent-authored
    TSV, say), in which case there is nothing to compare a candidate capture against.
    """
    try:
        meta = json.loads((ROOT / 'data' / 'meta.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    name = (meta.get('harvest_file') or '').rsplit('/', 1)[-1]
    if not name.startswith('olbg-harvest-') or not name.endswith('.tsv'):
        return None
    return 'live-' + name[len('olbg-harvest-'):-len('.tsv')]


def run(script: str, *args: str) -> int:
    cmd = [sys.executable, str(ROOT / 'scripts' / script), *args]
    print('$', ' '.join(str(c) for c in cmd))
    return subprocess.call(cmd)


def _harvest_rows(path: Path) -> list[list[str]]:
    """Return v3 data rows exactly as stored; comments and blanks are not rows."""
    return [
        line.split('|')
        for line in path.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]


def extract_capture(capture: Path, target: Path) -> int:
    """Extract SSR cards, retrying hydration data only when the SSR result is empty."""
    code = run('extract_listings.py', '--capture', str(capture), '--out', str(target))
    if code == EMPTY_CAPTURE:
        print(f'{capture.name}: no SSR tip cards; retrying the committed response with '
              'the SvelteKit hydration fallback.')
        code = run('extract_listings.py', '--capture', str(capture), '--out', str(target),
                   '--svelte-fallback')
    return code


def promote_primary(capture: Path, harvest: Path) -> bool:
    """Point the /olbg track at a newly captured, non-empty listing snapshot.

    Raw captures are immutable evidence. Promotion changes only ``data/meta.json`` so the next
    ``tools/build_dataset.py`` invocation reads the new TSV. Older primaries remain in ``data/raw``
    and are logged in ``archived_primary_harvests``; they are not chained into the current board,
    because doing so would make rotated-off or already-started cards look current.
    """
    rows = _harvest_rows(harvest)
    if not rows:
        raise ValueError(f'{harvest} has no data rows and cannot become the primary harvest')
    manifest = json.loads((capture / 'manifest.json').read_text(encoding='utf-8'))
    meta_path = ROOT / 'data' / 'meta.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    rel_harvest = str(harvest.relative_to(ROOT / 'data'))
    if meta.get('harvest_file') == rel_harvest:
        return False

    old_file = meta.get('harvest_file')
    old_completed = meta.get('harvest_completed_utc')
    history = meta.setdefault('archived_primary_harvests', [])
    if old_file and not any(item.get('file') == old_file for item in history):
        history.append({
            'file': old_file,
            'harvest_completed_utc': old_completed,
            'replaced_by': rel_harvest,
            'reason': ('A newer populated 18-endpoint OLBG capture became the current /olbg '
                       'snapshot. The old bytes remain immutable in data/raw.'),
        })

    fetched = [
        page.get('fetched_at_utc') for page in manifest.get('pages', [])
        if page.get('fetched_at_utc')
    ]
    started = manifest.get('captured_at_utc') or (min(fetched) if fetched else '')
    completed = max(fetched) if fetched else started
    sports = Counter(parts[0] for parts in rows if parts)
    empty_paths = [
        page.get('path') for page in manifest.get('pages', [])
        if page.get('outcome') == 'captured'
        and not any(parts[0] == page.get('sport') for parts in rows)
    ]
    stamp = (started or capture.name).replace('-', '').replace(':', '')[:8]

    meta.update({
        'run_id': f'S-{stamp}-LIVE',
        'run_started_utc': started,
        'harvest_completed_utc': completed,
        'olbg_locale_date': (started or '')[:10],
        'harvest_file': rel_harvest,
        'harvest_format': 'v3',
        'harvest_timezone_note': (
            'Format v3 preserves OLBG\'s machine-readable startDate UTC value and the clock '
            'printed on the card. Neither is treated as an official competition clock; official '
            'release checks are stored separately and missing values remain blank.'),
        'previous_harvest': None,
        'previous_harvests_extra': [],
        'supplementary_harvests': [],
        'harvest_method': {
            'tool': ('scripts/live_harvest.py plus scripts/extract_listings.py '
                     '(SSR cards; SvelteKit fallback only when SSR is empty)'),
            'pages': [page.get('url') for page in manifest.get('pages', []) if page.get('url')],
            'granularity': (
                f'{len(rows)} unique live listing rows across {len(sports)} sports from the '
                f'18-endpoint capture {capture.relative_to(ROOT)}; zero-row sports remain '
                f'explicitly empty ({", ".join(empty_paths) if empty_paths else "none"}).'),
            'values_inferred': 'none — unreadable values stay blank; source labels are copied from the captured response',
        },
        'archive_note': (
            f'The current /olbg board is rebuilt only from {rel_harvest}. Earlier harvests remain '
            'immutable audit artifacts and are not carried into the current snapshot.'),
    })
    session_note = f'automated primary promotion from {capture.name}'
    prior_session = (meta.get('session') or '').strip()
    if session_note not in prior_session:
        meta['session'] = f'{prior_session} + {session_note}' if prior_session else session_note
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'meta     : promoted {rel_harvest} ({len(rows)} rows; {len(sports)} sports)')
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    captures = candidates('live-*')
    probe = newest('official-*')
    if not captures:
        print('no live capture committed; nothing to extract')
        return 1
    print(f'probe   : {probe.relative_to(ROOT) if probe else "none"}')

    if args.check:
        # Side-effect free: report what the extraction loop would choose, using the committed
        # extract-reports. A capture with no report yet is reported as unknown rather than guessed.
        for capture in captures:
            cards = cards_in(capture)
            verdict = ('no tip cards — skipped as a harvest' if cards == 0
                       else f'{cards} tip cards' if cards is not None
                       else 'not yet extracted')
            print(f'capture : {capture.relative_to(ROOT)}  ({verdict})')
        usable = next((c for c in captures if (cards_in(c) or 0) > 0), None)
        print(f'harvest : {usable.relative_to(ROOT) if usable else "none of the committed captures carries tip cards"}')
        return 0

    # An empty listing page is what OLBG serves overnight (all 18 in-scope listings returned
    # HTTP 200 with zero tip cards at 2026-10-23T21:30Z). Such a capture is evidence, not a
    # harvest, so the loop walks back to the newest capture that actually carries rows instead
    # of publishing a zero-row harvest over the committed board.
    chosen = None
    tsv = None
    for capture in captures:
        stamp = capture.name.replace('live-', '')
        target = RAW / f'olbg-harvest-{stamp}.tsv'
        # Prefer the ordinary server-rendered cards. Hydration parsing is a compatibility retry,
        # not the default interpretation of every response: only invoke it when SSR is genuinely
        # empty (for example, the committed 21:33Z Svelte-only evidence snapshot).
        code = extract_capture(capture, target)
        if code == EMPTY_CAPTURE:
            print(f'{capture.name}: empty listing capture, not usable as a harvest; '
                  f'kept as evidence and moving to the next capture.')
            continue
        if code:
            print('extraction failed')
            return code
        chosen, tsv = capture, target
        break

    if chosen is None:
        print('capture : none of the committed live captures carries tip cards.')
        print('No harvest rewritten. data/meta.json["harvest_file"] still names the live '
              'primary, so the board keeps the rows that capture produced.')
        return 0

    print(f'capture : {chosen.relative_to(ROOT)}')
    print(f'tsv     : {tsv.relative_to(ROOT)}')
    # Only re-verify and promote when this capture is newer than the one that produced the
    # committed primary harvest. Falling back to an older populated capture adds no fact, and
    # re-stamping it would falsely renew release evidence. ``pages.yml`` runs this step before
    # either board is built, so a genuine new observation is consumed consistently by both tracks.
    live_primary = live_primary_capture()
    if live_primary is not None and chosen.name <= live_primary:
        print(f'verification skipped: {chosen.name} is not newer than the committed primary '
              f'harvest ({live_primary}); its verifications are already published.')
        return 0

    if probe is None:
        print('no official probe committed; fixture verification skipped (unmatched rows stay unverified)')
    else:
        code = run('verify_live.py', '--probe', str(probe), '--harvest', str(tsv))
        if code:
            print('verification failed')
            return code

    promote_primary(chosen, tsv)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
