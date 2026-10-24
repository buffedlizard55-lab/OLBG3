"""Integration pins for session-58ac0957's independent written-pick audit."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_prediction_quality as quality  # noqa: E402

PROBE = ROOT / "data" / "raw" / "probe-58ac0957"
BASELINE_OLBG_HIGH = {
    "GFA-3530", "MTR-913", "VOL-36997", "VOL-36995", "VOL-36996",
    "HAN-12130", "HAN-12138", "HAN-12134", "HAN-12129", "HAN-12133",
    "RGU-609581",
}


class WrittenPickAuditIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = quality.run_quality_gate(ROOT)
        cls.review = json.loads((PROBE / "source-review.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads(
            (PROBE / "prediction-quality-manifest.json").read_text(encoding="utf-8")
        )

    def test_current_combined_inputs_pass_the_independent_gate(self):
        self.assertEqual(self.report.errors, [], self.report.errors)
        high_entries = [entry for entry in self.report.manifest["picks"] if entry["status"] == "high"]
        self.assertTrue(high_entries)
        for entry in high_entries:
            self.assertEqual(entry["selection_body_agreement"], "pass", entry["id"])
            self.assertEqual(entry["official_source_diversity"], "pass", entry["id"])
            self.assertEqual(entry["prohibited_terms"], [], entry["id"])

    def test_existing_site_checker_invokes_the_gate_and_propagates_errors(self):
        source = (ROOT / "tools" / "check_site.py").read_text(encoding="utf-8")
        self.assertIn("from check_prediction_quality import run_quality_gate", source)
        self.assertIn("quality = run_quality_gate(ROOT)", source)
        self.assertIn("errors.extend(quality.errors)", source)

    def test_manual_receipts_cover_the_claimed_baseline_high_set(self):
        picks = {entry["id"]: entry for entry in self.review["picks"]}
        self.assertTrue(BASELINE_OLBG_HIGH.issubset(picks))
        source_ids = {source["id"] for source in self.review["sources"]}
        for pick_id in BASELINE_OLBG_HIGH:
            self.assertTrue(picks[pick_id]["sources_read"], pick_id)
            self.assertTrue(set(picks[pick_id]["sources_read"]).issubset(source_ids), pick_id)
            self.assertTrue(picks[pick_id]["finding"], pick_id)

    def test_two_contradictions_have_direct_official_match_receipts(self):
        picks = {entry["id"]: entry for entry in self.review["picks"]}
        contradicted = {
            pick_id for pick_id in BASELINE_OLBG_HIGH
            if picks[pick_id]["status"] == "contradicted_high"
        }
        self.assertEqual(contradicted, {"HAN-12134", "HAN-12133"})
        self.assertIn("EHF-AAL-PSG", picks["HAN-12134"]["sources_read"])
        self.assertIn("EHF-DIN-MON", picks["HAN-12133"]["sources_read"])
        sources = {source["id"]: source for source in self.review["sources"]}
        self.assertIn("33:33", " ".join(sources["EHF-AAL-PSG"]["confirmed"]))
        self.assertIn("23:27", " ".join(sources["EHF-DIN-MON"]["confirmed"]))
        for source_id in ("EHF-AAL-PSG", "EHF-DIN-MON"):
            self.assertTrue(sources[source_id]["url"].startswith("https://ehfcl.eurohandball.com/"))

    def test_correction_handoff_is_recorded_without_claiming_a_prediction_edit(self):
        handoff = self.review["handoff"]
        self.assertEqual(handoff["pr"], 169)
        self.assertIn("pull/169#issuecomment-", handoff["comment_url"])
        self.assertIn("did not edit", handoff["reason"])

    def test_committed_manifest_is_deterministic_and_internally_complete(self):
        self.assertNotIn("generated_at", self.manifest)
        counts = self.manifest["counts"]
        self.assertEqual(counts["predictions"], len(self.manifest["picks"]))
        self.assertEqual(counts["high"], sum(entry["status"] == "high" for entry in self.manifest["picks"]))
        self.assertEqual(
            counts["analysis"], sum(entry["status"] == "analysis" for entry in self.manifest["picks"])
        )
        required = {
            "track", "id", "status", "word_count", "body_sha256",
            "selection_body_agreement", "prohibited_terms", "official_document_urls",
            "official_source_diversity", "near_duplicates",
        }
        for entry in self.manifest["picks"]:
            self.assertTrue(required.issubset(entry), entry.get("id"))
            self.assertEqual(len(entry["body_sha256"]), 64, entry["id"])

    def test_gate_is_read_only_over_prediction_inputs(self):
        paths = [ROOT / "data" / "predictions.json", ROOT / "data" / "predictions-olbg.json"]
        before = [path.read_bytes() for path in paths]
        quality.run_quality_gate(ROOT)
        self.assertEqual(before, [path.read_bytes() for path in paths])


if __name__ == "__main__":
    unittest.main()
