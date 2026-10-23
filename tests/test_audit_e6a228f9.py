"""Pins the source-link repair of 2026-10-23 (FL-161).

The defect
----------
`tools/build_dataset.py` built every published OLBG event URL as

    https://www.olbg.com/betting-tips/{path_prefix}/{slug}/{sport_id}?event_id={eid}

which is right for a *v2* capture row, where `path_prefix` stops at the competition
(`Tennis/All_Tennis/All_Events`). The *v3* capture stores `path_prefix` as the href's path up to the
sport id, so it already ends in the slug:

    Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers

Appending the slug a second time produced

    .../TB_Rays_@_MIL_Brewers/TB_Rays_@_MIL_Brewers/12?event_id=160789

which OLBG answers with **404**. That was the `olbg_url` of 177 of the 180 published rows: none of
them equalled the href the server had actually rendered, so every "OLBG event page" source link on
`/olbg/` was dead while still reading as evidence. Re-fetched live on 2026-10-23T19:33Z: the served
href renders the event page, the published one 404s.

What is asserted here
---------------------
1. For every published row whose event id appears in the committed 17:00Z capture, `olbg_url` is
   byte-identical to an href present in that capture's served HTML. This is the actual repair.
2. No published row repeats its final path segment.
3. The helper still appends the slug when the prefix is a v2-style competition path, so the three
   rows that come from the supplementary v2 capture keep their working URLs.
4. The rows carried from the v2 supplementary capture resolve to pages that exist (checked as URL
   shape here; the live fetch is recorded in docs/audit-e6a228f9.md).

These are regression pins on committed evidence. They make no claim about a match and re-verify no
sporting fact.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_dataset as bd  # noqa: E402

CAPTURE = ROOT / "data/raw/live-20261023T1700Z/listings"
HREF_RE = re.compile(r'href="(https://www\.olbg\.com/betting-tips/[^"]*event_id=(\d+))"')


def served_hrefs() -> dict[str, set[str]]:
    hrefs: dict[str, set[str]] = {}
    for f in sorted(CAPTURE.glob("*.html")):
        for url, eid in HREF_RE.findall(f.read_text(errors="replace")):
            hrefs.setdefault(eid, set()).add(url)
    return hrefs


def match_rows() -> list[dict]:
    return json.loads((ROOT / "data/matches.json").read_text())


class PublishedLinkMatchesTheServedHref(unittest.TestCase):
    def setUp(self):
        self.hrefs = served_hrefs()
        self.rows = match_rows()

    def test_the_capture_still_holds_the_evidence(self):
        # If this fails the capture was replaced, not repaired, and every assertion below is void.
        self.assertEqual(len(self.hrefs), 177)

    def test_every_row_with_a_captured_href_publishes_that_exact_href(self):
        checked = 0
        for row in self.rows:
            eid = re.search(r"event_id=(\d+)", row["olbg_url"] or "")
            if not eid or eid.group(1) not in self.hrefs:
                continue
            self.assertIn(row["olbg_url"], self.hrefs[eid.group(1)],
                          f"{row['id']} publishes a link the server never rendered")
            checked += 1
        # 177 of 180 rows come from the v3 capture; the other three come from the v2 supplement
        # and have no href in it, which is why they are skipped rather than asserted.
        self.assertEqual(checked, 177)

    def test_no_row_repeats_its_final_path_segment(self):
        for row in self.rows:
            seg = re.search(r"/betting-tips/(.+)/\d+\?event_id=", row["olbg_url"] or "")
            self.assertIsNotNone(seg, row["id"])
            parts = seg.group(1).split("/")
            if len(parts) >= 2:
                self.assertNotEqual(parts[-1], parts[-2], f"{row['id']} repeats a path segment")

    def test_the_three_supplementary_rows_still_name_their_own_event(self):
        # These came from the 16:30Z v2 supplement (no startDate attribute, no href). Their URLs
        # must still be competition/slug/id shaped, and the slug must name the fixture OLBG does.
        supplements = {r["id"]: r for r in self.rows
                       if r["id"] in ("TEN-902147", "GRY-689803", "GRY-689800")}
        self.assertEqual(len(supplements), 3)
        expected = {
            "TEN-902147": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/"
                          "Luca_Van_Assche_vs_Lorenzo_Musetti/3?event_id=902147",
            "GRY-689803": "https://www.olbg.com/betting-tips/Greyhounds/All_Greyhounds/All_Events/"
                          "5:12_Towcester/28?event_id=689803",
            "GRY-689800": "https://www.olbg.com/betting-tips/Greyhounds/All_Greyhounds/All_Events/"
                          "5:18_Kinsley/28?event_id=689800",
        }
        for mid, url in expected.items():
            self.assertEqual(supplements[mid]["olbg_url"], url, mid)


class UrlBuilder(unittest.TestCase):
    def test_v3_prefix_already_holding_the_slug_is_not_appended_again(self):
        self.assertEqual(
            bd.event_url("Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers", "TB_Rays_@_MIL_Brewers", 12, "160789"),
            "https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789")

    def test_v2_competition_prefix_still_gets_the_slug(self):
        self.assertEqual(
            bd.event_url("Tennis/All_Tennis/All_Events", "Ann_Li_vs_Ashlyn_Krueger", 3, "902157"),
            "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/"
            "Ann_Li_vs_Ashlyn_Krueger/3?event_id=902157")

    def test_a_bare_slug_prefix_is_not_repeated(self):
        # No capture has ever produced a bare-slug prefix; the row would lose its competition path,
        # so the point of this case is only that the slug is not emitted twice.
        self.assertEqual(bd.event_url("Ann_Li_vs_Ashlyn_Krueger", "Ann_Li_vs_Ashlyn_Krueger", 3, "902157"),
                         "https://www.olbg.com/betting-tips/Ann_Li_vs_Ashlyn_Krueger/3?event_id=902157")

    def test_slashes_around_the_prefix_do_not_double_up(self):
        self.assertEqual(bd.event_url("/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/", "TB_Rays_@_MIL_Brewers", 12, "1"),
                         "https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=1")


if __name__ == "__main__":
    unittest.main()
