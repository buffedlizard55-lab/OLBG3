#!/usr/bin/env python3
"""live_refresh.py — run the extraction and verification steps against the newest committed capture.

Keeping the two steps behind one entry point means CI does not need to know which capture
directory an agent committed last: the newest one by name wins, and if there is no capture or no
official probe the step says so and changes nothing.

Usage
-----
    python scripts/live_refresh.py            # newest capture + newest official probe
    python scripts/live_refresh.py --check    # report what would be used, change nothing
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'


def newest(pattern: str, marker: str = 'manifest.json') -> Path | None:
    candidates = [p for p in RAW.glob(pattern) if (p / marker).exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.name)


def run(script: str, *args: str) -> int:
    cmd = [sys.executable, str(ROOT / 'scripts' / script), *args]
    print('$', ' '.join(str(c) for c in cmd))
    return subprocess.call(cmd)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    capture = newest('live-*')
    probe = newest('official-*')
    if capture is None:
        print('no live capture committed; nothing to extract')
        return 1
    print(f'capture : {capture.relative_to(ROOT)}')
    print(f'probe   : {probe.relative_to(ROOT) if probe else "none"}')

    stamp = capture.name.replace('live-', '')
    tsv = RAW / f'olbg-harvest-{stamp}.tsv'
    print(f'tsv     : {tsv.relative_to(ROOT)}')
    if args.check:
        return 0

    code = run('extract_listings.py', '--capture', str(capture), '--out', str(tsv))
    if code:
        print('extraction failed')
        return code
    if probe is None:
        print('no official probe committed; verification skipped (rows stay unverified)')
        return 0
    code = run('verify_live.py', '--probe', str(probe), '--harvest', str(tsv))
    if code:
        print('verification failed')
        return code
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
