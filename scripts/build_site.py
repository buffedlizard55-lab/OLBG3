#!/usr/bin/env python3
"""build_site.py - generates the static GitHub Pages site from data/*.json."""
import json, os, glob, html, shutil, sys
from collections import Counter, defaultdict

from board_dates import (american, in_band, BAND_LOW_US, BAND_HIGH_US, AS_OF, snapshot_utc,
                         snapshot_age_hours)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")          # published artifact root (built by build.py first)
GEN = "2026-10-22"          # latest live OLBG harvest date (S-20261022-A)
BUILT = AS_OF.isoformat()  # this rebuild
CLOCK = snapshot_utc().isoformat().replace("+00:00", "Z")
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)

# One navigation for the whole published site, grouped into four labelled shelves so the
# answer to "where are the picks?" is the first thing the bar says. NAV stays a flat list of
# (file, label) because head() and the tests read it; NAV_GROUPS is what the header renders and
# NAV is derived from it, so a page can never be in one and missing from the other. Every file the
# previous flat list linked is still linked here: this is a regrouping, not a removal, and
# scripts/check_links.py would fail on a page that survived only as a link target.
NAV_GROUPS = [
    ("Picks", [("today.html", "Today's picks"), ("predictions.html", "Written predictions"),
               ("lines.html", "Originated lines & markets")]),
    ("Board", [("index.html", "Dashboard"), ("brief.html", "Brief coverage"),
               ("olbg/index.html", "OLBG lines board")]),
    ("Evidence", [("verification.html", "Verification"), ("source-health.html", "Source health"),
                  ("reconcile.html", "Cross-track review"), ("audit.html", "Audit"),
                  ("discovery.html", "Current discovery"), ("feed-overview.html", "Official feed"),
                  ("matches.html", "Feed matches"), ("coverage.html", "Feed coverage"),
                  ("review.html", "Feed review")]),
    ("Review", [("flagged.html", "Flagged for Review"), ("method.html", "Method & Scope")]),
]
NAV = [(f, t) for _g, _links in NAV_GROUPS for f, t in _links]
ev = json.load(open(os.path.join(ROOT, "data/events.json")))
FIXTURES = ev["events"]
ASSUMPTIONS = ev["assumptions"]
# Outright / race markets (Golf, Motor Racing, Greyhounds, Rugby League, Gaelic football championship).
# These are in scope but are one-selection markets, so they are priced by scripts/build_gap_sports.py
# rather than by the two-sided model and carry their own disclosed field-size prior.
GAP = json.load(open(os.path.join(ROOT, "data/gap_sports.json")))
GAP_ROWS = GAP["rows"]
GAP_MODEL = GAP["model"]
for _r in FIXTURES:
    _r.setdefault("market_type", "fixture")
EVENTS = FIXTURES + GAP_ROWS
PREDS = {p["ref"]: p for p in json.load(open(os.path.join(ROOT, "data/predictions.json")))["predictions"]}
OFF = json.load(open(os.path.join(ROOT, "data/official.json")))

# ---------- unified pick surface (both boards, written predictions only) ----------
# session-3271b876: the two boards each published their own HIGH table, so a reader had to visit
# both to learn what the picks were, and a bare selection with no write-up sat in the same table
# style as a sourced piece. scripts/pick_surface.py merges the boards on the OLBG event id, keeps
# the prose on the card, and labels everything that is not a pick. It reads committed data only.
from pick_surface import collect as _collect_picks, card_html as _pick_card, summary_table as _pick_table, selection_market as _selection_market
from pick_surface import summary_line as _pick_summary_line, words as _wc, prose_problems as _prose_problems

OLBG_LINES = {r["match_id"]: r for r in json.load(open(os.path.join(ROOT, "data/lines.json")))}
OLBG_MATCHES = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "data/matches.json")))}
_olbg_pred_doc = json.load(open(os.path.join(ROOT, "data/predictions-olbg.json")))
OLBG_PREDS_BY_ID = {p["match_id"]: p for p in _olbg_pred_doc["predictions"]}

_capture_meta = json.load(open(os.path.join(ROOT, "data/meta.json")))
with open(os.path.join(ROOT, "data", _capture_meta["harvest_file"])) as _capture_stream:
    _active_event_ids = {line.split("|")[4] for line in _capture_stream
                         if line.strip() and not line.startswith("#")}
PICKS = _collect_picks(EVENTS, PREDS, OLBG_LINES, OLBG_MATCHES, OLBG_PREDS_BY_ID,
                       active_event_ids=_active_event_ids)
PICK_LIVE = [x for x in PICKS if x["state"] == "pick"]
PICK_HELD = [x for x in PICKS if x["state"] != "pick"]
PICK_SUMMARY = _pick_summary_line(PICKS)
PICK_BY_SPORT = {}
for _x in PICK_LIVE:
    PICK_BY_SPORT.setdefault(_x["sport"], []).append(_x)
# The brief's output rule, checked rather than asserted: every published piece is at least 30 words
# and free of the two internal words. Anything that fails is not hidden; it is printed on the page.
PROSE_DEFECTS = []
for _x in PICKS:
    for _k, _t in _x["tracks"].items():
        if _t.get("text"):
            _bad = _prose_problems(_t["text"])
            if _bad:
                PROSE_DEFECTS.append((_x["sport"], _t["ref"], ", ".join(_bad)))


def picks_cards(entries, pre=""):
    return "".join(_pick_card(x, pre) for x in entries)


def sport_picks_block(sport, meta):
    """The picks for one sport, written out, at the top of that sport's page.

    A reader who arrives from the OLBG listing for one sport should not have to hunt the board
    to find out whether we are publishing a pick for it. If we are, the write-up is here. If we
    are not, the mechanical reason is here, taken from the same accounting the brief-coverage
    page publishes, and it links to the register rather than to silence.
    """
    rows = PICK_BY_SPORT.get(sport) or []
    if rows:
        return (f'<h2>Written picks for {e(sport)} ({len(rows)})</h2>'
                f'<p class="legend">Selection, price and the full write-up are on the card; the price is our own '
                f'originated line, not a bookmaker quote. Older pieces for this sport are on '
                f'<a href="../predictions.html">Written predictions</a>, and the second board&rsquo;s own '
                f'line for every fixture it prices is on <a href="../olbg/picks.html">the OLBG lines board</a>.</p>'
                + picks_cards(rows, "../"))
    held = [x for x in PICK_HELD if x["sport"] == sport]
    why = ""
    try:
        acct = next((x for x in BRIEF["sports"] if x["sport"] == sport), None)
        if acct and acct.get("reasons"):
            why = acct["reasons"][0]
    except Exception:
        why = ""
    return ('<h2>Written picks for ' + e(sport) + ' (0)</h2>'
            '<p class="legend">No high-confidence written pick for this sport passes the release gates at this build.'
            + (f' The board&rsquo;s own accounting gives the mechanical reason: {e(why)}.' if why else '')
            + (' Graded HIGH and held back: ' + str(len(held)) + ' fixture(s), each listed with its reason on '
               '<a href="../today.html#written-picks">Today&rsquo;s picks</a>.' if held else '')
            + ' Nothing here is promoted to fill a quota; unconfirmed values stay blank and are on '
              '<a href="../flagged.html">Flagged for Review</a>.</p>')


def picks_sport_sections(entries_by_sport, order=None):
    out = []
    for sport in (order or SPORT_ORDER):
        rows = entries_by_sport.get(sport) or []
        if not rows:
            continue
        out.append(f'<h3 class="pick-sport-head">{e(sport)} '
                   f'<span class="dim small">{len(rows)} written pick(s)</span></h3>'
                   + picks_cards(rows))
    for sport in sorted(set(entries_by_sport) - set(order or SPORT_ORDER)):
        out.append(f'<h3 class="pick-sport-head">{e(sport)}</h3>' + picks_cards(entries_by_sport[sport]))
    return "".join(out)

SPORT_ORDER = ["Tennis","Basketball","Ice Hockey","Cricket","Baseball","Volleyball","Darts",
               "Snooker","Rugby Union","Rugby League","Handball","Gaelic Football",
               "Golf","Motor Racing","Greyhounds"]
SPORT_META = {}
for path in sorted(glob.glob(os.path.join(ROOT, "data/sports/*.json"))):
    b = json.load(open(path))
    SPORT_META[b["sport"]] = {"slug": os.path.basename(path)[:-5], "listing": b["listing_url"],
                              "note": b["listing_note"], "id": b["olbg_id"]}
# One slug per sport: the event rows link to sports/<sport_slug>.html, so the coverage table and the
# method page must derive their slugs from the same place or the two conventions disagree.
SLUG_BY_SPORT = {}
for _e in EVENTS:
    SLUG_BY_SPORT.setdefault(_e["sport"], _e["sport_slug"])
for _sport, _meta in SPORT_META.items():
    _meta["slug"] = SLUG_BY_SPORT.get(_sport, _meta["slug"])
SPORT_META["Rugby League"] = {"slug": "rugby_league", "listing": "https://www.olbg.com/betting-tips/Rugby_League/10",
    "note": "The Rugby League listing shows ONLY outright tournament markets (State of Origin 2027, Super League 2027 Grand Final, NRL 2027 Grand Final) and no dated match fixture, so the sport contributes three outright rows and no match rows. The series/grand-final prices are ours, built from the tip split plus a disclosed field-size prior.", "id": 10}
SPORT_META["Golf"] = {"slug": "golf", "listing": "https://www.olbg.com/betting-tips/Golf/5",
    "note": "Ten tournament winner markets verified across the PGA Tour, DP World Tour, LPGA Tour, Ladies European Tour, Legends Tour, Asian Tour and PGA Tour of Australasia. OLBG publishes no field size and no stroke-play line, so a handicap or a 72-hole total would be invented; we originate only the win price, using a disclosed field prior.", "id": 5}
SPORT_META["Motor Racing"] = {"slug": "motor_racing", "listing": "https://www.olbg.com/betting-tips/Motor_Racing/14",
    "note": "One Formula 1 race (United States Grand Prix, 25 Oct 2026) plus two 2026 championship outright markets. The race schedule and official 2026 F1 Drivers' Standings are verified on formula1.com; the top-point-scorer sub-market has no separate FIA table and stays unverified.", "id": 14}
SPORT_META["Greyhounds"] = {"slug": "greyhounds", "listing": "https://www.olbg.com/betting-tips/Greyhounds/28",
    "note": f"{sum(1 for x in GAP_ROWS if x['sport'] == 'Greyhounds')} UK race-winner rows across Kinsley, Sheffield, Nottingham, Monmore, Hove and Newcastle. Each row is a single race with one tipped dog; GBGB racecards sit behind Cloudflare anti-bot challenge on static HTTP fetch, so unconfirmed fields stay blank and every row is published on Flagged for Review.", "id": 28}

NOT_CAPTURED = ["Esports (no listing surfaced on the OLBG tips index at capture time)"]
FORMERLY_NOT_CAPTURED = ["Golf - now captured as 10 outright rows (data/raw/gap_sports_capture_20261021.json)",
                 "Motor Racing - now captured as 1 race and 2 outright rows",
                 "Greyhound Racing - now captured as 6 race rows"]
EXCLUDED = ["Soccer / Football","American Football","Boxing","UFC / MMA","Hurling","Horse Racing","Cycling","Specials (TV/Politics/Awards)"]

def e(x):
    return html.escape(str(x)) if x is not None else ""

def money(p):
    return f"{p:.2f}" if isinstance(p, (int, float)) else "&mdash;"

def usd(p):
    a = american(p)
    return "&mdash;" if a is None else f"{a:+d}"

def band_badge(r):
    pr = r["pick"].get("price")
    if not pr:
        return '<span class="tag">no price</span>'
    if r["pick"].get("in_band"):
        return '<span class="pill high" title="Inside the requested -250 to +10000 US band">in band</span>'
    return '<span class="pill low" title="Outside the requested -250 to +10000 US band">outside band</span>' 

# ---------- statistics ----------
n_events = len(EVENTS)
n_fixtures = sum(1 for r in EVENTS if r.get("market_type", "fixture") == "fixture")
n_outrights = n_events - n_fixtures
# Archive counters are computed from the data at build time, never hard-coded: the published
# finding used to say "Seventy of 137 rows" long after the board had grown to 196 rows.
n_archived = sum(1 for r in EVENTS
                 if (r.get("pick") or {}).get("start_iso") and r["pick"]["start_iso"] < BUILT)
n_live = n_events - n_archived
_live_dates = sorted((r.get("pick") or {}).get("start_iso") for r in EVENTS
                     if (r.get("pick") or {}).get("start_iso") and r["pick"]["start_iso"] >= BUILT)
_live_first = _live_dates[0] if _live_dates else None
_live_last = _live_dates[-1] if _live_dates else None
by_sport = defaultdict(list)
for r in EVENTS:
    by_sport[r["sport"]].append(r)
n_verified = sum(1 for r in EVENTS if r["verification"]["status"] == "verified")
n_corroborated = sum(1 for r in EVENTS if r["verification"]["status"] == "corroborated")
n_unverified = sum(1 for r in EVENTS if r["verification"]["status"] == "unverified")
conf_counter = Counter(r["pick"]["confidence"] for r in EVENTS)
n_price = sum(1 for r in EVENTS if r["model"].get("prices"))
n_hcap = sum(1 for r in EVENTS if r["model"].get("handicap"))
n_expired = sum(1 for r in EVENTS if r["pick"].get("kickoff_passed"))
n_started = sum(1 for r in EVENTS if r["pick"].get("kickoff_started"))
n_hi_started = sum(1 for r in EVENTS if r["pick"].get("kickoff_started") and r["pick"]["confidence"] == "HIGH")
n_evidence_high = sum(1 for r in EVENTS if r["pick"].get("evidence_grade") == "HIGH")
n_band_blocked = sum(1 for r in EVENTS if r["pick"].get("evidence_grade") == "HIGH" and not r["pick"].get("in_band"))
n_hi_in_band = sum(1 for r in EVENTS if r["pick"]["confidence"] == "HIGH" and r["pick"].get("in_band"))
n_total = sum(1 for r in EVENTS if r["model"].get("total"))

# ---------- shared chrome ----------
SNAPSHOT_AGE_H = snapshot_age_hours()
STALE_BANNER = ("" if SNAPSHOT_AGE_H < 30 else
                f'<div class="notice" style="border-left-color:#b3261e;background:#fdecea;color:#7a1c15">'
                f'<strong>SNAPSHOT STALE — {SNAPSHOT_AGE_H:.0f} h old.</strong> The newest committed source '
                f'observation is {CLOCK}. Rows below are archived analysis, not current picks. A new live '
                f'capture is needed before anything here can be presented as today\'s selection.</div>')

def head(title, depth=0):
    p = "../" * depth
    # The Picks shelf is rendered inline and always visible; the two evidence shelves collapse
    # under one disclosure each so the bar stays a single line on a laptop.
    shelves = []
    for i, (label, links) in enumerate(NAV_GROUPS):
        items = "".join('<a href="{0}{1}"{2}>{3}</a>'.format(p, f, ' class="nav-pick"' if f == "today.html" else "", e(t))
                        for f, t in links)
        if i == 0:
            shelves.append(f'<span class="navgrp navgrp-picks">{items}</span>')
        else:
            shelves.append(f'<details class="navgrp navgrp-more navgrp-{i}"><summary>{e(label)}</summary>'
                           f'<div>{items}</div></details>')
    navlinks = "".join(shelves)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} &middot; OLBG3 Match Board</title>
<meta name="description" content="Verified multi-sport fixture board reverse-engineered from OLBG.com, with our own originated prices, picks, confidence grades and written predictions.">
<link rel="stylesheet" href="{p}assets/style.css">
</head><body>
<header class="topbar">
  <a class="brand" href="{p}index.html"><span class="dot"></span> OLBG3 <span class="brandsub">Match Board</span></a>
  <nav>
    {navlinks}
  </nav>
</header>
<main>{STALE_BANNER}"""

FOOT = f"""
</main>
<footer>
  <p><strong>Captured {GEN} &middot; rebuilt {BUILT}.</strong> Data captured from OLBG.com event pages and checked against official competition sources where stated.
  Prices, handicaps and totals are <strong>our own model output</strong>, not bookmaker prices and not facts.</p>
  <p><strong>Snapshot, not a complete live fixture feed.</strong> Rebuilding does not refresh the captured OLBG listings or
  reverify official sources. HIGH is an evidence-based model grade, not a calibrated win rate or a demonstrated betting edge.
  Only explicitly timezone-qualified official clocks are converted to UTC. HIGH release expires at the scheduled start or 24 hours after its source check, whichever comes first. A clock cannot establish the final result.
  See <a href="{{P}}flagged.html">Flagged for Review</a> for limitations.</p>
  <p>18+. If gambling is causing you harm, contact <a href="https://www.gamcare.org.uk/" rel="noopener">GamCare</a> or
  <a href="https://www.gambleaware.org/" rel="noopener">GambleAware</a>. No bet is ever a certainty.</p>
</footer>
<script src="{{P}}assets/app.js"></script>
<script src="{{P}}assets/release.js"></script>
</body></html>"""

def foot(depth):
    return FOOT.replace("{P}", "../" * depth)

def conf_pill(c):
    return f'<span class="pill {c.lower()}">{c}</span>'

GOVERNING_PORTAL = {
    "Tennis": ("https://www.atptour.com/en/scores/current", "ATP official reference; fixture unverified"),
    "Basketball": ("https://www.nba.com/schedule", "NBA official reference; fixture unverified"),
    "Ice Hockey": ("https://www.nhl.com/schedule", "NHL official reference; fixture unverified"),
    "Volleyball": ("https://www.volleyballworld.com/", "official federation reference; fixture unverified"),
    "Darts": ("https://www.pdc.tv/", "PDC official reference; fixture unverified"),
    "Snooker": ("https://www.wst.tv/matches/", "WST official reference; fixture unverified"),
    "Handball": ("https://www.eurohandball.com/en/calendar/", "EHF official reference; fixture unverified"),
    "Rugby Union": ("https://www.world.rugby/", "World Rugby official reference; fixture unverified"),
    "Cricket": ("https://cricket.co.za/fixtures/", "check CSA / ICC"),
    "Golf": ("https://www.europeantour.com/dpworld-tour/schedule/", "check tour calendar"),
    "Motor Racing": ("https://www.formula1.com/en/results/2026/drivers", "check F1 standings"),
    "Greyhounds": ("https://www.gbgb.org.uk/", "check GBGB"),
    "Rugby League": ("https://www.nrl.com/draw/", "check NRL / RFL"),
    "Gaelic Football": ("https://www.gaa.ie/fixtures-results", "check GAA.ie"),
}

def ver_cell(r):
    v = r["verification"]
    if v["status"] == "verified":
        lab = e(v["official_label"]) or "official source"
        tier = v.get("source_tier", "official")
        return f'<a class="ok" href="{e(v["official_url"])}" rel="noopener" title="{e(v["note"])}">&#10003; {lab}</a>'
    if v["status"] == "corroborated":
        lab = e(v["official_label"]) or "third-party source"
        return (f'<a class="med" href="{e(v["official_url"])}" rel="noopener" '
                f'title="Third-party corroboration only, not the competition&#39;s own site. See Flagged for Review.">'
                f'~ {lab} <span class="tag">third-party</span></a>')
    gov_url, gov_lbl = GOVERNING_PORTAL.get(r["sport"], ("https://www.olbg.com/betting-tips", "OLBG listing only; fixture unverified"))
    return (f'<span class="unver" title="No official source retrieved for this fixture">unverified</span>'
            f' &middot; <a class="dim" href="{e(gov_url)}" rel="noopener">{e(gov_lbl)}</a>')

def price_cell(r):
    m = r["model"]
    if not m.get("prices"):
        return ('<td class="num dim" colspan="3" title="No defensible input: OLBG published a selection but no tip count">'
                'no price</td>')
    p = m["prices"]
    if "single" in p:
        # one-selection market: there is no opposing side and no draw to price
        return (f'<td class="num">{money(p["single"])}</td>'
                '<td class="num dim" title="A single-selection market has no draw">&mdash;</td>'
                '<td class="num dim" title="A single-selection market has no opposing side">&mdash;</td>')
    if "draw" in p:
        return f'<td class="num">{money(p.get("win_home"))}</td><td class="num">{money(p.get("draw"))}</td><td class="num">{money(p.get("win_away"))}</td>'
    # consensus rows only price the picked side and its opposite
    return f'<td class="num">{money(p.get("win_home"))}</td><td class="num dim">n/p</td><td class="num">{money(p.get("win_away"))}</td>'

def market_label(r):
    mt = r.get("market_type", "fixture")
    name = r.get("olbg_market") or "market not shown by OLBG"
    tag = {"fixture": "match", "outright": "outright", "race": "race"}.get(mt, mt)
    return f'{e(name)} <span class="tag">{tag}</span>'

def match_label(r):
    if not r.get("away"):
        return f'{e(r["home"])} <span class="vs">&middot;</span> <span class="dim small">single-selection</span>'
    return f'{e(r["home"])} <span class="vs">v</span> {e(r["away"])}'

def row_html(r):
    p = r["pick"]
    release = p.get("release", {})
    pick = e(p["label"]) if p.get("label") else '<span class="dim">selection withheld</span>'
    prob = f'<span class="prob">model {p["prob"]*100:.0f}%</span>' if p.get("prob") else ""
    ref = f'<a href="{e(r["olbg_event_url"])}" rel="noopener">{e(r["ref"])}</a>'
    price = (f'{money(p["price"])} <span class="dim">({usd(p["price"])} US)</span>' if p.get("price") else '')
    official_clock = (f'<div class="small">Official → UTC {e(p["kickoff_utc"])}</div>' if p.get("kickoff_utc") else '')
    state = release.get("status", "unverified_start")
    return f"""<tr id="row-{e(r['ref'])}" data-sport="{e(r['sport'])}" data-conf="{p['confidence']}" data-release="{e(state)}" data-expires-at="{e(release.get('expires_at') or '')}" data-text="{e((r['home']+' '+r['away']+' '+r['competition']+' '+r['sport']).lower())}">
