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
NAV = [("index.html", "Dashboard"), ("predictions.html", "Predictions"),
       ("verification.html", "Verification"), ("flagged.html", "Flagged for Review"),
       ("method.html", "Method & Scope"), ("feed-overview.html", "Official feed"),
       ("matches.html", "Feed matches"), ("coverage.html", "Feed coverage"), ("review.html", "Feed review"),
       ("olbg/index.html", "OLBG lines (audit)")]
ev = json.load(open(os.path.join(ROOT, "data/events.json")))
EVENTS = ev["events"]
ASSUMPTIONS = ev["assumptions"]
PREDS = {p["ref"]: p for p in json.load(open(os.path.join(ROOT, "data/predictions.json")))["predictions"]}
OFF = json.load(open(os.path.join(ROOT, "data/official.json")))

SPORT_ORDER = ["Tennis","Basketball","Ice Hockey","Cricket","Baseball","Volleyball","Darts",
               "Snooker","Rugby Union","Rugby League","Handball","Gaelic Football"]
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
    "note": "At the time of capture the Rugby League listing showed ONLY outright tournament markets (State of Origin 2027, Super League 2027 Grand Final, NRL 2027 Grand Final) and no dated match fixtures, so it contributes no rows to the match tables. Recorded on the Flagged for Review page.", "id": 10}

NOT_CAPTURED = ["Golf (tournament/outright markets, no two-sided fixture)",
                 "Motor Racing (race markets, no two-sided fixture)",
                 "Greyhound Racing (race markets, no two-sided fixture)",
                 "Esports (no listing surfaced on the OLBG tips index at capture time)"]
EXCLUDED = ["Soccer / Football","American Football","Boxing","UFC / MMA","Hurling","Horse Racing","Cycling","Specials (TV/Politics/Awards)"]

def e(x):
    return html.escape(str(x)) if x is not None else ""

def money(p):
    return f"{p:.2f}" if isinstance(p, (int, float)) else "&mdash;"

# ---------- statistics ----------
n_events = len(EVENTS)
by_sport = defaultdict(list)
for r in EVENTS:
    by_sport[r["sport"]].append(r)
n_verified = sum(1 for r in EVENTS if r["verification"]["status"] == "verified")
n_unverified = n_events - n_verified
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

def ver_cell(r):
    v = r["verification"]
    if v["status"] == "verified":
        lab = e(v["official_label"]) or "official source"
        return f'<a class="ok" href="{e(v["official_url"])}" rel="noopener" title="{e(v["note"])}">&#10003; {lab}</a>'
    return '<span class="unver" title="No official source retrieved for this fixture">unverified</span>'

def price_cell(r):
    m = r["model"]
    if not m.get("prices"):
        return '<td class="num dim">no price</td>'
    p = m["prices"]
    if "draw" in p:
        return f'<td class="num">{money(p.get("win_home"))}</td><td class="num">{money(p.get("draw"))}</td><td class="num">{money(p.get("win_away"))}</td>'
    h = p.get("win_home") or p.get("win_home")
    # consensus rows only price the picked side and its opposite
    side = "home" if "win_home" in p else "away"
    return f'<td class="num">{money(p.get("win_home"))}</td><td class="num dim">n/p</td><td class="num">{money(p.get("win_away"))}</td>'

def match_label(r):
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
<td class="when">{e(r['start'])}</td>
{price_cell(r)}
<td class="pick">{pick} {prob}</td>
<td>{conf_pill(p['confidence'])}</td>
<td class="basis">{e(r['model'].get('basis','none'))}</td>
<td class="src">{ver_cell(r)}</td>
</tr>"""

TABLE_HEAD = """<thead><tr>
<th>Ref</th><th>Sport</th><th>Competition</th><th>Match</th><th>Start (as listed)</th>
<th class="num">Our home</th><th class="num">Draw</th><th class="num">Our away</th>
<th>Our pick</th><th>Conf.</th><th>Basis</th><th>Official source</th>
</tr></thead>"""

def table(rows, tid="tbl"):
    body = "\n".join(row_html(r) for r in rows)
    return f'<div class="tablewrap"><table id="{tid}" class="board">{TABLE_HEAD}<tbody>{body}</tbody></table></div>'

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
        f"<td>{e(r['home'] if r['model']['handicap']['fav']=='home' else r['away'])} -{abs(r['model']['handicap']['line']):.1f}</td>"
        f"<td class='num'>{money(r['model']['handicap']['price'])}</td>"
        f"<td>{e(r['away'] if r['model']['handicap']['fav']=='home' else r['home'])} +{abs(r['model']['handicap']['dog_line']):.1f}</td>"
        f"<td class='num'>{money(r['model']['handicap']['dog_price'])}</td></tr>" for r in mark)
    tot_rows = "".join(
        f"<tr><td>{e(r['ref'])}</td><td>{match_label(r)}</td><td class='num'>{r['model']['total']['line']}</td>"
        f"<td class='num'>{money(r['model']['total']['over'])}</td><td class='num'>{money(r['model']['total']['under'])}</td></tr>" for r in tot)
    page = head(f"{sport}", 1) + f"""
