# Audit — `session-b329efe5`, 26 October 2026

Fresh-evidence refresh, official-clock renewal for the EHF Champions League, repair of the hourly
publication job, and the final integration for this pass.

## 1. What was broken before this pass

| Symptom | Evidence | Cause |
| --- | --- | --- |
| Every hourly `Verify and publish dashboard` run on `main` failed from 2026-10-25T01:14Z to 2026-10-26T19:19Z | [run 40385741490](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40385741490), job step *Rebuild the OLBG lines track* | `scripts/live_refresh.py` (the official-clock re-certification) ran **after** `scripts/model.py` and `tools/originate.py`, so the board was graded against the previous pass's release evidence and `scripts/check_board.py` then reported 22 `HIGH lacks a current official-start release` / `HIGH stored release differs from current evidence` violations. |
| The public site served the 24–25 October board for two days | last successful main deploy 2026-10-24T23:15Z | Nothing was committed after a red run, so the stale board stayed live. |
| `tools/check_site.py` failed with 15 × `broken internal link flagged.html` as soon as a rebuild succeeded | captured in the failing step log | `tools/build_site.py` `stale_banner()` emitted a depth-less `flagged.html`; the banner only renders when the published capture is older than 30 hours, which had never happened on a green build. |

## 2. Repair (code only — no sporting value changed)

* `.github/workflows/pages.yml`: the re-certification (`scripts/live_refresh.py`) is now its own step
  **before** `update.py`, `build.py`, `build_gap_sports.py`, `model.py` and `tools/originate.py`.
  One ordered pass now produces the bytes the old two-cycle workaround produced. Recorded as **FL-238**.
* `tools/build_site.py`: `stale_banner(depth)` prefixes `../` for the per-sport pages. **FL-239**.
* `scripts/apply_evidence.py` (new): derives release evidence from committed source bytes only.

## 3. Source evidence fetched this pass (CI runner, committed verbatim)

The agent sandbox has no outbound route to OLBG or the governing bodies (FL-077), so all reads are
performed by the runner and committed.

| Capture | Contents | Result |
| --- | --- | --- |
| `data/raw/live-20261026T2030Z-b329efe5/` | 18 in-scope OLBG listings, robots.txt honoured | 18/18 HTTP 200, 142 tip cards → 14 sports. `/betting-tips/Snooker/8` returned **no tip cards**. |
| `data/raw/official-20261026T2023Z/` | NHL/MLB/NBA schedule + standings, and 14 competition pages | 12/19 captured; `nba_schedule` 403, EuroLeague 429, URC 404, Super League 500, Volleyball World 404, GBGB 404, ATP 403. |
| `data/raw/cited-20261026T2023Z/` | Re-read of the pages `data/release_checks.json` cites | EHF playing-times PDF captured byte-faithfully (sha256 `b681d6ba…`, matches its manifest). |
| `data/raw/urls-20261026T2024Z/` | First explicit official list (44 URLs) | 33 captured. NHL standings 58 KB, MLB standings 81 KB, LegaVolley calendar, WTA rankings. |
| `data/raw/urls-20261026T2031Z/` | Second list (13 URLs) — form pages | EHF Champions League standings (24 clubs, after Round 5), URC fixtures-in-full, Top 14 calendar, NHL/MLB standings again. |
| `data/raw/urls-20261026T2034Z/` | Third list (4 URLs) — EHF match reports | All four captured; used to check every handball claim below. |
| `data/raw/derived-b329efe5/` | Text sidecar of the EHF PDF + `fixture-quotes.json` | pypdf 6.21.2 extraction of the committed bytes; every quote is a literal slice. |

## 4. Line-by-line check of the published handball write-ups

Each existing piece was re-checked against the 2026-10-26 bytes. The EHF group tables read today
(5 rounds played) match every figure the pieces quote.

