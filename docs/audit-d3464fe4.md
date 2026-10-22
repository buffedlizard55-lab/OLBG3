# Line-by-Line Engineering, URL & Official-Source Audit — `session-d3464fe4` (`2026-10-22T08:30Z`)

## 1. Executive Summary

During our independent live re-harvest (`2026-10-22T08:27Z–08:30Z`) across all **15 in-scope OLBG sports** and line-by-line governing-body verification across all published rows, predictions, and URLs, we uncovered **seven high-severity defect classes** — four of which had escaped every prior session and every automated validator in CI:

1. **43 Soft-404 `"No tips found."` OLBG Event URLs in `data/matches.json` (and corresponding `07:25Z` rows on `/`):**
   - `OLBG.com` returns **HTTP `200 OK`** with an empty shell (`"No tips found."`) whenever `<Sport>/<Category>/<Subcategory>/<Exact_Slug>` disagrees by even one character (`_vs_` instead of `_v_` in Snooker, omitted `<Sport>/` prefix, or guessed taxonomy folders like `International/Northern_Ireland_Open`, `UK_Racing/Kinsley`, `WTA/WTA_Guangzhou_Open`, `ATP/ATP_Almaty_Open`, `ATP/ATP_Lyon`, `Brazil/NBB`, `Other/Korea_KBL`, `Sweden/SHL`, `Brazil/Superliga_Women`, `Italy/SuperLega`).
   - Verified empirically live against `OLBG.com`:
     - **Broken (`main`):** `https://www.olbg.com/betting-tips/International/Northern_Ireland_Open/Kyren_Wilson_vs_Pang_Junxu/8?event_id=9940` -> `"No tips found."`
     - **Repaired (`08:30Z` harvest):** `https://www.olbg.com/betting-tips/Snooker/All_Snooker/All_Events/Kyren_Wilson_v_Pang_Junxu/8?event_id=9940` -> live multi-market page (`Kyren Wilson 6/11`, `Pang Junxu +1.50 3/4`, `Pang Junxu 4-2 3/6`).
   - All **43** broken paths and slugs are repaired verbatim in `docs/harvest-20261022-0830z.tsv`.

2. **Hidden `+24h` Capture-Date Shift on Root `data/events.json` (`140+` rows including Live In-Play `HIGH` Picks!):**
   - In `data/events.json`, all `2026-10-21` Harvest #1 rows carry `"captured_at": null` with un-updated relative labels (`"Today HH:MM"` / `"Tomorrow HH:MM"`).
   - When PR #73 advanced `CAPTURE_DATE` from `date(2026, 10, 21)` to `date(2026, 10, 22)` in `scripts/board_dates.py`, `resolve_kickoff_utc()` shifted **every `2026-10-21` row forward by `+24 hours`**:
     - Completed `21 Oct` matches (`BKB-01..18`, `IHO-01..07`, `SNK-01..06`, `TEN-01..15`, etc.) became fake `2026-10-22` pre-match fixtures (listing `SNK-01` `Liam Davies vs Pang Junxu` R32 on the very same `22 Oct` card as `SNK-07` `Kyren Wilson vs Pang Junxu` R16!).
     - Live in-play `22 Oct 08:00Z` matches (`CRK-06` `Namibia v Ireland` — verified live on `icc-cricket.com` ticker at `IRE 77/1 (15.4 ov)` — and `CRK-07` `England v Sri Lanka` — verified live at `ENG 37/0 (7.0 ov)` — plus `TEN-23` `Machac v Khachanov` and `TEN-24` `Eala v Shnaider`) were shifted to **`2026-10-23`**, causing even `kickoff_started` gates to treat live in-play cricket matches as tomorrow's pre-match `HIGH` picks!
   - **Fix for Phase 2 (`task-38`):** Explicitly stamp `"captured_at": "2026-10-21T07:05:00Z"` on Harvest #1 rows and `"2026-10-22T07:25:00Z"` / `"2026-10-22T08:30:00Z"` on `22 Oct` rows in `data/events.json` so `resolve_kickoff_utc()` computes true UTC start times for every row on the board, stepping down `CRK-06`, `CRK-07`, `TEN-23`, and `TEN-24` cleanly from `HIGH` to `analysis`.