<td class="ref">{ref}<div class="small">{e(r['sport'])}</div></td>
<td class="match">{match_label(r)}<div class="small">{e(r['competition'])}</div></td>
<td class="when" data-kickoff-utc="{e(p.get('kickoff_utc') or '')}">{e(r['start'])} <span class="small">OLBG, zone unverified</span>{official_clock}</td>
<td class="market">{market_label(r)}<div class="small">{e(r.get('olbg_tips') or '')} public tips — not probabilities</div></td>
<td class="pick">{pick}<div class="odds">{price} {prob}</div></td>
<td class="confidence-cell">{conf_pill(p['confidence'])}<div class="small">{e(r['model'].get('basis','none'))}</div></td>
<td class="src">{ver_cell(r)}</td>
<td class="release-cell"><span class="tag">{e(state.replace('_',' '))}</span><div class="small">{e(release.get('reason',''))}</div></td>
</tr>"""

TABLE_HEAD = """<thead><tr>
<th>Ref / sport</th><th>Match / competition</th><th>Captured start / official UTC</th><th>OLBG market</th>
<th>Our winner / originated odds</th><th>Model confidence</th><th>Official source / reference</th><th>Publication status</th>
</tr></thead>"""

def table(rows, tid="tbl"):
    body = "\n".join(row_html(r) for r in rows)
    return f'<div class="tablewrap"><table id="{tid}" class="board">{TABLE_HEAD}<tbody>{body}</tbody></table></div>'

# Why a market is missing for a sport: shown instead of a fabricated number.
HANDICAP_GAP = {
 "Cricket": "OLBG does not state the format (T20 / ODI / Test), and a runs line differs by an order of magnitude between them, so a handicap would be invented.",
 "Darts": "Neither OLBG nor the PDC pages retrieved state the leg format for these matches, so a legs handicap cannot be expressed.",
 "Gaelic Football": "No official scoring record was retrieved for these club fixtures, so there is no scoring unit to price against.",
}
TOTAL_GAP = ("Not originated: we captured no official scoring baseline for this sport in this pass, so any total would be a "
             "number we invented. The field is left empty on purpose and the gap is listed on the Flagged for Review page.")

# ---------- brief coverage accounting ----------
# data/brief_coverage.json is produced by scripts/brief_coverage.py from the same committed rows and
# is re-checked by scripts/check_board.py, so these numbers cannot drift away from the board.
BRIEF = json.load(open(os.path.join(ROOT, "data/brief_coverage.json")))
BT = BRIEF["totals"]
PE = BRIEF["prose_evidence"]


def pct(n, d):
    return f"{100.0 * n / d:.0f}%" if d else "&mdash;"


# ---------- sport pages ----------
os.makedirs(os.path.join(OUT, "sports"), exist_ok=True)
for sport in [x for x in SPORT_ORDER if x in SPORT_META]:
    rows = by_sport.get(sport, [])
    meta = SPORT_META[sport]
    hi = [r for r in rows if r["pick"]["confidence"] == "HIGH"]
    med = [r for r in rows if r["pick"]["confidence"] == "MEDIUM"]
    mark = [r for r in rows if r["model"].get("handicap")]
    tot = [r for r in rows if r["model"].get("total")]
    hcap_rows = "".join(
        f"<tr><td>{e(r['ref'])}</td><td>{match_label(r)}</td>"
        f"<td>{e(r['home'] if r['model']['handicap']['fav']=='home' else r['away'])} -{abs(r['model']['handicap']['line']):.1f}"
        f" <span class='dim small'>{e(r['model']['handicap'].get('unit',''))}</span></td>"
        f"<td class='num'>{money(r['model']['handicap']['price'])}</td>"
        f"<td>{e(r['away'] if r['model']['handicap']['fav']=='home' else r['home'])} +{abs(r['model']['handicap']['dog_line']):.1f}"
        f" <span class='dim small'>{e(r['model']['handicap'].get('unit',''))}</span></td>"
        f"<td class='num'>{money(r['model']['handicap']['dog_price'])}</td>"
        f"<td class='small'>{e(r['model']['handicap'].get('basis',''))}</td></tr>" for r in mark)
    tot_rows = "".join(
        f"<tr><td>{e(r['ref'])}</td><td>{match_label(r)}</td><td class='num'>{r['model']['total']['line']}</td>"
        f"<td class='num'>{money(r['model']['total']['over'])}</td><td class='num'>{money(r['model']['total']['under'])}</td></tr>" for r in tot)
    n_out = len([r for r in rows if r.get("market_type", "fixture") != "fixture"])
    page = head(f"{sport}", 1) + f"""
<section class="pagehead">
  <h1>{e(sport)}</h1>
  <p class="lede">{len(rows)} rows captured from <a href="{e(meta['listing'])}" rel="noopener">OLBG&rsquo;s {e(sport)} tips page</a>
  (sport ID {e(meta['id'])}): {len(rows) - n_out} two-sided {'fixture' if len(rows) - n_out == 1 else 'fixtures'} and {n_out} outright/race {'market' if n_out == 1 else 'markets'}.
  {len([r for r in rows if r['verification']['status']=='verified'])} were confirmed against the competition&rsquo;s own site,
  {len([r for r in rows if r['verification']['status']=='corroborated'])} rest on third-party corroboration only
  (<em>corroborated</em>), and the rest are published as <em>unverified</em> &mdash; all three groups are itemised on the
  <a href="../flagged.html">Flagged for Review</a> page.</p>
  <p class="note">{e(meta['note'])}</p>
</section>
{sport_picks_block(sport, meta)}
<div class="cards">
  <div class="card"><span class="k">{len(rows)}</span><span class="l">rows</span></div>
  <div class="card"><span class="k">{len([r for r in rows if r['verification']['status']=='verified'])}</span><span class="l">officially verified</span></div>
  <div class="card"><span class="k">{len([r for r in rows if r['verification']['status']=='corroborated'])}</span><span class="l">corroborated (third-party)</span></div>
  <div class="card"><span class="k">{len(hi)}</span><span class="l">high-confidence picks</span></div>
  <div class="card"><span class="k">{len(med)}</span><span class="l">medium-confidence picks</span></div>
</div>
<h2>Rows, our lines and picks</h2>
<p class="legend"><strong>Our price / Our price 2:</strong> decimal prices we originate (5% price haircut), one for each side, or a single price on a one-selection market. <strong>n/p</strong> = not priced, because the only input was an OLBG consensus figure on a different market. 
<strong>Basis:</strong> <code>official-league-table</code> / <code>official-standings</code> = model built on official data; <code>consensus</code> = de-vigged OLBG tip share only; <code>none</code> = no defensible input, so no price is shown.</p>
{table(rows, 'tbl-' + meta['slug'])}
{(f'<h2>Handicap lines we originated ({len(mark)})</h2><p class="legend"><code>official-form</code> = projected margin built on the competition&rsquo;s own scoring table. <code>consensus-scaled</code> = probability-implied line using a disclosed per-sport margin scale, capped at 85% probability. Both are our own lines, never bookmaker prices.</p><div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Match</th><th>Favourite line</th><th class="num">Price</th><th>Underdog line</th><th class="num">Price</th><th>Basis</th></tr></thead><tbody>{hcap_rows}</tbody></table></div>') if mark else '<h2>Handicap lines</h2><p class="dim">Not originated for this sport: ' + HANDICAP_GAP.get(sport, "no scoring unit and no defensible baseline were available, so a handicap would be a guess.") + ' Blank rather than invented.</p>'}
{(f'<h2>Match totals we originated ({len(tot)})</h2><div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Match</th><th class="num">Line</th><th class="num">Over</th><th class="num">Under</th></tr></thead><tbody>{tot_rows}</tbody></table></div>') if tot else '<h2>Match totals</h2><p class="dim">' + TOTAL_GAP + '</p>'}
""" + foot(1)
    open(os.path.join(OUT, "sports", meta["slug"] + ".html"), "w").write(page)

# ---------- brief coverage page ----------
brief_rows = ""
for srow in BRIEF["sports"]:
    slug = (SPORT_META.get(srow["sport"]) or {}).get("slug", "")
    name = f'<a href="sports/{slug}.html">{e(srow["sport"])}</a>' if slug else e(srow["sport"])
    markets_cell = (f'{srow["root_priced_win"]} win &middot; {srow["root_handicap"]} handicap &middot; '
                    f'{srow["root_total"]} total &middot; {srow["root_outright"]} outright')
    status = ('<span class="pill high">target met</span>' if srow["meets_target"]
              else f'<span class="pill low">{srow["shortfall"]} short</span>')
    brief_rows += (f'<tr><td>{name}</td><td class="num">{srow["root_rows"]}</td>'
                   f'<td class="num">{srow["root_verified"]}</td>'
                   f'<td class="small">{markets_cell}</td>'
                   f'<td class="num">{srow["root_high"]}</td>'
                   f'<td class="num">{srow["olbg_rows"]} / {srow["olbg_high"]}</td>'
                   f'<td class="num"><strong>{srow["live_high_union"]}</strong></td>'
                   f'<td class="num">{srow["target"]}</td>'
                   f'<td>{status}</td></tr>')

reason_blocks = ""
for srow in BRIEF["sports"]:
    if srow["meets_target"]:
        continue
    items = "".join(f"<li>{e(r)}</li>" for r in srow["reasons"]) or \
            "<li>No mechanical blocker recorded; the sport simply has fewer in-band, verified, priced fixtures than the target.</li>"
    reason_blocks += (f'<details class="sport-reasons"><summary>{e(srow["sport"])} '
                      f'&mdash; {srow["live_high_union"]} of {srow["target"]} live HIGH picks</summary>'
                      f'<ul class="small">{items}</ul></details>')

live_pick_rows = ""
for srow in BRIEF["sports"]:
    for p_ in srow["live_picks"]:
        ref = (f'<a href="sports/{(SPORT_META.get(p_["sport"]) or {}).get("slug","")}.html#row-{e(p_["root_ref"])}">{e(p_["root_ref"])}</a>'
               if p_.get("root_ref") else '<span class="dim">root: none</span>')
        olref = (f'<a href="olbg/picks.html">{e(p_["olbg_ref"])}</a>'
                 if p_.get("olbg_ref") else '<span class="dim">/olbg/: none</span>')
        tracks = " + ".join("root" if t == "root" else "/olbg/" for t in p_["tracks"])
        live_pick_rows += (f'<tr><td>{e(p_["sport"])}</td><td>{ref}</td><td>{olref}</td>'
                           f'<td class="pick">{e(p_["selection"] or "")}</td>'
                           f'<td class="num">{money(p_["price"])}</td><td class="num">{e(p_["american"] or "")}</td>'
                           f'<td class="small">{e(tracks)}</td></tr>')
if not live_pick_rows:
    live_pick_rows = '<tr><td colspan="7">No live HIGH pick on either track.</td></tr>'

briefpage = head("Brief coverage") + f"""
<section class="pagehead">
  <p class="eyebrow">THE BRIEF, COUNTED HONESTLY</p>
  <h1>Brief coverage: {BT['live_high_union']} of {BT['target_picks_if_all_sports_met']} targeted picks</h1>
  <p class="lede">The brief asks for the <strong>five highest-confidence picks for every covered sport, every day</strong>, on
  matches inside the <strong>-250 to +10000</strong> US-odds band (decimal 1.40&ndash;101.00), each with a written prediction of at least
  30 words. This page counts what is actually published against that target, per sport, and states the mechanical reason each sport falls
  short. It is an accounting of the committed board, not a promise that five exist.</p>
  <p class="stamp">Publication clock {e(BRIEF['source_clocks']['root_publication_clock'])} &middot;
  capture {e(BRIEF['source_clocks']['root_capture'])} &middot; built {e(BRIEF['source_clocks']['root_built'])}</p>
</section>

<div class="notice">
  <strong>No source was re-fetched for this page.</strong> It is computed from the committed rows by
  <code>scripts/brief_coverage.py</code> and re-checked by <code>scripts/check_board.py</code>. The counts are not a win rate, not a
  calibrated probability and not bookmaker odds. A distinct pick is counted once even when both tracks publish the same fixture
  (they are de-duplicated on the OLBG event id). Live re-verification is blocked in this environment by the outbound allowlist
  described in FL-077, so no <code>checked_at</code>, quote or verification label was renewed.
</div>

<div class="cards">
  <div class="card"><span class="k">{BT['sports_listed']}</span><span class="l">sports covered by the brief</span></div>
  <div class="card"><span class="k">{BT['sports_meeting_target']}</span><span class="l">sports with 5+ live HIGH picks</span></div>
  <div class="card"><span class="k">{BT['live_high_union']}</span><span class="l">distinct live HIGH picks</span></div>
  <div class="card warn"><span class="k">{BT['shortfall_to_target']}</span><span class="l">picks short of the daily target</span></div>
</div>

<h2>Per-sport accounting</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th class="num">Root rows</th><th class="num">Verified</th><th>Markets originated (root)</th>
<th class="num">Root HIGH</th><th class="num">/olbg/ rows / HIGH</th><th class="num">Distinct live HIGH</th>
<th class="num">Target</th><th>Against target</th></tr></thead>
<tbody>{brief_rows}</tbody></table></div>
<p class="dim">Margins, spreads, puck lines and run lines are originated where a scoring unit and an official baseline exist; match
totals only where the official scoring rates support a projected combined score. A blank market is a withheld guess, not a zero.
The full market-level detail per sport is on each sport page.</p>

<h2 id="window">Does a 70%-plus price exist inside the window?</h2>
<p>The brief also asks whether there are picks with more than about a 70% implied win chance inside
<strong>-250 to +10000</strong> US odds, and to focus there. The window can hold such a pick only in one narrow strip:
-250 is 71.43% implied and 70% implied is reached at -233.33, so the whole above-70% region is the 16.7 points of price from
-233.33 to -250 (6.7 percentage points of implied chance). Anything shorter than -250 is outside the window by definition.
A price there is a short-priced favourite, so the edge is thin; the selections published on this board sit further into the
window instead. The count of in-window prices and how many of them exceed 70% is recomputed from the rows on every build and
worked through line by line on the <a href="olbg/methodology.html#window">OLBG lines method page, section 1b</a> — it is not
asserted here.</p>

<h2>Why each sport falls short</h2>
<p class="legend">Each reason is counted from the published row fields: no official current-form input for both sides, a HIGH-grade
evidence score that sits outside the price band, an official-start or source-freshness gate, no defensible win price, or an
unverified fixture. Rows can fail more than one test, so the counts overlap and are not meant to add up.</p>
{reason_blocks}

<h2>The {BT['live_high_union']} distinct live HIGH picks</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th>Root ref</th><th>/olbg/ ref</th><th>Selection</th><th class="num">Decimal</th>
<th class="num">US</th><th>Tracks publishing it</th></tr></thead>
<tbody>{live_pick_rows}</tbody></table></div>

<h2 id="evidence">How the write-ups are evidenced</h2>
<p class="legend">Counted from each piece&rsquo;s own <code>sources</code> list. <em>Recorded official host</em> means a host this repository
already records as a governing body, league or club source. A host outside that set is listed individually below &mdash; being cited is
not the same as being verified, and some of them are league sites used as official elsewhere on the board.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Track</th><th class="num">Pieces</th><th class="num">Currently HIGH</th><th class="num">Words min / median / max</th>
<th class="num">Under 30 words</th><th class="num">Citing a recorded official host</th><th class="num">Citing only hosts outside that set</th><th class="num">Duplicate bodies</th></tr></thead>
<tbody>
<tr><td>Root board</td><td class="num">{PE['root']['pieces']}</td><td class="num">{PE['root']['high']}</td>
<td class="num">{PE['root']['words_min']} / {PE['root']['words_median']:.0f} / {PE['root']['words_max']}</td>
<td class="num">{PE['root']['under_30_words']}</td><td class="num">{PE['root']['citing_an_official_host']}</td>
<td class="num">{PE['root']['citing_only_hosts_outside_official_set']}</td><td class="num">{PE['root']['duplicate_bodies']}</td></tr>
<tr><td>/olbg/ audit track</td><td class="num">{PE['olbg']['pieces']}</td><td class="num">{PE['olbg']['high']}</td>
<td class="num">{PE['olbg']['words_min']} / {PE['olbg']['words_median']:.0f} / {PE['olbg']['words_max']}</td>
<td class="num">{PE['olbg']['under_30_words']}</td><td class="num">{PE['olbg']['citing_an_official_host']}</td>
<td class="num">{PE['olbg']['citing_only_hosts_outside_official_set']}</td><td class="num">{PE['olbg']['duplicate_bodies']}</td></tr>
</tbody></table></div>
<p class="small"><strong>Hosts outside the recorded official set, by number of citations:</strong>
{", ".join(f"{e(h)} ({c})" for h, c in PE['root']['hosts_outside_official_set'].items())}.
These citations are <strong>not</strong> re-read in this pass and are therefore not treated as verification anywhere on the board; the
review item is <a href="flagged.html#FL-106">FL-106</a>.</p>

<p class="small">The shortfall itself is also raised as <a href="flagged.html#FL-102">FL-102</a> in the shared register, and the
evening source-availability audit behind it is in <code>docs/coverage-20261022-evening.md</code>.</p>

<h2>What would raise the count</h2>
<div class="panel"><p>Only two things can, and neither can be done by relabelling a row:</p>
<ul>
<li><strong>A new dated official observation</strong> for a fixture whose start is still ahead of the publication clock, with the
competition naming the fixture and an explicit timezone on the clock. That is what unlocks the release gate.</li>
<li><strong>Official current-form data for both sides</strong> on a sport that currently has none, so the model can earn the third
evidence point instead of being capped at MEDIUM.</li>
</ul>
<p>Both require outbound access to the competitions' own sites. That access is blocked in this environment (FL-077), so the honest
position today is the {BT['shortfall_to_target']}-pick shortfall shown above &mdash; published rather than papered over.</p></div>
""" + foot(0)
open(os.path.join(OUT, "brief.html"), "w").write(briefpage)

# ---------- cross-track reconciliation page ----------
XT = BRIEF["cross_track"]
xt_rows = ""
for r_ in XT["rows"]:
    slug = (SPORT_META.get(r_["sport"]) or {}).get("slug", "")
    root_ref = (f'<a href="sports/{slug}.html#row-{e(r_["root_ref"])}">{e(r_["root_ref"])}</a>'
                if slug else e(r_["root_ref"]))
    xt_rows += (f'<tr><td>{e(r_["sport"])}</td><td>{e(r_["match"])}</td>'
                f'<td>{root_ref}<div class="small">{e(r_["root_selection"])}<br>'
                f'{money(r_["root_price"])} ({e(r_["root_american"] or "")}) &middot; '
                f'model {r_["root_prob"]*100:.1f}% &middot; {e(r_["root_confidence"] or "")}</div></td>'
                f'<td><a href="olbg/picks.html">{e(r_["olbg_ref"])}</a><div class="small">{e(r_["olbg_selection"])}<br>'
                f'{money(r_["olbg_price"])} ({e(r_["olbg_american"] or "")}) &middot; '
                f'model {r_["olbg_prob"]*100:.1f}% &middot; {e(r_["olbg_confidence"] or "")}</div></td>'
                f'<td class="small"><a href="{e(r_["olbg_url"])}" rel="noopener">OLBG event page</a></td></tr>')
if not xt_rows:
    xt_rows = '<tr><td colspan="5">The two tracks agree on every paired fixture.</td></tr>'

recpage = head("Cross-track review") + f"""
<section class="pagehead">
  <p class="eyebrow">TWO MODELS, ONE FIXTURE</p>
  <h1>Cross-track review: {XT['different_selection']} of {XT['paired_fixtures']} paired fixtures disagree</h1>
  <p class="lede">The repository carries two independent pipelines. The root board builds its lines from official competition tables and
  standings; the <code>/olbg/</code> audit track builds its own from the captured OLBG listing with a shrink plus home-edge model. Where
  the same OLBG fixture appears on both, they can name different selections. Both versions stay published and both are listed here so the
  disagreement is visible rather than hidden.</p>
</section>

<div class="notice">A disagreement is <strong>not</strong> evidence that either side is wrong, and it is not a settled outcome. Neither
number is a bookmaker price. The list exists so a human can review the pair; it is also published as <a href="flagged.html#FL-105">FL-105</a>
on the Flagged for Review page. Rows where one track deliberately withheld a selection (source conflict or a gate) are counted separately
and are not treated as disagreements.</div>

