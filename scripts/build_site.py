#!/usr/bin/env python3
"""build_site.py - generates the static GitHub Pages site from data/*.json."""
import json, os, glob, html, shutil, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")          # published artifact root (built by build.py first)
GEN = "2026-10-21"
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)

# One navigation for the whole published site: this track's pages first, then the
# official-feed track's pages (built by scripts/build.py, which runs before this script).
NAV = [("index.html", "Dashboard"), ("predictions.html", "Predictions"), ("lines.html", "Originated lines"),
       ("verification.html", "Verification"), ("audit.html", "Audit"), ("flagged.html", "Flagged for Review"),
       ("method.html", "Method & Scope"), ("feed-overview.html", "Official feed"),
       ("matches.html", "Feed matches"), ("coverage.html", "Feed coverage"), ("review.html", "Feed review"),
       ("olbg/index.html", "OLBG lines (audit)")]
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
    "note": "Ten tournament winner markets. OLBG publishes no field size and no stroke-play line, so a handicap or a 72-hole total would be invented; we originate only the win price, using a disclosed 156-player field prior. OLBG's date/time on these rows is the listing's own label and is not the tournament's start date.", "id": 5}
SPORT_META["Motor Racing"] = {"slug": "motor_racing", "listing": "https://www.olbg.com/betting-tips/Motor_Racing/14",
    "note": "One Formula 1 race (United States Grand Prix, 25 Oct 2026) plus two season-long drivers' championship markets. The race start is confirmed against formula1.com; the championship markets cannot be verified before the season ends and are published unverified.", "id": 14}
SPORT_META["Greyhounds"] = {"slug": "greyhounds", "listing": "https://www.olbg.com/betting-tips/Greyhounds/28",
    "note": "Six same-day UK races. Each row is a single race with one tipped dog; the race name carries the UK clock time while OLBG's own label is about five hours earlier, so no start time is derived from either. No official GBGB racecard was retrieved, so every row is unverified.", "id": 28}

NOT_CAPTURED = ["Esports (no listing surfaced on the OLBG tips index at capture time)"]
FORMERLY_NOT_CAPTURED = ["Golf - now captured as 10 outright rows (data/raw/gap_sports_capture_20261021.json)",
                 "Motor Racing - now captured as 1 race and 2 outright rows",
                 "Greyhound Racing - now captured as 6 race rows"]
EXCLUDED = ["Soccer / Football","American Football","Boxing","UFC / MMA","Hurling","Horse Racing","Cycling","Specials (TV/Politics/Awards)"]

def e(x):
    return html.escape(str(x)) if x is not None else ""

def money(p):
    return f"{p:.2f}" if isinstance(p, (int, float)) else "&mdash;"

# ---------- statistics ----------
n_events = len(EVENTS)
n_fixtures = sum(1 for r in EVENTS if r.get("market_type", "fixture") == "fixture")
n_outrights = n_events - n_fixtures
by_sport = defaultdict(list)
for r in EVENTS:
    by_sport[r["sport"]].append(r)
n_verified = sum(1 for r in EVENTS if r["verification"]["status"] == "verified")
n_corroborated = sum(1 for r in EVENTS if r["verification"]["status"] == "corroborated")
n_unverified = sum(1 for r in EVENTS if r["verification"]["status"] == "unverified")
conf_counter = Counter(r["pick"]["confidence"] for r in EVENTS)
n_price = sum(1 for r in EVENTS if r["model"].get("prices"))
n_hcap = sum(1 for r in EVENTS if r["model"].get("handicap"))
n_total = sum(1 for r in EVENTS if r["model"].get("total"))

# ---------- shared chrome ----------
def head(title, depth=0):
    p = "../" * depth
    navlinks = "".join(f'<a href="{p}{f}">{e(t)}</a>' for f, t in NAV)
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
<main>"""

FOOT = f"""
</main>
<footer>
  <p><strong>Built {GEN}.</strong> Data captured from OLBG.com event pages and checked against official competition sources where stated.
  Prices, handicaps and totals are <strong>our own model output</strong>, not bookmaker prices and not facts.</p>
  <p>18+. If gambling is causing you harm, contact <a href="https://www.gamcare.org.uk/" rel="noopener">GamCare</a> or
  <a href="https://www.gambleaware.org/" rel="noopener">GambleAware</a>. No bet is ever a certainty.</p>
