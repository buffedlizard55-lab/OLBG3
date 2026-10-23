# OLBG3 — reverse-engineered multi-sport board, originated lines & sourced research picks

A static research dashboard built from captured [OLBG.com](https://www.olbg.com/betting-tips) listings across **15 in-scope sports**, with independently originated model lines (win/money line, handicap/spread, totals and outright/race priors), `LOW`/`MEDIUM`/`HIGH` model confidence grades, sourced written predictions (>= 30 words) and a row-level publication (release) gate.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG3/>

## Source-link integrity, and four HIGH write-ups repaired after re-reading their sources — `session-e6a228f9` (task-52)

Full record: [`docs/audit-e6a228f9.md`](docs/audit-e6a228f9.md) · register: **FL-163** … **FL-167** on [Flagged for Review](https://buffedlizard55-lab.github.io/OLBG3/flagged.html) and the [`/olbg/` register](https://buffedlizard55-lab.github.io/OLBG3/olbg/flagged.html)

**The source link on 177 of the 180 published rows did not resolve.** `tools/build_dataset.py` built
each OLBG event URL as `{path_prefix}/{slug}/{sport_id}?event_id=…`, which is right for a v2 capture
row (its prefix stops at the competition) but wrong for every v3 row, whose `path_prefix` already ends
in the slug. The result repeated the final path segment on 177 of 180 rows, and re-fetching one live
proved the consequence: the href the server actually rendered returns the event page, the URL we
published returns **404**. The repair reads the prefix rather than assuming its depth, and
`tools/check_site.py` now fails the build on a repeated segment or on any row URL that differs from an
href physically present in the committed capture. `tests/test_audit_e6a228f9.py` pins all 177 rows to
the served href, so the next capture format change breaks the build instead of the links. No fixture,
price, probability or grade moved.

**Then the links were used.** Ten live HIGH pieces were re-read against the page each cites. Six were
fully confirmed — the MLB Game 1 piece, as rewritten on `main` mid-pass, matches its preview article
point for point (six bullpen earned runs in 40⅔ postseason innings, Contreras .367 in eight games,
McClanahan out for the postseason, Woodruff's shoulder risk, 1.80 ERA over eleven days, 24-9 in
Martinez starts), and the Cork GAA arithmetic reconciles exactly (St Finbarrs 116/85 = +31; Nemo
98/79 = +19). Four did not:

- **FL-164 (high).** `RGU-609580` reversed both URC Round 3 results, saying the Stormers were beaten
  39-22 by the Sharks and the Scarlets went down 27-26 to Benetton when the league's own table shows
  both clubs won — and drew "both clubs opened Round 3 badly" from it. The root track's `RGU-11`
  already had both right, so this was a cross-track inconsistency that survived an earlier repair.
- **FL-165 (medium).** `RGU-609579` placed the Lions "at home" in a match played at Loftus Versfeld,
  the Bulls' ground, in the very sentence used to argue Edinburgh's home edge.
- **FL-166 (medium).** Both NBA pieces cited `nba.com/schedule?date=2026-10-22` for Friday games; the
  official check behind their clocks quotes the 23 October page.
- **FL-167 (medium).** `VOL-36997` called the venue "confirmed verbatim" on a match page that names
  only "Perugia, Italy", alongside a "newly promoted" tag and a scorer line the page does not carry.

Every repair restates only what the linked page says and leaves price, selection and grade untouched;
where a detail could not be re-read, it was removed rather than re-sourced. Gates on the final tree:
200 tests OK (25 skipped dated pins), `check_board.py` PASS (359 rows / 311 fixtures / 270 verified /
310 priced), `tools/check_site.py` PASS (180 fixtures / 8 HIGH / 159 register items),
`check.py` PASS, `check_links.py` 108 pages / 2 246 links / **0 broken**, and the `/olbg/` rebuild is
byte-identical on a second run. `scripts/update.py` and `scripts/discovery.py` were deliberately not
run here — both need live feeds this sandbox cannot reach, and `update.py` withholds every row when a
fetch fails — so the 19:13Z official feed is untouched.

### What this pass could not do

No new OLBG listing was captured: the site is unreachable from the sandbox and its listings render
client-side ("No tips found." for every sport), though individual event pages do render — which is
what made the link audit possible. Five-per-sport remains unmet (12 live HIGH across both tracks, shortfall 63), and no
pick was manufactured to close it.


## Publication expiry repair — session-d6b030fc (2026-10-23)

[Audit and claim-by-claim official links](docs/audit-d6b030fc.md). Hourly builds now advance a
separate `data/publication.json` clock **without renewing source-check timestamps**. This
withdraws four stale pre-match HIGH selections and refreshes both tracks' coverage counts.
Both integrity checks independently recompute release eligibility. The Game 1 write-ups now
include MLB's injury/roster context; the extra Over 6.5 lean was withdrawn.

At the local 19:29 UTC snapshot: **359 root rows, 180 OLBG-track rows, 12 distinct current HIGH
picks across the tracks, zero sports meeting five, shortfall 63 of 75**. These are captured
research rows, not a complete current fixture list or calibrated win-rate claim. See
[Flagged for Review](https://buffedlizard55-lab.github.io/OLBG3/flagged.html), FL-161 / FL-162.

To begin a **new** publication cycle, run `python scripts/publication_clock.py` before the
normal pipeline. Omit that step to reproduce the committed build at its stored clock.
Run both origination tracks **before** `scripts/brief_coverage.py` and site rendering.
`OLBG_NOW_UTC=YYYY-MM-DDTHH:MMZ` still reproduces an explicit historical evaluation.

## Seventh parallel 2026-10-23 pass, landed as a defect repair: the tip-count parser and three classes of unsourced claim — `session-6327cf90` (task-50)

Full record: [`docs/audit-6327cf90.md`](docs/audit-6327cf90.md) · independent capture kept as evidence only: [`docs/harvest-20261023-1648z.tsv`](docs/harvest-20261023-1648z.tsv)

**This session ran a complete 2026-10-23 daily pass and then discarded it, deliberately.** At rebase, PRs #119–#136 had already landed six parallel passes and `main` was strictly ahead on every axis — 311 root rows against our 250, 180 fresh `/olbg/` rows against our 141 fresh plus 265 carried, 10/12 live HIGH against our 6/8, a publication clock of `17:22Z` against our `16:48Z`, 147 register items against our 138 — and our drafted FL-131…FL-146 collided with six sessions' FL-131…FL-155. Merging would have regressed all of it and discarded sibling work, so the branch was reset to `origin/main` and only the net-new remainder re-applied, renumbered from **FL-156**. The superseded pass is preserved at branch tip `c01cb49`; its capture corroborates the siblings' rather than entering the harvest chain. Two findings converged independently with repairs already on `main` — the Stormers v Scarlets clock certified at 15:00 UTC where the URC's `KO 15.00 IRE & UK` means 14:00 UTC, and a live HIGH write-up reporting two URC Round 3 results backwards when both clubs won — which is weak evidence those repairs are right.

### FL-156 — 167 of 180 rows were priced from a home-court baseline while disclosing a tip split that was never used

`parse_tips()` in `tools/build_dataset.py` split the captured tips string on `/` and called `int()` on the second half. OLBG renders the count inside a longer control label — `'25/31 Win Tips'` on the 23 October captures, bare `'7/8'` on earlier ones — so `int("31 Win Tips")` raised, the `except ValueError` returned `(None, None)`, and **167 of 180 rows lost their tip count**. The failure was silent in both directions:

- `inputs.basis` kept publishing *"OLBG tip split shrunk with Beta(2,2) prior + sport home-court logit adjustment"* for **77 rows that had no tip split at all**. With `p_raw` null, `tools/originate.py` falls back to `p_shrunk = 0.5` plus the home-court logit, so those rows were priced from nothing but which side is at home. Their probabilities cluster between 0.50 and 0.5646 — the fingerprint of the fallback rather than of any sporting judgement.
- **25 rows named the wrong side**, because with no split the pick defaults to the home team regardless of what the crowd tipped: `ICH-199984` read Chicago Blackhawks where OLBG's tips were 3/3 on Montreal; `HAN-12107` read Villa de Aranda against a unanimous 2/2 consensus *and* the official ASOBAL table; `CRI-188832` read New Zealand where the tips were on India.
- **Every outright and race market was left with no price at all** — `MTR-913`, `MTR-828`, `MTR-912`, `DAR-26023`, `CRI-182606`, `RGL-2695857`, `RGL-2801554`, `RGL-2801600` each published `our_pick` with a null `our_price_pick`, because the outright branch returns an unpriced row when the count is missing. Motor Racing, Darts and Rugby League therefore had no originated prices on the `/olbg/` track.

The fix reads the leading `N/M` with an anchored regex. **This is not inference**: the count is literally in the captured string, verbatim from the source, and the parser had failed to read it. Anything that does not begin `N/M` still returns `(None, None)` and stays unpriced exactly as before.

**After the repair:** 179 of 180 rows parse (the last rendered no count at all); the 25 rows name the side OLBG's tips actually named; the eight outrights above are priced for the first time; 17 rows move `low` → `medium`; the brief's five-per-sport target is met by one sport for the first time (`meeting_5_target` 0 → 1, Rugby Union); and **all 12 live HIGH picks are unchanged in selection, probability and price**, because every one carries an editorial prior from official form and never depended on the tip split. That last point is reassuring but was luck rather than design, and is recorded as such.

### FL-157 — a market label present in one of three sets that must agree

OLBG's tennis listing renders event 902157 (Ann Li v Ashlyn Krueger) under the label `Total Games` with the consensus `Over 22.50`. Three places classify market labels and must stay in step: `tools/build_dataset.py` `OTHER_MARKETS`, `scripts/model.py` `NON_WIN_CONSENSUS_MARKETS`, and `tools/originate.py` `_non_win`. The label had been added to the first only. The effect on this row was small — `resolve_team_side("Over 22.50", …)` matches neither player, so it still fell through to the disclosed baseline — but the disclosure flag understated why the tip was unused. The genuine risk is prospective: a totals consensus whose text happens to contain a player name would be reused as a match-winner probability, pricing a totals tip as though it tipped the outcome. Added to both missing sets, and `tests/test_audit_6327cf90.py` now asserts all three are identical so a future label cannot be added to one and missed in the others.

### FL-158 — two verification records held a different fixture's venue and kick-off while publishing as confirmed

All four `/olbg/` rows citing `S-CBV-2627` (Confederação Brasileira de Voleibol, Superliga Feminina 2026/27) carry a `facts` field naming the fixture the transcribed line describes. For two of them it is not the event the record is keyed to:

| event | the OLBG fixture | venue + clock it held | its own `facts` field |
|---|---|---|---|
| `37002` | Mackenzie W v Osasco W | Arena Paulo Skaf, Bauru · 2026-10-24 21:00 BRT | *"Sesi Vôlei Bauru vs Fluminense."* |
| `37003` | Abel-Moda Brusque W v Praia Clube W | Sportville, Barueri · 2026-10-25 18:30 BRT | *"Paulistano Barueri vs Gerdau Minas (3-2 winners in Round 1)."* |

Arena Paulo Skaf is Sesi Vôlei Bauru's home and Mackenzie is a Belo Horizonte club; Sportville is Paulistano Barueri's. The other two rows on the same source (`37000`, `37001`) match their facts and are untouched, which points to the Round 2 lines having been transcribed one position out rather than to an unreliable source. Both rows published `status: verified`, so a venue and kick-off belonging to different matches were presented as confirmed against a governing body — and the prediction prose reasoned from them, claiming *"Mackenzie's home-court familiarity in Bauru"* and Brusque's *"home-court energy"* at Barueri.

The repair follows the brief rather than the convenient option: venue and local clock are **blanked** and status **downgraded**, not corrected, because the federation listing could not be re-read in this pass and choosing the right line from the neighbouring rows would be exactly the inference the brief forbids. The withdrawn values are retained inside each record as `previous_venue` / `previous_start_local`. Fixture identity — teams and competition — comes from the OLBG listing and is unaffected. Same defect class as FL-154 on SuperLega rows 36994/36997, found independently on two other rows; the shared lesson recorded for future passes is that a transcribed fixture list must be keyed back to the event id, never to row position.

### FL-159 — three write-ups asserted form no cited source supports, and one contradicted a table this project already holds

Three pieces cited a single root URL with no path — `https://www.eurohandball.com`, `https://en.volleyballworld.com` — while asserting specific sporting claims a homepage cannot carry. `HAN-12107` is the serious case: its prose stated Villa de Aranda *"have been strong at home this season with four wins from five home matches and a positive goal differential of plus 18"* and Puerto Sagunto were *"losing three of their four away fixtures"*. The official ASOBAL standings this project already holds in `data/official.json` (read from `asobal.es` on 2026-10-22) give:

| club | GP | GF | GA | diff | pts |
|---|---|---|---|---|---|
| Tubos Aranda Villa de Aranda | 6 | 177 | 211 | **−34** | **1** |
| Fertiberia Puerto Sagunto | 6 | 182 | 184 | −2 | 4 |

Every figure in the prose is contradicted by the project's own committed source, in the opposite direction, and the cited host is the European federation rather than ASOBAL, so it could not have carried Spanish league standings even with a path. The row had also picked Villa de Aranda against both a unanimous 2/2 consensus and the table — an artefact of FL-156. With the parser repaired the row now selects **Puerto Sagunto at 1.52 (−192)**, agreeing with crowd and table alike, and the piece is rebuilt on the official numbers with the league's own site cited. `VOL-37002` and `VOL-37003` had their preseason-chemistry, roster-settling, momentum and home-court claims **removed rather than replaced**, since no retrieved source states any of them, and both now say plainly that standings, recent results and player availability are blank. All three remain `analysis`, not HIGH. The retraction history lives in the register and in each piece's `correction_note`, not in the reader-facing prose — an earlier draft narrated its own correction inline, and this session's own new audit test rejected it, because in a pick write-up that reads as hedging and buries the selection.

### FL-160 — two darts write-ups contradicted their own rows, and the price-quote check could not see it

Found by auditing the hand-off item FL-156 left open. Both tracks enforce that any price quoted in a write-up equals the price its row actually carries, because prose is hand-written while rows are re-priced on every rebuild. The root track's rule in `scripts/check_board.py` had been widened for exactly this on 2026-10-22 and is pinned by `tests/test_price_quote_rule.py`; the `/olbg/` track never received the widening and matched only the `1.58 (-172)` form. Two darts pieces wrote their selection as `money line, 1.66 / -152`, where the comma and slash sit between the decimal and the US odds, so the pattern never fired.

| row | the piece said | the row said |
|---|---|---|
| `DAR-32331` | selection **Kevin Doets**, with an argument for Doets | pick **Michael van Gerwen** at 1.71 (−141), from an OLBG consensus of 3/5 on van Gerwen |
| `DAR-32336` | **1.71 (−141)** | **1.37 (−270)** after the split firmed to 7/9 — shorter than the −250 floor, which is exactly why the row is capped below HIGH |

`DAR-32331` tipped the opposite player to the one the row beside it carried. Both also justified their calls with ranking movement, tournament results and scoring averages — *"dropping below 98"*, *"a first major semi-final"*, *"a top-twenty Order of Merit position"*, *"a scoring average of 99.2"* — citing only the PDC's schedule page, which carries the fixture list and format and no ranking or form data at all; the same class as FL-159. Repaired by bringing the `/olbg/` rule up to the root standard (all three quote forms, with the 1.91 handicap/total exemption carried over) and adding an optional comma to the root pattern too, since `money line, 1.66` defeated it as well — **the widened rule is what surfaced both rows**. Both pieces were rewritten so selection and price agree with the row and the unsourced claims were removed rather than re-sourced; both remain `analysis`.

Worth keeping as a process note: the first drafts of both rewrites narrated their own correction inline and quoted the figures they were retracting, and this session's own new test rejected them — twice. In a pick write-up that reads as hedging and buries the selection, so retraction history belongs in the register and in each piece's `correction_note`. The same test had already caught the identical mistake on `HAN-12107` earlier in the pass.

### Gates after this pass

unittest **170 OK** (25 dated pins skipped by the siblings' `archive_guard`; 21 new tests in `test_audit_6327cf90.py`) · `check_board.py` **PASS** (359 rows, 311 fixtures, 270 verified, 310 priced, 85 predictions) · `tools/check_site.py` **PASS** (20 pages, 180 fixtures, **12 HIGH**, 31 predictions, **152** flags) · `check.py` **PASS** · `check_links.py` **PASS** (108 pages, 2,266 links, **0 broken**) · two consecutive full rebuilds **byte-identical**. `.github/workflows/pages.yml` was not touched (`session-56f4da2b` still holds that task), nor the harvest chain, `data/raw/**`, `tests/archive_guard.py`, or any sibling's register item.

**Handed on:** FL-143's five Pro D2 rows still carry `timezone: CET` on a date when France is on CEST — FL-148 holds two of the five and this pass did not widen it, since the LNR calendar could not be re-read here either. And FL-156's 25 side changes and 17 grade changes have had their *prices* checked but not their prose, so any piece written against a pre-repair pick on those rows should be re-read against the row it now sits on.

## Daily cycle 2026-10-23 (16:30Z capture, 16:55Z–17:22Z official re-observations, merged on top of PRs #119–#127) — `session-beb7787b`, 2026-10-23T17:22Z

- **Capture.** All 15 in-scope OLBG listings re-read 16:16Z–16:40Z (180 rows, 0 excluded) into `data/raw/olbg-harvest-20261023T1630Z.tsv`; chained as a same-day supplementary source behind the 16:21Z v3 capture. 14 further root fixtures appended (NHL TB @ COL, NBA MEM @ GSW, PLK, Asobal/HBL, Swiss NL, PREM Rugby, Austrian/German volleyball), 66 tip-count syncs, OLBG label moves recorded with `start_prev` (Galway SFC final moved by the organisers to Sunday 25 Oct 4pm — FL-150).
- **Official clocks re-observed** on the competition's own pages: URC Round 4 (`IRE & UK`, incl. a corrected Stormers v Scarlets entry — FL-147), NBA.com (12 games, ET), MLB.com (Game 1, 8 p.m. ET), EuroLeague Round 7 article (CEST), NHL API (`startTimeUTC`), Cork GAA. Pages that print no zone (LNR Top 14, WTA order-of-play PDFs) or render the reader's zone (WST, PREM Rugby, EuroLeague game-center) are recorded date-only (FL-148/FL-149). The PDC schedule page returned only a consent wall (FL-145).
- **Picks.** 10 live HIGH picks (Brewers, Olympiacos, Valencia, St Finbarrs, Canadiens, Avalanche, Leinster, Perugia, Civitanova, Monza) with sourced 30+-word pieces; BKB-29/BKB-30 rewritten from the Round 7 article (FL-151). All 84 root pieces now avoid the words "model"/"verified" (FL-152, regression-tested). NHL standings are dated tables; a fixture is priced from the newest table on or before its own date.
- Full record: `docs/audit-beb7787b.md`; tests `tests/test_audit_beb7787b.py` (142 run, 25 skipped dated pins).

## 2026-10-23 freshness audit — `session-c4cde934` (task-46)

At the real **2026-10-23T16:18Z** clock the previously committed `/olbg/` build failed its own checker on five expired 22-Oct Ice Hockey HIGH picks. Re-running the documented `/olbg/` pipeline demoted them (`kick_off_passed_archived`): **HIGH 22 → 17**, all dated 2026-10-23 or later, all inside -250..+10000 with model probability < 0.70 (Basketball 5, Rugby Union 5, and one each for Baseball, Cricket, Darts, Gaelic Football, Golf, Motor Racing, Volleyball). The root track was *measured* at the 23-Oct clock (4 HIGH) but not rebuilt under an override clock, because its committed build is byte-reproducible against its stored observation clock by design; its pages re-check release expiry in the browser. **No new 23-Oct fixtures or predictions were added** — the five-per-sport target for 2026-10-23 is unmet and is published as **FL-131** on Flagged for Review, with the full record in `docs/audit-c4cde934.md`.


What the published numbers do and do not mean:

- **Captured board, not a complete live feed.** 359 root rows (311 fixtures + 48 outright/race) captured 21–23 Oct 2026 (through `2026-10-23T17:22Z`), plus the **180-row** `/olbg/` live-probe track (`152` review-register items) refreshed by the 23 Oct captures, and the hourly NHL/MLB/NBA official-schedule feed. Public hourly OLBG discovery (`scripts/discovery.py`, robots-aware) records event links only and never invents fixtures, clocks or prices.
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
| `/olbg/` | The separate OLBG lines audit track (21 pages, 180 rows at the `2026-10-23T17:22Z` snapshot, 12 live high-confidence picks) with the same release gate applied to its picks |

## Parallel-pass reconciliation: net-new corrections from a sixth 2026-10-23 session — `session-d0f5ca54` (task-49)

This session ran the same 2026-10-23 daily refresh independently and in parallel with `56f4da2b`/`c4cde934`/`be917e0f`/`22dbc477`/`beb7787b` (PRs #119–#132), then merged onto their result keeping only net-new work (`docs/audit-d0f5ca54.md`; its own 16:30Z capture kept as evidence at `docs/harvest-20261023-1630z-d0f5ca54.tsv`). The two passes converged on identical prices for tonight's headline picks (Montréal 1.55, Colorado 1.72, Olympiacos 1.69, Valencia 1.53, Milwaukee 1.67). Kept:

- **BSB-01 / BSB-160789 name the World Series Game 1 starters** — Nick Martinez (Rays 24–9 in his starts incl. playoffs) vs Jacob Misiorowski (1.80 ERA, 252 K, eleven days' rest) — from MLB.com's Game 1 preview; the pieces no longer say the Rays' starter is unnamed. **BKB-30 body corrected:** TJ Shorts plays *for* Valencia against his former club (not “back” for Paris), and Valencia are 4-2 on the official table, not the article snapshot's 5-1.
- **`/olbg/`-side EuroLeague leftovers (`FL-155`):** verifications `535925`/`535926` and pieces `BKB-535925`/`BKB-535926` still said “Round 8” after `FL-151` fixed the root prose; now Round 7 with certified 18:15Z/18:45Z starts. **SuperLega venue mix-up (`FL-154`):** `36994` carried another fixture's arena and local clock; `36997`'s venue blanked rather than guessed. Verification `534841` aligned to Moody Center per `FL-153`.
- **Banned-word sweep completed (`FL-155`):** 12 fields still contained “model”/“verified” after `FL-152` (SNK-09 plus 11 on `/olbg/`, incl. live selections) — all reworded; `tests/test_audit_d0f5ca54.py` now fails the build if either word re-enters a piece on either track. Plus a new sourced analysis piece for `TEN-902162` (Osaka SF, WTA order of play) and refreshed `BKB-534841/42` (Game 1 leaders Durant 30 / Castle 24; today's tip splits).
- Everything else from the parallel pass (its harvest chain, release batch, 23 root rows under sequential refs, NHL standings-dating workaround) was dropped as duplicative of the merged work — in particular `beb7787b`'s per-fixture dated NHL tables supersede this session's block-pinning.

## Daily capture 2026-10-23: fifteen-sport re-harvest, fresh official clocks, honest shortfall — `session-be917e0f`

A new day is a new capture, not a copy of yesterday's board. This pass read all fifteen in-scope OLBG listings on
**2026-10-23 (16:05Z–16:20Z)** and recorded 107 rows verbatim (`data/raw/olbg-harvest-20261023T1620Z.json`, format
v3-json, zero excluded-sport rows): 50 fixtures that were not on the board were appended, 55 that were already there
were **not** duplicated, and the two greyhound races stayed on the outright/race track. Applier:
`scripts/apply_capture.py`; every appended row carries its own `captured` date so `Today`/`Tomorrow` can never resolve
against the wrong day.

- **Three fresh official clocks, all exact UTC and none converted:** the NHL's own schedule payload gives Montreal at
  Chicago `2026-10-24T00:00:00Z` (and Tampa Bay at Colorado `01:00Z`, not rendered by OLBG today, so recorded but not
  priced); MLB's schedule service gives World Series Game 1, Rays at Brewers, `2026-10-24T00:00:00Z`. Because MLB's
  own service states the UTC start directly, `statsapi.mlb.com` was added to the reviewed clock-host list with the
  reason recorded in `scripts/release.py`.
- **The publication clock moved to `2026-10-23T16:45Z`,** so the release gate did what it is for: 22–23 October
  fixtures and observations older than 24 hours are now archived. The live set at this build is **5 root HIGH** —
  `BSB-01` Milwaukee 1.67 (-149), `IHO-199984` Montreal 1.55 (-182), `VOL-27` Perugia 1.58 (-172), `VOL-28` Civitanova
  1.44 (-227), `VOL-29` Monza 1.61 (-164) — plus 5 on `/olbg/`, a union of 8. `brief.html` recomputes the 15-sport
  accounting and the 67-pick shortfall from the rows, with a dated mechanical reason per sport (FL-132..FL-137).
- **Eight date-pinned assertions from earlier sessions were re-expressed as evidence invariants** rather than
  deleted: what changed today is the release status (archived vs live), never a price, a source or a word count.
  `112/112` tests pass; `check_board.py`, `tools/check_site.py`, `check.py` and `check_links.py` all pass; rebuilds are
  byte-identical.
- **New register items:** golf carried no listing (FL-132), rugby league has no fixture (FL-133), the greyhound
  race-card clock disagrees with the listing clock by about five hours (FL-134), 49 new rows publish unverified with
  blank official fields (FL-135, pinned in tests), NBA rows cannot reach HIGH without an official NBA form input
  (FL-136), and 78 earlier pieces still use the words "model"/"verified" that the brief excludes from published prose
  (FL-137). `data/events.json`'s headline `generated` date is now the newest per-row reading date on the board
  (`2026-10-23`) instead of a global constant, so `brief.html` no longer advertises an older capture than the landing page.
  Full working record: `docs/audit-be917e0f.md`.

## Live 2026-10-23 capture, official verification, and the deploy repair — `session-22dbc477`

The hourly build had been failing since midnight on 23 October (three runs, `deploy` skipped), so Pages served the
22 October snapshot for ~18 h. Cause and fix: `scripts/board_dates.build_date()` used the wall clock for the
date-level start gate, which made every rebuild differ from the committed tree; it now follows the committed
publication clock, and a **SNAPSHOT STALE** banner appears on both boards once a capture is 30 h old (`FL-138`).
A full rebuild is byte-identical.

With no route to OLBG from this sandbox (FL-214), the fetch moved to a GitHub Actions runner and the served bytes
are committed as evidence:

- **`scripts/live_harvest.py`** — robots-aware capture of all 18 in-scope listings, storing robots.txt, HTML, text
  renderings and a manifest with per-page status, bytes and sha256. The first run was refused by every page because
  `urllib.robotparser` matches a disallowed agent token as a **substring**: OLBG disallows `User-agent: es`, and the
  token `olbg3research` contains it (`FL-139`). The collector now uses `OLBG3Audit` and records which robots group
  governed each URL.
- **`scripts/extract_listings.py`** — 177 rows across 14 sports (Golf returned "No tips found.", `FL-141`) in harvest
  **format v3**, which adds OLBG's own `<time itemprop="startDate">` UTC instant and the price OLBG prints for each
  selection. A test proves the printed clock differs from that attribute by exactly the UK DST offset on every row,
  so the UTC value is machine evidence rather than an inference.
- **`scripts/official_probe.py` / `verify_live.py`** — NHL and MLB payloads confirmed three fixtures with the leagues'
  own UTC starts (World Series Game 1; MTL @ CHI; TB @ COL). `statsapi.mlb.com` joins the reviewed clock hosts with a
  written reason. NBA and EuroLeague refused the probe (403/429, `FL-142`), and the 15 European hockey fixtures have
  no official read (`FL-140`).
- **`scripts/probe_cited.py` / `reverify.py`** — 27 of 30 cited official pages re-read. Four renewals were proposed
  and **all four were rejected on inspection** (boilerplate, another fixture's clock, a JSON blob), so the 24-hour
  expiry stands and those rows remain analysis.
- **Published:** 177 live fixtures with our own money line, handicap and total; **5 current HIGH picks** (Rugby Union
  3, Volleyball 1, Baseball 1), each with a unique sourced prediction of 30+ words; an executive summary at the top of
  the `/olbg/` dashboard; register items `FL-138`…`FL-144`. Five-per-sport is **not** met and is not claimed — every
  shortfall prints its mechanical reason.

## Parallel evening harvest integration: 30 fixtures onto the root board, 22:10Z re-observations — `session-4b642f84`, 2026-10-22T22:10Z

This session ran the same evening window in parallel with `784afe97`/`c038b7f4`/`cab97f19`/`a1e5112b` (PRs #100–#111) and was re-applied on top of their merged state, keeping only net-new work (`docs/audit-4b642f84.md`; task id renumbered `task-45` at merge):

- **A second, later 15-sport harvest as the newest chained capture** (`data/raw/olbg-harvest-20261022T2130Z.tsv`, 118 rows, 0 excluded) chained ahead of the 20:55Z capture. The evening fixtures the sibling sessions had added to `/olbg/` only (their FL-126) are now also **30 curated root rows** (`TEN-41..48`, `CRK-17/18`, `BKB-31/32`, `RGU-17/18`, `HBL-32..38`, `VOL-31..35`, `IHO-26..29`): root board **295 rows** (247 fixtures + 48 outright/race), 246 verified, 268 priced; `/olbg/` **338 rows/lines, 22 high, 94 predictions, 122 register items**. Tip-count merge rule where the two evening reads overlapped: the larger (fresher) total wins, so no sibling read was regressed.
- **Nine governing-body fixture confirmations added** (WTA Ningbo 2092 + Osaka 405 OP PDFs; ATP Almaty/Lyon/Brussels Daily Schedules; ICC #271647) and **fresh 22:10Z exact-clock observations** for four NHL games (2026020154–157), MLB World Series Game 1 and the three SuperLega Sunday fixtures (VolleyballWorld; 25 Oct DST changeover, 18:00 local = 17:00 UTC). The BSB-01 piece gains MLB.com's Game 1 facts (Misiorowski's MLB-best 100.6 mph average fastball velocity vs Caminero's MLB-best 79.4 mph average bat speed; the Rays' starter remains unnamed in the sources read and is not assumed).
- **Five new root pieces** (78 root / 94 `/olbg/`): Taylor Fritz 1.44 (Lyon QF), Jovic 1.85 stated as a marginal 51% lean (Ningbo QF), India 1.57 (2nd T20I), Ryan Joyce 1.76 and Jonny Clayton 1.30 with the band exclusion stated (Dortmund R1). Brief-coverage recompute at the 22:10Z snapshot: **21 live root HIGH / 22 `/olbg/` high (28 union)**.
- **Two new register items** — **FL-129** (the EuroLeague Round 7 article cited by release_checks now returns 404; the observation was not re-dated without an equivalent reading) and **FL-130** (the 21 new root rows with no readable official source, blank + `unverified`, test-pinned). Overlapping drafts (DRT-17 tie, five-per-sport shortfall) were dropped in favour of the siblings' FL-107/FL-124 and FL-102.
- **Checks:** `109/109` unit tests OK (6 new pins in `tests/test_audit_4b642f84.py`), `check_board.py` PASS, `tools/check_site.py` PASS, `check.py` PASS, `check_links.py` 0 broken; rebuilds byte-identical.

## EuroLeague model inputs restored: two Basketball picks priced from official form — `session-1cdf1d14`, 2026-10-22T21:35Z

Evening pass rebased onto `main` `594a577` after two parallel-session collisions (`FL-129`, `FL-130`, `FL-069`
resolved; `docs/audit-1cdf1d14.md`, `docs/harvest-20261022-2055z.tsv`):

- **`FL-129` — the model table did not match the resolution already published on the release records.** `session-784afe97` released the holds on events `535925`/`535926` and recorded that "the official EuroLeague standings … are used for form", but the committed table still carried the pre-Round-7 numbers and still withheld Olympiacos Piraeus and Valencia Basket as "not model inputs". With neither club in the table, `BKB-29` fell back to a single OLBG tip capped at 98% and priced **`1.02 (-5000)` — outside the requested `-250..+10000` band**, while `BKB-30` priced `1.90 (-111)` from a `1/2` split. The official standings were re-read at `21:35Z` after the Thursday Round 7 games and all twenty clubs are now published verbatim, including Olympiacos `6/5/1, 564-524, +40` and Valencia `6/4/2, 583-537, +46`. Both rows now price from official form — `BKB-29` Olympiacos **`1.69 (-145)`** at 56.2% and `BKB-30` Valencia **`1.53 (-189)`** at 62.2% — with new sourced write-ups, taking **Basketball from 1 to 3** live in-band `HIGH`. On the merged tree the root board measures **15 → 21**: +2 from this change and +4 (`DRT-15`, `RGU-02`, `RGU-03`, `RGU-09`) that were already eligible on the committed inputs but had not been surfaced by the previously committed build — see the correction in `COORDINATION.md`. Three already-started EuroLeague rows re-priced off the newer table (`BKB-20` `1.59/-169`, `BKB-21` `1.41/-244`, `BKB-26` `1.65/-154`) with their write-ups re-worded to the current price and record; they stay `analysis` because their start has passed.
- **`FL-130`.** `scripts/release.py:sync_predictions` published the release gate's "start is ahead of this build" sentence as the reason a piece was withheld even when the release gate was satisfied and only the model/band gate had failed. It now publishes that sentence only when the release gate is the blocker.
- **Not repeated.** The NHL `gameDate` quote defect, the frozen `12:40Z` clock, the darts consensus moves, the European Championship outright leader change, four further consensus counts and the five-per-sport accounting were all already repaired or published on `main` by `session-cab97f19` / `session-784afe97`; where a sibling read a later count (PHI `11/17`, OKC `11/16`) this session's earlier read was dropped as the weaker evidence. This session's independent `21:20Z`–`21:45Z` re-read of `api-web.nhle.com/v1/schedule/2026-10-22` returned identical `startTimeUTC` values for all twelve games, corroborating the committed clocks; no NHL record was rewritten for that reason alone.
- **Verification:** unit tests, `check_board.py`, `tools/check_site.py`, `check.py` and `check_links.py` all **PASS** with byte-identical rebuilds — see the run log in `COORDINATION.md`.

## Evening live re-harvest, two official-source holds resolved & HIGH-pick expansion — `session-784afe97`, 2026-10-22T21:55Z

Live re-capture of all 15 allowed OLBG sport and sub-league endpoints (`data/raw/olbg-harvest-20261022T2055Z.tsv`, 128 live listing rows, `0` excluded-sport rows), two official-source holds resolved against the live official pages, and the live `HIGH` set rebuilt around the current clock. Merged on top of the parallel 21:00Z work already in `main` (`sessions cab97f19 / c038b7f4`), whose capture, cross-track reconciliation and brief-coverage accounting are preserved in full.

- **Board refreshed to the current listing.** `/olbg/` now carries **338 rows / 338 lines / 23 live in-band `HIGH` picks / 67 written pieces** (23 `high` + 44 `analysis`), root `/` carries 265 rows with 15 live `HIGH`. `Snooker` and `Greyhounds` returned *"No tips found."* server-side at 21:00Z (the Northern Ireland Open had finished, the UK greyhound cards had run off), so those sports carry dated rows only and publish no current pick (`FL-123`).
- **Two holds resolved against the live official pages.** `FL-117` — the 2026 US Grand Prix start is `2026-10-25T20:00:00Z`: formula1.com renders its session list in the reader clock, and the same page pins St. Louis (UTC-5) one hour behind it and carries `startDate 2026-10-25T20:00:00.000Z` in its own race payload, so the two official figures agree and `MTR-913`/`MTR-01` publish as live `HIGH`. `FL-118` (was `FL-069`) — the EuroLeague round-seven preview is dated 21 October and describes games played on 22 October, so its record and scoring lines are a pre-round-seven snapshot rather than a contradiction of the official table; the standings read at 21:55Z are used for form and the holds on `535925`/`535926` are lifted.
- **Live `HIGH` per sport — five where the official evidence supports it:** Rugby Union **5** (`RGU-609576` Vodacom Bulls 1.53 -189, `609577` Connacht 1.44 -227, `609578` Leinster 1.44 -227, `609579` Edinburgh 1.42 -238, `609580` DHL Stormers 1.58 -172 — from the URC's own Round 4 fixture list `KO … IRE & UK` and its official league table), Ice Hockey **5**, Basketball **5** (`535925` Olympiacos 1.69 -145, `535926` Valencia 1.58 -172, `535928` Zalgiris 1.45 -222 — official EuroLeague standings; plus `534841`/`534842` from the sibling session's NBA clock repair), Volleyball **2**, and one each for Baseball, Cricket, Darts, Gaelic Football, Golf (`GLF-101903` Stewart Cink 8.55 +755 from the official PGA Tour Champions tee-time sheet) and Motor Racing (`MTR-913` Max Verstappen 3.48 +248).
- **Sixty-seven written pieces** across fourteen sports — Tennis 12, Basketball 10, Ice Hockey 9, Darts 7, Snooker 5, Handball 5, Rugby Union 5, Cricket 4, Volleyball 4, Golf 2, plus one each for Baseball, Motor Racing, Rugby League and Gaelic Football — every one at least 30 unique words and citing the official page it was read from. Seventeen are new in this pass: five tennis quarter-finals, two handball ties, two basketball EuroLeague ties, four rugby union ties, a golf outright, a motor-racing race and a Formula 1 race rewrite. Tennis and Handball publish as **analysis** because the official ATP/WTA order-of-play PDFs and the ASOBAL/EHF calendars print session times with no timezone label (`FL-121`, `FL-122`).
- **Twelve stale or newly wrong statements repaired.** The four NHL write-ups that quoted the midday OLBG tip splits now quote the 20:55Z counts (EDM 5/9, DET 5/7, VGK 5/8, DAL 4/7); the darts outright moved from Gerwyn Price 3/12 to a three-way tie at 3/16 (Luke Littler, Gerwyn Price and Gian van Veen), and because the market's leading selection changed twice in one day after Luke Humphries' withdrawal the row is published **with no selection** rather than with a pick the source does not settle on (`FL-124`); the PDC World Championship tip count moved 23/36 to 23/37 and re-prices to 2.34 (+134); the Leinster–Munster piece cited a United Rugby URL that now 404s and was repointed to the working fixture list and table (`FL-119`); the root board's 68 rows were re-synced to the live tip counts.
- **Ten new register items** `FL-117`..`FL-126` on **Flagged for Review**, covering the two resolved holds, the dead URC URLs, the endpoint-dependent OLBG render zone (`FL-120`), the zone-less ATP/WTA order-of-play PDFs, the zone-less ASOBAL and EHF calendars, the "No tips found." Snooker and Greyhounds listings, the darts listing/event-page disagreement, the bracketed OLBG selection label that defeated the side matcher (`FL-125`, fixed in `tools/originate.py`), and the root-`/olbg/` row-count difference (`FL-126`).
- **New site disclosure:** the `/olbg/` dashboard's per-sport coverage table now carries a **Written pieces** column and a **Why fewer than five live HIGH picks** column derived from each row's own release decision, so the brief's five-per-sport target is reported honestly per sport instead of being asserted.
- **Validation:** `93/93` unit tests `OK`; `check_board.py` **PASS** (`265` rows = `217/217` verified fixtures + `48` outright/race, `245` priced, `15` live `HIGH`, `73` pieces, brief-coverage accounting recomputes); `tools/check_site.py` **PASS** (`338` fixtures/lines, `23` `high`, `67` pieces, `116` register items); `check.py` **PASS** (`40` feed rows); `check_links.py` **PASS** (`110` pages, `2,422` links, `0` broken).

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
  The brief's daily target is five picks per covered sport = **75 across 15 sports**. At the **21:20Z** publication clock (the evening
  re-stamp merged in PR #102) there are **17 distinct live HIGH picks** (14 on root, 17 on `/olbg/`, de-duplicated on OLBG event id), so
  **1 sport meets the target** (Ice Hockey, 5) and the shortfall is **58**. Every sport that falls short carries the mechanical reason counted
  from its own rows: no official current-form input for both sides (Tennis 21 of 40, Snooker 14 of 14, Volleyball 25 of 30, Basketball 22 of
  30 …), HIGH-grade evidence outside the `-250..+10000` band (Ice Hockey 9, Darts 9, Rugby Union 8), an official start that has passed or is
  unverified (Tennis 40 of 40, Snooker 14 of 14, Greyhounds 22 of 22), no defensible win price, or an unverified fixture (Greyhounds 22 of 22).
  Rows can fail more than one test, so the counts overlap by design.
- **`reconcile.html` + `flagged.html#FL-105`:** the root board and the `/olbg/` track are two independent models. Of **217 fixtures priced on
  both**, **167 name the same selection**, **28 name different sides** and **22** have a selection withheld by one track (source conflict or
  gate). All 28 disagreeing pairs are listed with both selections, both model probabilities, both confidence labels and the OLBG event page.
  A disagreement is published as a review item; it is not treated as an error and not resolved by guessing.
- **`brief.html#evidence` + `flagged.html#FL-106`:** how the write-ups are evidenced, counted from each piece's own `sources`: 73 root pieces
  (14 currently HIGH, 59–143 words, none under 30, no duplicate bodies) of which **70 cite a host this repo records as official** and 3 cite
  only hosts outside that set; `/olbg/` 55 pieces (17 HIGH, 46–105 words). The 14 hosts outside the recorded official set are listed with their
  citation counts and are explicitly **not** treated as verification — none was re-read in this pass.
- **`flagged.html#FL-102` (raised by the evening session) is the register entry for the five-per-sport shortfall;** `brief.html` is the live
  accounting behind it and links to it rather than opening a duplicate item.
- **Feed-track coherence:** the legacy official-feed pages said repo-wide things like *"No validated model … all picks remain withheld"* beside a
  board that publishes 20 HIGH picks. They now state that they are the feed track, print their own capture time, warn that rows are not
  filtered against the current clock, and link back to the dashboard and the brief coverage page. No feed data was changed.
- **New build-time guards:** `scripts/check_board.py` rules 7 and 8 fail the build if `data/brief_coverage.json` no longer recomputes from the
  rows, if it lists an excluded sport, if a shortfall does not recompute, if a "disagreement" pair names the same selection twice, or if two
  write-ups are word-for-word identical. `tests/test_brief_coverage.py` adds 12 tests. `.github/workflows/pages.yml` now runs
  `scripts/brief_coverage.py` between `model.py` and `build_site.py`.
- **Verification performed this pass, re-run after rebasing onto the 21:20Z evening capture (PR #102):** every count above is derived from
  committed data and the whole pipeline was rebuilt from a clean tree: `check_board.py` PASS (265 rows = 217 fixtures + 48 outright/race, 237
  verified, 242 priced, 73 pieces, 14 live in-band HIGH), `tools/check_site.py` PASS (324 lines, 17 high, 55 pieces, 106 register items),
  `check.py` PASS (40 feed rows), `check_links.py` PASS (110 pages, 2,402 links, 0 broken, with the stricter checker merged in PR #99), 93/93
  unit tests, two consecutive builds byte-identical. **No source observation was renewed by this pass:** no `checked_at`, quote or verification
  label was written, and nothing previously unverified is now claimed as verified. The 21:20Z clocks and the evening capture come from the
  sibling session's live reads, not from this one. Two live pages *were* read here through the platform page tool for a sanity check — the
  [OLBG tennis listing](https://www.olbg.com/betting-tips/Tennis/3) at 21:52Z and the
  [NHL 2026-10-22 schedule](https://api-web.nhle.com/v1/schedule/2026-10-22) — and they confirm what the board already says: OLBG's headline
  market and tip counts move between reads (902117 now shows *Sara Bejlek to win 2-1* under **Set Betting**, 902135 shows 6/7 not 1/1), which
  is exactly why the committed labels are published as a timestamped snapshot and no start is derived from them. No row was rewritten from
  those reads.

## Reconciled follow-up — `session-22fd95c8`, 2026-10-22T23:00Z

Claimed the same evening task five minutes before `session-cab97f19` and merged after PRs #102 and #101. The overlap was resolved by resetting onto `main` and keeping only what the merged passes did not cover: the **21:19Z darts re-read** (European Championship outright consensus Price 3/12 → **van Veen 3/16**, eight quarter-final tip counts corrected, Littler–O'Connor relabelled to the win market — FL-107) and a **written-piece price-rule fix** after five snooker pieces quoted stale money-line prices in their selection labels (FL-108, four regression tests). `tools/originate.py` now refuses to certify a `HIGH` row from a piece labelled `analysis`, which removes the 82%-consensus Ryan Joyce row priced at 1.30. Nothing from #101/#102 was reverted; the duplicated parts of this session's own work were dropped rather than re-applied.

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
python3 -m unittest discover -s tests # 93 unit, clock, band, release, link & brief-coverage tests
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

Current validation: 93 unit tests; both track validators; brief-coverage recompute; full build and local link scan (110 pages, 2,402 local links, 0 broken).
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
