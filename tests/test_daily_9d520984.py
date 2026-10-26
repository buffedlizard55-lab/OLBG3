"""session-9d520984: the next-day board (scripts/build_daily.py).

Every assertion uses a frozen instant passed in explicitly, never the wall clock, so these pins
cannot expire when a fixture kicks off (the FL-201 / FL-217 defect class).
"""
import datetime as dt
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_daily  # noqa: E402

RESEARCH = ROOT / "data" / "daily" / "research-20261025.json"
BEFORE = dt.datetime(2026, 10, 24, 22, 31, tzinfo=dt.timezone.utc)
AFTER_ALL = dt.datetime(2026, 11, 2, 0, 0, tzinfo=dt.timezone.utc)
EXPECTED_HIGH = {"NX-CRI-188852", "NX-ICE-200076"}
ZONELESS_FULL_WRITEUPS = {"NX-RUG-609571", "NX-RUG-609554", "NX-VOL-37114"}


def board(clock):
    res = json.loads(RESEARCH.read_text())
    rows = build_daily.read_capture(res["capture"])
    return res, [build_daily.evaluate(r, res["rows"].get(r["event_id"]), clock, res["captured_at_utc"]) for r in rows]


class DailyBoardTest(unittest.TestCase):
    def test_capture_rows_all_published(self):
        _res, rows = board(BEFORE)
        self.assertEqual(len(rows), 124)
        self.assertEqual(len({r["id"] for r in rows}), 124)

    def test_high_set_at_frozen_clock(self):
        _res, rows = board(BEFORE)
        self.assertEqual({r["id"] for r in rows if r["confidence"] == "HIGH"}, EXPECTED_HIGH)

    def test_high_rows_meet_the_brief(self):
        _res, rows = board(BEFORE)
        texts = set()
        for r in rows:
            if r["confidence"] != "HIGH":
                continue
            self.assertGreaterEqual(build_daily.words(r["prose"]), 30, r["id"])
            for term in build_daily.BANNED_TERMS:
                self.assertNotIn(term, r["prose"].lower(), r["id"])
            self.assertTrue(build_daily.BAND_LO <= r["fair_dec"] <= build_daily.BAND_HI, r["id"])
            self.assertGreaterEqual(len(r["official_sources"]), 2, r["id"])
            self.assertTrue(r["official_start"], r["id"])
            self.assertNotIn(r["prose"], texts)
            texts.add(r["prose"])

    def test_everything_closes_after_kickoff(self):
        _res, rows = board(AFTER_ALL)
        upcoming = [r for r in rows if build_daily.parse_utc(r["olbg_start"]) > AFTER_ALL]
        self.assertFalse(any(r["confidence"] == "HIGH" for r in rows))
        for r in rows:
            if r not in upcoming:
                self.assertEqual(r["confidence"], "CLOSED", r["id"])

    def test_research_sources_are_https_and_blanks_stay_blank(self):
        res = json.loads(RESEARCH.read_text())
        for eid, row in res["rows"].items():
            for s in row.get("official_sources", []) + row.get("press_sources", []):
                self.assertTrue(s["url"].startswith("https://"), (eid, s["url"]))
            if not row.get("official_sources"):
                self.assertEqual(row.get("official_start_utc"), "", eid)

    def test_zone_less_clocks_cap_at_medium(self):
        """FL-148: a local clock with no printed zone never becomes a UTC start, so never HIGH."""
        _res, rows = board(BEFORE)
        for r in rows:
            if r["id"] in ZONELESS_FULL_WRITEUPS:
                self.assertEqual(r["confidence"], "MEDIUM", r["id"])
                self.assertEqual(r["official_start"], "", r["id"])
                self.assertEqual(r["reasons"], ["official start printed without a time zone (FL-148 rule)"], r["id"])

    def test_totals_lean_flips_to_the_likelier_side(self):
        _res, rows = board(BEFORE)
        van = next(r for r in rows if r["id"] == "NX-ICE-200075")
        self.assertTrue(van["selection"].startswith("Under"))
        self.assertGreater(van["p"], 0.5)

    def test_nhl_offset_is_marked(self):
        _res, rows = board(BEFORE)
        dal = next(r for r in rows if r["id"] == "NX-ICE-200076")
        self.assertTrue(dal["start_mismatch"])
        self.assertEqual(dal["official_start"], "2026-10-25T22:00:00Z")


if __name__ == "__main__":
    unittest.main()