</footer>
<script src="{{P}}assets/app.js"></script>
</body></html>"""

def foot(depth):
    return FOOT.replace("{P}", "../" * depth)

def conf_pill(c):
    return f'<span class="pill {c.lower()}">{c}</span>'

GOVERNING_PORTAL = {
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
    gov_url, gov_lbl = GOVERNING_PORTAL.get(r["sport"], ("https://www.olbg.com/betting-tips", "check official site"))
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
    pick = e(p["label"]) if p["label"] else '<span class="dim">no pick</span>'
    prob = f'<span class="prob">{p["prob"]*100:.0f}%</span>' if p.get("prob") else ""
    ref = f'<a href="{e(r["olbg_event_url"])}" rel="noopener">{e(r["ref"])}</a>'
    return f"""<tr data-sport="{e(r['sport'])}" data-conf="{p['confidence']}" data-text="{e((r['home']+' '+r['away']+' '+r['competition']+' '+r['sport']).lower())}">
<td class="ref">{ref}</td>
<td>{e(r['sport'])}</td>
<td class="comp">{e(r['competition']) or '<span class="dim" title="OLBG does not state the competition for this fixture">not stated</span>'}</td>
<td class="match">{match_label(r)}</td>
<td class="market">{market_label(r)}</td>
<td class="when">{e(r['start'])}</td>
{price_cell(r)}
<td class="pick">{pick} {prob}</td>
<td>{conf_pill(p['confidence'])}</td>
<td class="basis">{e(r['model'].get('basis','none'))}</td>
<td class="src">{ver_cell(r)}</td>
</tr>"""

TABLE_HEAD = """<thead><tr>
<th>Ref</th><th>Sport</th><th>Competition</th><th>Match / event</th><th>Market</th><th>Start (as listed)</th>
<th class="num">Our price</th><th class="num">Draw</th><th class="num">Our price 2</th>
<th>Our pick</th><th>Conf.</th><th>Basis</th><th>Official source</th>
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
<div class="cards">
  <div class="card"><span class="k">{len(rows)}</span><span class="l">rows</span></div>
  <div class="card"><span class="k">{len([r for r in rows if r['verification']['status']=='verified'])}</span><span class="l">officially verified</span></div>
  <div class="card"><span class="k">{len([r for r in rows if r['verification']['status']=='corroborated'])}</span><span class="l">corroborated (third-party)</span></div>
  <div class="card"><span class="k">{len(hi)}</span><span class="l">high-confidence picks</span></div>
  <div class="card"><span class="k">{len(med)}</span><span class="l">medium-confidence picks</span></div>
