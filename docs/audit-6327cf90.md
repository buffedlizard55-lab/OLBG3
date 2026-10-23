# Audit — session-6327cf90 — 2026-10-23

**Branch:** `arena/6327cf90-olbg3` · **Claimed:** `task-46-daily-live-harvest-20261023-official-reverify-predict-integrate` at 2026-10-23T16:20Z atop `main` `46d8716`
**Outcome:** the daily pass this session built was **superseded and deliberately not merged**. What landed instead is four defects that `main` did not have. **FL-156 … FL-159.**

---

## 1. The collision, and why nothing was forced through

At claim time `main` was `46d8716` (PR #118) and `gh pr list --state open` was empty. This session
then ran a full daily pass: a 141-row live harvest of 14 of the 15 in-scope sports at 16:20Z–16:48Z,
re-observation of four governing bodies, eight fixtures given timezone-qualified official clocks,
eight `/olbg/` and six root HIGH picks, sixteen register items and a rewritten prose corpus.

By the time it came to rebase, **six parallel sessions had claimed the same `task-46` in the same
window and merged PRs #119–#136**, taking `main` to `10835ec`. Comparing the two results:

| | this session's pass | `main` after PRs #119–#136 |
| --- | --- | --- |
| Root fixture rows | 250 | **311** |
| `/olbg/` rows | 407 (141 fresh + 265 carried) | **180** (all fresh) |
| Live HIGH, root / `/olbg/` | 6 / 8 | **10 / 12** |
| Publication clock | `2026-10-23T16:48:00Z` | **`2026-10-23T17:22:00Z`** |
| Register items | 138 | **147** |

`main` was strictly larger and fresher on every axis. Independently and without coordination the
siblings had already: captured the 2026-10-23 listings; re-observed the NHL schedule API, MLB's
Stats API, the URC fixture list and the EuroLeague standings; added `statsapi.mlb.com` to
`OFFICIAL_CLOCK_HOSTS`; added the same three URC name aliases to `scripts/model.py`; registered
`unitedrugby.com` in `source_tiers.official`; **repaired the Stormers v Scarlets one-hour clock
defect**; completed the banned-word sweep across both prose corpora and added a regression test; and
resolved the dated-audit problem with `tests/archive_guard.py`.

Merging this session's branch would have **regressed** all of it — an older clock, a smaller board,
a superseded harvest chain, and flags FL-131…FL-146 colliding with six sessions' FL-131…FL-155. The
coordination protocol forbids discarding another session's work, so the branch was reset to
`origin/main` and the pass was dropped. The superseded commits remain on the branch at `c01cb49` for
the audit trail, and the independent capture is preserved as
[`harvest-20261023-1648z.tsv`](harvest-20261023-1648z.tsv) (141 rows), which corroborates the
siblings' captures rather than replacing them.

Two of this session's findings are worth recording even though the siblings fixed them first,
because they were reached independently and agree: the Stormers clock was certified at 15:00 UTC
where the URC's `KO 15.00 IRE & UK` means 14:00 UTC; and a live HIGH write-up reported two URC Round
3 results backwards, both clubs having won. Agreement between independent passes is weak evidence
that the repairs on `main` are right.

## 2. What was actually net-new

Five defects survived the comparison — each reproduced against `origin/main`, each repaired, each
pinned by `tests/test_audit_6327cf90.py`. The fifth (FL-160) was found after the merge of the first
four, by auditing the hand-off item FL-156 left open.

### FL-156 — the tip-count parser silently failed on OLBG's rendered label (high)

`tools/build_dataset.py` `parse_tips()` did `won, total = tips.split("/", 1)` then
`int(won), int(total)` inside a `try/except ValueError` returning `(None, None)`. OLBG renders the
count inside a longer control label — `'25/31 Win Tips'` on the 2026-10-23 captures, bare `'7/8'` on
earlier ones — so `int("31 Win Tips")` raised and **167 of 180 rows lost their tip count**.

The failure was silent in both directions:

- `inputs.basis` kept publishing *"OLBG tip split shrunk with Beta(2,2) prior + sport home-court
  logit adjustment"* for **77 rows that had no tip split at all**. With `p_raw` null,
  `tools/originate.py` falls back to `p_shrunk = 0.5` plus the home-court logit, so those rows were
  priced from nothing but which side is at home. Their probabilities cluster between 0.50 and
  0.5646 — the signature of the fallback, not of any sporting judgement. The published methodology
  statement was simply false for those rows.
- **25 rows named the wrong side**, because with no tip split the pick defaults to the home team
  regardless of what the crowd tipped: `ICH-199984` read Chicago Blackhawks where OLBG's tips were
  3/3 on Montreal; `HAN-12107` read Villa de Aranda against a unanimous 2/2 consensus and the
  official ASOBAL table; `CRI-188832` read New Zealand where the tips were on India.
- **Every outright and race market was left with no price at all** — `MTR-913`, `MTR-828`, `MTR-912`,
  `DAR-26023`, `CRI-182606`, `RGL-2695857`, `RGL-2801554`, `RGL-2801600` all published `our_pick`
  with `our_price_pick` null, because the outright branch returns an unpriced row when the count is
  missing. Motor Racing, Darts and Rugby League had no originated prices on the `/olbg/` track.

The fix reads the leading `N/M` with an anchored regex. This is **not** inference — the count is
literally in the captured string, verbatim from the source; the parser had failed to read it.
Anything not beginning `N/M` still returns `(None, None)` and stays unpriced as before.

**After:** 179 of 180 rows parse (the last rendered no count at all); the 25 rows name the side
OLBG's tips actually named; the eight outrights above are priced for the first time; 17 rows move
low → medium; `meeting_5_target` rises from 0 to 1 (Rugby Union). **All 12 live HIGH picks are
unchanged in selection, probability and price** — every one carries an editorial prior from official
form and never depended on the tip split. That is reassuring but was luck rather than design, and is
recorded as such.

### FL-157 — `"Total Games"` was in one of three market-label sets that must agree (medium)

OLBG's tennis listing renders event 902157 (Ann Li v Ashlyn Krueger) under the label `Total Games`
with the consensus `Over 22.50`. Three places classify market labels and must stay in step:
`tools/build_dataset.py` `OTHER_MARKETS` (decides `market_family`), `scripts/model.py`
`NON_WIN_CONSENSUS_MARKETS` and `tools/originate.py` `_non_win` (each decides whether a consensus may
be reused as a win probability, and which disclosure flag is attached). The label had been added to
the first only.

Effect on this row was small — `resolve_team_side("Over 22.50", …)` matches neither player, so it
still fell through to the disclosed baseline — but it was tagged only
`non_win_or_tie_consensus_mapped`, so the published disclosure understated why the tip was unused.
The real risk is prospective: a totals consensus whose text happens to contain a player name would
match `resolve_team_side` and be reused as a match-winner probability, pricing a totals tip as
though it tipped the outcome. Added to both missing sets, and the audit test now asserts all three
are identical so a future label cannot be added to one and missed in the others.

### FL-158 — two verification records held a *different* fixture's venue and kick-off (high)

All four `/olbg/` rows citing `S-CBV-2627` (Confederação Brasileira de Voleibol, Superliga Feminina
2026/27) carry a `facts` field naming the fixture the transcribed line describes. For two of them it
is not the event the record is keyed to:

| event | the OLBG fixture | venue + clock it held | its own `facts` field |
| --- | --- | --- | --- |
| `37002` | Mackenzie W v Osasco W | Arena Paulo Skaf, Bauru · 2026-10-24 21:00 BRT | *"Sesi Vôlei Bauru vs Fluminense."* |
| `37003` | Abel-Moda Brusque W v Praia Clube W | Sportville, Barueri · 2026-10-25 18:30 BRT | *"Paulistano Barueri vs Gerdau Minas (3-2 winners in Round 1)."* |

Arena Paulo Skaf is Sesi Vôlei Bauru's home and Mackenzie is a Belo Horizonte club; Sportville is
Paulistano Barueri's home. The other two rows citing the same source (`37000`, `37001`) match their
facts and are untouched, which points to the Round 2 lines having been transcribed one position out
rather than to an unreliable source.

Both rows published `status: verified`, so a venue and kick-off belonging to different matches were
presented as confirmed against a governing body — and the prediction prose reasoned from them,
claiming *"Mackenzie's home-court familiarity in Bauru"* and Brusque's *"home-court energy"* at
Barueri.

The repair follows the brief rather than the convenient option: venue and local clock are **blanked**
and status **downgraded**, not corrected, because the federation listing could not be re-read in this
pass and choosing the right line from the neighbouring rows would be exactly the inference the brief
forbids. The withdrawn values are retained inside each record as `previous_venue` /
`previous_start_local`. Fixture identity (teams, competition) comes from the OLBG listing and is
unaffected. Same defect class as FL-154 on SuperLega rows 36994/36997, found independently on two
other rows; the shared lesson is that a transcribed fixture list must be keyed back to the event id,
never to row position.

### FL-159 — three write-ups asserted form no cited source supports (high)

Three pieces cited a single root URL with no path — `https://www.eurohandball.com`,
`https://en.volleyballworld.com` — while asserting specific sporting claims a homepage cannot carry.

`HAN-12107` is the serious case. Its prose stated Villa de Aranda *"have been strong at home this
season with four wins from five home matches and a positive goal differential of plus 18"* and Puerto
Sagunto were *"losing three of their four away fixtures"*. The official ASOBAL standings this project
already holds in `data/official.json` (read from `asobal.es` on 2026-10-22) give:

| club | GP | GF | GA | diff | pts |
| --- | --- | --- | --- | --- | --- |
| Tubos Aranda Villa de Aranda | 6 | 177 | 211 | **−34** | **1** |
| Fertiberia Puerto Sagunto | 6 | 182 | 184 | −2 | 4 |

Every figure in the prose is contradicted by the project's own committed source, in the opposite
direction. The citation compounded it: `eurohandball.com` is the European federation, not ASOBAL, so
it could not have carried Spanish league standings even with a path. The row had also picked Villa de
Aranda against both a unanimous 2/2 consensus and the table — an artefact of FL-156. With the parser
repaired the row now selects **Puerto Sagunto at 1.52 (−192)**, agreeing with the crowd and the
table, and the piece is rebuilt on the official numbers with the league's own site cited.

`VOL-37002` and `VOL-37003` also inherited the wrong venues from FL-158. Their claims about a young
core developing chemistry in preseason, an opponent's roster still settling, building momentum and
being near-unbeatable at home in preseason play are **removed rather than replaced** — no retrieved
source states any of them — and both now say plainly that standings, recent results and player
availability are blank.

All three remain `analysis`, not HIGH: each rests on a two- or three-tip sample and none has a
timezone-qualified official start. The retraction history is kept in the register and in each piece's
`correction_note`, not in the reader-facing prose.

### FL-160 — two darts write-ups contradicted their own rows, and the price-quote check could not see it

Prose is hand-written while every row is re-priced on each rebuild, so the two drift; that is why both
tracks enforce that any price quoted in a write-up equals the price its row carries. The root track's
rule in `scripts/check_board.py` was widened on 2026-10-22 for precisely this reason and is pinned by
`tests/test_price_quote_rule.py`, whose own docstring records that five snooker pieces had drifted
before the gap was found. The `/olbg/` track never received the same widening: `tools/check_site.py`
matched only `(\d+\.\d{2})\s*\(([+-]\d{2,5})\)`, the `1.58 (-172)` form. Two darts pieces wrote
their selection as *"Kevin Doets to win (money line, 1.66 / -152)"*, where the comma and slash sit
between the decimal and the US odds, so the pattern never fired.

| row | the piece said | the row said |
|---|---|---|
| `DAR-32331` | selection **Kevin Doets**, with an argument for Doets | pick **Michael van Gerwen** at 1.71 (−141), priced from an OLBG consensus of 3/5 on van Gerwen |
| `DAR-32336` | **1.71 (−141)** | **1.37 (−270)** after the tip split firmed to 7/9 — shorter than the −250 floor, which is exactly why the row is capped below HIGH |

`DAR-32331` tipped the opposite player to the one the row beside it carried. Both pieces also
justified their calls with ranking movement, tournament results and scoring averages — *"dropping
below 98"*, *"a first major semi-final"*, *"a top-twenty Order of Merit position"*, *"a scoring
average of 99.2"* — citing only the PDC's schedule page, which carries the fixture list and format
and no ranking or form data at all. Same class as FL-159.

Repaired by bringing the `/olbg/` rule up to the root track's standard — all three quote forms now
matched, with the 1.91 handicap/total exemption the root rule already carries — and by adding an
optional comma to the root pattern too, since `money line, 1.66` defeated it as well; **the widened
rule is what surfaced both rows.** Both pieces were then rewritten so selection and price agree with
the row, and the unsourced ranking and average claims were removed rather than re-sourced, because no
official PDC Order of Merit or results page could be retrieved in this pass. Both remain `analysis`.

One process note worth keeping: the first drafts of both rewrites narrated their own correction
inline, quoting the very figures they were retracting. This session's own new audit test rejected
them, twice. In a pick write-up that reads as hedging and buries the selection, so retraction history
belongs in the register and in each piece's `correction_note` — which is where it now is. The same
test had already caught the identical mistake on `HAN-12107` earlier in the pass.

## 3. Gate results

- `python -m unittest discover -s tests` → **170 tests OK** (25 dated pins skipped by the siblings' `archive_guard`; 21 new in `test_audit_6327cf90.py`)
- `scripts/check_board.py` → **PASS** (359 rows, 311 fixtures, 48 outright/race, 270 verified, 310 priced, 85 predictions)
- `tools/check_site.py` → **PASS** (20 pages, 180 fixtures, 180 lines, **12 HIGH**, 31 predictions, **152** flags)
- `scripts/check.py` → **PASS** (40 feed rows)
- `scripts/check_links.py` → **PASS** (108 pages, 2,266 links, **0 broken**)
- `scripts/brief_coverage.py` → live HIGH root 10, `/olbg/` 12, union **16**, shortfall 59, `meeting_5_target` **1** (was 0)
- Two consecutive full rebuilds → **byte-identical** across `olbg-board/`, `olbg/` and all six gate-covered `data/` files

## 4. Standing caveats, carried forward not restated

Bookmaker odds are never quoted as our price; every decimal and US figure is originated from the
disclosed method. Editorial priors in `tools/originate.py` are modelling assumptions informed by
cited official facts, not governing-body probabilities. A blank field means the source did not state
it. "Needs review" means the item is on Flagged for Review and blocks nothing. No injury, suspension
or starting-lineup information was confirmed from an official source for any fixture touched in this
pass, so none is asserted anywhere.
