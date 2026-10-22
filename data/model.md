# Multi-Market Line Origination & Confidence Grading Specification (`OLBG3` — 2026-10-22)

## 1. Scope & Harvest Coverage
- **Current merged harvest (`data/raw/olbg-harvest-20261022T0829Z.tsv`):** Dated `2026-10-22T08:29:05Z`, carrying the 07:25Z primary rows plus fresh event-page reads for Bermuda, Stifel and Mobis–Changwon. The `/olbg/` builder chains prior immutable harvests into **270 rows** across all **15 in-scope sports**; this is not a claim of fresh Load-More or all-listing coverage.
- **Strict exclusions enforced (`0` rows included):** `soccer`, `football`, `boxing`, `ufc`, `mma`, `american football`, `hurling`, `horse racing`, `cycling`, `specials`.
- **Multi-market inspection:** In addition to top-level sport listings, individual OLBG event pages (`?event_id=...`) were audited across Basketball, Baseball, Tennis, Cricket, Darts, and Rugby Union to inspect server-rendered **Money Line / Win Match**, **Handicap / Pointspread / Run Line / Games Won**, **Game Totals / Total Legs / Total Games**, and **Tournament / Race Outrights**.

## 2. Independent Line Origination Across Markets
1. **Win Match / Money Line (`our_price_pick`, `our_us_odds_pick`, `our_price_other`):**
   - **Official Standings / Rankings / Tournament Strength Layer (`OFFICIAL_STRENGTH`):** Where governing-body standings, world rankings, and recent 2026 results are verified (`MLB`, `NBA`, `EuroLeague`, `ATP Tour`, `WTA Tour`, `ICC Cricket`, `PDC Darts`, `SHL`, `Liiga`, `URC`, `Pro D2`, `Top 14`, `EHF Champions League`, `DAIKIN HBL`), fair win probabilities `p` integrate official competition performance with Beta-shrunk tipster & tracked-expert evidence. Where official form contradicts thin `1/1` or `2/3` public splits (e.g. **5th-placed Brynäs IF at 9th-placed Örebro HK in SHL**, **Real Madrid vs Maccabi in neutral Belgrade**, **#6 seed Zizou Bergs indoors in Brussels**), our originated line overrides the crowd split.
   - **Beta-Binomial Shrinkage Fallback:** On remaining head-to-head fixtures, `p_shrunk = (k + 2) / (n + 4)` with sport-specific home-court logit shift `HOME_LOGIT[sport]`.
   - **Multi-Runner Outrights (`OUTRIGHT_FIELDS`):** Uses Dirichlet shrinkage toward `1 / F` rather than two-way `Beta(2,2)`. Every field has an independent `field_size_status`: `official` requires an official field URL; `model_input` discloses an assumption. JGTO Fortinet `96` is official; PGA Bermuda `120`, Formula 1 without-Antonelli `21`, and PDC `32` are model inputs, not verified entrant counts.
   - **Bookmaker Margin & American Odds Conversion:** `our_price = round((1 - 0.05) / p, 2)` (`5%` hold). American odds follow exact standard conversion: `-(100 / (d - 1))` for `d < 2.00` and `+((d - 1) * 100)` for `d >= 2.00`.
2. **Handicap / Pointspread / Run Line / Puck Line (`our_handicap_line`, `our_handicap_side`):**
   - Mapped via `margin = sigma_sport * Phi^-1(p_pick)` rounded to half-units (`-1.5` Run Line / Puck Line in Baseball & Ice Hockey; normal-margin spreads in Basketball, Rugby Union, Handball, Tennis games, Darts legs, Volleyball sets, Snooker frames, and Gaelic Football points).
3. **Match Totals — Over / Under (`our_total_line`, `our_total_side`):**
   - Originated across all scoring sports using verified team offensive/defensive rates plus audited OLBG event-page totals lines (`Over 6.5` runs MLB World Series Game 1, `Over 233.5` pts GSW@LAL, `Under 226.5` pts SAC@LAC, `Over 9.5` legs Noppert vs Bunting, etc.).

## 3. Focusing `HIGH` Confidence Strictly on `-250` to `+10000` Odds
- **Why trivial `>70%` chalk is excluded from `HIGH`:** A selection with fair win probability `>= 70%` prices at `<= 1.36` decimal (`-278` or shorter, e.g. `-455`, `-526`, `-667`), offering minimal actionable value and merely restating heavy market chalk.
- **Exact Odds Window Gate:**
  - `-250` American odds `= 1 + 100/250 = 1.40` decimal odds.
  - `+10000` American odds `= 1 + 10000/100 = 101.00` decimal odds.
  - Every `HIGH`-confidence pick MUST simultaneously satisfy:
    1. `competition_status == "verified"` from an official governing body / tour / federation;
    2. Live active fixture at `SNAPSHOT_UTC` (not carried from a prior day's pass and not already started);
    3. **`1.40 <= our_price_pick <= 101.00`** (`-250 <= our_us_odds_pick <= +10000`) **AND `our_pick_probability < 0.70`**;
    4. Backed by a unique `>= 30`-word human analysis naming team, player, current 2026 form, recent match history, and explicit betting selection with official source links.
  - Heavy >70% favorites (`Medvedev 1.14 / -714`, `Rybakina 1.18 / -556`, `Fritz 1.24 / -417`, `Panathinaikos ML 1.22 / -455`, `Barça 1.24 / -417`, `Magdeburg 1.23 / -435`) retain their honest calibrated probabilities and short prices and are explicitly capped at **`medium`**.