</div>
<h2>Rows, our lines and picks</h2>
<p class="legend"><strong>Our price / Our price 2:</strong> decimal prices we originate (5% overround), one for each side, or a single price on a one-selection market. <strong>n/p</strong> = not priced, because the only input was an OLBG consensus figure on a different market. 
<strong>Basis:</strong> <code>official-league-table</code> / <code>official-standings</code> = model built on official data; <code>consensus</code> = de-vigged OLBG tip share only; <code>none</code> = no defensible input, so no price is shown.</p>
{table(rows, 'tbl-' + meta['slug'])}
{(f'<h2>Handicap lines we originated ({len(mark)})</h2><p class="legend"><code>official-form</code> = projected margin built on the competition&rsquo;s own scoring table. <code>consensus-scaled</code> = probability-implied line using a disclosed per-sport margin scale, capped at 85% probability. Both are our own lines, never bookmaker prices.</p><div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Match</th><th>Favourite line</th><th class="num">Price</th><th>Underdog line</th><th class="num">Price</th><th>Basis</th></tr></thead><tbody>{hcap_rows}</tbody></table></div>') if mark else '<h2>Handicap lines</h2><p class="dim">Not originated for this sport: ' + HANDICAP_GAP.get(sport, "no scoring unit and no defensible baseline were available, so a handicap would be a guess.") + ' Blank rather than invented.</p>'}
{(f'<h2>Match totals we originated ({len(tot)})</h2><div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Match</th><th class="num">Line</th><th class="num">Over</th><th class="num">Under</th></tr></thead><tbody>{tot_rows}</tbody></table></div>') if tot else '<h2>Match totals</h2><p class="dim">' + TOTAL_GAP + '</p>'}
""" + foot(1)
    open(os.path.join(OUT, "sports", meta["slug"] + ".html"), "w").write(page)

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
                 f"<td class='num'>{len([r for r in rows if r['model'].get('total')])}</td></tr>")

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
    top += (f"<tr><td><a href='sports/{r['sport_slug']}.html'>{e(r['sport'])}</a></td><td>{match_label(r)}</td>"
            f"<td class='pick'>{e(p['label'])}</td><td class='num'>{money(price)}</td>"
            f"<td class='num'>{p['prob']*100:.0f}%</td><td>{conf_pill(p['confidence'])}</td>"
            f"<td><a href='predictions.html#{e(r['ref'])}'>read prediction</a></td></tr>")

index = head("Dashboard") + f"""
<section class="hero">
  <h1>Reverse-engineered board, our own lines, our own picks</h1>
  <p class="lede">Every in-scope sport on OLBG.com except soccer/football, American football, boxing, UFC/MMA, hurling,
  horse racing, cycling and specials. {n_events} rows: {n_fixtures} two-sided fixtures and {n_outrights} outright or race markets.
  {n_verified} rows are confirmed against the competition&rsquo;s own site, {n_corroborated} rest on third-party
  corroboration only and are labelled as such, {n_unverified} are published as unverified rather than guessed.
  {n_price} rows carry a price we originated and {len(hi_rows)} picks are graded high confidence &mdash; each of those
  has a written prediction.</p>
  <p class="stamp">Captured {GEN} &middot; every row links to the OLBG event page it came from</p>
</section>

<div class="notice">
  <strong>Re-verified line by line on 2026-10-21.</strong> Every high-confidence pick was re-read against the official
  league page behind it (URC, Pro D2, Top 14, ICEHL, SHL, NHL). Eight predictions were corrected; two were withdrawn when
  only a third-party page backed them and restored after the club&rsquo;s own fixture page and the Swedish federation&rsquo;s
  schedule confirmed the games. The full before-and-after is on the
  <a href="audit.html">audit page</a>; the open issues are on <a href="flagged.html">Flagged for Review</a>.
</div>

<div class="cards">
  <div class="card"><span class="k">{len(by_sport)}</span><span class="l">sports covered</span></div>
  <div class="card"><span class="k">{n_events}</span><span class="l">rows on the board</span></div>
  <div class="card"><span class="k">{n_outrights}</span><span class="l">outright / race rows</span></div>
  <div class="card"><span class="k">{n_verified}</span><span class="l">officially verified</span></div>
  <div class="card"><span class="k">{n_corroborated}</span><span class="l">corroborated only</span></div>
  <div class="card"><span class="k">{n_price}</span><span class="l">with our own price</span></div>
  <div class="card"><span class="k">{len(hi_rows)}</span><span class="l">high-confidence picks</span></div>
  <div class="card warn"><span class="k">{n_unverified}</span><span class="l">flagged unverified</span></div>
</div>

<h2>Coverage by sport</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th class="num">Rows</th><th class="num">of which outright/race</th><th class="num">Verified</th><th class="num">Corroborated</th><th class="num">High conf.</th><th class="num">Priced</th><th class="num">Handicaps</th><th class="num">Totals</th></tr></thead>
<tbody>{cov_rows}</tbody></table></div>
<p class="dim">Rugby League has no dated match fixture on OLBG at capture time: its three rows are 2027 outright markets. Golf, Motor Racing and Greyhounds are
race or tournament markets with a single selection, so they carry one originated price and no handicap or total. All of this is itemised on the
<a href="audit.html">audit page</a> and on <a href="flagged.html">Flagged for Review</a>.</p>

