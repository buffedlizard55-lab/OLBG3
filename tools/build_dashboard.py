#!/usr/bin/env python3
"""build_dashboard.py — the reader-facing summary site.

Why this exists
---------------
The repository had accumulated several overlapping views of the same research (a "feed track",
a "board track", an `/olbg/` audit track, a brief-coverage accounting page). Each was accurate
and each had its own navigation, and none of them answered the two questions a reader actually
opens the site with: *what are today's picks* and *where are the write-ups*.

This builder reads the same committed JSON the rest of the pipeline writes and produces one
small, consistent site:

  index.html            executive summary: the high-confidence picks, the day's numbers, and
                        a coverage table that names every shortfall instead of hiding it
  picks.html            every selection, sorted by confidence, filterable, with the write-up
                        inline behind a disclosure for each high-confidence pick
  matches.html          every captured fixture with our originated lines and its sources
  written.html          the complete written predictions, grouped by sport
  sports/<slug>.html    one page per sport: fixtures, picks, write-ups, sources
  review.html           the flag register (irregularities, unverified values, shortfalls)
  sources.html          how a row earns a price and a grade, and the full source registry

Every row carries a source link. A value that no source states is printed as a dash and is
listed on review.html; nothing here is inferred from a neighbouring row.

Output is written to BOTH site/ (the Pages artifact) and the repository root (the legacy branch
publisher serves the root). That makes the step idempotent regardless of whether
scripts/build_site.py --snapshot runs before or after it.

Usage
-----
    python tools/build_dashboard.py
"""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"

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
ICON = {
    "Cricket": "🏏", "Tennis": "🎾", "Basketball": "🏀", "Snooker": "🎱", "Darts": "🎯",
    "Rugby Union": "🏉", "Rugby League": "🏉", "Ice Hockey": "🏒", "Baseball": "⚾",
    "Volleyball": "🏐", "Handball": "🤾", "Golf": "⛳", "Motor Racing": "🏎️",
    "Gaelic Football": "🥎", "Greyhounds": "🐕",
}
SIDE_MARKET = {
    "match_winner": "Match winner", "handicap": "Handicap", "total": "Total",
}

E = html.escape


def load(name, default):
    path = DATA / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def money(price):
    """Decimal price -> (decimal, american) strings, or dashes when absent."""
    if price in (None, ""):
        return "—", "—"
    try:
        price = float(price)
    except (TypeError, ValueError):
        return "—", "—"
    if price >= 2.0:
        american = f"+{round((price - 1) * 100):d}"
    else:
        american = f"-{round(100 / (price - 1)):d}"
    return f"{price:.2f}", american


def conf_chip(conf):
    return f'<span class="chip chip-{E(conf)}">{E(conf.upper())}</span>'


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def clock(value):
    moment = parse_iso(value)
    return moment.strftime("%d %b %H:%M") if moment else "—"


def nav(active, depth=0):
    pre = "../" * depth
    items = [("index.html", "Summary"), ("picks.html", "Picks"), ("matches.html", "All matches"),
             ("written.html", "Write-ups"), ("sources.html", "Method & sources"),
             ("review.html", "Flagged for review")]
    out = []
    for href, label in items:
        cls = ' class="active"' if href == active else ""
        out.append(f'<a href="{pre}{href}"{cls}>{label}</a>')
    return "".join(out)


def head(title, active, depth=0, extra=""):
    pre = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · OLBG Match Board</title>
<meta name="description" content="A reverse-engineered OLBG fixture board across 15 sports with our own originated prices, a stated confidence grade and a written prediction for every high-confidence pick.">
<link rel="stylesheet" href="{pre}assets/dash.css">
</head><body>
<header class="top">
  <a class="brand" href="{pre}index.html"><span class="mark">◧</span> OLBG Match Board</a>
  <nav>{nav(active, depth)}</nav>
</header>
<main>
{extra}"""


def foot(extra="", depth=0):
    pre = "../" * depth
    return f"""{extra}
</main>
<footer>
  <p><strong>What this site is.</strong> An independent research project that reads OLBG's public
  betting-tips listings for 15 sports, originates its own prices for every captured fixture, grades a
  selection and writes a sourced prediction for the high-confidence ones. It is not affiliated with
  OLBG and it publishes no guaranteed outcomes. 18+.</p>
  <p><strong>What a price here means.</strong> "Our price" is our own originated line, not a bookmaker
  quote and not a promise. "OLBG price" is the number the listing printed when it was captured. Where the
  two disagree, that disagreement is the opinion being published.</p>
  <p><strong>Where the rest of the record lives.</strong>
  <a href="{pre}brief.html">Brief coverage</a> ·
  <a href="{pre}predictions.html">Legacy predictions track</a> ·
  <a href="{pre}verification.html">Verification log</a> ·
  <a href="{pre}flagged.html">Full flag register</a> ·
  <a href="{pre}olbg/index.html">OLBG lines audit</a> ·
  <a href="{pre}method.html">Method</a> ·
  <a href="{pre}data.json">Raw feed data</a></p>
