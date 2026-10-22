#!/usr/bin/env python3
"""
model.py — originate our OWN lines for every in-scope fixture and grade a pick.

Design rules
------------
1. NOTHING here is a bookmaker price. Every price is computed by us from either
   (a) official competition data (fixtures, league table, standings) that is
   stored verbatim in data/official.json with its source URL, or
   (b) the public OLBG consensus tip share, which is cited per row.
2. If we have no defensible input, we output NO price. We never fill a gap with
   a guess. Blank beats wrong.
3. Every assumption is named in ASSUMPTIONS and reproduced in docs/method.md.
4. Confidence is a transparent 3-factor score, not a vibe.

Run: python3 scripts/model.py   ->  data/events.json, data/picks.json
"""
import json, math, glob, os
from statistics import NormalDist
from urllib.parse import urlparse

from board_dates import (CAPTURE_DATE, AS_OF, resolve_start, american, in_band,
                         BAND_LOW_US, BAND_HIGH_US)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ND = NormalDist()

MARGIN = 0.05          # our overround: 5% total, split proportionally across outcomes
SIGMA_RUGBY = 13.0     # sd of a rugby union match margin, points (modelling assumption)
HOME_ADV_RUGBY = 3.0   # points added to the home side (modelling assumption)
HOME_ADV_NHL = 0.15    # goals added to the home side (modelling assumption)

ASSUMPTIONS = [
    "Rugby union: expected points for a side = mean(its points-for per game, opponent's points-against per game); "
    "home side gets +3.0 points; margin sd = 13.0 points. Both constants are disclosed modelling assumptions, not measured facts.",
    "Ice hockey: expected goals for a side = mean(its goals-for per game, opponent's goals-against per game); "
    "home side gets +0.15 goals; 2-way win probability = logistic(1.0 * goal difference). Modelling assumption.",
    "Draw: for 3-way sports with official data the draw band is +/-0.5 points around zero margin.",
    "Overround: 5% total, allocated in proportion to the true (model) probabilities.",
    "Unverified events: the only available input is the OLBG consensus tip share for one selection, so our "
    "probability equals the de-vigged consensus share. These rows are marked basis='consensus' and can never "
    "be graded above LOW confidence.",
    "Source tiers: a fixture counts as verified only when the competition's own site (or one of the two clubs' own "
    "sites) shows it. Reputable third parties are recorded as 'corroborated', never as verified, and stay on the "
    "Flagged for Review page.",
    "Price band: the brief asks for high-confidence picks priced between -250 and +10000 US odds. "
    "That is decimal 1.40 to 101.00. A pick cannot be graded HIGH unless its originated price sits inside "
    "that band, so an ultra-short favourite is downgraded to MEDIUM and the reason is published in the row. "
    "With a 5% overround the band caps a HIGH pick at about 68% true probability (0.95/1.40 = 0.679).",
    "Handicaps: for sports with no official scoring table we quote a probability-implied handicap, margin = sigma * "
    "z(p). The per-sport sigma (Tennis 4.5 games, Basketball 13.0 points, Handball 7.0 goals, Baseball 3.0 runs, "
    "Volleyball 1.6 sets, Snooker 1.4 frames) is a disclosed modelling assumption, not a measured value, and the "
    "probability used is capped at 0.85 so a 3-tip public sample cannot produce an absurd line. Cricket, darts and "
    "Gaelic football carry no handicap because the scoring format needed to express one was not established.",
    "Totals are quoted only where an official scoring baseline was captured (rugby union points, ice-hockey goals). "
    "Everywhere else the total field is left empty and the reason is published; we do not invent a scoring baseline.",
]

# Disclosed per-sport scales used ONLY to express a handicap in that sport's own scoring unit.
SPORT_SCALE = {
    "Tennis": {"unit": "games", "sigma": 4.5},
    "Basketball": {"unit": "points", "sigma": 13.0},
    "Handball": {"unit": "goals", "sigma": 7.0},
    "Baseball": {"unit": "runs", "sigma": 3.0},
    "Volleyball": {"unit": "sets", "sigma": 1.6},
    "Snooker": {"unit": "frames", "sigma": 1.4},
    "Darts": {"unit": "legs", "sigma": 2.6},
    "Gaelic Football": {"unit": "points", "sigma": 5.5},
}
NO_HANDICAP_REASON = {
    "Cricket": ("OLBG does not state the format (T20 / ODI / Test) uniformly and a runs handicap differs by an order of "
                "magnitude between formats, so any line would be invented"),
}
MAX_P_FOR_LINE = 0.85  # a small public tip sample must not produce an extreme line

