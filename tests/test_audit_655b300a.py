"""Regression pins for session-655b300a (task-54, 2026-10-23T22:40Z pass).

The pass found five league-table ordinals in four Rugby Union write-ups that the URC table had
overtaken after the three Friday Round 4 matches, and recorded five further irregularities rather
than repairing them. These tests pin both directions: the corrected ordinals, and the disclosure
items that must stay published instead of being silently dropped.

Nothing here depends on the wall clock, the network, or a sibling's register numbering.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(name):
    return json.loads((DATA / name).read_text())


class TestUrcOrdinals(unittest.TestCase):
    """FL-177: the table published on 23 October puts Leinster 11th, Munster 10th, Bulls 4th,
    Stormers 5th, Ulster 12th and Scarlets 13th. Four write-ups had the pre-Round-4 order."""

    STALE = {
        "predictions.json": [
            "sit tenth on 8 points",
            "Munster are ninth on 9",
        ],
        "predictions-olbg.json": [
            "puts Leinster tenth on eight points",
            "Munster sit ninth on nine points",
            "places the Stormers fourth on 11 points",
            "Scarlets sit twelfth on 7 points",
            "has the Bulls third on 11 points",
            "Ulster are eleventh on 8 points",
        ],
    }
    FRESH = {
        "predictions.json": ["sit 11th on 8 points", "Munster are 10th on 9"],
        "predictions-olbg.json": [
            "puts Leinster 11th on eight points",
            "Munster sit 10th on nine points",
            "places the Stormers fifth on 11 points",
            "Scarlets sit 13th on 7 points",
            "has the Bulls fourth on 11 points",
            "Ulster are 12th on 8 points",
        ],
    }

    def _bodies(self, name):
        doc = load(name)
        rows = doc["predictions"]
        return " \n ".join(row.get("body") or row.get("text") or "" for row in rows)

    def test_stale_ordinals_are_gone(self):
        for name, phrases in self.STALE.items():
            body = self._bodies(name)
            for phrase in phrases:
                with self.subTest(file=name, phrase=phrase):
                    self.assertNotIn(phrase, body)

    def test_corrected_ordinals_are_present(self):
        for name, phrases in self.FRESH.items():
            body = self._bodies(name)
            for phrase in phrases:
                with self.subTest(file=name, phrase=phrase):
                    self.assertIn(phrase, body)

    def test_positions_are_attributed_to_the_table_date(self):
        """A rank without a date decays silently; the replacement must date the snapshot."""
        for name in ("predictions.json", "predictions-olbg.json"):
            body = self._bodies(name)
            self.assertIn("published on 23 October", body)

    def test_urc_evidence_block_matches_the_correction(self):
        evidence = load("official.json")["reread_20261023T2130"]["fixtures"]
        expected = {
            "RGU-14 / RGU-609578": ("8 pts", "9 pts", "75 for", "72 for"),
            "RGU-609580": ("11 pts", "7 pts", "81 for", "68 for"),
            "RGU-609576": ("11 pts", "8 pts", "126 for", "88 for"),
        }
        for key, fragments in expected.items():
            facts = " ".join(evidence[key]["facts"])
            for fragment in fragments:
                with self.subTest(row=key, fragment=fragment):
                    self.assertIn(fragment, facts)
        self.assertIn("11th", " ".join(evidence["RGU-14 / RGU-609578"]["facts"]))
        self.assertIn("10th", " ".join(evidence["RGU-14 / RGU-609578"]["facts"]))

    def test_every_write_up_keeps_a_minimum_length(self):
        for name in ("predictions.json", "predictions-olbg.json"):
            for row in load(name)["predictions"]:
                text = row.get("body") or row.get("text") or ""
                if row.get("status") == "high":
                    with self.subTest(file=name, ref=row.get("ref") or row.get("match_id")):
                        self.assertGreaterEqual(len(text.split()), 30)


class TestRegisterItems(unittest.TestCase):
    """FL-177..FL-182 must exist, carry a reviewable source and stay published."""

    IDS = ["FL-177", "FL-178", "FL-179", "FL-180", "FL-181", "FL-182", "FL-183"]

    def setUp(self):
        self.items = {item["id"]: item for item in load("flagged.json")["items"]}

    def test_items_exist_and_have_a_source(self):
        for flag in self.IDS:
            with self.subTest(flag=flag):
                self.assertIn(flag, self.items)
                sources = self.items[flag]["sources"]
                self.assertTrue(sources, flag)
                for source in sources:
                    self.assertTrue(source["url"].startswith("https://"), source["url"])

    def test_displayed_detail_is_not_empty(self):
        for flag in self.IDS:
            item = self.items[flag]
            self.assertGreater(len(item["title"]), 20, flag)
            self.assertGreater(len(item["detail"]), 100, flag)
            self.assertGreater(len(item["action"]), 60, flag)

    def test_fl177_names_the_four_repaired_writes(self):
        affected = set(self.items["FL-177"]["affected_ids"])
        self.assertEqual(affected, {"RGU-14", "RGU-609578", "RGU-609580", "RGU-609576"})

    def test_fl178_records_the_three_listing_reads(self):
        urls = {source["url"] for source in self.items["FL-178"]["sources"]}
        self.assertIn("https://www.olbg.com/betting-tips", urls)
        self.assertIn("https://www.olbg.com/betting-tips/Tennis/3", urls)
        self.assertIn("https://www.olbg.com/betting-tips/Ice_Hockey/13", urls)

    def test_fl180_keeps_both_nhl_endpoints(self):
        urls = {source["url"] for source in self.items["FL-180"]["sources"]}
        self.assertTrue(any("api-web.nhle.com/v1/standings" in u for u in urls), urls)
        self.assertTrue(any("api.nhle.com/stats/rest" in u for u in urls), urls)

    def test_flag_ids_are_unique(self):
        ids = [item["id"] for item in load("flagged.json")["items"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_flags_are_rendered_on_both_review_pages(self):
        for page in ("flagged.html", ROOT / "olbg" / "flagged.html"):
            html = (ROOT / page).read_text() if isinstance(page, str) else page.read_text()
            for flag in self.IDS:
                with self.subTest(page=str(page), flag=flag):
                    self.assertIn(flag, html)


class TestReadReceipts(unittest.TestCase):
    """data/raw/probe-655b300a/reads.json is the dated record of what was actually fetched."""

    def setUp(self):
        self.doc = json.loads((DATA / "raw" / "probe-655b300a" / "reads.json").read_text())

    def test_every_read_has_an_https_url_and_a_finding(self):
        self.assertGreaterEqual(len(self.doc["reads"]), 10)
        for read in self.doc["reads"]:
            with self.subTest(url=read["url"]):
                self.assertTrue(read["url"].startswith("https://"))
                self.assertGreater(len(read["established"]), 40)
                self.assertGreater(len(read["quote"]), 20)

    def test_official_sources_behind_the_live_picks_were_read(self):
        urls = " ".join(read["url"] for read in self.doc["reads"])
        for host in ("statsapi.mlb.com", "api-web.nhle.com", "unitedrugby.com",
                     "legavolley.it", "gaacork.ie", "nba.com"):
            with self.subTest(host=host):
                self.assertIn(host, urls)

    def test_failed_reads_are_recorded_not_hidden(self):
        failed = self.doc["failed_reads"]
        self.assertTrue(failed)
        for entry in failed:
            self.assertTrue(entry["url"].startswith("https://"))
            self.assertGreater(len(entry["result"]), 20)

    def test_observation_clock_is_dated_and_not_in_the_future(self):
        """FL-183: the first draft stamped these receipts 63 minutes ahead of the build clock.
        This is the assertion that caught it, so it stays even though the stamp it guards has moved."""
        publication = load("publication.json")["publication_as_of"]
        self.assertRegex(self.doc["observation_clock_utc"], r"^2026-10-23T21:30:00Z$")
        self.assertLessEqual(self.doc["observation_clock_utc"], publication)


class TestSelfDatedStamp(unittest.TestCase):
    """FL-183 must stay in the register, and the withdrawal must stay visible in the receipts."""

    def test_fl183_exists_and_is_corrected(self):
        items = {item["id"]: item for item in load("flagged.json")["items"]}
        self.assertIn("FL-183", items)
        self.assertEqual(items["FL-183"]["status"], "corrected")
        self.assertIn("22:40", items["FL-183"]["detail"])

    def test_receipts_admit_the_withdrawn_stamp(self):
        doc = json.loads((DATA / "raw" / "probe-655b300a" / "reads.json").read_text())
        self.assertIn("22:40", doc["clock_note"])
        self.assertIn("FL-183", doc["clock_note"])

    def test_no_receipt_payload_still_claims_the_withdrawn_time(self):
        doc = json.loads((DATA / "raw" / "probe-655b300a" / "reads.json").read_text())
        payload = json.dumps({k: v for k, v in doc.items() if k != "clock_note"})
        self.assertNotIn("22:40", payload)
        self.assertNotIn("2240", (DATA / "official.json").read_text())

    def test_published_register_page_shows_fl183(self):
        for page in (ROOT / "flagged.html", ROOT / "olbg" / "flagged.html"):
            with self.subTest(page=str(page)):
                self.assertIn("FL-183", page.read_text())


class TestReviewedHostAllowlist(unittest.TestCase):
    """The comparator link in FL-180 must stay reviewable by the site checker."""

    def test_api_nhle_host_is_allowlisted_with_a_reason(self):
        source = (ROOT / "tools" / "check_site.py").read_text()
        self.assertIn('"api.nhle.com"', source)
        window = source.split('"api.nhle.com"')[0][-600:]
        self.assertIn("session-655b300a", window)


class TestPublicationIntegrity(unittest.TestCase):
    """No source observation may sit after the build clock, and every HIGH row needs a piece."""

    def setUp(self):
        self.events = load("events.json")
        self.checks = load("release_checks.json")["events"]
        self.publication = load("publication.json")["publication_as_of"]

    def test_no_observation_is_later_than_the_publication_clock(self):
        for key, record in self.checks.items():
            stamp = record.get("checked_at")
            if not stamp:
                continue
            with self.subTest(event=key):
                self.assertLessEqual(stamp, self.publication)

    def test_every_high_row_has_a_written_piece(self):
        preds = {row["ref"] for row in load("predictions.json")["predictions"]}
        highs = [row for row in self.events["events"]
                 if row["pick"]["confidence"] == "HIGH"]
        self.assertTrue(highs)
        for row in highs:
            with self.subTest(ref=row["ref"]):
                self.assertIn(row["ref"], preds)

    def test_high_rows_are_inside_the_requested_band(self):
        for row in self.events["events"]:
            if row["pick"]["confidence"] != "HIGH":
                continue
            price = row["pick"]["price"]
            with self.subTest(ref=row["ref"]):
                self.assertGreaterEqual(price, 1.40)
                self.assertLessEqual(price, 101.00)


if __name__ == "__main__":
    unittest.main()