3. **Same-Day Minute-Precision `started` Gate on `/olbg/` (`CRI-188828`, `CRI-188829`, `TEN-902110`, `TEN-902072`):**
   - `tools/originate.py` on `main` only checked `m["date_iso"] < BUILD_DATE.isoformat()`, allowing already-started morning matches on `2026-10-22` to remain `high`. Sibling `session-5a9926e5` independently implemented `match_clock()` in `tools/originate.py`; in Phase 2 (`task-38`) we preserve `5a9926e5`'s implementation and apply it at `SNAPSHOT_UTC = 2026-10-22T08:30:00Z` so `CRI-188828`, `CRI-188829`, `TEN-902110`, and `TEN-902072` step down automatically to `analysis` on `/olbg/` as well.

4. **Crossed Volleyball Event IDs (`36994..36997` SuperLega & `37000..37003` CBV Superliga Women) + Wrong SHL Puck Line Sign (`199906`):**
   - Live `OLBG.com` `/Volleyball/21` proves `36994` = `Trentino vs Cisterna`, `36995` = `Civitanova vs Padova`, `36996` = `Monza vs Verona`, `36997` = `Perugia vs Pordenone`, `37000` = `Paulistano/Barueri vs Minas`, `37001` = `Brasilia vs Sesc RJ Flamengo`, `37002` = `Mackenzie vs Osasco`, `37003` = `Abel-Moda Brusque vs Praia Clube` (corroborating `session-5a9926e5`).
   - Live `/Ice_Hockey/13` proves `199906` (`Rogle BK vs Frolunda HC`) carries `Frolunda HC -1.50` (`1/1`), not `+1.50`.

5. **Wrong KBL Match Date on Both Tracks (`BKB-23` / `536021` `Mobis Phoebus vs Changwon Sakers`):**
   - Both tracks recorded `2026-10-23`, whereas live OLBG (`Today 06:00` EDT) AND official KBL (`https://www.kbl.or.kr/match/schedule`: `10.22 (Thu) 19:00 KST` = `2026-10-22T10:00Z`, Ulsan Dongcheon Gymnasium) confirm the game is **today (`2026-10-22`)**.

