import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from board_dates import (resolve_start, american, in_band, expired,
                         BAND_LOW_DEC, BAND_HIGH_DEC)


class BandMaths(unittest.TestCase):
    def test_band_edges(self):
        self.assertTrue(in_band(1.40))       # -250
        self.assertTrue(in_band(101.0))      # +10000
        self.assertFalse(in_band(1.39))
        self.assertFalse(in_band(101.01))
        self.assertFalse(in_band(None))

    def test_american(self):
        self.assertEqual(american(1.40), -250)
        self.assertEqual(american(101.0), 10000)
        self.assertEqual(american(2.00), 100)
        self.assertEqual(american(1.07), -1429)
        self.assertEqual(american(1.46), -217)
        self.assertIsNone(american(None))

    def test_decimal_price_round_trip(self):
        # every published row's US odds must be the arithmetic conversion of its decimal price
        rows = json.load(open(ROOT / "data/events.json"))["events"]
        rows += json.load(open(ROOT / "data/gap_sports.json"))["rows"]
        for r in rows:
            pk = r["pick"]
            if pk.get("price") is None:
                continue
            self.assertEqual(pk["american"], american(pk["price"]), r["ref"])
            self.assertEqual(pk["in_band"], in_band(pk["price"]), r["ref"])


class ClockLabels(unittest.TestCase):
    def test_relative(self):
        self.assertEqual(resolve_start("Today 19:10")[0], "2026-10-21")
        self.assertEqual(resolve_start("Tomorrow 03:00")[0], "2026-10-22")

    def test_dated(self):
        self.assertEqual(resolve_start("23 Oct 12:00")[0], "2026-10-23")
        self.assertEqual(resolve_start("06 Dec 08:00")[0], "2026-12-06")
        self.assertEqual(resolve_start("27 May 2027 06:00")[0], "2027-05-27")

    def test_unrecognised_is_blank(self):
        self.assertIsNone(resolve_start("sometime next week")[0])

    def test_expired(self):
        self.assertTrue(expired("2026-10-21"))
        self.assertFalse(expired("2026-10-22"))
        self.assertFalse(expired(None))


class PublishedBoard(unittest.TestCase):
    def setUp(self):
        self.rows = json.load(open(ROOT / "data/events.json"))["events"]
        self.rows += json.load(open(ROOT / "data/gap_sports.json"))["rows"]
        self.preds = {p["ref"]: p for p in
                      json.load(open(ROOT / "data/predictions.json"))["predictions"]}

    def test_every_high_pick_is_in_band_and_live(self):
        highs = [r for r in self.rows if r["pick"]["confidence"] == "HIGH"]
        self.assertTrue(highs, "no high-confidence picks published")
        for r in highs:
            pk = r["pick"]
            self.assertTrue(pk["in_band"], r["ref"])
            self.assertGreaterEqual(pk["price"], BAND_LOW_DEC)
            self.assertLessEqual(pk["price"], BAND_HIGH_DEC)
            self.assertFalse(pk["kickoff_passed"], r["ref"])

    def test_every_high_has_a_high_prediction(self):
        for r in self.rows:
            if r["pick"]["confidence"] != "HIGH":
                continue
            self.assertIn(r["ref"], self.preds)
            self.assertEqual(self.preds[r["ref"]]["status"], "high")
            self.assertGreaterEqual(len(self.preds[r["ref"]]["body"].split()), 30)

    def test_non_high_pieces_are_labelled_analysis(self):
        for ref, p in self.preds.items():
            row = next((r for r in self.rows if r["ref"] == ref), None)
            self.assertIsNotNone(row, ref)
            if row["pick"]["confidence"] != "HIGH":
                self.assertEqual(p["status"], "analysis", ref)

    def test_no_prediction_is_a_high_confidence_claim_on_a_medium_row(self):
        for ref, p in self.preds.items():
            row = next((r for r in self.rows if r["ref"] == ref), None)
            if row["pick"]["confidence"] == "MEDIUM":
                self.assertNotEqual(p["status"], "high", ref)


if __name__ == "__main__":
    unittest.main()