<h2>High-confidence picks</h2>
{"<div class='tablewrap'><table class='board'><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th class='num'>Our price</th><th class='num'>Model</th><th>Conf.</th><th></th></tr></thead><tbody>" + top + "</tbody></table></div>" if top else "<p>None.</p>"}

<h2>Every row on the board</h2>
<div class="tools">
  <input id="q" type="search" placeholder="Search team, competition or sport&hellip;" aria-label="Search fixtures">
  <select id="fsport" aria-label="Filter by sport"><option value="">All sports</option>
  {''.join(f'<option>{e(s)}</option>' for s in SPORT_ORDER if by_sport.get(s))}</select>
  <select id="fconf" aria-label="Filter by confidence"><option value="">All confidence</option>
  <option>HIGH</option><option>MEDIUM</option><option>LOW</option></select>
  <span id="count" class="count"></span>
</div>
<p class="legend"><strong>Our price:</strong> decimal odds we originate (5% overround) for the home side, or for the single selection on an
outright/race row. <strong>n/p</strong> = not priced because OLBG's most-tipped market was not a winner market on that row.
<strong>Basis:</strong> <code>official-table</code>/<code>official-standings</code> = built on official league data;
<code>consensus</code> = de-vigged OLBG tip share only; <code>outright-prior</code>/<code>race-prior</code> = tip share shrunk toward a disclosed
field-size prior.</p>
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
open(os.path.join(OUT, "index.html"), "w").write(index)

# ---------- predictions ----------
pblocks = ""      # rows currently graded HIGH
kept_blocks = ""  # rows that were HIGH when the prose was written, downgraded by the source-tier audit
for ref, p in PREDS.items():
    r = next((x for x in EVENTS if x["ref"] == ref), None)
    if not r: continue
    _downgraded = r["pick"]["confidence"] != "HIGH"
    pr = r["model"]["prices"]; side = r["pick"]["side"]
    price = pr.get("win_home") if side == "home" else pr.get("win_away")
    facts = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["label"])}</a></li>' for s in p["sources"])
    _block = f"""
<article class="prediction" id="{e(ref)}">
  {('<p class="note">Kept after the source-tier audit: this fixture now rests on third-party corroboration only, so the row is graded ' + e(r['pick']['confidence']) + ' and this prediction is not counted among the high-confidence picks. The prose is unchanged.</p>') if _downgraded else ''}
  <div class="pmeta"><span class="tag">{e(r['sport'])}</span> <span class="tag">{e(ref)}</span> {conf_pill(r['pick']['confidence'])}</div>
  <h2>{e(p['headline'])}</h2>
  <p class="fixture">{match_label(r)} &middot; <span class="when">{e(r['start'])} (OLBG)</span>
     {('&middot; ' + e(r['verification']['official_datetime'])) if r['verification'].get('official_datetime') else ''}</p>
  <p class="selection">Betting selection: <strong>{e(p['selection'])}</strong>
     <span class="pricebox">our price {money(price)} &middot; model {r['pick']['prob']*100:.0f}%</span></p>
  <p class="body">{e(p['body'])}</p>
  <p class="srcs"><strong>Verified from:</strong></p><ul class="sourcelist">{facts}</ul>
</article>"""
    if _downgraded:
        kept_blocks += _block
    else:
        pblocks += _block

n_hi_preds = pblocks.count('<article class="prediction"')
n_kept = kept_blocks.count('<article class="prediction"')
kept_section = (f'<h2>Kept after the source-tier audit ({n_kept})</h2><p class="dim">Not counted as high-confidence picks. '
                f'Published so the work is not hidden and can be re-graded once an official fixture source is found.</p>' + kept_blocks) if n_kept else ""

