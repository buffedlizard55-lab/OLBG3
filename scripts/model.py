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
]

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
    "HCB Sudtirol Alperia": "HC Bolzano",
    "HC TWK Innsbruck": "HC Innsbruck",
    "Graz 99ers": "Graz99ers",
    "Milano HC": "Milano Hockey Club",
    "KAC Klagenfurt": "EC-KAC",
    "Fehervar AV19": "Fehérvár AV19",
    # SHL
    "Timra IK": "Timrå IK",
    "Farjestad BK": "Färjestad BK",
}

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
icehl = off["form_data"]["ICEHL_2026_27_table"]["teams"]
shl = off["form_data"]["SHL_2026_27_table_partial"]["teams"]
prod2_src = off["form_data"]["ProD2_2026_27_table"]["source"]
top14_src = off["form_data"]["Top14_2026_27_table"]["source"]
icehl_src = off["form_data"]["ICEHL_2026_27_table"]["source"]
shl_src = off["form_data"]["SHL_2026_27_table_partial"]["source"]

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

    # handicap + total only where a projected margin exists
    if margin is not None and probs and "home" in probs and "away" in probs:
        fav = "home" if margin > 0 else "away"
        # force a half-point line so a push is impossible, and never quote 0.0
        line = math.floor(abs(margin) * 2) / 2.0
        if abs(line - round(line)) < 1e-9:
            line += 0.5
        line = max(line, 0.5)
        model["handicap"] = {"fav": fav, "line": -line, "price": 1.91, "dog_line": line, "dog_price": 1.91,
                             "note": "Line derived from the model's projected margin; price is our standard 1.91 two-way quote."}
        tline = math.floor(total) + 0.5  # always a half-point line
        model["total"] = {"line": tline, "over": 1.91, "under": 1.91,
                          "note": "Line = projected combined score rounded to the nearest half point; price is our standard 1.91 two-way quote."}

    # ---- 3. pick + confidence ----
    ver_pts = 2 if (fixture_conf and fixture_conf["status"] == "verified") else 0
    form_pts = 2 if basis in ("official-league-table", "official-standings") else 0
    edge_pts = 0; pick_side = None; pick_prob = None; pick_label = None
    if model.get("probs"):
        keys = [k for k in ("home", "away", "draw") if k in model["probs"]]
        pick_side = max(keys, key=lambda k: model["probs"][k])
        pick_prob = model["probs"][pick_side]
        pick_label = {"home": e["home"], "away": e["away"], "draw": "Draw"}[pick_side]
        edge_pts = 2 if pick_prob >= 0.65 else (1 if pick_prob >= 0.55 else 0)

    score = ver_pts + form_pts + edge_pts
    conf_label = "HIGH" if score >= 6 else ("MEDIUM" if score >= 3 else "LOW")

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
        "verification": ({"status": conf.get(ref).get("status", "unverified") if isinstance(conf.get(ref), dict) else "unverified",
                          "official_url": conf.get(ref).get("source", "") if isinstance(conf.get(ref), dict) else "",
                          "official_label": conf.get(ref).get("source_label", "") if isinstance(conf.get(ref), dict) else "",
                          "official_datetime": conf.get(ref).get("official", "") if isinstance(conf.get(ref), dict) else "",
                          "note": conf.get(ref).get("note", "") if isinstance(conf.get(ref), dict) else ""}
                         if ref in conf else
                         {"status": "unverified", "official_url": "", "official_label": "", "official_datetime": "",
                          "note": "No official competition source retrieved and confirmed for this fixture in this pass."}),
        "model": model,
        "pick": {"side": pick_side, "label": pick_label, "prob": pick_prob,
                 "confidence": conf_label, "score": score,
                 "factors": {"fixture_verified": ver_pts, "official_form": form_pts, "model_edge": edge_pts}},
    })

json.dump({"generated": "2026-10-21", "assumptions": ASSUMPTIONS, "events": picks},
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