</footer>
<script src="{pre}assets/release.js"></script>
</body></html>
"""


# ---------------------------------------------------------------- data assembly

class Board:
    def __init__(self):
        self.rows = load("lines.json", [])
        self.matches = {m["id"]: m for m in load("matches.json", [])}
        self.preds = {p["match_id"]: p for p in load("predictions-olbg.json", {"predictions": []})["predictions"]}
        self.flags = load("flagged.json", {"items": []}).get("items", [])
        self.meta = load("meta.json", {})
        self.pub = load("publication.json", {})
        self.now = parse_iso(self.pub.get("publication_as_of")) or datetime.now(timezone.utc)

    def match(self, row):
        return self.matches.get(row["match_id"], {})

    def start(self, row):
        rel = row.get("release") or {}
        return parse_iso(rel.get("start_utc")) or parse_iso(self.match(row).get("olbg_start_utc"))

    def start_basis(self, row):
        rel = row.get("release") or {}
        if rel.get("start_utc"):
            return "official"
        if self.match(row).get("olbg_start_utc"):
            return "OLBG card"
        return "none"

    def upcoming(self, row):
        start = self.start(row)
        return start is not None and start > self.now

    def announced(self, row):
        """Upcoming by OLBG's own clock, even where the official clock is not yet certified."""
        return self.upcoming(row)

    def ordered(self, rows):
        return sorted(rows, key=lambda r: (self.start(r) or datetime.max.replace(tzinfo=timezone.utc)))

    def by_sport(self, sport):
        return [r for r in self.rows if r["sport"] == sport]

    def upcoming_rows(self):
        return self.ordered([r for r in self.rows if self.upcoming(r)])

    def high(self):
        return [r for r in self.upcoming_rows() if r["confidence"] == "high"]

    def pred(self, row):
        return self.preds.get(row["match_id"])

    def source_links(self, row, limit=3):
        out = []
        for src in (self.pred(row) or {}).get("sources", [])[:limit]:
            short = src["label"].split("—")[0].split(",")[0].split("(")[0].strip()
            if len(short) > 46:
                short = short[:43].rstrip() + "…"
            out.append(f'<a href="{E(src["url"])}" rel="noopener nofollow" target="_blank">{E(short)}</a>')
        rel = row.get("release") or {}
        if rel.get("source"):
            out.append(f'<a href="{E(rel["source"])}" rel="noopener nofollow" target="_blank">Official clock</a>')
        m = self.match(row)
        if m.get("olbg_url"):
            out.append(f'<a href="{E(m["olbg_url"])}" rel="noopener nofollow" target="_blank">OLBG listing</a>')
        return out


def selection_text(row):
    pick = row.get("our_pick") or "—"
    market = ((row.get("inputs") or {}).get("olbg_market") or "").lower()
    if "money" in market or market in ("", "win match"):
        label = "to win"
    elif "handicap" in market or "spread" in market or "pointspread" in market:
        label = "on the handicap"
    elif "total" in market:
        label = "on the total"
    else:
        label = "to win"
    return f"{pick} {label}".strip()


def line_cells(row):
    """Our originated handicap and total, printed only where the model produced them."""
    hc = "—"
    if row.get("our_handicap_line") is not None:
        side = row.get("our_handicap_side") or ""
        hc = f"{side} {row['our_handicap_line']:g} {row.get('our_handicap_unit') or ''}".strip()
    tot = "—"
    if row.get("our_total_line") is not None:
        tot = f"{row.get('our_total_side') or ''} {row['our_total_line']:g} {row.get('our_total_unit') or ''}".strip()
    return hc, tot


# ---------------------------------------------------------------- shared fragments

def olbg_price_text(row, match):
    """OLBG's printed price, labelled with the side it was printed for when that is not our pick."""
    odds = match.get("olbg_odds_decimal")
    if odds in (None, ""):
        return "—"
    side = (match.get("olbg_consensus_selection") or "").strip()
    if side and side.lower() != (row.get("our_pick") or "").lower():
        return f"{float(odds):.2f} ({side})"
    return f"{float(odds):.2f}"


