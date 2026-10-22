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


class TestPublishedSourceCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(name):
            with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
                return json.load(f)
        cls.matches = {row["id"]: row for row in load("matches.json")}
        cls.lines = {row["match_id"]: row for row in load("lines.json")}
        cls.events = {row["ref"]: row for row in load("events.json")["events"]}
        cls.gap = {row["ref"]: row for row in load("gap_sports.json")["rows"]}
        cls.verifications = load("verifications.json")["event_verifications"]
        cls.preds = {row["match_id"]: row for row in load("predictions-olbg.json")["predictions"]}

    def test_italian_ids_and_evidence_stay_with_fixture(self):
        expected = {
            "VOL-36994": ("Trentino vs Cisterna", "Itas Trentino"),
            "VOL-36995": ("Civitanova vs Padova", "Cucine Lube Civitanova"),
            "VOL-36996": ("Monza vs Verona", "Vero Volley Monza"),
            "VOL-36997": ("Perugia vs Pordenone", "Sir Susa Scai Perugia"),
        }
        for mid, (event_name, fact_name) in expected.items():
            self.assertEqual(self.matches[mid]["event_name"], event_name)
            facts = " ".join(self.verifications[mid.split("-")[1]]["facts"])
            self.assertIn(fact_name, facts, mid)
        for mid, name in (("VOL-36995", "Cucine Lube Civitanova"),
                          ("VOL-36996", "Vero Volley Monza"),
                          ("VOL-36997", "Sir Susa Scai Perugia")):
            self.assertIn(name, self.preds[mid]["selection"])
            self.assertEqual(self.preds[mid]["status"], "high")

    def test_brazilian_official_order_and_source_slug_are_both_preserved(self):
        row = self.matches["VOL-37000"]
        self.assertEqual(row["event_name"], "Gerdau Minas vs Paulistano Barueri")
        self.assertEqual(row["home"], "Gerdau Minas")
        self.assertEqual(row["olbg_event_name"], "Paulistano-Barueri W vs Minas W")
        self.assertIn("Paulistano-Barueri_W_vs_Minas_W", row["olbg_url"])
        self.assertEqual(row["official_start_utc"], "2026-10-23T21:30:00Z")

    def test_set_score_consensus_does_not_become_winner_probability(self):
        for ref in ("TEN-06", "TEN-29", "VOL-23", "VOL-25"):
            self.assertEqual(self.events[ref]["model"]["prices"], {}, ref)
            self.assertIsNone(self.events[ref]["pick"]["price"], ref)
        for mid in ("VOL-37000", "VOL-37002"):
            row = self.lines[mid]
            self.assertIn("non_win_consensus_excluded_from_winner_probability", row["flags"], mid)
            self.assertIn("non-winner OLBG consensus excluded", row["inputs"]["basis"], mid)

    def test_no_non_winner_market_uses_tip_share_as_winner_consensus(self):
        non_winner = {
            "Set Score", "Set Betting", "Handicap", "Handicap 2-way", "Match Handicap",
            "Pointspread", "Puck Line", "Total Legs", "Game Totals", "Games Won", "1st Set Winner",
        }
        for row in self.events.values():
            if row["olbg_market"] in non_winner:
                self.assertNotEqual(row["model"]["basis"], "consensus", row["ref"])
        for row in self.lines.values():
            if row["inputs"]["olbg_market"] in non_winner:
                self.assertFalse(row["inputs"]["basis"].startswith("OLBG tip split"), row["match_id"])

    def test_bermuda_uses_official_first_tee_on_both_tracks(self):
        expected = "2026-10-22T10:35:00Z"
        self.assertEqual(self.lines["GLF-101904"]["start_utc"], expected)
        self.assertEqual(self.gap["GLF-02"]["pick"]["kickoff_utc"], "2026-10-22T10:35Z")
        self.assertIn("pgatour.com", self.gap["GLF-02"]["pick"]["official_start_url"])
        self.assertFalse(self.lines["GLF-101904"]["kickoff_started"])
        self.assertFalse(self.gap["GLF-02"]["pick"]["kickoff_started"])


if __name__ == "__main__":
    unittest.main()
