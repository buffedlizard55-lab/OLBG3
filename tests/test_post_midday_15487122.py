"""Regression tests for session-15487122 post-PR #93 audit & parity sync (FL-096..FL-098)."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class PostMidday15487122AuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.events = {e["ref"]: e for e in json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]}
        cls.gap = {r["ref"]: r for r in json.loads((DATA / "gap_sports.json").read_text(encoding="utf-8"))["rows"]}
        cls.lines = {l["match_id"]: l for l in json.loads((DATA / "lines.json").read_text(encoding="utf-8"))}
        cls.rc = json.loads((DATA / "release_checks.json").read_text(encoding="utf-8"))["events"]
        cls.flagged = {f["id"]: f for f in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}
        cls.preds_root = {
            p["ref"]: p
            for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]
        }
        cls.preds_olbg = {
            p["match_id"]: p
            for p in json.loads((DATA / "predictions-olbg.json").read_text(encoding="utf-8"))["predictions"]
        }

    def test_un_timezoned_lnv_and_osaka_pdfs_do_not_guess_venue_zones(self) -> None:
        # FL-096: lnv.fr prints 'J3 : Arago de Sète - Chaumont VB 52 : jeudi 22 octobre (20h)' without CEST
        self.assertEqual(self.rc["37005"]["kind"], "date_only")
        self.assertIsNone(self.rc["37005"]["timezone"])
        self.assertIn("J3 : Arago de Sète - Chaumont VB 52 : jeudi 22 octobre (20h)", self.rc["37005"]["quote"])
        self.assertIn(self.events["VOL-30"]["pick"]["release"]["status"], ("unverified_start", "past_date"))  # 22 Oct fixture
        self.assertIn(self.lines["VOL-37005"]["release"]["status"], ("unverified_start", "past_date"))
        self.assertIn("FL-096", self.flagged)

        # FL-097: wtafiles 405/OP.pdf prints 'Starting at 11:30 AM' without JST
        self.assertEqual(self.rc["902135"]["kind"], "date_only")
        self.assertIsNone(self.rc["902135"]["timezone"])
        self.assertEqual(self.events["TEN-38"]["pick"]["release"]["status"], "unverified_start")
        self.assertIn("FL-097", self.flagged)

    def test_pdc_world_championship_2027_high_pick_and_root_parity(self) -> None:
        # FL-098: pdc.tv/WCFAQ explicitly states 'Friday December 11 (1900 GMT)' and 128-player field
        self.assertEqual(self.rc["26023"]["kind"], "exact")
        self.assertEqual(self.rc["26023"]["timezone"], "GMT")
        # HIGH while the 22 Oct pdc.tv observation is under 24 h old; afterwards the release gate
        # expires it to MEDIUM (stale_source) until the page is re-read.
        self.assertIn(self.gap["DRT-18"]["pick"]["confidence"], ("HIGH", "MEDIUM"))
        self.assertEqual(self.gap["DRT-18"]["pick"]["label"], "Luke Littler")
        # The OLBG outright tip count moved from 23/36 to 23/37 in the 20:55Z re-capture, so
        # the disclosed Dirichlet shrinkage re-prices the same selection.
        self.assertEqual(self.gap["DRT-18"]["pick"]["price"], 2.34)
        self.assertGreaterEqual(len(self.preds_root["DRT-18"]["body"].split()), 30)

        self.assertIn(self.lines["DAR-26023"]["confidence"], ("high", "medium"))
        self.assertEqual(self.lines["DAR-26023"]["our_pick"], "Luke Littler")
        self.assertEqual(self.lines["DAR-26023"]["our_price_pick"], 2.34)
        self.assertGreaterEqual(len(self.preds_olbg["DAR-26023"]["text"].split()), 30)

        # TEN-40 (902117) + 18 live 12:15Z root tip counts synced
        # Evening refresh 2026-10-22T20:55Z (session-784afe97): the live Osaka listing now
        # carries 2/2 tips on the Sara Bejlek v Marie Bouzkova quarter-final.
        self.assertEqual(self.events["TEN-40"]["olbg_tips"], "2/2")
        # Evening refresh 2026-10-22T20:55Z (session-784afe97): the live MLB listing now
        # carries 16/20 tips on the World Series opener.
        self.assertGreaterEqual(int(self.events["BSB-01"]["olbg_tips"].split("/")[1]), 20)  # 16/20 then; 25/31 on 23 Oct
        self.assertEqual(self.events["SNK-14"]["olbg_tips"], "3/4")
        self.assertIn("FL-098", self.flagged)


if __name__ == "__main__":
    unittest.main()
