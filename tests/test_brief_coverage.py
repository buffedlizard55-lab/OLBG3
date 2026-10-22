#!/usr/bin/env python3
"""Tests for the brief-coverage accounting and the cross-track reconciliation list.

The point of these tests is that the published numbers are produced from the committed rows, so a
stale or hand-edited accounting fails the build instead of quietly disagreeing with the board.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brief_coverage as bc  # noqa: E402


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


class TestBriefCoverageRecompute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = bc.build()
        cls.committed = load("brief_coverage.json")

    def test_committed_file_matches_a_fresh_recompute(self):
        # If a row, price or grade moves without regenerating the accounting, this fails.
        self.assertEqual(self.committed, self.doc,
                         "data/brief_coverage.json is stale; run scripts/brief_coverage.py")

    def test_every_covered_sport_is_accounted_once(self):
        allowed = sorted(k.replace("_", " ") for k in load("meta.json")["allowed_sports_olbg_ids"])
        seen = [s["sport"] for s in self.doc["sports"]]
        self.assertEqual(sorted(seen), allowed)
        self.assertEqual(len(seen), len(set(seen)))

    def test_target_is_the_briefs_five_per_sport(self):
        self.assertEqual(self.doc["brief_target"]["picks_per_sport_per_day"], 5)
        for s in self.doc["sports"]:
            self.assertEqual(s["target"], 5)
            self.assertEqual(s["shortfall"], max(0, 5 - s["live_high_union"]))
            self.assertEqual(s["meets_target"], s["live_high_union"] >= 5)

    def test_totals_recompute(self):
        sports = self.doc["sports"]
        t = self.doc["totals"]
        self.assertEqual(t["sports_listed"], len(sports))
        self.assertEqual(t["live_high_union"], sum(s["live_high_union"] for s in sports))
        self.assertEqual(t["live_high_root"], sum(s["root_high"] for s in sports))
        self.assertEqual(t["live_high_olbg"], sum(s["olbg_high"] for s in sports))
        self.assertEqual(t["sports_meeting_target"], sum(1 for s in sports if s["meets_target"]))
        self.assertEqual(
            t["shortfall_to_target"],
            max(0, t["target_picks_if_all_sports_met"] - t["live_high_union"]),
        )

    def test_excluded_sports_are_absent(self):
        names = {s["sport"].lower() for s in self.doc["sports"]}
        for banned in ("soccer", "boxing", "ufc", "mma", "american football",
                       "hurling", "horse racing", "cycling", "specials"):
            self.assertNotIn(banned, names)

    def test_live_high_picks_are_counted_once_and_priced_in_band(self):
        ids = [p["event_id"] for s in self.doc["sports"] for p in s["live_picks"]]
        self.assertEqual(len(ids), len(set(ids)), "a fixture was counted twice across the two tracks")
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from board_dates import in_band
        for s in self.doc["sports"]:
            for p in s["live_picks"]:
                self.assertTrue(in_band(p["price"]), f"{p['event_id']} live HIGH outside the band")
                self.assertTrue(p["tracks"], f"{p['event_id']} has no publishing track")

    def test_every_shortfall_states_a_reason(self):
        for s in self.doc["sports"]:
            if s["shortfall"]:
                self.assertTrue(s["reasons"], f"{s['sport']} falls short without a stated reason")


class TestCrossTrack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = bc.build()
        cls.xt = cls.doc["cross_track"]

    def test_counts_reconcile(self):
        xt = self.xt
        self.assertEqual(
            xt["paired_fixtures"],
            xt["same_selection"] + xt["different_selection"] + xt["withheld_by_one_track"],
        )
        self.assertEqual(xt["different_selection"], len(xt["rows"]))

    def test_every_disagreement_carries_both_sides_and_a_source(self):
        for row in self.xt["rows"]:
            self.assertNotEqual(row["root_selection"].lower(), row["olbg_selection"].lower())
            import re
            self.assertRegex(row["root_ref"], r"^[A-Z]{3}-\d+$")
            self.assertTrue(row["olbg_ref"])
            self.assertTrue(row["olbg_url"].startswith("https://www.olbg.com/"))

    def test_paired_fixtures_are_unique(self):
        ids = [r["event_id"] for r in self.xt["rows"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestBuildGuards(unittest.TestCase):
    """The accounting must not be able to hide a row that the board publishes."""

    def test_gap_rows_are_included_in_root_counts(self):
        doc = bc.build()
        gap = load("gap_sports.json")["rows"]
        ev = load("events.json")["events"]
        self.assertEqual(doc["totals"]["root_rows"], len(ev) + len(gap))

    def test_olbg_track_rows_are_included(self):
        doc = bc.build()
        lines = load("lines.json")
        self.assertEqual(doc["totals"]["olbg_rows"], len(lines))


if __name__ == "__main__":
    unittest.main()