<section class="pagehead">
  <h1>{e(sport)}</h1>
  <p class="lede">{len(rows)} fixtures captured from <a href="{e(meta['listing'])}" rel="noopener">OLBG&rsquo;s {e(sport)} tips page</a>
  (sport ID {e(meta['id'])}). {len([r for r in rows if r['verification']['status']=='verified'])} of them were confirmed against an official competition source;
  the rest are published as <em>unverified</em> and listed on the <a href="../flagged.html">Flagged for Review</a> page.</p>
  <p class="note">{e(meta['note'])}</p>
</section>
<div class="cards">
  <div class="card"><span class="k">{len(rows)}</span><span class="l">fixtures</span></div>
  <div class="card"><span class="k">{len([r for r in rows if r['verification']['status']=='verified'])}</span><span class="l">officially verified</span></div>
  <div class="card"><span class="k">{len(hi)}</span><span class="l">high-confidence picks</span></div>
  <div class="card"><span class="k">{len(med)}</span><span class="l">medium-confidence picks</span></div>
</div>
<h2>Fixtures, our lines and picks</h2>
<p class="legend"><strong>Our home / Our away:</strong> decimal prices we originate (5% overround). <strong>n/p</strong> = not priced, because the only input was an OLBG consensus figure on a different market. 
<strong>Basis:</strong> <code>official-league-table</code> / <code>official-standings</code> = model built on official data; <code>consensus</code> = de-vigged OLBG tip share only; <code>none</code> = no defensible input, so no price is shown.</p>
{table(rows, 'tbl-' + meta['slug'])}
{(f'<h2>Handicap lines we originated</h2><div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Match</th><th>Favourite line</th><th class="num">Price</th><th>Underdog line</th><th class="num">Price</th></tr></thead><tbody>{hcap_rows}</tbody></table></div>') if mark else '<h2>Handicap lines</h2><p class="dim">Not originated for this sport: OLBG provides no win-share or scoring baseline here, so a handicap would be a guess. Blank rather than invented.</p>'}
{(f'<h2>Totals we originated</h2><div class="tablewrap"><table class="board"><thead><tr><th>Ref</th><th>Match</th><th class="num">Line</th><th class="num">Over</th><th class="num">Under</th></tr></thead><tbody>{tot_rows}</tbody></table></div>') if tot else '<h2>Match totals</h2><p class="dim">Not originated for this sport: no official scoring baseline was captured, so any total would be invented. Recorded as flagged.</p>'}
""" + foot(1)
    open(os.path.join(OUT, "sports", meta["slug"] + ".html"), "w").write(page)

# ---------- index ----------
cov_rows = ""
for sport in SPORT_ORDER:
    rows = by_sport.get(sport, [])
    meta = SPORT_META[sport]
    ver = len([r for r in rows if r["verification"]["status"] == "verified"])
    hi = len([r for r in rows if r["pick"]["confidence"] == "HIGH"])
    cov_rows += (f"<tr><td><a href='sports/{meta['slug']}.html'>{e(sport)}</a></td><td class='num'>{len(rows)}</td>"
                 f"<td class='num'>{ver}</td><td class='num'>{hi}</td>"
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
  <h1>Reverse-engineered match board, our own lines, our own picks</h1>
  <p class="lede">Every in-scope sport on OLBG.com except soccer/football, American football, boxing, UFC/MMA, hurling,
  horse racing, cycling and specials. {n_events} fixtures captured, {n_verified} confirmed against an official competition source,
  {n_price} priced by our model, {len(hi_rows)} graded high confidence &mdash; each with a written prediction.</p>
  <p class="stamp">Captured {GEN} &middot; every row links to the OLBG event page it came from</p>
</section>

<div class="cards">
  <div class="card"><span class="k">{len(by_sport)}</span><span class="l">sports covered</span></div>
  <div class="card"><span class="k">{n_events}</span><span class="l">fixtures on the board</span></div>
  <div class="card"><span class="k">{n_verified}</span><span class="l">officially verified</span></div>
  <div class="card"><span class="k">{n_price}</span><span class="l">with our own price</span></div>
  <div class="card"><span class="k">{len(hi_rows)}</span><span class="l">high-confidence picks</span></div>
  <div class="card warn"><span class="k">{n_unverified}</span><span class="l">flagged unverified</span></div>
</div>

<h2>Coverage by sport</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th>Sport</th><th class="num">Fixtures</th><th class="num">Verified</th><th class="num">High conf.</th><th class="num">Priced</th><th class="num">Handicaps</th><th class="num">Totals</th></tr></thead>
<tbody>{cov_rows}</tbody></table></div>
<p class="dim">Rugby League had no dated fixtures on OLBG at capture time (outright markets only) &mdash; see <a href="flagged.html">Flagged for Review</a>.</p>

<h2>High-confidence picks</h2>
{"<div class='tablewrap'><table class='board'><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th class='num'>Our price</th><th class='num'>Model</th><th>Conf.</th><th></th></tr></thead><tbody>" + top + "</tbody></table></div>" if top else "<p>None.</p>"}

<h2>Every fixture on the board</h2>
<div class="tools">
  <input id="q" type="search" placeholder="Search team, competition or sport&hellip;" aria-label="Search fixtures">
  <select id="fsport" aria-label="Filter by sport"><option value="">All sports</option>
  {''.join(f'<option>{e(s)}</option>' for s in SPORT_ORDER if by_sport.get(s))}</select>
  <select id="fconf" aria-label="Filter by confidence"><option value="">All confidence</option>
  <option>HIGH</option><option>MEDIUM</option><option>LOW</option></select>
  <span id="count" class="count"></span>
</div>
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
  (NBA.com, NHL.com, URC) and the link is in the row. Where we could not do that, the row says <em>unverified</em> &mdash; we leave the
  competition blank rather than guessing it from a club name.</p></div>
  <div class="panel"><h3>What is ours</h3><p>Prices, handicap lines, totals and picks are produced by our own model
  (<a href="method.html">method</a>). They are opinions priced off disclosed inputs, not facts, and not bookmaker prices.</p></div>
</div>
""" + foot(0)
open(os.path.join(OUT, "index.html"), "w").write(index)

