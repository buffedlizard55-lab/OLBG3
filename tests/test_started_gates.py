#!/usr/bin/env python3
"""Regression tests for exact same-day/tournament-start HIGH-pick gates."""
import datetime as dt
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import board_dates as bd  # noqa: E402
import check_board  # noqa: E402
import originate  # noqa: E402


UTC = dt.timezone.utc


def moment(value):
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)


class TestMatchClock(unittest.TestCase):
    def test_same_day_started_uses_capture_date_not_legacy_default(self):
        row = {
            "date_iso": "2026-10-22",
            "olbg_date_label": "Today",
            "olbg_time_label": "03:00",
            "fetched_at": "2026-10-22T07:25:00Z",
        }
        start, started, _ = originate.match_clock(row, moment("2026-10-22T07:35Z"))
        self.assertEqual(start, "2026-10-22T07:00Z")
        self.assertTrue(started)

    def test_same_day_future_start_remains_eligible(self):
        row = {
            "date_iso": "2026-10-22",
            "olbg_date_label": "Today",
            "olbg_time_label": "04:00",
            "fetched_at": "2026-10-22T07:25:00Z",
        }
        start, started, _ = originate.match_clock(row, moment("2026-10-22T07:35Z"))
        self.assertEqual(start, "2026-10-22T08:00Z")
        self.assertFalse(started)

    def test_official_tournament_start_overrides_settlement_label(self):
        row = {
            "date_iso": "2026-10-25",
            "olbg_date_label": "25 Oct",
            "olbg_time_label": "17:45",
            "fetched_at": "2026-10-22T08:30:00Z",
            "official_start_utc": "2026-10-22T10:35:00Z",
        }
        start, started, basis = originate.match_clock(row, moment("2026-10-22T11:00Z"))
        self.assertEqual(start, "2026-10-22T10:35:00Z")
        self.assertTrue(started)
        self.assertIn("official", basis)

    def test_unknown_same_day_clock_is_not_assumed_live(self):
        row = {
            "date_iso": "2026-10-22",
            "olbg_date_label": "Today",
            "olbg_time_label": "",
            "fetched_at": "2026-10-22T07:25:00Z",
        }
        start, started, _ = originate.match_clock(row, moment("2026-10-22T07:35Z"))
        self.assertIsNone(start)
        self.assertIsNone(started)


class TestStartedValidator(unittest.TestCase):
    def setUp(self):
        check_board.errors = []

    def tearDown(self):
        check_board.errors = []

    def test_root_validator_rejects_started_high_row(self):
        row = {
            "ref": "TEST-STARTED",
            "sport": "Tennis",
            "olbg_event_url": "https://www.olbg.com/betting-tips/Tennis/3?event_id=1",
            "verification": {
                "status": "verified",
                "official_url": "https://www.atptour.com/",
                "official_label": "ATP official schedule",
                "source_tier": "official",
            },
            "model": {"prices": {}},
            "pick": {
                "confidence": "HIGH",
                "price": 2.0,
                "american": 100,
                "kickoff_passed": False,
                "kickoff_started": True,
                "start_iso": "2026-10-22",
                "kickoff_utc": None,
            },
        }
        preds = {"TEST-STARTED": {"status": "high"}}
        check_board.check_rows([row], preds)
        self.assertTrue(any("same-day kick-off has started" in e for e in check_board.errors),
                        check_board.errors)


class TestPublishedOlbgClocks(unittest.TestCase):
    def test_high_rows_and_written_statuses_are_synchronized(self):
        with open(os.path.join(ROOT, "data", "lines.json"), encoding="utf-8") as f:
            lines = json.load(f)
        with open(os.path.join(ROOT, "data", "predictions-olbg.json"), encoding="utf-8") as f:
            preds = json.load(f)["predictions"]
        by_id = {row["match_id"]: row for row in lines}
        for row in lines:
            if row["confidence"] != "high":
                continue
            self.assertIs(row.get("kickoff_started"), False, row["match_id"])
            self.assertFalse(row.get("kickoff_passed"), row["match_id"])
            if row.get("start_utc"):
                start = dt.datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
                self.assertGreater(start, bd.snapshot_utc(), row["match_id"])
        for pred in preds:
            confidence = by_id[pred["match_id"]]["confidence"]
            self.assertEqual(pred.get("status"), "high" if confidence == "high" else "analysis",
                             pred["match_id"])


if __name__ == "__main__":
    unittest.main()