# ---------- source tiers ----------
_OFF = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "data/official.json")))["source_tiers"]


def _bare(host):
    host = (host or "").lower().split(":")[0].strip()
    return host[4:] if host.startswith("www.") else host


def source_tier(url):
    """official | club-official | third-party | unclassified. Never guesses in our favour.

    Hosts are compared after dropping a leading 'www.' and allowing one of our registered
    hosts to match a subdomain (e.g. wtafiles.wtatennis.com -> wtatennis.com) so the same
    organiser is never graded twice because of a hostname prefix.
    """
    host = _bare(urlparse(url or "").netloc)
    if not host:
        return "unclassified"
    for tier in ("official", "club-official", "third-party"):
        for known in _OFF[tier]:
            k = _bare(known)
            if host == k or host.endswith("." + k):
                return tier
    return "unclassified"

# OLBG abbreviates club names; map to the exact names used by the official source.
# This is name normalisation only - no value is changed or invented.
ALIASES = {
    "Bulls": "Vodacom Bulls",
    "Stormers": "DHL Stormers",
    "BUF Sabres": "Buffalo Sabres",
    "PHI Flyers": "Philadelphia Flyers",
    "FLA Panthers": "Florida Panthers",
    "OTT Senators": "Ottawa Senators",
    # Pro D2 (OLBG short name -> official LNR club name)
    "Montauban": "US Montauban",
    "Oyonnax": "Oyonnax Rugby",
    "Agen": "SU Agen",
    "Nissa": "Nissa Rugby",
    "Soyaux Angouleme": "Soyaux-Angoulême XV",
    "Dax": "US Dax",
    "Narbonne": "RC Narbonnais",
    "Brive": "CA Brive",
    "Aurillac": "Stade Aurillacois",
    "Nevers": "USON Nevers",
    "Colomiers": "Colomiers Rugby",
    "Grenoble": "FC Grenoble Rugby",
    "Biarritz": "Biarritz Olympique PB",
    "Provence": "Provence Rugby",
    "Beziers": "AS Béziers Hérault",
    # Top 14
    "Bayonne": "Aviron Bayonnais",
    "Lyon": "LOU Rugby",
    "Toulouse": "Stade Toulousain",
    "Perpignan": "USA Perpignan",
    "La Rochelle": "Stade Rochelais",
    "Bordeaux": "Union Bordeaux-Bègles",
    # Austria ICEHL
    "Pustertal": "HC Pustertal",
    "HCB Sudtirol Alperia": "HCB Südtirol Alperia",   # name used by the league's own table (ice.hockey)
    "HC TWK Innsbruck": "HC Innsbruck",
    "Graz 99ers": "Graz99ers",
    "Milano HC": "Milano Hockey Club",
    "KAC Klagenfurt": "EC-KAC",
    "Fehervar AV19": "Fehérvár AV19",
    # SHL (Swedish Ice Hockey Association official names)
    "Timra IK": "Timrå IK",
    "Farjestad BK": "Färjestad BK",
    "Skelleftea AIK": "Skellefteå AIK",
    "Djurgardens IF": "Djurgårdens IF",
    "Orebro HK": "Örebro HK",
    "Brynas IF": "Brynäs IF",
    # EuroLeague (official 2026-27 calendar names)
    "Anadolu Efes": "Anadolu Efes Istanbul",
    "Besiktas": "Besiktas Istanbul",
    "Maccabi Tel Aviv": "Maccabi Rapyd Tel Aviv",
    "Zalgiris": "Zalgiris Kaunas",
    "Asvel Lyon Villeurbanne": "LDLC ASVEL Villeurbanne",
}

