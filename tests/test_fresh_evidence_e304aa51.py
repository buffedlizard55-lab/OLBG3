"""Regression coverage for the 2026-10-24 fresh-evidence promotion and publication pass.

These checks separate immutable historical audit pins from invariants that must hold for whichever
capture is current: one primary snapshot, dynamic probe provenance, complete HIGH-piece evidence,
and byte-faithful storage of binary source documents.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import live_refresh  # noqa: E402
import probe_cited  # noqa: E402
from build_dataset import parse_decimal_price  # noqa: E402
from extract_listings import EMPTY_CAPTURE  # noqa: E402


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def harvest_rows(path: Path) -> list[list[str]]:
    return [line.split("|") for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


class CurrentPrimaryLineage(unittest.TestCase):
    def setUp(self):
        self.meta = load("data/meta.json")
        self.harvest = DATA / self.meta["harvest_file"]
        self.rows = harvest_rows(self.harvest)
        self.matches = load("data/matches.json")

    def test_fresh_populated_capture_is_the_only_primary_input(self):
        self.assertEqual("raw/olbg-harvest-20261024T2224Z-e304aa51.tsv",
                         self.meta["harvest_file"])
        self.assertEqual(124, len(self.rows))
        self.assertEqual(12, len({row[0] for row in self.rows}))
        self.assertIsNone(self.meta["previous_harvest"])
        self.assertEqual([], self.meta["previous_harvests_extra"])
        self.assertEqual([], self.meta["supplementary_harvests"])
        archived = {row["file"] for row in self.meta["archived_primary_harvests"]}
        self.assertIn("raw/olbg-harvest-20261023T1700Z.tsv", archived)

    def test_current_board_has_one_row_per_current_harvest_event(self):
        source_ids = [row[4] for row in self.rows]
        published_ids = [re.search(r"event_id=(\d+)", row["olbg_url"]).group(1)
                         for row in self.matches]
        self.assertEqual(len(source_ids), len(set(source_ids)), "harvest event ids must be unique")
        self.assertEqual(len(published_ids), len(set(published_ids)), "published events must be unique")
        self.assertEqual(set(source_ids), set(published_ids))
        self.assertEqual(len(self.rows), len(self.matches))

    def test_non_numeric_starting_price_is_blank_and_disclosed(self):
        self.assertIsNone(parse_decimal_price("SP"))
        self.assertEqual(2.35, parse_decimal_price("2.35"))
        greyhound = next(row for row in self.matches if row["id"] == "GRY-690043")
        self.assertIsNone(greyhound["olbg_odds_decimal"])
        self.assertEqual("SP", greyhound["olbg_odds_raw"])
        self.assertIn("decimal left blank", greyhound["olbg_odds_displayed_note"])
        self.assertIn("not inferred", greyhound["row_notes"])


class RefreshControlFlow(unittest.TestCase):
    def test_hydration_fallback_runs_only_after_an_empty_ssr_result(self):
        capture, target = Path("capture"), Path("out.tsv")
        with patch.object(live_refresh, "run", return_value=0) as called:
            self.assertEqual(0, live_refresh.extract_capture(capture, target))
        self.assertEqual(1, called.call_count)
        self.assertNotIn("--svelte-fallback", called.call_args.args)

        with patch.object(live_refresh, "run", side_effect=[EMPTY_CAPTURE, 0]) as called:
            self.assertEqual(0, live_refresh.extract_capture(capture, target))
        self.assertEqual(2, called.call_count)
        self.assertNotIn("--svelte-fallback", called.call_args_list[0].args)
        self.assertIn("--svelte-fallback", called.call_args_list[1].args)

    def test_promotion_archives_metadata_but_does_not_chain_old_rows(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            raw = root / "data/raw"
            capture = raw / "live-20261024T2359Z-test"
            capture.mkdir(parents=True)
            manifest = {
                "captured_at_utc": "2026-10-24T23:59:00Z",
                "pages": [{"url": "https://www.olbg.com/betting-tips/Tennis/3",
                           "path": "/betting-tips/Tennis/3", "sport": "Tennis",
                           "outcome": "captured", "fetched_at_utc": "2026-10-24T23:59:01Z"}],
            }
            (capture / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            harvest = raw / "olbg-harvest-20261024T2359Z-test.tsv"
            harvest.write_text("Tennis|all|prefix|A_vs_B|42|Tomorrow|12:00|Win Match|A|1/2 Win Tips||2026-10-25T12:00:00.000Z|2.00|100|1/1|50|A vs B|https://www.olbg.com/betting-tips/Tennis/3\n",
                               encoding="utf-8")
            meta_path = root / "data/meta.json"
            meta_path.write_text(json.dumps({
                "harvest_file": "raw/old.tsv", "harvest_completed_utc": "2026-10-23T00:00:00Z",
                "previous_harvest": "raw/older.tsv", "previous_harvests_extra": ["raw/x.tsv"],
                "supplementary_harvests": ["raw/y.tsv"], "session": "prior",
            }), encoding="utf-8")
            old_root, old_raw = live_refresh.ROOT, live_refresh.RAW
            try:
                live_refresh.ROOT, live_refresh.RAW = root, raw
                self.assertTrue(live_refresh.promote_primary(capture, harvest))
                self.assertFalse(live_refresh.promote_primary(capture, harvest), "promotion is idempotent")
            finally:
                live_refresh.ROOT, live_refresh.RAW = old_root, old_raw
            promoted = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual("raw/olbg-harvest-20261024T2359Z-test.tsv",
                             promoted["harvest_file"])
            self.assertEqual([], promoted["supplementary_harvests"])
            self.assertIsNone(promoted["previous_harvest"])
            self.assertEqual([], promoted["previous_harvests_extra"])
            self.assertEqual("raw/old.tsv", promoted["archived_primary_harvests"][0]["file"])


class DynamicOfficialProbeProvenance(unittest.TestCase):
    def test_current_nhl_and_mlb_observations_name_the_probe_that_produced_them(self):
        probe = DATA / "raw/official-20261024T2225Z"
        manifest = json.loads((probe / "manifest.json").read_text(encoding="utf-8"))
        stamp = re.sub(r"[^0-9TZ]", "", manifest["started_at_utc"])
        expected = {f"S-NHL-API-{stamp}", f"S-MLB-API-{stamp}"}
        ver = load("data/verifications.json")
        sources = {source["id"]: source for source in ver["sources"]}
        self.assertTrue(expected <= set(sources))
        for source_id in expected:
            source = sources[source_id]
            self.assertEqual(manifest["started_at_utc"], source["observed_at"])
            self.assertTrue(source["probe_file"].startswith("data/raw/official-20261024T2225Z/"))
        linked = [record for record in ver["event_verifications"].values()
                  if set(record.get("sources") or []) & expected]
        self.assertEqual(15, len(linked))
        self.assertTrue(all(set(record["sources"]) <= expected for record in linked))
        self.assertIn("official-20261024T2225Z", ver["session"])


class CitedEvidenceCollection(unittest.TestCase):
    def test_scope_contains_every_non_olbg_source_on_both_high_prediction_tracks(self):
        _, refs = probe_cited.cited_urls("2026-10-24")
        expected: dict[str, set[str]] = {}
        for track, filename, key in (
            ("root", "predictions.json", "ref"),
            ("olbg", "predictions-olbg.json", "match_id"),
        ):
            for piece in load(f"data/{filename}")["predictions"]:
                if piece.get("status") != "high":
                    continue
                for source in piece.get("sources") or []:
                    url = source.get("url", "")
                    if urlsplit(url).hostname == "www.olbg.com":
                        continue
                    expected.setdefault(url, set()).add(f"{track}/{piece[key]}")
        for url, references in expected.items():
            self.assertIn(url, refs)
            self.assertTrue(references <= set(refs[url]), url)
        self.assertIn("https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka", refs)
        self.assertIn("root/CRK-188838", refs[next(url for url in refs if "ecb.co.uk/news/4594465" in url)])
        self.assertIn("olbg/CRI-188838", refs[next(url for url in refs if "ecb.co.uk/news/4594465" in url)])

    def test_binary_documents_are_stored_byte_for_byte(self):
        payload = b"%PDF-1.7\x00\xff\nnot utf8\n%%EOF"
        with tempfile.TemporaryDirectory() as tmp_name:
            out = Path(tmp_name)
            result = probe_cited.store_response(out, "document", "https://example.test/a.pdf",
                                                "application/pdf", payload)
            stored = out / result["file"]
            self.assertEqual("verbatim_pdf", result["storage"])
            self.assertEqual(payload, stored.read_bytes())
            self.assertEqual(hashlib.sha256(payload).hexdigest(),
                             hashlib.sha256(stored.read_bytes()).hexdigest())

    def test_different_urls_cannot_silently_overwrite_the_same_readable_name(self):
        a = probe_cited.evidence_key("https://example.test/report?a=1")
        b = probe_cited.evidence_key("https://example.test/report?a=2")
        self.assertNotEqual(a, b)
        self.assertRegex(a, r"-[0-9a-f]{12}$")


class PakistanEnglandPublication(unittest.TestCase):
    def test_fixture_clock_price_and_two_unique_writeups_are_published(self):
        match = next(row for row in load("data/matches.json") if row["id"] == "CRI-188838")
        line = next(row for row in load("data/lines.json") if row["match_id"] == "CRI-188838")
        self.assertEqual("2026-10-25T08:00:00Z", match["official_start_utc"])
        self.assertIsNone(match["venue"], "ECB states Lahore, not a stadium")
        self.assertEqual("Pakistan", line["our_pick"])
        self.assertEqual(1.60, line["our_price_pick"])
        self.assertEqual("-167", line["our_us_odds_pick"])
        self.assertEqual("high", line["confidence"])

        root = next(row for row in load("data/predictions.json")["predictions"]
                    if row["ref"] == "CRK-188838")
        olbg = next(row for row in load("data/predictions-olbg.json")["predictions"]
                    if row["match_id"] == "CRI-188838")
        self.assertNotEqual(root["body"], olbg["text"])
        banned = re.compile(r"\b(model|verified)\b", re.I)
        for text, piece in ((root["body"], root), (olbg["text"], olbg)):
            self.assertGreaterEqual(len(text.split()), 30)
            self.assertIn("Pakistan", piece["selection"])
            self.assertIsNone(banned.search(text))
            hosts = {urlsplit(source["url"]).hostname for source in piece["sources"]}
            self.assertIn("www.ecb.co.uk", hosts)
            self.assertIn("www.icc-cricket.com", hosts)

    def test_dated_icc_table_does_not_reprice_older_cricket_prose(self):
        lines = {row["match_id"]: row for row in load("data/lines.json")}
        self.assertEqual(1.60, lines["CRI-188838"]["our_price_pick"])
        root_events = {row["ref"]: row for row in load("data/events.json")["events"]}
        self.assertEqual(1.57, root_events["CRK-04"]["pick"]["price"])
        official = load("data/official.json")["form_data"]
        self.assertIn("ICC_WhiteBall_2026_ratings_2026_10_22", official)
        self.assertIn("ICC_WhiteBall_2026_ratings_2026_10_24", official)


class WorkflowOrdering(unittest.TestCase):
    def test_pages_promotes_evidence_before_either_board_build(self):
        text = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        refresh = text.index("scripts/live_refresh.py")
        self.assertLess(refresh, text.index("python scripts/build.py"))
        self.assertLess(refresh, text.index("tools/build_dataset.py"))

    def test_live_harvest_supports_schedule_and_manual_refresh_without_masked_rebase(self):
        text = (ROOT / ".github/workflows/live-harvest.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^\s+schedule:")
        self.assertRegex(text, r"(?m)^\s+workflow_dispatch:")
        self.assertNotIn("git rebase origin/main ||", text)


if __name__ == "__main__":
    unittest.main()
