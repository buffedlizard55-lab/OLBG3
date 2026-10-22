"""Regression tests for the 2026-10-22T08:29Z evidence/freshness integration."""
import json
import os
import sys
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_board import selection_matches  # noqa: E402


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class FieldProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gap = {r["ref"]: r for r in load("gap_sports.json")["rows"]}
        cls.lines = {r["match_id"]: r for r in load("lines.json")}

    def test_every_root_field_has_independent_status(self):
        for ref, row in self.gap.items():
            prior = row["model"]["prior"]
            self.assertIn(prior["field_size_status"], {"official", "model_input", "competition_format"}, ref)
            if prior["field_size_status"] == "official":
                self.assertTrue(prior["field_size_source"].startswith("https://"), ref)
                self.assertIn(prior["field_size_source_tier"], {"official", "club-official"}, ref)
            elif prior["field_size_status"] == "model_input":
                self.assertEqual(prior["field_size_source"], "", ref)

    def test_fixture_verification_does_not_verify_field_size(self):
        for ref, field in (("GLF-02", 120), ("GLF-04", 78), ("MTR-03", 21)):
            prior = self.gap[ref]["model"]["prior"]
            self.assertEqual(self.gap[ref]["verification"]["status"], "verified")
            self.assertEqual(prior["field"], field)
            self.assertEqual(prior["field_size_status"], "model_input")
        fortinet = self.gap["GLF-07"]["model"]["prior"]
        self.assertEqual(fortinet["field"], 96)
        self.assertEqual(fortinet["field_size_status"], "official")
        self.assertEqual(fortinet["field_size_source"], "https://www.jgto.org/en/tournament/3048/player")

    def test_olbg_track_uses_the_same_jgto_field_evidence(self):
        fortinet = self.lines["GLF-101908"]["inputs"]
        self.assertEqual((fortinet["field_size"], fortinet["field_size_status"]), (96, "official"))
        bermuda = self.lines["GLF-101904"]["inputs"]
        self.assertEqual((bermuda["field_size"], bermuda["field_size_status"]), (120, "model_input"))
        self.assertEqual(bermuda["field_size_source"], "")


class IntegrationFreshness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = {r["ref"]: r for r in load("events.json")["events"]}
        cls.matches = {r["id"]: r for r in load("matches.json")}
        cls.lines = {r["match_id"]: r for r in load("lines.json")}

    def test_exact_verified_aliases_restore_prices(self):
        for ref in ("BKB-19", "HBL-19", "GAF-02"):
            self.assertTrue(self.events[ref]["model"]["prices"], ref)

    def test_official_kbl_start_overrides_conflicting_raw_date_for_freshness(self):
        match = self.matches["BKB-536021"]
        self.assertEqual(match["date_iso"], "2026-10-23")  # raw OLBG Tomorrow label, retained
        self.assertEqual(match["official_start_utc"], "2026-10-22T10:00:00Z")
        self.assertEqual(self.lines["BKB-536021"]["start"], "2026-10-22")
        self.assertEqual(self.events["BKB-23"]["pick"]["kickoff_utc"], "2026-10-22T10:00:00Z")

    def test_no_started_row_remains_high(self):
        for row in self.events.values():
            if row["pick"]["confidence"] == "HIGH":
                self.assertFalse(row["pick"].get("kickoff_started"), row["ref"])
        for row in self.lines.values():
            if row.get("kickoff_utc"):
                self.assertTrue(row.get("kickoff_basis"), row["match_id"])
            if row["confidence"] == "high":
                self.assertFalse(row.get("kickoff_started"), row["match_id"])

    def test_osaka_correction_preserves_raw_label_and_flag(self):
        self.assertEqual(self.events["TEN-37"]["competition"], "WTA 250 Kinoshita Group Japan Open (Osaka)")
        self.assertEqual(self.matches["TEN-902107"]["olbg_league_label"], "WTA Guangzhou Open")
        flags = load("flagged.json")["items"]
        self.assertIn("FL-067", {item["id"] for item in flags})

    def test_derived_olbg_clock_also_expires_at_a_later_snapshot(self):
        from tools.originate import event_clock
        row = {"date_iso": "2026-10-22", "olbg_date_label": "Today", "olbg_time_label": "08:00"}
        with mock.patch.dict(os.environ, {"OLBG_NOW_UTC": "2026-10-22T11:59Z"}):
            before = event_clock(row)
        with mock.patch.dict(os.environ, {"OLBG_NOW_UTC": "2026-10-22T12:00Z"}):
            started = event_clock(row)
        self.assertEqual(before["kickoff_utc"], "2026-10-22T12:00Z")
        self.assertFalse(before["started"])
        self.assertTrue(started["started"])
        self.assertIn("derived", started["kickoff_basis"])


class PredictionIdentity(unittest.TestCase):
    def test_written_selection_matches_its_originated_row(self):
        rows = {r["ref"]: r for r in load("events.json")["events"]}
        rows.update({r["ref"]: r for r in load("gap_sports.json")["rows"]})
        for pred in load("predictions.json")["predictions"]:
            self.assertTrue(selection_matches(rows[pred["ref"]]["pick"]["label"], pred["selection"]), pred["ref"])
        lines = {r["match_id"]: r for r in load("lines.json")}
        for pred in load("predictions-olbg.json")["predictions"]:
            self.assertIn(lines[pred["match_id"]]["our_pick"].lower(), pred["selection"].lower(), pred["match_id"])


if __name__ == "__main__":
    unittest.main()