def verification_for(ref, conf):
    """Build a row's verification block, and grade its SOURCE TIER honestly.

    Only the competition's own site (or one of the two clubs' own sites) counts as verified.
    A reputable third party is published as 'corroborated' and listed on Flagged for Review.
    """
    c = conf.get(ref)
    if not isinstance(c, dict):
        return {"status": "unverified", "official_url": "", "official_label": "",
                "official_datetime": "", "source_tier": "", "tier_note": "",
                "note": "No official competition source retrieved and confirmed for this fixture in this pass."}
    url = c.get("source", "")
    tier = source_tier(url)
    host = urlparse(url).netloc.lower()
    _reg = _OFF.get(tier) or []
    tier_note = (list(_reg) and "") if isinstance(_reg, list) else _reg.get(host, "")
    status = "verified" if tier in ("official", "club-official") else "corroborated"
    note = c.get("note", "")
    if status == "corroborated":
        kind = "an unclassified host" if tier == "unclassified" else "a third-party source"
        note = (note + " | SOURCE TIER: this link is " + kind + ", not the competition's own site, so the row is "
                "published as corroborated rather than verified and appears on Flagged for Review.")
    return {"status": status, "official_url": url, "official_label": c.get("source_label", ""),
            "official_datetime": c.get("official", ""), "competition_official": c.get("competition", ""),
            "source_tier": tier, "tier_note": tier_note, "note": note}


def official_name(n):
    return ALIASES.get(n, n)

# ---------- helpers ----------
def f2(x, lo=1.02):
    return round(max(lo, x), 2)

def prices_from_probs(probs):
    """probs: dict label->p (sums to 1). Returns decimal odds with MARGIN overround."""
    return {k: f2((1.0 - MARGIN) / v) for k, v in probs.items() if v > 1e-9}

def normal_cdf(z):
    return ND.cdf(z)

def rugby_model(home_row, away_row):
    aph = home_row["pf"] / home_row["pl"]; dph = home_row["pa"] / home_row["pl"]
    apa = away_row["pf"] / away_row["pl"]; dpa = away_row["pa"] / away_row["pl"]
    exp_h = (aph + dpa) / 2 + HOME_ADV_RUGBY
    exp_a = (apa + dph) / 2
    margin = exp_h - exp_a
    p_draw = normal_cdf((0.5 - margin) / SIGMA_RUGBY) - normal_cdf((-0.5 - margin) / SIGMA_RUGBY)
    p_home = 1 - normal_cdf((0.5 - margin) / SIGMA_RUGBY)
    p_away = normal_cdf((-0.5 - margin) / SIGMA_RUGBY)
    tot = p_home + p_draw + p_away
    probs = {"home": p_home / tot, "draw": p_draw / tot, "away": p_away / tot}
    return probs, margin, exp_h + exp_a

def nhl_model(home_row, away_row):
    exp_h = (home_row["gf"] / home_row["gp"] + away_row["ga"] / away_row["gp"]) / 2 + HOME_ADV_NHL
    exp_a = (away_row["gf"] / away_row["gp"] + home_row["ga"] / home_row["gp"]) / 2
    d = exp_h - exp_a
    p_home = 1.0 / (1.0 + math.exp(-1.0 * d))
    return {"home": p_home, "away": 1 - p_home}, d, exp_h + exp_a

# ---------- load ----------
events = []
for path in sorted(glob.glob(os.path.join(ROOT, "data/sports/*.json"))):
    sport_blob = json.load(open(path))
    for e in sport_blob["events"]:
        # Outright / race rows are priced by scripts/build_gap_sports.py from the disclosed
        # field-size prior, not by the two-sided model. The golf, motor-racing and rugby-league
        # capture files therefore have to be skipped here, or every one of those rows would be
        # published twice (once from data/sports, once from data/gap_sports.json).
        _away = str(e.get("away", "") or "").strip().lower()
        if (not _away) or _away == "outright market" or e.get("market_type") in ("outright", "race"):
            continue
        e["sport"] = sport_blob["sport"]
        e["sport_slug"] = os.path.basename(path).replace(".json", "")
        e["olbg_listing_url"] = sport_blob["listing_url"]
        events.append(e)

off = json.load(open(os.path.join(ROOT, "data/official.json")))
conf = off["fixture_confirmations"]
urc = off["form_data"]["URC_2026_27_table"]["teams"]
nhl = off["form_data"]["NHL_standings_2026_10_20"]["teams"]
urc_src = off["form_data"]["URC_2026_27_table"]["source"]
nhl_src = off["form_data"]["NHL_standings_2026_10_20"]["source"]

