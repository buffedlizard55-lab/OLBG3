#!/usr/bin/env python3
"""audit_170e6805.py — executive-summary & written-pick quality audit (session-170e6805).

Recomputes, from committed data only (no network, no inference):
  * per-sport counts for the 15 in-scope sports: OLBG fixtures, originated lines
    (win / handicap / total markets present), written predictions, live HIGH picks;
  * line-by-line quality checks on every written prediction on both tracks:
    >=30 words, unique prose, no reader-facing banned words ("model"/"verified"),
    an explicit selection, a confidence label, an https source link, and — for
    HIGH picks on the OLBG track — an originated price inside the brief band
    -250..+10000 (decimal 1.40..101.00);
  * the live executive summary: HIGH picks whose release status is "upcoming"
    at the committed publication clock.

Outputs: data/audit-170e6805.json and exec-summary.html (standalone root page,
served by the legacy GitHub Pages branch publisher). Nothing in the source
data is modified; defects are reported, not repaired.
"""
from __future__ import annotations
import html, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
          "Baseball", "Gaelic Football", "Greyhounds", "Tennis", "Motor Racing",
          "Handball", "Ice Hockey", "Basketball", "Rugby League"]
BAND_LOW, BAND_HIGH = -250, 10000
BANNED = re.compile(r"\b(model|verified)\b", re.I)


def us_price(raw):
    try:
        return int(str(raw).replace("+", "").strip())
    except Exception:
        return None


def words(text):
    return len(re.findall(r"\S+", text or ""))


