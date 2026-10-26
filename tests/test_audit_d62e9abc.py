"""session-d62e9abc: 15-sport line origination, written-pick & official-source verification regressions."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_links  # noqa: E402


class AuditD62e9abcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/audit_d62e9abc.py")],
            check=True,
            capture_output=True,
        )
        cls.audit = json.loads((ROOT / "data/audit-d62e9abc.json").read_text(encoding="utf-8"))
        cls.page = (ROOT / "audit-d62e9abc.html").read_text(encoding="utf-8")

    def test_covers_all_15_in_scope_sports_with_zero_excluded_leaks(self) -> None:
        self.assertEqual(self.audit["counts"]["in_scope_sports"], 15)
        self.assertEqual(len(self.audit["per_sport"]), 15)
        self.assertEqual(self.audit["counts"]["excluded_sport_leaks"], 0)

    def test_line_origination_and_source_integrity(self) -> None:
        c = self.audit["counts"]
        self.assertEqual(c["arithmetic_failures"], 0)
        self.assertEqual(c["missing_olbg_links"], 0)
        self.assertEqual(c["unverified_value_leaks"], 0)
        self.assertGreaterEqual(c["olbg_track_rows"], 523)
        self.assertGreaterEqual(c["root_track_rows"], 367)
        self.assertGreaterEqual(c["olbg_priced_rows"], 520)
        self.assertGreaterEqual(c["olbg_handicap_rows"], 340)
        self.assertGreaterEqual(c["olbg_total_rows"], 360)

    def test_written_predictions_pass_quality_gates(self) -> None:
        c = self.audit["counts"]
        self.assertGreaterEqual(c["written_predictions_total"], 154)
        self.assertEqual(c["predictions_under_30_words"], 0)
        self.assertEqual(c["predictions_with_banned_words"], 0)
        self.assertEqual(c["predictions_missing_https_sources"], 0)
        dups = [p for p in self.audit["prediction_checks"] if p.get("duplicate_of")]
        self.assertEqual(dups, [])

    def test_any_live_high_pick_is_in_band_and_under_chalk_cap(self) -> None:
        for p in self.audit["live_high_picks"]:
            self.assertEqual(p["status"], "high")
            self.assertEqual(p["release_status"], "upcoming")
            us_odds = int(str(p["our_us_odds_pick"]).replace("+", "").strip())
            self.assertTrue(-250 <= us_odds <= 10000, p["id"])
            self.assertLess(p["our_pick_probability"], 0.70, p["id"])
            self.assertGreaterEqual(p["word_count"], 30, p["id"])
            self.assertEqual(p["banned_words"], [], p["id"])
            self.assertTrue(p["https_sources_ok"], p["id"])

    def test_official_nhl_and_ehf_pdf_cross_verifications(self) -> None:
        nhl = self.audit["oct26_nhl_verifications"]
        self.assertGreaterEqual(len(nhl), 1)
        by_id = {r["match_id"]: r for r in nhl}
        if "ICH-200101" in by_id:
            self.assertEqual(by_id["ICH-200101"]["official_start_utc"], "2026-10-26T23:00:00Z")
            self.assertEqual(by_id["ICH-200101"]["home_split"], "6-0-0")
        if "ICH-200102" in by_id:
            self.assertEqual(by_id["ICH-200102"]["official_start_utc"], "2026-10-27T01:30:00Z")
            self.assertEqual(by_id["ICH-200102"]["home_record"], "8-2-1")

        ehf = self.audit["ehf_pdf_round6_verification"]
        self.assertTrue(ehf["verified"])
        self.assertEqual(len(ehf["fixtures"]), 12)
        self.assertTrue(all(f["present_in_pdf_stream"] for f in ehf["fixtures"]))

    def test_standalone_dashboard_sections_and_zero_broken_links(self) -> None:
        for section_id in (
            'id="exec-summary"',
            'id="sport-categories"',
            'id="official-cross-check"',
            'id="outright-race-markets"',
            'id="all-written-predictions"',
            'id="all-lines-by-sport"',
            'id="flagged-review"',
        ):
            self.assertIn(section_id, self.page)
        _, checked, errors = check_links.check_tree(ROOT)
        tracked_errors = [e for e in errors if not e[0].startswith("site/")]
        self.assertGreaterEqual(checked, 1000)
        self.assertEqual(tracked_errors, [])


if __name__ == "__main__":
    unittest.main()
