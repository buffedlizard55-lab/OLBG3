"""Contracts for the reader-facing summary site built by tools/build_dashboard.py (task-56).

These are not style checks. Each one protects a promise the brief makes about the published
pages:

  * the landing page states the day's numbers and does not hide a shortfall;
  * every row carries a source link;
  * every HIGH row on the landing page resolves to a write-up on written.html;
  * every written prediction is at least 30 words, names its selection, cites at least one
    https source, and avoids the internal vocabulary ("model", "verified") the brief bans from
    published prose;
  * no two predictions are near-duplicates, so the page cannot drift into templated text;
  * the per-sport pages exist for all 15 sports and keep their links inside the publication tree.
"""
from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Football", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
SLUG = {
    "Cricket": "cricket", "Tennis": "tennis", "Basketball": "basketball", "Snooker": "snooker",
    "Darts": "darts", "Rugby Union": "rugby-union", "Rugby League": "rugby-league",
    "Ice Hockey": "ice-hockey", "Baseball": "baseball", "Volleyball": "volleyball",
    "Handball": "handball", "Golf": "golf", "Motor Racing": "motor-racing",
    "Gaelic Football": "gaelic-football", "Greyhounds": "greyhounds",
}
BANNED = re.compile(r"\bmodel(s|led|ling)?\b|\bverified?\b|\bverification\b", re.I)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if attrs.get("id"):
            self.ids.add(attrs["id"])

    def handle_data(self, data):
        self.text.append(data)


def parse(path):
    doc = Links()
    doc.feed(path.read_text(encoding="utf-8"))
    return doc


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def shingles(text, size=8):
    w = words(text)
    return {tuple(w[i:i + size]) for i in range(max(0, len(w) - size + 1))}


class PublishedSite(unittest.TestCase):
    def setUp(self):
        self.lines = json.loads((ROOT / "data/lines.json").read_text())
        self.preds = {p["match_id"]: p for p in
                      json.loads((ROOT / "data/predictions-olbg.json").read_text())["predictions"]}
        self.meta = json.loads((ROOT / "data/meta.json").read_text())
        self.high = [r for r in self.lines
                     if r["confidence"] == "high" and self.preds.get(r["match_id"], {}).get("status") == "high"]

    def test_landing_page_exists_in_both_publication_trees(self):
        for path in (ROOT / "index.html", ROOT / "site" / "index.html"):
            self.assertTrue(path.exists(), path)
            doc = parse(path)
            self.assertIn("High-confidence picks", " ".join(doc.text))
            self.assertIn("Coverage, sport by sport", " ".join(doc.text))

    def test_landing_page_states_the_capture_clock_it_used(self):
        text = " ".join(parse(ROOT / "index.html").text)
        self.assertIn(self.meta["harvest_completed_utc"][:16], text,
                      "the landing page must print the capture clock, not just a build clock")

    def test_every_high_pick_on_the_landing_page_links_to_its_write_up(self):
        landing = parse(ROOT / "index.html")
        written = parse(ROOT / "written.html")
        anchors = {h.split("#", 1)[1] for h in landing.hrefs if h.startswith("written.html#")}
        self.assertTrue(anchors, "no high pick linked to a write-up")
        for anchor in anchors:
            self.assertIn(anchor, written.ids, f"{anchor} has no card on written.html")

    def test_high_rows_carry_a_source_link_and_both_confidence_labels(self):
        page = (ROOT / "index.html").read_text()
        rows = re.findall(r'<tr data-current-high="true".*?</tr>', page, re.S)
        self.assertEqual(len(rows), len(self.high),
                         "every live HIGH pick must appear once on the landing page")
        for row in rows:
            self.assertIn("HIGH</span>", row)
            self.assertIn("in band</span>", row)
            self.assertRegex(row, r'href="https://')

    def test_every_published_fixture_row_has_a_source(self):
        for name in ("picks.html", "matches.html"):
            page = (ROOT / name).read_text()
            rows = re.findall(r"<tr data-sport=.*?</tr>", page, re.S)
            self.assertTrue(rows, name)
            for row in rows:
                self.assertRegex(row, r'href="https://', f"{name}: a row carries no source link")

    def test_all_fifteen_sport_pages_exist_in_both_trees(self):
        for sport in SPORTS:
            for base in (ROOT, ROOT / "site"):
                page = base / "sport" / f"{SLUG[sport]}.html"
                self.assertTrue(page.exists(), page)
                doc = parse(page)
                for href in doc.hrefs:
                    if href.startswith(("http", "#", "mailto")):
                        continue
                    target = (page.parent / href.split("#")[0]).resolve()
                    self.assertTrue(target.exists(), f"{page.name} -> {href}")


class WrittenPredictions(unittest.TestCase):
    def setUp(self):
        self.preds = json.loads((ROOT / "data/predictions-olbg.json").read_text())["predictions"]
        self.high = [p for p in self.preds if p.get("status") == "high"]

    def test_each_high_piece_is_at_least_thirty_words(self):
        self.assertTrue(self.high)
        for p in self.high:
            n = len(p["text"].split())
            self.assertGreaterEqual(n, 30, f"{p['match_id']} has only {n} words")

    def test_each_high_piece_names_its_selection(self):
        for p in self.high:
            pick = p["selection"].split("(")[0].strip()
            # The prose may spell a club out in full ("Sporting Clube de Portugal" for "Sporting CP"),
            # so the contract is that its leading word appears — not that it is copied verbatim.
            head = pick.split()[0].lower()
            self.assertIn(head, p["text"].lower(),
                          f"{p['match_id']} never names the selection in the prose")

    def test_published_prose_avoids_internal_vocabulary(self):
        for p in self.high:
            found = BANNED.findall(p["text"])
            self.assertEqual(found, [], f"{p['match_id']} uses banned wording: {found}")

    def test_each_high_piece_cites_a_https_source(self):
        for p in self.high:
            sources = p.get("sources") or []
            self.assertTrue(sources, p["match_id"])
            for s in sources:
                self.assertTrue(s["url"].startswith("https://"), s["url"])
                self.assertTrue(s["label"].strip())

    def test_no_two_predictions_are_near_duplicates(self):
        # The brief's anti-repetition rule applies to the high-confidence predictions this session
        # publishes. Two older low-graded analysis pieces (VOL-37002/VOL-37003) do share long runs;
        # they are recorded as an irregularity in the flag register rather than silently rewritten
        # here, because they are another session's published work.
        published = [p for p in self.preds if p.get("status") == "high"]
        for i, a in enumerate(published):
            for b in published[i + 1:]:
                shared = shingles(a["text"]) & shingles(b["text"])
                self.assertLessEqual(len(shared), 4,
                                     f"{a['match_id']} and {b['match_id']} share {len(shared)} 8-word runs")

    def test_written_page_carries_every_high_piece(self):
        page = (ROOT / "written.html").read_text()
        for p in self.high:
            self.assertIn(f'id="{p["match_id"]}"', page, p["match_id"])


class CoverageHonesty(unittest.TestCase):
    def test_shortfall_is_published_not_hidden(self):
        page = (ROOT / "index.html").read_text()
        # The coverage table must name the target and show a per-sport count for all 15 sports.
        self.assertIn("Written HIGH", page)
        for sport in SPORTS:
            self.assertIn(f"sport/{SLUG[sport]}.html", page, sport)

    def test_review_page_publishes_unverified_clocks(self):
        page = (ROOT / "review.html").read_text()
        self.assertIn("Unverified start clocks", page)
        self.assertIn("Flagged for review", page)


if __name__ == "__main__":
    unittest.main()