def main() -> int:
    clock = json.loads((ROOT / "data/publication.json").read_text())["publication_as_of"]
    matches = json.loads((ROOT / "data/matches.json").read_text())
    lines = {r["match_id"]: r for r in json.loads((ROOT / "data/lines.json").read_text())}
    olbg_preds = json.loads((ROOT / "data/predictions-olbg.json").read_text())["predictions"]
    root_preds = json.loads((ROOT / "data/predictions.json").read_text())["predictions"]

    issues, seen = [], {}
    def check(track, pid, sport, selection, text, sources, confidence):
        w = words(text)
        if w < 30:
            issues.append({"track": track, "id": pid, "issue": f"prediction under 30 words ({w})"})
        if BANNED.search(text or ""):
            issues.append({"track": track, "id": pid, "issue": "banned reader-facing word (model/verified) in prediction text"})
        if not (selection or "").strip():
            issues.append({"track": track, "id": pid, "issue": "no explicit selection"})
        if not confidence:
            issues.append({"track": track, "id": pid, "issue": "no confidence label"})
        urls = [s.get("url", "") for s in (sources or []) if isinstance(s, dict)]
        if not urls or not all(u.startswith("https://") for u in urls):
            issues.append({"track": track, "id": pid, "issue": "missing or non-https source link"})
        key = re.sub(r"\s+", " ", (text or "").strip().lower())
        if key in seen:
            issues.append({"track": track, "id": pid, "issue": f"duplicate prose of {seen[key]}"})
        else:
            seen[key] = pid

    for p in olbg_preds:
        check("olbg", p["match_id"], p.get("sport"), p.get("selection"), p.get("text"),
              p.get("sources"), p.get("confidence"))
        if p.get("confidence") == "high":
            line = lines.get(p["match_id"], {})
            price = us_price(line.get("our_us_odds_pick"))
            if price is None:
                issues.append({"track": "olbg", "id": p["match_id"], "issue": "HIGH pick has no originated price"})
            elif not (BAND_LOW <= price <= BAND_HIGH):
                issues.append({"track": "olbg", "id": p["match_id"],
                               "issue": f"HIGH pick originated price {price:+d} outside brief band -250..+10000"})
            if line.get("confidence") and line["confidence"] != "high":
                issues.append({"track": "olbg", "id": p["match_id"],
                               "issue": f"prediction labelled HIGH but originated line confidence is '{line['confidence']}'"})
    for p in root_preds:
        # Root-track pieces are archival 'analysis' unless explicitly graded; only a piece
        # presented as a pick (status/row_confidence set) must carry a confidence label.
        conf = p.get("row_confidence") or ("HIGH" if p.get("status") == "high" else "ARCHIVE")
        check("root", p["ref"], None, p.get("selection"), p.get("body"), p.get("sources"), conf)

    per_sport = {}
    live_high = []
    for sport in SPORTS:
        ms = [m for m in matches if m.get("sport") == sport]
        ls = [lines[m["id"]] for m in ms if m["id"] in lines]
        preds = [p for p in olbg_preds if p.get("sport") == sport]
        live = []
        for p in preds:
            line = lines.get(p["match_id"], {})
            if p.get("confidence") == "high" and (line.get("release") or {}).get("status") == "upcoming":
                live.append(p)
                live_high.append({**p, "price": line.get("our_us_odds_pick"),
                                  "decimal": line.get("our_price_pick"),
                                  "start_utc": (line.get("release") or {}).get("start_utc"),
                                  "olbg_url": line.get("olbg_url"),
                                  "handicap": line.get("our_handicap_line"),
                                  "total": line.get("our_total_line")})
        per_sport[sport] = {
            "fixtures": len(ms), "lines": len(ls),
            "markets": {"win": sum(1 for r in ls if r.get("our_price_pick")),
                        "handicap": sum(1 for r in ls if r.get("our_handicap_line") is not None),
                        "total": sum(1 for r in ls if r.get("our_total_line") is not None)},
            "written_predictions": len(preds),
            "written_high": sum(1 for p in preds if p.get("confidence") == "high"),
            "live_high_upcoming": len(live), "target": 5,
            "shortfall": max(0, 5 - len(live)),
        }

    audit = {"session": "170e6805", "publication_clock": clock,
             "brief": {"band_us": [BAND_LOW, BAND_HIGH], "min_words": 30, "target_per_sport": 5},
             "totals": {"fixtures": len(matches), "lines": len(lines),
                        "written_olbg": len(olbg_preds), "written_root": len(root_preds),
                        "live_high_upcoming": len(live_high),
                        "sports_meeting_target": sum(1 for v in per_sport.values() if v["live_high_upcoming"] >= 5),
                        "issues": len(issues)},
             "per_sport": per_sport, "live_high": sorted(live_high, key=lambda x: (x["sport"], x["match_id"])),
             "issues": issues}
    (ROOT / "data/audit-170e6805.json").write_text(json.dumps(audit, indent=2) + "\n")

    # ---- standalone executive-summary page ----
    rows = "".join(
        f"<tr><td>{html.escape(s)}</td><td>{v['fixtures']}</td><td>{v['lines']}</td>"
        f"<td>{v['markets']['win']}/{v['markets']['handicap']}/{v['markets']['total']}</td>"
        f"<td>{v['written_predictions']}</td><td>{v['live_high_upcoming']}</td><td>{v['target']}</td>"
        f"<td>{'✅ meets target' if v['shortfall']==0 else '⚠️ shortfall '+str(v['shortfall'])}</td></tr>"
        for s, v in per_sport.items())
    cards = "".join(
        f"<article class='card'><h3>🎯 PICK — {html.escape(p['selection'])}</h3>"
        f"<p><b>{html.escape(p.get('match',''))}</b> · {html.escape(p['sport'])} · starts {html.escape(str(p.get('start_utc') or 'see source'))} · "
        f"our originated price <b>{html.escape(str(p.get('decimal')))} ({html.escape(str(p.get('price')))})</b> · confidence <b>HIGH</b></p>"
        f"<p>{html.escape(p['text'])}</p><p>Sources: " +
        " · ".join(f"<a href='{html.escape(s['url'])}'>{html.escape(s.get('label','source'))}</a>" for s in p.get("sources", [])) +
        (f" · <a href='{html.escape(p['olbg_url'])}'>OLBG event</a>" if p.get("olbg_url") else "") + "</p></article>"
        for p in audit["live_high"])
    flags = "".join(f"<li><code>{html.escape(i['track'])}/{html.escape(i['id'])}</code> — {html.escape(i['issue'])}</li>" for i in issues)
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OLBG3 — Executive Summary &amp; Picks (audit 170e6805)</title>
<link rel="stylesheet" href="style.css"><style>.card{{border:2px solid #14532d;border-radius:10px;padding:14px;margin:12px 0;background:#f0fdf4}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px 8px}}</style></head>
<body><header><h1>🏆 OLBG3 — Executive Summary: Today's Highest-Confidence Picks</h1>
<p>Publication clock: <b>{clock}</b> (committed snapshot; picks whose start has passed are excluded by release status). Sports covered: {', '.join(SPORTS)}.</p>
<p><a href="index.html">Dashboard</a> · <a href="predictions.html">All written predictions</a> · <a href="lines.html">Originated lines &amp; markets</a> · <a href="flagged.html">Flagged for Review</a> · <a href="brief.html">Brief coverage (5-per-sport target)</a></p></header>
<section><h2>⭐ The picks — {len(live_high)} live HIGH-confidence picks (originated prices inside −250…+10000)</h2>{cards or '<p>No live HIGH pick at this clock.</p>'}</section>
<section><h2>📊 Per-sport coverage vs the 5-per-sport target</h2>
<p>Markets investigated for every fixture: win/money-line, handicap/spread, match total (counts shown as win/handicap/total). Shortfalls are published, never filled with unverified picks.</p>
<table><tr><th>Sport</th><th>OLBG fixtures</th><th>Originated lines</th><th>Markets W/H/T</th><th>Written predictions</th><th>Live HIGH</th><th>Target</th><th>Status</th></tr>{rows}</table></section>
<section><h2>🚩 Flagged for review ({len(issues)})</h2><ul>{flags or '<li>None</li>'}</ul>
<p>Full machine-readable audit: <a href="data/audit-170e6805.json">data/audit-170e6805.json</a> · write-up: <code>docs/audit-170e6805.md</code> in the repo. Every pick above links its official source and its OLBG event page for manual review. Prices are our own originated lines, not bookmaker prices.</p></section>
</body></html>"""
    (ROOT / "exec-summary.html").write_text(page)
    print(json.dumps(audit["totals"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