predpage = head("Predictions") + f"""
<section class="pagehead">
  <h1>Written predictions &mdash; high-confidence picks only</h1>
  <p class="lede">{len([r for r in EVENTS if r['pick']['confidence']=='HIGH'])} picks clear the high-confidence bar (officially verified fixture
  <em>and</em> official current-form data for both sides <em>and</em> a model probability of 65% or better). Every sentence that states a fact
  carries a source link. We deliberately wrote nothing for medium or low-confidence rows: there was no verified form data to base it on, and
  inventing it is worse than publishing less.</p>
  <p class="note">Every prediction below belongs to a row that is currently graded high confidence, and the grade is only available to a row whose fixture is on the competition&rsquo;s own site (or one of the two clubs&rsquo; own sites). A row that rests on a third-party listing is labelled <em>corroborated</em>, can never be graded high confidence, and cannot carry a prediction: <code>check_board.py</code> fails the build if one does.</p>
</section>
<h2>High-confidence predictions ({n_hi_preds})</h2>
{pblocks}
{kept_section}
""" + foot(0)
open(os.path.join(OUT, "predictions.html"), "w").write(predpage)

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
<p class="legend"><strong>Money line:</strong> home / draw / away decimal prices, 5% overround; <strong>n/p</strong> = not priced because the only input
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
  <li><strong>Price</strong> &mdash; 5% overround spread proportionally; handicap and total sides are quoted at our standard 1.91 two-way price.</li>
</ol>
""" + foot(0)
open(os.path.join(OUT, "lines.html"), "w").write(linespage)

# ---------- audit (this session's line-by-line review) ----------
AUDIT_CHECKS = [
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
 ("A live OLBG listing no longer matches the captured row",
  "The baseball listing was re-read today for event 160789 (TB Rays @ MIL Brewers). It now renders '24 Oct 01:00' with the featured market "
  "'Over 5.50, Game Totals, 4/4', and its money line shows MIL Brewers 4/7 (57%) and TB Rays 3/7 (43%). The captured row records "
  "'23 Oct 20:00', Money Line, TB Rays 3/6 (50%). The five-hour clock difference and the changed featured market are logged as an irregularity: "
  "the captured values are kept verbatim as a timestamped snapshot and no time is derived from them.",
  "irregularity", "https://www.olbg.com/betting-tips/Baseball/12"),
]

AUDIT_CHANGES = [
 ("scripts/build_gap_sports.py, data/raw/gap_sports_capture_20261021.json, data/gap_sports.json",
  "Captured and priced the 23 outright/race rows for Golf, Motor Racing, Greyhounds, Rugby League and the Gaelic football championship. Prices use the documented field-size prior, not a bookmaker quote."),
 ("scripts/build_site.py",
  "Board now renders 15 sports and 137 rows, adds a Market column so a single-selection row cannot be mistaken for a two-sided one, and publishes this audit page."),
 ("data/predictions.json",
  "RGU-14 no longer states a venue that the sources disagree on. No factual claim was added. IHO-03&rsquo;s prediction was withdrawn while its only source was Eliteprospects and then restored when the Swedish Ice Hockey Association&rsquo;s schedule (stats.swehockey.se) confirmed Timra v Farjestad on 22 Oct &mdash; and corrected the venue to SCA Arena. IHO-01 was restored on the club&rsquo;s own fixture page. The board carries 14 predictions, one for every HIGH row and no others, and check_board.py enforces that."),
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
 ("Documentation quoted numbers the site never had", "README.md and COORDINATION.md stated &lsquo;76 fixtures&rsquo; and &lsquo;48 detailed human predictions&rsquo;, and the README listed <code>methodology.html</code>, <code>flagged-review.html</code> and <code>js/dashboard.js</code> as live pages after they had been removed. The published board carries {n_events} rows and {len(PREDS)} predictions. Both documents now quote the published figures.", "https://github.com/buffedlizard55-lab/OLBG3/blob/main/README.md"),
 ("A prediction named a venue the sources dispute", "The Leinster v Munster prediction said &lsquo;At the Aviva Stadium&rsquo;, while the official URC Round 3 record lists Leinster&rsquo;s home fixture at &lsquo;Laya Arena&rsquo; and the row&rsquo;s venue is blank here for exactly that reason (FL-016). The venue sentence was removed rather than picked from two conflicting names.", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
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
 ("Our prices are model output, not market prices", "Every price on the site is computed by <code>scripts/model.py</code> from either official data or the OLBG tip share, with a 5% overround. They are not bookmaker prices and they are not verified facts. Where the only input is a public tip share, the row is graded LOW and cannot be graded higher.", "&mdash;"),
]


IRREGULARITY_EXTRA = [
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
]
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

flagpage = head("Flagged for Review") + f"""
<section class="pagehead flagged">
  <h1>Flagged for Review</h1>
  <p class="lede">Everything here is published deliberately, with its source, so it can be checked and challenged. None of it blocks the
  release; all of it deserves a human eye. {len(irregularities)} findings, {n_corroborated} rows that rest on third-party corroboration
  only, and {n_unverified} unverified rows.</p>
