"""session-4b642f84 (2026-10-22 evening) audit pins, re-applied on main d3ed893.

This session ran in parallel with sibling evening sessions (784afe97, c038b7f4,
22fd95c8, a1e5112b; PRs #100-#111). Its work was therefore re-applied on top of theirs:
only net-new contributions are pinned here (the 21:30Z harvest as newest chain capture,
30 new root fixtures with their verification split, the 22:10Z release re-observations,
5 new root pieces). Overlapping items (DRT-17 tie, five-per-sport shortfall) are owned
by the sibling register items FL-107/FL-124/FL-102 and are not duplicated.
"""
import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

NEW_VERIFIED = {  # governing-body pages read on 2026-10-22 evening (ATP/WTA/ICC)
    "TEN-41", "TEN-42", "TEN-43", "TEN-44",
    "TEN-45", "TEN-46", "TEN-47", "TEN-48", "CRK-17",
}
NEW_UNVERIFIED = {  # published blank-flagged as FL-103; nothing inferred
    "BKB-31", "BKB-32", "CRK-18",
    "HBL-32", "HBL-33", "HBL-34", "HBL-35", "HBL-36", "HBL-37", "HBL-38",
    "IHO-26", "IHO-27", "IHO-28", "IHO-29", "RGU-17", "RGU-18",
    "VOL-31", "VOL-32", "VOL-33", "VOL-34", "VOL-35",
}


class EveningHarvest4b642f84Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((DATA / "meta.json").read_text())
        cls.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        cls.gap = {r["ref"]: r for r in json.loads((DATA / "gap_sports.json").read_text())["rows"]}
        cls.rc = json.loads((DATA / "release_checks.json").read_text())["events"]
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text())["predictions"]}
        cls.flagged = {i["id"] for i in json.loads((DATA / "flagged.json").read_text())["items"]}
        cls.lines = {r["match_id"]: r for r in json.loads((DATA / "lines.json").read_text())}

    def test_harvest_chain_points_at_evening_capture(self):
        self.assertEqual(self.meta["harvest_file"], "raw/olbg-harvest-20261022T2130Z.tsv")
        self.assertEqual(self.meta["harvest_completed_utc"], "2026-10-22T21:35:00Z")
        self.assertEqual(self.meta["previous_harvest"]["file"], "raw/olbg-harvest-20261022T2055Z.tsv")
        chained = {e["file"] for e in self.meta["previous_harvests_extra"]}
        self.assertIn("raw/olbg-harvest-20261022T0830Z.tsv", chained)
        self.assertTrue((DATA / "raw/olbg-harvest-20261022T2130Z.tsv").exists())

    def test_new_fixtures_verification_split_is_exactly_as_registered(self):
        for ref in NEW_VERIFIED:
            self.assertEqual(self.events[ref]["verification"]["status"], "verified", ref)
        for ref in NEW_UNVERIFIED:
            self.assertEqual(self.events[ref]["verification"]["status"], "unverified", ref)
            self.assertNotEqual(self.events[ref]["pick"]["confidence"], "HIGH", ref)
        self.assertIn("FL-130", self.flagged)

    def test_no_excluded_sport_rows_added(self):
        excluded = {"soccer", "football", "american football", "boxing", "ufc", "mma",
                    "hurling", "horse racing", "cycling", "specials"}
        for ref in NEW_VERIFIED | NEW_UNVERIFIED:
            self.assertNotIn(self.events[ref]["sport"].lower(), excluded, ref)

    def test_release_refreshes_are_fresh_and_exact(self):
        # NHL API re-read at 21:30Z for four of tonight's games
        for eid in ("199936", "199937", "199942", "199932"):
            self.assertEqual(self.rc[eid]["kind"], "exact", eid)
            self.assertEqual(self.rc[eid]["checked_at"], "2026-10-22T22:10:00Z", eid)
            self.assertEqual(self.rc[eid]["source"], "https://api-web.nhle.com/v1/schedule/2026-10-22", eid)
        # MLB World Series Game 1 re-read on mlb.com on 22 Oct, then re-observed on the MLB schedule
        # service at 2026-10-23T16:45Z, which states the UTC start directly.
        self.assertEqual(self.rc["160789"]["checked_at"], "2026-10-23T16:45:00Z")
        self.assertEqual(self.rc["160789"]["date"], "2026-10-24")
        self.assertEqual(self.rc["160789"]["time"], "00:00")
        self.assertEqual(self.rc["160789"]["timezone"], "UTC")
        self.assertTrue(self.rc["160789"]["source"].startswith("https://statsapi.mlb.com/"))
        # SuperLega UTC clocks re-read on VolleyballWorld
        for eid in ("36997", "36995", "36996"):
            self.assertEqual(self.rc[eid]["checked_at"], "2026-10-22T22:10:00Z", eid)
            self.assertEqual(self.rc[eid]["timezone"], "UTC", eid)
        # WTA OPs print no timezone -> never exact, never eligible
        for eid in ("902118", "902140", "902143", "902138"):
            self.assertIsNone(self.rc[eid]["timezone"], eid)
            self.assertIn(self.rc[eid]["kind"], {"not_before", "followed_by"}, eid)

    def test_new_written_pieces_meet_the_brief(self):
        for ref in ("TEN-47", "TEN-42", "CRK-17", "DRT-10", "DRT-09"):
            piece = self.preds[ref]
            self.assertGreaterEqual(len(piece["body"].split()), 30, ref)
            self.assertIn("to win", piece["selection"], ref)
            self.assertTrue(piece["sources"], ref)
            # non-HIGH pieces must be labelled analysis by the build
            self.assertEqual(piece["status"], "analysis", ref)

    def test_every_live_high_is_in_band_and_written(self):
        rows = list(self.events.values()) + list(self.gap.values())
        highs = [r for r in rows if r["pick"]["confidence"] == "HIGH"]
        self.assertTrue(highs)
        for r in highs:
            self.assertGreaterEqual(r["pick"]["price"], 1.40, r["ref"])
            self.assertLessEqual(r["pick"]["price"], 101.00, r["ref"])
            self.assertLess(r["pick"]["prob"], 0.70, r["ref"])
            self.assertEqual(r["pick"]["release"]["status"], "upcoming", r["ref"])
            self.assertEqual(self.preds[r["ref"]]["status"], "high", r["ref"])
            self.assertGreaterEqual(len(self.preds[r["ref"]]["body"].split()), 30, r["ref"])


if __name__ == "__main__":
    unittest.main()
