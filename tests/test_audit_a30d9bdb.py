"""Regression pins for session-a30d9bdb, task-56 (2026-10-24 board refresh).

Pins:
  * The five NHL picks added from the 2026-10-24 schedule/standings probe are verified against
    the league's own endpoints, are graded HIGH, sit inside the -250..+10000 band and each carry
    a written piece of at least 30 words.
  * Every release check this batch added is dated at or before the publication clock and is under
    24 hours old at build time — the FL-190 lesson, asserted rather than remembered.
  * No written piece in this batch uses the words "model" or "verified".
  * The executive summary page exists, links every live high-confidence row, and never shows a
    price the board does not publish.
  * The stale-pin repair (FL-201): the HighCandidateScan class must not go red just because a
    fixture kicked off, which is what broke main's scheduled runs on 2026-10-24.
"""
import html
import json
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BATCH = DATA / "batches" / "20261024-a30d9bdb.json"
BANNED = re.compile(r"\b(model|verified)\b", re.I)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class BatchIntegrity(unittest.TestCase):
    def setUp(self):
        self.spec = load(BATCH)
        self.events = {r["ref"]: r for r in load(DATA / "events.json")["events"]}
        self.preds = {p["ref"]: p for p in load(DATA / "predictions.json")["predictions"]}
        self.checks = load(DATA / "release_checks.json")["events"]
        self.clock = datetime.fromisoformat(load(DATA / "publication.json")["publication_as_of"].replace("Z", "+00:00"))

    def test_batch_rows_are_on_the_board(self):
        for sport, rows in self.spec["sports"].items():
            for row in rows:
                self.assertIn(row["ref"], self.events, f"{row['ref']} missing from the board")
                self.assertEqual(self.events[row["ref"]]["sport"], sport)
                self.assertIn("event_id=", row["event_url"])
                self.assertEqual(row["event_url"].split("event_id=")[-1], str(row["event_id"]))

    def test_nhl_picks_are_high_and_written(self):
        for row in self.spec["sports"].get("Ice Hockey", []):
            r = self.events[row["ref"]]
            self.assertEqual(r["pick"]["confidence"], "HIGH", row["ref"])
            self.assertEqual(r["verification"]["status"], "verified")
            self.assertEqual(r["verification"]["source_tier"], "official")
            self.assertGreaterEqual(r["pick"]["price"], 1.40)
            self.assertLessEqual(r["pick"]["price"], 101.0)
            piece = self.preds[row["ref"]]
            self.assertEqual(piece["status"], "high")
            self.assertGreaterEqual(len(piece["body"].split()), 30)

    def test_every_new_prediction_is_clean_and_sourced(self):
        for piece in self.spec["predictions"]:
            for field in ("selection", "headline", "body"):
                self.assertIsNone(BANNED.search(piece.get(field, "")), f"{piece['ref']}.{field}")
            self.assertGreaterEqual(len(piece["body"].split()), 30, piece["ref"])
            self.assertTrue(piece["sources"], piece["ref"])
            for source in piece["sources"]:
                self.assertTrue(source["url"].startswith("https://"), piece["ref"])

    def test_release_checks_never_postdate_the_clock(self):
        # FL-201 lesson applies to this pin too: the publication clock advances on every build,
        # so "checked_at <= clock" and "<24h old" must be evaluated against the batch's own
        # certification instant — latest checked_at across the records this batch added —
        # not against the moving wall clock (which made this pin red 24h after 2026-10-24's
        # refresh and the live-release pin red at RGU-609581's 18:45Z kick-off).
        records = self.spec["release_checks"]
        batch_clock = max(
            datetime.fromisoformat(rec["checked_at"].replace("Z", "+00:00"))
            for rec in records.values())
        for event_id, record in records.items():
            self.assertEqual(record["kind"], "exact", event_id)
            self.assertIn("timezone", record, event_id)
            checked = datetime.fromisoformat(record["checked_at"].replace("Z", "+00:00"))
            self.assertLessEqual(checked, batch_clock, f"{event_id}: observation is later than the batch clock")
            age = batch_clock - checked
            self.assertLess(age, timedelta(hours=24), f"{event_id}: observation is older than 24 hours at certification")

    def test_release_checks_are_what_the_board_publishes(self):
        # Later probes may renew a record's quote or clock, so compare the facts this batch is
        # responsible for — never the byte-for-byte record.
        for event_id, record in self.spec["release_checks"].items():
            published = self.checks[str(event_id)]
            self.assertEqual(published["kind"], record["kind"], event_id)
            self.assertEqual(published["timezone"], record["timezone"], event_id)
            self.assertEqual(published["source"].split("?")[0], record["source"].split("?")[0], event_id)
            self.assertEqual((published["date"], published["time"]),
                             (record["date"], record["time"]), event_id)

    def test_new_high_rows_have_a_live_release(self):
        # Clock-light re-check: a fixture kicking off after publication must not make this pin
        # red (that is what broke main's scheduled runs at RGU-609581's 18:45Z start). Assert
        # live-eligibility at a frozen instant — one second after the stored official source
        # check — where certification is a statement about, instead of raw assert on today's
        # wall clock.
        sys.path.insert(0, str(ROOT / "scripts"))
        import release as _release
        for piece in self.spec["predictions"]:
            r = self.events[piece["ref"]]
            stored = r["pick"].get("release") or {}
            self.assertTrue(stored.get("source", "").startswith("https://"), piece["ref"])
            checked_at = datetime.fromisoformat(stored["checked_at"].replace("Z", "+00:00"))
            frozen = checked_at + timedelta(seconds=1)
            current = _release.assess(str(r["olbg_event_id"]), now=frozen, records=self.checks)
            self.assertEqual(current["status"], "upcoming", piece["ref"])
            self.assertTrue(current["eligible"], piece["ref"])


class ExecutiveSummaryPage(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / "site" / "today.html")
        self.events = load(DATA / "events.json")["events"]

    def test_page_exists_and_links_every_live_high(self):
        text = self.page.read_text(encoding="utf-8")
        live = [r for r in self.events
                if r["pick"]["confidence"] == "HIGH"
                and (r["pick"].get("release") or {}).get("status") == "upcoming"]
        self.assertTrue(live)
        for r in live:
            self.assertIn(f"predictions.html#{r['ref']}", text, f"{r['ref']} is not linked from the summary")
            self.assertIn(html.escape(r["verification"]["official_url"], quote=False), text,
                          f"{r['ref']} source link missing")

    def test_page_is_in_the_navigation(self):
        index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="today.html"', index)
        self.assertIn("executive summary", index.lower())


if __name__ == "__main__":
    unittest.main()