# ---------- predictions ----------
pblocks = ""
for ref, p in PREDS.items():
    r = next((x for x in EVENTS if x["ref"] == ref), None)
    if not r: continue
    pr = r["model"]["prices"]; side = r["pick"]["side"]
    price = pr.get("win_home") if side == "home" else pr.get("win_away")
    facts = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["label"])}</a></li>' for s in p["sources"])
    pblocks += f"""
<article class="prediction" id="{e(ref)}">
  <div class="pmeta"><span class="tag">{e(r['sport'])}</span> <span class="tag">{e(ref)}</span> {conf_pill(r['pick']['confidence'])}</div>
  <h2>{e(p['headline'])}</h2>
  <p class="fixture">{match_label(r)} &middot; <span class="when">{e(r['start'])} (OLBG)</span>
     {('&middot; ' + e(r['verification']['official_datetime'])) if r['verification'].get('official_datetime') else ''}</p>
  <p class="selection">Betting selection: <strong>{e(p['selection'])}</strong>
     <span class="pricebox">our price {money(price)} &middot; model {r['pick']['prob']*100:.0f}%</span></p>
  <p class="body">{e(p['body'])}</p>
  <p class="srcs"><strong>Verified from:</strong></p><ul class="sourcelist">{facts}</ul>
</article>"""

predpage = head("Predictions") + f"""
<section class="pagehead">
  <h1>Written predictions &mdash; high-confidence picks only</h1>
  <p class="lede">{len(PREDS)} picks cleared the high-confidence bar (officially verified fixture <em>and</em> official current-form data
  for both sides <em>and</em> a model probability of 65% or better). Every sentence that states a fact carries a source link.
  We deliberately wrote nothing for medium or low-confidence rows: there was no verified form data to base it on, and inventing it is worse than publishing less.</p>
</section>
{pblocks}
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
    else:
        st = "<span class='pill low'>unverified</span>"
        off = '<span class="dim">no official source retrieved</span>'
        dt = '<span class="dim">&mdash;</span>'
    vrows += (f"<tr><td>{e(r['ref'])}</td><td>{e(r['sport'])}</td><td>{match_label(r)}</td>"
              f"<td>{e(r['start'])}</td><td>{dt}</td><td>{off}</td><td>{st}</td>"
              f"<td><a href='{e(r['olbg_event_url'])}' rel='noopener'>OLBG event</a></td></tr>")

verpage = head("Verification") + f"""
<section class="pagehead">
  <h1>Row-by-row verification log</h1>
  <p class="lede">Each row records what OLBG showed, what the official source says, and the link. {n_verified} rows are confirmed;
  {n_unverified} are marked unverified because no official source was retrieved for them in this session &mdash; they are published with the
  field blank rather than filled from inference.</p>