<div class="cards">
  <div class="card"><span class="k">{XT['paired_fixtures']}</span><span class="l">fixtures priced on both tracks</span></div>
  <div class="card"><span class="k">{XT['same_selection']}</span><span class="l">same selection</span></div>
  <div class="card warn"><span class="k">{XT['different_selection']}</span><span class="l">different selection</span></div>
  <div class="card"><span class="k">{XT['withheld_by_one_track']}</span><span class="l">selection withheld by one track</span></div>
</div>

<h2>Fixtures where the tracks pick different sides</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th>Match</th><th>Root board pick</th><th>/olbg/ track pick</th><th>Source</th></tr></thead>
<tbody>{xt_rows}</tbody></table></div>
<p class="dim">Root picks carry their release status on the sport page; <code>/olbg/</code> picks carry theirs on the
<a href="olbg/picks.html">/olbg/ lines page</a>. A selection shown as MEDIUM or <code>medium</code> is analysis, not a current pick.</p>
""" + foot(0)
open(os.path.join(OUT, "reconcile.html"), "w").write(recpage)

# ---------- index ----------
cov_rows = ""
for sport in SPORT_ORDER:
    rows = by_sport.get(sport, [])
    meta = SPORT_META[sport]
    ver = len([r for r in rows if r["verification"]["status"] == "verified"])
    hi = len([r for r in rows if r["pick"]["confidence"] == "HIGH"])
    n_out_s = len([r for r in rows if r.get("market_type", "fixture") != "fixture"])
    corr = len([r for r in rows if r["verification"]["status"] == "corroborated"])
    cov_rows += (f"<tr><td><a href='sports/{meta['slug']}.html'>{e(sport)}</a></td><td class='num'>{len(rows)}</td>"
                 f"<td class='num'>{n_out_s}</td><td class='num'>{ver}</td><td class='num'>{corr}</td><td class='num'>{hi}</td>"
                 f"<td class='num'>{len([r for r in rows if r['model'].get('prices')])}</td>"
                 f"<td class='num'>{len([r for r in rows if r['model'].get('handicap')])}</td>"
                 f"<td class='num'>{len([r for r in rows if r['model'].get('total')])}</td>"
                 f"<td><a href='{e(next((r['verification'].get('official_url') for r in rows if r['verification']['status']=='verified'), GOVERNING_PORTAL.get(sport, ('https://www.olbg.com/betting-tips',''))[0]))}'>official reference</a></td></tr>")

try:
    n_feed = len(json.load(open(os.path.join(ROOT, "data/current.json")))["matches"])
except Exception:
    n_feed = 0
hi_rows = [r for r in EVENTS if r["pick"]["confidence"] == "HIGH"]
med_rows = [r for r in EVENTS if r["pick"]["confidence"] == "MEDIUM"]
top = ""
for r in hi_rows:
    p = r["pick"]; pr = r["model"]["prices"]
    price = pr.get("win_home") if p["side"] == "home" else pr.get("win_away")
    top += (f"<tr data-current-high='true' data-expires-at='{e(p.get('release',{}).get('expires_at') or '')}'><td><a href='sports/{r['sport_slug']}.html'>{e(r['sport'])}</a></td><td>{match_label(r)}</td>"
            f"<td class='pick'>{e(p['label'])}</td><td class='num'>{money(price)}</td>"
            f"<td class='num'>{usd(price)}</td><td class='num'>{p['prob']*100:.0f}%</td>"
            f"<td>{conf_pill(p['confidence'])} {band_badge(r)}</td>"
            f"<td><a href='predictions.html#{e(r['ref'])}'>read prediction</a><br>{ver_cell(r)}</td></tr>")

blocked = [r for r in EVENTS if r["pick"].get("evidence_grade") == "HIGH" and r["pick"]["confidence"] != "HIGH"]
band_blocked_rows = ""
for r in sorted(blocked, key=lambda x: (x["pick"].get("in_band"), x["sport"], x["ref"])):
    p_ = r["pick"]; pr = p_.get("price")
    why = p_.get("note") or ("kick-off has passed" if p_.get("kickoff_passed") else "outside the requested band")
    band_blocked_rows += (f"<tr><td>{e(r['ref'])}</td><td>{e(r['sport'])}</td><td>{match_label(r)}</td>"
                          f"<td>{e(p_['label'])}</td><td class='num'>{money(pr)}</td><td class='num'>{usd(pr)}</td>"
                          f"<td class='small'>{why}<br>{ver_cell(r)}</td></tr>")
if not band_blocked_rows:
    band_blocked_rows = "<tr><td colspan='7'>None.</td></tr>"

# The landing-page answer to "what are the picks?": one line per live written pick, in start
# order, each linking straight to its card on the executive summary. No card, no line.
_strip_items = []
for _x in PICK_LIVE[:12]:
    _t = _x["tracks"].get("root") or _x["tracks"].get("olbg") or {}
    _price = _t.get("price")
    _strip_items.append(
        "<a class='strip-item' href='today.html#pick-{k}'>"
        "<span class='strip-sport'>{sp}</span><span class='strip-match'>{mt}</span>"
        "<span class='strip-pick'>{sel}</span><span class='strip-price'>{pr}</span>"
        "<span class='strip-when'>{wh}</span></a>".format(
            k=e(_x["key"]), sp=e(_x["sport"]), mt=e(_x["match"]),
            sel=e(_t.get("selection") or ""),
            pr=(money(_price) + " (" + usd(_price) + " US)") if _price else "no price originated",
            wh=e((_x.get("start_utc") or "")[:16].replace("T", " ") + "Z" if _x.get("start_utc")
                 else (_x.get("olbg_label") or "start unverified"))))
if not _strip_items:
    _strip_items.append("<p class='dim'>No pick passes every gate at this build. The HIGH rows held back, "
                        "and the mechanical reason for each, are on <a href='today.html#written-picks'>"
                        "Today&rsquo;s picks</a>.</p>")
pick_paired = sum(1 for _x in PICK_LIVE if len(_x["tracks"]) > 1)
_shown = len(PICK_LIVE[:12])
pick_strip_note = (f"{len(PICK_LIVE)} live, every one a written prediction &mdash; in start order"
                   if len(PICK_LIVE) <= _shown
                   else f"{len(PICK_LIVE)} live, every one a written prediction &mdash; "
                        f"the first {_shown} in start order are listed here; all {len(PICK_LIVE)} are on the summary page")
index_pick_strip = "".join(_strip_items)

index = head("Dashboard") + f"""
<section class="hero">
  <p class="eyebrow">INDEPENDENT SPORTS RESEARCH · NOT AFFILIATED WITH OLBG</p>
  <h1>Find the match. Check the evidence.</h1>
  <p class="lede"><strong>Looking for today's picks?</strong> <a href="today.html">Today's picks, written out</a> is one
  list, one card per match: the fixture and its official start, who we have picked on each board and at what price,
  our probability for that pick, the full written prediction, and the source behind every claim. A fixture with no
  written prediction is not on that list, and its page says why.
  This dashboard is the full board behind it. A source-linked workspace for fixtures, independent model lines and candid verification notes.
  {n_events} captured rows across {len(by_sport)} sports. Not a complete live schedule, and never bookmaker odds.
  Unconfirmed facts stay blank; source conflicts and expired picks stay visible as research, not current recommendations.</p>
  <p class="hero-actions"><a class="button" href="today.html">Today's picks — executive summary</a>
  <a class="button secondary" href="predictions.html">Read the written predictions</a>
  <a class="button secondary" href="lines.html">All originated lines &amp; markets</a>
  <a class="button secondary" href="olbg/picks.html">The second board's lines</a>
  <a class="button secondary" href="#research-board">Explore all captured records ↓</a></p>
  <p class="stamp">Build {CLOCK} · Listing capture: {e(json.load(open(os.path.join(ROOT, "data/meta.json"))).get("harvest_completed_utc") or "unconfirmed")} · <a href="source-health.html">Check source age</a></p>
</section>

<section class="pick-strip" id="picks-strip">
  <h2>The picks right now <span class="dim small">{pick_strip_note}</span>
      <a class="strip-more" href="today.html#written-picks">read them in full &rarr;</a></h2>
  {index_pick_strip}
</section>

<div class="notice clock-notice">
  <strong>Publication clock: {CLOCK}.</strong> This is a captured research board, not a complete live fixture feed.
  Bare OLBG clocks are <strong>not converted</strong>. A current HIGH release requires a checked, timezone-qualified
  official start and an observation under 24 hours old. A passed start, missing clock, stale observation or source conflict
  moves the piece to analysis. <a href="source-health.html">Inspect every row’s release evidence →</a>
</div>

<div class="cards overview-stats">
  <div class="card"><span class="k">{len(by_sport)}</span><span class="l">sport categories</span></div>
  <div class="card"><span class="k">{n_events}</span><span class="l">captured records</span></div>
  <div class="card"><span class="k">{n_price}</span><span class="l">originated prices</span></div>
  <div class="card"><span class="k" data-high-count>{len(hi_rows)}</span><span class="l">current HIGH research picks</span></div>
  <div class="card"><span class="k">{n_verified}</span><span class="l">recorded official confirmations</span></div>
  <div class="card warn"><span class="k">{n_unverified + n_corroborated}</span><span class="l">unverified / corroborated only</span></div>
</div>

<div class="notice brief-summary">
  <strong>Against the brief:</strong> {len(PICK_LIVE)} current written picks across {BT['sports_listed']} covered sports,
  against the daily target of {BT['target_picks_if_all_sports_met']} (five per sport).
  {sum(len(v) >= 5 for v in PICK_BY_SPORT.values())} sport(s) meet the target; shortfall {max(0, 75-len(PICK_LIVE))}.
  Raw research HIGH counts elsewhere can include entries held from this current shortlist.
  <a href="brief.html">See the per-sport accounting and every blocker &rarr;</a>
</div>

<h2>Coverage by sport</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th class="num">Rows</th><th class="num">of which outright/race</th><th class="num">Verified</th><th class="num">Corroborated</th><th class="num">High conf.</th><th class="num">Priced</th><th class="num">Handicaps</th><th class="num">Totals</th><th>Source</th></tr></thead>
<tbody>{cov_rows}</tbody></table></div>
<p class="dim">Rugby League has no dated match fixture on OLBG at capture time: its three rows are 2027 outright markets. Golf, Motor Racing and Greyhounds are
race or tournament markets with a single selection, so they carry one originated price and no handicap or total. All of this is itemised on the
<a href="audit.html">audit page</a> and on <a href="flagged.html">Flagged for Review</a>.</p>
<p class="dim"><strong>Five live HIGH picks per sport:</strong> the brief asks for five high-confidence selections for every sport we cover. This board is the
curated capture dataset; the live listing and the per-sport reason for every shortfall are published on the
<a href="olbg/index.html">OLBG lines board</a> (a sport with no live listing, a fixture whose official clock carries no timezone, a match that has
already started, or a price outside the -250 to +10000 window). Where the official evidence is short, the written piece is published as
<em>analysis</em> rather than a live pick, and every shortfall is listed on <a href="flagged.html">Flagged for Review</a>.</p>

<h2>High-confidence picks</h2>
{"<div class='tablewrap'><table class='board'><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th class='num'>Decimal</th><th class='num'>US odds</th><th class='num'>Model</th><th>Conf. / band</th><th></th></tr></thead><tbody>" + top + "</tbody></table></div>" if top else "<p>None.</p>"}

<details class="research-details"><summary>Why stronger evidence does not always qualify for HIGH</summary><h2>Release and price-band gates</h2>
<p class="dim">The brief asks for high-confidence picks on matches priced between <strong>-250</strong> and <strong>+10000</strong>
US odds, i.e. decimal 1.40 to 101.00, applied to our model prices (no bookmaker price was verified). The table below also shows rows held by the official-start, freshness or conflict gates. They are published as MEDIUM, with the reason, rather than stretched into a band
they do not fit.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Ref</th><th>Sport</th><th>Match</th><th>Selection</th><th class="num">Decimal</th><th class="num">US odds</th><th>Why not HIGH</th></tr></thead>
<tbody>{band_blocked_rows}</tbody></table></div>

</details><h2 id="research-board">Every captured record</h2>
<div class="tools">
  <input id="q" type="search" placeholder="Search team, competition or sport&hellip;" aria-label="Search fixtures">
  <select id="fsport" aria-label="Filter by sport"><option value="">All sports</option>
  {''.join(f'<option>{e(s)}</option>' for s in SPORT_ORDER if by_sport.get(s))}</select>
  <select id="fconf" aria-label="Filter by confidence"><option value="">All confidence</option>
  <option>HIGH</option><option>MEDIUM</option><option>LOW</option></select>
  <select id="frelease" aria-label="Filter by publication status"><option value="">All captured rows</option>
  <option value="upcoming">Official start ahead / source fresh</option><option value="source_conflict">Source conflict — held</option>
  <option value="unverified_start">Start unverified</option><option value="past_date">Past-date archive</option>
  <option value="stale_source">Stale source</option><option value="start_window_reached">Scheduled start passed</option></select>
  <button type="button" id="reset-filters">Reset filters</button>
  <span id="count" class="count" aria-live="polite"></span>
</div>
<p class="legend"><strong>Our odds</strong> are uncalibrated estimates, not observed bookmaker prices.
The -250..+10000 badge applies to the originated price only. <strong>Official source</strong> refers to the recorded fixture confirmation,
not a guarantee of current form. <a href="lines.html">Handicaps, totals and both outcome prices →</a></p>
{table(EVENTS, 'tbl-all')}

<h2>The other track: the official feed</h2>
<div class="panel"><p>A second, independent pipeline in this repo pulls official NHL / MLB / NBA schedule feeds hourly
(<code>api-web.nhle.com</code>, <code>statsapi.mlb.com</code>, <code>cdn.nba.com</code>) and publishes the raw fixtures with <em>no</em> picks,
lines or prose &mdash; its validator fails the build if any betting field is filled. It is kept separate on purpose: facts with a
digest, next to our model output with a label. Its current snapshot holds <strong>{n_feed}</strong> fixture records.</p>
<p><a href="feed-overview.html">Feed overview</a> &middot; <a href="matches.html">Feed matches</a> &middot;
<a href="coverage.html">Feed coverage</a> &middot; <a href="markets.html">Feed method</a> &middot; <a href="review.html">Feed review</a></p></div>

<h2>How to read this board</h2>
<div class="grid2">
  <div class="panel"><h3>What is verified</h3><p>Fixture, opponent, date and time are checked against the competition&rsquo;s own site
  (NBA.com, NHL.com, MLB.com, ATP Tour, WST, CSA, URC, LNR, ICEHL &hellip;) and the link is in the row. A row that only has a
  reputable third-party listing says <em>corroborated</em>; a row with neither says <em>unverified</em>. We leave the competition blank
  rather than guessing it from a club name, and we never promote a third-party link to &ldquo;official&rdquo;.</p></div>
  <div class="panel"><h3>What is ours</h3><p>Prices, handicap lines, totals and picks are produced by our own model
  (<a href="method.html">method</a>). They are opinions priced off disclosed inputs, not facts, and not bookmaker prices.</p></div>
</div>
""" + foot(0)

# ---------- executive summary (today.html) ----------
# One page that answers the three questions the board has to answer at a glance:
# what are the matches, what is the pick, and where does the evidence live.
from datetime import date as _date, timedelta as _td

BC = json.load(open(os.path.join(ROOT, "data/brief_coverage.json")))
OLBG_PREDS = json.load(open(os.path.join(ROOT, "data/predictions-olbg.json")))["predictions"]
OLBG_HIGH = [p for p in OLBG_PREDS if p.get("status") == "high"]
TODAY = AS_OF.isoformat()
HORIZON = (AS_OF + _td(days=3)).isoformat()


def _kick(r):
    return (r["pick"].get("release") or {}).get("start_utc") or r["pick"].get("kickoff_utc") or ""


def _hhmm(iso):
    return iso[11:16] + "Z" if len(iso) >= 16 else ""


LIVE_HIGH = sorted([r for r in EVENTS if r["pick"]["confidence"] == "HIGH"
                    and (r["pick"].get("release") or {}).get("status") == "upcoming"],
                   key=lambda r: (_kick(r), r["sport"], r["ref"]))


def _high_row(r):
    p = r["pick"]
    pred = PREDS.get(r["ref"])
    src = r["verification"]
    link = (f"<a href='predictions.html#{e(r['ref'])}'>read the write-up</a>" if pred
            else "<span class='dim'>no write-up</span>")
    return (f"<tr><td><a href='sports/{r['sport_slug']}.html'>{e(r['sport'])}</a>"
            f"<br><span class='dim small'>{e(r.get('competition') or '')}</span></td>"
            f"<td><strong>{e(r['home'])} v {e(r['away'])}</strong><br>"
            f"<span class='small'>{e(r['start'])} listed &middot; {e(_hhmm(_kick(r)))} UTC official</span></td>"
            f"<td class='pick'>{e(p['label'])}<br><span class='small'>{e(_selection_market(r.get('market_type', 'fixture')))}</span></td>"
            f"<td class='num'>{money(p['price'])}<br><span class='small'>{usd(p['price'])}</span></td>"
            f"<td class='num'>{p['prob']*100:.0f}%</td>"
            f"<td>{conf_pill(p['confidence'])}</td>"
            f"<td>{link}<br>{ver_cell(r)}</td></tr>")


TODAY_UPCOMING = sorted([r for r in EVENTS if r["pick"].get("start_iso")
                         and TODAY <= r["pick"]["start_iso"] <= HORIZON],
                        key=lambda r: (r["pick"]["start_iso"], r["sport"], r["ref"]))
by_sport_up = defaultdict(list)
for _r in TODAY_UPCOMING:
    by_sport_up[_r["sport"]].append(_r)
up_rows = ""
for _s in SPORT_ORDER:
    _rows = by_sport_up.get(_s) or []
    if not _rows:
        continue
    _hi = len([x for x in _rows if x["pick"]["confidence"] == "HIGH"])
    _pr = len([x for x in _rows if x["pick"]["price"]])
    _next = sorted(_rows, key=lambda r: r["pick"]["start_iso"])[0]
    up_rows += (f"<tr><td><a href='sports/{_next['sport_slug']}.html'>{e(_s)}</a></td>"
                f"<td class='num'>{len(_rows)}</td><td class='num'>{_pr}</td><td class='num'>{_hi}</td>"
                f"<td>{e(_next['home'])} v {e(_next['away'])}<br><span class='small'>{e(_next['start'])}</span></td></tr>")
if not up_rows:
    up_rows = "<tr><td colspan='5'>No dated fixture inside the next three days.</td></tr>"

cov_rows2 = ""
for _s in SPORT_ORDER:
    _c = next((x for x in BC["sports"] if x["sport"] == _s), None)
    if not _c:
        continue
    _state = ("<span class='pill high'>target met</span>" if _c["meets_target"]
              else f"<span class='pill med'>short by {_c['shortfall']}</span>")
    cov_rows2 += (f"<tr><td><a href='sports/{SPORT_META.get(_s, {}).get('slug', '')}.html'>{e(_s)}</a></td>"
                  f"<td class='num'>{_c['root_high']}</td><td class='num'>{_c['olbg_high']}</td>"
                  f"<td class='num'>{_c['live_high_union']} / {_c['target']}</td><td>{_state}</td></tr>")

olbg_high_rows = "".join(
    f"<tr><td>{e(p['sport'])}</td><td>{e(p['match'])}</td><td class='pick'>{e(p['selection'])}</td>"
    f"<td><a href='olbg/predictions.html'>OLBG lines board write-up</a></td></tr>"
    for p in OLBG_HIGH) or "<tr><td colspan='4'>No high-confidence pick on the OLBG lines board.</td></tr>"

# Blocks the merged pick surface needs, computed once so the page and its counts cannot drift.
today_prose_note = (
    '<div class="notice"><strong>Prose rule check.</strong> '
    + str(len([1 for x in PICK_LIVE for _k in x["tracks"] if x["tracks"][_k].get("text")]))
    + ' published piece(s) on the live list were measured against the brief&rsquo;s two output rules '
      '(at least 30 words; no internal vocabulary in the reader-facing text). '
    + (f'{len(PROSE_DEFECTS)} fail: ' + "; ".join(f"{e(a)} {e(b)} ({e(c)})" for a, b, c in PROSE_DEFECTS[:6])
       + ' — published rather than quietly reworded.' if PROSE_DEFECTS else
       'None fails: every card you can read below satisfies both, and <code>tools/check_site.py</code> and '
       '<code>scripts/check_board.py</code> re-check the same rule on every build.')
    + '</div>')

_disagree = [x for x in PICK_LIVE if len({(t.get("selection") or "").lower() for t in x["tracks"].values()}) > 1]
today_held_block = (
    '<details class="research-details"><summary>Held back from the pick list '
    + str(len(PICK_HELD)) + ' row(s) graded HIGH that we are not publishing as a pick)</summary>'
    '<p class="legend">These carry a HIGH evidence grade and are not shown as picks: the official start has '
    'passed, the source observation is over 24 hours old, the price sits outside -250 to +10000, or no written '
    'prediction exists for the selection. They stay visible so the count cannot be inflated by a bare name.</p>'
    + (picks_cards(PICK_HELD) or "<p class='dim'>Nothing is being held back at this build.</p>")
    + '</details>')

# Per-sport scoreboard: what the brief asks for, what this merged list can actually support,
# and the board's own mechanical reason for every gap (from data/brief_coverage.json).
_sf_rows = []
for _s in SPORT_ORDER:
    _acct = next((x for x in BC["sports"] if x["sport"] == _s), None)
    _n = len(PICK_BY_SPORT.get(_s) or [])
    _slug = (SPORT_META.get(_s) or {}).get("slug", "")
    if _n >= 5:
        _state = '<span class="pill high">target met</span>'
    elif _n:
        _state = f'<span class="pill med">short by {5 - _n}</span>'
    else:
        _state = '<span class="pill low">no written pick today</span>'
    _reason = ((_acct or {}).get("reasons") or [""])[0]
    _sf_rows.append(f"<tr><td><a href='sports/{_slug}.html'>{e(_s)}</a></td>"
                    f"<td class='num'>{_n} / 5</td><td>{_state}</td>"
                    f"<td class='num'>{(_acct or {}).get('root_high', 0)}</td>"
                    f"<td class='num'>{(_acct or {}).get('olbg_high', 0)}</td>"
                    f"<td class='small'>{e(_reason) or 'not itemised by the accounting step'}</td></tr>")
today_shortfall_block = (
    '<h2 id="per-sport">Five written picks per sport, counted honestly</h2>'
    '<p class="dim">The brief asks for the five highest-confidence written picks for every covered sport, every day. '
    'The count below is what this merged list can actually support: the same fixture priced by both boards is one '
    'entry, a selection without a write-up is not counted, and nothing is promoted to close a gap. The last column '
    'is the board&rsquo;s own mechanical reason for the shortfall, recomputed by <code>scripts/brief_coverage.py</code> '
    'and re-checked by <code>scripts/check_board.py</code>.</p>'
    '<div class="tablewrap"><table class="board"><thead><tr><th>Sport</th><th class="num">Written picks</th>'
    '<th>Against the five-a-day target</th><th class="num">Main board HIGH</th><th class="num">OLBG board HIGH</th>'
    '<th>Why it falls short</th></tr></thead><tbody>' + "".join(_sf_rows) + '</tbody></table></div>'
    + (f'<p class="legend"><strong>Where the two boards disagree on a live fixture:</strong> {len(_disagree)} '
       'of the entries above carries a different selection on each board. Both are published on the card, and the '
       'pair sits on <a href="reconcile.html">Cross-track review</a> for a human to judge.</p>' if _disagree else ''))



today_page = head("Today's picks — executive summary") + f"""
<section class="hero">
  <p class="eyebrow">EXECUTIVE SUMMARY &middot; {TODAY} &middot; BUILD {CLOCK}</p>
  <h1>Today’s picks, in one place.</h1>
  <p class="lede">Every high-confidence pick we are currently publishing, with the match, the selection, the price,
  the confidence grade, the written prediction and the official source, on one page. The main board carries
  {len(LIVE_HIGH)} live high-confidence rows and the OLBG lines board {len(OLBG_HIGH)}; {pick_paired} of those fixtures are
  priced by both boards, so the two lists fold into <strong>{len(PICK_LIVE)} distinct written picks</strong> below — one card per
  match, each board's own call and price on it. A fixture with a selection but no written prediction is not counted
  as a pick, whatever its grade, and is listed further down with the reason.</p>
  <p class="hero-actions"><a class="button" href="#shortlist">Jump to the picks ↓</a>
  <a class="button secondary" href="#per-sport">Browse all 15 sports</a>
  <a class="button secondary" href="method.html">How a pick is graded</a></p>