| Ref | Claim in the piece | Reread today | Verdict |
| --- | --- | --- | --- |
| HAN-12130 | Melsungen 3-0-2, 138:138, 6 pts; Vardar 1-0-4, 154:158, 2 pts | identical in today's standings table | confirmed |
| HAN-12130 | "Melsungen beat Plock 28:26 in Round 5"; Balenciaga 6/6, Mensing 6/11 | "MT Melsungen (GER) vs Orlen Wisla Plock (POL) 28:26"; "Eric Balenciaga 6/6, Aaron Mensing 6/11" | confirmed |
| HAN-12130 | "goalkeeper Nebojsa Simic's 11 saves" | source says *three consecutive saves in crunch time*, no count | **repaired** to the sourced wording |
| HAN-12130 | Vardar "upsetting Nantes 33:27", Ljevar 7/9 | "Leon Ljevar 7/9 (HC Vardar 1961)", 33:27 in the Round 5 report | confirmed |
| HAN-12138 | Plock 3-0-2, 141:136, +5; Nantes 3-0-2, 142:143, −1 | identical | confirmed |
| HAN-12138 | "battling Melsungen to a 28:26 road loss … Bjerre 4/7, Kosorotov 4/6" | "Frederik Bjerre 4/7, Sergei Mark Kosorotov 4/6" | confirmed |
| HAN-12138 | Nantes "collapsed 33:27 at home to previously winless Vardar" | Round 5 report: Vardar beat Nantes 33:27 | confirmed |
| HAN-12138 | "coach Gregory Cojean citing ongoing one-on-one finishing struggles" | Cojean quoted on one-on-one finishing in today's report | confirmed |
| HAN-12129 | Sporting 4-1-0, 191:165, +26; GOG 3-1-1, 178:172 | identical | confirmed |
| HAN-12129 | Francisco Costa "14 goals"; 42:40 win | "new personal record with 14 goals in Sporting CP's 42:40 win" | confirmed |
| HAN-12129 | "Kevin Moller's buzzer-beating save", 33:33 at Szeged | "Kevin Møller's final save against Sebastian Frimmel's shot on the buzzer" | confirmed |
| HAN-12136 | Magdeburg 5-0, 176:140, 10 pts; Kriens 2-0-3, 158:161 | identical | confirmed |
| HAN-12136 | table "read on 24 October" | re-read 26 October, unchanged | **date updated** |
| HAN-12132 | Kielce 3-0-2, 155:153; Kolstad 0-5, 143:178 | identical | confirmed |
| HAN-12128 | Berlin 3-0-2, 184:172; Partizan 0-1-4, 148:184 | identical | confirmed |
| HAN-12134 | Aalborg 4-1-0, 170:145; PSG 3-1-1, 182:157 | identical | confirmed |
| HAN-12134 | "Ferran Sole's 10/11 outing"; PSG lost 29:28 in Zagreb; Aalborg beat Celje 34:30 | "Ferran Solé 10/11 (Paris Saint-Germain)"; "Paris were defeated in Zagreb, 29:28"; "Aalborg … 34:30" | confirmed |
| VOL-37002 | quoted "1.57 (-175)" and a three-tip split | row now prices 1.78 (-128) on 2/4 tips | **repaired** (price and sample) |

## 5. New written picks this pass

| Ref | Selection | Price | Grade | Basis |
| --- | --- | --- | --- | --- |
| ICH-200103 | Toronto Maple Leafs to win | 1.56 (-179) | HIGH | Toronto 7-4-2, 50 GF/41 GA, W4, 3-1-1 road; Calgary 4-6-0, 23 GF/39 GA |
| ICH-200101 | NY Rangers to win | 1.24 (-417) | analysis | Rangers 6-0-0 at home; LA 2-5-2, 0-3-0 at home. Price inside the floor, so analysis. |
| ICH-200102 | Edmonton to win | 1.26 (-385) | analysis | Edmonton 8-2-1, 49 GF, 5-0-0 road; Detroit 4-4-3 |
| ICH-200112 | NY Islanders to win | 1.65 (-154) | analysis | Both on 12 pts; NYI 1-3-1 road, NSH 3-2-1 home; one recorded tip only |
| BSB-160795 | Tampa Bay Rays to win | 1.26 (-385) | analysis | Rays 98-64 (736/650); Brewers 103-59 (832/618, W5) |

