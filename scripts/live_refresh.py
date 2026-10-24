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
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
sys.path.insert(0, str(ROOT / 'scripts'))
from extract_listings import EMPTY_CAPTURE  # noqa: E402


STAMP = re.compile(r'(\d{8}T\d{4}Z)')


def stamp_of(path: Path) -> str:
    """The capture's own UTC stamp, wherever the session put it in the directory name.

    Sorting on the whole name was wrong once a capture directory was named
    `live-<session-id>-<stamp>`: "live-1c6981d1-..." sorts before every
    "live-2026...", so a fresh capture was silently ignored in favour of the
    previous day's board. The stamp is the only part that orders captures.
    """
    found = STAMP.findall(path.name)
    return found[-1] if found else ''


def candidates(pattern: str, marker: str = 'manifest.json') -> list[Path]:
    """Committed capture/probe directories, newest first by their own UTC stamp."""
    return sorted((p for p in RAW.glob(pattern) if (p / marker).exists()),
                  key=lambda p: (stamp_of(p), p.name), reverse=True)


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
        code = run('extract_listings.py', '--capture', str(capture), '--out', str(target))
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
    if probe is None:
        print('no official probe committed; verification skipped (rows stay unverified)')
        return 0

    # Only re-verify when the capture we settled on is NEWER than the one that produced the
    # committed primary harvest. Two reasons, both structural:
    #   * Falling back to an older populated capture means "no new capture arrived", and that
    #     capture's verifications are already in data/verifications.json. Re-running the probe
    #     against it rewrites data/release_checks.json (including its accumulated policy history
    #     and top-level checked_at) without adding a single new fact.
    #   * The pipeline computes the board (scripts/model.py, tools/originate.py) BEFORE this step.
    #     Re-stamping release evidence afterwards desynchronises the stored release blocks from
    #     the evidence scripts/check_board.py recomputes, and the integrity check rightly fails.
    # Renewing a source observation is a deliberate data change, made and rebuilt as one, not a
    # side effect of choosing a capture directory.
    live_primary = live_primary_capture()
    if live_primary is not None and stamp_of(chosen) <= stamp_of(Path(live_primary)):
        print(f'verification skipped: {chosen.name} is not newer than the committed primary '
              f'harvest ({live_primary}); its verifications are already published.')
        return 0

    code = run('verify_live.py', '--probe', str(probe), '--harvest', str(tsv))
    if code:
        print('verification failed')
        return code
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
