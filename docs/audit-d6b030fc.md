# Publication-clock and Game 1 evidence audit — session-d6b030fc

Date: 2026-10-23. Base: `3f126e6`. Branch: `arena/d6b030fc-olbg3`.

## What this pass does — and does not — establish

This is a focused repair of an existing multi-session dashboard, **not a claim to have
re-verified every historical row or discovered every current OLBG market**. The existing
OLBG captures, official records and their original retrieval stamps are preserved. No new
bookmaker prices, injury assumptions, completed-match results or calibrated win rates are
introduced. LOW/MEDIUM/HIGH are research grades, not guarantees.

The initial repository state had 359 root rows and 180 OLBG-track rows, 15 sports in the
root coverage accounting, 10/12 HIGH across the two tracks and a deduplicated union of 16.
The captured lists are not a complete live fixture feed. Golf has no cards in the latest
capture and relies on older archived rows in the root board; a missing listing is not proof
of no upcoming events. Five HIGH picks per sport cannot honestly be promised from this evidence.

## FL-161 — frozen expiry clock (reproduced and corrected)

### Reproduction

The successful scheduled run [40009667298](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40009667298)
committed the baseline board at approximately 19:20 UTC. In that board:

- `data/events.json` / `data/lines.json` still used `2026-10-23T17:22:00+00:00` as `release.as_of`.
- `scripts/board_dates.py::snapshot_utc()` selected the newest timestamp in
  `data/release_checks.json`, rather than a new publication evaluation time.
- The existing source observations already placed these starts before the build:

