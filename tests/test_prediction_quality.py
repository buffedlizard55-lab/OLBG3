"""Unit tests for the independent two-track written-pick quality gate."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_prediction_quality as quality  # noqa: E402


BODY = (
    "Back Alpha Team to win after their disciplined defensive display and efficient transition "
    "attack in the latest officially documented fixture. Beta Team remain dangerous on the road, "
    "but Alpha's healthier rotation, stronger recent shot selection and home-court consistency "
    "make the hosts the clear selection for this upcoming contest at the listed price."
)


def prediction(**changes):
    value = {
        "ref": "R-1",
        "selection": "Alpha Team to win at 1.50 (-200)",
        "headline": "Alpha's defensive balance earns the lean",
        "body": BODY,
        "status": "high",
        "sources": [
            {"label": "Official fixture", "url": "https://official.example/fixtures"},
            {"label": "Official form", "url": "https://official.example/form"},
        ],
    }
    value.update(changes)
    return value


def olbg_prediction(**changes):
    value = {
        "match_id": "O-1",
        "selection": "Alpha Team Match Winner (1.50 / -200)",
        "text": BODY,
        "status": "high",
        "sources": [
            {"label": "Official fixture", "url": "https://official.example/fixtures-olbg"},
            {"label": "Official form", "url": "https://official.example/form-olbg"},
        ],
    }
    value.update(changes)
    return value


class RepositoryCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "data").mkdir()
        self.root_prediction = prediction()
        self.olbg_predictions = []
        self.root_row = {
            "ref": "R-1", "home": "Alpha Team", "away": "Beta Team",
            "pick": {"label": "Alpha Team"},
        }
        self.lines = []
        self._write()

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self):
        data = self.root / "data"
        documents = {
            "predictions.json": {"predictions": [self.root_prediction]},
            "predictions-olbg.json": {"predictions": self.olbg_predictions},
            "events.json": {"events": [self.root_row]},
            "gap_sports.json": {"rows": []},
            "lines.json": self.lines,
            "verifications.json": {
                "sources": [
                    {"class": "official", "url": "https://official.example/fixtures"},
                    {"class": "primary", "url": "https://official.example/form"},
                    {"class": "official", "url": "https://www.olbg.com/betting-tips"},
                ]
            },
        }
        for filename, document in documents.items():
            (data / filename).write_text(json.dumps(document), encoding="utf-8")

    def report(self):
        self._write()
        return quality.run_quality_gate(self.root)

    def add_olbg(self, prediction_value=None):
        value = prediction_value or olbg_prediction()
        self.olbg_predictions = [value]
        self.lines = [{
            "match_id": value["match_id"], "home": "Alpha Team", "away": "Beta Team",
            "our_pick": "Alpha Team",
        }]

    def test_valid_high_pick_passes_and_has_per_pick_manifest(self):
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)
        entry = report.manifest["picks"][0]
        self.assertEqual(entry["id"], "R-1")
        self.assertEqual(entry["selection_body_agreement"], "pass")
        self.assertEqual(entry["official_source_diversity"], "pass")
        self.assertEqual(entry["official_document_count"], 2)
        self.assertGreaterEqual(entry["word_count"], 30)
        self.assertEqual(entry["near_duplicates"], [])

    def test_selection_and_body_must_agree_with_actual_row_pick(self):
        self.root_row["pick"]["label"] = "Beta Team"
        report = self.report()
        self.assertTrue(any("selection does not agree" in error for error in report.errors))
        self.assertTrue(any("body does not explicitly endorse" in error for error in report.errors))

    def test_body_cannot_argue_for_the_opponent(self):
        self.root_prediction["body"] = BODY.replace("Back Alpha Team", "Back Beta Team")
        report = self.report()
        self.assertTrue(any("body does not explicitly endorse" in error for error in report.errors))

    def test_abbreviated_row_pick_accepts_full_name_alias(self):
        self.root_row["pick"]["label"] = "AT Alpha Team"
        self.root_prediction["body"] = BODY.replace("Back Alpha Team", "Back Alpha")
        # The selection still carries the full team name and agrees through Alpha/Team identity.
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)

    def test_high_cannot_publish_a_no_selection_placeholder(self):
        self.root_prediction["selection"] = "No selection published while evidence is reviewed"
        report = self.report()
        self.assertTrue(any("does not name a concrete row selection" in error for error in report.errors))

    def test_analysis_no_selection_is_not_a_high_selection_failure(self):
        self.root_prediction["status"] = "analysis"
        self.root_prediction["selection"] = "No selection published while evidence is reviewed"
        self.root_prediction["sources"] = []
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)

    def test_exact_prohibited_words_fail_in_all_prediction_prose(self):
        self.root_prediction["headline"] = "Verified team news supports Alpha"
        self.root_prediction["body"] = BODY + " The model is not mentioned as evidence."
        report = self.report()
        self.assertTrue(any("prohibited word 'model' in body" in error for error in report.errors))
        self.assertTrue(any("prohibited word 'verified' in headline" in error for error in report.errors))

    def test_longer_words_containing_prohibited_terms_are_not_false_positives(self):
        self.root_prediction["body"] = BODY + " Modelling notes and unverified items stay outside this piece."
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)

    def test_high_requires_two_distinct_official_documents_not_fragments(self):
        self.root_prediction["sources"] = [
            {"label": "Fixture section", "url": "https://official.example/fixtures#teams"},
            {"label": "Same fixture page", "url": "https://official.example/fixtures#form"},
            {"label": "Crowd listing", "url": "https://www.olbg.com/betting-tips/example"},
        ]
        report = self.report()
        self.assertTrue(any("has 1 distinct reviewed official document" in error for error in report.errors))

    def test_analysis_does_not_need_high_source_diversity(self):
        self.root_prediction["status"] = "analysis"
        self.root_prediction["sources"] = [
            {"label": "Crowd listing", "url": "https://www.olbg.com/betting-tips/example"}
        ]
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)

    def test_cross_track_near_duplicate_involving_high_fails(self):
        changed = BODY.replace("disciplined", "organised")
        self.add_olbg(olbg_prediction(text=changed))
        report = self.report()
        self.assertTrue(any("quality near-duplicate" in error for error in report.errors))
        self.assertTrue(all(entry["near_duplicates"] for entry in report.manifest["picks"]))

    def test_analysis_only_cross_track_duplicate_is_a_review_warning(self):
        self.root_prediction["status"] = "analysis"
        value = olbg_prediction(status="analysis")
        self.add_olbg(value)
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)
        self.assertTrue(any("BKB" not in warning and "near-duplicate" in warning for warning in report.warnings))

    def test_distinct_cross_track_prose_passes(self):
        value = olbg_prediction(
            text="Choose Alpha Team to win because their goalkeeper has stopped eleven high-quality "
                 "chances across the last two home matches. A different official injury report confirms "
                 "the starting defensive pair trained this week, while Beta Team completed only one "
                 "full session after travelling. Those availability details and the shot-stopping sample "
                 "support Alpha without relying on the earlier defensive analysis."
        )
        self.add_olbg(value)
        report = self.report()
        self.assertEqual(report.errors, [], report.errors)

    def test_manifest_is_byte_deterministic(self):
        first = self.report()
        second = self.report()
        serialise = lambda report: json.dumps(report.manifest, sort_keys=True, ensure_ascii=False)
        self.assertEqual(serialise(first), serialise(second))
        self.assertNotIn("generated_at", first.manifest)


if __name__ == "__main__":
    unittest.main()