def pick_row(board, row, show_sources=True, depth=0):
    """One row of the primary pick table. Kept on one line where the release script needs it."""
    m = board.match(row)
    dec, us = money(row.get("our_price_pick"))
    olbg_txt = olbg_price_text(row, m)
    sources = " · ".join(board.source_links(row)) if show_sources else ""
    start = board.start(row)
    basis = board.start_basis(row)
    when = start.strftime("%a %d %b · %H:%M UTC") if start else "—"
    note = "" if basis == "official" else '<span class="tag tag-warn">OLBG clock</span>'
    conf = row.get("confidence") or "low"
    high_attrs = ' data-current-high="true"' if conf == "high" else ""
    band = ('<span class="chip chip-band">in band</span>' if conf == "high" else "")
    anchor = f'../' * depth + f'written.html#{row["match_id"]}'
    return (f'<tr{high_attrs} data-sport="{E(row["sport"])}" data-conf="{E(conf)}">'
            f'<td class="nowrap">{E(when)} {note}</td>'
            f'<td>{ICON.get(row["sport"], "•")} {E(row["sport"])}</td>'
            f'<td><strong>{E(row["event_name"])}</strong><br><span class="muted">{E((m.get("competition") or "")[:70] or "Competition not printed by the listing")}</span></td>'
            f'<td class="pick">{E(selection_text(row))}</td>'
            f'<td class="num">{E(dec)}<br><span class="muted">{E(us)}</span></td>'
            f'<td class="num">{E(olbg_txt)}</td>'
            f'<td>{conf_chip(conf)} {band}</td>'
            f'<td class="src">{sources}'
            + (f'<br><a href="{anchor}">Read the write-up</a>' if conf == "high" and board.pred(row) else "")
            + '</td></tr>')


def pick_table(board, rows, tid="picks", depth=0):
    prefix = "../" * depth
    body = "".join(pick_row(board, r, depth=depth) for r in rows)
    if not body:
        body = ('<tr><td colspan="8">No upcoming fixture in this view. The reason is on the '
                f'<a href="{prefix}review.html">Flagged for review</a> page — a sport with no live listing, a '
                'fixture whose official clock is not yet certified, or a match that has started.</td></tr>')
    return f"""<div class="table-wrap"><table id="{tid}">
<thead><tr><th>Starts (UTC)</th><th>Sport</th><th>Match</th><th>Our pick</th>
<th>Our price</th><th>OLBG price</th><th>Confidence</th><th>Sources</th></tr></thead>
<tbody>{body}</tbody></table></div>"""


def prose_card(board, row, depth=0):
    pred = board.pred(row)
    if not pred:
        return ""
    m = board.match(row)
    srcs = "".join(
        f'<li><a href="{E(s["url"])}" rel="noopener nofollow" target="_blank">{E(s["label"])}</a></li>'
        for s in pred.get("sources", []))
    dec, us = money(row.get("our_price_pick"))
    start = board.start(row)
    status = pred.get("status")
    badge = conf_chip(row.get("confidence") or "low")
    label = "Reasoning published" if status == "high" else "Analysis only — not a published pick"
    return f"""<article class="card writeup" id="{E(row['match_id'])}">
  <header class="card-head">
    <div>
      <p class="eyebrow">{ICON.get(row['sport'], '•')} {E(row['sport'])} · {E(m.get('competition') or 'competition not printed')}</p>
      <h3>{E(row['event_name'])}</h3>
      <p class="muted">{E(start.strftime('%A %d %B %Y · %H:%M UTC')) if start else 'start time not established'}</p>
    </div>
    <div class="card-pick">
      <span class="muted">Selection</span>
      <strong>{E(selection_text(row))}</strong>
      <span class="muted">{E(dec)} ({E(us)})</span>
      {badge}
    </div>
  </header>
  <p class="lede">{E(label)}</p>
  <p>{E(pred.get('text', ''))}</p>
  <details><summary>Sources for every fact above</summary><ul class="links">{srcs}
    <li><a href="{E(m.get('olbg_url') or 'https://www.olbg.com/betting-tips')}" rel="noopener nofollow" target="_blank">OLBG listing this fixture was captured from</a></li>
  </ul></details>
</article>"""


def coverage_rows(board):
    out = []
    for sport in SPORTS:
        rows = board.by_sport(sport)
        up = [r for r in rows if board.upcoming(r)]
        high = [r for r in up if r["confidence"] == "high"]
        written = [r for r in high if board.pred(r)]
        if not rows:
            status = '<span class="tag tag-warn">no live listing today</span>'
            why = "OLBG served no tip card on this sport's listing at capture time."
        elif not up:
            status = '<span class="tag tag-warn">nothing upcoming</span>'
            why = "Every captured card had already started."
        elif len(written) >= 5:
            status = '<span class="tag tag-ok">target met</span>'
            why = ""
        else:
            status = f'<span class="tag tag-warn">{len(written)}/5</span>'
            why = ("captured, but fewer than five selections passed the confidence, price-band and "
                   "official-clock gates with a written prediction.")
        out.append(
            f'<tr><td>{ICON.get(sport, "•")} <a href="sport/{SLUG[sport]}.html">{E(sport)}</a></td>'
            f'<td class="num">{len(rows)}</td><td class="num">{len(up)}</td>'
            f'<td class="num">{len([r for r in up if r.get("our_pick")])}</td>'
            f'<td class="num">{len(written)}</td><td>{status}<br><span class="muted">{E(why)}</span></td></tr>')
    return "".join(out)