6. **Factual Captaincy Error in `CRI-188831` Prose (`Sikandar Raza` vs `Craig Ervine`):**
   - `data/predictions-olbg.json` (`CRI-188831`) referred to `"Craig Ervine's Zimbabwe"` in the 19 October 2026 ODI; official match records confirm **`Sikandar Raza`** captained Zimbabwe (`48` runs, his 10th ODI as captain; Ervine batted #5 non-captain).

7. **100% (`206/206`) Non-Greyhound Match Governing-Body Verification + 100% (`9/9`) Golf + **13th Sport (`Rugby League`)** Live `HIGH` + Fresh `08:30Z` Fixtures:**
   - **New live OLBG fixtures captured & officially verified:**
     - `ICH-199937` / `IHO-14`: `New York Rangers @ Toronto Maple Leafs` (`api-web.nhle.com/v1/schedule/2026-10-22`, Game `2026020155`, `23:00Z`, Scotiabank Arena; closes `FL-042`).
     - `TEN-902117` / `TEN-38`: `Sara Bejlek vs Marie Bouzkova` (`wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf`, WTA 500 Ningbo QF).
     - `TEN-902133` / `TEN-36`: `Corentin Moutet vs Tommy Paul` (`atptour.com/en/scores/current/lyon/496/results`, ATP 250 Lyon QF).
     - `CRI-188831` / `CRK-11`: `Afghanistan vs Zimbabwe` (`icc-cricket.com/matches/274659/afghanistan-vs-zimbabwe`, UAE ODI Tri-Series).
   - **Upgraded rows to primary governing-body sources (`HTTP 200`):**
     - `TEN-37` / `TEN-902107`: `Talia Gibson vs Ashlyn Krueger` (`wtafiles.wtatennis.com/pdf/draws/2026/405/MDS.pdf` — OLBG mislabelled WTA Osaka as `'WTA Guangzhou Open'`).
     - `BKB-03` (`535966`) & `BKB-23` (`536021`): `kbl.or.kr/match/schedule`.
     - `GLF-07` (`jgto.org/en/`) & `GLF-09` (`sunshinetour.com/schedule?code=RWAO&id=226S`) -> **100% (`9/9`) Golf verified**.
     - `MTR-03` (`912` `F1 World Championship 2026` -> `formula1.com/en/results/2026/drivers`, Round 19 of 24 live).
     - `RGL-01` (`State of Origin 2027` -> `nrl.com` official 2027 release) & `RGL-03` (`2801600` `NRL 2027 Grand Final Winner` -> `nrl.com` 2026 Finals Series & Grand Final releases, `Penrith Panthers` at `7.18 / +618`).
     - `GAF-01` / `GFA-3530` (`St Finbarrs vs Nemo Rangers`, `2026 Cork Premier SFC Final` -> `gaacork.ie` official event schema `"startDate":"2026-10-25T16:00:00+00:00"` + complete 10-game 2026 Cork PSFC group & knockout results).
     - **7 of 8** OLBG tournament outrights (`182606`, `187184`, `187503`, `187504`, `26023`, `32338`, `609013`), plus verified live `<12h:mm>_<Track>` Greyhound slugs on `689570..689604` (dropping already-closed `689613`), keeping `188350` (`T20 Blast 2027`), `3327` (`All-Ireland SFC 2027`), `RGL-02` (`Super League 2027`), and `GRY-*` strictly `unverified` with zero inferred values and forensic `+1yr` rollover proof.

## 2. Phase 2 Integration Summary & Live Board Metrics (`task-38`, `2026-10-22T09:58Z`)

Following completion of PRs `#78`, `#79`, and `#80` on `main` (`3b9cedd`) and expiry of the `>60m` idle window across earlier unmerged claims, Phase 2 integrated all `08:30Z`–`09:42Z` live OLBG and governing-body verifications across both dashboard tracks with **zero custom formula overrides** and **100% deterministic CI reproducibility**:

- **Root Dashboard (`/`):**
  - `230` rows (`202` two-sided fixtures **`100% verified` (`202/202`)** on primary `official` `[193]` and `club-official` `[9]` hosts + `28` priced gap-sport rows **`100% priced` (`28/28`)**, including `DRT-17` `Luke Humphries` European Championship Outright at `6.07` / `+507`).
  - **`17` live in-band `HIGH` picks (`-250..+10000` / `1.40..101.00`, `<70%` implied probability)** across **11 sports**: `Baseball` (`BSB-01`), `Basketball` (`BKB-20, 21, 22, 26`), `Cricket` (`CRK-10`), `Ice Hockey` (`IHO-10` `Brynäs IF` `1.50 / -200` & `IHO-12` `Frölunda HC` `1.60 / -167`, both verified live on `shl.se` Game Center for `22 Oct 19:00 CEST = 17:00 UTC`), `Darts` (`DRT-17` `Luke Humphries` `6.07 / +507`), `Handball` (`HBL-15` `Pick Szeged`), `Volleyball` (`VOL-27, 28, 29` un-crossed SuperLega `Perugia`, `Civitanova`, `Monza`), `Rugby Union` (`RGU-14` `Leinster`), `Golf` (`GLF-02` `Seamus Power`), `Motor Racing` (`MTR-01` `Max Verstappen`), and `Gaelic Football` (`GAF-01` `St Finbarrs` `1.62 / -161`), plus `50` additional `analysis` write-ups (`67` total written pieces including `IHO-14` `NY Rangers @ TOR Maple Leafs` refreshed from live `api-web.nhle.com/v1/standings/2026-10-22` and `RGL-03` `Penrith Panthers`).
- **Live OLBG Lines Board (`/olbg/`):**
  - `275` originated lines across all **15 in-scope sports** (`0` excluded sports, `0` soft-404 URLs), **`22` live in-band `high` picks across 12 sports** (`Baseball`, `Basketball`, `Cricket`, `Ice Hockey`, `Darts`, `Handball`, `Volleyball`, `Rugby Union`, `Rugby League` [`RGL-2801600` `Penrith Panthers` `7.18 / +618`], `Golf`, `Motor Racing`, `Gaelic Football`), `47` written predictions/analyses, and `76` documented items on `flagged.html` / `/olbg/flagged.html`.
- **Full Validation Suite:** `59` unit & integration tests passing (`0.04s`), `check_board.py` (`0` violations), `tools/check_site.py` (`All checks passed`), `check.py` (`PASS`), and `check_links.py` (`pages=85 local_links_checked=1529 broken=0`).
