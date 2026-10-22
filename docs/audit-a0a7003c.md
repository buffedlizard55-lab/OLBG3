# Midday Live OLBG Harvest & Official Source Audit — `session-a0a7003c` (2026-10-22T12:30Z)

## 1. Scope & Methodology
Between `2026-10-22T12:10Z` and `2026-10-22T12:30Z`, `session-a0a7003c` executed a complete live re-harvest of `OLBG.com` across `/betting-tips` and all 15 allowed sport category and sub-league endpoints (`Tennis`, `Basketball` + `NBA`/`Other`, `Golf`, `Cricket`, `Snooker`, `Rugby_Union`, `Rugby_League`, `Baseball`, `Ice_Hockey` + `NHL`/`Other`, `Motor_Racing`, `Darts`, `Handball`, `Volleyball`, `Gaelic_Football`, `Greyhounds`), enforcing the 10-sport exclusion rule (`soccer`, `boxing`, `ufc`, `mma`, `football`, `american football`, `hurling`, `horse racing`, `cycling`, `specials` = `0` rows). Every newly posted or updated fixture and every `HIGH`-confidence selection on both published tracks (`/` and `/olbg/`) was re-verified line by line against live governing-body APIs, official tournament PDFs, and league match centres.

## 2. Empirical Proof of OLBG's Unverified Geo-Proxy Clock Rendering
During the `12:10Z`–`12:30Z` harvest, OLBG's server-rendered HTML emitted **two different timezone offsets across endpoints within the same session**:
- **UK BST (`UTC+1`)** on `/Basketball/4` (`DEN @ OKC Tomorrow 02:40`), `/Ice_Hockey/NHL/13` (`SJ @ OTT Tomorrow 00:07`, `UTA @ SEA Tomorrow 03:07`), `/Golf/5`, `/Rugby_Union/9`, `/Baseball/12` (`TB @ MIL 24 Oct 01:08`), `/Motor_Racing/14`, `/Handball/20`, and `/Greyhounds/28`.
- **US EDT (`UTC-4`)** on `/betting-tips`, `/Tennis/3`, `/Basketball/NBA/4`, `/Cricket/7` (`India W vs Zimbabwe W Tomorrow 04:30`), `/Snooker/8`, `/Ice_Hockey/Other/13`, `/Darts/15`, `/Volleyball/21` (`Sete vs Chaumont Today 14:00`), and `/Gaelic_Football/25`.

This directly validates `scripts/board_dates.py` and `scripts/release.py`: bare OLBG strings never establish kick-off timezone or start status; only explicitly sourced governing-body clocks (`data/release_checks.json` and `data/verifications.json`) may determine UTC start times.

