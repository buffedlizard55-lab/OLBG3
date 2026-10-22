#!/usr/bin/env python3
"""Build the OLBG lines track into olbg-board/ and mirror it to olbg/ at the repo root.

Everything is generated from data/*.json, so the site can never disagree with the data.
"""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "olbg-board"   # published at /olbg/ inside the shared artifact
SNAPSHOT = ROOT / "olbg"        # identical bytes at the repo root for the legacy Pages publisher

E = html.escape

SPORT_SLUG = {
    "Cricket": "cricket", "Tennis": "tennis", "Basketball": "basketball",
    "Snooker": "snooker", "Darts": "darts", "Rugby Union": "rugby-union",
    "Rugby League": "rugby-league", "Ice Hockey": "ice-hockey", "Baseball": "baseball",
    "Volleyball": "volleyball", "Handball": "handball", "Golf": "golf",
    "Motor Racing": "motor-racing", "Gaelic Football": "gaelic-football",
    "Greyhounds": "greyhounds",
}

SPORT_ICON = {
    "Cricket": "🏏", "Tennis": "🎾", "Basketball": "🏀", "Snooker": "🎱", "Darts": "🎯",
    "Rugby Union": "🏉", "Rugby League": "🏉", "Ice Hockey": "🏒", "Baseball": "⚾",
    "Volleyball": "🏐", "Handball": "🤾", "Golf": "⛳", "Motor Racing": "🏎️",
    "Gaelic Football": "🥎", "Greyhounds": "🐕",
}