</section>
<div class="tablewrap"><table class="board">
<thead><tr><th>Ref</th><th>Sport</th><th>Match</th><th>OLBG start</th><th>Official fixture (verbatim)</th><th>Official source</th><th>Status</th><th></th></tr></thead>
<tbody>{vrows}</tbody></table></div>
<h2>Method of checking</h2>
<ol class="steps">
  <li>Read the fixture off the OLBG sport listing, then off the individual OLBG event page URL recorded in the row.</li>
  <li>Find the same fixture on the competition&rsquo;s own website (official scheduler / match centre / standings).</li>
  <li>Copy the official wording verbatim into the row. Do not convert time zones, do not round, do not &ldquo;fix&rdquo; a discrepancy &mdash; log it.</li>
  <li>If step 2 fails, the row keeps its OLBG data, the official column stays blank, and the row appears on Flagged for Review.</li>
</ol>
""" + foot(0)
open(os.path.join(OUT, "verification.html"), "w").write(verpage)

# ---------- flagged ----------
irregularities = [
 ("Repo had no substantive content", "The repository at commit <code>96f089b</code> contained a single 7-byte <code>README.md</code> (<code># OLBG3</code>) and nothing else. There was no prior work, code, data or CI to review or trust, so nothing in it could be &ldquo;confirmed&rdquo;. Everything on this site was built in this session.", "&mdash;"),
 ("OLBG start times run 7&ndash;10 minutes late", "On every fixture where we could compare, OLBG&rsquo;s displayed start time is later than the official one: NHL 19:37 vs 19:30 EDT (both 21 Oct games); NBA 19:10 vs 19:00, 19:40 vs 19:30, 20:10 vs 20:00 ET. Treat OLBG minute-values as approximate.", "https://www.nhl.com/schedule/2026-10-21"),
 ("OLBG does not state a time zone", "Times are shown as bare values (&ldquo;Today 19:10&rdquo;). They line up with US Eastern for the North American fixtures but with local/UK time for the URC fixtures, so the displayed zone is inconsistent. We publish the string exactly as shown and label the column &ldquo;Start (as listed)&rdquo;.", "https://www.olbg.com/betting-tips/Rugby_Union/9"),
 ("Competition is blank for most sports", "Tennis, cricket, volleyball, darts, snooker, handball, Gaelic football and rugby union listings do not show a competition (the URL group is <code>All_&lt;Sport&gt;/All_Events</code>). We left the column blank rather than infer a league from the team names.", "https://www.olbg.com/betting-tips/Tennis/3"),
 ("Sport IDs are mandatory and some are stale", "<code>/betting-tips/Basketball</code> and <code>/betting-tips/Cricket</code> return 404 without the numeric ID. <code>/Ice_Hockey/11</code> redirects to 13, <code>/Baseball/5</code> to 12, <code>/Handball/14</code> to 20. Any link built with a guessed ID lands on the wrong sport or a 404.", "https://www.olbg.com/betting-tips/Handball/20"),
 ("Listings are paginated", "Baseball, ice hockey, snooker, Gaelic football and handball pages end in a &ldquo;Load More Tips&rdquo; control, so the captured rows are the first page and are <strong>not</strong> a complete list of that sport&rsquo;s fixtures. One handball row (FC Barcelona v Montpellier) was cut off mid-record and was therefore dropped rather than reconstructed.", "https://www.olbg.com/betting-tips/Handball/20"),
 ("Rugby League has no match fixtures", "At capture time the Rugby League page listed only outright markets (State of Origin 2027, Super League 2027 Grand Final, NRL 2027 Grand Final). No dated match could be placed on the board, so the sport is listed with zero rows.", "https://www.olbg.com/betting-tips/Rugby_League/10"),
 ("Gaelic football rows show no market", "OLBG&rsquo;s Gaelic football listing displays no market name for its selections (the market column is empty on their own page) even though the selections are clearly handicap-style. We left market and competition blank.", "https://www.olbg.com/betting-tips/Gaelic_Football/25"),
 ("Team names differ between OLBG and the official source", "OLBG says &ldquo;Bulls&rdquo;, &ldquo;Stormers&rdquo;, &ldquo;BUF Sabres&rdquo;; the official sources say &ldquo;Vodacom Bulls&rdquo;, &ldquo;DHL Stormers&rdquo;, &ldquo;Buffalo Sabres&rdquo;. We map these with an explicit, published alias table in <code>scripts/model.py</code> &mdash; name normalisation only, no value is altered.", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
 ("Totals and handicaps are missing for most sports", "A total or a handicap needs a scoring baseline. We only had official scoring data for URC and NHL. For the other nine sports we published no total and no handicap rather than invent one. This is a deliberate gap, not an oversight.", "&mdash;"),
 ("Our prices are model output, not market prices", "Every price on the site is computed by <code>scripts/model.py</code> from either official data or the OLBG tip share, with a 5% overround. They are not bookmaker prices and they are not verified facts. Where the only input is a public tip share, the row is graded LOW and cannot be graded higher.", "&mdash;"),
]

def _src(u):
    if u == "&mdash;":
        return '<span class="dim">&mdash;</span>'
    return '<a href="' + e(u) + '" rel="noopener">source</a>'

irr_html = "".join(
    "<tr><td class='num'>" + str(i + 1) + "</td><td><strong>" + e(t) + "</strong><p>" + d + "</p></td><td>" + _src(u) + "</td></tr>"
    for i, (t, d, u) in enumerate(irregularities))

def _unver_row(r):
    comp = e(r["competition"]) if r["competition"] else '<span class="dim">blank</span>'
    return ("<tr><td>" + e(r["ref"]) + "</td><td>" + e(r["sport"]) + "</td><td>" + match_label(r) + "</td><td>" + comp +
            "</td><td>" + e(r["start"]) + "</td><td><a href='" + e(r["olbg_event_url"]) + "' rel='noopener'>OLBG event page</a></td>"
            "<td><span class='pill low'>unverified</span></td></tr>")

unver_rows = "".join(_unver_row(r) for r in EVENTS if r["verification"]["status"] != "verified")

flagpage = head("Flagged for Review") + f"""
<section class="pagehead flagged">
  <h1>Flagged for Review</h1>
  <p class="lede">Everything here is published deliberately, with its source, so it can be checked and challenged. None of it blocks the
  release; all of it deserves a human eye. {len(irregularities)} findings and {n_unverified} unverified rows.</p>
