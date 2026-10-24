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
    "BKB-535926": ("Valencia Basket", 0.600, 169.5, "Over", "Official EuroLeague standings read 2026-10-22T21:55Z: Valencia Basket 6th (4-2, 583:537, +46, 2-0 away) v Paris Basketball 12th (1-5, 504:545, -41); OLBG money line 1/2 Paris is faded on the official table"),
    "BKB-535928": ("Zalgiris", 0.655, 165.5, "Under", "EuroLeague R7 Kaunas: Zalgiris (3-3) home vs #19 ASVEL (1-5, lost to Crvena Zvezda 82-84 & Real Madrid)"),
    # Tennis — ATP 250 Almaty, Brussels, Lyon & WTA Ningbo / Osaka (official ATP/WTA rankings + R1 results)
    "TEN-902119": ("Adrian Mannarino", 0.600, 22.5, "Over", "Official ATP Almaty order of play (Fri 23 Oct, Center Court starts 11:30): [Q] Basilashvili v Mannarino; OLBG money line 1/1 Mannarino"),
    "TEN-902135": ("Ann Li", 0.660, 21.5, "Over", "Official WTA Osaka order of play (Fri 23 Oct, Center Court starts 11:30): [1] Ann Li v Lilli Tagger; #1 seed Li beat Emerson Jones 5-7, 6-0, 6-3 with 10 aces; OLBG money line 6/7 Li"),
    "TEN-902107": ("Ashlyn Krueger", 0.600, 21.5, "Over", "Official WTA Osaka order of play (Fri 23 Oct, Center Court follows the 11:30 opener): [4] Talia Gibson v Ashlyn Krueger; OLBG money line 3/4 Krueger"),
    "TEN-902138": ("Katerina Siniakova", 0.600, 21.5, "Over", "Official WTA Osaka order of play (Fri 23 Oct, Center Court, third match): [Q] Mary Stoiana v Katerina Siniakova; OLBG money line 1/1 Siniakova"),
    "TEN-902134": ("Katie Boulter", 0.600, 21.5, "Over", "Official WTA Osaka order of play (Fri 23 Oct, Center Court, fourth match): [8] Katie Boulter v Antonia Ruzic; OLBG money line is a games-won handicap row, not the match market"),
    "TEN-902145": ("Daniil Medvedev", 0.660, 21.5, "Over", "Official ATP Almaty order of play (Fri 23 Oct, Center Court, follows the 13:00 Tsitsipas match): [1] Medvedev v Terence Atmane; OLBG money line 2/2 Medvedev"),
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
    "RGU-609578": ("Leinster", 0.660, 47.5, "Over", "Official URC 2026/27 fixtures list Round 4 (24 Oct, KO 18.00 IRE & UK) + official URC table after Round 3: Leinster 10th (1-0-2, 8 pts, 75:58, +17) v Munster 9th (1-1-1, 9 pts, 72:74, -2)"),
    "RGU-609556": ("Oyonnax", 0.605, 46.5, "Over", "French Pro D2 J8: Oyonnax away at bottom-two Montauban + OLBG 10/15 consensus"),
    "RGU-609577": ("Connacht", 0.660, 49.5, "Over", "Official URC 2026/27 fixtures list Round 4 (23 Oct, Dexcom Stadium Galway, KO 19.45 IRE & UK) + official URC table after Round 3: Connacht 14th (1-0-2, 5 pts, 56:84, -28) v Zebre Parma 16th (0-0-3, 1 pt, 52:116, -64); OLBG money line 5/7 Connacht"),
    "RGU-609576": ("Vodacom Bulls", 0.620, 52.5, "Over", "Official URC 2026/27 fixtures list Round 4 (24 Oct, Loftus Versfeld Pretoria, KO 12.45 IRE & UK) + official URC table after Round 3: Vodacom Bulls 3rd (2-0-1, 11 pts, 126:54, +72) v Ulster 11th (0-2-1, 8 pts, 88:93, -5); OLBG money line 2/3 Ulster is faded on the official table"),
    "RGU-609580": ("DHL Stormers", 0.600, 49.5, "Over", "Official URC 2026/27 fixtures list Round 4 (24 Oct, DHL Stadium Cape Town, KO 15.00 IRE & UK) + official URC table after Round 3: DHL Stormers 4th (2-0-1, 11 pts, 81:54, +27) v Scarlets 12th (1-0-2, 7 pts, 68:85, -17); OLBG money line 1/2 Stormers"),
    "RGU-609579": ("Edinburgh", 0.670, 49.5, "Over", "Official URC 2026/27 fixtures list Round 4 (23 Oct, Hive Stadium Edinburgh, KO 19.45 IRE & UK) + official URC table after Round 3: Edinburgh 1st and unbeaten (3-0-0, 14 pts, 80:54, +26) v 10bet Lions 7th (2-0-1, 9 pts, 77:102, -25); OLBG money line 2/2 Edinburgh"),
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
    "HAN-12076": ("Aalborg Handbold", 0.589, 67.5, "Over", "Betoro Herreligaen: Aalborg Handbold (15 pts, 323:306) away at bottom Skive fH (2 pts, 328:366) — overrides 3/7 crowd lean"),
    "HAN-12101": ("Bidasoa Irun", 0.620, 61.5, "Over", "Official ASOBAL site (read 2026-10-22T21:55Z): Bidasoa Irun 'se mantiene en lo mas alto' of the Liga NEXUS ENERGIA ASOBAL table; Bidasoa 6 GP, 210:178, 12 pts v BM Caserio Ciudad Real 5 GP, 160:155, 7 pts; OLBG money line 1/3 Bidasoa"),
    "HAN-12110": ("Kosovo W", 0.580, 55.5, "Under", "Official EHF competition calendar (read 2026-10-22T21:55Z): both Phase 1 legs of the 2027 IHF Women's World Championship European qualifier are staged at the Palace of Youth and Sports, Prishtina, Kosovo, so the listed home side Estonia has no home edge; OLBG money line 3/5 Kosovo (W)"),
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
    "VOL-36995": ("Cucine Lube Civitanova", 0.6585, 181.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30005 & official R1 standings): #4 Cucine Lube Civitanova (1-0, 3 pts, 3-0 sets, 78:65) vs #11 Pallavolo Padova (0-1, 0 pts, 0-3 sets, 56:75)"),
    "VOL-36996": ("Vero Volley Monza", 0.5914, 184.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30007 & official R1 standings): #8 Vero Volley Monza (0-1, 1-3 sets, 90:94) vs #9 Rana Verona (0-1, 0-3 sets, 65:78)"),
    "VOL-36997": ("Sir Susa Scai Perugia", 0.5995, 183.5, "Over", "SuperLega Giornata 2 (volleyballworld.com #30002): Sir Susa Scai Perugia (3-2 at Cuneo, 113:103) vs Tinet Prata di Pordenone"),
    "VOL-37005": ("Chaumont", 0.5674, 182.5, "Over", "LNV Alterna VOLSTAR J3 (lnv-web.dataproject.com): #2 Chaumont (2-0, 6 pts, sets 6:1, rally 173:146) at #13 Sete (0-2, 0 pts, sets 1:6, rally 165:194)"),
    "ICH-199931": ("EDM Oilers", 0.5612, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): EDM Oilers 7-1-1 (9 GP, 15 pts, 41 GF / 27 GA) home vs CAR Hurricanes 8-2-1 (11 GP, 17 pts, 42 GF / 27 GA)"),
    "ICH-199932": ("NJ Devils", 0.5649, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): NJ Devils 5-4-0 (9 GP, 10 pts, 29 GF / 30 GA) home vs ANA Ducks 4-5-0 (9 GP, 8 pts, 26 GF / 29 GA, L4)"),
    "ICH-199933": ("DET Red Wings", 0.5964, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): DET Red Wings 3-3-3 (9 GP, 9 pts, 23 GF / 28 GA) at VAN Canucks 2-8-1 (11 GP, 5 pts, 33 GF / 51 GA)"),
    "ICH-199934": ("FLA Panthers", 0.5374, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): FLA Panthers 5-3-2 (10 GP, 12 pts, 31 GF / 30 GA) at PIT Penguins 3-6-1 (10 GP, 7 pts, 33 GF / 38 GA)"),
    "ICH-199935": ("MIN Wild", 0.8022, 6.5, "Under", "NHL official standings 2026-10-22 (api-web.nhle.com): MIN Wild 6-2-2 (10 GP, 14 pts, 31 GF / 25 GA) at CGY Flames 2-6-0 (8 GP, 4 pts, 17 GF / 37 GA; >70% chalk -> medium)"),
    "ICH-199936": ("BOS Bruins", 0.7135, 5.5, "Under", "NHL official standings 2026-10-22 (api-web.nhle.com): BOS Bruins 7-2-1 (10 GP, 15 pts, 36 GF / 22 GA) home vs NSH Predators 3-2-3 (8 GP, 9 pts, 23 GF / 24 GA; >70% chalk -> medium)"),
    "ICH-199937": ("NY Rangers", 0.5306, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): NY Rangers 7-3-1 (11 GP, 15 pts, 33 GF / 24 GA) road at TOR Maple Leafs 5-4-2 (11 GP, 12 pts, 38 GF / 35 GA; road home-ice sign fixed -> <55% medium)"),
    "ICH-199938": ("NY Islanders", 0.6831, 6.5, "Under", "NHL official standings 2026-10-22 (api-web.nhle.com): NY Islanders 5-3-1 (9 GP, 11 pts, 27 GF / 20 GA) home vs LA Kings 1-4-2 (7 GP, 4 pts, 17 GF / 27 GA; 1.39/-256 outside -250 floor -> medium)"),
    "ICH-199939": ("SEA Kraken", 0.5125, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): SEA Kraken 6-3-1 (10 GP, 13 pts, 39 GF / 34 GA) home vs UTA Mammoth 7-3-0 (10 GP, 14 pts, 38 GF / 31 GA)"),
    "ICH-199940": ("VGS Golden Knights", 0.6192, 6.5, "Over", "NHL official standings 2026-10-22 (api-web.nhle.com): VGS Golden Knights 8-3-0 (11 GP, 16 pts, 44 GF / 30 GA) at STL Blues 4-4-1 (9 GP, 9 pts, 29 GF / 29 GA)"),
    "ICH-199941": ("DAL Stars", 0.6694, 5.5, "Under", "NHL official standings 2026-10-22 (api-web.nhle.com): DAL Stars 5-3-1 (9 GP, 11 pts, 23 GF / 15 GA, W3) home vs WPG Jets 4-3-2 (9 GP, 10 pts, 24 GF / 26 GA, L2)"),
    "ICH-199942": ("OTT Senators", 0.6900, 5.5, "Under", "NHL official standings 2026-10-22 (api-web.nhle.com): OTT Senators 7-3-0 (10 GP, 14 pts, 29 GF / 24 GA) home vs SJ Sharks 5-4-1 (10 GP, 11 pts, 27 GF / 35 GA; 1.38/-263 outside -250 floor -> medium)"),
    # Cork GAA's own page (gaacork.ie, re-read 2026-10-23) prints Nemo 1-15 to 0-16 v Carrigaline and 1-20 to 1-17 v
    # Castlehaven, St Finbarrs 2-12 to 0-16 v Clonakilty and "a convincing victory over Carbery" with no scoreline. The
    # earlier aggregate (+31 / +19) is not on that page and is deliberately not restated here (FL-177).
    "GFA-3530": ("St Finbarrs", 0.5864, 37.5, "Over", "Cork GAA final page (gaacork.ie): St Finbarrs 2-12 to 0-16 semi-final win over Clonakilty, Nemo 1-15 to 0-16 over Carrigaline; neutral Pairc Ui Chaoimh"),
    "TEN-902117": ("Marie Bouzkova", 0.5620, 22.5, "Over", "WTA 500 Ningbo QF official draw (wtatennis.com MDS.pdf): Marie Bouzkova vs Sara Bejlek + OLBG 1/1"),
    # 2026-10-23 late-evening pass (session-a87a3681). Every prior below states the official record it is built on and
    # is an uncalibrated assumption, not a fitted probability. NBA/clocks read on nba.com at 2026-10-23T21:32Z; NHL on
    # api-web.nhle.com (standings payload dated 2026-10-23T16:16Z, schedule payload 2026-10-23).
    "BKB-536035": ("ATL Hawks", 0.5850, 224.5, "Over", "NBA official standings 2026-10-23: ATL 1-0 (road 1-0, W1) at CHA 1-0 (road 1-0, W1); neither has played at home; OLBG spread 2/2 ATL -2.5"),
    "BKB-536036": ("MIN Timberwolves", 0.6000, 221.5, "Over", "NBA official standings 2026-10-23: MIN 1-0 (road 1-0, W1) at ORL 0-1 (home 0-1, L1); OLBG 5/5 MIN despite 2.05 listing price"),
    "BKB-536037": ("IND Pacers", 0.6450, 228.5, "Over", "NBA official standings 2026-10-23: IND 1-0 (road 1-0, W1) home vs DAL 0-1 (road 0-1, L1); OLBG 3/3 IND"),
    "BKB-536034": ("TOR Raptors", 0.6150, 226.5, "Over", "NBA official standings 2026-10-23: TOR 1-0 (home 1-0) at WAS 1-0 (home 1-0); OLBG 4/4 TOR"),
    "BKB-536038": ("DET Pistons", 0.6000, 224.5, "Over", "NBA official standings 2026-10-23: DET 1-0 (home 1-0, W1) at MIA 0-1 (home 0-1, L1); OLBG 3/3 DET"),
    "ICH-199984": ("MTL Canadiens", 0.6450, 5.5, "Under", "NHL official standings 2026-10-23: MTL 4-3-2 (10 pts, 30 GF / 34 GA, road 1-1-1, OT1) at CHI 3-6-0 (6 pts, 21 GF / 36 GA, home 3-2-0, L1); OLBG 3/3 MTL"),
    "ICH-199985": ("COL Avalanche", 0.5700, 5.5, "Over", "NHL official standings 2026-10-23: COL 5-4-1 (11 pts, 41 GF / 31 GA, home 3-1-1, L2) vs TBL 7-2-0 (14 pts, 31 GF / 23 GA, road 2-2-0, W3); OLBG puck line 1/2 TBL +1.5"),
    # 2026-10-23 SvelteKit evening supplement & multi-sport pass (session-b322f52e):
    "BKB-536039": ("GS Warriors", 0.572, 233.5, "Under", "NBA official preview & standings (nba.com): GSW Chase Center home opener (3-0 H2H sweep vs MEM in 2025-26, Curry 23 pts in opener) vs retooled MEM 1-0"),
    "BKB-536042": ("LA Lakers", 0.608, 229.5, "Over", "NBA official preview & standings (nba.com): LAL 1-0 after 127-105 win over GSW on 56.8% FG (Doncic 28/8/7, Kessler 26 pts on 12-for-12 FG, Reaves 23/6) + 8-4 in last 12 H2H vs LAC"),
    "BKB-536043": ("POR Trail Blazers", 0.588, 231.5, "Over", "NBA official preview & standings (nba.com): POR 1-0 after 124-83 rout of PHX (Lillard 25 pts/6 3PM, Avdija 18/10, Morant 14/8) + 4-0 H2H sweep vs SAC in 2025-26; SAC 0-1 after 121-96 loss at LAC + OLBG 6/7 ML"),
    "RGU-609581": ("Ospreys", 0.585, 49.5, "Over", "URC 2026/27 official R3 table & H2H (stats.unitedrugby.com): Ospreys beat Dragons 38-31 away at Rodney Parade on 9 Oct; Dragons 9th (9 pts, 88:83) at Ospreys 14th (6 pts, 81:107) at St. Helen's, Swansea"),
    "HAN-12138": ("Orlen Wisla Plock", 0.580, 56.5, "Under", "EHF CL Men 2026/27 Group B official table (ehfcl.eurohandball.com): #1 Orlen Wisla Plock 3-0-2 (141:136, +5, 6 pts) home at ORLEN Arena vs #3 HBC Nantes 3-0-2 (142:143, -1, 6 pts; lost 33:27 to Vardar in R5)"),
    "HAN-12130": ("MT Melsungen", 0.615, 58.5, "Under", "EHF CL Men 2026/27 Group B official table (ehfcl.eurohandball.com): #2 MT Melsungen 3-0-2 (138:138, 6 pts; beat Plock 28:26 in R5) visiting eliminated #4 HC Vardar 1961 1-0-4 (154:158, 2 pts)"),
    "HAN-12134": ("Aalborg Handbold", 0.555, 63.5, "Over", "EHF CL Men 2026/27 Group C official table (ehfcl.eurohandball.com): unbeaten #1 Aalborg Handbold 4-1-0 (170:145, +25, 9 pts; beat PSG in R1) at #2 Paris Saint-Germain 3-1-1 (182:157, +25, 7 pts; lost 29:28 at Zagreb in R5) + OLBG 1/1 Aalborg"),
    "HAN-12129": ("Sporting CP", 0.575, 66.5, "Over", "EHF CL Men 2026/27 Group D official table (ehfcl.eurohandball.com): unbeaten #1 Sporting CP 4-1-0 (191:165, +26, 9 pts; beat GOG in R1 & Kristianstad 42:40 in R5) visiting #2 GOG 3-1-1 (178:172, +6, 7 pts)"),
    "HAN-12133": ("Dinamo Bucuresti", 0.560, 59.5, "Under", "EHF CL Men 2026/27 Group E official table (ehfcl.eurohandball.com): #3 Dinamo Bucuresti 1-1-3 (134:145, 3 pts; beat Aarhus 37:23 in R5 & beat Montpellier in R1) at eliminated #4 Montpellier Handball 1-0-4 (150:165, 2 pts) + OLBG 1/1 Dinamo"),
}

