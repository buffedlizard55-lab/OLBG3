#!/usr/bin/env python3
"""build_daily.py - the next-day board: every OLBG row from the latest capture, with our own line.

Inputs (committed, never fetched here)
--------------------------------------
* ``data/raw/olbg-harvest-<capture>.tsv`` - OLBG's listing exactly as served (event id, market,
  tipster consensus, printed price, OLBG's own ``start_utc``).
* ``data/daily/research-<board date>.json`` - per-row research: official start, official and press
  sources, the form inputs read from those sources, our selection and a written piece.

Line method (same arithmetic for every row, stated on the page)
---------------------------------------------------------------
* Market anchor: OLBG's printed price, de-margined: ``p_mkt = (1/price) / M`` with M = 1.05 for
  two-way markets, 1.08 where the selection is a draw/tie (three-way) and 1.20 for outrights,
  correct-score and player markets. When our selection is the other side of a two-way market, the
  anchor is ``1 - p_mkt``. A three-way draw price cannot anchor a side, so it is not used.
* Form: ``log5`` on Laplace-smoothed records ``(w+1)/(g+2)`` read from the official table, shrunk
  50% toward 0.5, plus the stated home/away edge (and minus a stated draw allowance for handball);
  or ``poisson_total`` from official goals-for/against rates for an over/under line.
* Our probability: the mean of form and market when both exist; otherwise whichever exists.
* Fair price = 1/p, shown in decimal and US odds.

Confidence (mechanical)
-----------------------
HIGH needs all of: form inputs read from official sources, a market anchor, at least two official
sources, an official start time, p >= 0.58, a fair price inside -250..+10000 (decimal 1.40-101),
OLBG's price not shorter than 95% of our fair price, a written piece of 30+ words that avoids the
brief's banned words, and a start after the publication clock. MEDIUM: researched rows with
p >= 0.52 and at least one official source. LOW: everything else, including every row we only
anchored to the market. Rows whose start has passed are shown as CLOSED.

The page never fills a blank: an official start we could not read stays empty and is listed in the
flagged section on the board's front page.
"""
from __future__ import annotations

import datetime as dt
import glob
import html
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from pick_surface import BANNED_TERMS, MIN_WORDS, words  # noqa: E402

RESEARCH_GLOB = os.path.join(ROOT, "data", "daily", "research-*.json")
BAND_LO, BAND_HI = 1.40, 101.0
P_HIGH, P_MEDIUM = 0.58, 0.52
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Football", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
TARGET = 5
OUTRIGHT_WORDS = ("outright", "tournament", "grand final", "top team", "man of the match",
                  "set score", "correct", "winner")


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def slug(sport: str) -> str:
    return sport.lower().replace(" ", "-")


def american(dec: float | None) -> str:
    if not dec or dec <= 1:
        return ""
    v = (dec - 1) * 100 if dec >= 2 else -100 / (dec - 1)
    return f"{round(v):+d}"


def parse_utc(s: str | None):
    if not s:
        return None
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def fmt_utc(s: str | None) -> str:
    t = parse_utc(s)
    return t.strftime("%a %d %b %H:%MZ") if t else ""


# ---------------------------------------------------------------- inputs
def latest_research():
    paths = sorted(glob.glob(RESEARCH_GLOB))
    if not paths:
        return None
    with open(paths[-1], encoding="utf-8") as fh:
        return json.load(fh)


def read_capture(rel_path: str) -> list[dict]:
    cols = None
    rows = []
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("# Columns:"):
                cols = [c.strip() for c in line[len("# Columns:"):].split("|")]
                continue
            if not line or line.startswith("#"):
                continue
            vals = line.split("|")
            rows.append(dict(zip(cols, vals + [""] * (len(cols) - len(vals)))))
    return rows


# ---------------------------------------------------------------- arithmetic
def margin_for(market: str, selection: str) -> float:
    m, s = (market or "").lower(), (selection or "").lower()
    if any(w in m for w in OUTRIGHT_WORDS):
        return 1.20
    if s in ("tie", "draw"):
        return 1.08
    return 1.05


def is_outright(market: str) -> bool:
    return any(w in (market or "").lower() for w in OUTRIGHT_WORDS)


def laplace(w, g):
    return (w + 1) / (g + 2)