</section>

<div class="notice">
  <strong>How to read this page.</strong> A pick is <em>live</em> only while its official start is ahead of the build clock
  and its source observation is under 24 hours old. Prices are <strong>our own originated lines</strong>, not bookmaker odds.
  Every row links to the official source used to confirm the fixture and to the full written prediction.
  Anything we could not confirm is left blank and published on <a href="flagged.html">Flagged for Review</a>.
</div>

<h2 id="shortlist">Executive shortlist — what to pick and where to read it</h2>
<p class="legend">Ordered by official UTC start. These are research selections with independent estimated prices,
not bookmaker quotes or proof that OLBG currently accepts a tip. HIGH describes evidence confidence, not a guaranteed
outcome or a 70% win probability. An official fixture link confirms scheduling, not every claim in the analysis.
Injury information is not assumed when an official match-specific report is absent. The selected market is separate
from OLBG&rsquo;s captured featured market; current availability and settlement rules are unconfirmed.</p>
{_pick_table(PICKS)}
<h2 id="written-picks">The picks, written out &mdash; both boards, one list</h2>
<p class="lede">{PICK_SUMMARY} Every entry below is de&#8209;dupicated on the OLBG event id, so a fixture priced by both
boards appears once, with each board&rsquo;s own price and its own written piece underneath it. A selection with no written
prediction is not a pick and is listed separately, not promoted.</p>
<p class="notice"><strong>{sum(x.get('start_utc', '')[:10] == TODAY for x in PICK_LIVE)} current written picks start today (UTC);
{sum(x.get('start_utc', '')[:10] != TODAY for x in PICK_LIVE)} start on later dates.</strong>
The five-per-sport counts below include all upcoming starts, not five fixtures in every sport today.</p>
{today_prose_note}
<section class="pick-grid">{picks_sport_sections(PICK_BY_SPORT)}</section>
{today_held_block}
{today_shortfall_block}
<details><summary>Inspect the main board’s research grades</summary>
<h2 id="live-high">Root-track HIGH research rows</h2>
<p class="dim">Raw grading rows below may include selections held from the executive shortlist because current OLBG availability is unconfirmed. The shortlist above is the current written-pick list. Counts are as of the build clock; expired browser labels override them. Sorted by official start time. “Listed” is what OLBG printed; “UTC” is the competition’s own clock, converted only when the source states its zone.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th>Match &amp; start</th><th>Selection</th><th class="num">Our price</th><th class="num">Chance</th><th>Conf.</th><th>Prediction &amp; source</th></tr></thead>
<tbody>{''.join(_high_row(r) for r in LIVE_HIGH) or "<tr><td colspan='7'>No live high-confidence pick at this build.</td></tr>"}</tbody></table></div>

</details>
<h2>What is coming up in the next three days</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th class="num">Fixtures</th><th class="num">Priced</th><th class="num">High conf.</th><th>Next fixture</th></tr></thead>
<tbody>{up_rows}</tbody></table></div>
<p class="dim">Every captured fixture, with our win price, handicap and total, is on <a href="index.html#research-board">the dashboard</a>
and on the sport pages. <a href="lines.html">Handicaps and totals →</a></p>

<details><summary>Raw research-grade accounting (not the current shortlist)</summary>
<h2>Five-per-sport research accounting</h2>
<p class="dim">Current written-pick counts are in the per-sport table above; the figures below are independent-track grading totals, including held-back listing entries. The brief asks for five high-confidence picks for every sport we cover, every day. This table is the honest count:
it includes both boards and it does not promote a pick to close a gap. The blocker for each shortfall is itemised on
<a href="brief.html">Brief coverage</a>.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th class="num">Main board HIGH</th><th class="num">OLBG board HIGH</th><th class="num">Distinct live</th><th>Status</th></tr></thead>
<tbody>{cov_rows2}</tbody></table></div>
<div class="notice brief-summary"><strong>Against the brief:</strong> {BC['totals']['live_high_union']} distinct live high-confidence picks
today across {BC['totals']['sports_listed']} covered sports, against a daily target of {BC['totals']['target_picks_if_all_sports_met']}.
{BC['totals']['sports_meeting_target']} sport(s) meet the five-pick target; shortfall {BC['totals']['shortfall_to_target']}.
<a href="brief.html">See the per-sport blockers →</a></div>

</details>
<details class="research-details"><summary>High-confidence picks on the OLBG lines board ({len(OLBG_HIGH)})</summary>
<p class="dim">The second board prices the same OLBG capture with a different method and its own release gate. These are its current high-confidence pieces.</p>
<div class="tablewrap"><table class="board"><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Write-up</th></tr></thead>
<tbody>{olbg_high_rows}</tbody></table></div>
<p class="dim"><a href="olbg/index.html">Open the OLBG lines board →</a></p>
</details>

<h2>Where everything lives</h2>
<div class="grid2">
  <div class="panel"><h3>Picks</h3><p>This page is the short list. The full written set is on
  <a href="predictions.html">Predictions</a>; our win prices, handicaps and totals for every captured fixture are on
  <a href="lines.html">Originated lines</a>.</p></div>
  <div class="panel"><h3>Evidence</h3><p><a href="verification.html">Verification</a> records what each official source confirmed,
  <a href="source-health.html">Source health</a> shows how old each observation is, and <a href="flagged.html">Flagged for Review</a>
  lists every conflict and unverified field.</p></div>
</div>
""" + foot(0)
open(os.path.join(OUT, "today.html"), "w").write(today_page)

open(os.path.join(OUT, "index.html"), "w").write(index)

# ---------- predictions ----------
pblocks = ""       # rows currently graded HIGH and inside the band
kept_blocks = ""   # medium-confidence analysis: price outside the band or kick-off passed
_ordered = sorted(PREDS.items(), key=lambda kv: (
    0 if next((r["pick"]["confidence"] for r in EVENTS if r["ref"] == kv[0]), "") == "HIGH" else 1,
    next((x["sport"] for x in EVENTS if x["ref"] == kv[0]), ""),
    next((x["start"] for x in EVENTS if x["ref"] == kv[0]), "")))
for ref, p in _ordered:
    r = next((x for x in EVENTS if x["ref"] == ref), None)
    if not r: continue
    _downgraded = r["pick"]["confidence"] != "HIGH"
    pr = r["model"]["prices"]; side = r["pick"]["side"]
    price = pr.get("win_home") if side == "home" else pr.get("win_away")
    facts = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["label"])}</a></li>' for s in p["sources"])
    _why = r["pick"].get("note") or p.get("downgrade_reason") or ("the price is outside the requested -250..+10000 band" if _downgraded else "")
    _note = (f'<p class="note">Retained as research analysis, not a current high-confidence pick: {e(_why)}</p>' if _downgraded else '')
    _kick = r["pick"].get("kickoff_utc")
    _release = r["pick"].get("release", {})
    _clock = (f'<p class="note">Official UTC start: {e(_kick)} · source observed {e(_release.get("checked_at"))}. '
              f'{e(_release.get("reason"))}</p>' if _kick else
              f'<p class="note">Exact official UTC start unverified. {e(_release.get("reason"))}</p>')
    _prob = f'{r["pick"]["prob"]*100:.0f}%' if r['pick'].get('prob') is not None else 'withheld'
    _block = f"""
<article class="prediction" id="{e(ref)}" data-expires-at="{e(_release.get('expires_at') or '')}" data-release="{e(_release.get('status') or 'unverified_start')}" {'data-current-high="true"' if not _downgraded else ''}>
  {_note}
  <div class="pmeta"><span class="tag">{e(r['sport'])}</span> <span class="tag">{e(ref)}</span> {conf_pill(r['pick']['confidence'])} {band_badge(r)}</div>
  <h2>{e(p['headline'])}</h2>
  <p class="fixture">{match_label(r)} &middot; <span class="when">{e(r['start'])} (OLBG)</span>
     {('&middot; ' + e(r['verification']['official_datetime'])) if r['verification'].get('official_datetime') else ''}</p>
  {_clock}
  <p class="selection">Betting selection: <strong>{e(p['selection'])}</strong>
     <span class="pricebox">our price {money(price)} ({usd(price)} US) &middot; model {_prob}</span></p>
  <p class="body">{e(p['body'])}</p>
  <p class="srcs"><strong>Factual sources (selection and prices are our estimates):</strong></p><ul class="sourcelist">{facts}</ul>
</article>"""
    if _downgraded:
        kept_blocks += _block
    else:
        pblocks += _block

n_hi_preds = pblocks.count('<article class="prediction"')
n_kept = kept_blocks.count('<article class="prediction"')
kept_section = (f'<h2>Medium-confidence analysis ({n_kept})</h2><p class="dim">These write-ups were produced for picks that were '
                f'graded HIGH before the price-band correction. Their selection now prices shorter than -250 (or its kick-off has passed), '
                f'so the row is MEDIUM and the piece is not counted among the high-confidence picks. Nothing is hidden: the analysis, its '
                f'price and the reason for the downgrade are all shown.</p>' + kept_blocks) if n_kept else ""

predpage = head("Predictions") + f"""
<section class="pagehead">
  <h1>Written predictions &mdash; high-confidence picks inside the band</h1>
  <p class="lede">{len([r for r in EVENTS if r['pick']['confidence']=='HIGH'])} picks clear the high-confidence bar ({n_hi_started} of them had already kicked off when this page was built and say so on the card): an officially verified fixture,
  official current-form data for both sides, a model probability of at least 55%, <em>and</em> a price inside the requested
  <strong>-250 to +10000</strong> US band. Every sentence that states a fact carries a source link. Picks that fail the price test are
  kept below as clearly labelled medium-confidence analysis rather than passed off as high confidence.</p>
  <p class="note">The grade is only available to a row whose fixture is on the competition&rsquo;s own site (or one of the two clubs&rsquo; own
  sites). A row that rests on a third-party listing is labelled <em>corroborated</em> and can never be graded high confidence.
  <code>check_board.py</code> fails the build if a HIGH row has no prediction, if a HIGH price escapes the band, or if a HIGH pick&rsquo;s
  kick-off has passed.</p>
</section>
<h2>High-confidence predictions ({n_hi_preds})</h2>
{pblocks}
{kept_section}
""" + foot(0)
open(os.path.join(OUT, "predictions.html"), "w").write(predpage)

# ---------- automated public OLBG discovery ----------
from discovery import OFFICIAL_REFERENCES


def load_discovery(root):
    """The published discovery payload, reproducible from the committed tree.

    ``data/discovery.json`` is a gitignored runtime artifact written only by
    ``scripts/discovery.py`` (which needs a network route this build does not have). The
    published page artifact ``discovery.json`` in the repo root *is* committed. A clean
    checkout used to fall through to an empty scaffold here, so the next
    ``build_site.py --snapshot`` copied that scaffold over the real published payload: a
    rebuild without a discovery run silently replaced 15 sourced rows with "not attempted".
    Prefer the fresh runtime capture, then the last committed payload, and only then an
    explicitly empty document.
    """
    for candidate in (os.path.join(root, 'data', 'discovery.json'),
                      os.path.join(root, 'discovery.json')):
        if os.path.exists(candidate):
            with open(candidate) as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    return {'attempted_at': None, 'events': [], 'sources': [], 'robots': {'state': 'not attempted'}}


_discovery = load_discovery(ROOT)
_discovery_rows = ''.join(
    f'<tr data-sport="{e(r["sport"])}"><td>{e(r["sport"])}</td><td><a href="{e(r["olbg_url"])}">{e(r["title"])}</a></td>'
    f'<td>{e(r["observed_at"])}</td><td></td><td></td><td>Unverified — discovery only; no inferred facts or prices</td>'
    f'<td><a href="{e(r["official_reference"])}">Official reference (not fixture verification)</a></td></tr>'
    for r in _discovery.get('events', []))
_discovery_sources = ''.join(
    f'<tr><td>{e(r["sport"])}</td><td>{e(r["state"])}</td><td>{r["count"]}</td><td>{e(r.get("fetched_at"))}</td>'
    f'<td>{e(r["detail"])}</td><td><a href="{e(r["url"])}">OLBG public listing</a> · '
    f'<a href="{e(r["official_reference"])}">official sport reference</a></td></tr>' for r in _discovery.get('sources', []))
_discovery_body = head('Current discovery') + f"""
<section class="pagehead"><p class="eyebrow">AUTOMATED DISCOVERY · OFFICIAL VERIFICATION SEPARATE</p>
<h1>What the public listings expose</h1><p class="lede">A bounded, robots-aware hourly scan of the eligible OLBG sport pages.
Actual linked text and URLs only: no clock, league, form, winner or price is invented from a URL slug.</p></section>
<div class="notice">Latest attempt: {e(_discovery.get('attempted_at'))}. Robots policy: {e(_discovery.get('robots', {}).get('state'))}.
This is <strong>partial public-HTML discovery, not a complete upcoming match list</strong>. Dynamic, hidden and “load more” content may be missing;
blocked or unparseable pages remain explicitly unverified. New events do not inherit an old event’s source verification or model.</div>
<p><a href="discovery.json">Download discovery and collection-health JSON</a> · <a href="matches.html">Verified official-feed fixtures →</a></p>
<h2>Source health by sport</h2>
<div class="tablewrap"><table class="board"><thead><tr><th>Sport</th><th>Result</th><th>Links seen</th><th>Observed UTC</th><th>Limit / error</th><th>Sources</th></tr></thead><tbody>{_discovery_sources}</tbody></table></div>
<h2>Observed event references</h2><label for="discovery-search">Search observed link text or sport</label>
<input type="search" id="discovery-search" placeholder="Team, player or sport…">
<div class="tablewrap"><table class="board" id="discovery-table"><thead><tr><th>Sport</th><th>Observed link text / OLBG source</th><th>Observed UTC</th><th>Official UTC start</th><th>Verified price</th><th>Verification</th><th>Official reference</th></tr></thead><tbody>{_discovery_rows}</tbody></table></div>
<p class="dim">An empty discovery table means no parseable references were collected, not that no matches exist.
Blank start and price cells are unverified, never zero. Football exclusions follow the board’s documented scope; Gaelic football remains an explicitly flagged ambiguity.</p>
""" + foot(0)
open(os.path.join(OUT, 'discovery.html'), 'w').write(_discovery_body)
json.dump(_discovery, open(os.path.join(OUT, 'discovery.json'), 'w'), indent=2)

# ---------- source health / row-level release audit ----------
health_rows = ""
for r in EVENTS:
    rel = r['pick'].get('release', {})
    source = rel.get('source') or (r['verification'].get('official_url') if r['verification']['status']=='verified' else '')
    if not source:
        source = GOVERNING_PORTAL.get(r['sport'], ('https://www.olbg.com/betting-tips',''))[0]
    health_rows += (f'<tr><td>{e(r["ref"])}</td><td>{match_label(r)}</td><td>{e(rel.get("status"))}</td>'
                    f'<td>{e(rel.get("start_utc"))}</td><td>{e(rel.get("checked_at"))}</td><td>{e(rel.get("expires_at"))}</td>'
                    f'<td>{e(rel.get("reason"))}</td><td><a href="{e(source)}">official source / reference</a>'
                    f' · <a href="{e(r["olbg_event_url"])}">OLBG capture</a></td></tr>')
checks_doc = json.load(open(os.path.join(ROOT, 'data/release_checks.json')))
observations = ''.join(f'<tr><td>{e(ident)}</td><td>{e(c["checked_at"])}</td><td>{e(c["quote"])}</td>'
                       f'<td><a href="{e(c["source"])}">official observation</a>'
                       + (f' · <a href="{e(c["conflicting_source"])}">conflicting official source</a>' if c.get('conflicting_source') else '')
                       + '</td></tr>' for ident,c in checks_doc['events'].items())
health = head('Source health') + f"""
<section class="pagehead"><p class="eyebrow">PROVENANCE, NOT JUST LINKS</p><h1>Source health &amp; release checks</h1>
<p class="lede">Publication as of {CLOCK}. A source URL is not proof that the page supports a claim.
This register distinguishes a previously recorded fixture confirmation from a newly checked exact start.</p></section>
<div class="notice">Blank UTC starts are intentional. “Not before”, “followed by”, a session start, a date-only draw or a
personalized clock cannot establish an exact match time. HIGH is an uncalibrated research grade, not a guaranteed win rate
or proof of value. No observed bookmaker price was verified; the -250..+10000 test applies to our originated price only.</div>
<p><a href="research.json">Download model rows and release metadata (JSON)</a> · <a href="flagged.html">Flagged for Review</a></p>
<h2>Official observations made in this pass</h2>
<p class="dim">These are the observations actually retrieved and read, not a claim that all other historical rows were independently reverified.
Paired official sources that disagree are both linked. Mathematical timezone conversion is labelled as derived UTC, never as an OLBG value.</p>
<div class="tablewrap"><table class="board"><thead><tr><th>OLBG ID</th><th>Checked UTC</th><th>Source statement / dated heading</th><th>Official link</th></tr></thead><tbody>{observations}</tbody></table></div>
<h2>Every board row — publication decision</h2>
<p class="dim">An “official reference” on an unverified row is a research lead, not confirmation of that fixture. Missing normalized times and current checks stay blank.</p>
<div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Event</th><th>Status</th><th>Official → UTC start</th><th>Last checked UTC</th><th>Release expires UTC</th><th>Reason</th><th>Sources</th></tr></thead><tbody>{health_rows}</tbody></table></div>
""" + foot(0)
open(os.path.join(OUT, 'source-health.html'), 'w').write(health)
json.dump({'as_of': CLOCK, 'complete_live_coverage': False,
           'bookmaker_price_verified': False, 'events': EVENTS},
          open(os.path.join(OUT, 'research.json'), 'w'), indent=2, ensure_ascii=False)

# ---------- verification ----------
vrows = ""
for r in EVENTS:
    v = r["verification"]
    if v["status"] == "verified":
        st = "<span class='pill high'>verified</span>"
        off = f'<a href="{e(v["official_url"])}" rel="noopener">{e(v["official_label"])}</a>'
        dt = e(v.get("official_datetime", ""))
        tier = e(v.get("source_tier", "official"))
    elif v["status"] == "corroborated":
        st = "<span class='pill med'>corroborated</span>"
        off = f'<a href="{e(v["official_url"])}" rel="noopener">{e(v["official_label"])}</a>'
        dt = e(v.get("official_datetime", ""))
        tier = e(v.get("source_tier", "third-party"))
    else:
        st = "<span class='pill low'>unverified</span>"
        off = '<span class="dim">no official source retrieved</span>'
        dt = '<span class="dim">&mdash;</span>'
        tier = '&mdash;'
    vrows += (f"<tr><td>{e(r['ref'])}</td><td>{e(r['sport'])}</td><td>{match_label(r)}</td>"
              f"<td>{e(r['start'])}</td><td>{dt}</td><td>{off}</td><td>{tier}</td><td>{st}</td>"
              f"<td><a href='{e(r['olbg_event_url'])}' rel='noopener'>OLBG event</a></td></tr>")

verpage = head("Verification") + f"""
<section class="pagehead">
  <h1>Row-by-row verification log</h1>
  <p class="lede">Each row records what OLBG showed, what the source says, and the link. {n_verified} rows are confirmed against the
  competition&rsquo;s own site, {n_corroborated} are <em>corroborated</em> by a reputable third party only, and {n_unverified} are unverified
  because no source was retrieved for them &mdash; those are published with the field blank rather than filled from inference. The
  <strong>source tier</strong> column is the point: a third-party listing is never counted as official confirmation.</p>