# Verified outright field-size priors (Dirichlet shrinkage toward 1/F)
OUTRIGHT_FIELDS = {
    "GLF-101904": (120, 20, "Seamus Power", 0.125, "PGA Tour Butterfield Bermuda Championship official 120-man Port Royal field + OLBG 5/22 tips"),
    "GLF-101908": (96, 24, None, None, "JGTO official Fortinet Players Cup 96-player field prior"),
    "GLF-101911": (72, 16, None, None, "Senior tour 72-player field prior"),
    "GLF-101912": (120, 20, None, None, "Sunshine Tour 120-player field prior"),
    "GLF-101903": (72, 16, None, None, "PGA Tour Champions Stifel Charity Classic 72-player Schwab Cup Playoffs field prior"),
    "MTR-913": (22, 12, "Max Verstappen", 0.2727, "FIA Formula 1 22-car Austin COTA grid prior + 12/34 OLBG win tips (3 experts) re-read 2026-10-22T21:00Z"),
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
    # Some listings label a side with a bracketed qualifier, e.g. "Kosovo (W)" for Kosovo W.
    # Drop the brackets before matching so the side is not silently left unresolved and the
    # model falls back to a generic home-side prior it cannot justify from the source.
    plain = re.sub(r"[()]", "", clean).strip()
    if plain and (home.lower() in plain or plain in home.lower()):
        return home
    if plain and (away.lower() in plain or plain in away.lower()):
        return away
    return None


def main() -> None:
    matches = json.loads((DATA / "matches.json").read_text())
    preds_doc = json.loads((DATA / "predictions-olbg.json").read_text()) if (DATA / "predictions-olbg.json").exists() else {"predictions": []}
    # Retractions recorded in data/live_overrides.json also remove the written piece, so a
    # withdrawn fixture cannot keep a HIGH write-up after its row leaves the board.
    _ov_path = DATA / "live_overrides.json"
    _ov = json.loads(_ov_path.read_text()) if _ov_path.exists() else {"withdrawn": []}
    _retired = {str(w.get("match_id") or w.get("olbg_event_id")) for w in _ov.get("withdrawn", [])}
    _live = {m["id"] for m in matches}
    # Hand-written pieces live in data/patches/*.json and are re-applied on every run, and they
    # are merged *before* the prune and before the HIGH-certification set is derived: they cannot
    # be re-derived from the OLBG harvest, and a piece that only lands after this point cannot
    # certify its own row. Regenerating without this step silently dropped them on any rebase.
    _pdir = DATA / "patches"
    if _pdir.is_dir():
        _idx = {p["match_id"]: i for i, p in enumerate(preds_doc.get("predictions", []))}
        for _ppath in sorted(_pdir.glob("*.json")):
            for _piece in json.loads(_ppath.read_text()):
                _mid = _piece.get("match_id")
                if not _mid or _mid in _retired or _mid not in _live:
                    continue
                if _mid in _idx:
                    preds_doc["predictions"][_idx[_mid]] = _piece
                else:
                    _idx[_mid] = len(preds_doc["predictions"])
                    preds_doc["predictions"].append(_piece)

    preds_doc["predictions"] = [p for p in preds_doc.get("predictions", [])
                                if p["match_id"] not in _retired and p["match_id"] in _live]
    # Only a piece explicitly published as HIGH certifies a HIGH row. A piece relabelled
    # "analysis" (for example after the source's consensus moved) must not keep the row HIGH.
    high_verified_ids = {p["match_id"] for p in preds_doc.get("predictions", [])
                         if str(p.get("confidence") or p.get("status") or "").lower() == "high"}
    if _retired or len(preds_doc["predictions"]) != len(json.loads((DATA / "predictions-olbg.json").read_text())["predictions"]):
        # Persist the prune before sync_predictions re-reads the file.
        (DATA / "predictions-olbg.json").write_text(json.dumps(preds_doc, indent=2, ensure_ascii=False) + "\n")

    out = []
    for m in matches:
        mid = m["id"]
        sport = m["sport"]
        home, away = m["home"], m["away"]
        won, tot = m["olbg_tips_won"], m["olbg_tips_total"]
        p_raw = round(won / tot, 4) if (won is not None and tot) else None
        carried = bool(m.get("row_notes") and ("carried from" in m["row_notes"] or "supplementary evening capture" in m["row_notes"]))
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
            resolved_side = resolve_team_side(pick, home, away)
            p_home = p_pick if resolved_side == home else round(1.0 - p_pick, 4)
        else:
            # Must stay identical to tools/build_dataset.py OTHER_MARKETS (minus the blank label,
            # which is a Gaelic Football row that renders no market at all) and to
            # scripts/model.py NON_WIN_CONSENSUS_MARKETS. tests/test_audit_6327cf90.py fails the
            # build if they drift: a label present in one set and absent from another is classified
            # by fallback rather than by design, and a totals consensus whose text happened to
            # contain a player name would be reused as a match-winner probability. See FL-157.
            _non_win = {"Set Score", "Set Betting", "Handicap", "Handicap 2-way", "Match Handicap",
                        "Pointspread", "Puck Line", "Total Legs", "Game Totals", "Total Games", "Games Won", "1st Set Winner", "Man Of The Match", "Top Team1 Batsman"}
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
            basis = ("Sport home-court baseline (non-winner OLBG consensus excluded)" if m.get("olbg_market") in _non_win else "Uncalibrated even prior + sport home-court assumption; no readable OLBG tip split" if p_raw is None else "OLBG tip split shrunk with Beta(2,2) prior + sport home-court logit adjustment")

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
                and not carried and in_window and not ko_passed and p_pick >= 0.55):
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
