# Audit record — task-53, session-ebe6dc9c (evening 2026-10-23, claimed 2026-10-23T19:35Z)

Branch: `arena/ebe6dc9c-olbg3`, claimed against `origin/main` `7fb22d1`. This session works only on its own branch scope and touches no other session's files.

## 1. Work performed

| Item | Result |
|------|--------|
| Evening 15-sport OLBG listing capture | Attempted by CI (run 40012642116, `live-harvest.yml`, request `session-ebe6dc9c` at 19:35Z): all 18 listings returned HTTP 200, but extraction returned **zero tip cards** on every listing and the Tennis listing renders "No tips found." The live primary harvest remains `olbg-harvest-20261023T1700Z.tsv` (177 rows) per `data/meta.json`; the empty evening render displaces nothing. No fixture, clock, price or tip count was inferred from the empty pages. |
| Governing-body structured probes | `data/raw/official-20261023T1936Z/`: NHL schedule + standings, MLB schedule + standings, all captured HTTP 200 and stored verbatim with sha256. |
| Cited-page re-reads | `data/raw/cited-20261023T1937Z/`: 28 cited official pages re-fetched (NHL/MLB schedules, URC fixtures, WTA/ATP order-of-play PDFs, WST matches, PDC, LNR Pro D2/Top 14, ICC, GAA, PGA Tour, EuroLeague, BCCI, F1, etc.). Every entry records status, final URL, bytes and sha256; failures are visible evidence, not silent gaps. |
| Root-track prose/price alignment audit | All 85 root predictions compared against their rows: selection side, quoted decimal price and US odds. One genuine defect found and repaired: **SNK-12** (see below). `HBL-30` ("Skanela IF" row vs "Skånela IF" piece) is the same club rendered with/without å at the identical price 1.70/-143 — not a defect. |
| Banned-word sweep | The rewritten SNK-12 piece contains neither "model" nor "verified" (project-wide banned words in reader-facing prose). All 85 pieces pass `tests/test_audit_beb7787b.py` and `tests/test_audit_d0f5ca54.py`. |
| HIGH-candidate scan | Verified + upcoming + in-band (-250..+10000 US / 1.40..101.00 decimal) non-HIGH rows: exactly one, **BKB-17** (SA Spurs 1.42/-238, prob 0.670, MEDIUM). It cannot be graded HIGH under the project's own rule because it has no official two-sided form source for both sides (basis = OLBG consensus); upgrading it would require inference, which is forbidden. Recorded as the nearest candidate, blocked, not acted on. |
| Release clock | `data/release_checks.json` observations re-read via `cited-20261023T1937Z`; publication clock unchanged (`data/publication.json`); no source timestamp renewed without retrieval. |

## 2. Defect repaired

