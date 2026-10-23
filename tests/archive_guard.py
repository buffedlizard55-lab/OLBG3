"""Shared guard for tests that pin a dated snapshot.

Several audit tests written by earlier sessions assert the *state* of a particular harvest: the
2026-10-22T2130Z capture owning the board, three Basketball HIGH picks, a declared supplementary
capture and so on. Those assertions are still true of that snapshot, and the dated files are never
edited — but once a newer capture becomes the live primary harvest, the assertions no longer describe
the current build.

Rather than delete the pins or quietly weaken them, each class that pins a snapshot carries one
decorator naming the snapshot it describes. When the live harvest has moved on, the class is skipped
with a message that says exactly why, and test_live_20261023 asserts the archive it describes is
still present and byte-identical. FL-137 records the convention.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pins(harvest_name: str):
    """Skip the decorated test class unless this dated harvest is the live primary harvest."""
    try:
        meta = json.loads((ROOT / 'data/meta.json').read_text())
    except (OSError, ValueError):
        return unittest.skip('data/meta.json unreadable; snapshot pin cannot be evaluated')
    live = (meta.get('harvest_file') or '').rsplit('/', 1)[-1]
    if live == harvest_name:
        return lambda cls: cls
    return unittest.skip(
        f'Pins the {harvest_name} snapshot, which is archived: the live harvest is now {live}. '
        f'The dated file is unchanged and is asserted present by tests/test_live_20261023.py (FL-137).')