| Affected root / OLBG rows | Selection | Existing sourced start UTC | Official clock source |
| --- | --- | --- | --- |
| BKB-29 / BKB-535925 | Olympiacos | 2026-10-23 18:15 | [EuroLeague round-seven preview](https://www.euroleaguebasketball.net/en/euroleague/news/game-center-round-7-el2627/) |
| BKB-30 / BKB-535926 | Valencia | 2026-10-23 18:45 | [EuroLeague round-seven preview](https://www.euroleaguebasketball.net/en/euroleague/news/game-center-round-7-el2627/) |
| RGU-609577 | Connacht | 2026-10-23 18:45 | [URC fixtures in full](https://www.unitedrugby.com/latest/news/2026-27-fixtures-in-full/) |
| RGU-609579 | Edinburgh | 2026-10-23 18:45 | [URC fixtures in full](https://www.unitedrugby.com/latest/news/2026-27-fixtures-in-full/) |

Those source pages were **not re-read in this pass**. The table reproduces the existing
quoted clock evidence, not a new attestation of their content. The actual defect is purely
arithmetic: 19:20 is later than 18:15 / 18:45. It does not depend on knowing a final score.

Browser JavaScript can downgrade displayed badges at cutoff, but cannot repair committed
JSON, server-rendered coverage accounting or all text on a page. The four distinct selections
were therefore still HIGH in the static data. No outcome is inferred by withdrawing them.

### Repair

1. `scripts/publication_clock.py` writes only `data/publication.json`, once before each CI build.
   It records the real UTC build minute, not an official retrieval timestamp.
2. `snapshot_utc()` reads that file, or the explicit historical `OLBG_NOW_UTC` override.
   Missing/malformed files fail the build; they never silently revive an old release.
3. `source_snapshot_utc()` independently reads source observations. Source age remains
   measured against them, so advancing publication time cannot make evidence seem new.
4. Both site integrity checks call `release.high_release_errors()`, which independently
   recomputes eligibility from the source record at publication time. A stale `eligible: true`
   field, mismatched timestamp or missing release record is rejected.
5. A source check timestamp later than publication time no longer leaks a UTC start or expiry
   into a release labelled unconfirmed.
6. Workflow ordering is now: feed collection → base build → root origination → OLBG extraction
   and origination → brief accounting → both site renderers/checks → snapshot/tests/links.
   Computing the brief before repricing the OLBG track produced stale counts when expiry moved;
   this was reproduced locally, then fixed rather than loosening the accounting assertion.
7. The old candidate-set test retains the original 10 candidates but recomputes which remain
   eligible; it also asserts that expired candidates' write-ups become analysis.

### Local result at publication 2026-10-23 19:29 UTC

- Root: 359 rows (311 fixture, 48 outright/race); 310 with originated prices, 270 carrying the
  prior sessions' official-confirmation status, 8 current HIGH.
- OLBG track: 180 rows, 8 current HIGH, 31 written pieces including analysis.
- Union: 12 distinct current HIGH selections, **zero** sports meeting five, shortfall **63**
  from the requested 75. These counts are snapshot-specific and will decrease at cutoffs.
- No official `checked_at`, OLBG capture time, input probability or originated price was
  changed by the publication-clock repair.

## FL-162 — Game 1 injury context and an unsupported extra recommendation

Re-read through the page retrieval tool on 2026-10-23:

- [MLB official Game 1 schedule JSON](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-25&hydrate=team,linescore,probablePitcher)
- [MLB Game 1 preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup),
  first **two** returned chunks (the pitching, bullpen, injury and current-form sections).

### Claim-by-claim evidence used in the two rewritten predictions

| Published fact | Source excerpt / field | Official source |
| --- | --- | --- |
| Rays away at Brewers; Game 1 starts 2026-10-24 00:00 UTC | `gamePk: 849805`, `gameDate: 2026-10-24T00:00:00Z`, home/away team names | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-25&hydrate=team,linescore,probablePitcher) |
| Nick Martinez / Jacob Misiorowski probable starters | `probablePitcher.fullName` for away / home | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-25&hydrate=team,linescore,probablePitcher) |
| Tampa Bay 24–9 in Martinez starts, including playoffs | “Rays have gone 24-9 in games started by Martinez this season, including playoffs” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| Martinez three runs in nine postseason innings, on the road | “pitched only on the road this postseason, permitting only three runs … over nine innings” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| Misiorowski regular-season 1.80 ERA / 252 strikeouts | “MLB regular-season leader in ERA (1.80), strikeouts (252)” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| 94 pitches in 4⅓ innings in last start; eleven full days off | “94 Misiorowski pitches in 4 1/3 … Game 1 of the NLCS”; “11 full days off” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| Brewers swept NLCS in four games | “Brewers finished off the Dodgers in four games” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| Brewers bullpen 1.33 postseason ERA; six earned runs in 40⅔ innings | “1.33 ERA (six earned runs in 40 2/3 innings this postseason” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| Contreras .367 / five RBIs in eight games | “hitting .367 with five RBIs in eight games” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| McClanahan out for postseason | “ruled out for the postseason” in injury section | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |
| Woodruff roster inclusion does not prove fitness | Injury section describes shoulder recovery, addition to 26-man roster, substitution risk and “A lot of unknowns” | [MLB preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup) |

The two bodies are distinct, over 30 words, name the selection and players, and include
current form, recent match history, matchup-specific statistics and sourced availability.
Neither uses the words prohibited by the brief. The winning selection is an opinion,
explicitly distinguished from the cited facts. Prices/probabilities remain the existing
originated estimates, not official values or observed bookmaker prices.

The OLBG-track **Over 6.5 supporting lean was withdrawn**, not strengthened from general
scoring impressions. This pass has established no separate totals edge. The money-line pick
is unchanged. The preview's batting orders are proposed, so neither rewrite calls them
confirmed starting lineups. The older regular-season records and runs figures were removed
from these bodies rather than claimed to have been re-read in this pass.

**Source irregularity:** the retrieval tool reported a final URL ending
`junior-caminero-damages-american-family-field-videoboard-before-world-series-game-1`
with title `undefined` for the requested preview URL, while returning the complete Game 1
preview text quoted above. Both are on MLB's official host. This mismatch is recorded for
manual review; no claim is made about canonical redirects, and the requested source URL
remains linked for review. No observation timestamp is renewed from this tool response.

## Checks and deployment

- Baseline: 170 unit tests, 25 skipped archival pins.
- After repair: 181 unit tests, **156 passed / 25 skipped**, no failures.
- Both board/site integrity checks PASS; official-feed checker PASS (53 rows).
- Internal-link check PASS: 108 pages, 2,246 links, zero broken (before final audit-link additions).
- Skipped tests are existing dated-capture pins, not new exemptions.
- Workflow and build outputs are checked again before merge. The PR and observed Pages
  result are recorded in `COORDINATION.md`; a green build alone is not claimed as deployment.