</section>
<div class="tablewrap"><table class="board">
<thead><tr><th>Ref</th><th>Sport</th><th>Match</th><th>OLBG start</th><th>Official fixture (verbatim)</th><th>Source</th><th>Source tier</th><th>Status</th><th></th></tr></thead>
<tbody>{vrows}</tbody></table></div>
<h2>Method of checking</h2>
<ol class="steps">
  <li>Read the fixture off the OLBG sport listing, then off the individual OLBG event page URL recorded in the row.</li>
  <li>Find the same fixture on the competition&rsquo;s own website (official scheduler / match centre / standings), or on one of the two clubs&rsquo; own sites. A broadcaster, aggregator or independent database is recorded as <em>corroborated</em> only.</li>
  <li>Copy the official wording verbatim into the row. Do not convert time zones, do not round, do not &ldquo;fix&rdquo; a discrepancy &mdash; log it.</li>
  <li>If step 2 fails, the row keeps its OLBG data, the official column stays blank, and the row appears on Flagged for Review.</li>
</ol>
""" + foot(0)
open(os.path.join(OUT, "verification.html"), "w").write(verpage)



# ---------- originated lines (every market we priced, in one table) ----------
def _ml(r):
    pr = r["model"].get("prices") or {}
    if not pr:
        return '<span class="dim">no price</span>'
    if "single" in pr:
        return f'{money(pr["single"])} <span class="dim small">single selection</span>'
    if pr.get("draw") is not None:
        return f'{money(pr.get("win_home"))} / {money(pr.get("draw"))} / {money(pr.get("win_away"))}'
    return f'{money(pr.get("win_home"))} / <span class="dim">n/p</span> / {money(pr.get("win_away"))}'


def _hc(r):
    h = r["model"].get("handicap")
    if not h:
        return '<span class="dim" title="No defensible scoring unit for this sport, so no line was originated">not quoted</span>'
    unit = h.get("unit", "")
    fav = r["home"] if h["fav"] == "home" else r["away"]
    dog = r["away"] if h["fav"] == "home" else r["home"]
    return (f'{e(fav)} -{abs(h["line"]):.1f} {e(unit)} <span class="dim">@ {money(h["price"])}</span><br>'
            f'{e(dog)} +{abs(h["dog_line"]):.1f} {e(unit)} <span class="dim">@ {money(h["dog_price"])}</span>')


def _tt(r):
    t = r["model"].get("total")
    if not t:
        return '<span class="dim">not quoted</span>'
    return (f'<strong>{t["line"]}</strong> {e(t.get("unit",""))}<br>'
            f'over {money(t.get("over"))} &middot; under {money(t.get("under"))}')


line_rows = "".join(
    f"<tr><td class='ref'><a href='{e(r['olbg_event_url'])}' rel='noopener'>{e(r['ref'])}</a></td><td>{e(r['sport'])}</td>"
    f"<td class='match'>{match_label(r)}</td><td>{e(r['start'])}</td><td class='num'>{_ml(r)}</td>"
    f"<td class='small'>{_hc(r)}</td><td class='small'>{_tt(r)}</td>"
    f"<td class='basis'>{e(r['model'].get('basis','none'))}</td><td class='src'>{ver_cell(r)}</td></tr>"
    for r in EVENTS)

gap_block = "".join(
    f"<li><strong>{e(sp)}</strong> &mdash; {e(reason)}</li>" for sp, reason in HANDICAP_GAP.items())

linespage = head("Originated lines") + f"""
<section class="pagehead">
  <h1>Every line we originated, in one table</h1>
  <p class="lede">This is the whole point of the project: for each fixture we price the <strong>match winner</strong>, a
  <strong>handicap</strong> and a <strong>match total</strong> ourselves, then grade a pick. None of these numbers is a bookmaker quote.
  {sum(1 for r in EVENTS if r['model'].get('prices'))} of {n_events} rows carry a price, {n_hcap} carry a handicap and {n_total} carry a total.
  Where a market is missing the cell says so and the reason is written below &mdash; we leave it blank instead of inventing a number.</p>
</section>
<div class="cards">
  <div class="card"><span class="k">{sum(1 for r in EVENTS if r['model'].get('prices'))}</span><span class="l">rows with a money line</span></div>
  <div class="card"><span class="k">{n_hcap}</span><span class="l">rows with a handicap</span></div>
  <div class="card"><span class="k">{n_total}</span><span class="l">rows with a total</span></div>
  <div class="card"><span class="k">{sum(1 for r in EVENTS if (r['model'].get('handicap') or {}).get('basis')=='official-form')}</span><span class="l">handicaps from official form</span></div>
</div>
<p class="legend"><strong>Money line:</strong> home / draw / away decimal prices, 5% price haircut; <strong>n/p</strong> = not priced because the only input
was a tip share on a different market. <strong>Handicap:</strong> our line in the sport&rsquo;s own scoring unit, priced at 1.91 each side.
<strong>Total:</strong> quoted only where an official scoring baseline exists. <strong>Basis</strong> tells you what the model was fed:
<code>official-form</code> (official league table/standings), <code>consensus-scaled</code> (the public tip share plus a disclosed
margin scale), <code>consensus</code> (tip share only), <code>single-selection</code> (outright/race market).</p>
<div class="tablewrap"><table id="tbl-lines" class="board">
<thead><tr><th>Ref</th><th>Sport</th><th>Match / event</th><th>Start (as listed)</th><th class="num">Money line</th>
<th>Handicap (our line)</th><th>Match total</th><th>Basis</th><th>Source</th></tr></thead>
<tbody>{line_rows}</tbody></table></div>

<h2>Markets we deliberately did not quote</h2>
<ul class="tight">
  <li><strong>Match totals outside rugby union and ice hockey.</strong> {TOTAL_GAP}</li>
  {gap_block}
  <li><strong>Handicaps on outright and race rows</strong> (golf tournaments, the F1 race and championship markets, greyhound races, rugby league futures, the All-Ireland championship): a one-selection market has no opponent to give a start to.</li>
</ul>

<h2>How a line is produced</h2>
<ol class="steps">
  <li><strong>Official form</strong> &mdash; where the competition publishes a table, expected score is built from it (points/goals for and against), the two sides are compared, and a projected margin and combined score fall out of that.</li>
  <li><strong>Probability implied</strong> &mdash; where there is no official table, the only input is the public tip share. The win probability is turned into a margin with a disclosed per-sport scale (Tennis 4.5 games, Basketball 13 points, Handball 7 goals, Baseball 3 runs, Volleyball 1.6 sets, Snooker 1.4 frames), and the probability is capped at 85% so a three-tip sample cannot set an extreme line. These rows are labelled <code>consensus-scaled</code> and can never be graded high confidence.</li>
  <li><strong>Half-point lines only</strong> &mdash; every handicap and total is set on a half point, so a push is impossible and the quote is unambiguous.</li>
  <li><strong>Price</strong> &mdash; 5% price haircut spread proportionally; handicap and total sides are quoted at our standard 1.91 two-way price.</li>