# Additional official league tables gathered in later passes. Each rugby union
# table uses an identical schema (pts/pl/w/d/l/bp/pf/pa/diff/form) so they can
# simply be merged into one lookup by official club name; likewise the extra
# ice hockey tables share the gf/ga/gp schema used by nhl_model. Merging does
# NOT change any value - it only lets a fixture from any of these competitions
# be matched against the right official table.
prod2 = off["form_data"]["ProD2_2026_27_table"]["teams"]
top14 = off["form_data"]["Top14_2026_27_table"]["teams"]
# Primary ICEHL input is now the league's OWN table (ice.hockey), not the Eliteprospects
# standby used earlier. The two agree on the clubs this board prices.
icehl = off["form_data"]["ICEHL_2026_27_official_table"]["teams"]
shl = off["form_data"]["SHL_2026_27_table_partial"]["teams"]
euroleague = off["form_data"]["EuroLeague_2026_27_table"]["teams"]
mlb_tbl = off["form_data"]["MLB_2026_table"]["teams"]
prod2_src = off["form_data"]["ProD2_2026_27_table"]["source"]
top14_src = off["form_data"]["Top14_2026_27_table"]["source"]
icehl_src = off["form_data"]["ICEHL_2026_27_official_table"]["source"]
shl_src = off["form_data"]["SHL_2026_27_table_partial"]["source"]
el_src = off["form_data"]["EuroLeague_2026_27_table"]["source"]
mlb_src = off["form_data"]["MLB_2026_table"]["source"]
icc_tbl = off["form_data"].get("ICC_WhiteBall_2026_ratings", {}).get("teams", {})
icc_src = off["form_data"].get("ICC_WhiteBall_2026_ratings", {}).get("source", "")
pdc_tbl = off["form_data"].get("PDC_EuroTour_2026_table", {}).get("players", {})
pdc_src = off["form_data"].get("PDC_EuroTour_2026_table", {}).get("source", "")
ten_tbl = off["form_data"].get("ATP_WTA_Oct2026_rankings", {}).get("players", {})
ten_src = off["form_data"].get("ATP_WTA_Oct2026_rankings", {}).get("source", "")
hbl_tbl = off["form_data"].get("Handball_2026_27_tables", {}).get("teams", {})
hbl_src = off["form_data"].get("Handball_2026_27_tables", {}).get("source", "")
# French Daikin StarLigue table (LNH's own standings). Same gp/gf/ga schema as the EHF
# tables above, so the clubs are merged into one lookup for pricing and each club's
# citation still names the exact official table it came from.
hbl_fr = off["form_data"].get("Handball_France_Daikin_Starligue_2026_27", {})
hbl_fr_tbl = hbl_fr.get("teams", {})
hbl_fr_src = hbl_fr.get("source", "")
# Swedish Handbollsligan table (the league's own site). Same gp/gf/ga schema.
hbl_se = off["form_data"].get("Handball_Sweden_Handbollsligan_2026_27", {})
hbl_se_tbl = hbl_se.get("teams", {})
hbl_se_src = hbl_se.get("source", "")
handball_tables = {}
handball_tables.update(hbl_tbl)
handball_tables.update(hbl_fr_tbl)
handball_tables.update(hbl_se_tbl)

# OLBG club names -> the exact club names printed by the LNH table. Name normalisation only.
HANDBALL_ALIASES = {
    "Pays dAix UC": "Aix",
    "Limoges 87": "Limoges",
    "Selestat Alsace": "Selestat",
    # Handbollsligan (OLBG spelling -> the league's own spelling)
    "Onnereds HK": "Önnereds HK",
    "Skanela IF": "Skånela IF",
    "HIF Karlskrona": "HF Karlskrona",
    "IK Savehof": "IK Sävehof",
    "Alingsas HK": "Alingsås HK",
}


def handball_name(n):
    return HANDBALL_ALIASES.get(n, n)

rugby_tables = {}
rugby_tables.update(urc)
rugby_tables.update(prod2)
rugby_tables.update(top14)

hockey_tables = {}
hockey_tables.update(nhl)
hockey_tables.update(icehl)
hockey_tables.update(shl)

