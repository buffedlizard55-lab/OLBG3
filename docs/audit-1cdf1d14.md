# Evening pass audit — `session-1cdf1d14`, 2026-10-22T20:55Z–23:10Z

Claim: `task-44-evening-official-reverification-euroleague-conflict-and-integration-20261022`
(`COORDINATION.md`). Branch `arena/1cdf1d14-olbg3` (Arena-locked branch name).

Baseline when work started: `main` `13f31f4` (PR #98), `69/69` unit tests `OK`.
Baseline the work was finally rebased onto: `main` `594a577` (PRs #104/#106/#109/#110 —
`session-cab97f19`, `session-22fd95c8`, `session-784afe97`).

Every observation below was read during this pass. Nothing is inferred, and no field was filled
that a retrieved source does not state.

## 0. Two parallel-session collisions, and how they were handled

While this session was working, two sibling sessions merged evening passes that overlapped this
one. Both times `git pull --rebase` conflicted; **both rebases were aborted rather than forced
through**, `main` was compared item by item against this session's work, and only the
non-duplicative remainder was re-applied on the new base with this session's flags renumbered.
Nothing from a sibling session was deleted or reworded.

| This session's original finding | Disposition |
|---|---|
| NHL release quotes cited a `gameDate` key the `v1/schedule` payload does not contain | **Already repaired on `main`** by `session-cab97f19` (`FL-099`). This session's independent re-read at `21:20Z`–`21:45Z` returned identical `startTimeUTC` values for all twelve games, corroborating the committed clocks. No NHL record was touched — corroboration alone is not a reason to rewrite another session's evidence. |
| Publication clock frozen at `12:40Z` | **Already repaired on `main`** (`FL-099`, clock at `21:20Z`). Not repeated. |
| Darts Round 3 consensus moves and the European Championship outright leader change | **Already applied on `main`** (`FL-107`, and the committed `data/sports/darts.json` holds the same values this session read). Not repeated. |
| Four further consensus counts (World Series Game 1 `16/20`, Zalgiris `2/3`, PHI `10/16`, OKC `10/15`) | **Already applied on `main`** by `session-784afe97`, which read slightly later counts for two of them (PHI `11/17`, OKC `11/16`). This session's earlier read is the weaker evidence and was **dropped**. |
| Five-per-sport accounting | **Already published on `main`** as `scripts/brief_coverage.py` → `data/brief_coverage.json` (`FL-102`). Not duplicated. |
| `FL-069` conflict: the resolution was published but the model table still withheld both clubs | **New.** Published as `FL-127`. |
| `sync_predictions` publishing the wrong downgrade reason | **New.** Published as `FL-128`. |

## 1. Sources read in this pass

| Read at | Source | What it established |
|---|---|---|
| 20:58Z | <https://www.olbg.com/betting-tips/Ice_Hockey/13>, <https://www.olbg.com/betting-tips/Ice_Hockey/NHL/13> | Exactly the 12 NHL games of Thu 22 Oct (event ids 199931–199942) plus three newly posted 23 Oct European fixtures (199946, 199969, 199947). No 23 Oct NHL rows on OLBG. |
| 21:00Z | <https://www.olbg.com/betting-tips/Basketball/4> | 11 rows incl. three EuroLeague Round 8 fixtures (535928, 535925, 535926) and NBA / Brazil NBB rows. |
| 21:00Z | <https://www.olbg.com/betting-tips/Baseball/12> | World Series Game 1 (160789) 16/20 tips for MIL Brewers (80%). |
| 21:00Z | <https://www.olbg.com/betting-tips/Darts/15> | Eight European Championship Round 3 fixtures for 23 Oct, the PDC World Championship 2027 outright (26023, Littler 23/37) and the European Championship outright (32338, van Veen 3/16). |
| 21:00Z | <https://www.olbg.com/betting-tips/Snooker/8> | "No tips found." — listing empty. |
| 21:20Z–21:45Z | <https://api-web.nhle.com/v1/schedule/2026-10-22> | All 12 `startTimeUTC` values re-confirmed (`23:00Z` ×5, `23:30Z`, `00:00Z` ×2, `01:00Z` ×2, `02:00Z` ×2); 23 Oct carries only two NHL games (MTL @ CHI `2026-10-24T00:00Z`, TBL @ COL `2026-10-24T01:00Z`). |
| 21:35Z | <https://www.euroleaguebasketball.net/en/euroleague/standings/> | Full 20-club table after the Thursday Round 7 games. |
| 21:40Z | <https://www.euroleaguebasketball.net/en/euroleague/news/game-center-round-7-el2627/> | The page is now a results report: Anadolu Efes 89–80 Besiktas Istanbul (both 3–4), FC Bayern Munich 91–107 Dubai Basketball (Dubai 5–2, Bayern 2–5). |

Endpoints **not** re-read: Tennis, Cricket, Volleyball, Handball, Rugby Union, Rugby League, Golf,
Motor Racing, Gaelic Football, Greyhounds. `docs/harvest-20261022-2055z.tsv` is labelled partial on
its face and was deliberately **not** promoted to `data/meta.json["harvest_file"]`.

## 2. FL-127 — the model table now matches the published FL-069 resolution

`session-784afe97` released the holds on events `535925` / `535926` and wrote on both release
records that "the official EuroLeague standings read at 2026-10-22T21:55Z are used for form". The
committed model table did not match that sentence:

| What the committed table said | What the official table says (read 21:35Z) |
|---|---|
| Olympiacos Piraeus — *withheld, "not model inputs"* | GP 6, W 5, L 1, PTS+ 564, PTS− 524, +40, H 1-0, A 4-1 |
| Valencia Basket — *withheld, "not model inputs"* | GP 6, W 4, L 2, PTS+ 583, PTS− 537, +46, H 2-2, A 2-0 |
| Panathinaikos 6/5/1, 528–438 | 7/6/1, 613–517 |
| Anadolu Efes 6/2/4, 492–510 | 7/3/4, 581–590 |

Because neither club was in the table, `BKB-29` fell back to the OLBG tip share — a single tip,
capped at 98% — and priced `1.02 (-5000)`, **outside** the requested `-250..+10000` band, while
`BKB-30` priced `1.90 (-111)` from a `1/2` split. After the table was replaced with the 20-club read,
both rows price from official form:

| Row | Selection | Probability | Price | Grade |
|---|---|---|---|---|
| `BKB-29` | Olympiacos Piraeus to win | 56.2% | `1.69 (-145)` | `HIGH` |
| `BKB-30` | Valencia Basket to win | 62.2% | `1.53 (-189)` | `HIGH` |

Basketball moves from 1 to 3 live in-band `HIGH` picks on the root board, taking that track from 15
to 17. The `/olbg/` track is unchanged at 23 live `high` (its own gate already priced both fixtures
from the tip share, and its Basketball count was already 5); both rows on the root board carry new
≥30-word sourced write-ups.

Knock-on, disclosed rather than hidden: three already-started EuroLeague rows re-priced off the
newer table — `BKB-20` `1.59 (-169)`, `BKB-21` `1.41 (-244)`, `BKB-26` `1.65 (-154)`. Their
write-ups were re-worded to quote the current price and the current official record; they stay
labelled `analysis` because their official start has passed, and no result is inferred from the
clock (the Efes–Besiktas scoreline quoted in `BKB-20` was read directly from the official game
centre).

## 3. FL-128 — a withheld piece quoted the wrong reason (code repair)

`scripts/release.py:sync_predictions` copied the release reason onto every non-HIGH piece. For a
row whose official start is still ahead (release status `upcoming`, `eligible: true`) but whose
model grade or price band did not reach `HIGH`, the published reason read "Official scheduled start
is ahead of this build" — the opposite of a downgrade. It now publishes that sentence only when the
release gate is the actual blocker. Regression test: `tests/test_evening_1cdf1d14.py`.

## 4. State after the pass

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests` | see the run log in `COORDINATION.md` |
| `python3 scripts/check_board.py` | `PASS` — 265 rows (217 fixtures + 48 outright/race), 237 verified, 245 priced, 73 pieces, brief-coverage accounting recomputes, no duplicate write-ups |
| `python3 tools/check_site.py` | `PASS` — see the run log in `COORDINATION.md` |
| Live in-band `HIGH` | root **21** on the merged tree, of which **+2** is this pass (`BKB-29`, `BKB-30`; Basketball 1 → 3) and **+4** (`DRT-15`, `RGU-02`, `RGU-03`, `RGU-09`) were already eligible on the committed inputs but had not been surfaced by the previously committed build. `/olbg/` was 23 at the PR #114 merge and is 22 on `main` at `a63fc1f`, because PR #112 advanced the publication clock to `22:10Z` — not this pass's doing. See the correction in `COORDINATION.md`. |

`scripts/update.py` and `scripts/discovery.py` were not run locally: this sandbox has no outbound
route to `cdn.nba.com`, `api-web.nhle.com` or `olbg.com` over plain HTTPS (`curl` returns
`SSL_ERROR_SYSCALL`). CI runs both, and the deployed feed pages are the authority for them.