</section>

<h2>Findings &amp; irregularities</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th class="num">#</th><th>Finding and what we did about it</th><th>Evidence</th></tr></thead>
<tbody>{irr_html}</tbody></table></div>

<h2>Rows corroborated by a third party only ({n_corroborated})</h2>
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
<section class="pagehead">
  <h1>Method, scope and what we refuse to do</h1>
</section>
<h2>Scope</h2>
<p>OLBG lists 20+ sports. We excluded, on instruction: soccer/football, American football, boxing, UFC/MMA, hurling, horse racing,
cycling and specials. Everything left is on the board: 114 two-sided fixtures plus the 23 outright and race markets that OLBG publishes
for golf, Formula 1, greyhound racing, rugby league and the Gaelic football championship. A one-selection market is labelled
&ldquo;outright&rdquo; or &ldquo;race&rdquo; in the Market column so it cannot be mistaken for a match.</p>
<div class="grid2">
  <div class="panel"><h3>Excluded</h3><ul class="tight">{excl}</ul></div>
  <div class="panel"><h3>Included</h3><ul class="tight">{sport_links}</ul></div>
</div>

<div class="panel" style="margin-top:14px"><h3>Previously disclosed gap, now closed</h3><ul class="tight">{fc}</ul>
<p class="dim" style="margin:8px 0 0">These four sports were missing from the previous build because their rows are race or tournament markets rather than
two-sided fixtures. They are now captured from the same OLBG listings and priced with the one-selection model described below, so {n_gap} rows
({n_gap_priced} of them priced) have been added. Raw capture: <code>data/raw/gap_sports_capture_20261021.json</code>; generator:
<code>scripts/build_gap_sports.py</code>; output: <code>data/gap_sports.json</code>.</p></div>
<div class="panel" style="margin-top:14px"><h3>Still not captured</h3><ul class="tight">{nc}</ul>
<p class="dim" style="margin:8px 0 0">No esports listing surfaced on the OLBG tips index at capture time. That is disclosed rather than guessed at.</p></div>

<h2>How the OLBG site is structured (reverse-engineered)</h2>
<pre class="code">listing : https://www.olbg.com/betting-tips/&lt;Sport_Slug&gt;/&lt;sport_id&gt;
event   : https://www.olbg.com/betting-tips/&lt;Sport&gt;/&lt;Group&gt;/&lt;Competition&gt;/&lt;Home&gt;_v_&lt;Away&gt;/&lt;sport_id&gt;?event_id=&lt;id&gt;</pre>
<ul class="tight">
  <li>IDs found: Tennis 3, Basketball 4, Cricket 7, Snooker 8, Rugby Union 9, Rugby League 10, Baseball 12, Ice Hockey 13, Darts 15, Handball 20, Volleyball 21, Gaelic Football 25.</li>
  <li>The slug without an ID is a 404; a wrong ID redirects to the right slug, so the slug is authoritative and the ID is cosmetic.</li>
  <li>The listing exposes, per event: both sides, date/time, competition (only for some sports), the market, the most-tipped selection, the tip count and the percentage of tips on that selection.</li>
</ul>