## 3. Midday Live Harvest Delta (`docs/harvest-20261022-1215z.tsv` — 159 Live Rows)
- **24 brand-new live OLBG events captured & audited:**
  - **NHL (11 new Thu Oct 22 games on `/Ice_Hockey/NHL/13`, completing the full 12-game `api-web.nhle.com/v1/schedule/2026-10-22` slate alongside `199937`):** `199931` (`CAR @ EDM`, `01:00Z`), `199932` (`ANA @ NJ`, `23:00Z`), `199933` (`DET @ VAN`, `02:00Z`), `199934` (`FLA @ PIT`, `23:00Z`), `199935` (`MIN @ CGY`, `01:00Z`), `199936` (`NSH @ BOS`, `23:00Z`), `199938` (`LA @ NYI`, `23:30Z`), `199939` (`UTA @ SEA`, `02:00Z`), `199940` (`VGS @ STL`, `00:00Z`), `199941` (`WPG @ DAL`, `00:00Z`), `199942` (`SJ @ OTT`, `23:00Z`).
  - **Tennis (2 new WTA 250 Osaka QFs):** `902135` (`Ann Li vs Lilli Tagger`, Fri 23 Oct `11:30 JST` / `02:30Z` Center Court 1st match per `wtafiles.wtatennis.com/pdf/draws/2026/405/OP.pdf` & `405_4.pdf`) and `902134` (`Katie Boulter vs Antonia Ruzic`, Center Court 4th match `followed_by`).
  - **Cricket (1 new Women's ODI):** `188830` (`India W vs Zimbabwe W 1st ODI`, Fri 23 Oct `14:00 IST` / `08:30Z`, BCA Stadium Vadodara per `bcci.tv`; OLBG headline market is `Man Of The Match`: `S Mandhana 1/1`).
  - **Volleyball (1 new French Ligue A Masculine / Alterna VOLSTAR J3 match):** `37005` (`Sete vs Chaumont`, Thu 22 Oct `20:00 CEST` / `18:00Z`, Salle Louis Marty per `lnv.fr` & `lnv-web.dataproject.com`).
  - **Greyhounds (9 new UK afternoon/evening races):** `689614`, `689623`, `689627`, `689632`, `689636`, `689637`, `689643`, `689656` (Central Park `14:41`–`17:31 BST`) and `689696` (Newcastle `20:19 BST`) — kept unverified with blank prices per `FL-055`.
- **13 started/finished events removed since `08:30Z`:** Golf `101904` (Bermuda Championship started `10:35Z`), Tennis `902073`/`902069`/`902104`/`902103`/`902100`, Snooker `9940`/`9942`, and morning Greyhounds `689570`/`689576`/`689581`/`689584`/`689587`/`689592`.
- **Outright consensus shifts:** `101903` Stifel Charity Classic (`Stewart Cink 3/13`, 72-player Schwab Cup Playoffs field at Norwood Hills CC) and `32338` PDC European Championship (`Gerwyn Price 3/12`, `Luke Littler 2/12`, `Gian van Veen 2/12`, `Josh Rock 2/12`).

## 4. Defect & Verification Findings for Phase 2 Integration
1. **Home-ice sign bug on `ICH-199937` (`NY Rangers @ TOR Maple Leafs`):** `tools/originate.py` line 175 hardcoded `p_nyr = 0.5682` (`HIGH`) by adding `+0.15` home-ice log-odds to road team `NYR` instead of home team `TOR` (Scotiabank Arena, NHL Game `2026020155`). Re-running `nhl_model()` on verbatim `2026-10-22` standings (`NYR` `7-3-1`, `33:24` vs `TOR` `5-4-2`, `38:35`) gives `p_NYR = 0.5306` (`1.79` / `-127`), which is `< 0.55` and must be downgraded to **`MEDIUM`**.
2. **5 genuine in-band (`-250..+10000`) `HIGH` NHL picks + 1 `HIGH` French Volleyball pick:**
   - `199931` (`CAR @ EDM`): **Edmonton Oilers** `p = 0.5612`, `1.69` (`-145`)
   - `199932` (`ANA @ NJ`): **New Jersey Devils** `p = 0.5649`, `1.68` (`-147`)
   - `199933` (`DET @ VAN`): **Detroit Red Wings** `p = 0.5964`, `1.59` (`-169`)
   - `199940` (`VGS @ STL`): **Vegas Golden Knights** `p = 0.6192`, `1.53` (`-189`)
   - `199941` (`WPG @ DAL`): **Dallas Stars** `p = 0.6694`, `1.42` (`-238`)
   - `37005` (`Sete vs Chaumont`): **Chaumont** `p = 0.5628`, `1.69` (`-145`)
3. **Broken 404 URL fix:** `https://www.leinsterrugby.ie/fixtures-results/` returns HTTP `404` on `leinsterrugby.ie`; replace with verified `https://www.leinsterrugby.ie/fixtures-rugby/` in `data/verifications.json` and `data/predictions-olbg.json`.
4. **27 `/olbg/` track verification upgrades:** Cross-sync verified tier-1/tier-2 governing-body/club sources already audited in `data/official.json` (`HAN-12072..12117` [14 rows], `GFA-3531..3532` [2 rows], `ICH-199878` [1 row], `VOL-36945..36986` [8 rows], `GLF-101907/101910` [2 rows]) into `data/verifications.json`.
5. **MLB World Series Game 1 (`BSB-01` / `BSB-40120`):** Official `mlb.com/schedule/2026-10-23` now lists Milwaukee RHP **Jacob Misiorowski** vs Tampa Bay **TBD** (`8:00 PM ET` / `2026-10-24T00:00:00Z`).
