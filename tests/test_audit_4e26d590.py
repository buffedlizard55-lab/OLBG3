"""Regression tests for the independent capture-to-publication provenance auditor."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_provenance as audit  # noqa: E402


CAPTURE_LINE = (
    "Tennis|all|Tennis/All_Tennis/All_Events/A_vs_B|A_vs_B|42|Tomorrow|12:00|"
    "Win Match|A|3/4 Win Tips||2026-10-25T12:00:00.000Z|1.80|125|4/5|75|A vs B|"
    "https://www.olbg.com/betting-tips/Tennis/3"
)
OFFICIAL_URL = "https://www.atptour.com/en/scores/example-official-source"
PREDICTION_TEXT = (
    "A is the money-line selection after stronger recent results and a settled lineup. "
    "The home player has won three consecutive matches, while the opponent arrives after "
    "two defeats. Official availability notes list no withdrawal, so the selection remains "
    "A to win with measured confidence and an explicit match-winner market."
)


def write_json(root: Path, relative: str, value) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class SyntheticWorkspace:
    """One fully linked, synthetic capture/match/line/prediction workspace."""

    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data" / "raw").mkdir(parents=True)
        self.meta = {
            "run_started_utc": "2026-10-24T12:00:00Z",
            "harvest_completed_utc": "2026-10-24T12:00:00Z",
            "olbg_locale_date": "2026-10-24",
            "harvest_file": "raw/test.tsv",
            "harvest_format": "v3",
            "supplementary_harvests": [],
        }
        (self.root / "data" / "raw" / "test.tsv").write_text(CAPTURE_LINE + "\n", encoding="utf-8")
        self.verifications = {
            "sources": [{"id": "S1", "url": OFFICIAL_URL, "class": "official", "name": "Official test"}],
            "event_verifications": {
                "42": {
                    "status": "verified", "competition": "Test Tour", "sources": ["S1"],
                    "fixture_name": "A vs B", "home": "A", "away": "B",
                }
            },
        }
        self._write_common()
        observations, issues, _ = audit.read_captures(self.root / "data", self.meta)
        if issues:
            raise AssertionError(issues)
        source_row = observations[0]
        match = audit.expected_match(source_row, self.verifications["event_verifications"]["42"], {})
        self.match = match
        self.line = {
            "match_id": "TEN-42", "sport": match["sport"], "event_name": match["event_name"],
            "home": "A", "away": "B", "competition": match["competition"],
            "start": match["date_iso"], "olbg_url": match["olbg_url"],
            "inputs": {
                "olbg_market": match["olbg_market"],
                "olbg_consensus_selection": match["olbg_consensus_selection"],
                "olbg_tips": match["olbg_tips"], "p_raw": 0.75, "p_shrunk": 0.7143,
                "basis": "synthetic test input",
            },
            "our_match_probability": 0.6, "our_home_probability": 0.6,
            "our_pick": "A", "our_pick_probability": 0.6, "our_fair_odds": 1.67,
            "our_price_pick": 1.58, "our_us_odds_pick": "-172", "our_price_other": 2.37,
            "confidence": "high", "release": {"source": OFFICIAL_URL},
        }
        self.prediction = {
            "match_id": "TEN-42", "sport": "Tennis", "match": "A vs B",
            "selection": "A to win (money line, 1.58 / -172)", "confidence": "high",
            "text": PREDICTION_TEXT,
            "sources": [{"label": "Official test source", "url": OFFICIAL_URL}],
            "status": "high",
        }
        self.rewrite_derived()

    def _write_common(self):
        write_json(self.root, "data/meta.json", self.meta)
        write_json(self.root, "data/verifications.json", self.verifications)
        write_json(self.root, "data/live_overrides.json", {"withdrawn": [], "updates": []})
        write_json(self.root, "data/official.json", {"source_tiers": {"official": ["atptour.com"]}})
        write_json(self.root, "data/publication.json", {"publication_as_of": "2026-10-24T12:00:00Z"})
        write_json(self.root, "data/events.json", {"events": []})
        write_json(self.root, "data/gap_sports.json", {"rows": []})
        write_json(self.root, "data/predictions.json", {"predictions": []})
        (self.root / "data" / "schema.md").write_text("# Test schema\n", encoding="utf-8")

    def rewrite_derived(self):
        write_json(self.root, "data/matches.json", [self.match])
        write_json(self.root, "data/lines.json", [self.line])
        write_json(self.root, "data/predictions-olbg.json", {"predictions": [self.prediction]})

    def report(self):
        self.rewrite_derived()
        return audit.build_report(self.root)

    def cleanup(self):
        self.temp.cleanup()


class FunctionTests(unittest.TestCase):
    def test_tip_parser_accepts_rendered_suffix_and_rejects_non_count(self):
        self.assertEqual((25, 31), audit.parse_tips("25/31 Win Tips"))
        self.assertEqual((0, 0), audit.parse_tips("0/0"))
        self.assertEqual((None, None), audit.parse_tips("about 25/31"))
        self.assertEqual((None, None), audit.parse_tips(""))

    def test_event_url_handles_both_capture_depths(self):
        shallow = audit.event_url("Tennis/All_Tennis/All_Events", "A_vs_B", 3, "42")
        deep = audit.event_url("Tennis/All_Tennis/All_Events/A_vs_B", "A_vs_B", 3, "42")
        self.assertEqual(shallow, deep)
        self.assertNotIn("A_vs_B/A_vs_B", deep)

    def test_numeric_reader_leaves_unreadable_values_empty(self):
        self.assertEqual(1.8, audit.numeric_or_none("1.80"))
        self.assertIsNone(audit.numeric_or_none("not stated"))
        self.assertIsNone(audit.numeric_or_none(""))

    def test_override_history_uses_last_record_for_that_match(self):
        source = audit.capture_sources({
            "run_started_utc": "2026-10-24T00:00:00Z", "harvest_file": "raw/test.tsv",
            "harvest_format": "v3", "harvest_completed_utc": "2026-10-24T00:00:00Z",
        })[0]
        row = audit.parse_capture_line(CAPTURE_LINE, source, 1)
        expected = audit.expected_match(row, {}, {
            "olbg_consensus_selection": "B", "olbg_tips": "4/5 Win Tips",
            "olbg_confidence_pct": 80, "olbg_market": "Money Line",
        })
        self.assertEqual("B", expected["olbg_consensus_selection"])
        self.assertEqual((4, 5), (expected["olbg_tips_won"], expected["olbg_tips_total"]))
        self.assertEqual("match_winner", expected["market_family"])

    def test_similarity_is_normalized_and_bounded(self):
        self.assertEqual(1.0, audit.trigram_similarity(PREDICTION_TEXT, PREDICTION_TEXT.lower()))
        score = audit.trigram_similarity(PREDICTION_TEXT, "completely different words about another event")
        self.assertGreaterEqual(score, 0.0)
        self.assertLess(score, 0.1)

    def test_selection_alias_expansion_is_conservative(self):
        aliases = {"CAR Hurricanes": "Carolina Hurricanes"}
        self.assertTrue(audit.selection_names_pick(
            "PIT Penguins", "Pittsburgh Penguins to win the money line at 1.53 (-189)", aliases,
        ))
        self.assertTrue(audit.selection_names_pick(
            "MIL Brewers", "Milwaukee Brewers to win the money line at 1.67 (-149)", aliases,
        ))
        self.assertTrue(audit.selection_names_pick(
            "CAR Hurricanes", "Carolina Hurricanes to win the money line at 1.70 (-143)", aliases,
        ))
        self.assertFalse(audit.selection_names_pick(
            "PIT Penguins", "Nashville Penguins to win the money line at 1.53 (-189)", aliases,
        ))
        self.assertFalse(audit.selection_names_pick(
            "PIT Penguins", "Nashville Predators to win the money line at 1.53 (-189)", aliases,
        ))


class SyntheticReportTests(unittest.TestCase):
    def setUp(self):
        self.workspace = SyntheticWorkspace()

    def tearDown(self):
        self.workspace.cleanup()

    def codes(self, report, severity=None):
        return {
            issue["code"] for issue in report["issues"]
            if severity is None or issue["severity"] == severity
        }

    def test_fully_linked_workspace_passes(self):
        report = self.workspace.report()
        self.assertEqual([], [i for i in report["issues"] if i["severity"] == "error"])
        self.assertEqual(1, report["summary"]["capture_observations"])
        self.assertEqual(1, report["summary"]["published_matches"])
        self.assertEqual("TEN-42", report["event_lineage"][0]["match_id"])
        self.assertEqual(64, len(report["input_sha256"]["matches.json"]))
        markdown = audit.render_markdown(report)
        self.assertIn("# Capture-to-publication provenance audit", markdown)
        self.assertIn("[raw/test.tsv](../data/raw/test.tsv)", markdown)
        self.assertIn("data/provenance_audit.json", markdown)

    def test_changed_published_capture_field_is_an_error(self):
        self.workspace.match["olbg_tips"] = "99/100 Win Tips"
        report = self.workspace.report()
        self.assertIn("capture_publication_field_mismatch", self.codes(report, "error"))
        mismatch = next(i for i in report["issues"] if i["code"] == "capture_publication_field_mismatch")
        self.assertEqual("olbg_tips", mismatch["field"])
        self.assertEqual("3/4 Win Tips", mismatch["expected"])
        self.assertEqual(1, mismatch["line"])

    def test_unresolved_verification_source_is_an_error(self):
        self.workspace.match["verification_ids"] = ["MISSING"]
        report = self.workspace.report()
        self.assertIn("verification_source_id_unresolved", self.codes(report, "error"))

    def test_line_arithmetic_and_input_drift_are_errors(self):
        self.workspace.line["our_price_pick"] = 1.60
        self.workspace.line["our_price_other"] = 2.40
        self.workspace.line["our_match_probability"] = 0.61
        self.workspace.line["inputs"]["olbg_tips"] = "1/1 Win Tips"
        self.workspace.line["inputs"]["p_raw"] = 0.5
        report = self.workspace.report()
        self.assertIn("line_price_does_not_recompute", self.codes(report, "error"))
        self.assertIn("line_other_price_mismatch", self.codes(report, "error"))
        self.assertIn("line_match_probability_mismatch", self.codes(report, "error"))
        self.assertIn("line_raw_probability_mismatch", self.codes(report, "error"))
        self.assertIn("line_input_mismatch", self.codes(report, "error"))

    def test_high_prediction_must_name_pick_and_have_official_source(self):
        self.workspace.prediction["selection"] = "B to win (money line, 1.58 / -172)"
        self.workspace.prediction["sources"] = [{"label": "Unknown", "url": "https://example.com/source"}]
        self.workspace.line["release"]["source"] = "https://example.com/source"
        report = self.workspace.report()
        self.assertIn("high_prediction_selection_mismatch", self.codes(report, "error"))
        self.assertIn("high_prediction_official_source_missing", self.codes(report, "error"))

    def test_prohibited_prediction_term_is_an_error(self):
        self.workspace.prediction["text"] = PREDICTION_TEXT + " This model sentence must not be published."
        report = self.workspace.report()
        self.assertIn("prediction_prohibited_term", self.codes(report, "error"))

    def test_later_capture_start_conflict_is_warning_not_silent_choice(self):
        later = CAPTURE_LINE.replace("2026-10-25T12:00:00.000Z", "2026-10-25T06:00:00.000Z")
        later = later.replace("|1.80|125|", "|2.00|100|")
        (self.workspace.root / "data" / "raw" / "later.tsv").write_text(later + "\n", encoding="utf-8")
        self.workspace.meta["supplementary_harvests"] = [{
            "file": "raw/later.tsv", "format": "v3", "olbg_locale_date": "2026-10-24",
            "harvest_completed_utc": "2026-10-24T13:00:00Z",
        }]
        write_json(self.workspace.root, "data/meta.json", self.workspace.meta)
        report = self.workspace.report()
        self.assertIn("capture_start_conflict", self.codes(report, "warning"))
        self.assertNotIn("capture_start_conflict", self.codes(report, "error"))
        self.assertIn("capture_price_changed", self.codes(report, "info"))
        selected = report["event_lineage"][0]
        self.assertEqual("raw/test.tsv", selected["selected_capture"])
        self.assertEqual(2, len(selected["observations"]))
        self.assertEqual(1.8, selected["observations"][0]["odds_decimal"])
        self.assertEqual(2.0, selected["observations"][1]["odds_decimal"])
        self.assertEqual("4/5", selected["observations"][0]["odds_fractional"])
        self.assertEqual("all", selected["observations"][0]["league_label"])
        self.assertEqual(1, report["summary"]["unselected_observations"])

    def test_malformed_event_id_is_reported_without_crashing(self):
        (self.workspace.root / "data" / "raw" / "test.tsv").write_text(
            CAPTURE_LINE.replace("|42|", "|not-an-id|") + "\n", encoding="utf-8"
        )
        report = self.workspace.report()
        self.assertIn("capture_event_id_invalid", self.codes(report, "error"))
        self.assertIn("published_match_has_no_selected_capture", self.codes(report, "error"))

    def test_schema_probability_semantics_conflict_is_visible(self):
        (self.workspace.root / "data" / "schema.md").write_text(
            "our_match_probability is the probability of the **OLBG consensus selection**, not the pick.",
            encoding="utf-8",
        )
        self.workspace.match["olbg_consensus_selection"] = "B"
        self.workspace.line["inputs"]["olbg_consensus_selection"] = "B"
        report = self.workspace.report()
        self.assertIn("schema_probability_semantics_conflict", self.codes(report, "warning"))


class CommittedSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.build_report(ROOT)

    def test_committed_capture_to_publication_chain_has_no_errors(self):
        errors = [issue for issue in self.report["issues"] if issue["severity"] == "error"]
        self.assertEqual([], errors)

    def test_lineage_accounts_for_every_published_match(self):
        lineage = self.report["event_lineage"]
        published = {row["match_id"] for row in lineage if row["published"]}
        actual = {row["id"] for row in json.loads((ROOT / "data" / "matches.json").read_text())}
        self.assertEqual(actual, published)
        self.assertEqual(len(actual), self.report["summary"]["published_lines"])

    def test_every_lineage_observation_has_manual_review_provenance(self):
        for row in self.report["event_lineage"]:
            self.assertTrue(row["observations"], row["match_id"])
            for observation in row["observations"]:
                self.assertTrue(observation["capture"], row["match_id"])
                self.assertIsInstance(observation["line"], int)
                self.assertTrue(observation["event_url"].startswith("https://www.olbg.com/"))
                self.assertIn("event_id=" + row["event_id"], observation["event_url"])

    def test_report_is_deterministic_for_fixed_inputs(self):
        self.assertEqual(self.report, audit.build_report(ROOT))

    def test_any_source_clock_conflict_retains_both_observations(self):
        for issue in self.report["issues"]:
            if issue["code"] != "capture_start_conflict":
                continue
            values = {observation["value"] for observation in issue["observations"]}
            self.assertGreater(len(values), 1)
            self.assertTrue(all(observation["capture"] for observation in issue["observations"]))


if __name__ == "__main__":
    unittest.main()