</ol>
""" + foot(0)
open(os.path.join(OUT, "lines.html"), "w").write(linespage)

# ---------- audit (this session's line-by-line review) ----------
AUDIT_CHECKS = [
 ("Darts European Championship &mdash; Humphries withdrawal re-read",
  "PDC announced on 22 October that Luke Humphries had withdrawn from the Machineseeker European Championship with gastroenteritis and that Kim Huybrechts would take his place against Ryan Searle. Re-opening OLBG confirmed the source had already moved: the outright page carries 12 win tips (Gerwyn Price 3/12, 25%, most popular) with no Humphries and Huybrechts added at 0/12, and the All Darts listing returns &lsquo;No tips found for Luke Humphries vs Ryan Searle&rsquo; with event id 32337 gone. The 08:30Z harvest predates the announcement. Fixed: DRT-05 and DAR-32337 are retired rather than re-pointed (OLBG lists no replacement market), and DRT-17 is re-derived from the 12-tip page to Price at 7.19 (+619), 13.2% &mdash; MEDIUM, because only 12 tips remain. Both recorded in data/live_overrides.json and on Flagged for Review.",
  "fixed", "https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship"),
 ("Price-band arithmetic &mdash; every HIGH pick is inside -250..+10000",
  "Recomputed the US odds for every published pick. Before this rebuild, 15 of 15 HIGH picks were priced shorter than -250. The full set was 1.07 = -1429, 1.08 = -1250, 1.11 = -909, 1.17 = -588, 1.18 = -556 (twice), 1.21 = -476, 1.23 = -435 (twice), 1.27 = -370, 1.28 = -357, 1.33 = -303, 1.35 = -286, 1.42 = -238 and 1.46 = -217. Cause: the grading rule required a 65% probability, and 0.95/0.65 = 1.46, so no HIGH pick could ever reach the -250 floor. The rule now requires 55% and checks the band explicitly. Result: 6 HIGH picks, 6 in band, 0 outside; 13 strong favourites are downgraded for being too short and 1 for a passed kick-off, each with the reason in its row and on Flagged for Review.",
  "fixed", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/scripts/model.py"),
 ("Pro D2 table and Round 8 fixtures &mdash; live re-read",
  "Opened prod2.lnr.fr/classement today and re-read the whole J7 table: Oyonnax 33 pts (7-0, 313-154), Provence 29, Grenoble 22 (5-2, 213-176), Brive 21, Biarritz 20 (4-1-2, 213-191), Dax 19 (269-264), Soyaux-Angouleme 17 (220-180), Montauban 17, Aurillac 16, Agen 15 (189-206, form V-D-D-V-V), Valence Romans 13 (192-190), Colomiers 12 (220-207), Nissa 11 (171-213), Beziers 9, Narbonne 9, Nevers 4. Confirmed the J8 fixtures and LNR match ids used by the new predictions: 12063 agen-nice, 12065 angouleme-dax, 12067 grenoble-biarritz, 12070 valence-romans-colomiers.",
  "match", "https://prod2.lnr.fr/classement"),
 ("MLB World Series Game 1 &mdash; live re-read",
  "MLB.com's 23 Oct schedule and postseason bracket both list World Series Game 1: Tampa Bay at Milwaukee, Friday 23 October, 8:00 PM ET, FOX. The Brewers are 103-59 with 832 runs scored and 618 allowed; the Rays are 98-64 with 736 scored and 650 allowed (+86). This re-read also caught a stored error: the 21 Oct capture had Tampa Bay at 755/645 (+110), which contradicts MLB.com's own +86 differential. The stored row was corrected to 736/650 and the prediction's 4.01 runs-allowed figure updated. The schedule lists Jacob Misiorowski (0-0) for Milwaukee and TBD for Tampa Bay.",
  "match", "https://www.mlb.com/schedule/2026-10-23"),
 ("URC table and Round 4 venue &mdash; live re-read",
  "Re-read stats.unitedrugby.com/match-centre/table/2026-27 today: Leinster 10th, 8 pts, 3 PL, 1-0-2, PF 75 / PA 58; Munster 9th, 9 pts, 1-1-1, PF 72 / PA 74, form L-W-D. Round 3 results on the same page include Ulster 26-26 Munster and Leinster 29-5 Cardiff at Laya Arena. Round 4's page lists Leinster v Munster on Sat 24 Oct at 13:00 at Aviva Stadium. The RGU-14 prediction quotes only the table figures and the draw, all of which match.",
  "match", "https://stats.unitedrugby.com/match-centre/2026-27/4"),
 ("URC league table &mdash; 4 high-confidence predictions",
  "Read every table figure quoted in the Connacht, Bulls, Stormers and Leinster predictions off the official URC table and compared it value by value: Connacht 14th on 5 pts (PF 56 / PA 84); Zebre 16th on 1 pt, 0 wins, PA 116, TA 17; Bulls 3rd on 11 pts, PF 126, DIFF +72, TA 7; Ulster 11th on 8 pts, 0 wins, 2 draws, PF 88; Stormers 4th on 11 pts, DIFF +27, PA 54; Scarlets 12th on 7 pts, PA 85; Leinster 10th on 8 pts, PA 58 (4th fewest); Munster 9th on 9 pts, PF 72 / PA 74, TA 8. Round-3 scorelines quoted (Glasgow 36-19 Connacht, Bulls 57-15 Lions, Stormers 39-22 Sharks, Zebre 12-29 Edinburgh, Scarlets 27-26 Benetton, Ulster 26-26 Munster, Leinster 29-5 Cardiff) all match the same page.",
  "match", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
 ("NHL standings &mdash; Buffalo Sabres prediction",
  "Checked the numbers in the IHO-06 prediction against the NHL standings dated 20 Oct: Buffalo 9 GP, 4-3-2, 10 PTS, home 3-2-0, GF 27, GA 34; Philadelphia 11 GP, 2-6-3, 17 GF (1.55 per game, the lowest rate in the East), away 0-4-1, current streak W2.",
  "match", "https://www.nhl.com/standings/2026-10-20/wildcard"),
 ("Formula 1 United States Grand Prix &mdash; race date and start time",
  "The official race page gives Practice 1 23 Oct 13:30-14:30, Practice 2 17:00-18:00, Practice 3 24 Oct 13:30-14:30, Qualifying 24 Oct 17:00-18:00 and the Race on 25 Oct at 16:00, at the 5.513 km Circuit of the Americas over 56 laps. OLBG lists the same row as '25 Oct 16:00'.",
  "match", "https://www.formula1.com/en/racing/2026/united-states"),
 ("OLBG event page &mdash; BKB-534889 money line",
  "Opened the OLBG event page for MIL Bucks @ WAS Wizards and compared the money-line tips: page shows WAS Wizards 9/11 (82%) and MIL Bucks 2/11 (18%), which is exactly what data/matches.json holds for that row.",
  "match", "https://www.olbg.com/betting-tips/Basketball/NBA/NBA/MIL_Bucks_@_WAS_Wizards/4?event_id=534889"),
 ("OLBG tip counts drift between captures",
  "Genesis Championship was 5/18 (30%) in the 05:20Z capture and 6/20 (30%) at 07:05Z; USA Grand Prix was 10/31 (32%) and is 11/32 (34%). OLBG recounts as tips arrive, so every share on this site is a timestamped snapshot, not a fixed fact. The two newly captured rows use the 07:05Z values.",
  "irregularity", "https://www.olbg.com/betting-tips/Golf/5"),
 ("Prediction RGU-14 asserted a venue the sources do not agree on",
  "The Leinster v Munster prediction said 'At the Aviva Stadium'. The official URC Round 3 record lists Leinster's home match at 'Laya Arena', the row's venue field is blank on this board (FL-016), and no source retrieved names a venue for the Round 4 fixture. The sentence was rewritten so the prediction no longer states a venue.",
  "fixed", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
 ("Legacy file claimed verification it does not have",
  "data/master_matches.json holds 76 rows, 71 of them marked 'Verified' and 48 marked 'High' confidence, each with a narrative containing specific figures (for example 'won seven consecutive EuroLeague home fixtures by an average of 11.2 points'). The 'official_source_url' on those rows is a sport homepage such as euroleaguebasketball.net/eurocup/ or atptour.com/en/scores, which cannot support a fixture-level or statistic-level claim. Nothing in this repo publishes that file. It has been relabelled a legacy draft and the claims are listed here for review.",
  "irregularity", "https://github.com/buffedlizard55-lab/OLBG3/blob/877def1c1c8e7456b64f5424f9ac3804126fdb15/data/master_matches.json"),
 ("README and COORDINATION board quoted numbers the site never had",
  "Both documents said '76 fixtures' and '48 detailed predictions'. The published board carries {n_events} rows and {len(PREDS)} predictions; build_full_database.py is a legacy generator whose output is not rendered anywhere. The documents now state the published figures and point at the data files that produce them.",
  "fixed", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/README.md"),
 ("Four in-scope sports were missing from the board",
  "Golf, Motor Racing, Greyhounds and Rugby League are not in the exclusion list, and the previous build disclosed them as an uncaptured gap while holding zero rows for them. All four OLBG listings were re-read at 07:05Z and 23 rows (10 golf tournaments, 1 F1 race plus 2 championship markets, 6 greyhound races, 3 rugby league outrights, 1 Gaelic football championship) are now on the board with an originated price each.",
  "fixed", "https://www.olbg.com/betting-tips/Golf/5"),
 ("Six Northern Ireland Open snooker fixtures re-read against the tour&rsquo;s own site",
  "wst.tv/matches lists all six as Round 2 on Wed 21 Oct: Match 36 Pang Junxu v Liam Davies 05:00; Match 42 Ka Wai Cheung v Stuart Bingham 05:00; Match 45 John Higgins v Jak Jones 08:00; Match 38 Sam Craigie v Xu Si 09:00; Match 39 Elliot Slessor v Jamie Jones 15:00; Match 44 Luca Brecel v Martin O&rsquo;Donnell 15:00. Every pairing and session time matches OLBG. The rows now link to those match centres instead of snooker.org.",
  "match", "https://www.wst.tv/matches/"),
 ("Eight ATP fixtures re-read against the tour&rsquo;s own draws",
  "Almaty (ATP 250): the official draw shows Nurlanuly (WC) v Machac and Mannarino v Rublev in the Round of 32/16 slots, Diaz Acosta v Basilashvili in the Round of 16, and Duckworth v Darderi in the Round of 16 with the match live on the ATP scores board. Brussels (BNP Paribas Fortis European Open): Prizmic v Dzumhur and Goffin (WC) v Bertola (LL) in the Round of 32, Damm (LL) v Cerundolo (3) and Navone (8) v Griekspoor in the Round of 16. All eight pairings match OLBG.",
  "match", "https://www.atptour.com/en/scores/current/almaty/9410/draws"),
 ("World Series Game 1 re-read against MLB.com",
  "MLB.com&rsquo;s schedule for Friday 23 October lists &lsquo;World Series, TB @ MIL, 8:00 PM ET&rsquo; with gameday id 849805. OLBG&rsquo;s label is &lsquo;23 Oct 20:00&rsquo;, which is 8:00 PM ET exactly. BSB-01 is now verified after having no official source at all.",
  "match", "https://www.mlb.com/schedule/2026-10-23?date=2026-10-23"),
 ("Two CSA fixtures re-read against Cricket South Africa",
  "cricket.co.za lists Northern Cape Heat v Garden Route Badgers on 21/10/26 at 13:00 and North West Dragons v Wenbro Impalas on 21/10/26 at 18:00, both in the Pro20 Cup 2026/27. OLBG&rsquo;s labels (07:00 and 12:00) equal those clock times once read as US Eastern, which independently supports the FL-002/FL-021 time-zone finding. The same page does not list Eastern Storm v Tuskers, so CRK-05 stays unverified.",
  "match", "https://cricket.co.za/fixtures/"),
 ("ICEHL standings replaced with the league&rsquo;s own table",
  "ice.hockey publishes the Tabelle: HCB Südtirol Alperia 1st, 11 games, 44-28, 24 pts; EC-KAC 4th, 12 games, 46-36, 21 pts; HC Pustertal 7th, 10 games, 31-27, 17 pts; Graz99ers 8th, 30-31, 17 pts; Milano 6th, 36-36; Innsbruck 10th, 30-35; Fehérvár 13th, 23-39; Pioneers Vorarlberg 14th, 0 wins, 26-52, 1 pt. These figures now drive the ice-hockey model; the numbers quoted in the IHO-01 prediction were re-checked against them and all match.",
  "match", "https://www.ice.hockey/"),
 ("Twelve rows were labelled verified on a third-party source",
  "The final host count over the 113 confirmed fixtures: 98 rest on the competition organiser&rsquo;s own domain and 6 on one of the two clubs&rsquo; own sites (both labelled verified), and 9 rest on a third party &mdash; cricinfo.com (4), espn.com (3), espncricinfo.com (1) and sofascore.com (1, BKB-03). Those 9 are labelled <em>corroborated</em>, cannot be graded HIGH and are listed on Flagged for Review. Nothing was deleted; the label was corrected.",
  "fixed", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/data/official.json"),
 ("Handicaps existed for only 22 of 114 fixtures",
  "scripts/model.py originated a handicap only where an official scoring table existed. It now derives a probability-implied line for every priced two-sided fixture in a sport with a statable scoring unit (83 rows), disclosed per-sport scales, capped at 85% probability, and labelled <code>consensus-scaled</code> where the input is a tip share. Cricket, darts and Gaelic football are deliberately left without a handicap and the reason is written on each sport page.",
  "fixed", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/docs/method.md"),
 ("WTA, volleyball and EHF sources could not be read",
  "wtatennis.com draw pages render client-side and returned navigation only; the Polish, German, Italian, Finnish and Dutch league sites returned pages without a retrievable 21&ndash;25 October fixture list; every path tried on ehfcl.eurohandball.com returned 404. No value was taken from any of them, so the 4 WTA tennis rows, 15 volleyball rows and 8 unverified handball rows stay unverified.",
  "unverified", "https://www.wtatennis.com/scores"),
 ("Official pages that could not be read are left unverified",
  "europeantour.com/genesis-championship-2026 rendered no schedule, dates or field on retrieval, and pdc.tv served a consent wall. No value was taken from either. The golf rows therefore stay unverified even though an official URL exists, and the Genesis row is published with the OLBG label only.",
  "unverified", "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/"),
]

# ---------- 2026-10-21 re-verification pass (session-7244efad) ----------
# Appended to the audit log. Each entry is a check that was actually run this session against a page
# that was actually read: the URLs below were opened, and the quoted values were copied from them.
AUDIT_CHECKS += [
 ("URC Round 4 fixtures re-read on the official Match Centre",
  "All four URC rows behind the high-confidence rugby predictions were re-read on the official Round 4 page: "
  "Connacht v Zebre Fri 23 Oct 14:45 at Dexcom Stadium; Vodacom Bulls v Ulster Sat 24 Oct 07:45 at Loftus Versfeld; "
  "DHL Stormers v Scarlets Sat 24 Oct 10:00 at DHL Stadium; Leinster v Munster Sat 24 Oct 13:00 at Aviva Stadium. "
  "Opponents, dates, kick-off times and venues match the rows on this board exactly.",
  "match", "https://stats.unitedrugby.com/match-centre/2026-27/4"),
 ("Pro D2 table and round-7 scorelines re-read on the official LNR site",
  "Every Pro D2 figure used in the four French predictions was re-read off the official classement and the round-7 results page: "
  "Oyonnax 33 pts (7-0, PF 313, PA 154); Provence 29 pts (7-0, PF 222); Brive 4th, 21 pts, +42, PF 206; Montauban 8th, 17 pts, PA 214; "
  "Aurillac 9th, 16 pts, PF 240; Beziers 14th, 9 pts, PA 240; Narbonne 15th, 9 pts, PA 296; Nevers 16th, 4 pts (0-7), PA 222. "
  "Round 7: Dax 54-28 Montauban, Colomiers 49-28 Narbonne, Beziers 24-25 Aurillac, Nevers 7-38 Agen, Nice 24-34 Provence, "
  "Oyonnax 51-25 Valence Romans, Brive 14-26 Grenoble. These readings exposed four errors in the published predictions, corrected below.",
  "fixed", "https://prod2.lnr.fr/classement"),
 ("Top 14 table and the Dupont claims re-read",
  "Toulouse: 24 pts from 6 (5-0-1), PF 197 / PA 124, diff +73, the best in the league. Perpignan: 9th, 13 pts, 3-0-3, with defeats to "
  "Montpellier (round 3) and Racing 92 (round 5), exactly as the prediction states. Dupont's two braces (Montpellier 40-18, Bayonne 45-34) "
  "and his ACL history were confirmed from match reports and the Sud Ouest piece of 18 October. The original sentence attributed a quotation "
  "to Dupont that no source carried; it now cites the report instead.",
  "fixed", "https://top14.lnr.fr/classement"),
 ("ICEHL table read on the league's own site, not only an aggregator",
  "The official ICEHL table shows Bolzano 1st on 24 pts (11 GP), Linz 2nd on 24 (12 GP), KAC 4th on 21 (12 GP), Pustertal 7th on 17 (10 GP), "
  "Innsbruck 10th on 15 (12 GP), Fehervar 13th on 13 (12 GP, GA 39) and Pioneers Vorarlberg 14th on 1 pt (12 GP, GA 52). "
  "Every figure in the four Austrian predictions matches; Fehervar's 39 goals against is second-worst only to Salzburg's 42, as now stated.",
  "fixed", "https://www.ice.hockey/saison/tabelle"),
 ("SHL standings and the Dahlen transfer",
  "Farjestad: 10 GP, 8 regulation wins, 1 OTW, 1 OTL, GF 40 / GA 11, 27 pts, first. Timra: 10 GP, 12 pts, 10th. Jonathan Dahlen scored "
  "30 goals in 50 SHL games for Timra in 2025/26 (the league's top scorer) and joined Langnau for 2026/27, confirmed on Eliteprospects' "
  "transfer record and reported by kicker. The prediction originally said the move happened over the summer; it was agreed in November 2025, "
  "so the wording now says 'to Langnau for 2026/27'.",
  "fixed", "https://www.eliteprospects.com/league/shl"),
 ("Player claims that no official source supported were removed",
  "Eight player-level statements in the published predictions could not be confirmed from any official or primary page this session: two "
  "Pustertal scorers' combined points total, an injury to a Pustertal forward, a 5-0 Bolzano win over Linz with a six-game streak, two KAC "
  "players' points totals, Brive's captain, Oyonnax's top scorer and Beziers' new centre. They were deleted rather than reworded, and the "
  "predictions were rewritten around the figures that are verified. Player facts that were confirmed (Glira, Frigo, Hundertpfund, Dahlen, "
  "Dupont) were kept and now carry their own source link.",
  "fixed", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/data/predictions.json"),
 ("IHO-01 fixture had no official source and was downgraded",
  "The Pustertal v Pioneers Vorarlberg row was marked verified on the strength of a betting-preview page (tipsterio.de), which is not an official "
  "source. The row was re-checked later the same day against the club&rsquo;s own fixture page (hcpustertal.com/matches/21-10-2026-hcp-piv/), which "
  "confirms the date and the pairing, so it is verified again at club-official tier and its prediction is restored; the kick-off time is still not "
  "readable from that page and is disclosed as an OLBG-derived value.",
  "fixed", "https://www.ice.hockey/saison/spielplan"),
 ("Five handball rows were priced off tipster consensus and are now priced off league tables",
  "The French Daikin StarLigue and Swedish Handbollsligan tables were read today (lnh.fr/daikin-starligue/classement, "
  "handbollsligan.se/herr/tabell/) and transcribed into data/official.json with every column preserved. "
  "HBL-23 (Aix v Toulouse) was 1.42 = -238 on a capped 100% tip share and is now 1.52 = -192 from the two clubs' own goal rates; "
  "HBL-21 (Onnereds v Ystads) and HBL-30 (Skanela v Karlskrona) were unpriced-by-consensus rows and now carry 1.60 and 1.70. "
  "All three verify against the leagues' own fixture lists, sit inside -250..+10000 and carry a written prediction. "
  "HBL-26 (Limoges 1.24) and HBL-27 (Selestat 1.33) are strong on the same evidence but shorter than the band floor, so they are graded MEDIUM with the reason in the row.",
  "fixed", "https://www.lnh.fr/daikin-starligue/classement"),
 ("Karlskrona naming: OLBG abbreviates a club the league prints differently",
  "OLBG lists the Swedish fixture as &lsquo;Skanela IF vs HIF Karlskrona&rsquo;. The Handbollsligan table and fixture list print "
  "&lsquo;HF Karlskrona&rsquo; (the club renamed from HIF to HF). The row keeps OLBG&rsquo;s spelling as the source value and the model uses the "
  "league&rsquo;s name for the table lookup through an explicit alias; no value was changed by inference.",
  "irregularity", "https://handbollsligan.se/herr/tabell/"),
 ("A live OLBG listing no longer matches the captured row",
  "The baseball listing was re-read today for event 160789 (TB Rays @ MIL Brewers). It now renders '24 Oct 01:00' with the featured market "
  "'Over 5.50, Game Totals, 4/4', and its money line shows MIL Brewers 4/7 (57%) and TB Rays 3/7 (43%). The captured row records "
  "'23 Oct 20:00', Money Line, TB Rays 3/6 (50%). The five-hour clock difference and the changed featured market are logged as an irregularity: "
  "the captured values are kept verbatim as a timestamped snapshot and no time is derived from them.",
  "irregularity", "https://www.olbg.com/betting-tips/Baseball/12"),
 ("F1 'Win Race' outright mis-priced as a two-way coin flip &mdash; repaired (session-f0f3be65)",
  "An independent line-by-line audit recomputed every price and found MTR-913 (USA Grand Prix, Max Verstappen) classified as a two-sided "
  "match even though it is a 22-driver outright with no home/away side. The fallback set p=0.52 and published 1.83 / -120, contradicting its "
  "own written prediction (+235 / 3.35) and the parallel root outright model. Moving the OLBG 'Win Race' label into the outright family routes "
  "the row through its disclosed 22-car field prior (p=0.284), so it now originates 3.35 / +235 and matches the prose. Only MTR-913 used the "
  "label; the high/medium/low counts are unchanged and the pick stays HIGH (verified, in the -250..+10000 band, under the 0.70 chalk cap). "
  "Logged as FL-047; formula1.com confirms the Circuit of the Americas race on 25 Oct and Verstappen's Red Bull entry.",
  "fixed", "https://www.formula1.com/en/racing/2026/united-states"),
]

AUDIT_CHANGES = [
 ("scripts/build_gap_sports.py, data/raw/gap_sports_capture_20261021.json, data/gap_sports.json",
  "Captured and priced the 23 outright/race rows for Golf, Motor Racing, Greyhounds, Rugby League and the Gaelic football championship. Prices use the documented field-size prior, not a bookmaker quote."),
 ("scripts/build_site.py",
  "Board now renders 15 sports and 137 rows, adds a Market column so a single-selection row cannot be mistaken for a two-sided one, and publishes this audit page."),
 ("data/predictions.json",
  "RGU-14 no longer states a venue that the sources disagree on. No factual claim was added. IHO-03&rsquo;s prediction was withdrawn while its only source was Eliteprospects and then restored when the Swedish Ice Hockey Association&rsquo;s schedule (stats.swehockey.se) confirmed Timra v Farjestad on 22 Oct &mdash; and corrected the venue to SCA Arena. IHO-01 was restored on the club&rsquo;s own fixture page. The board carries one written piece for every row that was HIGH at the time; after the price-band correction the HIGH set is 6 and the other 14 pieces are labelled medium-confidence analysis."),
 ("data/official.json",
  "Added 11 fixture confirmations (8 ATP, 1 MLB, 2 CSA), replaced 6 snooker sources with WST match centres, replaced 2 cricket sources with Cricket South Africa, added the official ice.hockey ICEHL table, and added a source-tier register (official / club-official / third-party) with the host list it applies to."),
 ("scripts/model.py",
  "Verification now carries a source tier and only an official or club-official source counts as verified; a third-party link becomes status 'corroborated' and forfeits the verification point. Handicaps are originated for every priced two-sided fixture in a statable scoring unit."),
 ("scripts/build_site.py",
  "Board shows the tier on every source link, adds a corroborated section to Flagged for Review, a corroborated column to the coverage table, unit and basis columns to the handicap tables, and a per-sport reason wherever a market is deliberately absent."),
 ("data/master_matches.json",
  "verification_status on the 71 'Verified' and 5 'Flagged' rows replaced with 'legacy draft - not source-checked', plus a superseded_by pointer. Not published by any builder."),
 ("README.md, docs/scope.md, COORDINATION.md",
  "Replaced the 76-fixture / 48-prediction claims with the published 137 rows / 5 predictions and recorded this session's checks."),
]


AUDIT_CHANGES += [
 ("data/predictions.json",
  "Eight predictions corrected against the official tables (Pro D2 ranks for Narbonne and Beziers, a 'second-worst defence' claim, a wrong "
  "round number, an away-scoring figure presented as a home-and-away average, a 'division-high' conceding claim, an unattributed Dupont "
  "quotation, and Dahlen's transfer timing). IHO-01 withdrawn during that pass and restored the same day on the club&rsquo;s own fixture page. Every prediction now lists a source for each "
  "factual claim."),
 ("data/official.json",
  "IHO-01 moved out of the confirmed-fixture set into a new 'downgraded' record that names the third-party page it had relied on and why "
  "that is not good enough. A 'reverified' block records this pass and its source list."),
 ("scripts/check_board.py",
  "New rule: a prediction may only exist for a HIGH-confidence row, so a downgraded row cannot keep a published prediction."),
]

def _audit_det(det):
    # older entries carry live counts as placeholders; fill them at render time so a count
    # can never go stale relative to the data the page is built from.
    return det.replace("{n_events}", str(n_events)).replace("{len(PREDS)}", str(len(PREDS)))


def _res_pill(res):
    cls = {"match": "high", "fixed": "med", "irregularity": "warn", "unverified": "low"}.get(res, "low")
    return f'<span class="pill {cls}">{e(res)}</span>'

audit_rows = "".join(
    f"<tr><td class='num'>{i+1}</td><td><strong>{chk}</strong><p>{_audit_det(det)}</p></td><td>{_res_pill(res)}</td>"
    f"<td><a href='{e(url)}' rel='noopener'>source</a></td></tr>"
    for i, (chk, det, res, url) in enumerate(AUDIT_CHECKS))

change_rows = "".join(f"<tr><td><code>{e(f)}</code></td><td>{e(d)}</td></tr>" for f, d in AUDIT_CHANGES)

official_sources = sorted({r["verification"]["official_url"] for r in EVENTS if r["verification"]["status"] == "verified"})
official_sources += sorted({s["url"] for p in PREDS.values() for s in p["sources"]})
official_sources = list(dict.fromkeys(official_sources))
source_rows = "".join(f"<li><a href='{e(u)}' rel='noopener'>{e(u)}</a></li>" for u in official_sources)

auditpage = head("Audit") + f"""
<section class="pagehead">
  <h1>Audit: what was checked, what failed, what changed</h1>
  <p class="lede">This page is the review log for the current build. Each line below names the claim, the official page it was compared with, the
  outcome and the link, so it can be re-checked by hand. Nothing on this page is a promise: where an official page could not be read, the outcome
  says <em>unverified</em> rather than <em>match</em>.</p>
</section>
<div class="cards">
  <div class="card"><span class="k">{len(AUDIT_CHECKS)}</span><span class="l">checks logged</span></div>
  <div class="card"><span class="k">{sum(1 for c in AUDIT_CHECKS if c[2]=='match')}</span><span class="l">matched the official source</span></div>
  <div class="card"><span class="k">{sum(1 for c in AUDIT_CHECKS if c[2]=='fixed')}</span><span class="l">defects fixed</span></div>
  <div class="card warn"><span class="k">{sum(1 for c in AUDIT_CHECKS if c[2] in ('irregularity','unverified'))}</span><span class="l">flagged, not fixed</span></div>
</div>

<h2>Line-by-line checks</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th class="num">#</th><th>What was compared, and what the source says</th><th>Outcome</th><th>Source</th></tr></thead>
<tbody>{audit_rows}</tbody></table></div>

<h2>Changes made in this build</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>File</th><th>Change</th></tr></thead><tbody>{change_rows}</tbody></table></div>

<h2>Sources used, for manual review</h2>
<p>Every official or primary page this build relied on. Open them in order; each one backs at least one row or one prediction.</p>
<ul class="sourcelist">{source_rows}</ul>

<h2>What this audit does not cover</h2>
<ul class="tight">
  <li><strong>{n_unverified} of {n_events} rows remain unverified, and {n_corroborated} rest on third-party corroboration only.</strong> No official page was retrieved for those fixtures in this session, so their
      competition, venue and start are left blank or published as OLBG&rsquo;s raw label. They are listed row by row on
      <a href="flagged.html">Flagged for Review</a>; absence of a flag would be a stronger claim than we can support.</li>
  <li><strong>The tip shares are a snapshot.</strong> OLBG recount constantly (see check 5). Re-reading a listing tomorrow will not reproduce these
      percentages exactly.</li>
  <li><strong>Pagination.</strong> OLBG hides further rows behind a &ldquo;Load More Tips&rdquo; control. The board is the first page of each sport,
      so it is a complete list of what OLBG rendered, not a complete list of everything OLBG holds.</li>
  <li><strong>Our prices are model output.</strong> Every number in the price columns is ours, produced by <code>scripts/model.py</code> and
      <code>scripts/build_gap_sports.py</code>. They are not market quotes and they are not predictions of fact.</li>
