#!/usr/bin/env python3
"""Integrity checks for the generated site. Exits non-zero on any failure, so CI blocks a bad build.

Checks
  1. every internal link resolves to a file that exists
  2. every external link is https and on the reviewed host allowlist
  3. every data table row carries at least one source link
  4. every fixture, line and prediction appears on the pages that should show it
  5. predictions are at least 30 words and cite at least one source
  6. no placeholder text ("None", "nan", "{", "}") leaked into the HTML
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "data"

ALLOWED_HOSTS = {
    "www.olbg.com",
    "www.pdc.tv",
    "www.mlb.com",
    "www.espn.com",
    "www.nba.com",
    "www.cbssports.com",
    "www.snooker.org",
    "www.wst.tv",
    "www.bbc.com",
    "www.europeantour.com",
    "news.sbs.co.kr",
    "www.cricinfo.com",
    "en.wikipedia.org",
    "www.atptour.com",
    "www.unitedrugby.com",
    "ehfcl.eurohandball.com",
    "buffedlizard55-lab.github.io",
    "github.com",
}

errors: list[str] = []
warnings: list[str] = []


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.hrefs.append(d["href"])
            if self._row is not None:
                self._row.append(d["href"])
        if tag == "tr":
            self._row = []

    def handle_endtag(self, tag):
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def main() -> int:
    matches = json.loads((DATA / "matches.json").read_text())
    lines = {x["match_id"]: x for x in json.loads((DATA / "lines.json").read_text())}
    preds = json.loads((DATA / "predictions.json").read_text())["predictions"]
    flagged = json.loads((DATA / "flagged.json").read_text())["items"]

    parsers = {}
    for f in DOCS.rglob("*.html"):
        p = Collector()
        p.feed(f.read_text())
        parsers[f] = p

    # 1 + 2 links
    for f, p in parsers.items():
        for href in p.hrefs:
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            parsed = urlparse(href)
            if parsed.scheme in ("http", "https"):
                if parsed.scheme != "https":
                    errors.append(f"{f.name}: non-https external link {href}")
                if parsed.netloc not in ALLOWED_HOSTS:
                    errors.append(f"{f.name}: external host not reviewed: {parsed.netloc} ({href})")
            else:
                target = (f.parent / parsed.path).resolve()
                if not target.exists():
                    errors.append(f"{f.name}: broken internal link {href}")

    # 3 every table row in the data pages carries a source link
    for name in ("picks.html", "matches.html"):
        f = DOCS / name
        for i, row in enumerate(parsers[f].rows[1:], start=2):
            if not any(h.startswith("http") for h in row):
                errors.append(f"{name}: data row {i} has no source link")

    # 4 coverage
    picks_html = (DOCS / "picks.html").read_text()
    matches_html = (DOCS / "matches.html").read_text()
    for m in matches:
        if m["olbg_url"] not in picks_html:
            errors.append(f"picks.html missing {m['id']} ({m['olbg_url']})")
        if m["olbg_url"] not in matches_html:
            errors.append(f"matches.html missing {m['id']}")
    pred_html = (DOCS / "predictions.html").read_text()
    for p in preds:
        if p["match_id"] not in lines:
            errors.append(f"prediction {p['match_id']} has no line")
        if p["selection"] not in pred_html:
            errors.append(f"predictions.html missing selection for {p['match_id']}")
    flag_html = (DOCS / "flagged.html").read_text()
    for it in flagged:
        if it["id"] not in flag_html:
            errors.append(f"flagged.html missing {it['id']}")

    # 5 predictions
    for p in preds:
        wc = len(p["text"].split())
        if wc < 30:
            errors.append(f"prediction {p['match_id']} is only {wc} words")
        if not p["sources"]:
            errors.append(f"prediction {p['match_id']} has no sources")
        if lines[p["match_id"]]["confidence"] != "high":
            errors.append(f"prediction {p['match_id']} is not marked high confidence")

    # 6 placeholders
    for f, _ in parsers.items():
        text = f.read_text()
        for bad in (">None<", ">nan<", "{{", "}}", "&lt;class"):
            if bad in text:
                errors.append(f"{f.name}: placeholder {bad!r} found")

    # warnings only
    for m in matches:
        if m["competition"] is None:
            warnings.append(f"{m['id']}: competition not stated by source (blank by design)")
    hc = sum(1 for l in lines.values() if l["confidence"] == "high")
    print(f"pages: {len(parsers)}  fixtures: {len(matches)}  lines: {len(lines)}  "
          f"high: {hc}  predictions: {len(preds)}  flagged: {len(flagged)}")
    print(f"blank competition fields (by design): {len(warnings)}")
    if errors:
        print("\nFAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