def log5_form(f: dict) -> float:
    a, b = laplace(f["pick_w"], f["pick_g"]), laplace(f["opp_w"], f["opp_g"])
    p = a * (1 - b) / (a * (1 - b) + b * (1 - a))
    p = 0.5 + 0.5 * (p - 0.5) + f.get("edge", 0.0)
    return min(0.97, max(0.03, p * (1 - f.get("draw", 0.0))))


def poisson_le(lam: float, k: int) -> float:
    return sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))


def totals_form(f: dict) -> float:
    total = f["lam_home"] + f["lam_away"]
    under = poisson_le(total, int(math.floor(f["line"])))
    return under if f["side"].lower() == "under" else 1 - under


def flip_total(sel: str) -> str:
    if sel.lower().startswith("over"):
        return "Under" + sel[4:]
    if sel.lower().startswith("under"):
        return "Over" + sel[5:]
    return sel


# ---------------------------------------------------------------- one row
def evaluate(row: dict, res: dict | None, clock: dt.datetime) -> dict:
    sport = row["sport"]
    try:
        price = float(row.get("odds_decimal") or "")
    except ValueError:          # OLBG prints "SP" for some greyhound selections
        price = None
    market, consensus = row.get("market", ""), row.get("consensus", "")
    m = margin_for(market, consensus)
    p_cons = (1 / price) / m if price else None
    start = row.get("start_utc", "")
    out = {
        "id": f"NX-{sport[:3].upper()}-{row['event_id']}",
        "sport": sport, "event": row.get("event_name", "").strip(),
        "event_id": row["event_id"],
        "olbg_url": f"https://www.olbg.com/betting-tips/{row['path_prefix']}/"
                    f"{row['listing_url'].rstrip('/').rsplit('/', 1)[-1]}?event_id={row['event_id']}",
        "olbg_start": start, "olbg_market": market or "(not printed)", "olbg_consensus": consensus,
        "olbg_tips": row.get("tips", ""), "olbg_price": price,
        "official_start": "", "official_sources": [], "press_sources": [],
        "selection": "", "market": "", "p": None, "p_form": None, "p_mkt": None,
        "basis": "", "form_text": "", "prose": "", "reasons": [], "researched": False,
    }
    started = parse_utc(start) is not None and parse_utc(start) <= clock
    if res is None:
        # Line only: our de-margined reading of OLBG's own price for OLBG's selection.
        out.update(selection="", market=market, p=p_cons, p_mkt=p_cons,
                   basis="market-anchored line only (no form read)")
        out["confidence"] = "CLOSED" if started else "LOW"
        out["reasons"].append("no official form read for this row")
        return finish(out)

    out["researched"] = True
    out.update(official_start=res.get("official_start_utc", ""),
               official_clock_printed=res.get("official_clock_printed", ""),
               official_sources=res.get("official_sources", []),
               press_sources=res.get("press_sources", []),
               market=res.get("market", market), selection=res.get("selection", consensus),
               form_text=res.get("form_text", ""), prose=res.get("prose", ""))
    rel = res.get("market_relation", "none")
    if p_cons is not None and rel == "same":
        p_mkt = p_cons
    elif p_cons is not None and rel == "complement" and m == 1.05:
        p_mkt = 1 - p_cons
    else:
        p_mkt = None
    form = res.get("form")
    p_form = None
    if form and form.get("type") == "log5":
        p_form = log5_form(form)
    elif form and form.get("type") == "poisson_total":
        p_form = totals_form(form)
    if p_form is not None and p_mkt is not None:
        p = 0.5 * p_form + 0.5 * p_mkt
    else:
        p = p_form if p_form is not None else p_mkt
    # A totals lean that comes out under 50% is the other side of the same line.
    if form and form.get("type") == "poisson_total" and p is not None and p < 0.5:
        p, p_form = 1 - p, (1 - p_form if p_form is not None else None)
        p_mkt = 1 - p_mkt if p_mkt is not None else None
        out["selection"] = flip_total(out["selection"])
        rel = "complement"
    out.update(p=p, p_form=p_form, p_mkt=p_mkt, basis=(form or {}).get("basis", "market-anchored"))

    fair = 1 / p if p else None
    reasons = []
    if started:
        out["confidence"] = "CLOSED"
        return finish(out)
    if p_form is None:
        reasons.append("no form inputs from an official table")
    if p_mkt is None:
        reasons.append("no OLBG price for this side to anchor the line")
    if len(out["official_sources"]) < 2:
        reasons.append("fewer than two official sources")
    if not out["official_start"]:
        reasons.append("official start printed without a time zone (FL-148 rule)"
                       if out.get("official_clock_printed") else "official start time not read")
    if p is None or p < P_HIGH:
        reasons.append(f"probability under {P_HIGH:.2f}")
    if fair is None or not (BAND_LO <= fair <= BAND_HI):
        reasons.append("fair price outside -250..+10000")
    if price and rel == "same" and fair and price < 0.95 * fair:
        reasons.append(f"OLBG price {price:.2f} is shorter than our fair {fair:.2f}")
    prose = out["prose"]
    lowered = prose.lower()
    if words(prose) < MIN_WORDS or any(t in lowered for t in BANNED_TERMS):
        reasons.append("write-up shorter than 30 words (or uses a banned word)")
    if is_outright(market) and rel != "none":
        reasons.append("outright/player market")
    out["reasons"] = reasons
    if not reasons:
        out["confidence"] = "HIGH"
    elif p is not None and p >= P_MEDIUM and out["official_sources"]:
        out["confidence"] = "MEDIUM"
    else:
        out["confidence"] = "LOW"
    return finish(out)