# ---------------------------------------------------------------- pages

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_index(board):
    high = board.high()
    upcoming = board.upcoming_rows()
    written = [r for r in high if board.pred(r)]
    sports_with = sorted({r["sport"] for r in upcoming})
    target_sports = [s for s in SPORTS if len([r for r in high if r["sport"] == s and board.pred(r)]) >= 5]
    capture = board.meta.get("harvest_completed_utc") or "not recorded"
    built = board.now.strftime("%Y-%m-%d %H:%M UTC")

    top = "".join(pick_row(board, r) for r in high)
    if not top:
        top = ('<tr><td colspan="8">No high-confidence selection is live at this build clock. '
               'Every captured fixture is listed on <a href="matches.html">All matches</a> with its grade.</td></tr>')

    kpis = f"""
<section class="kpis">
  <article><span>Fixtures captured</span><strong>{len(board.rows)}</strong><small>across {len(sports_with)} of 15 sports</small></article>
  <article><span>Still upcoming</span><strong>{len(upcoming)}</strong><small>fixtures with a start ahead of this build</small></article>
  <article class="accent"><span>High-confidence picks</span><strong data-high-count>{len(written)}</strong><small>each with a written prediction and sources</small></article>
  <article><span>Sports meeting the 5-a-day target</span><strong>{len(target_sports)}</strong><small>{E(", ".join(target_sports)) if target_sports else "shortfall disclosed below"}</small></article>
</section>"""

    lead = board.high()[0] if board.high() else None
    lead_block = ""
    if lead:
        m = board.match(lead)
        pred = board.pred(lead) or {}
        dec, us = money(lead.get("our_price_pick"))
        start = board.start(lead)
        lead_block = f"""
<section class="lead">
  <div>
    <p class="eyebrow">Start here</p>
    <h2>{E(lead['event_name'])} <span class="muted">· {E(lead['sport'])}</span></h2>
    <p class="big">Pick: <strong>{E(selection_text(lead))}</strong> at {E(dec)} ({E(us)})</p>
    <p>{E((pred.get('text') or '')[:340])}{'…' if len(pred.get('text') or '') > 340 else ''}</p>
    <p class="muted">{E(start.strftime('%A %d %B · %H:%M UTC')) if start else ''} · {E(m.get('competition') or '')}</p>
    <p><a class="button" href="written.html#{E(lead['match_id'])}">Read the full write-up</a>
       <a class="button ghost" href="picks.html">See all {len(written)} high-confidence picks</a></p>
  </div>
</section>"""

    page = head("Today's picks, in one place", "index.html") + f"""
<section class="hero">
  <p class="eyebrow">Executive summary · {board.now.strftime('%A %d %B %Y')}</p>
  <h1>Today's picks, and exactly where the reasoning is.</h1>
  <p class="intro">OLBG's listings captured at <strong>{E(capture)}</strong>, our own lines originated for every
  fixture, and every high-confidence selection written up with the official source behind each fact.
  This page is the summary; the tables below and the six pages in the menu are the detail.</p>
  <p class="stamp">Page built {E(built)} · listing capture {E(capture)} · all times UTC</p>
</section>
{kpis}
{lead_block}
<section>
  <h2>High-confidence picks <span class="count">{len(written)}</span></h2>
  <p class="muted">A pick is graded <strong>HIGH</strong> only when its official start is checked and ahead of now,
  its price sits inside the -250 to +10000 band, its win probability is below 70%, and a written prediction with
  sources exists. <strong>Our price</strong> is the line we originated; <strong>OLBG price</strong> is what the
  listing printed. The two differ on purpose.</p>
  <div class="table-wrap"><table>
  <thead><tr><th>Starts (UTC)</th><th>Sport</th><th>Match</th><th>Our pick</th>
  <th>Our price</th><th>OLBG price</th><th>Confidence</th><th>Sources</th></tr></thead>
  <tbody>{top}</tbody></table></div>
</section>
<section>
  <h2>Coverage, sport by sport</h2>
  <p class="muted">The brief asks for five written high-confidence predictions per sport per day. This table is the
  honest scorecard: fixtures captured, fixtures still upcoming, selections originated, and how many of those carry a
  full write-up. A sport below five says why in the same cell.</p>
  <div class="table-wrap"><table>
  <thead><tr><th>Sport</th><th>Captured</th><th>Upcoming</th><th>Priced</th><th>Written HIGH</th><th>Status</th></tr></thead>
  <tbody>{coverage_rows(board)}</tbody></table></div>
</section>
<section class="cards">
  <a class="card" href="picks.html"><h3>Picks →</h3><p>Every selection sorted by confidence, filterable by sport, with the write-up inline.</p></a>
  <a class="card" href="matches.html"><h3>All matches →</h3><p>Every captured fixture, our money line, handicap and total, and its sources.</p></a>
  <a class="card" href="written.html"><h3>Write-ups →</h3><p>The full predictions, one card per match, each fact linked to an official page.</p></a>
  <a class="card" href="sources.html"><h3>Method &amp; sources →</h3><p>How a row earns a price and a grade, and every source used.</p></a>
  <a class="card" href="review.html"><h3>Flagged for review →</h3><p>Irregularities, unverified values and the honest shortfalls.</p></a>
</section>
""" + foot()
    write(SITE / "index.html", page)
    write(ROOT / "index.html", page)


