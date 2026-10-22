# OLBG3 — reverse-engineered multi-sport board, originated lines & sourced research picks

A static research dashboard built from captured [OLBG.com](https://www.olbg.com/betting-tips) listings across **15 in-scope sports**, with independently originated model lines (win/money line, handicap/spread, totals and outright/race priors), `LOW`/`MEDIUM`/`HIGH` model confidence grades, sourced written predictions (>= 30 words) and a row-level publication (release) gate.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

What the published numbers do and do not mean:

- **Captured board, not a complete live feed.** 228 root rows (201 fixtures + 27 outright/race) captured 21–22 Oct 2026, plus the chained 270-row `/olbg/` audit track and the hourly NHL/MLB/NBA official-schedule feed. Public hourly OLBG discovery (`scripts/discovery.py`, robots-aware) records event links only and never invents fixtures, clocks or prices.
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
| `/olbg/` | The separate OLBG lines audit track (21 pages, 270 chained rows) with the same release gate applied to its picks |

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

- **Included (all 15 non-excluded OLBG sports — `196` combined board rows = `173` two-sided fixtures + `23` outright/race rows; `145` live `2026-10-22` `/olbg/` rows):**
  Tennis (`34`), Handball (`31`), Basketball (`24`), Volleyball (`21`), Darts (`16`), Rugby Union (`15`), Cricket (`10`), Ice Hockey (`10`), Golf (`10`), Greyhounds (`6`), Snooker (`6`), Gaelic Football (`6`), Rugby League (`3`), Motor Racing (`3`), Baseball (`1`).
- **Strictly excluded (`0` rows published across both tracks):**
  `soccer`, `boxing`, `ufc`, `mma`, `football`, `american football`, `hurling`, `horse racing`, `cycling`, `specials`.
  *(Ambiguity note: Gaelic football, greyhound racing, and Formula 1 motor racing are distinct sports not named in the exclusion list; they are included and explicitly flagged on `flagged.html`.)*

## How Lines, Markets & `-250` to `+10000` Confidence Work

1. **Multi-Market Origination (`scripts/model.py`, `scripts/build_gap_sports.py`, `tools/originate.py`):**
   - **Win Match / Money Line:** Computed from verbatim official competition standings, world rankings, and scoring tables in `data/official.json` (`MLB`, `EuroLeague`, `ATP Tour`, `WTA Tour`, `ICC Cricket`, `PDC Darts`, `SHL`, `NHL`, `ICEHL`, `URC`, `Pro D2`, `Top 14`, `EHF Champions League`, `DAIKIN HBL`) with 5% overround, or shrunk tip-share priors where official form tables are unavailable.
   - **Handicap / Spread / Run Line / Puck Line (`157` root rows; all 2-way `/olbg/` sports):** Derived from projected score margin or sport-specific margin scale (`sigma * Phi^-1(p)`) in native units (`points`, `runs`, `goals`, `games`, `legs`, `sets`, `frames`).
   - **Match Totals — Over / Under (`68` official-form root rows; all scoring `/olbg/` sports):** Derived from team offensive/defensive scoring rates and audited against OLBG event-page totals markets (`Over 6.5` runs MLB World Series Game 1, `Over 233.5` pts GSW@LAL, `Under 226.5` pts SAC@LAC, `Over 9.5` legs Noppert vs Bunting).
   - **Outrights & Multi-Runner Fields (`23` rows):** Dirichlet-multinomial shrinkage toward `1 / N` field priors (`120` PGA Bermuda field, `22` F1 Austin grid, etc.).
2. **Focusing `HIGH` Confidence on `-250` to `+10000` Odds (`1.40` to `101.00` Decimal):**
   - Heavy >70% moneyline chalk (`price < 1.40`, shorter than `-250`) retains its honest calibrated probability and short price and is explicitly capped at **`MEDIUM`** with its reason disclosed.
   - A selection earns **`HIGH`** only when: (a) confirmed on an official governing-body / club domain (`verified`), (b) backed by official competition form/rankings, (c) kick-off has not passed as of `2026-10-22`, AND (d) its originated price sits strictly inside **`-250` to `+10000` (`1.40 <= price <= 101.00`)**.
   - **Result:** **33 live `HIGH` predictions across 10 sports** on `/` (`Baseball`, `Basketball`, `Cricket`, `Darts`, `Golf`, `Handball`, `Ice Hockey`, `Motor Racing`, `Rugby Union`, `Tennis`, spanning `-238` to `+740` US odds) and **23 live `HIGH` predictions across 10 sports** on `/olbg/` (spanning `-227` to `+660` US odds), every one `>= 30` words of unique human prose citing verified 2026 players, current form, recent match scores, explicit betting selections, and official source URLs.

## Reproducible Build & Verification Commands

```bash
python3 scripts/build.py              # official-feed pages/data -> site/
python3 scripts/build_gap_sports.py   # price outright/race markets -> data/gap_sports.json
python3 scripts/model.py              # multi-sport lines, handicaps, totals, picks -> data/events.json
python3 scripts/build_site.py         # combined root site -> site/
python3 scripts/check_board.py        # enforce OLBG links, tiers, price recomputation, -250..+10000 band & >=30w predictions
python3 tools/build_dataset.py        # live 2026-10-22 /olbg/ dataset -> data/matches.json
python3 tools/originate.py            # multi-market /olbg/ lines -> data/lines.json
python3 tools/build_site.py           # 21 /olbg/ HTML pages -> olbg-board/ & olbg/
python3 tools/check_site.py           # enforce host allowlist, links, -250..+10000 band & unique >=30w predictions
python3 scripts/build_site.py --snapshot
python3 scripts/check.py              # official-feed invariants
python3 scripts/check_links.py        # 0 broken local links across combined site
python3 -m unittest discover -s tests # 28 unit, clock & band invariant tests
```

## Summary Data Metrics (`2026-10-22`)

| File | Contents | Track |
|---|---|---|
| `data/raw/olbg-harvest-20261022.tsv` | Live `2026-10-22` OLBG harvest across all active sports + multi-market notes | `/olbg/` & root |
| `data/events.json` + `data/gap_sports.json` | `173` two-sided fixtures + `23` outright/race rows = **`196` rows** (`172` verified, `192` priced) | root board |
| `data/predictions.json` | **`47` written pieces**: **`33` live `HIGH` predictions** + `14` `analysis` notes | root board |
| `data/matches.json` + `data/lines.json` | **`145` fixtures & multi-market lines** across all 15 allowed sports (`112` official-verified, `0` corroborated debt) | `/olbg/` track |
| `data/predictions-olbg.json` | **`23` live `HIGH` predictions** across 10 sports (`-227` to `+660` US, all `< 70%` prob) plus `3` archived analysis pieces | `/olbg/` track |
| `data/flagged.json` | **`53` flagged review items** with direct source links | both tracks |

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