def finish(out: dict) -> dict:
    p = out["p"]
    out["fair_dec"] = round(1 / p, 2) if p else None
    out["fair_us"] = american(1 / p) if p else ""
    out["start_mismatch"] = bool(out["official_start"] and out["olbg_start"]
                                 and parse_utc(out["official_start"]) != parse_utc(out["olbg_start"]))
    return out


# ---------------------------------------------------------------- pages
CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1d232b}
header{background:#14213d;color:#fff;padding:14px 22px}header a{color:#fca311;text-decoration:none;margin-right:14px}
main{max-width:1240px;margin:0 auto;padding:18px 22px 60px}h1{margin:.2em 0 .3em}h2{margin-top:1.8em}
.lede{color:#4a5563;max-width:900px}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.card{background:#fff;border:1px solid #d8dde3;border-left:6px solid #2a9d8f;border-radius:8px;padding:14px 16px}
.card h3{margin:.1em 0 .4em;font-size:1.05em}.pick{font-size:1.15em;font-weight:700;color:#14213d}
.meta{color:#5b6573;font-size:.88em}.tag{display:inline-block;border-radius:10px;padding:1px 9px;font-size:.8em;font-weight:700}
.HIGH{background:#2a9d8f;color:#fff}.MEDIUM{background:#e9c46a;color:#1d232b}.LOW{background:#d8dde3;color:#1d232b}
.CLOSED{background:#6c757d;color:#fff}table{border-collapse:collapse;width:100%;background:#fff;font-size:.88em}
th,td{border:1px solid #d8dde3;padding:6px 8px;vertical-align:top;text-align:left}th{background:#eef1f4}
td.num{text-align:right;white-space:nowrap}.wrap{overflow-x:auto}.warn{color:#9d0208;font-weight:600}
.small{font-size:.82em;color:#5b6573}ul.src{margin:0;padding-left:16px}.counts td{text-align:center}
"""


def page(title: str, body: str, depth: str = "../") -> str:
    nav = (f'<a href="{depth}index.html">Dashboard</a><a href="{depth}today.html">Today\'s picks</a>'
           f'<a href="index.html">Next-day board</a><a href="{depth}flagged.html">Flagged for Review</a>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} - OLBG3</title>'
            f'<style>{CSS}</style></head><body><header><strong>OLBG3</strong> &nbsp; {nav}</header>'
            f'<main>{body}</main></body></html>\n')


def src_list(items) -> str:
    if not items:
        return ""
    return '<ul class="src">' + "".join(
        f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["label"])}</a></li>' for s in items) + "</ul>"


def pct(p) -> str:
    return f"{100 * p:.0f}%" if isinstance(p, (int, float)) else ""


def card(r: dict) -> str:
    return (f'<div class="card"><span class="tag {r["confidence"]}">{r["confidence"]}</span> '
            f'<span class="meta">{esc(r["sport"])} &middot; {esc(fmt_utc(r["official_start"] or r["olbg_start"]))}</span>'
            f'<h3>{esc(r["event"])}</h3><div class="pick">{esc(r["market"])}: {esc(r["selection"])}</div>'
            f'<div class="meta">Our probability {pct(r["p"])} &middot; fair {r["fair_dec"]:.2f} ({esc(r["fair_us"])})'
            + (f' &middot; OLBG price {r["olbg_price"]:.2f}' if r["olbg_price"] else "") + '</div>'
            f'<p>{esc(r["prose"])}</p><div class="small">{esc(r["form_text"])}</div>'
            f'<div class="small">Sources: {src_list(r["official_sources"] + r["press_sources"])}'
            f'<a href="{esc(r["olbg_url"])}" rel="noopener">OLBG event page</a></div></div>')


def table(rows: list[dict]) -> str:
    head = ("<tr><th>Match</th><th>OLBG start (UTC)</th><th>Official start (UTC)</th><th>OLBG market / consensus / tips</th>"
            "<th class=num>OLBG price</th><th>Our pick</th><th class=num>Our prob.</th><th class=num>Fair dec / US</th>"
            "<th>Confidence</th><th>Why not higher / notes</th><th>Sources</th></tr>")
    body = []
    for r in rows:
        if r["official_start"]:
            off = esc(fmt_utc(r["official_start"]))
        elif r.get("official_clock_printed"):
            off = f'<span class="small">UTC blank; printed: {esc(r["official_clock_printed"])}</span>'
        elif r["researched"]:
            off = '<span class="small">blank - not read</span>'
        else:
            off = ""
        if r["start_mismatch"]:
            off += ' <span class="warn">differs from OLBG</span>'
        pick = f'{esc(r["market"])}: <strong>{esc(r["selection"])}</strong>' if r["selection"] else \
            f'<span class="small">line only for OLBG selection &ldquo;{esc(r["olbg_consensus"])}&rdquo;</span>'
        notes = "; ".join(r["reasons"]) if r["confidence"] != "HIGH" else "meets every HIGH test"
        if r["form_text"]:
            notes = esc(r["form_text"]) + "<br><span class=small>" + esc(notes) + "</span>"
        else:
            notes = f'<span class="small">{esc(notes)}</span>'
        body.append(
            f'<tr id="{esc(r["id"])}"><td>{esc(r["event"])}<br><span class="small">{esc(r["id"])}</span></td>'
            f'<td class=num>{esc(fmt_utc(r["olbg_start"]))}</td><td class=num>{off}</td>'
            f'<td>{esc(r["olbg_market"])} / {esc(r["olbg_consensus"])}<br><span class="small">{esc(r["olbg_tips"])}</span></td>'
            f'<td class=num>{"%.2f" % r["olbg_price"] if r["olbg_price"] else ""}</td><td>{pick}</td>'
            f'<td class=num>{pct(r["p"])}</td>'
            f'<td class=num>{"%.2f" % r["fair_dec"] if r["fair_dec"] else ""}<br>{esc(r["fair_us"])}</td>'
            f'<td><span class="tag {r["confidence"]}">{r["confidence"]}</span></td><td>{notes}</td>'
            f'<td>{src_list(r["official_sources"] + r["press_sources"])}'
            f'<a href="{esc(r["olbg_url"])}" rel="noopener">OLBG event</a></td></tr>')
    return f'<div class="wrap"><table>{head}{"".join(body)}</table></div>'


def build(out_root: str) -> dict | None:
    """Write <out_root>/daily/*.html. Returns a small summary, or None when there is no research file."""
    research = latest_research()
    if research is None:
        return None
    from board_dates import snapshot_utc
    clock = snapshot_utc()
    rows = [evaluate(r, research["rows"].get(r["event_id"]), clock) for r in read_capture(research["capture"])]
    rows.sort(key=lambda r: (r["olbg_start"], r["event"]))
    by_sport = {s: [r for r in rows if r["sport"] == s] for s in SPORTS}
    highs = [r for r in rows if r["confidence"] == "HIGH"]
    meds = [r for r in rows if r["confidence"] == "MEDIUM"]
    out_dir = os.path.join(out_root, "daily")
    os.makedirs(out_dir, exist_ok=True)
    shortfall = research.get("shortfall", {})

    count_rows = []
    for s in SPORTS:
        rs = by_sport[s]
        live = [r for r in rs if r["confidence"] != "CLOSED"]
        h = sum(r["confidence"] == "HIGH" for r in rs)
        reason = shortfall.get(s, "")
        link = f'<a href="{slug(s)}.html">{esc(s)}</a>'
        count_rows.append(
            f'<tr><td>{link}</td><td>{len(rs)}</td><td>{len(live)}</td>'
            f'<td>{sum(r["researched"] for r in live)}</td><td><strong>{h}</strong> / {TARGET}</td>'
            f'<td>{sum(r["confidence"] == "MEDIUM" for r in rs)}</td><td style="text-align:left" class="small">'
            f'{esc(reason) if h < TARGET else ""}</td></tr>')

    flagged = [r for r in rows if r["researched"] and r["confidence"] != "CLOSED"
               and (not r["official_start"] or r["start_mismatch"] or not r["official_sources"])]
    flag_items = "".join(
        f'<li><a href="{slug(r["sport"])}.html#{esc(r["id"])}">{esc(r["event"])}</a> - '
        + (("official start printed without a time zone, UTC left blank: " + esc(r["official_clock_printed"]))
           if not r["official_start"] and r.get("official_clock_printed") else
           "official start blank (not printed on a page we could read)" if not r["official_start"] else
           f'official {esc(fmt_utc(r["official_start"]))} vs OLBG {esc(fmt_utc(r["olbg_start"]))}')
        + ("; no official source, press only" if not r["official_sources"] else "") + "</li>"
        for r in flagged)
    extra_flags = "".join(f'<li>{esc(f)}</li>' for f in research.get("board_flags", []))

    method = ("Our probability is the average of a form reading (official tables and results, shown on each row) and "
              "OLBG's printed price with the bookmaker margin removed. Rows with no form reading are market-anchored "
              "LOW lines. HIGH means every test passed: two or more official sources, an official start time with a stated time zone, a "
              "probability of 58% or more, a fair price between -250 and +10000, OLBG's price not shorter than our "
              "fair price, a full write-up, and a start after the publication clock.")
    body = (f'<h1>Next-day board &middot; {esc(research["board_date"])}</h1>'
            f'<p class="lede">Every OLBG row in the in-scope sports from the capture taken at '
            f'{esc(research["captured_at_utc"])}, with our own line, our pick and a confidence grade. Publication clock '
            f'{esc(clock.strftime("%Y-%m-%d %H:%MZ"))}. Rows whose start has passed show as CLOSED. '
            f'{len(highs)} HIGH picks, {len(meds)} MEDIUM, {len(rows)} rows in total.</p>'
            f'<h2>Highest-confidence picks</h2>'
            + (f'<div class="cards">{"".join(card(r) for r in highs)}</div>' if highs else
               '<p>No row passed every HIGH test in this capture.</p>')
            + '<h2>Per-sport count against the target of five HIGH picks</h2>'
            '<div class="wrap"><table class="counts"><tr><th>Sport</th><th>OLBG rows</th><th>Still to start</th>'
            '<th>Researched</th><th>HIGH / target</th><th>MEDIUM</th><th>Why the target was not reached</th></tr>'
            + "".join(count_rows) + '</table></div>'
            + f'<h2>Medium-confidence leans</h2>{table(meds) if meds else "<p>None.</p>"}'
            + f'<h2>Flagged on this board</h2><ul>{flag_items}{extra_flags}</ul>'
            '<p class="small">The full register is on <a href="../flagged.html">Flagged for Review</a>.</p>'
            f'<h2>How the line is made</h2><p class="lede">{esc(method)}</p>')
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page(f"Next-day board {research['board_date']}", body))
    for s in SPORTS:
        rs = by_sport[s]
        h = [r for r in rs if r["confidence"] == "HIGH"]
        sb = (f'<h1>{esc(s)} &middot; next-day board</h1>'
              f'<p class="lede">{len(rs)} OLBG rows, {len(h)} HIGH. {esc(shortfall.get(s, "")) if len(h) < TARGET else ""}</p>'
              + (f'<h2>HIGH picks</h2><div class="cards">{"".join(card(r) for r in h)}</div>' if h else "")
              + ('<h2>All rows</h2>' + table(rs) if rs else '<p>OLBG listed no rows for this sport in the capture.</p>')
              + f'<p class="small">{esc(method)}</p>')
        with open(os.path.join(out_dir, f"{slug(s)}.html"), "w", encoding="utf-8") as fh:
            fh.write(page(f"{s} next-day board", sb))
    return {"rows": len(rows), "high": len(highs), "medium": len(meds),
            "high_by_sport": {s: sum(r["confidence"] == "HIGH" for r in by_sport[s]) for s in SPORTS}}


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "site")), indent=1))