def build_picks(board):
    rows = sorted(board.upcoming_rows(), key=lambda r: ({"high": 0, "medium": 1, "low": 2}[r["confidence"]],
                                                       board.start(r) or datetime.max.replace(tzinfo=timezone.utc)))
    options = "".join(f'<option value="{E(s)}">{E(s)}</option>' for s in SPORTS if any(r["sport"] == s for r in rows))
    table = pick_table(board, rows)
    page = head("Every pick", "picks.html") + f"""
<section class="hero small">
  <p class="eyebrow">All selections</p>
  <h1>Every pick, highest confidence first</h1>
  <p class="intro">Each row is one captured fixture with our originated selection. Filter by sport or by grade;
  high-confidence rows link straight to the reasoning.</p>
</section>
<div class="controls">
  <label>Sport <select id="sport"><option value="">All sports</option>{options}</select></label>
  <label>Confidence <select id="conf"><option value="">All grades</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
  <label class="grow">Search <input id="search" type="search" placeholder="Team, player, competition…"></label>
</div>
<p class="muted" id="tally"></p>
{table}
<script>
const rows=[...document.querySelectorAll('#picks tbody tr[data-sport]')];
const s=document.getElementById('sport'),c=document.getElementById('conf'),q=document.getElementById('search'),t=document.getElementById('tally');
function apply(){{let n=0;rows.forEach(r=>{{const ok=(!s.value||r.dataset.sport===s.value)&&(!c.value||r.dataset.conf===c.value)&&(!q.value||r.textContent.toLowerCase().includes(q.value.toLowerCase()));r.hidden=!ok;if(ok)n++;}});t.textContent=n+' of '+rows.length+' selections shown';}}
[s,c,q].forEach(el=>el.addEventListener('input',apply));apply();
</script>
""" + foot()
    write(SITE / "picks.html", page)
    write(ROOT / "picks.html", page)


def build_matches(board):
    rows = board.upcoming_rows()
    body = []
    for r in rows:
        m = board.match(r)
        dec, us = money(r.get("our_price_pick"))
        fair = f"{r['our_fair_odds']:.2f}" if r.get("our_fair_odds") else "—"
        hc, tot = line_cells(r)
        start = board.start(r)
        basis = board.start_basis(r)
        olbg_txt = olbg_price_text(r, m)
        srcs = " · ".join(board.source_links(r))
        body.append(
            f'<tr data-sport="{E(r["sport"])}">'
            f'<td>{ICON.get(r["sport"], "•")} {E(r["sport"])}</td>'
            f'<td><strong>{E(r["event_name"])}</strong><br><span class="muted">{E(m.get("competition") or "")}</span></td>'
            f'<td class="nowrap">{E(start.strftime("%d %b %H:%M") if start else "—")}<br>'
            f'<span class="tag {"tag-ok" if basis == "official" else "tag-warn"}">{"official" if basis == "official" else basis}</span></td>'
            f'<td class="pick">{E(selection_text(r))}</td>'
            f'<td class="num">{E(dec)}<br><span class="muted">{E(us)}</span></td>'
            f'<td class="num">{E(fair)}</td><td class="num">{E(olbg_txt)}</td>'
            f'<td>{E(hc)}</td><td>{E(tot)}</td><td>{conf_chip(r.get("confidence") or "low")}</td>'
            f'<td class="src">{srcs}</td></tr>')
    if not body:
        body = ['<tr><td colspan="11">No upcoming fixture at this build clock.</td></tr>']
    page = head("All matches and originated lines", "matches.html") + f"""
<section class="hero small">
  <p class="eyebrow">The board</p>
  <h1>Every captured fixture, with our own line on it</h1>
  <p class="intro">Our price is the line we originate from the captured market and our own adjustment. The OLBG
  price is what the listing printed. Handicap and total are printed only where a line was originated; a dash means
  no line, never zero.</p>
</section>
<div class="controls">
  <label>Sport <select id="sport"><option value="">All sports</option>{''.join(f'<option>{E(s)}</option>' for s in SPORTS if any(r['sport'] == s for r in rows))}</select></label>
  <label class="grow">Search <input id="search" type="search" placeholder="Team, player, competition…"></label>
</div>
<p class="muted" id="tally"></p>
<div class="table-wrap"><table id="matches">
<thead><tr><th>Sport</th><th>Match</th><th>Starts</th><th>Our pick</th><th>Our price</th>
<th>Our fair odds</th><th>OLBG price</th><th>Our handicap</th><th>Our total</th><th>Grade</th><th>Sources</th></tr></thead>
<tbody>{''.join(body)}</tbody></table></div>
<script>
const rows=[...document.querySelectorAll('#matches tbody tr[data-sport]')];
const s=document.getElementById('sport'),q=document.getElementById('search'),t=document.getElementById('tally');
function apply(){{let n=0;rows.forEach(r=>{{const ok=(!s.value||r.dataset.sport===s.value)&&(!q.value||r.textContent.toLowerCase().includes(q.value.toLowerCase()));r.hidden=!ok;if(ok)n++;}});t.textContent=n+' of '+rows.length+' fixtures shown';}}
[s,q].forEach(el=>el.addEventListener('input',apply));apply();
</script>
""" + foot()
    write(SITE / "matches.html", page)
    write(ROOT / "matches.html", page)


