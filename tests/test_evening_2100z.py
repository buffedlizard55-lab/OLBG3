"""Regression tests for the 2026-10-22 21:00Z evening listing capture (session-cab97f19).

These guard three properties that are easy to lose when another harvest is chained in:
  1. every row of the evening capture actually reaches the published dataset;
  2. a later capture adds rows but never restates a row an earlier capture already published;
  3. no row can be published as a live HIGH confidence pick once its certified start has passed.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from archive_guard import pins  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

EXCLUDED = {"soccer", "football", "boxing", "ufc", "mma", "american football",
            "hurling", "horse racing", "cycling", "specials"}


def load(name):
    return json.loads((DATA / name).read_text())


@pins('olbg-harvest-20261022T2100Z.tsv')
class EveningCaptureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = load("meta.json")
        cls.matches = load("matches.json")
        cls.lines = load("lines.json")
        cls.checks = load("release_checks.json")["events"]
        cls.supplementary = cls.meta.get("supplementary_harvests", [])

    def test_supplementary_capture_is_declared_and_present(self):
        files = [s["file"] for s in self.supplementary]
        self.assertIn("raw/olbg-harvest-20261022T2100Z.tsv", files)
        for rel in files:
            self.assertTrue((DATA / rel).exists(), rel)

    def test_every_captured_row_reaches_the_dataset(self):
        ids = {r["id"].split("-", 1)[1] for r in self.matches}
        for entry in self.supplementary:
            text = (DATA / entry["file"]).read_text()
            for line in text.splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                event_id = line.split("|")[4]
                self.assertIn(event_id, ids, f"{entry['file']}: event {event_id} was dropped")

    def test_supplementary_does_not_restate_primary_rows(self):
        """The primary harvest owns any event it already published; the evening read only adds."""
        primary = (DATA / self.meta["harvest_file"]).read_text()
        primary_ids = set()
        for line in primary.splitlines():
            if line.strip() and not line.startswith("#"):
                parts = line.split("|")
                if len(parts) > 4:
                    primary_ids.add(parts[4])
        self.assertTrue(primary_ids)
        # NBA CLE @ PHI appeared in both captures with different rendered clocks. The committed row
        # must still carry the capture that first published it, not the evening restatement.
        row = next(r for r in self.matches if r["id"] == "BKB-534845")
        # Rolled 2026-10-23 (session-d0f5ca54): BKB-534845 is not in today's primary, so
        # the capture that first published it is now the chained previous harvest; the
        # invariant (it keeps its first-publication stamp) is unchanged.
        self.assertEqual(row["fetched_at"], self.meta["previous_harvest"]["harvest_completed_utc"])
        self.assertFalse((row.get("row_notes") or "").startswith("supplementary"))

    def test_no_high_pick_after_its_certified_start(self):
        for line in self.lines:
            if line["confidence"] != "high":
                continue
            start = (line.get("release") or {}).get("start_utc")
            self.assertIsNotNone(start, line["match_id"])
            self.assertTrue((line.get("release") or {}).get("eligible"), line["match_id"])
            self.assertFalse(line.get("kickoff_started"), line["match_id"])

    def test_no_excluded_sport_is_published(self):
        for row in self.matches:
            self.assertNotIn(row["sport"].strip().lower(), EXCLUDED, row["id"])

    def test_high_picks_carry_a_unique_long_writeup(self):
        preds = load("predictions-olbg.json")["predictions"]
        by_id = {p["match_id"]: p for p in preds}
        texts = set()
        for line in self.lines:
            if line["confidence"] != "high":
                continue
            pred = by_id.get(line["match_id"])
            self.assertIsNotNone(pred, line["match_id"])
            self.assertGreaterEqual(len(pred["text"].split()), 30, line["match_id"])
            self.assertNotIn(pred["text"], texts, "duplicate write-up")
            texts.add(pred["text"])


if __name__ == "__main__":
    unittest.main()