**SNK-12 — wrong side and mismatched quoted price in an analysis piece.** The row (OLBG event 9945, David Gilbert v Cheung Ka Wai, Northern Ireland Open round 3) carries our pick **Cheung Ka Wai** at 1.42 (-238), from a 2/3 OLBG consensus (prob 0.67, MEDIUM, score 4). The published piece tipped **David Gilbert at 1.57** — the opposite side to its own row, with a price the row does not carry. Repaired by rewriting the piece to select **Cheung Ka Wai at 1.42 (-238)**, citing the WST official Matches page (Gilbert's 4-1 over Oliver Sykes and 4-3 over Gao Yang; Cheung's 4-3 over Ronnie O'Sullivan and 4-0 over Stuart Bingham) and the OLBG event page (tip split 2/3). The fixture is dated 22 October, which has passed at the 23 October build, so the piece stays `analysis` (archived), not HIGH; no outcome is inferred. Sources: https://www.wst.tv/matches/ and https://www.olbg.com/betting-tips/Snooker/All_Snooker/All_Events/David_Gilbert_v_Cheung_Ka_Wai/8?event_id=9945

## 3. Findings (irregularities, non-blocking; published for review)

**Finding A — evening 19:35Z capture carries no tip cards.** CI run 40012642116 (`live-harvest.yml`, request `session-ebe6dc9c`, 2026-10-23T19:35Z) returned HTTP 200 for all 18 in-scope OLBG listings, but the v3 extractor found zero tip-card blocks on any page and the Tennis listing renders "No tips found." No fixture, clock, price or tip field can be taken from this capture; nothing was inferred. The raw HTML was stored as CI run evidence and is not part of the live board: the live primary harvest remains `olbg-harvest-20261023T1700Z.tsv` (177 rows) per `data/meta.json`. This is an observation about OLBG's evening rendering, not a board defect.

**Finding B — LNR Pro D2/Top 14 rows keep no certified clock (FL-143 / FL-148 standing).** The re-read of https://prod2.lnr.fr/calendrier-et-resultats at 19:37Z prints match times (e.g. "19:30", "21:00") with **no time-zone label**, exactly as on 22 October. France was on CEST (UTC+2) on 23 October, so rows labelled CET would convert to the wrong UTC instant; per the FL-096 precedent a venue zone is never guessed. Rows 609558/609560/609563 stay recorded as claimed without a certifiable UTC start, and 609561/609562 remain on hold as analysis. Published on Flagged for Review; non-blocking.

**Finding C — five-per-sport target not met.** Committed brief-coverage accounting: 12 live HIGH picks union-wide (Baseball 1, Basketball 2, Ice Hockey 2, Rugby Union 3, Volleyball 3, Gaelic Football 1), shortfall 63 of 75. Blocking reasons are published per sport (no official form source, start/source gate, unpriced, unverified). No inference is used to close the gap.

## 4. Verification performed

- `python3 scripts/check_board.py` — PASS (359 rows / 311 fixtures / 48 outright-race / 270 verified / 310 priced / 85 predictions; brief-coverage accounting recomputes; no duplicate prose).
- `python3 tools/check_site.py` — PASS (180 /olbg/ fixtures, 8 HIGH, 31 predictions, 154 flags).
- `python3 scripts/build.py` + `python3 scripts/check.py` — PASS (feed track: 53 fixture rows, official hosts, blank betting fields, unique IDs, internal links).
- `python3 scripts/check_links.py` — PASS (54 pages, 1,123 links, 0 broken).
- `python3 -m unittest discover -s tests` — 186 run, OK (25 dated snapshot pins skipped by the archive guard).
- SNK-12 specifically: selection matches the row (Cheung Ka Wai), quoted price 1.42 / -238 matches the row, body 96 words (≥30), status `analysis`, sources are https URLs on reviewed hosts (wst.tv, www.olbg.com), no banned words, prose unique (no other piece shares its body).

## 5. Sources used (official where claimed)

- OLBG listings: https://www.olbg.com/betting-tips/{Tennis,Basketball,Golf,Cricket,Snooker,Rugby_Union,Rugby_League,Baseball,Ice_Hockey,Motor_Racing,Darts,Handball,Volleyball,Gaelic_Football,Greyhounds} + /robots.txt (CI run 40012642116, 2026-10-23T19:35:56Z, HTTP 200 on all 18 listings; zero tip cards rendered — verbatim HTML retained as CI run evidence, not in the live board).
- WST official Matches: https://www.wst.tv/matches/ (re-read 2026-10-23T19:37Z; pair/date confirmed, no timezone inferred).
- NHL official schedule: https://api-web.nhle.com/v1/schedule/2026-10-23 (re-read in CI run 40012642116; Canadiens @ Blackhawks 2026-10-24T00:00Z and Lightning @ Avalanche 2026-10-24T01:00Z — both already on the board as IHO-199984 / IHO-199985).
- MLB official schedule: https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-25&hydrate=team,linescore,probablePitcher (re-read in CI run 40012642116; World Series Game 1 Rays @ Brewers 2026-10-24T00:00Z, Game 2 2026-10-25T00:00Z — Game 1 already on the board as BSB-01).
- LNR Pro D2 calendar: https://prod2.lnr.fr/calendrier-et-resultats (re-read 2026-10-23T19:37Z; times printed, no zone label — Finding B).

## 6. Records added

- `tests/test_audit_ebe6dc9c.py` — regression pins for the SNK-12 repair, the HBL-30 encoding equivalence, the empty-evening-capture observation, the LNR clock finding, and the HIGH-candidate scan.
- This document (`docs/audit-ebe6dc9c.md`).
- Regenerated accounting: `data/brief_coverage.json` (words_median 89 → 90 after the SNK-12 rewrite; all other figures unchanged).

No other session's files were touched; no sibling PR (#143, #144, #145 or any open sibling branch) was modified. Integration: rebase onto `origin/main`, open PR from `arena/ebe6dc9c-olbg3`, merge after green CI, confirm GitHub Pages deploy.