</section>

<h2>Findings &amp; irregularities</h2>
<div class="tablewrap"><table class="board">
<thead><tr><th class="num">#</th><th>Finding and what we did about it</th><th>Evidence</th></tr></thead>
<tbody>{irr_html}</tbody></table></div>

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
sport_links = "".join(f"<li><a href='sports/{SPORT_META[s]['slug']}.html'>{e(s)}</a> &mdash; {len(by_sport.get(s,[]))} fixtures</li>" for s in SPORT_ORDER)
excl = "".join(f"<li>{e(x)}</li>" for x in EXCLUDED)
nc = "".join(f"<li>{e(x)}</li>" for x in NOT_CAPTURED)

method = head("Method & Scope") + f"""
<section class="pagehead">
  <h1>Method, scope and what we refuse to do</h1>
</section>
<h2>Scope</h2>
<p>OLBG lists 20+ sports. We excluded, on instruction: soccer/football, American football, boxing, UFC/MMA, hurling, horse racing,
cycling and specials. Everything left that sets two sides or two players against each other is on the board.</p>
<div class="grid2">
  <div class="panel"><h3>Excluded</h3><ul class="tight">{excl}</ul></div>
  <div class="panel"><h3>Included</h3><ul class="tight">{sport_links}</ul></div>
</div>

<div class="panel" style="margin-top:14px"><h3>Eligible but not captured this pass</h3><ul class="tight">{nc}</ul>
<p class="dim" style="margin:8px 0 0">These are race or tournament markets rather than two-sided fixtures, so they need a different schema. They are disclosed as a gap, not presented as complete.</p></div>

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
print("board pages:", len(glob.glob(os.path.join(OUT, "sports/*.html"))) + 5)
print("verified", n_verified, "unverified", n_unverified, "priced", n_price, "hcap", n_hcap, "totals", n_total)
