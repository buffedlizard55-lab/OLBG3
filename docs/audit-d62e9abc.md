# 15-Sport Line Origination, Written-Pick & Official-Source Verification Audit — `session-d62e9abc`

- **Session / Branch:** `session-d62e9abc` on `arena/d62e9abc-olbg3`
- **Publication Clock Evaluated:** `2026-10-26T20:23:00Z` (recomputed dynamically from `data/publication.json`)
- **Primary OLBG Capture:** `data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv` (captured `2026-10-26T20:20:26Z`, 18/18 endpoints HTTP 200, **142 primary entries**)
- **Combined Audited Inventory:** **890 rows** across all **15 in-scope sports** (**523** OLBG-track match/line rows in `data/matches.json` + `data/lines.json`, and **367** root-track rows in `data/events.json` [319 fixtures] + `data/gap_sports.json` [48 outright/race rows])
- **Standalone Dashboard Published:** [`audit-d62e9abc.html`](https://buffedlizard55-lab.github.io/OLBG3/audit-d62e9abc.html)
- **Machine-Readable Audit Receipt:** [`data/audit-d62e9abc.json`](https://buffedlizard55-lab.github.io/OLBG3/data/audit-d62e9abc.json)

---

## 1. Executive Summary & Obvious Pick Locations

Where the picks are located on the live GitHub Pages site:
- **Standalone 15-Sport Verification & Executive Summary Dashboard (this session):** <https://buffedlizard55-lab.github.io/OLBG3/audit-d62e9abc.html>
- **Main Landing & Shortlist:** <https://buffedlizard55-lab.github.io/OLBG3/index.html> and <https://buffedlizard55-lab.github.io/OLBG3/today.html#shortlist>
- **All Written Predictions:** <https://buffedlizard55-lab.github.io/OLBG3/predictions.html> and <https://buffedlizard55-lab.github.io/OLBG3/olbg/predictions.html>
- **Originated Lines & Markets:** <https://buffedlizard55-lab.github.io/OLBG3/lines.html> and <https://buffedlizard55-lab.github.io/OLBG3/olbg/picks.html>
- **Flagged for Review Register:** <https://buffedlizard55-lab.github.io/OLBG3/flagged.html> and <https://buffedlizard55-lab.github.io/OLBG3/audit-d62e9abc.html#flagged-review>

### Certified Live HIGH-Confidence Picks (Inside `-250..+10000` US Odds & `<70%` Chalk Cap)

| Row ID | Sport | Match | Official Start (UTC) | Selection | Originated Win Line (Dec / US) | Handicap Line | Total Line | Word Count | Official & OLBG Sources |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| `ICH-200101` | Ice Hockey | LA Kings @ NY Rangers | `2026-10-26T23:00:00Z` | **NY Rangers to win — money line** | `1.45` (`-222`, p=0.6565) | NY Rangers -0.5 goals @ 1.91 | Over 6.5 goals @ 1.91 | 95 | [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG Event](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/LA_Kings_@_NY_Rangers/13?event_id=200101) |
| `ICH-200102` | Ice Hockey | DET Red Wings @ EDM Oilers | `2026-10-27T01:30:00Z` | **EDM Oilers to win — money line** | `1.42` (`-238`, p=0.6713) | EDM Oilers -1.0 goals @ 1.91 | Over 6.5 goals @ 1.91 | 98 | [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG Event](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/DET_Red_Wings_@_EDM_Oilers/13?event_id=200102) |

### Additional Upcoming Official-Source Written Predictions (26–29 Oct 2026)

1. **5 Upcoming NHL Medium-Confidence Written Analyses (27–28 Oct 2026):**
   - `ICH-200103` (`TOR Maple Leafs @ CGY Flames`, `2026-10-27T00:30:00Z`): **TOR Maple Leafs to win — money line** at `1.80` (`-125`, p=0.5277), 96 words — [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/TOR_Maple_Leafs_@_CGY_Flames/13?event_id=200103)
   - `ICH-200104` (`BOS Bruins @ CAR Hurricanes`, `2026-10-28T00:00:00Z`): **CAR Hurricanes to win — money line** at `1.89` (`-112`, p=0.5022), 96 words — [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/BOS_Bruins_@_CAR_Hurricanes/13?event_id=200104)
   - `ICH-200105` (`FLA Panthers @ WPG Jets`, `2026-10-28T00:00:00Z`): **FLA Panthers to win — money line** at `1.80` (`-125`, p=0.5277), 97 words — [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/FLA_Panthers_@_WPG_Jets/13?event_id=200105)
   - `ICH-200111` (`NJ Devils @ DAL Stars`, `2026-10-28T00:00:00Z`): **DAL Stars to win — money line** at `1.79` (`-127`, p=0.5300), 99 words — [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/NJ_Devils_@_DAL_Stars/13?event_id=200111)
   - `ICH-200112` (`NY Islanders @ NSH Predators`, `2026-10-28T00:00:00Z`): **NY Islanders to win — money line** at `1.87` (`-115`, p=0.5092), 95 words — [NHL Schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) · [NHL Standings](https://api-web.nhle.com/v1/standings/2026-10-26) · [OLBG](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/NY_Islanders_@_NSH_Predators/13?event_id=200112)

2. **8 Upcoming EHF Men's Champions League Round 6 Written Predictions (28–29 Oct 2026):**
   - `HAN-12130` (`HC Vardar vs MT Melsungen`, `2026-10-28T17:45:00Z`): **MT Melsungen to win — money line** at `1.54` (`-185`, p=0.6184) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/HC_Vardar_vs_MT_Melsungen/20?event_id=12130)
   - `HAN-12138` (`Wisla Plock vs Nantes`, `2026-10-28T17:45:00Z`): **Orlen Wisla Plock to win — money line** at `1.64` (`-156`, p=0.5809) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/Wisla_Plock_vs_Nantes/20?event_id=12138)
   - `HAN-12132` (`KS Kielce vs Kolstad`, `2026-10-28T19:45:00Z`): **KS Kielce to win — money line** at `1.68` (`-147`, p=0.5646) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/KS_Kielce_vs_Kolstad/20?event_id=12132)
   - `HAN-12134` (`PSG Handball vs Aalborg Handbold`, `2026-10-28T19:45:00Z`): **Aalborg Handbold to win — money line** at `1.71` (`-141`, p=0.5562) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/PSG_Handball_vs_Aalborg_Handbold/20?event_id=12134)
   - `HAN-12136` (`SC Magdeburg vs HC Kriens Luzern`, `2026-10-28T19:45:00Z`): **SC Magdeburg to win — money line** at `1.68` (`-147`, p=0.5646) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/SC_Magdeburg_vs_HC_Kriens_Luzern/20?event_id=12136)
   - `HAN-12128` (`Fuchse Berlin vs RK Partizan`, `2026-10-29T17:45:00Z`): **Fuchse Berlin to win — money line** at `1.68` (`-147`, p=0.5646) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/Fuchse_Berlin_vs_RK_Partizan/20?event_id=12128)
   - `HAN-12129` (`GOG vs Sporting CP`, `2026-10-29T17:45:00Z`): **Sporting CP to win — money line** at `1.65` (`-154`, p=0.5761) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/GOG_vs_Sporting_CP/20?event_id=12129)
   - `HAN-12133` (`Montpellier vs Dinamo Bucuresti`, `2026-10-29T19:45:00Z`): **Dinamo Bucuresti to win — money line** at `1.70` (`-143`, p=0.5582) — [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) · [OLBG](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/Montpellier_vs_Dinamo_Bucuresti/20?event_id=12133)

