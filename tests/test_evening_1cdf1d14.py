"""Regression tests for the session-1cdf1d14 evening pass (FL-127, FL-128, FL-069 resolved).

This pass runs on top of the parallel evening passes by session-cab97f19 (FL-099..FL-108) and
session-784afe97 (FL-109..FL-126), so it asserts only what this session changed: putting the
official EuroLeague standings table behind the FL-069 resolution that was already published on the
release records, and the downgrade-reason repair in scripts/release.py.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest
from archive_guard import pins  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))


@pins('olbg-harvest-20261022T2130Z.tsv')
class EveningRefresh1cdf1d14Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.events = {e["ref"]: e for e in json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]}
        cls.gap = {r["ref"]: r for r in json.loads((DATA / "gap_sports.json").read_text(encoding="utf-8"))["rows"]}
        cls.rc = json.loads((DATA / "release_checks.json").read_text(encoding="utf-8"))["events"]
        cls.official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))
        cls.flagged = {f["id"]: f for f in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]}

    # ---- FL-127: the model table now matches the FL-069 resolution ----

    def test_euroleague_table_is_the_full_post_round_seven_table(self) -> None:
        table = self.official["form_data"]["EuroLeague_2026_27_table"]
        self.assertNotIn("withheld_conflicting_rows", table)
        self.assertEqual(table["retrieved"], "2026-10-22T21:35:00Z")
        self.assertEqual(len(table["teams"]), 20)
        self.assertEqual(table["teams"]["Olympiacos Piraeus"],
                         {"pl": 6, "w": 5, "l": 1, "pf": 564, "pa": 524, "diff": 40})
        self.assertEqual(table["teams"]["Valencia Basket"],
                         {"pl": 6, "w": 4, "l": 2, "pf": 583, "pa": 537, "diff": 46})
        self.assertEqual(table["teams"]["Paris Basketball"],
                         {"pl": 6, "w": 1, "l": 5, "pf": 504, "pa": 545, "diff": -41})
        # the read is post-Round-7, so the clubs that played on 22 October carry seven games
        self.assertEqual(table["teams"]["Panathinaikos AKTOR Athens"]["pl"], 7)
        self.assertEqual(table["teams"]["Anadolu Efes Istanbul"],
                         {"pl": 7, "w": 3, "l": 4, "pf": 581, "pa": 590, "diff": -9})
        self.assertEqual(table["conflict_resolution"]["resolves"], "FL-069")
        self.assertEqual(self.flagged["FL-069"]["status"], "resolved")
        self.assertIn("FL-127", self.flagged)

    def test_the_two_released_rows_are_priced_from_official_form_not_tip_share(self) -> None:
        for ref, price, us, side, prob in (("BKB-29", 1.69, -145, "Olympiacos Piraeus", 0.5621),
                                           ("BKB-30", 1.53, -189, "Valencia Basket", 0.6223)):
            row = self.events[ref]
            self.assertEqual(row["model"]["basis"], "official-standings", ref)
            pick = row["pick"]
            self.assertEqual(pick["confidence"], "HIGH", ref)
            self.assertEqual(pick["price"], price, ref)
            self.assertEqual(pick["american"], us, ref)
            self.assertEqual(pick["label"], side, ref)
            self.assertAlmostEqual(pick["prob"], prob, places=3, msg=ref)
            self.assertTrue(1.40 <= price <= 101.0, ref)
            self.assertEqual(pick["factors"]["official_form"], 2, ref)
            piece = self.preds[ref]
            self.assertEqual(piece["status"], "high", ref)
            self.assertGreaterEqual(len(piece["body"].split()), 30, ref)
            self.assertTrue(any("standings" in s["url"] for s in piece["sources"]), ref)

    def test_basketball_publishes_three_live_high_picks(self) -> None:
        sports = [r["sport"] for r in self.events.values() if r["pick"]["confidence"] == "HIGH"]
        self.assertEqual(sports.count("Basketball"), 3)
        for ref in ("BKB-22", "BKB-29", "BKB-30"):
            self.assertEqual(self.events[ref]["pick"]["release"]["status"], "upcoming", ref)

    def test_repriced_started_euroleague_pieces_quote_the_current_price(self) -> None:
        for ref, price, us in (("BKB-20", 1.59, -169), ("BKB-21", 1.41, -244), ("BKB-26", 1.65, -154)):
            pick = self.events[ref]["pick"]
            self.assertEqual(pick["price"], price, ref)
            self.assertEqual(pick["american"], us, ref)
            self.assertEqual(pick["release"]["status"], "start_window_reached", ref)
            piece = self.preds[ref]
            self.assertEqual(piece["status"], "analysis", ref)
            self.assertIn(f"{price:.2f}", piece["selection"], ref)
            self.assertIn(str(us), piece["selection"], ref)
            self.assertGreaterEqual(len(piece["body"].split()), 30, ref)

    # ---- FL-128: the published downgrade reason must match the gate that actually blocked ----

    def test_sync_predictions_only_quotes_the_release_gate_when_it_blocked_the_row(self) -> None:
        from release import sync_predictions

        eligible = {"pick": {"release": {"eligible": True, "reason": "Official scheduled start is ahead of this build"}}}
        blocked = {"pick": {"release": {"eligible": False, "reason": "Official scheduled start has passed."}}}
        doc = {"predictions": [{"ref": "ELIG", "status": "high"}, {"ref": "BLOCK", "status": "high"}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            sync_predictions(path, {"ELIG": eligible, "BLOCK": blocked}, "ref", lambda row: "medium")
            out = {p["ref"]: p for p in json.loads(path.read_text(encoding="utf-8"))["predictions"]}
        self.assertEqual(out["ELIG"]["status"], "analysis")
        self.assertIn("Model grade or price-band gate", out["ELIG"]["downgrade_reason"])
        self.assertNotIn("ahead of this build", out["ELIG"]["downgrade_reason"])
        self.assertEqual(out["BLOCK"]["downgrade_reason"], "Official scheduled start has passed.")
        # a released HIGH piece must not carry a stale downgrade reason
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.json"
            path.write_text(json.dumps({"predictions": [{"ref": "ELIG", "status": "analysis",
                                                         "downgrade_reason": "stale"}]}), encoding="utf-8")
            sync_predictions(path, {"ELIG": eligible}, "ref", lambda row: "high")
            out = json.loads(path.read_text(encoding="utf-8"))["predictions"][0]
        self.assertEqual(out["status"], "high")
        self.assertNotIn("downgrade_reason", out)
        self.assertIn("FL-128", self.flagged)

    def test_no_published_piece_contradicts_its_own_release_status(self) -> None:
        for ref, piece in self.preds.items():
            if piece["status"] != "analysis":
                continue
            row = self.events.get(ref) or self.gap.get(ref)
            if not row:
                continue
            release = (row.get("pick") or {}).get("release") or {}
            if release.get("eligible"):
                self.assertNotIn("ahead of this build", piece.get("downgrade_reason", ""), ref)


if __name__ == "__main__":
    unittest.main()