</ul>
""" + foot(0)
open(os.path.join(OUT, "audit.html"), "w").write(auditpage)

# ---------- flagged ----------
irregularities = [
 ("This build started from a repo that already carried three tracks", "Earlier sessions had produced a fixture board, an official-feed pipeline and an OLBG audit track. Nothing was taken on trust: the rows were re-read against OLBG, the high-confidence predictions were re-checked line by line against the official URC table and NHL standings, and the defects found are listed below and on the <a href=\"audit.html\">audit page</a>. Where a document disagreed with the data, the document was corrected.", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/COORDINATION.md"),
 ("OLBG start times run 7\u201310 minutes late", "On every fixture where we could compare, OLBG&rsquo;s displayed start time is later than the official one: NHL 19:37 vs 19:30 EDT (both 21 Oct games); NBA 19:10 vs 19:00, 19:40 vs 19:30, 20:10 vs 20:00 ET. Treat OLBG minute-values as approximate.", "https://www.nhl.com/schedule/2026-10-21"),
 ("OLBG does not state a time zone", "Times are shown as bare values (&ldquo;Today 19:10&rdquo;). They line up with US Eastern for the North American fixtures but with local/UK time for the URC fixtures, so the displayed zone is inconsistent. We publish the string exactly as shown and label the column &ldquo;Start (as listed)&rdquo;.", "https://www.olbg.com/betting-tips/Rugby_Union/9"),
 ("Competition is blank for most sports", "Tennis, cricket, volleyball, darts, snooker, handball, Gaelic football and rugby union listings do not show a competition (the URL group is <code>All_&lt;Sport&gt;/All_Events</code>). We left the column blank rather than infer a league from the team names.", "https://www.olbg.com/betting-tips/Tennis/3"),
 ("Sport IDs are mandatory and some are stale", "<code>/betting-tips/Basketball</code> and <code>/betting-tips/Cricket</code> return 404 without the numeric ID. <code>/Ice_Hockey/11</code> redirects to 13, <code>/Baseball/5</code> to 12, <code>/Handball/14</code> to 20. Any link built with a guessed ID lands on the wrong sport or a 404.", "https://www.olbg.com/betting-tips/Handball/20"),
 ("Listings are paginated", "Baseball, ice hockey, snooker, Gaelic football and handball pages end in a &ldquo;Load More Tips&rdquo; control, so the captured rows are the first page and are <strong>not</strong> a complete list of that sport&rsquo;s fixtures. One handball row (FC Barcelona v Montpellier) was cut off mid-record and was therefore dropped rather than reconstructed.", "https://www.olbg.com/betting-tips/Handball/20"),
 ("Rugby League has no dated match fixtures", "At capture time the Rugby League page listed only outright markets (State of Origin 2027, Super League 2027 Grand Final, NRL 2027 Grand Final). Those three rows are now published as outright markets with an originated price; there is still no dated match to place on the board.", "https://www.olbg.com/betting-tips/Rugby_League/10"),
 ("Golf, Motor Racing, Greyhounds and the Gaelic championship had no rows", "All four were in scope but absent from the previous board. They are now captured: 10 golf tournaments, 1 F1 race plus 2 drivers' championship markets, 6 greyhound races, 3 rugby league outrights and 1 All-Ireland championship row. Each carries an originated win price built from a disclosed field-size prior; none has a handicap or total, because a one-selection market has neither.", "https://www.olbg.com/betting-tips/Motor_Racing/14"),
 ("OLBG tip counts move between captures", "Genesis Championship read 5/18 at 05:20Z and 6/20 at 07:05Z; the USA Grand Prix read 10/31 (32%) and then 11/32 (34%). Percentages on this site are timestamped snapshots of a live count, not fixed values. Rows added in this pass use the 07:05Z reading and record it in <code>data/gap_sports.json</code>.", "https://www.olbg.com/betting-tips/Golf/5"),
 ("A legacy file in this repo claimed verification it does not have", "<code>data/master_matches.json</code> (76 rows, produced by <code>build_full_database.py</code>) marks 71 rows &lsquo;Verified&rsquo; and 48 &lsquo;High&rsquo; confidence, and its narratives quote precise figures (&lsquo;seven consecutive EuroLeague home fixtures by an average of 11.2 points&rsquo;). Its <code>official_source_url</code> values are sport homepages such as <code>euroleaguebasketball.net/eurocup/</code>, which cannot support a fixture-level or statistic-level claim. No builder publishes that file; it is now labelled a legacy draft, its status field no longer says &lsquo;Verified&rsquo;, and it is listed here so the claim is visible rather than buried.", "https://github.com/buffedlizard55-lab/OLBG3/blob/877def1c1c8e7456b64f5424f9ac3804126fdb15/data/master_matches.json"),
 ("Documentation quoted numbers the site never had", "README.md and COORDINATION.md stated &lsquo;76 fixtures&rsquo; and &lsquo;48 detailed human predictions&rsquo;, and the README listed <code>methodology.html</code>, <code>flagged-review.html</code> and <code>js/dashboard.js</code> as live pages after they had been removed. The published board carries {n_events} rows and {len(PREDS)} written pieces, of which {len([r for r in EVENTS if r['pick']['confidence']=='HIGH'])} are high-confidence predictions. Both documents now quote the published figures.", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/README.md"),
 ("A prediction named a venue the sources dispute", "The Leinster v Munster prediction originally said &lsquo;At the Aviva Stadium&rsquo;, while the official URC Round 3 record lists Leinster&rsquo;s 10 October home fixture at &lsquo;Laya Arena&rsquo;, a different ground. The sentence was removed rather than picked from two conflicting names. <strong>Resolved 2026-10-22:</strong> the Round 4 match centre explicitly lists Leinster v Munster on Sat 24 Oct at 13:00 at <em>Aviva Stadium</em>, so the venue is confirmed for the correct round.", "https://stats.unitedrugby.com/match-centre/2026-27/4"),
 ("Gaelic football rows show no market", "OLBG&rsquo;s Gaelic football listing displays no market name for its selections (the market column is empty on their own page) even though the selections are clearly handicap-style. We left market and competition blank.", "https://www.olbg.com/betting-tips/Gaelic_Football/25"),
 ("Team names differ between OLBG and the official source", "OLBG says &ldquo;Bulls&rdquo;, &ldquo;Stormers&rdquo;, &ldquo;BUF Sabres&rdquo;; the official sources say &ldquo;Vodacom Bulls&rdquo;, &ldquo;DHL Stormers&rdquo;, &ldquo;Buffalo Sabres&rdquo;. We map these with an explicit, published alias table in <code>scripts/model.py</code> &mdash; name normalisation only, no value is altered.", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
 ("Handicaps are now originated for 83 of the 114 fixtures; totals still only where an official scoring baseline exists", "Until this pass a handicap existed only where an official scoring table did (URC, Pro D2, Top 14, NHL, ICEHL, SHL): 22 rows. It is now originated for every priced two-sided fixture in a sport whose scoring unit can be stated &mdash; 83 rows &mdash; by a disclosed probability-to-margin transform with a per-sport margin scale (Tennis 4.5 games, Basketball 13 points, Handball 7 goals, Baseball 3 runs, Volleyball 1.6 sets, Snooker 1.4 frames), capped at 85% probability. Those lines are labelled <code>consensus-scaled</code> because the input is a public tip share, not official form. Cricket, darts and Gaelic football still carry no handicap, and only rugby union and ice hockey carry a total, because no official scoring baseline was captured for the rest: we left the cell empty instead of inventing a number.", "&mdash;"),
 ("Twelve rows were called &lsquo;verified&rsquo; on a third-party source", "The board&rsquo;s earlier &lsquo;verified&rsquo; label accepted ESPN/ESPNcricinfo, Sofascore, AS, TNT Sports, ORF, snooker.org, Eliteprospects and a German betting-preview site. A reputable aggregator is not the competition&rsquo;s own site, so those rows are now published as <strong>corroborated</strong>, with their link kept and their tier stated, and they are listed at the bottom of this page. Where an official source could be found it replaced the third-party one: the six snooker rows now cite the World Snooker Tour&rsquo;s own match centres, and two Cricket South Africa fixtures now cite cricket.co.za.", "https://www.wst.tv/matches/"),
 ("A snooker source was described as &lsquo;official&rsquo; when it is not", "The six Northern Ireland Open rows cited <code>snooker.org</code> and called it the &lsquo;official Upcoming Matches schedule&rsquo;. snooker.org is an independent site, not the World Snooker Tour. All six pairings and session times were found on <code>wst.tv/matches</code> (Round 2, Wed 21 Oct, matches 36/38/39/42/44/45) and now link to their own WST match centre pages.", "https://www.wst.tv/matches/"),
 ("Fourteen tennis fixtures, fifteen volleyball fixtures and eight handball fixtures had no official confirmation", "This pass closed part of that gap and recorded the rest precisely. Eight ATP fixtures are now confirmed on the tour&rsquo;s own draw pages for Almaty and Brussels. The four WTA fixtures could not be confirmed: wtatennis.com&rsquo;s draw pages render client-side and returned no draw content on retrieval, so those rows stay unverified rather than being taken from a third party. The Polish, German, Italian, Finnish and Dutch volleyball leagues&rsquo; official sites were fetched, but no machine-readable fixture list for 21&ndash;25 October could be retrieved from them, so all 15 volleyball rows stay unverified. The EHF Champions League domain (<code>ehfcl.eurohandball.com</code>) returned 404 for every path tried, so the eight unverified handball rows could not be checked this pass.", "https://www.atptour.com/en/scores/current/almaty/9410/draws"),
 ("Cricket South Africa&rsquo;s own list resolves two rows and contradicts a third", "cricket.co.za lists &lsquo;Northern Cape Heat v Garden Route Badgers, 21/10/26 13:00&rsquo; and &lsquo;North West Dragons v Wenbro Impalas, 21/10/26 18:00&rsquo;, which match CRK-02 and CRK-03 once OLBG&rsquo;s unlabelled clock is read as US Eastern (07:00 &rarr; 13:00 SAST, 12:00 &rarr; 18:00 SAST). That is now the second independent confirmation of the FL-002/FL-021 time-zone finding. The same page does <em>not</em> show &lsquo;Eastern Storm v Tuskers&rsquo; for 22 October (it lists North West v Tuskers and Boland v Border), so CRK-05 stays unverified and is not resolved by guessing which name OLBG meant.", "https://cricket.co.za/fixtures/"),
 ("ICEHL form data came from an independent database", "The Austrian league table used to price Pustertal, HCB, KAC, Graz and Milano came from Eliteprospects. The league&rsquo;s own site now supplies it: <code>ice.hockey</code> publishes the Tabelle (HCB 1st, 11 games, 44-28; Pustertal 7th, 10 games, 17 points; Vorarlberg last, 0 wins, 52 conceded), and those are the figures the model uses. Eliteprospects stays in the repo only as a standby and is no longer cited by any verified row.", "https://www.ice.hockey/"),
 ("Sixteen markets were counted twice on the previous build", "The 2026-10-21 verification pass listed the golf, motor-racing and rugby-league outrights twice: once in data/sports/*.json (away = &lsquo;outright market&rsquo;) and again in data/gap_sports.json. The same OLBG event ids appear in both files (101905, 101904, 913, 828, 2695857 and so on). That is how a 137-row board was reported as 153 rows with &lsquo;130 two-sided fixtures&rsquo; &mdash; a golf tournament is not a two-sided fixture. This build drops the duplicate copies when the board is aggregated and prices each market once, on the outright/race track: 114 fixtures + 23 outright/race = 137 rows. Nothing was deleted from the capture; the deduplication is in code and the ids are listed here for manual review.", "https://www.olbg.com/betting-tips/Golf/5"),
 ("A venue in the verification pass was wrong", "The re-verification pass recorded IHO-03 at &lsquo;E.ON Arena, Timra&rsquo; and repeated it in the prediction text. The Swedish Ice Hockey Association&rsquo;s schedule (stats.swehockey.se, overview 20961) lists 2026-10-22 19:00 Timra IK v Farjestad BK at <strong>SCA Arena</strong>. Both the row and the prediction now say SCA Arena; the venue was corrected because it was wrong, not merely unsourced.", "https://stats.swehockey.se/ScheduleAndResults/Overview/20961"),
 ("Our prices are model output, not market prices", "Every price on the site is computed by <code>scripts/model.py</code> from either official data or the OLBG tip share, with a 5% price haircut. They are not bookmaker prices and they are not verified facts. Where the only input is a public tip share, the row is graded LOW and cannot be graded higher.", "&mdash;"),
]


IRREGULARITY_EXTRA = [
 ("Live 2026-10-22 OLBG harvest, governing-body verification sweep &amp; 10-sport in-band expansion",
  "Re-harvested all 15 in-scope OLBG sport listings and multi-market event pages live on 2026-10-22 01:26–01:32 UTC (<code>data/raw/olbg-harvest-20261022.tsv</code>). Added 59 new live fixtures to the board (bringing total coverage to 196 rows: 173 two-sided fixtures + 23 outright/race markets; 162 verified on official/club domains, only 2 third-party corroborated, 32 unverified), promoted international cricket (<code>icc-cricket.com</code>, <code>ecb.co.uk</code>, <code>cricketireland.ie</code>), ATP/WTA Tour draws, full 14-club SHL standings (<code>stats.swehockey.se</code>), PDC European Championship Dortmund order of play (<code>pdc.tv</code>), EHF Champions League &amp; DAIKIN HBL tables, Czech CVF Extraliga, PlusLiga/TAURON Liga and Munster/Cork GAA county finals, and expanded live in-band (<code>-250..+10000</code>) HIGH predictions to 30 picks across 10 sports on <code>/</code> (and 26 across 10 sports on <code>/olbg/</code>).",
  "https://www.olbg.com/betting-tips"),
 ("Every published high-confidence pick was priced shorter than -250",
  "All 15 HIGH picks on the previous build sat between 1.07 and 1.46 decimal, which is -1429 to -217 US: not one of them was inside the requested -250 to +10000 band. The arithmetic is unavoidable under the old rule, which demanded a 65% model probability and therefore a maximum price of 0.95/0.65 = 1.46. The rule now demands 55% <em>and</em> an explicit band check, so 6 picks are HIGH and all 6 are inside the band. The 13 favourites that are now too short to qualify (BKB-11, IHO-01, IHO-02, IHO-03, IHO-05, RGU-01, RGU-04, RGU-05, RGU-06, RGU-07, RGU-10, RGU-11, RGU-13) are relabelled MEDIUM with their prices published, and IHO-06 is MEDIUM because its 21 Oct kick-off has passed. No price was changed to fit the band.",
  "https://github.com/buffedlizard55-lab/OLBG3/blob/main/scripts/model.py"),
 ("A stored MLB run total did not match the official standings",
  "The 21 October capture recorded Tampa Bay at 755 runs scored and 645 allowed. Re-reading mlb.com/brewers/standings on 22 October gives 736 scored and 650 allowed, a +86 differential that matches MLB.com's own DIFF column; the stored 755/645 implies +110 and was wrong. The value was corrected in data/official.json and the BSB-01 prediction now quotes 650 conceded (4.01 per game). The win-loss record (98-64) and the log5 model input were unaffected, so the price (1.67) and the grade did not move.",
  "https://www.mlb.com/brewers/standings"),
 ("A Pro D2 venue in the 21 October capture was wrong",
  "The stored confirmation for RGU-08 (Valence Romans v Colomiers) said &lsquo;Stade du Polygone&rsquo;. Re-reading the official LNR match sheet for J8, match 12070, on 22 October gives <em>Stade Georges Pompidou</em>, 23 Octobre 2026 at 19h30. The fixture, date and OLBG start label were all correct; only the ground was wrong. It is corrected in data/official.json and the prediction now names the correct venue. The three other Pro D2 match sheets (12063 Agen, 12065 Angouleme, 12067 Grenoble) confirmed the venues already published.",
  "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12070-valence-romans-colomiers"),
 ("A Pro D2 points-difference rank in the RGU-09 write-up was wrong",
  "The first draft said Grenoble's +37 differential &lsquo;ranks fifth&rsquo;. The official LNR table ranks it fourth behind Oyonnax (+159), Provence (+64) and Brive (+42). Corrected to fourth. The underlying figures (213 scored, 176 conceded, 22 points, third place) were unchanged, so the price and the grade did not move.",
  "https://prod2.lnr.fr/classement"),
 (f"{n_archived} of {n_events} rows carry a kick-off date before this {BUILT} build",
  f"The board is a verbatim capture of OLBG's listings taken at 01:26&ndash;01:32Z on 22 October 2026 (a clock OLBG labels &lsquo;Today&rsquo; for the 21st) and, before that, at 07:05Z on 21 October. At this {BUILT} rebuild the archive test answers for itself: <strong>{n_archived}</strong> rows are dated before today, so their kick-offs have passed. They are kept, tagged <em>archive</em> and excluded from high-confidence grading rather than silently re-dated, and <strong>{n_live}</strong> rows"
  + (f" run from {_live_first} to {_live_last}." if _live_first else " remain.")
  + " The full 15-sport re-capture was completed on 22 October (<code>data/raw/olbg-harvest-20261022.tsv</code>) and each newly added row carries its own governing-body confirmation in <code>data/verifications.json</code>; no archived value was altered. This count is recomputed on every build, so it cannot go stale the way a hand-written figure would.",
  "https://www.olbg.com/betting-tips"),
 ("Empirical proof of OLBG IP-timezone rendering across fetches",
  "Comparing fetches across US Eastern (EDT, UTC-4) and UK (BST, UTC+1) endpoints proved that OLBG dynamically shifts every bare timestamp into the requester&rsquo;s geolocation timezone without printing a zone label: MIL Bucks @ WAS Wizards renders as <code>Today 19:10</code> in EDT and <code>Tomorrow 00:10</code> in BST; RK Zagreb vs PSG renders as <code>12:45</code> in EDT and <code>17:45</code> in BST against the official <code>18:45 CEST</code> EHF throw-off.",
  "https://www.olbg.com/betting-tips"),
 ("OLBG tipster venue slip on World Series Game 1",
  "On OLBG&rsquo;s TB Rays @ MIL Brewers event page (<code>event_id=160789</code>), the featured Best Tipster comment backs Tampa Bay citing <em>&lsquo;Rays are 5-1 at Tropicana this October&rsquo;</em>, whereas MLB&rsquo;s official schedule confirms Milwaukee (103-59) hold home-field advantage at American Family Field for Game 1.",
  "https://www.mlb.com/brewers/standings"),
 ("Ten more rows promoted to governing-body verification &amp; 19 stale root scripts removed",
  "Upgraded five cricket fixtures (CRK-01, CRK-02, CRK-03, CRK-04, CRK-08) off third-party aggregators onto <code>icc-cricket.com</code>, <code>cricket.co.za</code>, <code>nzc.nz</code> and <code>cricket.com.au</code>; confirmed five golf events (GLF-01, GLF-02, GLF-04, GLF-05, GLF-10) on official DP World Tour, PGA Tour, LPGA and LET portals (bringing all 23 outright/race rows to 100% priced); added EuroLeague and MLB official standings tables; rewrote all 15 board predictions without robotic prefixes and with named 2026 players; and removed 19 unreferenced root draft scripts/duplicates.",
  "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview"),
 ("OLBG was an hour early on a Finnish volleyball fixture", "VLB-01 is listed by OLBG at 10:00 ET, but the Mestaruusliiga&rsquo;s own match notice gives Puijo Wolley v Oriveden Ponnistus at 18:00 EEST on 21 Oct, which is 11:00 ET. Every other row we could compare converted cleanly to ET, so this looks like a single-row slip rather than a different zone. The official time is what we publish, and the discrepancy is stated in the row&rsquo;s note.", "https://mestaruusliiga.fi/uutiset/keskiviikon-ottelussa-voiitoputkessa-oleva-puijo-kohtaa-orpon/"),
 ("OLBG had a county final a week late", "GAF-04 (Rathgormack v The Nire) is listed by OLBG on 1 Nov at 10:30. Waterford GAA&rsquo;s fixture list and the Munster GAA calendar both put the Waterford senior football final on Sunday 25 Oct at 14:30 in Fraher Field. The official date is published and the row says OLBG is a week late.", "https://munster.gaa.ie/fixtures/events-calendar/"),
 ("An earlier pass recorded the wrong venue for a Basketball Champions League game", "BKB-14 was recorded at &lsquo;OAKA, Athens&rsquo;. The competition&rsquo;s own game page (game 136250) lists AEK BC v Windrose Giants Antwerp at SUNEL Arena, Ano Liosia, Athens, on 21 Oct, and 18:00 CEST is 12:00 ET as on OLBG. The venue has been corrected rather than left to stand because it was wrong, not merely unsourced.", "https://www.championsleague.basketball/en/games/136250-AEK-WGA"),
 ("Fifteen rows were moved off aggregators and broadcasters onto the competition organiser", "Earlier passes verified some rows from Sofascore, AS.com, TNT Sports, tipsterio.de, ORF, Eliteprospects and snooker.org. Fourteen of those now cite the organiser instead: the WST match centre for the six Northern Ireland Open rows, the EHF calendar for HBL-05, HC Pustertal and the Austrian federation&rsquo;s game centre for IHO-01 and IHO-04, and the Swedish Ice Hockey Association&rsquo;s schedule for IHO-03. One row (BKB-03, KBL) still cites Sofascore because the league publishes no machine-readable fixture feed; it is named as outstanding debt rather than quietly counted as official.", "https://wst.tv/matches/"),
 ("CRK-05 stays unverified on purpose", "Eastern Storm v Tuskers could not be tied to a governing-body fixture list in this pass, and the secondary sources disagree on both date and start by hours. Per the &lsquo;leave blank, don&rsquo;t infer&rsquo; rule the row keeps its blank official fields and sits on this page instead of being guessed into the verified column.", "https://www.olbg.com/betting-tips/Cricket/4"),
 ("A published prediction quoted figures that were wrong",
  "Four Pro D2 predictions contained errors that the official LNR pages contradict: Narbonne was called 14th (it is 15th), Beziers 15th "
  "(it is 14th), Beziers' 240 goals against was called 'second-worst' (Aurillac's 254 is worse), and a round-6 win at Soyaux-Angouleme "
  "was dated to round 7. All four are corrected on the predictions page; the audit page carries the before-and-after.",
  "https://prod2.lnr.fr/classement"),
 ("A row was 'verified' against a betting-preview site",
  "IHO-01 was marked verified with tipsterio.de as its source. That page is a preview, not an official competition or club page, so the row "
  "is now unverified and its prediction has been withdrawn. This is the only row in the set whose verification depended on a non-official "
  "domain; every other verified row cites a league, club or official stats page.",
  "https://www.ice.hockey/saison/spielplan"),
 ("The captured OLBG snapshot no longer reproduces",
  "Re-reading the baseball listing today gives '24 Oct 01:00' for TB Rays @ MIL Brewers with a featured Game Totals tip, while the captured "
  "row records '23 Oct 20:00' and a Money Line tip at 3/6 (50%). Tip counts were always known to move; a five-hour shift in the clock label "
  "and a change of featured market were not. The captured labels are published unchanged as a snapshot, and no start time is derived from them.",
  "https://www.olbg.com/betting-tips/Baseball/12"),
 ("Nine handball fixtures were confirmed on their own league's site, and the official clock settles the time-zone question",
  "Nine of the twelve handball rows that had been published as unverified are now confirmed on the organiser's own page: KIF Kolding v Fredericia on DanskHåndbold's official schedule (<em>Torsdag 22. okt. kl. 20:00, Betoro Herreligaen</em>), Sønderjyske v Nordsjælland on the club's own fixture list (<em>22. Oct kl. 19:30</em>), Önnereds v Ystads IF and Skånela v Karlskrona on the Handbollsligan fixture list (<em>Tors 22 OKT 19:00</em>), Granollers v Cuenca on ASOBAL's calendar (<em>22/10/2026 20:00</em>), and Aix v Toulouse, Limoges v Dunkerque and Sélestat v Caen on the LNH's Daikin StarLigue J08 calendar (<em>ven. 23 oct. 20h00 / 20h30</em>). In every case OLBG's unlabelled clock converts to the official throw-off only when read as US Eastern (UTC&minus;4): 13:30&rarr;19:30, 14:00&rarr;20:00, 14:30&rarr;20:30 CEST. Three rows stay unverified because the organiser's page did not publish the fixture (Skive fH v Aalborg, Estonia W v Kosovo W) or the listing could not be read.",
  "https://handbollsligan.se/herr/spelschema/"),
 ("One official Spanish calendar contradicts OLBG's date (FL-044)",
  "ASOBAL's official 2026/27 calendar places IRUDEK Bidasoa Irun v BM. Caserío Ciudad Real in <em>Jornada 07, dated 24/10/2026</em>. OLBG lists the same fixture on <strong>23 Oct at 13:00</strong>. The pairing and the competition are confirmed, so the row is published as verified with the official round date in its verification block, but the date OLBG shows is a day apart from the official one and is <em>not</em> confirmed. The neighbouring Jornada 07 fixture (Villa de Aranda v Puerto Sagunto, 24 Oct) agrees with OLBG, so this looks like a single-fixture slip rather than a different round.",
  "https://asobal.es/documentos/noticias/8660-CalendarioOFICIALLigaNEXUSENERGIAASOBAL2627.pdf"),
 ("OLBG's spelling of the Cuenca club is not the league's",
  "OLBG lists &lsquo;Ciudad Encantada&rsquo; for the Granollers fixture; ASOBAL's calendar and team list publish the same club as <strong>REBI Balonmano Cuenca</strong> (code CQN). The row is verified on the league's pairing; the club name is published as OLBG printed it, and the league's name is quoted in the verification note rather than silently substituted.",
  "https://asobal.es/liga/calendario/"),
]
IRREGULARITY_EXTRA.append((
    "Freshness clock repaired; source freshness remains a separate limitation",
    "The board previously compared dates against a frozen 22 October 2026 build date. It now uses the actual UTC build date "
    "(or an explicit OLBG_AS_OF archive override). This prevents past dates retaining a live label on future builds. "
    "It does not refresh OLBG captures, verify same-day kick-offs, or independently validate previously stored source claims. "
    "Structural validation of URLs and arithmetic is not source-content verification. The separate /olbg/ track retains its own confidence logic.",
    "https://github.com/buffedlizard55-lab/OLBG3/blob/main/scripts/board_dates.py"))
IRREGULARITY_EXTRA.append((
    "An F1 race was priced like a two-way coin flip instead of a 22-driver outright (FL-047, fixed 2026-10-22)",
    "MTR-913 (USA Grand Prix 'Win Race') was mapped to the match-winner family; with no home/away side it hit the 0.52 fallback and was "
    "published at 1.83 / -120, contradicting its +235 / 3.35 prediction and the root outright model. Reclassifying the 'Win Race' label as an "
    "outright restores the disclosed 22-car field prior (p=0.284) and a 3.35 / +235 line that matches the prose exactly. No probability input, "
    "grade or other row changed. That session's sampled cross-check of scores, standings, dates and injuries found nothing contradicted, but it "
    "did not test every numeric claim in the prose; the later line-by-line read that produced FL-048 did find seven stale or wrong figures.",
    "https://www.formula1.com/en/racing/2026/united-states"))
IRREGULARITY_EXTRA.append((
    "Seven HIGH write-ups carried stale or wrong figures (FL-048, fixed 2026-10-22)",
    "A line-by-line re-read of all 33 published HIGH pieces against the official pages they cite found stale or wrong figures in seven: "
    "HBL-15 published Szeged 124 / GOG 132 goals conceded when the EHF Group D table says 139:136 and 145:139 (and GOG won the reverse fixture 36:34, which the piece omitted); "
    "DRT-11 called Krzysztof Ratajski the 19th seed when the PDC draw lists him third; "
    "MTR-01's headline called Max Verstappen a three-time Austin winner when Formula 1 lists four COTA wins (2021, 2022, 2023, 2025); "
    "and four tennis figures were stale or wrong against the ATP list of 19 October 2026 - Bublik No. 22 (actually 19), Dzumhur No. 103 (actually 83), "
    "Cobolli 1,650 ranking points (actually 3,640) and a '300-point' Vacherot-Van Assche gap (actually 415 points, 1,480 v 1,065). "
    "Every value was replaced with the official one and the dated ATP page was added to the source list. A BSB-01 clause saying Tampa Bay had not named a "
    "Game 1 starter was removed because MLB.com's probable-pitchers page says TBD while multiple reports name Drew Rasmussen. "
    "No price, probability or grade changed, and every corrected pick remains inside the -250..+10000 band.",
    "https://ehfcl.eurohandball.com/men/2026-27/standings/"))
IRREGULARITY_EXTRA.append((
    "Four more HIGH write-ups corrected: a wrong match day, an unsourced surface brand and two comparisons the sources do not support (FL-049)",
    "TEN-24 dated Alexandra Eala's win over Diane Parry to Tuesday when the WTA draw and report put it on Monday 19 October, and named an acrylic surface brand the WTA does not publish; "
    "TEN-28 described Gojo's two qualifying wins as 'three-hour battles' although the ATP scorelines do not support a duration; GLF-02 ranked Seamus Power 'ahead of' Ben James in OLBG tips when today's capture "
    "publishes Power's 5/22 but not James's count (and James is the market favourite); and BKB-21's headline called Maccabi's home record in the fixture 'perfect' when the EuroLeague says only that the home team "
    "won each of the last five meetings, the most recent of which was in Madrid. Each sentence now states only what its source states. No price, grade or market line changed.",
    "https://www.wtatennis.com/tournaments/2092/ningbo/2026/draws"))
IRREGULARITY_EXTRA.append((
    "The OLBG clock is US Eastern, and three same-day HIGH picks had already kicked off at the verification clock (FL-050, fixed)",
    "OLBG prints a bare clock and no zone, so the board could only date a fixture, not time it. Reading the captured labels as "
    "<strong>US Eastern (UTC&minus;4)</strong> reproduces the organiser&rsquo;s own start time in every case we could check &mdash; "
    "04:00 &rarr; 13:00 Almaty, 08:00 &rarr; 14:00 Lyon, 09:00 &rarr; the second Centre Court match in Brussels from 13:30, "
    "13:00 &rarr; 19:00 CEST handball. At 07:20 UTC that puts TEN-20 (05:00 UTC), TEN-21 (05:30 UTC) and CRK-04 (07:00 UTC, ICC live "
    "score already showing New Zealand batting) past their start while still published as live HIGH picks. Every row now carries a "
    "derived UTC kick-off and a <em>started</em> marker instead of implying a kick-off is still ahead; the grade is not rewritten by "
    "the wall clock, because the hourly rebuild re-derives the board from committed inputs and a clock-dependent grade would be "
    "irreproducible. The date-level archive gate is unchanged.",
    "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"))
irregularities = IRREGULARITY_EXTRA + irregularities

def _src(u):
    if u == "&mdash;":
        return '<span class="dim">&mdash;</span>'
    return '<a href="' + e(u) + '" rel="noopener">source</a>'

irr_html = "".join(
    "<tr><td class='num'>" + str(i + 1) + "</td><td><strong>" + e(t) + "</strong><p>"
    + d.replace("{n_events}", str(n_events)).replace("{len(PREDS)}", str(len(PREDS))) + "</p></td><td>" + _src(u) + "</td></tr>"
    for i, (t, d, u) in enumerate(irregularities))

def _unver_row(r):
    comp = e(r["competition"]) if r["competition"] else '<span class="dim">blank</span>'
    return ("<tr><td>" + e(r["ref"]) + "</td><td>" + e(r["sport"]) + "</td><td>" + match_label(r) + "</td><td>" + comp +
            "</td><td>" + e(r["start"]) + "</td><td><a href='" + e(r["olbg_event_url"]) + "' rel='noopener'>OLBG event page</a></td>"
            "<td><span class='pill low'>unverified</span></td></tr>")

unver_rows = "".join(_unver_row(r) for r in EVENTS if r["verification"]["status"] == "unverified")


def _corr_row(r):
    v = r["verification"]
    comp = e(r["competition"]) if r["competition"] else '<span class="dim">blank</span>'
    return ("<tr><td>" + e(r["ref"]) + "</td><td>" + e(r["sport"]) + "</td><td>" + match_label(r) + "</td><td>" + comp +
            "</td><td>" + e(v.get("source_tier", "third-party")) + "</td><td><a href='" + e(v["official_url"]) +
            "' rel='noopener'>" + (e(v["official_label"]) or "third-party source") + "</a></td>"
            "<td><span class='pill med'>corroborated</span></td></tr>")


corr_rows = "".join(_corr_row(r) for r in EVENTS if r["verification"]["status"] == "corroborated")

REGISTER = json.load(open(os.path.join(ROOT, "data/flagged.json")))["items"]


def _reg_row(it):
    srcs = "".join(f'<li><a href="{e(x["url"])}" rel="noopener">{e(x.get("label") or x["url"])}</a></li>'
                   for x in it.get("sources", []))
    rows = ", ".join(it.get("affected_rows") or []) or "&mdash;"
    return (f'<tr id="{e(it["id"])}"><td><strong>{e(it["id"])}</strong></td><td>{e(str(it.get("severity","")))}</td>'
            f'<td><strong>{e(it.get("title",""))}</strong><br><span class="small">{e(it.get("detail",""))}</span></td>'
            f'<td class="small">{e(rows)}</td><td class="small"><ul class="srclist">{srcs}</ul></td></tr>')


register_rows = "".join(_reg_row(it) for it in reversed(REGISTER))
current_findings = "".join(_reg_row(it) for it in reversed(REGISTER) if int(it["id"].split("-")[1]) >= 63)

flagpage = head("Flagged for Review") + f"""
<section class="pagehead flagged">
  <h1>Flagged for Review</h1>
  <p class="lede">Everything here is published deliberately, with its source, so it can be checked and challenged. None of it blocks the
  release; all of it deserves a human eye. {len(irregularities)} findings, {n_corroborated} rows that rest on third-party corroboration
  only, and {n_unverified} unverified rows.</p>
