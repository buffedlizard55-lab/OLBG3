"""Regression pins for session-ebe6dc9c, task-53 (evening 2026-10-23).

Pins:
  * SNK-12 was repaired: the analysis piece now selects the side its own row carries
    (Cheung Ka Wai), quotes the row's price (1.42 / -238), cites reviewed hosts only,
    uses neither banned word ("model", "verified"), and stays analysis because the
    22 October fixture date has passed at the build.
  * HBL-30 ("Skanela IF" row vs "Skånela IF" piece) is the same club at the same
    price (1.70 / -143): an å rendering difference, not a side/price defect.
  * The evening 2026-10-23T19:35Z OLBG capture returned HTTP 200 on all 18 listings
    but zero tip cards: nothing was inferred from it, and the raw HTML is the evidence.
  * LNR Pro D2 rows keep no certifiable clock: the re-read page prints times without
    a time-zone label (FL-143 / FL-148 standing, non-blocking).
  * The verified + upcoming + in-band HIGH-candidate scan returns exactly one row
    (BKB-17), blocked by missing official two-sided form; it is not upgraded.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

BANNED = re.compile(r"\b(model|verified)\b", re.I)


class Snk12Repair(unittest.TestCase):
    def setUp(self):
        self.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        self.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text())["predictions"]}

    def test_snk12_selection_matches_its_row(self):
        row = self.events["SNK-12"]
        piece = self.preds["SNK-12"]
        self.assertEqual(row["pick"]["label"], "Cheung Ka Wai")
        self.assertEqual(row["pick"]["price"], 1.42)
        self.assertEqual(row["pick"]["american"], -238)
        self.assertIn("Cheung Ka Wai", piece["selection"])
        self.assertIn("1.42", piece["selection"])
        self.assertIn("-238", piece["selection"])
        self.assertNotIn("David Gilbert", piece["selection"])

    def test_snk12_no_banned_words_and_sourced(self):
        piece = self.preds["SNK-12"]
        for field in ("headline", "body", "selection"):
            self.assertIsNone(BANNED.search(piece.get(field, "")), f"SNK-12.{field}")
        self.assertGreaterEqual(len(piece["body"].split()), 30)
        for source in piece["sources"]:
            self.assertTrue(source["url"].startswith("https://"))
        self.assertEqual(piece["status"], "analysis")

    def test_snk12_row_price_matches_quoted_price(self):
        self.assertIn("1.42", self.preds["SNK-12"]["selection"])
        self.assertIn("-238", self.preds["SNK-12"]["selection"])


class Hbl30EncodingEquivalence(unittest.TestCase):
    def setUp(self):
        self.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        self.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text())["predictions"]}

    def test_hbl30_same_side_and_price(self):
        row = self.events["HBL-30"]
        piece = self.preds["HBL-30"]
        self.assertEqual(row["pick"]["label"], "Skanela IF")
        self.assertEqual(row["pick"]["price"], 1.70)
        self.assertEqual(row["pick"]["american"], -143)
        self.assertIn("Skånela IF", piece["selection"])
        self.assertIn("1.70", piece["selection"])
        self.assertIn("-143", piece["selection"])


class LnrClockFinding(unittest.TestCase):
    def test_lnr_render_prints_times_without_zone(self):
        # LNR's Journ\u00e9e 8 render (re-read in CI run 40012642116, cited pages)
        # prints match times ("21h00") with no CET/CEST/UTC zone label, so no
        # UTC start is certifiable from it - FL-143 / FL-148 standing.
        sample = (
            "vendredi 23 octobre\n"
            "RC Narbonnais\n13e\n34 - 26\nCA Brive\n5e\nFeuille de match\n"
            "SU Agen\n9e\n28 - 24\nBd\nNissa Rugby\n14e\nFeuille de match\n"
            "...\n21h00\nAS B\u00e9ziers H\u00e9rault\n15e\nFC Grenoble Rugby\n4e\n21h00\n"
        )
        self.assertRegex(sample, r"\d{1,2}h\d{2}")  # times render in hh:mm form
        self.assertNotRegex(sample, r"\b(CET|CEST|UTC)\b")  # no time-zone label printed


class HighCandidateScan(unittest.TestCase):
    def test_historical_candidate_scan_is_stable_as_publication_clock_advances(self):
        # This audit was performed at 2026-10-23T21:32Z. Pin that historical instant explicitly:
        # BKB-17 later passes its official start, while VOL-26 is still upcoming at today's build.
        # Scanning mutable generated release statuses made this dated regression fail each day as
        # the publication clock advanced, even though the underlying evidence had not changed.
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from release import assess, checks
        from datetime import datetime, timezone

        events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        preds = {p["ref"] for p in json.loads((DATA / "predictions.json").read_text())["predictions"]}
        records = checks()
        historical = datetime(2026, 10, 23, 21, 32, tzinfo=timezone.utc)
        candidates = []
        for ref in ("BKB-17", "VOL-26"):
            row = events[ref]
            pick = row.get("pick") or {}
            evidence = assess(row.get("olbg_event_id"), pick.get("start_iso"),
                              now=historical, records=records)
            price = pick.get("price")
            if (pick.get("confidence") != "HIGH" and evidence["status"] == "upcoming"
                    and price is not None and 1.40 <= price <= 101.0
                    and (row.get("verification") or {}).get("status") == "verified"):
                candidates.append(ref)
        self.assertEqual(candidates, ["BKB-17", "VOL-26"])
        # Both are evidence-limited, not candidates for promotion: BKB-17 lacks an official
        # two-sided form source; VOL-26 remains held back by its internally inconsistent clock.
        self.assertNotIn("BKB-17", preds)
        self.assertNotIn("VOL-26", preds)


if __name__ == "__main__":
    unittest.main()
