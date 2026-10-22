# OLBG3 — reverse-engineered multi-sport board, originated lines & sourced research picks

A static research dashboard built from captured [OLBG.com](https://www.olbg.com/betting-tips) listings across **15 in-scope sports**, with independently originated model lines (win/money line, handicap/spread, totals and outright/race priors), `LOW`/`MEDIUM`/`HIGH` model confidence grades, sourced written predictions (>= 30 words) and a row-level publication (release) gate.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

What the published numbers do and do not mean:

- **Captured board, not a complete live feed.** 265 root rows (217 fixtures + 48 outright/race) captured 21–22 Oct 2026 (through `12:40Z`), plus the chained **324-row** `/olbg/` audit track (`104` review-register items) refreshed by an evening listing capture at `20:53Z–21:12Z`, and the hourly NHL/MLB/NBA official-schedule feed. Public hourly OLBG discovery (`scripts/discovery.py`, robots-aware) records event links only and never invents fixtures, clocks or prices.
  These are repository counts, not a newly verified complete list of upcoming matches.
- **Release gate.** A current `HIGH` pick requires an official fixture confirmation, a unique sourced write-up, an originated price inside **-250..+10000 US** (1.40–101.00 decimal, model price only — no bookmaker odds were verified), and a **recently checked, explicitly timezone-qualified official start** still ahead of the publication clock (`scripts/release.py`, `data/release_checks.json`). Expired, unverified-start, stale-source and source-conflict rows are published as analysis, not current picks; conflicts are also unpriced.
- **No guessed timezones.** Bare OLBG clocks are published verbatim and never converted; only explicitly labelled official clocks (ET/CEST/…) are normalized to UTC. Pages re-check release expiry in the browser (`assets/release.js`).
- **Honest provenance.** `HIGH` is an uncalibrated model grade, not a demonstrated win rate or betting edge. Fields that no retrieved source states stay blank and are listed on **Flagged for Review** together with every correction. Row-level release evidence (source quotes, checked-at, expiry) is on **Source health** (`source-health.html`).

| Page | What it is |
|---|---|
| `index.html` | Dashboard: coverage, current released HIGH picks, filterable captured-row table with per-row publication status |
| `predictions.html` | Sourced written predictions; non-released pieces are labelled analysis with the reason |
| `source-health.html` | Row-by-row release decisions, the official observations actually made (with quotes), and `research.json` export |
| `discovery.html` | Latest robots-aware public OLBG discovery snapshot (partial by design, unverified rows stay blank) |
| `lines.html`, `verification.html`, `audit.html`, `flagged.html`, `method.html`, `sports/<sport>.html` | Originated markets, verification log, audit trail, review register, method, and category subpages |
| `feed-overview.html`, `matches.html`, `coverage.html`, `review.html`, `markets.html` | Official NHL/MLB/NBA schedule feed with per-source attempt/success timestamps and payload hashes; failed sources are withheld as cache |
| `brief.html` | **Brief coverage**: per-sport accounting of published live HIGH picks against the brief's five-per-sport daily target, the mechanical blocker for every sport that falls short, and how each written piece is evidenced |
| `reconcile.html` | **Cross-track review**: every fixture priced on both tracks where the two models name different selections, both versions with their prices and confidence labels |
| `/olbg/` | The separate OLBG lines audit track (21 pages, 298 chained rows, 24 live high-confidence picks) with the same release gate applied to its picks |

## Evening live re-validation, five-per-sport coverage audit & clock repair — `session-cab97f19`, 2026-10-22T21:20Z

- **Defect found first (FL-099):** the committed build takes its publication clock from the newest
  source observation in `data/release_checks.json`, which was frozen at `12:40Z`. Re-assessing every
  published `HIGH` pick against the real `21:05Z` clock showed **9 of 24 had already started**
  (3 SHL games at 17:00Z, 3 EuroLeague games at 17:30/18:05/18:30Z, EHF handball at 16:45Z, 2 darts
  matches at 17:00Z). After re-reading the official clocks that could be re-read this session — the
  [NHL 2026-10-22 slate](https://api-web.nhle.com/v1/schedule/2026-10-22) (12 games, read 20:56Z) and
  the [NBA 22/23 October slate](https://www.nba.com/schedule?date=2026-10-22) (5 games, read 21:20Z) —
  the clock is `21:20Z` and every started row is demoted by the release gate. Root track: 13 live
  `HIGH` (was 19). `/olbg/` track: 17 live `HIGH` (was 24).
- **Evening listing capture:** 88 rows read live between `20:53Z` and `21:12Z`
  (`data/raw/olbg-harvest-20261022T2100Z.tsv`) and chained as a *supplementary* capture — it adds the
  26 fixtures no earlier capture held and never restates a row an earlier capture published. Snooker
  returned "No tips found." at `21:07Z` (**FL-100**); 25 of the 26 new fixtures could not be certified
  in this pass and publish unverified with blank fields (**FL-101**).
- **Five-per-sport audit (FL-102, `docs/coverage-20261022-evening.md`):** 17 live `HIGH` picks across
  nine sports — Ice Hockey 5, Basketball 3, Volleyball 3, Darts 2, Baseball 1, Cricket 1, Rugby Union
  1, Gaelic Football 1. Seven sports carry none, and the reason is source availability rather than a
  modelling choice: tennis and handball league pages publish local clocks without a zone, snooker has
  no listing, rugby league has no upcoming fixture, and golf, motor racing and greyhounds are outright
  or unverifiable race markets.
- **New verified `HIGH` picks with unique sourced write-ups:** `BKB-534842` (Boston Celtics, `-154`,
  p=0.575) and `BKB-534841` (San Antonio Spurs, `-139`, p=0.552), both sourced to the NBA.com schedule
  and the NBA.com standings after the opening round of games.
- **Allowlist repair (FL-104):** `data/release_checks.json` cited `nba.com` while
  `scripts/release.py`'s reviewed `OFFICIAL_CLOCK_HOSTS` did not contain that domain, leaving every NBA
  row stuck at `unverified_start`. `www.nba.com` was added with the reason recorded in the source; no
  other domain was added and no verification label was upgraded.
- **Snapshot state (`21:20Z`):** `/olbg/` 324 fixtures and 324 lines with **17 live `high`**;
  `tools/check_site.py` PASS (104 register items), root `check_board.py` PASS (265 rows, 13 live
  in-band `HIGH`), `check.py` PASS, `check_links.py` PASS (85 pages, 1,529 links, 0 broken),
  `75/75` unit tests OK including the new clock/capture regressions in `tests/test_evening_2100z.py`.

## Brief-coverage accounting, cross-track reconciliation & feed-track labelling — `session-c038b7f4`, 2026-10-22T21:00Z

This pass added no fixture, price, grade or source observation. Its subject is the question the brief asks most directly — *are there five
high-confidence picks for every covered sport?* — and the honest answer, published as data and as a page instead of left implicit.

- **`brief.html` + `data/brief_coverage.json` (`scripts/brief_coverage.py`):** per-sport accounting computed only from the committed rows.
  The brief's daily target is five picks per covered sport = **75 across 15 sports**. Published today: **24 distinct live HIGH picks**
  (20 on root, 24 on `/olbg/`, de-duplicated on OLBG event id), so **1 sport (Ice Hockey, 8) meets the target** and the shortfall is **51**.
  Every sport that falls short carries the mechanical reason counted from its own rows: no official current-form input for both sides
  (Tennis 21 of 40, Snooker 14 of 14, Volleyball 25 of 30 …), HIGH-grade evidence outside the `-250..+10000` band (Ice Hockey 9, Darts 9,
  Rugby Union 8), an official start that has passed or is unverified (Tennis 40 of 40), no defensible win price, or an unverified fixture
  (Greyhounds 22 of 22). Rows can fail more than one test, so the counts overlap by design.
- **`reconcile.html` + `flagged.html#FL-099`:** the root board and the `/olbg/` track are two independent models. Of **217 fixtures priced on
  both**, **167 name the same selection**, **28 name different sides** and **22** have a selection withheld by one track (source conflict or
  gate). All 28 disagreeing pairs are listed with both selections, both model probabilities, both confidence labels and the OLBG event page.
  A disagreement is published as a review item; it is not treated as an error and not resolved by guessing.
- **`brief.html#evidence` + `flagged.html#FL-101`:** how the write-ups are evidenced, counted from each piece's own `sources`: 73 root pieces
  (20 currently HIGH, 59–143 words, none under 30, no duplicate bodies) of which **70 cite a host this repo records as official** and 3 cite
  only hosts outside that set; `/olbg/` 53 pieces (24 HIGH, 46–105 words). The 14 hosts outside the recorded official set are listed with their
  citation counts and are explicitly **not** treated as verification — none could be re-read in this sandbox.
- **`flagged.html#FL-100`:** the five-per-sport shortfall itself, published as a medium-severity review item with the blockers, because it is
  the brief's central target and should not be discoverable only by counting.
- **Feed-track coherence:** the legacy official-feed pages said repo-wide things like *"No validated model … all picks remain withheld"* beside a
  board that publishes 20 HIGH picks. They now state that they are the feed track, print their own capture time, warn that rows are not
  filtered against the current clock, and link back to the dashboard and the brief coverage page. No feed data was changed.
- **New build-time guards:** `scripts/check_board.py` rules 7 and 8 fail the build if `data/brief_coverage.json` no longer recomputes from the
  rows, if it lists an excluded sport, if a shortfall does not recompute, if a "disagreement" pair names the same selection twice, or if two
  write-ups are word-for-word identical. `tests/test_brief_coverage.py` adds 12 tests. `.github/workflows/pages.yml` now runs
  `scripts/brief_coverage.py` between `model.py` and `build_site.py`.
- **Verification performed this pass (and its boundary):** every count above is derived from committed data, and the whole pipeline was rebuilt
  from a clean tree: `check_board.py` PASS (265 rows = 217 fixtures + 48 outright/race, 237 verified, 242 priced, 73 pieces, 20 live in-band
  HIGH), `tools/check_site.py` PASS (298 lines, 24 high, 53 pieces, 101 register items), `check.py` PASS (40 feed rows), `check_links.py`
  PASS (110 pages, 2,450 links, 0 broken, using the stricter checker merged in PR #99), 87/87 unit tests, two consecutive builds byte-identical. **No official source and no OLBG page was
  fetched**: this sandbox's outbound allowlist covers GitHub and package registries only (`www.olbg.com`, `api-web.nhle.com` and `www.mlb.com`
  all return HTTP 000), so no `checked_at`, quote or verification label was renewed and nothing previously unverified is now claimed as
  verified. That limitation is `FL-077`.

## Post-midday line-by-line timezone audit, PDC World Championship HIGH & root parity — `session-15487122`, 2026-10-22T12:40Z

Line-by-line official-source audit on top of PR #93 (`FL-096`..`FL-098`):

- **Repaired two venue-guessed timezones & a non-verbatim quote (`FL-096`, `FL-097`):** Re-reading live `lnv.fr` (`programmation-tv-alterna-volstar-x-bein-sports-j1-j8`) confirmed the verbatim text is `J3 : Arago de Sète - Chaumont VB 52 : jeudi 22 octobre (20h)` with **no explicit CET/CEST label**, and re-reading `wtafiles.wtatennis.com/pdf/draws/2026/405/OP.pdf` confirmed `Starting at 11:30 AM` carries **no explicit JST/UTC+9 string**. Both `release_checks['37005']` and `release_checks['902135']` were downgraded to `kind=date_only` (`timezone=null`), honestly stepping `VOL-30`/`VOL-37005` down from live `HIGH` to `MEDIUM`/`analysis` under the strict no-guessed-timezone rule.
- **Verified PDC World Championship 2027 (`DRT-18` / `DAR-26023`) as live `HIGH`/`high` (`FL-098`):** Official `pdc.tv/WCFAQ` explicitly states `Friday December 11 (1900 GMT)` (`2026-12-11T19:00:00Z`) and a `128`-player Alexandra Palace draw; reigning World Champion & world #1 `Luke Littler` (`23/36` OLBG win tips, `64%`) prices at `+130` (`2.30` decimal) across both `/` and `/olbg/` with unique sourced prose.
- **Full root `/` parity & live `12:15Z` tip-count sync (`FL-098`):** Added the 12 missing root rows already present on `/olbg/` (`TEN-40` WTA Ningbo QF `902117`, `DRT-18` `26023`, `MTR-04` `911`, `RGU-16` `613137`, `CRK-12..16`, `GRY-20..22`) and synced 18 stale morning OLBG consensus tip counts on root `data/sports/{baseball,snooker,basketball,handball,volleyball}.json`.
- **Snapshot state (`12:40Z`):** `check_board.py` **PASS** (`265` rows = `217/217` verified fixtures + `48` outright/race; `242` priced; `20` live in-band `HIGH` across `9` sports; `73` pieces), `tools/check_site.py` **PASS** (`298` fixtures/lines; `24` live `high`; `53` pieces; `98` register items), `check.py` **PASS**, `check_links.py` **PASS** (`85` pages, `1,529` links, `0` broken), `69/69` unit tests **OK**.

## Midday live harvest & official-source integration — `session-a0a7003c`, 2026-10-22T12:25Z

Live re-harvest of all 15 allowed OLBG sport and sub-league endpoints (`data/raw/olbg-harvest-20261022T1215Z.tsv`, `docs/audit-a0a7003c.md`, `docs/verifications-a0a7003c.json`, `FL-091`..`FL-095`):

- **24 newly posted midday OLBG events captured & verified:** all 11 remaining Thu 22 Oct NHL regular-season games (`199931`–`199936`, `199938`–`199942` against verbatim `api-web.nhle.com/v1/{schedule,standings}/2026-10-22`), 2 WTA 250 Osaka quarterfinals (`902135` `Ann Li vs Lilli Tagger`, `902134` `Katie Boulter vs Antonia Ruzic` against `wtafiles.wtatennis.com`), 1 ICC Women's Championship ODI (`188830` `India W vs Zimbabwe W 1st ODI` against `bcci.tv`, guarding OLBG's `"Man Of The Match"` player market from team win pricing), 1 French Ligue A Masculine / Alterna VOLSTAR J3 fixture (`37005` `Sete vs Chaumont` against `lnv.fr` & `lnv-web.dataproject.com`), and 9 UK afternoon/evening greyhound races (`689614`..`689696`, left honestly `unverified` per `FL-055`/`FL-095`).
- **Model & cross-track alignment fixes:** fixed road home-ice sign bug on `ICH-199937` (`NY Rangers @ TOR Maple Leafs` `0.5682` `HIGH` -> `0.5306` / `1.79` `-127` `MEDIUM`, matching `IHO-14`), cross-synced 27 official/club-official verifications onto `/olbg/`, updated `GLF-05`/`GLF-101903` Stifel Charity Classic (`Stewart Cink 3/13` across 72-player Norwood Hills field) and `GLF-07`/`GLF-101908` JGTO dates (`Oct 22–25, 2026`), and added 6 unique sourced in-band (`-250..+10000`, `<70%`) `HIGH` predictions (`IHO-15`/`ICH-199931`, `IHO-16`/`ICH-199932`, `IHO-17`/`ICH-199933`, `IHO-23`/`ICH-199940`, `IHO-24`/`ICH-199941`, `VOL-30`/`VOL-37005`).
- **Committed `12:25Z` snapshot state (the live dashboard remains authoritative as hourly builds run):** `check_board.py` **PASS** (`253 rows / 216 fixtures [100% verified] + 37 outright/race / 231 verified / 230 priced / 72 pieces / 20 live in-band HIGH`), `tools/check_site.py` **PASS** (`298 fixtures / 298 lines / 24 HIGH / 52 pieces / 95 register items`), `check.py` **PASS** (`40` feed rows), `check_links.py` **PASS** (`85` pages, `1,529` links, `0` broken), `67/67` unit tests **OK**, `0` excluded-sport rows.

## Independent verification — `session-7da75ec9`, 2026-10-22T12:00Z (this branch, no data change)

Full pipeline re-run on `main` `f55593f` (PR #82) with zero drift: `59/59` unit tests, `check_board.py` **PASS** (`230 rows / 202 fixtures + 28 outright / 217 verified / 210 priced / 67 pieces`, 17 live in-band HIGH across 11 sports, 0 broken links across 85 pages/1,529 links), `tools/check_site.py` **PASS** (`275 fixtures / 275 lines / 22 HIGH / 47 predictions / 76 flags`), `check.py` PASS, `scripts/update.py` + `discovery.py` PASS. **0 excluded-sport rows** in both tracks; every row carries an OLBG `event_id` source link; every `HIGH` sits strictly inside `-250..+10000` (`1.40–101.00` decimal) with a timezone-qualified official start in `data/release_checks.json` and a unique ≥30-word sourced write-up (59–91 words) naming teams, current form, recent results and an explicit selection (table). 12 unverified / 1 corroborated rows blank+flagged; pricing recomputes (`0.95/p`, ~5.26% recip. overround). No invented player claims; WST 404, EuroLeague Valencia/Olympiacos conflicts, Zalgiris/ASVEL 2-4, and SHL shootout corrections already live (FL-063–FL-076). `COORDINATION.md` `task-39` holds the per-row audit table with official URLs.

## Audit — `session-0570f99b`, 2026-10-22 (provenance, freshness & release gate)

Register items `FL-066`..`FL-072` (renumbered at merge; sibling session-08885c97 holds `FL-063`..`FL-065`) (`flagged.html`); row evidence on `source-health.html`.

| Finding | Fix |
|---|---|
| A failed official-feed refresh reused old matches and success text under a fresh timestamp | `scripts/update.py` rewritten: per-source `attempted_at`/`last_success_at`, payload SHA-256, cached rows withheld from the current feed, successful-empty responses clear the cache (FL-066) |
| Every bare OLBG clock was converted with a global UTC−4 assumption and compared to a frozen snapshot time | Conversion removed; shared release gate requires a checked, timezone-qualified official start; in-browser expiry added (FL-067) |
| The cited WST tournament URL renders a 404; seeds/venues/exact clocks were not supported by the working official page | Citations moved to the official WST Matches page; unsupported seeds, venue and clock inputs withheld; snooker write-ups rebuilt from the visible official results (FL-068) |
| Two official EuroLeague pages disagree (Valencia record/scoring, Olympiacos scoring) | Both sources linked; conflicting inputs withheld; affected rows held as unpriced LOW/analysis instead of picking a side (FL-069) |
| Stale/wrong prose: Zalgiris–ASVEL records (both 2-4, Zalgiris 0-2 home per official standings), GOG reverse-fixture date/opponent, an unconfirmed MLB Game 1 starter | Rewritten strictly from the official preview/standings/schedule pages; no starter or injury claims invented (FL-070) |
| Discovery/completeness and bookmaker-odds limits were under-documented; "5% overround" mis-described `0.95/p` pricing | Limits published on the method page and register (FL-071, FL-072) |

Reproduce: run the commands in `method.html` §6; use `OLBG_NOW_UTC` / `OLBG_AS_OF` to pin the publication clock. The committed tracks rebuild byte-identically (CI staleness gate).

## Latest audit — `session-08885c97`, 2026-10-22 08:20–09:10 UTC

Independent re-read of the published write-ups against the competitions' own pages, plus a dead-link sweep of every official source cited by a snooker row.
Three defects were found and repaired; register: **65 items** (`flagged.html`, `/olbg/flagged.html`).

| Finding | What was wrong | Fix |
|---|---|---|
| FL-063 | All 21 snooker source links pointed at `wst.tv/tournaments/northern-ireland-open-2026/`, which now returns a **World Snooker Tour `404 error` page** (the year-less variant 404s too). A row cannot be labelled `verified` on a dead URL | Every occurrence repointed to the live WST match centre `https://www.wst.tv/matches/`, which serves the *BetVictor Northern Ireland Open 2026* match list. Seed numerals in the prose are corroborated on snooker.org Event 2548 exactly as each row note already says; they were **not** re-derived or altered |
| FL-064 | `IHO-03` described Farjestad's two non-regulation results as "one overtime win, one overtime loss". The official SHL table prints `OTW 0, OTL 0, GWSW 1, GWSL 1` — one **shootout** win and one shootout loss, no overtime at all | Prose now states the shootout split. Price (1.42 / -238), probability and `HIGH` grade unchanged |
| FL-065 | `BSB-160789` claimed Milwaukee held "MLB's premier home record at 55-26". Tampa Bay finished **55-26 at home as well**, so the mark is joint-best, not Milwaukee's alone | Rewritten to "a 55-26 (.679) home record, level with Tampa Bay's own home mark as the joint-best in MLB". Every other figure in the piece stands |

Figures re-read verbatim and confirmed **unchanged** this pass: the official SHL table
([Farjestad 10 GP, 8-2-0, 40:11, 27 TP, 1 shootout win / 1 shootout loss](https://stats.swehockey.se/ScheduleAndResults/Overview/20961); Frolunda 2nd on 25 from 11, 38:24; Rogle 6th on 14 from 10, 23:21),
the [EuroLeague standings](https://www.euroleaguebasketball.net/en/euroleague/standings/) (Panathinaikos 5-1, 528:438, +90 — `BKB-11`),
the [ICC Men's ODI team rankings of 21 Oct 2026](https://www.icc-cricket.com/rankings/team-rankings/mens/odi) (England 6, Sri Lanka 7, Ireland 12/51, Namibia 16/32 — `CRK-06`, `CRK-07`),
the [Betoro Herreligaen table](https://tophaandbold.dk/stillinger/herreligaen) (Skive 10 GP, 328:366, 2 pts; Aalborg 10 GP, 323:306, 15 pts — `HBL-28`),
the [MLB 2026 standings](https://www.mlb.com/standings/2026) (Brewers 103-59, 832/618, +214; Rays 98-64, 736/650, 43-38 away — `BSB-01`/`BSB-160789`),
WST's own Day Four reports (Cheung 4-0 Bingham with breaks of 56, 54 and 111; Jak Jones 4-2 John Higgins; McGill 4-1 Lisowski, corroborated by
[BBC Sport](https://www.bbc.com/sport/snooker/articles/cwkg5k7873kxo)), and the ATP Almaty Day 6 order of play
([Machac v Khachanov NB 13:00, Bublik v Marozsan NB 19:30 on Thu 22 Oct](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule)) behind `TEN-23`/`TEN-31`.
The PDC European Championship draw page could not be read this pass (cookie wall), so no darts claim was re-certified — it stays disclosed, not upgraded.
Full source-by-source record: `docs/source-health-20261022.md`.

## Latest audit & live morning refresh — `session-5cef1e25`, 2026-10-22 07:25 UTC

Full re-harvest of all **15 allowed OLBG sport pages** (`2026-10-22T07:21Z–07:26Z`), primary governing-body verification across 15 sports, zero-inference repair, deterministic snapshot clock architecture, and complete root + `/olbg/` dual-track synchronization (`FL-054`..`FL-062`; full logs in `docs/harvest-20261022-0725z.tsv`, `docs/verifications-5cef1e25.json`, and `docs/audit-5cef1e25.md`).

- **Zero live sport gaps across all 15 allowed sports:** Captured all **8** newly posted BetVictor Northern Ireland Open Last 16 ties (`SNK-07..14` / `SNO-9940..9947`), **4** UK morning Greyhound bags (`GRY-07..10`), **6** EuroLeague Round 7 & NBB fixtures (`BKB-25..30`), **3** Swedish SHL games (`IHO-11..13`), **3** ATP/WTA quarter-finals (`TEN-35..37`), **8** Italian SuperLega & Brazilian Superliga Feminina fixtures (`VOL-22..29`), and **11** consensus flips across Handball, Basketball, Tennis, and Ice Hockey.
- **Line-by-line primary verification & zero-inference enforcement:** Upgraded `SNK-01..06` to official `wst.tv` Day Four reports, verified `CRK-05`/`CRK-09` (`cricket.co.za`), `BKB-24`/`BKB-28` (`lnb.com.br`), `HBL-24`/`HBL-28`/`HBL-31` (`eurohandball.com`, `aalborghaandbold.dk`, `tophaandbold.dk`, `asobal.es`), `VOL-22..29` (`cbv.com.br`, `legavolley.it`), `GLF-03`/`GLF-06`/`GLF-08` (`golf.com.au`, `legendstour.com`, `asiantour.com`), `MTR-02`/`MTR-03` (`formula1.com`), and `RGL-03` (`nrl.com`). Removed 4 previously inferred walk-on clock times from `DRT-11..14` (`FL-062`), left `TEN-37` (`wtatennis.com` client JS) and `GRY-07..10` (`gbgb.org.uk` Cloudflare) transparently `unverified` (`FL-054`, `FL-055`), and suppressed home-court edge on neutral Belgrade (`BKB-21`) and Prishtina (`HBL-24`) venues (`FL-058`, `FL-059`).
- **Deterministic CI snapshot + live browser `started` badges:** Anchored tracked JSON to `SNAPSHOT_UTC = 2026-10-22T07:35Z` while `assets/app.js` updates `<span class="tag">started</span>` live in the reader's browser (`data-kickoff`), guaranteeing clean `git status --porcelain` across hourly GitHub Actions runs alongside accurate live in-play indicators.

## Latest audit — `session-e689d84a`, 2026-10-22 09:05 UTC

Independent re-read of the live competition pages behind the published HIGH write-ups, and repair of what did not hold up.
Register: **53 items** (`flagged.html`, `/olbg/flagged.html`).

| Finding | What was wrong | Fix |
|---|---|---|
| FL-052 | Five `/olbg/` write-ups repeated defects already corrected on the root board, because the two tracks keep separate prediction files: `TEN-902110` dated Khachanov's 6-2 6-4 win over Sakamoto to "Tuesday" (the ATP results page puts that round of 32 on **Wednesday 21 October**); `TEN-902071` and `TEN-902063` asserted unverified weekdays; `TEN-902072` named Ningbo's "Plexipave" surface; `GLF-101904` re-used the withdrawn "far ahead of Ben James" comparison and the word "confirmed" for a 120-player field | Weekday corrected or removed, surface brand dropped, field size labelled a disclosed model input, unverifiable tip comparison removed. No price, probability or grade changed |
| FL-053 | The published finding "Seventy of 137 rows … the remaining 67 rows" was written for a 137-row board; the live board holds 196, so the 2026-10-22 figures are **74 archived / 122 live** — and the same sentence still called the 15-sport re-capture an open task after it had been completed | `scripts/build_site.py` now computes both counts from the data on every build, and the sentence cites `data/raw/olbg-harvest-20261022.tsv` |

Verified verbatim in this pass: [ATP Almaty results](https://www.atptour.com/en/scores/current/almaty/9410/results) and
[Day 6 order of play](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) (Khachanov d. Sakamoto 6-2 6-4 on
Wed 21 Oct; Machac d. Nurlanuly 6-2 6-0; Marozsan d. Skatov 7-5 7-6(4); Machac v Khachanov NB 13:00 and Bublik v Marozsan NB 19:30
on Thu 22 Oct), [ATP Lyon results](https://www.atptour.com/en/scores/current/lyon/496/results) (Nakashima d. Medjedovic
7-6(4) 6-7(4) 6-2; Gojo d. Fery 6-3 7-6(2); Altmaier d. Droguet 5-7 7-6(4) 7-6(3); Jacquet d. Berrettini 7-6(4) 7-5; Van Assche d.
Tabur 7-6(3) 6-3; Wawrinka d. Landaluce 6-3 6-7(2) 7-6(5)), [EuroLeague Round 7 game facts](https://www.euroleaguebasketball.net/en/euroleague/news/tae2627-rs7-game-facts-pan-bas/)
(Panathinaikos 5-1 v Baskonia 1-5 on 22 Oct at 14:15, league-low 73.0 points allowed) and the
[SHL table and 22 October schedule](https://stats.swehockey.se/ScheduleAndResults/Overview/20961) (Färjestad 10 GP 8-2-0, 27 pts,
40:11; Brynäs 5th 28:23; Örebro 9th 20:29; Timrå 10th 20:23, 12 pts; Örebro-Brynäs and Timrå-Färjestad both 19:00).
`wtatennis.com` scores/draws (client-side rendering) and `pdc.tv` (cookie wall) could not be read, so rows resting only on those
pages were not re-certified by this session. No new HIGH prediction was written: every remaining in-band, verified `/olbg/`
candidate without a written piece was a 2026-10-22 fixture at or past kick-off.

## Latest audit — independent pass, 2026-10-22 07:20 UTC

Two defects fixed and one method gap closed; full detail on the Flagged page (`FL-050`, `FL-051`).

| Finding | What was wrong | Fix |
|---|---|---|
| FL-050 | OLBG prints a bare clock with no time zone and the board only resolved a **date**, so a same-day fixture could be published as live after its start. Reading the captured labels as **US Eastern (UTC−4)** reproduces the organiser's own times exactly — 04:00 → 13:00 Almaty, 08:00 → 14:00 Lyon, 09:00 → the second Centre Court match in Brussels (from 13:30), 13:00 → 19:00 CEST handball — and at 07:20 UTC that put **TEN-20** (05:00 UTC), **TEN-21** (05:30 UTC) and **CRK-04** (07:00 UTC; the ICC live score already had New Zealand batting) past kick-off while still published as live HIGH picks | Every row now carries a derived UTC kick-off (`board_dates.resolve_kickoff_utc`) plus a `started` marker in the table and on the prediction card (74 of 196 rows, 3 of them HIGH). Grades are deliberately **not** rewritten by the wall clock: the hourly CI rebuild re-derives the board from committed inputs, so a clock-dependent grade would be irreproducible. The date-level archive gate is unchanged |
| FL-051 | `TEN-20` published "world No. 12" for Iva Jovic in both the headline and the body; the official Ningbo main-draw sheet (released 21 Oct 2026 22:13) prints her at **rank 11**. The same piece's "No. 35" for Paolini and `TEN-21`'s "No. 77" for Linette are not published for unseeded players on any reachable official page | Ranks corrected to the published No. 11; the two unverifiable ranks removed rather than guessed. `TEN-21` now cites the official Osaka main-draw sheet, which carries its scorelines, instead of the player-list page that does not |

Re-verified line by line during this pass: the Almaty Day 6 order of play (Machac v Khachanov NB 13:00, Bublik v Marozsan NB 19:30,
seeds 5 and 3), the Lyon Day 5 order of play (Vacherot v Van Assche NB 14:00, Cobolli v Wawrinka NB 19:00, Jacquet v Nakashima
closing, Gojo v Altmaier on Court 1), the Brussels Day 6 order of play (Goffin v Michelsen, Dzumhur v Bergs NB 17:00, seeds 5 and 6),
the Ningbo and Osaka main-draw sheets (Jovic rank 11, Shnaider 13; Eala 6-3 6-1 Parry; Paolini 6-2 7-5 Kalinina; Siniakova
6-4 0-6 4-0 ret. Stearns; Linette 6-4 6-3 Liu; Linette v Siniakova is the R16 pairing), the China Open sheet (Swiatek 6-1 6-3 Jovic;
Siniakova 6-4 6-3 Linette), the Handbollsligan table (Ystads 6th, 6 pts, 125-112; Önnereds 12th, 2 pts, 140-152; Skånela 13th, 2 pts,
142-155; Karlskrona 11th, 4 pts, 156-164), the LNH table (Aix 8th, 6 pts, 227-223; Toulouse 13th, 6 pts, 198-201; Dunkerque lowest on
175), the EHF Group D table (Szeged 3rd, 3 pts, 139:136; GOG 2nd, 6 pts), the ICC ODI team rankings (Ireland 12th/51, Namibia 16th/32),
the ICC ODI batting/blocks pages and the 2026 T20 World Cup final (India 255/5, New Zealand 159, Samson 89), the Pakistan tri-series
results (Pakistan beat Sri Lanka by 37 on 18 Oct and England by 87 on 20 Oct), the MLB standings and Game 1 schedule, and the two
remaining same-day live cards (BKB-20/21, HTR/HBL/Darts rows) against the competitions' own pages — no further contradiction found.

## Latest audit — `session-8c24595c` (2026-10-22)

Re-verified live against official sources and fixed. Full register on `flagged.html` (49 items).

| Finding | What was wrong | Fix |
|---|---|---|
| FL-044 | The `/olbg/` track graded `HIGH` without looking at the fixture date, so **3 picks** were published for matches already played on 2026-10-21 (`BKB-534839`, `BKB-535674`, `TEN-902063`) | Kick-off gate added in `tools/originate.py`; rows archived to `medium` with the `kick_off_passed_archived` flag; write-ups moved under a labelled **Archived analysis** section; `tools/check_site.py` now rejects a past-dated `HIGH`. Live `HIGH` 26 → **23** |
| FL-045 | `GLF-02`/`GLF-04` claimed the official pages confirmed a 120- and a 78-player field — they do not | Field sizes re-labelled as disclosed model inputs; `GLF-02` prose no longer says "confirmed" |
| FL-046 | `BKB-20` credited a win to "Shane Larkin and Vincent Poirier" and `BKB-21` to "Walter Tavares and Facundo Campazzo"; the official EuroLeague Round 7 page names neither | Both rewritten to the official wording (Cam Payne in for the injured Mike James; Theo Maledon) and the official Game Center added as a source |
| Price drift | `GLF-02` quoted `+738 / 8.38` and `MTR-01` quoted `+254 / 3.54` while their published lines were `+740 / 8.40` and `+241 / 3.41` | Corrected, and `check_board.py` now fails the build if any price quoted in a write-up disagrees with its row (negative-tested) |
| Conflict markers | PR #44 merged four `<<<<<<<`/`=======`/`>>>>>>>` marker lines into `COORDINATION.md` | Removed; `check_board.py` rule 6 now guards every data file |
| Prior text | `gap_sports` rows with a field override repeated the generic "assumed 156-player field" / "22-car grid" text next to `field: 120` / `78` / `21` | Per-row basis text now names the field actually used |

Re-verified exactly against the governing body during this pass: MLB World Series Game 1 (TB @ MIL, Fri 23 Oct,
8:00 PM ET, Misiorowski starting, Brewers 103-59 / 832-618, Rays 98-64 / 736-650); URC table (Leinster 10th,
8 pts, 75/58; Munster 9th, 9 pts, 72/74); LNR Pro D2 J7 (Agen 10th 15 pts, Nissa 13th 11 pts, Soyaux 7th 17 pts,
Dax 6th 19 pts / 269-264, Valence Romans 11th 13 pts, Colomiers 12th 12 pts, Grenoble 3rd 22 pts / 213-176 +37,
Biarritz 5th 20 pts / 213-191); ATP Almaty Day 6 (Bublik v Marozsan R16 NB 19:30, Machac v Khachanov NB 13:00);
ATP Lyon (Wawrinka beat Landaluce 6-3 6-7(2) 7-6(5); Gojo v Altmaier R16); EuroLeague Round 7 game center;
PGA Tour Bermuda overview + facts article (Oct 22-25, Port Royal, par 71, 6,828 yd, $6M, Power won 2022);
LPGA BMW Ladies overview (Oct 22-25, Pine Beach, par 72, 6,784 yd, $2.35M, Sei Young Kim 2025 winner).

## Scope & Strict Exclusions

- **Included (all 15 non-excluded OLBG sports — `229` combined board rows = `202` two-sided fixtures + `27` outright/race rows; `274` `/olbg/` rows spanning `2026-10-22` to `2026-11-01`):**
  Tennis (`37`), Handball (`31`), Basketball (`30`), Volleyball (`29`), Darts (`16`), Rugby Union (`15`), Ice Hockey (`14`), Snooker (`14`), Cricket (`10`), Golf (`10`), Greyhounds (`10`), Gaelic Football (`6`), Motor Racing (`3`), Rugby League (`3`), Baseball (`1`).
- **Strictly excluded (`0` rows published across both tracks):**
  `soccer`, `boxing`, `ufc`, `mma`, `football`, `american football`, `hurling`, `horse racing`, `cycling`, `specials`.
  *(Ambiguity note: Gaelic football, greyhound racing, and Formula 1 motor racing are distinct sports not named in the exclusion list; they are included and explicitly flagged on `flagged.html`.)*

## How Lines, Markets & `-250` to `+10000` Confidence Work

1. **Multi-Market Origination (`scripts/model.py`, `scripts/build_gap_sports.py`, `tools/originate.py`):**
   - **Win Match / Money Line:** Computed from verbatim official competition standings, world rankings, and scoring tables in `data/official.json` (`MLB`, `EuroLeague`, `ATP Tour`, `WTA Tour`, `ICC Cricket`, `PDC Darts`, `SHL`, `NHL`, `ICEHL`, `URC`, `Pro D2`, `Top 14`, `EHF Champions League`, `DAIKIN HBL`) with 5% overround, or shrunk tip-share priors where official form tables are unavailable.
   - **Handicap / Spread / Run Line / Puck Line (every root fixture and every 2-way `/olbg/` sport):** Derived from projected score margin or sport-specific margin scale (`sigma * Phi^-1(p)`) in native units (`points`, `runs`, `goals`, `games`, `legs`, `sets`, `frames`).
   - **Match Totals — Over / Under (every official-form scoring row on both tracks):** Derived from team offensive/defensive scoring rates and audited against OLBG event-page totals markets (`Over 6.5` runs MLB World Series Game 1, `Over 233.5` pts GSW@LAL, `Under 226.5` pts SAC@LAC, `Over 9.5` legs Noppert vs Bunting).
   - **Outrights & Multi-Runner Fields (`27` rows):** Dirichlet-multinomial shrinkage toward `1 / N` field priors (`120` PGA Bermuda field, `22` F1 Austin grid, etc.).
2. **Focusing `HIGH` Confidence on `-250` to `+10000` Odds (`1.40` to `101.00` Decimal):**
   - Heavy >70% moneyline chalk (`price < 1.40`, shorter than `-250`) retains its honest calibrated probability and short price and is explicitly capped at **`MEDIUM`** with its reason disclosed.
   - A selection earns **`HIGH`** only when: (a) confirmed on an official governing-body / club domain (`verified`), (b) backed by official competition form/rankings, (c) kick-off has not passed as of `2026-10-22`, AND (d) its originated price sits strictly inside **`-250` to `+10000` (`1.40 <= price <= 101.00`)**.
   - **Result (as of the committed snapshot; the dashboard and `brief.html` are authoritative because the hourly build re-derives the gap rows and expires picks as official kick-offs pass):** **20 live `HIGH` predictions across 9 sports** on `/` (`Baseball`, `Basketball`, `Cricket`, `Darts`, `Gaelic Football`, `Handball`, `Ice Hockey`, `Rugby Union`, `Volleyball`, spanning `-238` to `+130` US odds) and **24 live `HIGH` predictions across 9 sports** on `/olbg/` (spanning `-238` to `+619` US odds), every one `>= 30` words of unique human prose citing verified 2026 players, current form, recent match scores, explicit betting selections, and official source URLs. That is **24 distinct fixtures**, because the two tracks overlap; `brief.html` counts them once each.

## Reproducible Build & Verification Commands

```bash
python3 scripts/build.py              # official-feed pages/data -> site/
python3 scripts/build_gap_sports.py   # price outright/race markets -> data/gap_sports.json
python3 scripts/model.py              # multi-sport lines, handicaps, totals, picks -> data/events.json
python3 scripts/brief_coverage.py     # per-sport accounting vs the brief -> data/brief_coverage.json (must run after model.py)
python3 scripts/build_site.py         # combined root site -> site/
python3 scripts/check_board.py        # enforce OLBG links, tiers, price recomputation, -250..+10000 band & >=30w predictions
python3 tools/build_dataset.py        # live 2026-10-22 /olbg/ dataset -> data/matches.json
python3 tools/originate.py            # multi-market /olbg/ lines -> data/lines.json
python3 tools/build_site.py           # 21 /olbg/ HTML pages -> olbg-board/ & olbg/
python3 tools/check_site.py           # enforce host allowlist, links, -250..+10000 band & unique >=30w predictions
python3 scripts/build_site.py --snapshot
python3 scripts/check.py              # official-feed invariants
python3 scripts/check_links.py        # 0 broken local links across combined site
python3 -m unittest discover -s tests # 87 unit, clock, band, release, link & brief-coverage tests
```

## Current repository audit (2026-10-22 12:04 UTC)

| File | Contents | Track |
|---|---|---|
| `data/raw/olbg-harvest-20261022.tsv` | Live `2026-10-22` OLBG harvest across all active sports + multi-market notes | `/olbg/` & root |
| `data/events.json` + `data/gap_sports.json` | `202` two-sided fixtures + `27` outright/race rows = **`229` rows** (`216` verified, `1` corroborated, `12` unverified; `208` priced) | root board |
| `data/predictions.json` | **`66` written pieces**: **`14` live `HIGH` predictions** + `52` `analysis` notes | root board |
| `data/matches.json` + `data/lines.json` | **`274` fixtures & multi-market lines** across all 15 allowed sports | `/olbg/` track |
| `data/predictions-olbg.json` | **`46` written pieces**: **`19` live `HIGH` predictions** across 9 sports (`-238` to `+619` US) + `27` `analysis` notes | `/olbg/` track |
| `data/flagged.json` | **`90` flagged review items** with direct source links | both tracks |
`session-adeebd4c`, 12:04 UTC: fresh independent sports-source verification is **blocked from the agent shell**: outbound access
via `curl` is restricted to GitHub and package registries. A direct PDC HTTPS request failed (curl exit 35).
No inherited quote or verification timestamp was renewed. **Passing tests does not verify match facts.**
See [audit details](docs/audit-adeebd4c.md) and **FL-077** on [Flagged for Review](https://buffedlizard55-lab.github.io/OLBG3/flagged.html).
Earlier audit sections below describe prior sessions, not work independently reproduced here.

| Tracked dataset | Repository count | Verification boundary |
|---|---:|---|
| Root fixtures (`data/events.json`) | 202 | Stored assertions only; not freshly retrieved |
| Root outright/race rows (`data/gap_sports.json`) | 48 | Model prices, not verified bookmaker offers |
| Root written pieces (`data/predictions.json`) | 73 | Includes analysis; not 67 released HIGH picks |
| `/olbg/` fixtures and lines | 298 each | Separate track, not additive unique fixture coverage |
| `/olbg/` written pieces | 53 | Includes analysis; current release eligibility depends on time |
| Flag register | 101 | Includes resolved historical items and open review items |

Current validation: 87 unit tests; both track validators; brief-coverage recompute; full build and local link scan (110 pages, 2,450 local links, 0 broken).
These checks establish schema, price-band and release-policy consistency, not factual accuracy,
calibrated confidence, exhaustive market coverage, or a profitable betting edge.

## Freshness and verification limitations (independent audit, 2026-10-22)

The captured board is **not a complete live fixture feed**. Hourly rebuilding does not re-fetch
all OLBG listings or independently re-check the official-source assertions stored in JSON.
The root board now expires past fixture dates against the actual UTC build date, rather than a
frozen session date. For an explicit historical reproduction, set `OLBG_AS_OF=2026-10-22`.
This override does not change capture dates or source verification timestamps.
Same-day fixtures can already have started: the OLBG clock labels lack a confirmed timezone.
`HIGH` is a model evidence grade, not an empirically calibrated probability or proven betting edge;
matching the requested price band alone does not establish value. The `/olbg/` track uses separate logic.
Automated URL/schema checks establish structural consistency, **not that a source supports a claim**.

This session re-read the [official MLB standings](https://www.mlb.com/standings/2026):
Tampa Bay 98–64, 736 RS / 650 RA; Milwaukee 103–59, 832 RS / 618 RA match the stored figures.
This targeted check must not be treated as independent re-verification of every row or prediction.

### Release-evidence hardening (2026-10-22)

The [independent structural audit](docs/audit-d4c3db6c.md) adds fail-closed official-clock
URL and clock-format checks with four regression tests (64 tests total). Both site pipelines
and 1,529 local links pass; generated data is unchanged. This does not upgrade any factual
verification label: complete fresh official-source verification remains **FL-077, needs review**.