def load(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def match_date(m: dict) -> str:
    """Prefer an official start date without discarding the raw OLBG label shown beside it."""
    return (m.get("official_start_utc") or "")[:10] or m["date_iso"] or m["olbg_date_label"]


def conf_badge(c: str) -> str:
    return f'<span class="badge badge-{E(c)}">{E(c)}</span>'


def link(url: str, label: str) -> str:
    return f'<a href="{E(url)}" rel="noopener nofollow" target="_blank">{E(label)}</a>'


def nav(active: str, depth: int) -> str:
    pre = "../" * depth
    items = [
        ("index.html", "Dashboard"),
        ("picks.html", "Lines &amp; picks"),
        ("predictions.html", "Predictions"),
        ("matches.html", "All matches"),
        ("methodology.html", "Method &amp; sources"),
        ("flagged.html", "Flagged for review"),
        ("https://buffedlizard55-lab.github.io/OLBG3/", "Main site"),
    ]
    out = []
    for href, label in items:
        cls = ' class="active"' if href == active else ""
        absolute = href.startswith("http")
        target = ' target="_blank" rel="noopener"' if absolute else ""
        out.append(f'<a href="{href if absolute else pre + href}"{cls}{target}>{label}</a>')
    return "".join(out)


def page(title: str, body: str, active: str, depth: int, subtitle: str = "") -> str:
    pre = "../" * depth
    stamp = E(RUN["harvest_completed_utc"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} · OLBG3 Sports Dashboard</title>
<meta name="description" content="Reverse-engineered OLBG fixture coverage, our own originated lines, confidence-rated picks and verified sources.">
<link rel="stylesheet" href="{pre}assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="wrap">
    <a class="brand" href="{pre}index.html"><span class="dot"></span> OLBG3 <span class="brand-sub">Sports Dashboard</span></a>
    <nav>{nav(active, depth)}</nav>
  </div>
</header>
<main class="wrap">
{f'<p class="crumb">{subtitle}</p>' if subtitle else ''}
{body}
</main>
<footer class="foot">
  <div class="wrap">
    <p><strong>Data as harvested {stamp}.</strong> Every OLBG field is transcribed from the linked OLBG page; our lines are model output, not market prices. 18+ · Betting involves risk.</p>
    <p><a href="{pre}methodology.html">Method</a> · <a href="{pre}flagged.html">Flagged for review</a> · <a href="https://github.com/buffedlizard55-lab/OLBG3">Repository</a></p>
  </div>
</footer>
<script src="{pre}assets/app.js"></script>
</body>
</html>
"""


def stat(value, label: str, hint: str = "") -> str:
    h = f'<span class="stat-hint">{E(hint)}</span>' if hint else ""
    return f'<div class="stat"><span class="stat-value">{value}</span><span class="stat-label">{E(label)}</span>{h}</div>'


def confidence_bar(counts: dict) -> str:
    total = sum(counts.values()) or 1
    segs = []
    for key in ("high", "medium", "low"):
        pct = 100 * counts.get(key, 0) / total
        segs.append(f'<span class="seg seg-{key}" style="width:{pct:.1f}%" title="{key}: {counts.get(key,0)}"></span>')
    return f'<div class="cbar">{"".join(segs)}</div>'


def sources_cell(match: dict, verifications: dict) -> str:
    bits = [link(match["olbg_url"], "OLBG")]
    for vid in match.get("verification_ids", []):
        src = verifications.get(vid)
        if src:
            bits.append(link(src["url"], src["name"].split("—")[0].strip()))
    return " · ".join(bits)


def main() -> None:
    matches = load("matches.json", [])
    lines = {x["match_id"]: x for x in load("lines.json", [])}
    preds = load("predictions-olbg.json", {"predictions": []})["predictions"]
    flagged = load("flagged.json", {"items": []})["items"]
    meta = load("meta.json", {})
    ver = load("verifications.json", {"sources": [], "event_verifications": {}})
    vmap = {s["id"]: s for s in ver.get("sources", [])}

    sports = []
    for m in matches:
        if m["sport"] not in sports:
            sports.append(m["sport"])

    counts_all = {"high": 0, "medium": 0, "low": 0}
    for l in lines.values():
        counts_all[l["confidence"]] += 1

    verified_comp = sum(1 for m in matches if m["competition_status"] == "verified")
    with_price = sum(1 for l in lines.values() if l.get("our_price_pick"))
    with_hc = sum(1 for l in lines.values() if l.get("our_handicap_line") is not None)
    with_total = sum(1 for l in lines.values() if l.get("our_total_line") is not None)

    # ---------- index ----------
    high_rows = [m for m in preds]
    high_table = "".join(
        f"""<tr><td>{E(p['sport'])}</td><td>{E(p['match'])}</td>
        <td class="pick">{E(p['selection'])}</td><td class="num">{lines[p['match_id']]['our_price_pick']} <span class="muted small">({lines[p['match_id']].get('our_us_odds_pick','')})</span></td>
        <td>{conf_badge(p['confidence'])}</td><td>{link(p['sources'][0]['url'], 'source')}</td></tr>"""
        for p in high_rows
    )

    sport_rows = []
    for s in sports:
        rows = [m for m in matches if m["sport"] == s]
        c = {"high": 0, "medium": 0, "low": 0}
        for m in rows:
            c[lines[m["id"]]["confidence"]] += 1
        slug = SPORT_SLUG[s]
        sport_rows.append(
            f"""<tr><td><a href="sports/{slug}.html">{SPORT_ICON.get(s,'•')} {E(s)}</a></td>
            <td class="num">{len(rows)}</td><td class="num">{c['high']}</td><td class="num">{c['medium']}</td><td class="num">{c['low']}</td>
            <td>{confidence_bar(c)}</td>
            <td class="num">{sum(1 for m in rows if m['competition_status']=='verified')}/{len(rows)}</td></tr>"""
        )

    flag_rows = "".join(
        f"""<tr><td><a href="flagged.html#{E(f['id'])}">{E(f['id'])}</a></td><td>{E(f['severity'])}</td><td>{E(f['title'])}</td></tr>"""
        for f in flagged[:6]
    )

    index_body = f"""
<section class="hero">
  <h1>Every OLBG fixture we cover, with our own line on each one.</h1>
  <p class="lede">We reverse-engineered OLBG's per-sport fixture listings, kept only the sports in scope,
  then originated our own money line, handicap and total for every fixture, rated each pick
  low / medium / high, and wrote verified long-form predictions for the high-confidence calls.
  Every row links to the page it came from. Anything we could not confirm is blank and published on
  <a href="flagged.html">Flagged for review</a>.</p>
</section>

<section class="stats">
  {stat(len(matches), 'fixtures in scope', f'{len(sports)} sports')}
  {stat(with_price, 'fixtures with our own price', 'money line, both sides')}
  {stat(with_hc, 'with a handicap line', f'{with_total} with a total line')}
  {stat(len(preds), 'high-confidence predictions', 'verified sources only')}
  {stat(len(flagged), 'items flagged', 'see register')}
</section>

<section class="grid2">
  <div class="card">
    <h2>High-confidence picks (-250 to +10000 odds window)</h2>
    <p class="muted">Every high-confidence call sits strictly inside <strong>-250 to +10000 American odds (1.40–101.00 decimal, &lt;70% win prob.)</strong> — trivial heavy moneyline chalk (&gt;70%) is capped at medium — and carries a unique &ge;30-word human prediction backed by official governing-body sources.</p>
    <table class="tbl compact">
      <thead><tr><th>Sport</th><th>Match</th><th>Our pick</th><th>Price (US)</th><th>Conf.</th><th>Source</th></tr></thead>
      <tbody>{high_table}</tbody>
    </table>
    <p><a class="btn" href="predictions.html">Read all {len(preds)} predictions →</a></p>
  </div>
  <div class="card">
    <h2>Confidence split</h2>
    <p class="muted">High requires a verified prediction. Medium means a lopsided split on at least five tips. Everything else is low on purpose — a 100% figure built on one tip is not evidence.</p>
    {confidence_bar(counts_all)}
    <ul class="legend">
      <li><span class="dot dot-high"></span> High: {counts_all['high']}</li>
      <li><span class="dot dot-medium"></span> Medium: {counts_all['medium']}</li>
      <li><span class="dot dot-low"></span> Low: {counts_all['low']}</li>
    </ul>
    <hr>
    <h3>What is verified</h3>
    <p class="muted">{verified_comp} of {len(matches)} fixtures have a competition name confirmed from an official or primary source.
    The rest are left blank rather than guessed — OLBG's listing does not name the competition for most domestic fixtures.</p>
  </div>
</section>

<section class="card">
  <h2>Coverage by sport</h2>
  <p class="muted">Only sports inside the brief are here. Soccer/football, American football, boxing/UFC/MMA, hurling, horse racing and cycling were seen on OLBG and deliberately excluded — the evidence is in <a href="methodology.html#exclusions">Method &amp; sources</a>.</p>
  <table class="tbl sortable">
    <thead><tr><th>Sport</th><th class="num">Fixtures</th><th class="num">High</th><th class="num">Medium</th><th class="num">Low</th><th>Split</th><th class="num">Competition verified</th></tr></thead>
    <tbody>{''.join(sport_rows)}</tbody>
  </table>
</section>

<section class="card">
  <h2>Flagged for review</h2>
  <p class="muted">{len(flagged)} items need a human eye: unlabelled timezones, two conflicting dates for one golf tournament, missing competition names, truncated rows, and the Gaelic football inclusion question. Nothing here blocks publication.</p>
  <table class="tbl compact">
    <thead><tr><th>ID</th><th>Severity</th><th>Item</th></tr></thead>
    <tbody>{flag_rows}</tbody>
  </table>
  <p><a class="btn" href="flagged.html">Open the register →</a></p>
</section>
"""

    # ---------- picks ----------
    pick_body_rows = []
    for m in matches:
        l = lines[m["id"]]
        pick_body_rows.append(f"""<tr>
<td>{E(m['sport'])}</td>
<td><strong>{E(m['event_name'])}</strong><br><span class="muted small">{E((m['competition'] or 'competition not stated'))} · {E(l['start'])}</span></td>
<td class="pick">{E(l['our_pick'] or '—')}</td>
<td class="num">{'' if l['our_price_pick'] is None else f"{l['our_price_pick']} ({l.get('our_us_odds_pick','')})"}</td>
<td class="num">{'' if l['our_pick_probability'] is None else f"{l['our_pick_probability']*100:.1f}%"}</td>
<td class="num">{'—' if l['our_handicap_line'] is None else f"{l['our_handicap_side']} {l['our_handicap_line']:+g} {l['our_handicap_unit']}"}</td>
<td class="num">{'—' if l['our_total_line'] is None else f"{(l.get('our_total_side') or '') + ' ' if l.get('our_total_side') else ''}{l['our_total_line']} {l['our_total_unit']}"}</td>
<td>{conf_badge(l['confidence'])}</td>
<td class="src">{sources_cell(m, vmap)}</td>
</tr>""")

    picks_body = f"""
<section class="hero small">
  <h1>Our lines and picks</h1>
  <p class="lede">Every fixture in scope, with the price we would put up, our handicap and total, and the confidence label.
  Prob. is our model probability of our pick; predictions cannot raise or floor it, and HIGH requires strictly above 70%. Prices are ours (5% theoretical hold).
  <a href="methodology.html#model">How the numbers are made →</a></p>
  <div class="tools">
    <input id="q" type="search" placeholder="Filter by team, player, sport or competition…" aria-label="Filter rows">
    <select id="conf" aria-label="Filter by confidence">
      <option value="">All confidence levels</option>
      <option value="high">High only</option>
      <option value="medium">Medium only</option>
      <option value="low">Low only</option>
    </select>
    <span id="count" class="muted small"></span>
  </div>
</section>
<section class="card">
  <table class="tbl sortable filterable" id="picktable">
    <thead><tr><th>Sport</th><th>Fixture</th><th>Our pick</th><th class="num">Price</th><th class="num">Prob.</th><th class="num">Handicap</th><th class="num">Total</th><th>Conf.</th><th>Sources</th></tr></thead>
    <tbody>{''.join(pick_body_rows)}</tbody>
  </table>
</section>
"""

    # ---------- predictions ----------
    live_preds = [p for p in preds if p.get("status", "high") == "high"]
    archived_preds = [p for p in preds if p.get("status", "high") == "analysis"]
    pred_cards = []
    for p in live_preds:
        l = lines[p["match_id"]]
        srcs = "".join(f"<li>{link(s['url'], s['label'])}</li>" for s in p["sources"])
        wc = len(p["text"].split())
        pred_cards.append(f"""
<article class="card pred">
  <div class="pred-head">
    <div><span class="tag">{E(p['sport'])}</span> {conf_badge('high')}</div>
    <h2>{E(p['match'])}</h2>
  </div>
  <p class="selection">Selection: <strong>{E(p['selection'])}</strong> · our price {l['our_price_pick']} ({E(l.get('our_us_odds_pick') or '')}) · model probability {l['our_pick_probability']*100:.1f}%</p>
  <p class="predtext">{E(p['text'])}</p>
  <p class="muted small">{wc} words · start {E(l['start'])} · OLBG source {link(l['olbg_url'], 'fixture listing')}</p>
  <h3>The facts in this prediction, and where they come from</h3>
  <ul class="srclist">{srcs}</ul>
</article>""")

    archived_cards = []
    for p in archived_preds:
        l = lines[p["match_id"]]
        srcs = "".join(f"<li>{link(s['url'], s['label'])}</li>" for s in p["sources"])
        wc = len(p["text"].split())
        archived_cards.append(f"""
<article class="card pred archived">
  <div class="pred-head">
    <div><span class="tag">{E(p['sport'])}</span> {conf_badge(l['confidence'])} <span class="tag">analysis</span></div>
    <h2>{E(p['match'])}</h2>
  </div>
  <p class="selection">Selection: <strong>{E(p['selection'])}</strong> · our price {l['our_price_pick']} ({E(l.get('our_us_odds_pick') or '')}) · model probability {(l['our_pick_probability'] or 0)*100:.1f}%</p>
  <p class="muted small"><strong>Why this is not a live high-confidence pick:</strong> {E(p.get('archive_reason') or 'the row is graded ' + l['confidence'] + '.')}</p>
  <p class="predtext">{E(p['text'])}</p>
  <p class="muted small">{wc} words · start {E(l['start'])} · OLBG source {link(l['olbg_url'], 'fixture listing')}</p>
  <h3>The facts in this prediction, and where they come from</h3>
  <ul class="srclist">{srcs}</ul>
</article>""")

    preds_body = f"""
<section class="hero small">
  <h1>High-confidence predictions</h1>
  <p class="lede">{len(live_preds)} live fixtures qualified. A prediction is written only when form, recent results and the fixture itself
  could be confirmed from an official or primary source, and only while the fixture's official or derived start is still ahead.
  Everything else is capped at low or medium, because we will not write a "current form" sentence we cannot source
  and we will not present a played fixture as a live tip.</p>
</section>
{''.join(pred_cards)}
{('<section class="hero small"><h2>Archived analysis</h2><p class="lede">'
  + str(len(archived_preds)) + ' pieces are kept for the record because their fixture has already kicked off. They are '
  + 'labelled analysis, never high confidence, and they carry the reason they were withdrawn.</p></section>'
  + ''.join(archived_cards)) if archived_cards else ''}
"""

    # ---------- all matches ----------
    match_rows = []
    for m in matches:
        comp = E(m["competition"]) if m["competition"] else '<span class="unver" title="OLBG does not state the competition on this listing">not stated</span>'
        match_rows.append(f"""<tr>
<td>{E(m['sport'])}</td>
<td>{E(match_date(m))}<br><span class="muted small">OLBG: {E(m['olbg_date_label'])} {E(m['olbg_time_label'])}</span></td>
<td><strong>{E(m['event_name'])}</strong></td>
<td>{comp}</td>
<td>{E(m['olbg_market'] or '—')}</td>
<td class="pick">{E(m['olbg_consensus_selection'] or '—')}</td>
<td class="num">{E(m['olbg_tips'] or '—')}</td>
<td class="num">{'' if m['olbg_confidence_pct'] is None else str(m['olbg_confidence_pct']) + '%'}</td>
<td class="src">{sources_cell(m, vmap)}</td>
</tr>""")

    matches_body = f"""
<section class="hero small">
  <h1>All matches (OLBG as published)</h1>
  <p class="lede">This is the reverse-engineered layer: exactly what OLBG published, with no value added or inferred.
  Dates are the OLBG labels resolved against the harvest date where possible; the raw label is kept underneath because
  OLBG does not state a timezone. Every row links to its OLBG page.</p>
  <div class="tools">
    <input id="q" type="search" placeholder="Filter by team, player, sport or competition…" aria-label="Filter rows">
    <span id="count" class="muted small"></span>
  </div>
</section>
<section class="card">
  <table class="tbl sortable filterable" id="matchtable">
    <thead><tr><th>Sport</th><th>Date</th><th>Fixture</th><th>Competition</th><th>OLBG market</th><th>OLBG consensus</th><th class="num">Tips</th><th class="num">OLBG %</th><th>Source</th></tr></thead>
    <tbody>{''.join(match_rows)}</tbody>
  </table>
</section>
"""

    # ---------- flagged ----------
    flag_cards = []
    for f in flagged:
        srcs = "".join(f"<li>{link(s['url'], s['label'])}</li>" for s in f.get("sources", []))
        rows = ", ".join(f["affected_rows"]) if f.get("affected_rows") else "—"
        flag_cards.append(f"""
<article class="card flag" id="{E(f['id'])}">
  <div class="flag-head"><span class="tag">{E(f['id'])}</span> <span class="sev sev-{E(f['severity'].split()[0])}">{E(f['severity'])}</span></div>
  <h2>{E(f['title'])}</h2>
  <p>{E(f['detail'])}</p>
  <p class="muted small">Affected rows: {E(rows)}</p>
  <ul class="srclist">{srcs}</ul>
</article>""")

    flagged_body = f"""
<section class="hero small">
  <h1>Flagged for review</h1>
  <p class="lede">{len(flagged)} items. These are the places where the source disagreed with itself, where an official source reports
  two different values, where OLBG left something out, or where the brief is ambiguous. Nothing here blocks publication —
  each item is published with its sources so you can decide what to change.</p>
</section>
{''.join(flag_cards)}
"""

    # ---------- methodology ----------
    excl = "".join(
        f"<tr><td><strong>{E(x['exclusion'])}</strong></td><td>{E(str(x.get('olbg_sport') or '—'))}</td><td class='num'>{len(x.get('rows_observed', []))}</td><td>{E(x.get('note') or (', '.join(r['event'] for r in x.get('rows_observed', [])) or '—'))}</td></tr>"
        for x in load("excluded.json", {}).get("excluded_sports", [])
    )
    src_table = "".join(
        f"<tr><td>{E(s['id'])}</td><td>{link(s['url'], s['name'])}</td><td>{E(s['class'])}</td></tr>"
        for s in ver.get("sources", [])
    )
    ev_table = "".join(
        f"<tr><td>{E(k)}</td><td>{E(v.get('competition') or '—')}</td><td>{E(v.get('venue') or '—')}</td>"
        f"<td>{E(v.get('start_local') or '—')}</td><td>{E(v.get('status'))}</td>"
        f"<td>{', '.join(link(vmap[x]['url'], x) for x in v.get('sources', []) if x in vmap)}</td></tr>"
        for k, v in ver.get("event_verifications", {}).items()
    )

    method_body = f"""
<section class="hero small">
  <h1>Method, model and sources</h1>
  <p class="lede">Three layers: what OLBG published, what an official source confirmed, and what our model produced.
  They are kept apart on purpose so you can audit any single number.</p>
</section>

<section class="card" id="model">
  <h2>1 · Our line model</h2>
  <p>For each fixture where OLBG's most-tipped market is a winner market we take the tip split, shrink it with a
  Beta(2,2) prior of strength four, then apply a sport-specific home-field shift in logit space. Small samples are
  pulled toward even money, so a 1/1 split becomes 60% rather than 100%. Prices are <code>1 / (p × 1.05)</code>.</p>
  <p>Handicaps come from <code>−Φ⁻¹(p) × σ<sub>sport</sub></code> rounded to the nearest half point, where σ is our assumed
  margin dispersion (basketball 11.5 points, ice hockey 1.8 goals, snooker 2.3 frames, and so on). Totals are anchored to a
  per-sport baseline, not to per-match scoring data — we could not verify pace, weather or injuries fixture by fixture.</p>
  <p><strong>These are our own lines, as requested. They are not bookmaker prices and no bookmaker price is copied.</strong>
  The full parameter tables are in <code>data/model.md</code> in the repository, and
  <code>tools/originate.py</code> reproduces every number.</p>
  <h3>Confidence ladder</h3>
  <ul>
    <li><strong>High</strong> — the fixture has a written prediction backed by official/primary sources for form and results.</li>
    <li><strong>Medium</strong> — winner market, at least five tips, and our probability is at least 0.08 from even money.</li>
    <li><strong>Low</strong> — small samples, rows where OLBG's market was not the winner market, or outrights with no field size.</li>
  </ul>
</section>

<section class="card" id="verification">
  <h2>2 · Verification rule</h2>
  <p>A value is written only when the linked source states it. If a source is silent, the field is blank and the row is flagged.
  Competition names are the clearest example: OLBG's rugby union, volleyball, handball and tennis listings do not name the
  competition, so {len(matches) - verified_comp} of {len(matches)} rows show "not stated" instead of a guessed league.</p>
  <h3>Event-level verification</h3>
  <table class="tbl compact sortable">
    <thead><tr><th>OLBG event id</th><th>Competition</th><th>Venue</th><th>Verified start</th><th>Status</th><th>Sources</th></tr></thead>
    <tbody>{ev_table}</tbody>
  </table>
</section>

<section class="card" id="exclusions">
  <h2>3 · Exclusions, and the evidence for them</h2>
  <p>The brief excludes soccer, boxing, UFC, MMA, football, American football, hurling, horse racing, cycling and specials.
  Each excluded sport was located on OLBG first, so this is an evidence trail rather than a silent omission.</p>
  <table class="tbl compact sortable">
    <thead><tr><th>Excluded</th><th>OLBG sport</th><th class="num">Rows seen</th><th>Notes / examples</th></tr></thead>
    <tbody>{excl}</tbody>
  </table>
  <p class="notice"><strong>One judgement call:</strong> Gaelic football is not named in the exclusion list. It is a different sport from
  association football and from hurling, so it is included and every Gaelic row is tagged so the block can be deleted in one step.
  Flagged as FL-001.</p>
</section>

<section class="card">
  <h2>4 · Source register</h2>
  <p class="muted">Every source used anywhere in this project. "Official" means the governing body, league or operator; "primary" means the
  official draw/schedule page; "secondary" is used only to corroborate.</p>
  <table class="tbl compact sortable">
    <thead><tr><th>ID</th><th>Source</th><th>Class</th></tr></thead>
    <tbody>{src_table}</tbody>
  </table>
</section>

<section class="card">
  <h2>5 · Reproducing this</h2>
  <pre><code>python3 tools/build_dataset.py   # raw TSV + verifications -> data/matches.json
python3 tools/originate.py       # matches -> data/lines.json
python3 tools/build_site.py      # data + lines -> docs/
python3 tools/check_site.py      # link + integrity checks (CI runs this)</code></pre>
  <p class="muted">Run metadata: harvest completed {E(meta.get('harvest_completed_utc',''))}. Method note: the sandbox HTTP client cannot reach
  olbg.com directly (SSL_ERROR_SYSCALL), so pages were retrieved with the agent's page-retrieval tool and transcribed with timestamps.</p>
</section>
"""

    # ---------- write ----------
    DOCS.mkdir(exist_ok=True)
    # drop pages from earlier harvests (e.g. a sport that has since left the scope) so the
    # published tree never contradicts the current dataset
    if (DOCS / "sports").exists():
        shutil.rmtree(DOCS / "sports")
    (DOCS / "sports").mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("")

    (DOCS / "index.html").write_text(page("Dashboard", index_body, "index.html", 0))
    (DOCS / "picks.html").write_text(page("Lines & picks", picks_body, "picks.html", 0))
    (DOCS / "predictions.html").write_text(page("Predictions", preds_body, "predictions.html", 0))
    (DOCS / "matches.html").write_text(page("All matches", matches_body, "matches.html", 0))
    (DOCS / "flagged.html").write_text(page("Flagged for review", flagged_body, "flagged.html", 0))
    (DOCS / "methodology.html").write_text(page("Method & sources", method_body, "methodology.html", 0))

    # ---------- per sport ----------
    for s in sports:
        rows = [m for m in matches if m["sport"] == s]
        c = {"high": 0, "medium": 0, "low": 0}
        for m in rows:
            c[lines[m["id"]]["confidence"]] += 1
        body_rows = []
        for m in rows:
            l = lines[m["id"]]
            body_rows.append(f"""<tr>
<td>{E(match_date(m))}<br><span class="muted small">OLBG: {E(m['olbg_date_label'])} {E(m['olbg_time_label'])}</span></td>
<td><strong>{E(m['event_name'])}</strong><br><span class="muted small">{E(m['competition'] or 'competition not stated')}</span></td>
<td class="pick">{E(l['our_pick'] or '—')}</td>
<td class="num">{'' if l['our_price_pick'] is None else l['our_price_pick']}</td>
<td class="num">{'—' if l['our_handicap_line'] is None else f"{l['our_handicap_line']:+g} {l['our_handicap_unit']}"}</td>
<td class="num">{'—' if l['our_total_line'] is None else l['our_total_line']}</td>
<td>{conf_badge(l['confidence'])}</td>
<td class="src">{sources_cell(m, vmap)}</td>
</tr>""")
        slug = SPORT_SLUG[s]
        n_verified = sum(1 for m in rows if m["competition_status"] == "verified")
        body = f"""
<section class="hero small">
  <p class="crumb"><a href="../index.html">Dashboard</a> / {E(s)}</p>
  <h1>{SPORT_ICON.get(s,'•')} {E(s)}</h1>
  <p class="lede">{len(rows)} fixtures captured from {link('https://www.olbg.com/betting-tips/' + s.replace(' ','_') + '/' + str(rows[0]['olbg_sport_id']), 'OLBG ' + s + ' tips')}.
  {n_verified} of {len(rows)} have a competition name confirmed from an official or primary source; the rest are left blank rather than inferred.</p>
</section>
<section class="stats">
  {stat(len(rows), 'fixtures')}
  {stat(c['high'], 'high confidence')}
  {stat(c['medium'], 'medium confidence')}
  {stat(c['low'], 'low confidence')}
  {stat(sum(1 for m in rows if lines[m['id']]['our_price_pick']), 'with our price')}
</section>
<section class="card">
  {confidence_bar(c)}
  <table class="tbl sortable filterable" id="matchtable">
    <thead><tr><th>Date</th><th>Fixture</th><th>Our pick</th><th class="num">Price</th><th class="num">Handicap</th><th class="num">Total</th><th>Conf.</th><th>Sources</th></tr></thead>
    <tbody>{''.join(body_rows)}</tbody>
  </table>
</section>"""
        (DOCS / "sports" / f"{slug}.html").write_text(page(s, body, "", 1, subtitle=f"Sport · {s}"))

    print(f"site built: {len(sports)+6} pages")

    # The live site is served twice: by the Actions artifact (site/) and by the legacy
    # Pages publisher, which serves the repository root. Both must carry the same bytes,
    # so this track is mirrored to the root as well (documented in COORDINATION.md).
    if SNAPSHOT.exists():
        shutil.rmtree(SNAPSHOT)
    shutil.copytree(DOCS, SNAPSHOT)


RUN = {"harvest_completed_utc": ""}


if __name__ == "__main__":
    RUN["harvest_completed_utc"] = json.loads((DATA / "meta.json").read_text())["harvest_completed_utc"]
    main()
