#!/usr/bin/env python3
"""Originate independent multi-market lines (Win / Money Line, Handicap / Spread, Totals, Outrights)
for every fixture in data/matches.json, grade confidence (low / medium / high) strictly focusing HIGH
confidence on verified edges inside the -250 to +10000 American odds window (1.40 to 101.00 decimal),
and emit data/lines.json.

Every parameter, official rating input, and formula is documented in data/model.md.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

MARGIN = 0.05  # 5% theoretical bookmaker hold on two-way / outright markets
PRICE_MIN_HIGH = 1.40    # -250 American odds exact decimal floor (1 + 100/250)
PRICE_MAX_HIGH = 101.00  # +10000 American odds exact decimal ceiling (1 + 10000/100)
PROB_MAX_HIGH = 0.70     # Strictly exclude >70% heavy chalk from HIGH confidence
# Single source of truth for the expiry clock: scripts/board_dates.py reads real UTC today and
# honours OLBG_AS_OF so an archived build can be reproduced. Never hard-code the date here, or the
# clock freezes and yesterday's fixtures keep grading HIGH forever.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from release import apply_lines, sync_predictions
from board_dates import build_date  # noqa: E402

BUILD_DATE = build_date()

HOME_LOGIT = {
    "Basketball": 0.14,
    "Baseball": 0.08,
    "Ice Hockey": 0.10,
    "Rugby Union": 0.22,
    "Rugby League": 0.18,
    "Handball": 0.18,
    "Volleyball": 0.14,
    "Gaelic Football": 0.10,
    "Cricket": 0.06,
    "Tennis": 0.0,
    "Darts": 0.0,
    "Snooker": 0.0,
}

SPREAD_CFG = {
    "Basketball": (11.5, "pts"),
    "Rugby Union": (14.5, "pts"),
    "Rugby League": (12.5, "pts"),
    "Handball": (4.5, "goals"),
    "Tennis": (4.2, "games"),
    "Darts": (2.6, "legs"),
    "Baseball": (2.8, "runs"),
    "Ice Hockey": (2.1, "goals"),
    "Volleyball": (1.5, "sets"),
    "Gaelic Football": (5.5, "pts"),
    "Snooker": (2.0, "frames"),
}

TOTAL_CFG = {
    "Basketball": (228.5, "pts", "league scoring pace baseline (NBA 228.5, EuroLeague 169.5, domestic 163.5)"),
    "Baseball": (7.5, "runs", "MLB postseason run-scoring environment baseline"),
    "Ice Hockey": (5.5, "goals", "league goals-per-game baseline (SHL / Liiga / NHL)"),
    "Handball": (60.5, "goals", "EHF Champions League 60.82 goals/game & HBL 60.0 baseline"),
    "Rugby Union": (48.5, "pts", "URC 48.9 / Top 14 49.7 / Pro D2 empirical scoring baseline"),
    "Tennis": (22.5, "games", "ATP/WTA 3-set hard-court total games baseline"),
    "Darts": (9.5, "legs", "PDC European Championship Round 1 best-of-11 legs baseline"),
    "Cricket": (345.5, "runs", "international white-ball match aggregate runs baseline"),
    "Volleyball": (182.5, "pts", "European top-flight match total points baseline"),
    "Snooker": (6.5, "frames", "WST Home Nations best-of-7 frames baseline"),
}

# Manually specified strength and total priors, informed by cited sporting facts.
# Probabilities, totals, side preferences and field sizes below are MODELLING ASSUMPTIONS,
# not values verified by a governing body and not fitted/calibrated model coefficients.
# Tuple format: (pick_name, assumed_fair_prob, assumed_total, assumed_side, context_note)
EDITORIAL_STRENGTH = {
    # Baseball — MLB World Series Game 1 (mlb.com standings: MIL 103-59, 55-26 home, +214 diff vs TB 98-64, +110 diff)
    "BSB-160789": ("MIL Brewers", 0.586, 6.5, "Over", "MLB official 2026 standings (MIL 103-59, .679 home vs TB 98-64) + OLBG 12/15 ML, 8/8 Over 6.5"),
    # Basketball — NBA & EuroLeague (nba.com game notes + euroleaguebasketball.net Round 7 tables)
    "BKB-534839": ("LA Lakers", 0.594, 233.5, "Over", "NBA official game notes (LAL home opener with Doncic vs depleted GSW) + OLBG 11/17 ML, 4/5 Over 233.5"),
    "BKB-535674": ("LA Clippers", 0.642, 226.5, "Under", "NBA official Clippers schedule/preseason form (122-110 vs DEN, 3-1 H2H series vs SAC) + OLBG 10/11 ML, 5/8 Under 226.5"),
    "BKB-534893": ("POR Trail Blazers", 0.556, 227.5, "Over", "NBA official schedule + Moda Center home edge & OLBG 7/12 split"),
    "BKB-534843": ("OKC Thunder", 0.735, 235.5, "Over", "NBA #1 seed OKC home vs DEN (heavy favorite >70% fair prob -> capped at medium; OLBG spread -8.5, total 235.5)"),
    "BKB-534845": ("PHI 76ers", 0.548, 224.5, "Over", "NBA home opener Xfinity Mobile Arena + shrunk prior"),
    "BKB-534841": ("SA Spurs", 0.552, 225.5, "Over", "NBA Friday slate Frost Bank Center + shrunk prior"),
    "BKB-534842": ("BOS Celtics", 0.575, 226.5, "Over", "NBA Friday slate TD Garden (OLBG spread BOS -2.50)"),
    "BKB-535918": ("Anadolu Efes", 0.572, 169.5, "Over", "EuroLeague R7 Istanbul derby: Efes (beat Zalgiris 85-70 away in R6) home vs Besiktas (3-3, beat Bayern 95-87 in R6)"),
    "BKB-535921": ("Real Madrid", 0.585, 172.5, "Over", "EuroLeague R7 neutral Belgrade: Real Madrid (beat Milan 98-89 & ASVEL) vs Maccabi (neutral-court game)"),
    "BKB-535923": ("Panathinaikos", 0.780, 171.5, "Over", "EuroLeague R7 table: #1 Panathinaikos (5-1, +90) vs #20 Baskonia (1-5, -60); >70% chalk on ML -> medium"),
    "BKB-535928": ("Zalgiris", 0.655, 165.5, "Under", "EuroLeague R7 Kaunas: Zalgiris (3-3) home vs #19 ASVEL (1-5, lost to Crvena Zvezda 82-84 & Real Madrid)"),
    # Tennis — ATP 250 Almaty, Brussels, Lyon & WTA Ningbo / Osaka (official ATP/WTA rankings + R1 results)
    "TEN-902110": ("Karen Khachanov", 0.597, 22.5, "Over", "ATP Almaty R16: #5 seed Khachanov (beat Sakamoto 6-2, 6-4) vs Machac + OLBG 3/5"),
    "TEN-902082": ("Alexander Bublik", 0.625, 22.5, "Over", "ATP Almaty R16: #3 seed world #22 Bublik (Shanghai R16) home indoor vs #64 Marozsan (beat Skatov 7-5, 7-6)"),
    "TEN-902069": ("Daniil Medvedev", 0.835, 20.5, "Under", "ATP Almaty R16: #1 seed world #5 Medvedev vs #109 Shimabukuro (>70% heavy chalk -> medium)"),
    "TEN-902104": ("Jiri Lehecka", 0.725, 21.5, "Under", "ATP Brussels R16: #2 seed world #20 Lehecka vs Collignon (>70% chalk -> medium)"),
    "TEN-902120": ("Zizou Bergs", 0.618, 22.5, "Over", "ATP Brussels R16: home #6 seed Zizou Bergs indoors vs #103 Damir Dzumhur"),
    "TEN-902131": ("Alex Michelsen", 0.592, 22.5, "Over", "ATP Brussels R16: #5 seed Alex Michelsen vs WC David Goffin"),
    "TEN-902087": ("Taylor Fritz", 0.765, 21.5, "Under", "ATP Lyon R16: #2 seed world #14 Taylor Fritz vs qualifier #290 Herbert (>70% chalk -> medium)"),
    "TEN-902103": ("Valentin Vacherot", 0.580, 22.5, "Over", "ATP Lyon R16: #3 seed Valentin Vacherot vs Luca Van Assche"),
    "TEN-902100": ("Daniel Altmaier", 0.562, 23.5, "Over", "ATP Lyon R16: #65 Altmaier (2-0 H2H, 19 aces vs Droguet) vs #148 qualifier Gojo (beat #8 seed Fery 6-3, 7-6)"),
    "TEN-902126": ("Flavio Cobolli", 0.640, 22.5, "Over", "ATP Lyon R16: #1 seed Flavio Cobolli vs WC Stan Wawrinka"),
    "TEN-902105": ("Brandon Nakashima", 0.645, 22.5, "Under", "ATP Lyon R16: #5 seed Brandon Nakashima vs qualifier Kyrian Jacquet"),
    "TEN-902109": ("Terence Atmane", 0.525, 23.5, "Over", "ATP Almaty R16: Atmane (beat Hijikata 7-6, 6-2) vs Bellucci coin-flip"),
    "TEN-902063": ("Ann Li", 0.613, 21.5, "Over", "WTA Osaka R16: #1 seed world #25 Ann Li (10 aces in R1 win over Jones) vs #63 Zeynep Sonmez + OLBG 8/10"),
    "TEN-902071": ("Katerina Siniakova", 0.601, 21.5, "Over", "WTA Osaka R16: Siniakova (beat #2 seed Stearns R1 & beat Linette at China Open) vs #77 Linette + OLBG 4/6"),
    "TEN-902072": ("Diana Shnaider", 0.586, 22.5, "Over", "WTA Ningbo R16: #6 seed world #13 Diana Shnaider vs Alexandra Eala + OLBG 3/4"),
    "TEN-902093": ("Belinda Bencic", 0.720, 20.5, "Under", "WTA Ningbo R16: #5 seed world #14 Bencic vs qualifier Kawa (>70% chalk -> medium)"),
    "TEN-902073": ("Elena Rybakina", 0.805, 19.5, "Under", "WTA Ningbo R16: #1 seed world #1 Rybakina (9,196 pts) vs #105 qualifier Kudermetova (>70% chalk -> medium)"),
    "TEN-902075": ("Iva Jovic", 0.565, 22.5, "Over", "WTA Ningbo R16: #4 seed world #12 Iva Jovic vs Jasmine Paolini"),
    "TEN-902067": ("Mary Stoiana", 0.578, 22.5, "Over", "WTA Osaka R16: Stoiana (beat #7 seed Oliynykova 6-2, 6-3) vs Moyuka Uchijima + OLBG 6/9"),
    "TEN-902066": ("Antonia Ruzic", 0.505, 22.5, "Over", "WTA Osaka R16: Ruzic (beat Badosa) vs Day (beat Kenin) + OLBG 3/6 split"),
    # Cricket — ICC / National Board verified white-ball internationals
    "CRI-188814": ("India", 0.646, 352.5, "Over", "ICC T20I rankings & T20 World Cup Final form (India 255/5 vs NZ 159) + OLBG 12/16 (2 experts)"),
    "CRI-188829": ("England", 0.609, 515.5, "Over", "ICC Men's ODI rankings (#6 England vs #7 Sri Lanka in Rawalpindi Tri-Series) + OLBG 8/10"),
    "CRI-188828": ("Ireland", 0.617, 455.5, "Over", "ICC Men's ODI rankings (#12 Ireland led by Paul Stirling vs #16 Namibia in Windhoek) + OLBG 7/11 (2 experts)"),
    "CRI-188826": ("Australia W", 0.730, 310.5, "Over", "Cricket Australia Women's T20I series at North Sydney Oval (>70% favorite -> medium)"),
    "CRI-188831": ("Afghanistan", 0.642, 472.5, "Over", "ICC ODI rankings (#8 Afghanistan 92 rating vs #11 Zimbabwe 64 rating; beat Zimbabwe 294 vs 136 on Oct 19 in UAE)"),
    # Darts — PDC Machineseeker European Championship Dortmund (Best of 11 R1)
    "DAR-32330": ("Danny Noppert", 0.580, 9.5, "Over", "PDC European Championship R1: #5 Noppert (Maastricht finalist Oct 18) vs #28 Bunting (Maastricht SF); OLBG 9/13 ML & 5/5 Over 9.5 legs"),
    "DAR-32334": ("Niels Zonneveld", 0.625, 9.5, "Over", "PDC European Championship R1: #4 Zonneveld (won Dutch Darts Championship Oct 18) vs #29 Menzies + OLBG 11/14"),
    "DAR-32337": ("Luke Humphries", 0.651, 9.5, "Under", "PDC European Championship R1: world #2 Humphries (100.01 Euro Tour avg, 2025 finalist) vs #21 Searle + OLBG 10/13"),
    "DAR-32325": ("Gerwyn Price", 0.601, 9.5, "Over", "PDC European Championship R1: #13 Gerwyn Price (10x Euro Tour winner) vs #20 Rob Cross + OLBG 10/13"),
    "DAR-32323": ("Gian van Veen", 0.621, 9.5, "Over", "PDC European Championship R1: defending champion #8 Gian van Veen (record Euro Tour avg Oct 17) vs #25 Andrew Gilding + OLBG 9/14"),
    "DAR-32324": ("Dirk van Duijvenbode", 0.635, 9.5, "Over", "PDC European Championship R1: Dirk van Duijvenbode vs #9 Luke Woodhouse + OLBG 11/13 (1 expert)"),
    "DAR-32322": ("James Wade", 0.562, 9.5, "Over", "PDC European Championship R1: 2018 champion #16 James Wade vs #17 Damon Heta + OLBG 9/14"),
    "DAR-32329": ("Ross Smith", 0.588, 9.5, "Over", "PDC European Championship R1: #1 Euro Tour seed Ross Smith vs #32 Karel Sedlacek"),
    "DAR-32328": ("Luke Littler", 0.760, 8.5, "Under", "PDC European Championship R1: World Champion #3 Luke Littler vs #22 William O'Connor (>70% chalk -> medium)"),
    # Ice Hockey — Swedish SHL & Finnish Liiga (stats.swehockey.se & liiga.fi tables)
    "ICH-199900": ("Brynas IF", 0.634, 5.5, "Under", "SHL official standings flip: #5 Brynas IF (28:23, +5 GD) at #9 Orebro HK (20:29, -9 GD) — overrides 1/1 crowd pick"),
    "ICH-199901": ("Farjestad BK", 0.660, 5.5, "Under", "SHL official standings: unbeaten #1 Farjestad BK (10 GP, 8-2-0, 40:11, +29 GD) at #10 Timra IK (20:23, 12 pts) + 2/2 experts"),
    "ICH-199905": ("Skelleftea AIK", 0.715, 5.5, "Over", "SHL official standings: #3 Skelleftea AIK (32:25, 19 pts) home vs #12 Djurgardens IF (23:33, 12 pts; >70% chalk -> medium)"),
    "ICH-199912": ("Jyp", 0.585, 5.5, "Over", "Finnish Liiga official table: #8 JYP (12 GP, 24 pts) home vs #9 HPK (14 GP, 21 pts)"),
    # Rugby Union — URC, Pro D2 & Top 14 official tables
    "RGU-609578": ("Leinster", 0.660, 47.5, "Over", "URC Round 6 Irish derby: Leinster home in Dublin vs Munster + official URC table"),
    "RGU-609556": ("Oyonnax", 0.605, 46.5, "Over", "French Pro D2 J8: Oyonnax away at bottom-two Montauban + OLBG 10/15 consensus"),
    "RGU-609577": ("Connacht", 0.725, 49.5, "Over", "URC Round 6: Connacht home in Galway vs Zebre Parma (>70% favorite -> medium; OLBG handicap -18.5)"),
    "RGU-609576": ("Bulls", 0.770, 52.5, "Over", "URC Round 6: Bulls at Loftus Versfeld vs Ulster (>70% favorite -> medium; OLBG handicap Ulster +18.5)"),
    "RGU-609567": ("Toulouse", 0.840, 54.5, "Over", "Top 14 J8: leader Toulouse home vs winless Perpignan (>70% heavy chalk -> medium; OLBG Perpignan +23.5)"),
    # Handball — EHF Champions League Round 5 & DAIKIN HBL Matchday 10 official standings
    "HAN-12046": ("FC Barcelona", 0.765, 62.5, "Over", "EHFCL Group E: unbeaten Barca (4-0-0, 137:104, 20 straight wins) vs Montpellier (1-0-3, 116:125; >70% chalk -> medium)"),
    "HAN-12048": ("SC Magdeburg", 0.775, 60.5, "Over", "EHFCL Group F: unbeaten SC Magdeburg (4-0-0, 141:108; won reverse 37:22) at Kolstad (0-0-4, 111:143; >70% chalk -> medium)"),
    "HAN-12054": ("Sporting CP", 0.745, 63.5, "Over", "EHFCL Group D: unbeaten Sporting CP (3-1-0, 149:125) home vs Kristianstad (0-0-4, 122:155; >70% chalk -> medium)"),
    "HAN-12051": ("Pick Szeged", 0.565, 61.5, "Over", "EHFCL Group D Round 5 at PICK Arena Szeged: OTP Bank-PICK Szeged home edge vs GOG Handbold"),
    "HAN-12094": ("TVB Stuttgart", 0.638, 58.5, "Over", "DAIKIN HBL Matchday 10 Swabian derby: #9 TVB Stuttgart (272:270, 9 pts) home vs #16 promoted SG BBM Bietigheim (260:292, 4 pts)"),
    # Newly verified 2026-10-22T07:25Z morning refresh (EuroLeague R7, SHL, Herreligaen, WST Belfast Last 16, ATP Almaty QF, SuperLega G2)
    "BKB-535920": ("Dubai Basketball", 0.545, 168.5, "Over", "EuroLeague R7: Dubai Basketball (4-2, 490:493) at FC Bayern Munich (2-4, 521:552)"),
    "BKB-535922": ("FC Barcelona", 0.5652, 180.5, "Over", "EuroLeague R7: FC Barcelona (3-3, 534:525, +9) at Olimpia Milan (1-5, 504:559, -55)"),
    "BKB-535924": ("Crvena Zvezda", 0.542, 162.5, "Under", "EuroLeague R7 Belgrade Eternal Derby: Crvena Zvezda (4-2, +28) at Partizan (3-3, -5)"),
    "BKB-535925": ("Olympiacos Piraeus", 0.5621, 172.5, "Over", "EuroLeague R7 co-leaders clash at SEF: Olympiacos (5-1, 564:524) home vs Fenerbahce (5-1, 501:447)"),
    "BKB-535926": ("Valencia Basket", 0.6223, 183.5, "Over", "EuroLeague R7: Valencia Basket (4-2, 583:537, 97.2 ppg) at Paris Basketball (1-5, 504:545)"),
    "HAN-12076": ("Aalborg Handbold", 0.589, 67.5, "Over", "Betoro Herreligaen: Aalborg Handbold (15 pts, 323:306) away at bottom Skive fH (2 pts, 328:366) — overrides 3/7 crowd lean"),
    "HAN-12101": ("Bidasoa Irun", 0.720, 61.5, "Over", "Liga ASOBAL J7: #2 Bidasoa Irun (6 GP, 210:178, 12 pts) home vs Caserio (5 GP, 160:155, 7 pts; >70% chalk -> medium)"),
    "HAN-12109": ("Kosovo W", 0.535, 55.5, "Under", "IHF Women's WCQ Europe: both legs staged in Prishtina, Kosovo — zero home edge for listed home side Estonia W"),
    "ICH-199899": ("IF Bjorkloven", 0.548, 5.5, "Under", "SHL official standings: #4 IF Bjorkloven (17 pts) home vs #7 IF Malmo Redhawks (14 pts in 9 GP)"),
    "ICH-199906": ("Frolunda HC", 0.5954, 5.5, "Over", "SHL official standings: #2 Frolunda HC (11 GP, 38:24, 25 pts) away at #6 Rogle BK (10 GP, 23:21, 14 pts)"),
    "ICH-199902": ("Lulea HF", 0.528, 5.5, "Over", "SHL official standings: #8 Lulea HF (14 pts) at #11 Vaxjo Lakers HC (12 pts)"),
    "SNO-9940": ("Kyren Wilson", 0.5918, 5.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Kyren Wilson vs Pang Junxu"),
    "SNO-9942": ("Matthew Selt", 0.5367, 5.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Matthew Selt vs Sam Craigie"),
    "SNO-9946": ("Anthony McGill", 0.569, 5.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Anthony McGill (beat Lisowski 4-1) vs Mateusz Baranowski"),
    "SNO-9947": ("Elliot Slessor", 0.581, 5.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Elliot Slessor (beat Jamie Jones 4-1) vs Ricky Walden"),
    "SNO-9943": ("Mark Williams", 0.6449, 5.5, "Under", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Mark Williams vs Martin O'Donnell"),
    "SNO-9945": ("David Gilbert", 0.6033, 5.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): David Gilbert vs Cheung Ka Wai — contrarian model edge"),
    "SNO-9944": ("Jordan Brown", 0.5014, 6.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Jordan Brown vs Scott Donaldson coin-flip"),
    "SNO-9941": ("Jak Jones", 0.5446, 5.5, "Over", "Editorial Northern Ireland Open strength prior (official seed ranks unverified): Jak Jones vs Daniel Wells"),
    "TEN-902129": ("Stefanos Tsitsipas", 0.5739, 22.5, "Over", "ATP Almaty QF: #39 [7] Stefanos Tsitsipas (beat Kukushkin 6-1, 6-2) vs #73 James Duckworth"),
    "TEN-902133": ("Tommy Paul", 0.725, 21.5, "Under", "ATP Lyon QF: #15 [4] Tommy Paul (2575 pts) vs #94 Corentin Moutet (640 pts; >70% favorite -> medium)"),
    "VOL-36994": ("Itas Trentino", 0.5293, 185.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30003): Itas Trentino vs Cisterna Volley"),
    "VOL-36995": ("Cucine Lube Civitanova", 0.6585, 181.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30005): Cucine Lube Civitanova (3-1, 97:85) vs Pallavolo Padova"),
    "VOL-36996": ("Vero Volley Monza", 0.5914, 184.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30007): Vero Volley Monza (91:94 at Prata) vs Rana Verona"),
    "VOL-36997": ("Sir Susa Scai Perugia", 0.5995, 183.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30002): Sir Susa Scai Perugia (3-2 at Cuneo, 113:103) vs Tinet Prata di Pordenone"),
    "ICH-199937": ("NY Rangers", 0.5682, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): NY Rangers 7-3-1 (11 GP, 15 pts, 33 GF / 24 GA) at TOR Maple Leafs 5-4-2 (11 GP, 12 pts, 38 GF / 35 GA)"),
    "GFA-3530": ("St Finbarrs", 0.5864, 37.5, "Over", "Cork GAA 2026 Premier SFC complete 5-game championship record (gaacork.ie): St Finbarrs 3-2 (116 PF / 85 PA, +31) vs Nemo Rangers 4-1 (98 PF / 79 PA, +19) at neutral Pairc Ui Chaoimh"),
    "TEN-902117": ("Marie Bouzkova", 0.5620, 22.5, "Over", "WTA 500 Ningbo QF official draw (wtatennis.com MDS.pdf): Marie Bouzkova vs Sara Bejlek + OLBG 1/1"),
}

# Verified outright field-size priors (Dirichlet shrinkage toward 1/F)
OUTRIGHT_FIELDS = {
    "GLF-101904": (120, 20, "Seamus Power", 0.125, "PGA Tour Butterfield Bermuda Championship official 120-man Port Royal field + OLBG 5/22 tips"),
    "GLF-101908": (96, 24, None, None, "JGTO official Fortinet Players Cup 96-player field prior"),
    "GLF-101911": (72, 16, None, None, "Senior tour 72-player field prior"),
    "GLF-101912": (120, 20, None, None, "Sunshine Tour 120-player field prior"),
    "GLF-101903": (78, 16, None, None, "PGA Tour Champions 78-player field prior"),
    "MTR-913": (22, 12, "Max Verstappen", 0.284, "FIA Formula 1 22-car Austin COTA grid prior + 12/33 OLBG win tips (3 experts)"),
    "MTR-911": (22, 12, None, None, "FIA Formula 1 22-car Austin Qualifying grid prior + 5/7 OLBG tips"),
    "MTR-828": (22, 12, None, None, "FIA Formula 1 2026 Drivers Championship prior + 9/33 OLBG tips"),
    "MTR-912": (21, 10, None, None, "FIA Formula 1 Drivers Championship w/o leader market prior"),
    "DAR-32338": (32, 14, None, None, "PDC Machineseeker European Championship 32-player Dortmund field prior"),
    "DAR-26023": (128, 20, None, None, "PDC World Darts Championship field prior"),
    "CRI-182606": (14, 10, None, None, "ICC Men's Cricket World Cup 2027 14-team tournament prior"),
    "CRI-187184": (8, 8, None, None, "WBBL 8-team tournament prior"),
    "CRI-187503": (8, 8, None, None, "BBL 8-team tournament prior"),
    "CRI-187504": (6, 6, None, None, "SA20 6-team tournament prior"),
    "CRI-188350": (18, 10, None, None, "Vitality Blast 18-county prior (unpriced: 0/0 OLBG tips)"),
    "RGU-609013": (6, 6, None, None, "Six Nations 6-team championship prior"),
    "RGL-2695857": (2, 4, None, None, "State of Origin 2-state series prior"),
    "RGL-2801554": (12, 8, None, None, "Super League 12-club Grand Final prior"),
    "RGL-2801600": (17, 10, None, None, "NRL 17-club Grand Final prior"),
    "GFA-3327": (32, 12, None, None, "GAA All-Ireland SFC 32-county prior"),
}


def decimal_to_american(price: float | None) -> str | None:
    if price is None or price <= 1.0:
        return None
    if price >= 2.0:
        return f"+{round((price - 1.0) * 100)}"
    return f"-{round(100.0 / (price - 1.0))}"


def norm_inv(p: float) -> float:
    """Acklam rational inverse normal CDF for spread mapping."""
    p = min(max(p, 0.001), 0.999)
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def half_point(val: float) -> float:
    return math.floor(abs(val)) + 0.5


def resolve_team_side(selection: str | None, home: str | None, away: str | None) -> str | None:
    if not selection or not home or not away:
        return None
    s = selection.lower()
    if s in ("tie", "draw"):
        return None
    # strip set score / handicap suffixes
    clean = re.sub(r"\s+(to win.*|[+-]\d+(\.\d+)?)$", "", s).strip()
    if home.lower() in clean or clean in home.lower():
        return home
    if away.lower() in clean or clean in away.lower():
        return away
    return None


def main() -> None:
    matches = json.loads((DATA / "matches.json").read_text())
    preds_doc = json.loads((DATA / "predictions-olbg.json").read_text()) if (DATA / "predictions-olbg.json").exists() else {"predictions": []}
    high_verified_ids = {p["match_id"] for p in preds_doc.get("predictions", [])}

    out = []
    for m in matches:
        mid = m["id"]
        sport = m["sport"]
        home, away = m["home"], m["away"]
        won, tot = m["olbg_tips_won"], m["olbg_tips_total"]
        p_raw = round(won / tot, 4) if (won is not None and tot) else None
        carried = bool(m.get("row_notes") and "carried from" in m["row_notes"])
        flags: list[str] = []

        # Outright / multi-runner markets (including Greyhound races)
        if m["market_family"] == "outright" or sport == "Greyhounds":
            field_info = OUTRIGHT_FIELDS.get(mid)
            field_n = field_info[0] if field_info else (6 if sport == "Greyhounds" else 16)
            k_str = field_info[1] if field_info else (6 if sport == "Greyhounds" else 10)
            override_sel = field_info[2] if field_info else None
            override_p = field_info[3] if field_info else None
            basis = field_info[4] if field_info else f"Dirichlet shrinkage toward 1/{field_n} field prior"

            if won is None or not tot:
                out.append({
                    "match_id": mid,
                    "sport": sport,
                    "event_name": m["event_name"],
                    "home": home,
                    "away": away,
                    "competition": m["competition"],
                    "start": m["date_iso"] or m["olbg_date_label"],
                    "olbg_url": m["olbg_url"],
                    "inputs": {
                        "olbg_market": m["olbg_market"],
                        "olbg_consensus_selection": m["olbg_consensus_selection"],
                        "olbg_tips": m["olbg_tips"],
                        "p_raw": None,
                        "p_shrunk": None,
                        "basis": basis,
                    },
                    "our_match_probability": None,
                    "our_home_probability": None,
                    "our_pick": m["olbg_consensus_selection"],
                    "our_pick_probability": None,
                    "our_fair_odds": None,
                    "our_price_pick": None,
                    "our_us_odds_pick": None,
                    "our_price_other": None,
                    "our_handicap_line": None,
                    "our_handicap_side": None,
                    "our_handicap_unit": None,
                    "our_total_line": None,
                    "our_total_side": None,
                    "our_total_unit": None,
                    "our_total_basis": "not applicable to unpriced outright market",
                    "confidence": "low",
                    "flags": ["zero_tips_unpriced", "outright_market"],
                })
                continue

            alpha = k_str * (1.0 / field_n)
            p_pick = override_p if override_p is not None else round((won + alpha) / (tot + k_str), 4)
            pick = override_sel or m["olbg_consensus_selection"]
            fair_odds = round(1.0 / p_pick, 2)
            price_pick = round((1.0 - MARGIN) / p_pick, 2)
            us_pick = decimal_to_american(price_pick)

            in_window = (PRICE_MIN_HIGH <= price_pick <= PRICE_MAX_HIGH) and (p_pick < PROB_MAX_HIGH)
            if (mid in high_verified_ids and m["competition_status"] == "verified"
                    and not carried and in_window):
                conf = "high"
            elif m["competition_status"] == "verified" and tot >= 6 and p_pick >= 0.15 and not carried:
                conf = "medium"
            else:
                conf = "low"

            out.append({
                "match_id": mid,
                "sport": sport,
                "event_name": m["event_name"],
                "home": home,
                "away": away,
                "competition": m["competition"],
                "start": m["date_iso"] or m["olbg_date_label"],
                "olbg_url": m["olbg_url"],
                "inputs": {
                    "olbg_market": m["olbg_market"],
                    "olbg_consensus_selection": m["olbg_consensus_selection"],
                    "olbg_tips": m["olbg_tips"],
                    "p_raw": p_raw,
                    "p_shrunk": round(p_pick, 4),
                    "basis": basis,
                },
                "our_match_probability": round(p_pick, 4),
                "our_home_probability": None,
                "our_pick": pick,
                "our_pick_probability": round(p_pick, 4),
                "our_fair_odds": fair_odds,
                "our_price_pick": price_pick,
                "our_us_odds_pick": us_pick,
                "our_price_other": None,
                "our_handicap_line": None,
                "our_handicap_side": None,
                "our_handicap_unit": None,
                "our_total_line": None,
                "our_total_side": None,
                "our_total_unit": None,
                "our_total_basis": "single-selection outright / multi-runner field",
                "confidence": conf,
                "flags": ["outright_field_prior"] + (["carried_from_prior_pass"] if carried else []),
            })
            continue

        # Head-to-head match markets
        p_shrunk = round((won + 2) / (tot + 4), 4) if (won is not None and tot is not None) else 0.5
        if mid in EDITORIAL_STRENGTH:
            pick, p_pick, tot_override, tot_side_override, basis = EDITORIAL_STRENGTH[mid]
            p_home = p_pick if pick == home else round(1.0 - p_pick, 4)
        else:
            _non_win = {"Set Score", "Set Betting", "Handicap", "Handicap 2-way", "Match Handicap",
                        "Pointspread", "Puck Line", "Total Legs", "Game Totals", "Games Won", "1st Set Winner"}
            side = None if (m.get("olbg_market") in _non_win) else resolve_team_side(m["olbg_consensus_selection"], home, away)
            if side is None:
                # e.g. Handball "Tie" consensus or totals-only listing -> lean home edge
                side = home or m["olbg_consensus_selection"]
                p_base = 0.52
                flags.extend(["non_win_or_tie_consensus_mapped", "non_win_consensus_excluded_from_winner_probability"] if m.get("olbg_market") in _non_win else ["non_win_or_tie_consensus_mapped"])
            else:
                p_base = p_shrunk
            logit = math.log(p_base / (1.0 - p_base))
            h_shift = HOME_LOGIT.get(sport, 0.0)
            if side == home:
                logit += h_shift
            elif side == away:
                logit -= h_shift
            p_side = 1.0 / (1.0 + math.exp(-logit))
            if p_side >= 0.5:
                pick = side
                p_pick = round(p_side, 4)
            else:
                pick = away if side == home else home
                p_pick = round(1.0 - p_side, 4)
            p_home = p_pick if pick == home else round(1.0 - p_pick, 4)
            tot_override, tot_side_override = None, None
            basis = ("Sport home-court baseline (non-winner OLBG consensus excluded)" if m.get("olbg_market") in _non_win else "OLBG tip split shrunk with Beta(2,2) prior + sport home-court logit adjustment")

        if mid in EDITORIAL_STRENGTH:
            basis = "EDITORIAL PRIOR (uncalibrated model assumption, not an official probability): " + basis
        fair_odds = round(1.0 / p_pick, 2)
        price_pick = round((1.0 - MARGIN) / p_pick, 2)
        price_other = round((1.0 - MARGIN) / (1.0 - p_pick), 2)
        us_pick = decimal_to_american(price_pick)

        # Handicap / Spread / Run Line / Puck Line origination
        if sport in SPREAD_CFG and home and away:
            sigma, hc_unit = SPREAD_CFG[sport]
            if sport in ("Baseball", "Ice Hockey"):
                hc_line = -1.5
            elif sport == "Volleyball":
                hc_line = -2.5 if p_pick >= 0.72 else -1.5
            else:
                raw_margin = sigma * norm_inv(max(p_pick, 0.51))
                hc_line = -max(1.5, half_point(raw_margin))
            hc_side = pick
        else:
            hc_line, hc_side, hc_unit = None, None, None

        # Match Totals Over / Under origination
        if tot_override is not None:
            t_line = tot_override
            t_side = tot_side_override
            _, t_unit, _ = TOTAL_CFG.get(sport, (None, "pts", ""))
            t_basis = "Editorial total/side assumption informed by source context; not a verified scoring rate or observed bookmaker line"
        elif sport in TOTAL_CFG:
            base_line, t_unit, t_basis = TOTAL_CFG[sport]
            if sport == "Basketball" and (m.get("olbg_league_label") or "") != "NBA":
                base_line = 169.5 if "Euro" in (m.get("competition") or m.get("olbg_league_label") or "") else 163.5
            t_line = base_line
            t_side = "Over" if p_pick < 0.63 else "Under"
        else:
            t_line, t_side, t_unit, t_basis = None, None, None, "no total market originated"

        # Confidence grading:
        # HIGH strictly requires:
        #   1) official source verification (competition_status == 'verified')
        #   2) live non-carried row (not carried from yesterday's pass)
        #   3) price strictly inside [-250, +10000] (1.40 <= price_pick <= 101.00) AND fair prob < 0.70
        #   4) verified form & recent history backing in predictions-olbg.json
        if p_pick >= PROB_MAX_HIGH or price_pick < PRICE_MIN_HIGH:
            flags.append("heavy_chalk_above_70pct_excluded_from_high")

        in_window = (PRICE_MIN_HIGH <= price_pick <= PRICE_MAX_HIGH) and (p_pick < PROB_MAX_HIGH)
        ko_passed = bool(m.get("date_iso")) and m["date_iso"] < BUILD_DATE.isoformat()
        if ko_passed:
            # A fixture whose kick-off date has already passed cannot be a live high-confidence
            # selection: publishing it as one would mean tipping a match that has been played.
            flags.append("kick_off_passed_archived")
        if (mid in high_verified_ids and m["competition_status"] == "verified"
                and not carried and in_window and not ko_passed):
            conf = "high"
        elif carried:
            conf = "medium" if (m["competition_status"] == "verified" and (tot or 0) >= 5) else "low"
            flags.append("carried_from_prior_pass")
        elif m["competition_status"] == "verified" and (mid in EDITORIAL_STRENGTH or ((tot or 0) >= 5 and p_pick >= 0.56)):
            conf = "medium"
        else:
            conf = "low"

        out.append({
            "match_id": mid,
            "sport": sport,
            "event_name": m["event_name"],
            "home": home,
            "away": away,
            "competition": m["competition"],
            "start": m["date_iso"] or m["olbg_date_label"],
            "olbg_url": m["olbg_url"],
            "inputs": {
                "olbg_market": m["olbg_market"],
                "olbg_consensus_selection": m["olbg_consensus_selection"],
                "olbg_tips": m["olbg_tips"],
                "p_raw": p_raw,
                "p_shrunk": p_shrunk,
                "basis": basis,
            },
            "our_match_probability": p_pick,
            "our_home_probability": p_home,
            "our_pick": pick,
            "our_pick_probability": p_pick,
            "our_fair_odds": fair_odds,
            "our_price_pick": price_pick,
            "our_us_odds_pick": us_pick,
            "our_price_other": price_other,
            "our_handicap_line": hc_line,
            "our_handicap_side": hc_side,
            "our_handicap_unit": hc_unit,
            "our_total_line": t_line,
            "our_total_side": t_side,
            "our_total_unit": t_unit,
            "our_total_basis": t_basis,
            "confidence": conf,
            "flags": flags,
        })

    out = apply_lines(out, matches)
    sync_predictions(DATA / 'predictions-olbg.json', {r['match_id']: r for r in out},
                     'match_id', lambda r: r['confidence'])
    (DATA / "lines.json").write_text(json.dumps(out, indent=2) + "\n")
    counts = {c: sum(1 for x in out if x["confidence"] == c) for c in ("high", "medium", "low")}
    print(f"lines: {len(out)}  high={counts['high']}  medium={counts['medium']}  low={counts['low']}")


if __name__ == "__main__":
    main()