def build_written(board):
    upcoming = board.upcoming_rows()
    high = [r for r in upcoming if r["confidence"] == "high" and board.pred(r)]
    others = [r for r in upcoming if r["confidence"] != "high" and board.pred(r)]
    groups = []
    for sport in SPORTS:
        rows = [r for r in high if r["sport"] == sport]
        if rows:
            groups.append(f'<h2 id="{E(SLUG[sport])}">{ICON.get(sport,"•")} {E(sport)}'
                          f' <span class="count">{len(rows)}</span></h2>' +
                          "".join(prose_card(board, r) for r in rows))
    analysis = ""
    if others:
        analysis = ('<h2>Analysis pieces (published, not graded high)</h2><p class="muted">These carry a selection and '
                    'sources but did not clear the confidence, price-band or clock gate, so they are labelled analysis rather '
                    'than picks. They are kept because the reasoning is still checkable.</p>' +
                    "".join(prose_card(board, r) for r in others))
    page = head("Written predictions", "written.html") + f"""
<section class="hero small">
  <p class="eyebrow">The reasoning</p>
  <h1>Written predictions, one per high-confidence pick</h1>
  <p class="intro">{len(high)} pieces, each at least 30 words, each naming the selection, the current form, the recent
  results, the match-specific numbers and any injury the official source states. Every fact is linked at the foot of
  its card.</p>
</section>
{''.join(groups) or '<p>No high-confidence write-up is live at this build clock.</p>'}
{analysis}
""" + foot()
    write(SITE / "written.html", page)
    write(ROOT / "written.html", page)


def build_sport(board, sport):
    rows = board.by_sport(sport)
    up = [r for r in board.ordered(rows) if board.upcoming(r)]
    high = [r for r in up if r["confidence"] == "high" and board.pred(r)]
    built = board.now.strftime("%Y-%m-%d %H:%M UTC")
    depth = 1
    page = head(f"{sport} picks and matches", "sport/" + SLUG[sport] + ".html", depth=1) + f"""
<section class="hero small">
  <p class="eyebrow"><a href="../index.html">Summary</a> › {E(sport)}</p>
  <h1>{ICON.get(sport,"•")} {E(sport)}</h1>
  <p class="intro">{len(rows)} fixture{'' if len(rows)==1 else 's'} captured from OLBG's {E(sport)} listing,
  {len(up)} still upcoming, {len(high)} with a written high-confidence prediction. Built {E(built)}.</p>
</section>
<section>
  <h2>Fixtures and our lines</h2>
  {pick_table(board, up, tid='sportpicks', depth=1)}
</section>
<section>
  <h2>Write-ups</h2>
  {''.join(prose_card(board, r) for r in high) or '<p class="muted">No high-confidence write-up for this sport at this build clock. The reason is recorded in the coverage table on the summary page and on the review page.</p>'}
</section>
""" + foot(depth=1)
    write(SITE / "sport" / f"{SLUG[sport]}.html", page)
    write(ROOT / "sport" / f"{SLUG[sport]}.html", page)