---

## 2. 15-Sport Coverage & Line Origination Summary

| Sport | Oct 26 Capture Rows | OLBG Track Rows | Root Track Rows | Originated Markets (Win / Hcap / Total) | Confidence Split (H / M / L) | Written Predictions | Live HIGH vs 5 Target | Official Governing-Body Reference |
| --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| **Golf** | 3 | 3 | 6 | 3 / 0 / 0 (plus 6 root outrights) | 0H / 3M / 0L | 1 | 0/5 (shortfall 5) | [PGA Tour Schedule](https://www.pgatour.com/schedule) |
| **Volleyball** | 15 | 62 | 35 | 62 / 62 / 62 | 0H / 9M / 53L | 18 | 0/5 (shortfall 5) | [Lega Pallavolo Serie A](https://www.legavolley.it/calendario/?idCampionato=999) |
| **Rugby Union** | 13 | 39 | 26 | 37 / 37 / 37 | 0H / 3M / 36L | 11 | 0/5 (shortfall 5) | [United Rugby Championship](https://www.unitedrugby.com/) |
| **Cricket** | 17 | 30 | 20 | 28 / 0 / 0 | 0H / 4M / 26L | 5 | 0/5 (shortfall 5) | [ICC Fixtures & Results](https://www.icc-cricket.com/fixtures-results) |
| **Snooker** | 0 | 3 | 12 | 3 / 3 / 3 | 0H / 0M / 3L | 3 | 0/5 (shortfall 5) | [World Snooker Tour](https://www.wst.tv/matches/) |
| **Darts** | 2 | 21 | 21 | 21 / 19 / 19 | 0H / 2M / 19L | 9 | 0/5 (shortfall 5) | [PDC Tournaments](https://www.pdc.tv/tournaments) |
| **Baseball** | 1 | 3 | 3 | 3 / 3 / 3 | 0H / 3M / 0L | 5 | 0/5 (shortfall 5) | [MLB Stats API Schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-26&endDate=2026-10-28&hydrate=team,linescore,probablePitcher) |
| **Gaelic Football** | 3 | 5 | 4 | 5 / 4 / 4 | 0H / 2M / 3L | 4 | 0/5 (shortfall 5) | [GAA Fixtures & Results](https://www.gaa.ie/fixtures-results) |
| **Greyhounds** | 8 | 128 | 36 | 128 / 0 / 0 | 0H / 0M / 128L | 0 | 0/5 (shortfall 5) | [GBGB Official Portal](https://www.gbgb.org.uk/) |
| **Tennis** | 20 | 44 | 80 | 44 / 44 / 44 | 0H / 6M / 38L | 16 | 0/5 (shortfall 5) | [WTA Official Scores](https://www.wtatennis.com/scores) |
| **Motor Racing** | 2 | 4 | 3 | 3 / 0 / 0 | 0H / 3M / 1L | 2 | 0/5 (shortfall 5) | [Formula 1 2026 Calendar](https://www.formula1.com/en/racing/2026) |
| **Handball** | 17 | 57 | 38 | 57 / 57 / 57 | 0H / 16M / 41L | 22 | 0/5 (shortfall 5) | [EHF Playing Times PDF](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) |
| **Ice Hockey** | 11 | 60 | 32 | 60 / 58 / 80 | 2H / 16M / 42L | 34 | 2/5 (shortfall 3) | [NHL Official Schedule API](https://api-web.nhle.com/v1/schedule/2026-10-26) |
| **Basketball** | 27 | 61 | 48 | 61 / 61 / 61 | 0H / 2M / 59L | 22 | 0/5 (shortfall 5) | [NBA Official Portal](https://www.nba.com/) |
| **Rugby League** | 3 | 3 | 3 | 3 / 0 / 0 | 0H / 2M / 1L | 2 | 0/5 (shortfall 5) | [NRL Official Portal](https://www.nrl.com/) |
| **TOTAL (15 Sports)** | **142** | **523** | **367** | **520 W / 348 H / 370 T** | **2H / 71M / 450L** | **154** | **2/75 (shortfall 73)** | All 15 in-scope sports verified |

---

## 3. Direct Line-by-Line Verification Against 2026-10-26 Official Captures

### A. NHL Official Schedule & Standings (`data/raw/official-20261026T2021Z/json/nhl_schedule.json` & `nhl_standings.json`)
All 7 NHL games in the October 26 capture were cross-checked digit-for-digit against the NHL API payloads fetched at `2026-10-26T20:21Z`:
- `ICH-200101` (`LA Kings @ NY Rangers`, game `2026020185`, Madison Square Garden): Official start `2026-10-26T23:00:00Z` (OLBG prints `23:07:00Z`, +7m offset). LAK `2-5-2` (`21-32` GF-GA, road `2-2-2`, L10 `2-5-2`, `L1`) vs NYR `7-5-1` (`41-36` GF-GA, home `6-0-0`, L10 `6-3-1`, `L2`).
- `ICH-200103` (`TOR Maple Leafs @ CGY Flames`, game `2026020186`, Scotiabank Saddledome): Official start `2026-10-27T00:30:00Z` (OLBG `00:37:00Z`). TOR `6-4-2` (`40-36` GF-GA, road `3-1-1`, L10 `6-2-2`, `W4`) vs CGY `4-6-0` (`23-39` GF-GA, home `3-3-0`, L10 `4-6-0`, `W3`).
- `ICH-200102` (`DET Red Wings @ EDM Oilers`, game `2026020187`, Rogers Place): Official start `2026-10-27T01:30:00Z` (OLBG `01:37:00Z`). DET `4-4-3` (`29-33` GF-GA, road `1-1-2`, L10 `3-4-3`, `L1`) vs EDM `8-2-1` (`49-34` GF-GA, home `3-2-1`, L10 `8-1-1`, `L1`).
- `ICH-200104` (`BOS Bruins @ CAR Hurricanes`, game `2026020189`, Lenovo Center): Official start `2026-10-28T00:00:00Z` (OLBG `00:07:00Z`). BOS `9-2-1` (`48-26` GF-GA, road `4-1-1`, L10 `7-2-1`, `W1`) vs CAR `9-3-1` (`51-33` GF-GA, home `2-1-1`, L10 `8-1-1`, `L1`).
- `ICH-200105` (`FLA Panthers @ WPG Jets`, game `2026020194`, Canada Life Centre): Official start `2026-10-28T00:00:00Z` (OLBG `00:07:00Z`). FLA `6-4-2` (`34-36` GF-GA, road `4-3-2`, L10 `5-4-1`, `W1`) vs WPG `4-4-3` (`27-31` GF-GA, home `2-3-1`, L10 `4-4-2`, `L1`).
- `ICH-200111` (`NJ Devils @ DAL Stars`, game `2026020193`, American Airlines Center): Official start `2026-10-28T00:00:00Z` (OLBG `00:07:00Z`). NJD `7-4-0` (`34-26` GF-GA, road `1-2-0`, L10 `7-3-0`, `W3`) vs DAL `8-2-1` (`32-20` GF-GA, home `4-2-0`, L10 `7-2-1`, `W5`).
- `ICH-200112` (`NY Islanders @ NSH Predators`, game `2026020192`, Bridgestone Arena): Official start `2026-10-28T00:00:00Z` (OLBG `00:07:00Z`). NYI `6-3-2` (`32-29` GF-GA, road `1-3-1`, L10 `5-3-2`, `W1`) vs NSH `4-3-4` (`31-35` GF-GA, home `3-2-1`, L10 `4-2-4`, `W1`).

### B. EHF Men's Champions League Round 6 Playing-Times PDF (`data/raw/cited-20261026T2022Z/pages/ehfel-eurohandball-com-media-jqal4wt0-ehfcl-men-2026-27-group-phase-playing-times-pdf.pdf`)
Decompressing FlateDecode stream 7 of the byte-faithful 218,756-byte PDF (`sha256: b681d6ba3ebd764018813802f54f9ad2311e0f776a546253698042387f8bdb1d`, captured `2026-10-26T20:22:28Z`) confirms all 12 Round 6 fixtures under `GROUP ROUND 6 DATE TO TIME CET`:
- **Wednesday 28.10.2026 18:45h CET (`17:45 UTC`):** `HC Vardar 1961 vs MT Melsungen` (`HAN-12130`), `Orlen Wisla Plock vs HBC Nantes` (`HAN-12138`).
- **Wednesday 28.10.2026 20:45h CET (`19:45 UTC`):** `FC Porto vs One Veszprém HC` (`HAN-12127` — conflicts with OLBG `17:45Z`), `RK Celje Pivovarna Lasko vs HC Zagreb` (`HAN-12135`), `Paris Saint-Germain Handball vs Aalborg Handbold` (`HAN-12134`), `SC Magdeburg vs HC Kriens-Luzern` (`HAN-12136`), `Industria Kielce vs Kolstad Handball` (`HAN-12132`).
- **Thursday 29.10.2026 18:45h CET (`17:45 UTC`):** `Füchse Berlin vs RK Partizan AdmiralBet` (`HAN-12128`), `IFK Kristianstad vs OTP Bank-Pick Szeged` (`HAN-12131`), `GOG vs Sporting CP` (`HAN-12129`).
- **Thursday 29.10.2026 20:45h CET (`19:45 UTC`):** `SAH Aarhus vs Barça` (`HAN-12137`), `Montpellier HB vs CS Dinamo Bucuresti` (`HAN-12133`).

### C. MLB World Series (`data/raw/official-20261026T2021Z/json/mlb_schedule.json`) & Formula 1 (`motor-racing-formula-1.txt`)
- `BSB-160795` (`MIL Brewers @ TB Rays`): Confirmed in `mlb_schedule.json` as `gamePk 849804`, `gameDate: 2026-10-27T00:00:00Z` at Tropicana Field. Originated probability `0.7569` (`1.26 / -385`) exceeds the `<70%` (`-250`) chalk cap, so it is graded `MEDIUM`.
- `MTR-914` (`Mexico City Grand Prix`) & `MTR-912` (`Formula 1 Drivers Championship 2026 Without Kimi Antonelli`): Confirmed on the official F1 2026 race calendar (`ROUND 19 Mexico 30 Oct - 01 Nov` and `ROUND 23 Abu Dhabi 04 - 06 Dec`). `MTR-914` (`Top 6 Finish: Kimi Antonelli - Yes` at `1.08 / -1205`) has no tip count on OLBG and is left unpriced.

---

## 4. Irregularities Flagged for Review (`data/audit-d62e9abc.json` & `audit-d62e9abc.html#flagged-review`)

1. **`AUD-D62-EHF-PDF-BINARY-HOLD` (`HAN-12128..HAN-12138`):** `scripts/reverify.py` skips `.pdf` binary files (`'binary source requires separate content review; clock not renewed'`), leaving 11 upcoming EHF Champions League Round 6 fixtures at `stale_source` even though the byte-faithful PDF captured at `2026-10-26T20:22:28Z` confirms all 11 CET times.
2. **`AUD-D62-HAN-12127-CLOCK-CONFLICT` (`HAN-12127`):** `FC Porto vs One Veszprem HC` on 28 Oct 2026 is listed on OLBG at `17:45 UTC` (`18:45 CET`), whereas the July 29 EHF playing-times PDF prints `20:45h CET` (`19:45 UTC`).
3. **`AUD-D62-NHL-7MIN-OFFSET` (`ICH-200101..ICH-200112`):** All 7 NHL listings on OLBG carry start times 7 minutes after the official NHL schedule API (`startTimeUTC`). Official NHL clock governs release.
4. **`AUD-D62-BSB-160795-CHALK-CAP` (`BSB-160795`):** Confirmed MLB World Series fixture (`MIL Brewers @ TB Rays`, `2026-10-27T00:00:00Z`), capped at `MEDIUM` because `p=0.7569` (`1.26 / -385`) exceeds the `<70%` (`-250`) chalk cap.
5. **`AUD-D62-CRT-188863-UNPRICED`, `AUD-D62-CRT-188871-UNPRICED`, `AUD-D62-MTR-914-UNPRICED`, `AUD-D62-CRT-188350-UNPRICED`:** Primary Oct 26 capture rows with player-prop markets (`Top Team1 Batsman`, `Man Of The Match`, `Top 6 Finish`) or missing tip counts (`T20 Blast 2027` Derbyshire `0/0`) left unpriced by design rather than inferred.
6. **`AUD-D62-DAR-32332-BAND` (`DAR-32332`):** Historical Darts piece carries stored `confidence='high'` with originated odds `-333` outside `-250..+10000` (already demoted to `status='analysis'` by the release gate).
