#!/usr/bin/env python3
"""Unit tests for the -250..+10000 price band and the board invariants that enforce it."""
import json
import datetime as dt
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import board_dates as bd  # noqa: E402


class TestConversion(unittest.TestCase):
    def test_band_edges(self):
        self.assertEqual(bd.american(1.40), -250)
        self.assertEqual(bd.american(101.0), 10000)
        self.assertTrue(bd.in_band(1.40))
        self.assertTrue(bd.in_band(101.0))
        self.assertFalse(bd.in_band(1.39))
        self.assertFalse(bd.in_band(101.5))
        self.assertFalse(bd.in_band(None))
        self.assertFalse(bd.in_band(0))

    def test_known_prices(self):
        self.assertEqual(bd.american(2.00), 100)
        self.assertEqual(bd.american(1.50), -200)
        self.assertEqual(bd.american(1.67), -149)
        self.assertEqual(bd.american(1.42), -238)
        self.assertEqual(bd.american(5.00), 400)
        self.assertIsNone(bd.american(1.0))

    def test_round_trip_within_a_point(self):
        for dec in (1.4, 1.55, 1.91, 2.5, 3.62, 12.0, 51.0, 101.0):
            us = bd.american(dec)
            back = 1 + 100.0 / abs(us) if us < 0 else 1 + us / 100.0
            self.assertAlmostEqual(back, dec, places=2)


class TestDates(unittest.TestCase):
    def test_relative_labels(self):
        self.assertEqual(bd.resolve_start("Today 19:10")[0], "2026-10-21")
        self.assertEqual(bd.resolve_start("Tomorrow 03:00")[0], "2026-10-22")

    def test_dated_labels(self):
        self.assertEqual(bd.resolve_start("23 Oct 12:00")[0], "2026-10-23")
        self.assertEqual(bd.resolve_start("27 May 2027 06:00")[0], "2027-05-27")
        # a month already passed in the capture year means the next year
        self.assertEqual(bd.resolve_start("06 Mar 09:00")[0], "2027-03-06")

    def test_unknown(self):
        iso, why = bd.resolve_start("Saturday evening")
        self.assertIsNone(iso)
        self.assertIn("unrecognised", why)

    def test_expiry(self):
        self.assertTrue(bd.expired("2026-10-21", dt.date(2026, 10, 22)))
        self.assertFalse(bd.expired("2026-10-23", dt.date(2026, 10, 22)))
        self.assertFalse(bd.expired(None))


class TestPublishedBoard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8") as f:
            cls.events = json.load(f)["events"]
        with open(os.path.join(ROOT, "data", "gap_sports.json"), encoding="utf-8") as f:
            cls.gap = json.load(f)["rows"]
        with open(os.path.join(ROOT, "data", "predictions.json"), encoding="utf-8") as f:
            cls.preds = {p["ref"]: p for p in json.load(f)["predictions"]}

    def test_every_high_pick_is_in_the_band_and_live(self):
        highs = [r for r in self.events + self.gap if r["pick"]["confidence"] == "HIGH"]
        self.assertGreater(len(highs), 0)
        for r in highs:
            pk = r["pick"]
            self.assertTrue(bd.in_band(pk["price"]), f"{r['ref']} price {pk['price']} outside band")
            self.assertFalse(pk.get("kickoff_passed"), f"{r['ref']} kick-off has passed")
            self.assertEqual(pk["american"], bd.american(pk["price"]), r["ref"])

    def test_every_high_has_a_prediction(self):
        highs = [r["ref"] for r in self.events + self.gap if r["pick"]["confidence"] == "HIGH"]
        for ref in highs:
            self.assertIn(ref, self.preds)
            p = self.preds[ref]
            self.assertEqual(p["status"], "high")
            self.assertGreaterEqual(len(p["body"].split()), 30, ref)
            self.assertTrue(p["sources"], ref)
            self.assertTrue(all(s["url"].startswith("http") for s in p["sources"]), ref)

    def test_non_high_pieces_are_analysis(self):
        conf = {r["ref"]: r["pick"]["confidence"] for r in self.events + self.gap}
        for ref, p in self.preds.items():
            if conf.get(ref) != "HIGH":
                self.assertEqual(p["status"], "analysis", ref)


if __name__ == "__main__":
    unittest.main()