def build_review(board):
    flags = board.flags
    rows = []
    for item in flags[-40:]:
        rows.append(
            f'<tr><td class="nowrap">{E(item.get("id",""))}</td>'
            f'<td>{E(item.get("severity",""))}</td>'
            f'<td><strong>{E(item.get("title",""))}</strong><br><span class="muted small">{E((item.get("detail") or "")[:320])}</span></td></tr>')
    unverified = [r for r in board.upcoming_rows() if board.start_basis(r) != "official"]
    page = head("Flagged for review", "review.html") + f"""
<section class="hero small">
  <p class="eyebrow">Open items</p>
  <h1>Flagged for review</h1>
  <p class="intro">Everything this project could not confirm, could not fill in, or found contradictory
  is published here rather than smoothed over. A blank value stays blank.</p>
</section>
<section>
  <h2>Unverified start clocks <span class="count">{len(unverified)}</span></h2>
  <p class="muted">These fixtures are listed by OLBG and priced here, but no official source has yet confirmed
  their exact start. They cannot be graded high, and the table says so.</p>
  <div class="table-wrap"><table><thead><tr><th>Sport</th><th>Match</th><th>OLBG clock</th><th>Source</th></tr></thead><tbody>
  {''.join(f'<tr><td>{E(r["sport"])}</td><td>{E(r["event_name"])}</td><td class="nowrap">{E((board.start(r).strftime("%d %b %H:%M") if board.start(r) else "—"))}</td><td class="src">{board.source_links(r)[-1] if board.source_links(r) else "—"}</td></tr>' for r in unverified[:60])}
  </tbody></table></div>
</section>
<section>
  <h2>The register <span class="count">{len(flags)}</span></h2>
  <p class="muted">Newest 40 entries. The complete register, with the full reasoning, is on the
  <a href="flagged.html">legacy flag page</a>.</p>
  <div class="table-wrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Finding</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="3">No open items.</td></tr>'}</tbody></table></div>
</section>
""" + foot()
    write(SITE / "review.html", page)
    write(ROOT / "review.html", page)


def build_sources(board):
    used = {}
    for pred in board.preds.values():
        for s in pred.get("sources", []):
            used[s["url"]] = s["label"]
    for r in board.rows:
        src = (r.get("release") or {}).get("source")
        if src:
            used.setdefault(src, f"Official start clock — {r['sport']}")
    listing = "".join(f'<li><a href="{E(u)}" rel="noopener nofollow" target="_blank">{E(l)}</a></li>'
                      for u, l in sorted(used.items()))
    page = head("Method and sources", "sources.html") + f"""
<section class="hero small">
  <p class="eyebrow">How this works</p>
  <h1>Method, rules and every source used</h1>
</section>
<section class="prose">
  <h2>1. Capture</h2>
  <p>Each day a bounded, robots-aware read of OLBG's public betting-tips listings for the 15 in-scope
  sports is captured verbatim: HTTP status, byte count, hash and the served HTML. Fixtures, the printed
  clock, the card's own machine-readable start attribute, the market, the consensus selection and the price
  are copied out of that HTML. Nothing is inferred from a slug or a neighbouring card.</p>
  <h2>2. Originate a line</h2>
  <p>For every captured fixture we originate a money line from a shrunk version of the captured consensus
  with a per-sport home edge, then derive a handicap and a total from the same distribution. These are our
  own numbers, published next to OLBG's printed price so the disagreement is visible.</p>
  <h2>3. Grade the pick</h2>
  <p><strong>HIGH</strong> requires all four: an official, timezone-qualified start that is checked and still
  ahead; a price strictly inside -250 to +10000; a win probability below 70% so heavy chalk is never dressed
  up as insight; and a written prediction of at least 30 words whose facts are linked.</p>
  <p><strong>MEDIUM</strong> and <strong>LOW</strong> are published too, with the reason for the lower grade
  printed beside them. A sport with nothing meeting the bar says so on the summary page.</p>
  <h2>4. What is deliberately not done</h2>
  <ul class="links">
    <li>No value is filled in from a similar fixture, a previous season or an assumption.</li>
    <li>No clock is converted from an unlabelled local time; an unqualified time stays unverified.</li>
    <li>No injury is mentioned unless an official league, club or governing-body source states it.</li>
    <li>No outcome is presented as certain, and no past result is inferred from a clock.</li>
  </ul>
  <h2>Sources used by the live board</h2>
  <ul class="links">{listing}</ul>
</section>
""" + foot()
    write(SITE / "sources.html", page)
    write(ROOT / "sources.html", page)


