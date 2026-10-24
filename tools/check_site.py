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
from release import high_release_errors  # noqa: E402
from check_prediction_quality import run_quality_gate  # noqa: E402

BUILD_DATE = build_date()  # real UTC today, never a frozen constant
DOCS = ROOT / "olbg-board"
DATA = ROOT / "data"

ALLOWED_HOSTS = {
    # session-9d520984 (2026-10-24): FL-220 cites two Irish broadcasters/GAA press for the Galway
    # re-fixture (labelled press, not official); FL-222 cites the HBL's own table page.
    "www.rte.ie",
    "www.hoganstand.com",
    "www.opel-hbl.de",
    # FL-224 cites the club and federation schedule pages whose clocks carry no zone.
    "saracens.com",
    "tvf.org.tr",
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
    "www.premrugby.com",
    "stats.unitedrugby.com",
    "ehfcl.eurohandball.com",
    "ehfel.eurohandball.com",
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
    # 2026-10-23 (session-655b300a): the league's second published data service, api.nhle.com, is
    # the same organisation as api-web.nhle.com (NHL stats REST service). It is cited only as the
    # comparator in FL-180, where its season goal totals disagree with the standings service; it
    # is not used for any fixture clock, price or grade. Host reviewed, structural only.
    "api.nhle.com",
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
    # Official governing-body & club hosts verified/synced in session-a0a7003c's 2026-10-22T12:25Z audit.
    "wtafiles.wtatennis.com",
    "protennislive.com",
    "www.bcci.tv",
    "www.lnv.fr",
    "lnv-web.dataproject.com",
    "soenderjyskehh.dk",
    "www.danskhaandbold.dk",
    "www.lnh.fr",
    "www.eurohandball.com",
    "www.maighcuilinn.com",
    "gaacork.ie",
    "sedziowie.pzps.pl",
    "stats.swehockey.se",
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


def captured_event_hrefs() -> dict[str, set[str]]:
    """Every event href present in the committed raw OLBG captures, keyed by event id.

    The captures are the evidence, so this reads them directly rather than trusting a derived
    file. Nothing here is parsed into a claim: the hrefs are copied out of the served HTML.
    """
    hrefs: dict[str, set[str]] = {}
    for html_file in sorted((DATA / "raw").glob("live-*/listings/*.html")):
        text = html_file.read_text(errors="replace")
        for url, eid in re.findall(
                r'href="(https://www\.olbg\.com/betting-tips/[^"]*event_id=(\d+))"', text):
            hrefs.setdefault(eid, set()).add(url)
    for html_file in sorted((DATA / "raw").glob("svelte-*/listings/*.html")):
        text = html_file.read_text(errors="replace")
        for rel, eid in re.findall(
                r'eventUrl:"(/betting-tips/[^"]*event_id=(\d+))"', text):
            hrefs.setdefault(eid, set()).add("https://www.olbg.com" + rel)
    return hrefs


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

    # Every quoted price in a write-up must be the price the row actually carries. Prose is
    # hand-written while rows are re-priced on every rebuild, so the two drift. The root track's
    # equivalent rule in scripts/check_board.py was widened on 2026-10-22 for exactly this reason
    # (tests/test_price_quote_rule.py); this track kept only the narrow "1.58 (-172)" form, so a
    # selection label written "money line, 1.66 / -152" escaped it and DAR-32331 published a piece
    # tipping one player beside a row naming another. See FL-160. The optional comma below closes
    # a gap the root pattern has too. 1.91 is our fixed two-way handicap/total quote and is exempt
    # when the sentence names a handicap or total, because that is a different market.
    _QUOTE_PATTERNS = (
        (r"(\d+\.\d{2})\s*\(([+-]\d{2,5})\)", "dec_us"),        # "1.58 (-172)"
        (r"([+-]\d{2,5})\s*/\s*(\d+\.\d{2})", "us_dec"),        # "+732 / 7.32"
        (r"(?:money line|\bat\b|\bPriced\b)\s*,?\s*(?:an?\s+)?(\d\.\d{2})\s*(?:/|\()\s*([+-]\d{2,5})",
         "dec_us"),                                                   # "money line, 1.66 / -152"
    )
    for p in preds:
        row = lines[p["match_id"]]
        price, us = row.get("our_price_pick"), row.get("our_us_odds_pick")
        us = int(us) if us is not None else None
        blob = (p.get("selection") or "") + " " + (p.get("text") or "")
        for pattern, order in _QUOTE_PATTERNS:
            for a, b in re.findall(pattern, blob):
                q_dec, q_us = (a, b) if order == "dec_us" else (b, a)
                if float(q_dec) == 1.91 and re.search(r"handicap|total", blob, re.I):
                    continue
                if price is not None and abs(float(q_dec) - float(price)) > 0.005:
                    errors.append(f"prediction {p['match_id']} quotes decimal {q_dec} but its row prices {price}")
                if us is not None and int(q_us) != us:
                    errors.append(f"prediction {p['match_id']} quotes {q_us} but its row's US odds are {us}")

    for mid, l in lines.items():
        if l["confidence"] == "high":
            errors.extend(f"{mid}: {error}" for error in high_release_errors(
                mid.split("-", 1)[1], l.get("release")))
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

    # 5b every published OLBG source link must be the href the server actually rendered
    # The row URL used to be synthesised as {prefix}/{slug}/{sport_id}, which duplicated the final
    # path segment on the v3 capture because its path_prefix already ends in the slug: 177 of the
    # 180 published links returned 404 while reading as evidence. Anything that repeats the final
    # segment is rejected here, and where the committed capture still holds the served href the
    # two must be equal byte for byte. See FL-161.
    captured = captured_event_hrefs()
    for m in matches:
        url = m.get("olbg_url") or ""
        seg = re.search(r"/betting-tips/(.+)/\d+\?event_id=", url)
        if seg:
            parts = seg.group(1).split("/")
            if len(parts) >= 2 and parts[-1] == parts[-2]:
                errors.append(f"{m['id']}: OLBG source link repeats its final path segment ({url})")
        eid = re.search(r"event_id=(\d+)", url)
        if eid and eid.group(1) in captured and url not in captured[eid.group(1)]:
            errors.append(f"{m['id']}: OLBG source link differs from the served href "
                          f"({url} vs {sorted(captured[eid.group(1)])[0]})")

    # 6 placeholders
    for f, _ in parsers.items():
        text = f.read_text()
        for bad in (">None<", ">nan<", "{{", "}}", "&lt;class"):
            if bad in text:
                errors.append(f"{f.name}: placeholder {bad!r} found")

    # Independent written-pick prose quality (both tracks). Existing checks above stay in force;
    # this adds selection/body agreement, prohibited terms, official-document diversity and
    # cross-track near-duplicate detection without rewriting any prediction input.
    quality = run_quality_gate(ROOT)
    errors.extend(quality.errors)
    quality_counts = quality.manifest["counts"]
    print(f"written-pick quality: predictions={quality_counts['predictions']} "
          f"high={quality_counts['high']} warnings={quality_counts['warnings']}")
    for warning in quality.warnings:
        print(f"written-pick quality WARN: {warning}")

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