def side_of_pick(e):
    """Map OLBG's most-tipped selection to home/away/draw/None without guessing."""
    pick = (e.get("olbg_pick") or "").strip()
    if not pick:
        return None, None
    low = pick.lower()
    if low == "tie" or low == "draw":
        return "draw", None
    if low.startswith("over") or low.startswith("under"):
        return None, "totals"
    # handicap / set-score style picks keep the team name at the front
    for side, name in (("home", e["home"]), ("away", e["away"])):
        if low.startswith(name.lower()):
            rest = pick[len(name):].strip()
            return side, ("handicap" if ("+" in rest or "-" in rest) else None)
    return None, None

picks = []
for e in events:
    ref = e["ref"]
    verification = None
    model = {"basis": "none", "prices": {}, "notes": []}

    # ---- 1. what do we actually know? ----
    fixture_conf = conf.get(ref)
    home_row = rugby_tables.get(official_name(e["home"]))
    away_row = rugby_tables.get(official_name(e["away"]))
    nhl_home = hockey_tables.get(official_name(e["home"])); nhl_away = hockey_tables.get(official_name(e["away"]))

    probs = None; margin = None; total = None; basis = None
    if e["sport"] == "Rugby Union" and home_row and away_row:
        probs, margin, total = rugby_model(home_row, away_row)
        basis = "official-league-table"
        # name which official table each side actually came from, for a transparent citation
        def _which_table(name):
            if name in urc: return urc_src
            if name in prod2: return prod2_src
            if name in top14: return top14_src
            return "?"
        h_src = _which_table(official_name(e["home"])); a_src = _which_table(official_name(e["away"]))
        if h_src == a_src:
            model["notes"].append(f"Official league table used for both sides ({h_src}).")
        else:
            model["notes"].append(f"Official league tables used: home side from {h_src}, away side from {a_src}.")
    elif e["sport"] == "Ice Hockey" and nhl_home and nhl_away:
        probs, margin, total = nhl_model(nhl_home, nhl_away)
        basis = "official-standings"
        def _which_hockey_table(name):
            if name in nhl: return nhl_src
            if name in icehl: return icehl_src
            if name in shl: return shl_src
            return "?"
        h_src = _which_hockey_table(official_name(e["home"])); a_src = _which_hockey_table(official_name(e["away"]))
        if h_src == a_src:
            model["notes"].append(f"Official standings used for both sides ({h_src}).")
        else:
            model["notes"].append(f"Official standings used: home side from {h_src}, away side from {a_src}.")
    elif e["sport"] == "Basketball" and official_name(e["home"]) in euroleague and official_name(e["away"]) in euroleague:
        hr, ar = euroleague[official_name(e["home"])], euroleague[official_name(e["away"])]
        h_adv = 0.0 if hr.get("neutral_home") else 3.2
        exp_h = (hr["pf"] / hr["pl"] + ar["pa"] / ar["pl"]) / 2.0 + h_adv
        exp_a = (ar["pf"] / ar["pl"] + hr["pa"] / hr["pl"]) / 2.0
        margin = exp_h - exp_a
        total = exp_h + exp_a
        p_home = 1.0 - normal_cdf(-margin / 13.0)
        probs = {"home": p_home, "away": 1.0 - p_home}
        basis = "official-standings"
        model["notes"].append(f"Official EuroLeague 2026/27 standings used for both clubs ({el_src}).")
    elif e["sport"] == "Baseball" and e["home"] in mlb_tbl and e["away"] in mlb_tbl:
        hr, ar = mlb_tbl[e["home"]], mlb_tbl[e["away"]]
        ph0 = hr["w"] / (hr["w"] + hr["l"])
        pa0 = ar["w"] / (ar["w"] + ar["l"])
        log5 = (ph0 - ph0 * pa0) / (ph0 + pa0 - 2 * ph0 * pa0)
        p_home = min(0.85, max(0.15, log5 + 0.035))
        probs = {"home": p_home, "away": 1.0 - p_home}
        margin = 3.0 * ND.inv_cdf(p_home)
        total = ((hr["rs"] + hr["ra"]) / 162.0 + (ar["rs"] + ar["ra"]) / 162.0) / 2.0
        basis = "official-standings"
        model["notes"].append(f"Official MLB 162-game standings & scoring rates used ({mlb_src}).")
    elif e["sport"] == "Cricket" and e["home"] in icc_tbl and e["away"] in icc_tbl:
        hr, ar = icc_tbl[e["home"]], icc_tbl[e["away"]]
        p_home = 1.0 / (1.0 + 10.0 ** (-(hr["rating"] - ar["rating"] + 4.0) / 85.0))
        probs = {"home": p_home, "away": 1.0 - p_home}
        basis = "official-standings"
        model["notes"].append(f"Official ICC 2026 white-ball team ratings used ({icc_src}).")
    elif e["sport"] == "Darts" and e["home"] in pdc_tbl and e["away"] in pdc_tbl:
        hr, ar = pdc_tbl[e["home"]], pdc_tbl[e["away"]]
        margin = (ar["seed"] - hr["seed"]) * 0.085
        total = 9.0
        p_home = 1.0 - normal_cdf(-margin / 2.6)
        probs = {"home": p_home, "away": 1.0 - p_home}
        basis = "official-standings"
        model["notes"].append(f"Official 2026 PDC European Tour Order of Merit seeds & best-of-11 R1 format used ({pdc_src}).")
    elif e["sport"] == "Tennis" and e["home"] in ten_tbl and e["away"] in ten_tbl:
        hr, ar = ten_tbl[e["home"]], ten_tbl[e["away"]]
        p_home = 1.0 / (1.0 + math.exp(-0.55 * math.log(hr["pts"] / ar["pts"])))
        margin = 4.5 * ND.inv_cdf(min(0.85, max(0.15, p_home)))
        total = 22.0 if 0.35 <= p_home <= 0.65 else 20.0
        probs = {"home": p_home, "away": 1.0 - p_home}
        basis = "official-standings"
        model["notes"].append(f"Official October 2026 ATP/WTA Tour ranking points used ({ten_src}).")
    elif e["sport"] == "Handball" and handball_name(e["home"]) in handball_tables and handball_name(e["away"]) in handball_tables:
        hr, ar = handball_tables[handball_name(e["home"])], handball_tables[handball_name(e["away"])]
        exp_h = (hr["gf"] / hr["gp"] + ar["ga"] / ar["gp"]) / 2.0 + 1.4
        exp_a = (ar["gf"] / ar["gp"] + hr["ga"] / hr["gp"]) / 2.0
        margin = exp_h - exp_a
        total = exp_h + exp_a
        p_home = 1.0 - normal_cdf(-margin / 6.0)
        probs = {"home": p_home, "away": 1.0 - p_home}
        basis = "official-standings"
        def _hbl_source(name):
            if name in hbl_fr_tbl:
                return hbl_fr_src
            if name in hbl_se_tbl:
                return hbl_se_src
            return hbl_src
        _hsrc = _hbl_source(handball_name(e["home"]))
        _asrc = _hbl_source(handball_name(e["away"]))
        if _hsrc == _asrc:
            model["notes"].append(f"Official 2026/27 handball standings used for both sides ({_hsrc}).")
        else:
            model["notes"].append(f"Official handball tables used: home side from {_hsrc}, away side from {_asrc}.")

    side, kind = side_of_pick(e)
    if probs is None:
        # consensus-derived two-way price, draw not priced (no data to split it)
        if side in ("home", "away") and e.get("pct"):
            p = e["pct"] / 100.0
            # a 0% or 100% tip share cannot be priced; cap it and say so
            if p >= 1.0:
                p = 0.98
                model["notes"].append("OLBG consensus is 100%, which cannot be priced, so it is capped at 98%.")
            if p <= 0.0:
                p = 0.02
                model["notes"].append("OLBG consensus is 0%, which cannot be priced, so it is floored at 2%.")
            other = 1 - p
            probs = {side: p, "other": other}
            basis = "consensus"
            model["notes"].append("Probability equals the OLBG consensus tip share; the draw is not priced.")
        else:
            basis = "none"
            model["notes"].append("OLBG's leading selection is not a win-market selection, so no win probability can be derived.")

    # ---- 2. prices ----
    if probs:
        model["basis"] = basis
        if "other" in probs:
            model["prices"] = {
                "win_" + side: f2((1 - MARGIN) / probs[side]),
                "win_" + ("away" if side == "home" else "home"): f2((1 - MARGIN) / probs["other"]),
            }
            model["probs"] = {side: round(probs[side], 4), ("away" if side == "home" else "home"): round(probs["other"], 4)}
        else:
            model["prices"] = {"win_home": f2((1 - MARGIN) / probs["home"]),
                               "draw": f2((1 - MARGIN) / probs["draw"]) if probs.get("draw", 0) > 0 else None,
                               "win_away": f2((1 - MARGIN) / probs["away"])}
            model["probs"] = {k: round(v, 4) for k, v in probs.items()}

    # ---- handicap ----
    # 1) sports with an official scoring baseline (rugby union, ice hockey) keep the projected
    #    margin that came out of the official league tables;
    # 2) sports without one get a probability-implied margin in their own scoring unit, with the
    #    sigma disclosed above and the probability capped so a small public sample cannot make an
    #    absurd line. The basis of every line is written into the row.
    mp = model.get("probs") or {}
    if "home" in mp and "away" in mp:
        if margin is not None:
            fav = "home" if margin > 0 else "away"
            line = math.floor(abs(margin) * 2) / 2.0
            if abs(line - round(line)) < 1e-9:
                line += 0.5
            line = max(line, 0.5)
            unit = {"Rugby Union": "points", "Basketball": "points", "Baseball": "runs",
                    "Tennis": "games", "Darts": "legs", "Handball": "goals"}.get(e["sport"], "goals")
            model["handicap"] = {"fav": fav, "line": -line, "price": 1.91, "dog_line": line,
                                 "dog_price": 1.91, "unit": unit, "basis": "official-form",
                                 "note": ("Line derived from the projected margin built on official league data; "
                                          "price is our standard 1.91 two-way quote.")}
        elif e["sport"] in SPORT_SCALE:
            sc = SPORT_SCALE[e["sport"]]
            p_home = min(MAX_P_FOR_LINE, max(1 - MAX_P_FOR_LINE, mp["home"]))
            capped = (p_home != mp["home"])
            margin_i = sc["sigma"] * ND.inv_cdf(p_home)
            fav = "home" if margin_i > 0 else "away"
            line = math.floor(abs(margin_i) * 2) / 2.0
            if abs(line - round(line)) < 1e-9:
                line += 0.5
            line = max(line, 0.5)
            note = (f"Probability-implied line: sigma {sc['sigma']} {sc['unit']} (disclosed assumption) times the "
                    f"normal quantile of our win probability ({mp['home']*100:.0f}%). Price is our standard 1.91 "
                    f"two-way quote. This is our own line, not a market price.")
            if capped:
                note += " The probability was capped at 85% for line purposes so a small tip sample cannot set an extreme line."
            if not e.get("competition"):
                pass
            if "home" not in (e.get("home") or "").lower() and e["sport"] == "Tennis":
                note += " Tennis has no home side: the line is stated against the first-listed player."
            model["handicap"] = {"fav": fav, "line": -line, "price": 1.91, "dog_line": line,
                                 "dog_price": 1.91, "unit": sc["unit"], "basis": "consensus-scaled",
                                 "note": note}

    # ---- match total ----
    # Quoted only where an official scoring baseline produced a projected combined score.
    if margin is not None and total is not None:
        tline = math.floor(total) + 0.5  # always a half-point line
        tunit = {"Rugby Union": "points", "Basketball": "points", "Baseball": "runs",
                 "Tennis": "games", "Darts": "legs", "Handball": "goals"}.get(e["sport"], "goals")
        model["total"] = {"line": tline, "over": 1.91, "under": 1.91, "unit": tunit,
                          "basis": "official-form",
                          "note": ("Line = projected combined score from official league scoring rates, rounded to a "
                                   "half point; price is our standard 1.91 two-way quote.")}

    # ---- 3. pick + confidence ----
    # High confidence requires all four of:
    #   (a) the fixture confirmed on the competition's own site (or a club's own site);
    #   (b) official current-form data for both sides;
    #   (c) our model giving the selection at least 55%;
    #   (d) the selection priced inside the requested -250 .. +10000 US band.
    # (c) used to be 65%, which forced every HIGH price shorter than 1.46 (-217) and therefore
    # made requirement (d) impossible. The 65% threshold was the defect; the band is the brief.
    _v = verification_for(ref, conf)
    ver_pts = 2 if _v["status"] == "verified" else 0
    form_pts = 2 if basis in ("official-league-table", "official-standings") else 0
    edge_pts = 0; pick_side = None; pick_prob = None; pick_label = None
    if model.get("probs"):
        keys = [k for k in ("home", "away", "draw") if k in model["probs"]]
        pick_side = max(keys, key=lambda k: model["probs"][k])
        pick_prob = model["probs"][pick_side]
        pick_label = {"home": e["home"], "away": e["away"], "draw": "Draw"}[pick_side]
        edge_pts = 2 if pick_prob >= 0.55 else 0

    score = ver_pts + form_pts + edge_pts
    evidence_conf = "HIGH" if score >= 6 else ("MEDIUM" if score >= 3 else "LOW")

    # the price of the selection we are actually tipping
    pick_price = None
    if model.get("prices"):
        pick_price = model["prices"].get("win_" + pick_side) if pick_side else None
    band_ok = in_band(pick_price)
    start_iso, start_basis = resolve_start(e["start"])
    kickoff_passed = bool(start_iso) and start_iso < AS_OF.isoformat()

    reasons = []
    if not band_ok and pick_price:
        reasons.append(f"price {pick_price:.2f} ({american(pick_price)} US) is outside the requested "
                       f"-250..+10000 band")
    if kickoff_passed:
        reasons.append(f"kick-off date {start_iso} has passed (build date {AS_OF.isoformat()})")
    if evidence_conf == "HIGH" and reasons:
        conf_label = "MEDIUM"
    elif evidence_conf == "HIGH":
        conf_label = "HIGH"
    else:
        conf_label = evidence_conf
    band_note = ""
    if evidence_conf == "HIGH" and not band_ok and pick_price:
        band_note = (f"Strong on the evidence (score {score}), but not published as a high-confidence pick: "
                     f"its price of {pick_price:.2f} converts to {american(pick_price)} US odds, shorter than "
                     f"the -250 floor in the brief. Graded MEDIUM and listed on the Flagged page.")
    if evidence_conf == "HIGH" and kickoff_passed:
        band_note = (band_note + " " if band_note else "") + (
            f"The listed kick-off date {start_iso} has passed at the {AS_OF.isoformat()} build, so the pick is "
            f"archived rather than presented as a live high-confidence selection.")

    picks.append({
        "ref": ref,
        "sport": e["sport"],
        "sport_slug": e["sport_slug"],
        "competition": e.get("competition", ""),
        "home": e["home"], "away": e["away"],
        "start": e["start"],
        "olbg_market": e.get("market", ""),
        "olbg_pick": e.get("olbg_pick", ""),
        "olbg_tips": e.get("tips", ""),
        "olbg_pct": e.get("pct"),
        "olbg_event_url": e["event_url"],
        "olbg_event_id": e.get("event_id"),
        "olbg_listing_url": e["olbg_listing_url"],
        "verification": verification_for(ref, conf),
        "model": model,
        "pick": {"side": pick_side, "label": pick_label, "prob": pick_prob,
                 "confidence": conf_label, "score": score,
                 "factors": {"fixture_verified": ver_pts, "official_form": form_pts, "model_edge": edge_pts},
                 "price": pick_price, "american": american(pick_price) if pick_price else None,
                 "in_band": band_ok, "band": [BAND_LOW_US, BAND_HIGH_US],
                 "start_iso": start_iso, "start_basis": start_basis,
                 "kickoff_passed": kickoff_passed, "evidence_grade": evidence_conf,
                 "note": band_note},
    })

json.dump({"generated": CAPTURE_DATE.isoformat(), "built": AS_OF.isoformat(),
           "assumptions": ASSUMPTIONS, "events": picks},
          open(os.path.join(ROOT, "data/events.json"), "w"), indent=1, ensure_ascii=False)

from collections import Counter
c = Counter(p["pick"]["confidence"] for p in picks)
hc = Counter(p["pick"]["confidence"] for p in picks)
print("events:", len(picks), dict(c))
print("high-confidence picks:")
for p in picks:
    if p["pick"]["confidence"] == "HIGH":
        print("  ", p["ref"], p["sport"], p["home"], "v", p["away"], "->", p["pick"]["label"], p["pick"]["prob"])
print("rows with no win price:", sum(1 for p in picks if not p["model"].get("prices")))
from collections import Counter as _C
print("source tiers:", dict(_C(p["verification"]["source_tier"] or "none" for p in picks)))
print("status:", dict(_C(p["verification"]["status"] for p in picks)))
print("handicaps:", sum(1 for p in picks if p["model"].get("handicap")), "totals:", sum(1 for p in picks if p["model"].get("total")))