CSS = """
:root{--bg:#f7f8fa;--panel:#fff;--ink:#12161c;--muted:#67707d;--line:#e3e7ee;--brand:#1449d4;
--brand-soft:#eaf0ff;--high:#0a7d3f;--medium:#9a6200;--low:#5d6673;--warn:#a4400b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
.top{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;
padding:14px 24px;background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.brand{font-weight:700;font-size:18px;color:var(--ink)}.brand .mark{color:var(--brand)}
nav{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}
nav a{color:var(--muted);font-weight:600}nav a.active{color:var(--brand)}
main{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:clamp(28px,4vw,44px);line-height:1.15;margin:6px 0 12px;letter-spacing:-.02em}
h2{font-size:22px;margin:38px 0 10px}h3{font-size:17px;margin:0 0 6px}
.eyebrow{text-transform:uppercase;letter-spacing:.08em;font-size:12px;font-weight:700;color:var(--brand);margin:0 0 4px}
.intro{font-size:18px;color:#2b333f;max-width:70ch}
.stamp,.muted{color:var(--muted);font-size:14px}
.small{font-size:13px}
.hero{padding:8px 0 4px}.hero.small h1{font-size:clamp(24px,3vw,34px)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:24px 0}
.kpis article{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.kpis span{display:block;font-size:13px;color:var(--muted);font-weight:600}
.kpis strong{display:block;font-size:34px;line-height:1.2;margin:4px 0}
.kpis small{color:var(--muted);font-size:12px}
.kpis .accent{background:var(--brand-soft);border-color:#cfdcff}
.lead{background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--brand);border-radius:14px;
padding:20px 22px;margin:18px 0 6px}
.lead .big{font-size:18px}
.button{display:inline-block;background:var(--brand);color:#fff;padding:10px 16px;border-radius:10px;font-weight:600;margin:6px 8px 0 0}
.button.ghost{background:transparent;color:var(--brand);border:1px solid var(--brand)}
.table-wrap{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:11px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:#f1f4f9;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#4b5563;position:sticky;top:0}
tbody tr:hover{background:#fafbfd}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.pick{font-weight:700;color:#0d2a66}
td.src{font-size:12.5px;color:var(--muted)}
.nowrap{white-space:nowrap}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}
.chip-high{background:#e4f6ea;color:var(--high)}
.chip-medium{background:#fdf0d9;color:var(--medium)}
.chip-low{background:#eef0f4;color:var(--low)}
.chip-band{background:#eef2ff;color:#2a3fa0}
.tag{display:inline-block;padding:1px 7px;border-radius:6px;font-size:11px;font-weight:700}
.tag-ok{background:#e4f6ea;color:var(--high)}.tag-warn{background:#fdeee3;color:var(--warn)}
.count{background:var(--brand-soft);color:var(--brand);border-radius:999px;padding:2px 10px;font-size:14px;vertical-align:middle}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:14px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;color:var(--ink)}
.card:hover{border-color:#c7d3ea;text-decoration:none}
.card p{color:var(--muted);font-size:14px;margin:0}
.writeup{margin:16px 0;padding:0;overflow:hidden}
.card-head{display:flex;justify-content:space-between;gap:18px;padding:16px 18px;background:#fbfcfe;border-bottom:1px solid var(--line);flex-wrap:wrap}
.card-head h3{margin:2px 0 2px}
.card-pick{text-align:right;display:flex;flex-direction:column;gap:2px;min-width:190px}
.card-pick strong{font-size:16px;color:#0d2a66}
.writeup>p{padding:0 18px}
.writeup .lede{font-size:13px;text-transform:uppercase;letter-spacing:.06em;font-weight:700;color:var(--muted);padding-top:14px}
.writeup details{padding:0 18px 18px}
.writeup summary{cursor:pointer;color:var(--brand);font-weight:600;font-size:14px}
.links{margin:8px 0 0;padding-left:18px}.links li{margin:4px 0;font-size:14px}
.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:end;margin:14px 0}
.controls label{display:flex;flex-direction:column;font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.controls .grow{flex:1;min-width:220px}
select,input{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:9px;background:#fff;margin-top:4px}
.prose{max-width:78ch}.prose h2{margin-top:28px}
footer{max-width:1180px;margin:0 auto;padding:26px 20px 60px;color:var(--muted);font-size:13.5px;border-top:1px solid var(--line)}
footer p{margin:8px 0}
@media(max-width:640px){.card-head{flex-direction:column}.card-pick{text-align:left}}
"""


def main():
    board = Board()
    SITE.mkdir(exist_ok=True)
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets").mkdir(parents=True, exist_ok=True)
    write(SITE / "assets" / "dash.css", CSS)
    write(ROOT / "assets" / "dash.css", CSS)
    build_index(board)
    build_picks(board)
    build_matches(board)
    build_written(board)
    for sport in SPORTS:
        build_sport(board, sport)
    build_review(board)
    build_sources(board)
    print(f"dashboard: {len(board.rows)} fixtures, {len(board.upcoming_rows())} upcoming, "
          f"{len(board.high())} high, {len([r for r in board.high() if board.pred(r)])} written")


if __name__ == "__main__":
    main()