## 6. Gates

* `scripts/check_board.py` — PASS (367 rows, 93 root predictions).
* `tools/check_site.py` — PASS (21 pages, 523 fixtures, 9 HIGH, 59 pieces, 224 flags).
* `scripts/check.py` and `scripts/check_links.py` — PASS in CI on commit `05f7dab`
  ([run 40397290210](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40397290210)).
* `python -m unittest discover -s tests` — 422 tests, 27 dated skips, OK (CI). Two dated pins were
  repaired the documented way (FL-231 class): the VOL-27/28/29 kickoff assertion now allows a
  `past_date` row to publish no start, and the NHL HIGH pin now treats an expired observation like a
  started fixture.

## 7. Published irregularities

FL-238 (pipeline order), FL-239 (stale-banner link), FL-240 (six sports with no reachable official
clock/form source), FL-241 (OLBG's consensus is the draw on twelve handball rows), FL-242 (Porto v
Veszprem clock conflict). All are on the Flagged for Review page with their source links.

## 7. Merge with `main` (2026-10-26T20:46Z)

`gh pr merge 197` reported "the merge commit cannot be cleanly created": `main` had taken PRs #194–#196 after this branch
was cut. `git merge origin/main` conflicted in 84 files. Generated pages (`index.html`, `sports/*.html`, `daily/*.html`,
`olbg-board/**`, `olbg/**`, `research.json`, the root snapshot) were taken from `main` and then rebuilt from this session's
data, so no page keeps a half-merged state. `data/*.json` were taken from `main` and then regenerated by the pipeline that
owns them, except where noted below.

* **Capture identity.** `main` committed `raw/olbg-harvest-20261026T2020Z-ef52c632.tsv` at 20:20:26Z; this session captured
  `raw/olbg-harvest-20261026T2030Z-b329efe5.tsv` at 20:22:06Z. The two list the same fixtures. This session's capture is the
  primary (`data/meta.json`), the sibling capture is kept as `previous_harvest` so the carry-over rows are not lost.
* **Flag ids.** `main` had already issued FL-232…FL-237. This session's five flags are therefore FL-238…FL-242, each keeping
  its previous id in `original_id`: FL-238 pipeline order, FL-239 stale-banner link, FL-240 twelve sports without a reachable
  official clock/form source, FL-241 OLBG consensus is the draw on twelve handball rows, FL-242 Porto v Veszprem clock conflict.
* **VOL-37002.** The merged capture re-lists a two-of-three tip split, so the row prices 1.57 (−175) again. The prose was
  corrected to the row's price — the row was not bent to the prose — and the historical `price_revised` entry now reads
  1.78 → 1.57 with the reason.
* **NHL grades.** On the merged data the two pieces in play tonight and tomorrow (NY Rangers, Edmonton) sit inside the
  −250..+10000 band and are eligible, so they publish as HIGH; Toronto at Calgary (1.80) and NY Islanders at Nashville (1.87)
  stay analysis. Every figure in both published pieces was re-read against
  `https://api-web.nhle.com/v1/standings/now` at 20:43Z: NYR 7-5-1 with 41:36 and a 6-0-0 home record on a two-game losing
  streak; LAK 2-5-2 with 21:32 and 2-2-2 on the road; EDM 8-2-1 with 49 goals and 3-2-1 at home; DET 4-4-3 with 29 goals,
  1-1-2 away and a one-game losing run. Nothing was added that the page does not print.
* **One dated pin repaired.** `tests/test_audit_a30d9bdb.test_new_high_rows_have_a_live_release` froze its gate at one second
  after the row's stored `checked_at`. A sibling session then re-certified the same EHF fixtures at 20:24Z, so the frozen
  instant preceded the evidence and the gate correctly answered `unverified_start`. The pin now freezes after the freshest of
  the two observations (row stamp, release record). The assertion is unchanged.
* **Local-only test failure.** `NavigationTest` reports `site/review.html` missing. That page is written by `scripts/build.py`
  from the official feed, which cannot run here; it is green on CI.
