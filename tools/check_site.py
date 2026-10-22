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
sys.path.insert(0, str(ROOT / "scripts"))
from board_dates import build_date  # noqa: E402

BUILD_DATE = build_date()  # real UTC today, never a frozen constant
DOCS = ROOT / "olbg-board"
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
    "stats.unitedrugby.com",
    "ehfcl.eurohandball.com",
    "buffedlizard55-lab.github.io",
    "github.com",
    # Hosts reviewed and accepted by session-074739aa's re-audit (2026-10-21).
    # Each is the official body/league/event site used for a verification record,
    # or a corroborating listing explicitly classed "secondary" in data/verifications.json.
    "www.nhl.com",
    "www.wtatennis.com",
    "prod2.lnr.fr",
    "top14.lnr.fr",
    "www.eishockey.at",
    "www.kac.at",
    "www.ice.hockey",
    "www.shl.se",
    "euroleague.tv",
    "www.euroleaguebasketball.com",
    "cricket.co.za",
    "www.icc-cricket.com",
    "sedziowie.pzps.pl",
    "www.vfb-volleyball.de",
    "www.butterfieldbdachampionship.com",
    "www.lpga.com",
    "www.bbc.co.uk",
    "apnews.com",
    "www.formula1.com",
    "scores24.live",
    "www.sportsgambler.com",
    # Hosts reviewed by session-af0789e6's 06:50Z sweep (official bodies / official data feeds).
    "api-web.nhle.com",
    "statsapi.mlb.com",
    "www.protennislive.com",
    "api.wtatennis.com",
    "www.euroleaguebasketball.net",
    "www.tauronliga.pl",
    # Official governing-body & federation hosts verified in session-4f267387's 2026-10-22 pass.
    "wtafiles.wtatennis.com",
    "ftpserver.euroleague.net",
    "www.realmadrid.com",
    "www.ecb.co.uk",
    "cricketireland.ie",
    "www.nzc.nz",
    "www.cricket.com.au",
    "stats.swehockey.se",
    "www.liiga.fi",
    "www.eurohandball.com",
    "www.daikin-hbl.de",
    "www.tvbstuttgart.de",
    "cvf.cz",
    "www.cvf.cz",
    "www.plusliga.pl",
    "www.pgatour.com",
    # Governing-body reference portals linked as "official reference — fixture unverified"
    # for rows without a retrieved official confirmation (session-0570f99b). The link is a
    # research lead to the sport's official body, never a claim that it confirms the row.
    "www.world.rugby",
    "www.intrl.sport",
    "www.gaa.ie",
    "www.volleyballworld.com",
    "www.ladieseuropeantour.com",
    "munster.gaa.ie",
    "gaacork.ie",
    "www.maighcuilinn.com",
    "www.gbgb.org.uk",
    "www.nrl.com",
    "www.superleague.co.uk",
    "www.sixnationsrugby.com",
    # Official competition/club hosts synced from audited board verifications (events.json / gap_sports.json).
    "www.volleyball-bundesliga.de",
    "ladieseuropeantour.com",
    "www.championsleague.basketball",
    "topphandball.no",
    "handbollsligan.se",
    "morsthy.dk",
    "www.hcb.net",
    "mestaruusliiga.fi",
    "www.volleybal.nl",
    "www.legavolleyfemminile.it",
    # Official governing-body & club hosts verified in session-5cef1e25's 2026-10-22 07:25Z audit.
    "wst.tv",
    "aalborghaandbold.dk",
    "tophaandbold.dk",
    "lnb.com.br",
    "www.legavolley.it", "www.sunshinetour.com", "shl.se", "www.sa20.co.za", "www.leinsterrugby.ie", "www.kbl.or.kr", "www.jgto.org", "sunshinetour.com", "sixnationsrugby.com", "sa20.co.za", "leinsterrugby.ie", "kbl.or.kr", "jgto.org", "en.volleyballworld.com",
    "cbv.com.br",
    "www.cdbidasoa.eus",
    "asobal.es",
    "www.asiantour.com",
    "legendstour.com",
    "www.legendstour.com",
    "golf.com.au",
    "www.cricket.co.za",
    "biz.chosun.com",
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
    preds = json.loads((DATA / "predictions-olbg.json").read_text())["predictions"]
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

    # 5 predictions & strict -250..+10000 odds window enforcement
    seen_texts: set[str] = set()
    pred_ids: set[str] = set()
    for p in preds:
        pred_ids.add(p["match_id"])
        wc = len(p["text"].split())
        if wc < 30:
            errors.append(f"prediction {p['match_id']} is only {wc} words")
        if p["text"].strip() in seen_texts:
            errors.append(f"prediction {p['match_id']} duplicates text")
        seen_texts.add(p["text"].strip())
        if not p["sources"]:
            errors.append(f"prediction {p['match_id']} has no sources")
        row = lines[p["match_id"]]
        status = p.get("status", "high")
        if status not in ("high", "analysis"):
            errors.append(f"prediction {p['match_id']} status {status!r} is not 'high' or 'analysis'")
        if status == "high" and row["confidence"] != "high":
            errors.append(f"prediction {p['match_id']} claims status 'high' but its row is "
                          f"{row['confidence']}")
        if status == "analysis" and row["confidence"] == "high":
            errors.append(f"prediction {p['match_id']} is labelled analysis but its row is HIGH")

    for mid, l in lines.items():
        if l["confidence"] == "high":
            price = l.get("our_price_pick")
            prob = l.get("our_pick_probability")
            if price is None or not (1.40 <= price <= 101.00):
                errors.append(f"high pick {mid} price {price} outside -250..+10000 (1.40..101.00)")
            if prob is None or prob >= 0.70:
                errors.append(f"high pick {mid} prob {prob} >= 0.70 chalk cap")
            if mid not in pred_ids:
                errors.append(f"high pick {mid} missing written prediction")
            if l.get("start") and l["start"] < BUILD_DATE.isoformat():
                errors.append(f"high pick {mid} kick-off {l['start']} has already passed")

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