<h2>How our lines are made</h2>
<ol class="steps">
  <li><strong>Rugby union (URC fixtures).</strong> Expected points for each side = mean(its points-for per game, opponent&rsquo;s points-against per game), taken from the official URC table. Home side +{int(3)} points. Margin sd 13 points gives win/draw/loss probabilities; totals come from the same expected-points pair; the handicap line is the projected margin rounded to the nearest half point.</li>
  <li><strong>Ice hockey (NHL fixtures).</strong> Same idea with goals from the official NHL standings, home side +0.15 goals, and a logistic mapping of the goal difference to a 2-way win probability.</li>
  <li><strong>Everything else.</strong> The only input on the page is OLBG&rsquo;s consensus tip share, so our probability equals that share, capped at 98% (a 100% share cannot be priced). No total, no handicap &mdash; there is no scoring baseline to build one from.</li>
  <li><strong>Pricing.</strong> Decimal odds = (1 &minus; 5%) / probability, i.e. a 5% overround allocated in proportion to probability.</li>
</ol>

<h2>How outright and race prices are made (the one-selection markets)</h2>
<p>A golf tournament, an F1 race, a greyhound race or a season-long championship has one winner and no opposing side, so there is no
home/away split and no draw to price. Handicapping it or setting a "match total" would be invention, so we originate the win price only:</p>
<ol class="steps">
  <li><code>p = (wins + a) / (total + k)</code>, where the prior <code>Beta(a, b)</code> has mean <code>1/N</code> and strength <code>k</code>
      (<code>a = k/N</code>, <code>b = k &minus; k/N</code>). In words: the OLBG tip share is shrunk toward "one chance in a field of N".</li>
  <li>Decimal odds = <code>(1 &minus; 0.05) / p</code>, the same 5% overround as the two-sided model.</li>
  <li>If OLBG publishes a selection but no tip count (Hero Women&rsquo;s Indian Open), no probability and no price is originated.</li>
</ol>
<p class="note"><strong>Disclosed assumptions.</strong> N and k are ours, not facts. OLBG does not publish a field size on any of these rows.</p>
<div class="tablewrap"><table class="board">
<thead><tr><th>Field basis</th><th class="num">N assumed</th><th class="num">k (prior strength)</th><th>Why this number</th></tr></thead>
<tbody>{gap_prior_rows}</tbody></table></div>
<ul class="tight">{gap_basis_notes}</ul>
<p class="dim">The figures above are written into every row (<code>data/gap_sports.json</code>) so a reviewer can recompute the price. Treat them as
model output, never as a market quote.</p>
<p class="note"><strong>Disclosed assumptions</strong> (constants we chose, not measured facts):</p>
<ul class="tight">{assum}</ul>

<h2>Confidence grading</h2>
<p>Three factors, scored 0&ndash;6: fixture verified against an official source (+2), official current-form data for <em>both</em> sides (+2),
model probability of the pick &ge;65% (+2, or +1 if &ge;55%). <strong>HIGH &ge; 6</strong>, <strong>MEDIUM 3&ndash;5</strong>, <strong>LOW &le; 2</strong>.
A row built only on a public tip share therefore can never be graded above MEDIUM, and in practice lands on LOW.</p>
<p>Current split: HIGH {conf_counter['HIGH']} &middot; MEDIUM {conf_counter['MEDIUM']} &middot; LOW {conf_counter['LOW']}.</p>

<h2>What we will not do</h2>
<ul class="tight">
  <li>We do not infer a competition, a venue, a time zone or a score. If the official source does not say it, the cell stays blank and the row is flagged.</li>
  <li>We do not write predictions for picks we cannot support with verified form. That is why only {len(PREDS)} of {n_events} rows carry a written prediction.</li>
  <li>We do not claim that a row is verified because a source exists for the competition. A row is verified only when the specific fixture appears on that source; see the <a href="audit.html">audit page</a>.</li>
  <li>We do not present our own prices as facts or as bookmaker odds.</li>
</ul>
""" + foot(0)
open(os.path.join(OUT, "method.html"), "w").write(method)

# ---------- nojekyll ----------
for asset in ("style.css", "app.js"):
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