</section>

<h2>Current audit priorities</h2>
<p>New findings from this pass are listed below. A source observation is not a verified betting edge. Start with <a href="source-health.html">Source health</a> for row-level release decisions and the actual quoted official observations.</p>
<div class="tablewrap"><table class="board"><thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Affected rows</th><th>Sources</th></tr></thead><tbody>{current_findings.replace('id="FL-', 'id="current-FL-')}</tbody></table></div>
<details class="research-details"><summary>Historical findings from earlier passes (may have been superseded)</summary>
<p class="dim">These dated observations are retained as an audit trail, not statements of current verification. In particular, earlier timezone assumptions and source-count claims do not govern the current release gate.</p>
<h2>Historical findings &amp; irregularities</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th class="num">#</th><th>Finding and what we did about it</th><th>Evidence</th></tr></thead>
<tbody>{irr_html}</tbody></table></div>

</details><h2>Rows corroborated by a third party only ({n_corroborated})</h2>
<p>For these rows a reputable third party (ESPN, ESPNcricinfo, Sofascore, AS, TNT Sports, ORF, snooker.org, Eliteprospects,
tipsterio.de) lists the fixture, but the competition&rsquo;s own site did not, or was not readable, in this pass. They are kept on the
board because the link is real, and labelled <em>corroborated</em> rather than <em>verified</em>. Treat them as unconfirmed: the
verification point is withheld, so none of them can be graded high confidence.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Ref</th><th>Sport</th><th>Match</th><th>Competition</th><th>Tier</th><th>Third-party source</th><th>Status</th></tr></thead>
<tbody>{corr_rows}</tbody></table></div>

<h2>Rows we could not verify ({n_unverified})</h2>
<p>For each row below we could not retrieve an official competition source in this session, so the competition, handicap and total
fields are left blank. The fixture as OLBG published it is shown, with the OLBG event link, so you can check it yourself and tell us
to promote or drop it.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Ref</th><th>Sport</th><th>Match</th><th>Competition</th><th>Start (as listed)</th><th>OLBG source</th><th>Status</th></tr></thead>
<tbody>{unver_rows}</tbody></table></div>

<h2>The itemised register ({len(REGISTER)})</h2>
<p>Every numbered finding from the audit register, with its source links. The same register drives the
<a href="olbg/flagged.html">/olbg/ lines-track Flagged page</a>; it is reproduced here so the main site has one
complete list. Nothing in it blocks the release.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Affected rows</th><th>Sources</th></tr></thead>
<tbody>{register_rows}</tbody></table></div>
""" + foot(0)
open(os.path.join(OUT, "flagged.html"), "w").write(flagpage)

# ---------- method ----------
assum = "".join(f"<li>{e(a)}</li>" for a in ASSUMPTIONS)
sport_links = "".join(
    f"<li><a href='sports/{SPORT_META[s]['slug']}.html'>{e(s)}</a> &mdash; {len(by_sport.get(s,[]))} rows"
    f" ({len([r for r in by_sport.get(s,[]) if r.get('market_type','fixture') == 'fixture'])} fixtures,"
    f" {len([r for r in by_sport.get(s,[]) if r.get('market_type','fixture') != 'fixture'])} outright/race)</li>"
    for s in SPORT_ORDER)
excl = "".join(f"<li>{e(x)}</li>" for x in EXCLUDED)
nc = "".join(f"<li>{e(x)}</li>" for x in NOT_CAPTURED)
fc = "".join(f"<li>{e(x)}</li>" for x in FORMERLY_NOT_CAPTURED)
gap_prior_rows = "".join(
    f"<tr><td>{e(k)}</td><td class='num'>{v}</td><td class='num'>{GAP_MODEL['strength_k_by_basis'].get(k, '')}</td><td>{e(GAP_MODEL['field_sizes'].get(k, ''))}</td></tr>"
    for k, v in sorted(GAP_MODEL["strength_k_by_basis"].items()))
n_gap = len(GAP_ROWS)
n_gap_priced = sum(1 for r in GAP_ROWS if r["model"]["prices"])
GAP_FIELDS = json.load(open(os.path.join(ROOT, "data/raw/gap_sports_capture_20261021.json")))["field_size_assumptions"]
gap_basis_notes = "".join(
    f"<li><strong>{e(k)}</strong> &mdash; {e(v['basis'])}</li>" for k, v in sorted(GAP_FIELDS.items()))

method = head("Method & Scope") + f"""
<section class="pagehead"><p class="eyebrow">REPRODUCIBLE ESTIMATES · TRACEABLE FACTS</p><h1>Method &amp; scope</h1>
<p class="lede">Facts, captured opinions and model estimates are different things. This site labels them separately and never treats a source hostname as factual verification.</p></section>
<h2>Coverage and exclusions</h2><p>The board contains {n_fixtures} captured two-sided fixtures and {n_outrights} outright/race rows.
Neither that count nor the public HTML collector proves a full list of updated OLBG matches. Pagination and dynamic content remain a disclosed gap.</p>
<div class="grid2"><div class="panel"><h3>Excluded sports</h3><ul>{excl}</ul><p>Gaelic football is retained only as the historically flagged scope ambiguity FL-001; the official-feed track excludes it conservatively.</p></div>
<div class="panel"><h3>Categories</h3><ul>{sport_links}</ul></div></div>
<h2>1. Discovery is not verification</h2><p>Public OLBG listing and event URLs are preserved. The hourly collector respects robots.txt and makes at most one public listing request per sport, two at a time.
It reads actual linked text, never guesses a match from its URL, does not call disallowed private APIs and does not bypass challenges or invent pagination URLs.
New event references remain unverified; their UTC time, competition and betting fields stay blank on <a href="discovery.html">Current discovery</a>.</p>
<h2>2. Official sporting facts</h2><p>Recorded fixture confirmations and scoring/ranking inputs live in <code>data/official.json</code> and <code>data/verifications.json</code>, with official source links.
Some are historical observations, not independently refreshed by this pass. Only retrieved official evidence may fill a factual field; third parties stay corroborated.
The NBA/NHL/MLB connectors refresh their own schedules hourly, keep payload SHA-256 hashes, and show per-source successes and failures. Cached rows are withheld from the current feed.</p>
<h2>3. Our originated prices</h2><p>The root model in <code>scripts/model.py</code> uses disclosed sport-specific heuristics: scoring-rate/normal-margin models for rugby, basketball and handball, a goals/logistic model for hockey,
Log5 plus an assumed home adjustment for baseball, and assumed mappings of ranking points, ratings or seeds for some individual sports. Without the relevant inputs it may use a public tip share or leave a market empty.</p>
<p>The separate <code>/olbg/</code> audit model uses shrunk tip shares and home-logit assumptions, plus explicitly marked <strong>editorial prior overrides</strong> in <code>tools/originate.py</code>.
Those hard-coded probabilities and total preferences are assumptions, not official statistics, trained coefficients or independently validated edges. Different disclosed models can disagree.</p>
<p>Both use <code>decimal = 0.95 / p</code>, a <strong>5% price haircut</strong>. In an exhaustive two-way book, the reciprocal probabilities therefore sum to approximately 1.05263 before rounding: about 5.26% overround, not exactly 5%.
Fair decimal odds would be <code>1/p</code>. Single-selection field priors do not establish an exhaustive market book.</p>
<h2>4. Markets investigated</h2><div class="tablewrap"><table class="board"><thead><tr><th>Market</th><th>What is available</th><th>Limit / evidence</th></tr></thead><tbody>
<tr><td>Match winner / money line</td><td>Our modeled selection and prices where inputs exist</td><td>Official schedules establish the fixture, not its probability. <a href="https://www.mlb.com/schedule/2026-10-23">Example official fixture</a></td></tr>
<tr><td>Handicap / spread / run line / puck line</td><td>Projected or probability-mapped line where shown</td><td>Dispersion and standard prices are modeling assumptions; not verified settlement rules. <a href="https://github.com/buffedlizard55-lab/OLBG3/blob/main/scripts/model.py">Formula</a></td></tr>
<tr><td>Match totals</td><td>Root scoring/ranking heuristic or audit-track editorial baseline</td><td>Not a calibrated over/under distribution. Unsupported sport/format fields stay blank. <a href="https://github.com/buffedlizard55-lab/OLBG3/blob/main/tools/originate.py">Audit priors</a></td></tr>
<tr><td>Outright / race winner</td><td>Tip share shrunk toward an assumed field-size prior</td><td>Field size and prior strength are assumptions unless separately sourced. No invented opposing side, handicap or total. <a href="https://www.formula1.com/en/racing/2026/united-states">Example race source</a></td></tr>
<tr><td>Set scores / periods / player props / other markets</td><td>OLBG labels retained where captured; no invented full market inventory</td><td>Automated comprehensive event-market discovery and settlement validation remain unverified. <a href="https://www.olbg.com/betting-tips">OLBG public index</a></td></tr>
</tbody></table></div>
<h2>5. Confidence and publication</h2><p>LOW/MEDIUM/HIGH are uncalibrated model evidence grades, not observed win rates. The root rubric scores fixture evidence, stored form inputs and its model preference.
HIGH also requires a unique sourced prediction of at least 30 words, an originated price from 1.40 to 101.00 (−250 to +10000 US), and a current official-start release.</p>
<p>No observed bookmaker price was verified, so <strong>we cannot certify that a market price is in the requested range or that a bet has positive expected value</strong>.
Do not confuse filtering out very short model favorites with discovering value.</p>
<p>A release requires a dated observation with an explicitly timezone-qualified exact official clock. No timezone is assigned to bare OLBG labels.
“Followed by”, “not before”, session ordering and date-only draws cannot establish an exact start. A HIGH release expires at its scheduled start or 24 hours after the source check, whichever comes first.
Passed starts are not final-result claims. A conflict blanks affected model lines and holds the pick for review. <a href="source-health.html">Inspect all release decisions →</a></p>
<h2>6. Reproduce and validate</h2><pre class="code">python scripts/update.py
python scripts/discovery.py
python scripts/build.py
python scripts/build_gap_sports.py
python scripts/model.py
python scripts/build_site.py
python tools/build_dataset.py
python tools/originate.py
python tools/build_site.py
python scripts/build_site.py --snapshot
python -m unittest discover -s tests -v
python scripts/check_board.py
python tools/check_site.py
python scripts/check.py
python scripts/check_links.py</pre>
<p>Use explicit <code>OLBG_NOW_UTC=2026-10-22T08:33Z</code> and <code>OLBG_AS_OF=2026-10-22</code> to reproduce a historical publication clock.
This never renews capture/source timestamps. Builds and link checks are structural validation, not proof that every historical claim is supported.</p>
<p>Outstanding issues and historical corrections are published on <a href="flagged.html">Flagged for Review</a>. No guaranteed outcomes. 18+.</p>
""" + foot(0)
open(os.path.join(OUT, "method.html"), "w").write(method)

# ---------- nojekyll ----------
for asset in ("style.css", "app.js", "release.js"):
    shutil.copyfile(os.path.join(ROOT, "assets", asset), os.path.join(OUT, "assets", asset))
open(os.path.join(OUT, ".nojekyll"), "w").write("")

# The third session's OLBG audit section (tools/build_site.py) is committed at ./olbg.
# It is published at /olbg/ so both Pages publishers serve it and the shared nav link resolves.
if os.path.isdir(os.path.join(ROOT, "olbg")):
    shutil.rmtree(os.path.join(OUT, "olbg"), ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "olbg"), os.path.join(OUT, "olbg"))

for extra_dir in ("css", "js"):
    src_dir = os.path.join(ROOT, extra_dir)
    if os.path.isdir(src_dir):
        dst_dir = os.path.join(OUT, extra_dir)
        shutil.rmtree(dst_dir, ignore_errors=True)
        shutil.copytree(src_dir, dst_dir)

for extra_file in ("flagged-review.html", "methodology.html"):
    src_file = os.path.join(ROOT, extra_file)
    if os.path.isfile(src_file):
        shutil.copyfile(src_file, os.path.join(OUT, extra_file))

# --snapshot mirrors the built site into the repository root.
# Reason: this repository's Pages site is configured for LEGACY branch publishing
# (source: main, path: /) and the API that would switch it to Actions returns 403 for
# every token we have. GitHub also runs our Actions artifact deployment. Whichever
# publisher runs last wins, so both targets must contain the same bytes or the site
# flaps. Root is committed; site/ is generated in CI and always the fresher of the two.
if "--snapshot" in sys.argv:
    keep = {"data", "scripts", "docs", "tests", "assets", ".git", ".github", "site", "__pycache__", "css", "js"}
    for name in os.listdir(OUT):
        if name in keep:
            continue
        src = os.path.join(OUT, name); dst = os.path.join(ROOT, name)
        if os.path.isdir(src):
            shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
        else:
            shutil.copyfile(src, dst)
    print("root snapshot refreshed from site/")
print("board pages:", len(glob.glob(os.path.join(OUT, "*.html"))) + len(glob.glob(os.path.join(OUT, "sports/*.html"))))
print("verified", n_verified, "unverified", n_unverified, "priced", n_price, "hcap", n_hcap, "totals", n_total)
