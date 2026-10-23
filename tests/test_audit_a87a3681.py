"""Pins for session-a87a3681: late-evening 2026-10-23 coverage pass.

Each assertion is derived from a page read in that pass, not from the prose it checks.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

NEW = ["BKB-536035", "BKB-536036", "BKB-536037", "BKB-536034", "BKB-536038",
       "ICH-199984", "ICH-199985"]


class NewPieces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pieces = {p["match_id"]: p for p in json.loads((DATA / "predictions-olbg.json").read_text())["predictions"]}

    def test_new_pieces_are_published_as_high_with_sources(self):
        for mid in NEW:
            self.assertIn(mid, self.pieces, mid)
            piece = self.pieces[mid]
            self.assertEqual(piece["confidence"], "high", mid)
            self.assertGreaterEqual(len(piece["text"].split()), 30, mid)
            self.assertTrue(piece["sources"], mid)
            for source in piece["sources"]:
                self.assertTrue(source["url"].startswith("https://"), mid)

    def test_new_pieces_are_not_repetitive(self):
        bodies = [self.pieces[m]["text"] for m in NEW]
        self.assertEqual(len(set(bodies)), len(bodies))

    def test_published_prose_never_uses_internal_vocabulary(self):
        banned = re.compile(r"\b(model|verified)\b", re.I)
        for mid in NEW + ["GFA-3530", "RGU-609576", "RGU-609578", "RGU-609580", "BKB-534841"]:
            self.assertIsNone(banned.search(self.pieces[mid]["text"]), mid)


class Repairs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pieces = {p["match_id"]: p for p in json.loads((DATA / "predictions-olbg.json").read_text())["predictions"]}

    def test_cork_piece_does_not_restate_unprinted_figures(self):
        text = self.pieces["GFA-3530"]["text"]
        self.assertNotIn("4-23", text)          # Carbery scoreline is not on gaacork.ie
        self.assertNotIn("+31", text)           # nor is the five-game aggregate
        self.assertIn("2-12", text)             # printed semi-final
        self.assertIn("1-15", text)             # printed Nemo semi-final

    def test_leinster_venue_is_not_invented(self):
        text = self.pieces["RGU-609578"]["text"]
        self.assertNotIn("Aviva", text)
        self.assertIn("TBC", text)
        self.assertIn("18.00", text)

    def test_nba_player_lines_removed(self):
        text = self.pieces["BKB-534841"]["text"]
        self.assertNotIn("Durant", text)
        self.assertNotIn("Castle", text)


class Clocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev = json.loads((DATA / "release_checks.json").read_text())["events"]

    def test_nba_slate_is_carried_with_an_explicit_et_label(self):
        for eid in ("536035", "536036", "536037", "534842", "536034", "536038", "534841",
                    "536040", "536039", "536042", "536043", "536041"):
            self.assertEqual(self.ev[eid]["timezone"], "ET", eid)
            self.assertEqual(self.ev[eid]["source"], "https://www.nba.com/schedule?date=2026-10-23", eid)

    def test_urc_round_four_uses_irish_time(self):
        for eid, time in (("609576", "12:45"), ("609580", "15:00"), ("609578", "18:00")):
            self.assertEqual(self.ev[eid]["timezone"], "Irish time", eid)
            self.assertEqual(self.ev[eid]["time"], time, eid)
            self.assertEqual(self.ev[eid]["date"], "2026-10-24", eid)

    def test_volleyball_inconsistency_is_recorded_not_hidden(self):
        self.assertEqual(self.ev["36994"]["timezone"], "UTC")
        self.assertIn("inconsistent", self.ev["36994"]["note"])


class Register(unittest.TestCase):
    def test_session_flags_are_published(self):
        items = json.loads((DATA / "flagged.json").read_text())["items"]
        ids = {i["id"] for i in items}
        for n in range(177, 184):
            self.assertIn(f"FL-{n}", ids)


class Band(unittest.TestCase):
    def test_every_high_row_stays_inside_the_odds_window(self):
        rows = json.loads((DATA / "lines.json").read_text())
        rows = rows if isinstance(rows, list) else rows["lines"]
        for row in rows:
            if row["confidence"] != "high":
                continue
            self.assertGreaterEqual(row["our_price_pick"], 1.40, row["match_id"])
            self.assertLessEqual(row["our_price_pick"], 101.0, row["match_id"])
            self.assertLess(row["our_pick_probability"], 0.70, row["match_id"])


if __name__ == "__main__":
    unittest.main()
