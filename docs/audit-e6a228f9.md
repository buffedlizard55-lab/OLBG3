# Audit — `session-e6a228f9`, task-52 (2026-10-23, 19:40Z–21:00Z)

**Scope claimed:** source-link integrity on the published board, then a fresh line-by-line official
re-read of the live HIGH picks. **Branch:** `arena/e6a228f9-olbg3`, from `main` `3f126e6`.

Nothing in this pass invents a fixture, price, grade or sporting fact. Every value quoted below was
read off the page linked beside it, on 2026-10-23, and the repairs *remove* claims that no linked
page carries.

---

## 1. What the pass found first: the source link on 177 of 180 rows was not the href the server rendered

The brief's verification rule is that every row carries a source link. That is only a real check if
the link resolves to the page the row was read from, so the published `olbg_url` was compared to the
hrefs physically present in the committed capture
(`data/raw/live-20261023T1700Z/listings/*.html`) instead of to the shape of the string.

| what was compared | result |
|---|---|
| published `olbg_url` equal to an href in the served HTML | **0 of 177** (3 rows have no href in that capture) |
| published `olbg_url` with a repeated final path segment | **177 of 180** |
| published rows whose URL 404s when fetched live | confirmed for the sampled row (`160789`) |

The cause is a format mismatch, not a bad capture. A **v2** row's `path_prefix` stops at the
competition (`Tennis/All_Tennis/All_Events`), so the slug has to be appended. A **v3** row's
`path_prefix` is the href's path up to the sport id and therefore **already ends in the slug**
(`Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers`). `tools/build_dataset.py` appended it in both cases:

```
served : https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789
published: .../TB_Rays_@_MIL_Brewers/TB_Rays_@_MIL_Brewers/12?event_id=160789   →  404 Not Found
```

Live re-fetch at 19:33Z: the served href renders the page **“TB Rays @ MIL Brewers Tips”** (with the
Market / tip-split panels), the published URL renders **“404 Not Found”**. The three rows that were
right (`TEN-902147`, `GRY-689803`, `GRY-689800`) come from the v2 supplementary capture, where the
prefix genuinely needs the slug; one of those was re-read live and resolves.

**Repair.** `event_url()` in `tools/build_dataset.py` appends the slug only when the prefix does not
already end in it. `tools/check_site.py` now fails the build on either symptom: a repeated final
segment, or a row URL that differs from an href present in the committed captures.
`tests/test_audit_e6a228f9.py` pins all 177 rows to the exact href in the served HTML, so a future
capture change breaks the build rather than the links. **No fixture, selection, price, probability
or grade changed.** Registered as **FL-163**.

---

## 2. Line-by-line re-read of the live HIGH picks

Eight HIGH pieces had not started at the 19:31Z clock. Each was re-read against the page it cites.
“Verified” here means the specific figure was seen on the linked page in this pass.

| row | fixture / selection | what the piece asserts | source re-read | verdict |
|---|---|---|---|---|
| `BSB-160789` | TB Rays @ MIL Brewers — MIL money line, 1.62 | **Piece rewritten on `main` by `session-d6b030fc` mid-pass (FL-162: injury context added, the separate Over 6.5 lean withdrawn), so the version read here is the current one.** It now states: Martinez three runs over nine road innings; Rays 24-9 in his starts; Misiorowski 1.80 ERA after eleven days off; his last outing 4⅓ innings; Brewers bullpen six earned runs in 40⅔ postseason innings; Contreras .367 in eight playoff games; McClanahan out for the postseason; Woodruff a roster add with MLB-described shoulder risk | [MLB Game 1 preview](https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup), [MLB 2026 standings](https://www.mlb.com/standings/2026), [MLB postseason schedule](https://www.mlb.com/news/2026-mlb-playoff-and-world-series-schedule) | **every figure in the current text verified** (article: “six earned runs in 40 2/3 innings”, “.367 with five RBIs in eight games”, McClanahan “ruled out for the postseason”, Woodruff shoulder-substitution risk, “three runs … over nine innings”, 1.80 ERA / 11 days / 4⅓ innings). The earlier version's standings and postseason figures were verified in the same pass before the rewrite: MIL 103-59 / 832 / 618 / 55-26, MIL 6-4 LAD on 15 Oct for 4-0, TB 7-3 / 3-1 / 7-3 on 17–19 Oct for 4-2 |
| `BKB-534842` | NYK @ BOS — Boston money line | Friday 23 Oct, 7:00 PM ET, TD Garden | [NBA schedule 23 Oct](https://www.nba.com/schedule?date=2026-10-23) | claim verified from the stored official quote; **the piece cited the 22 Oct page** — FL-166 |
| `BKB-534841` | HOU @ SAS — SAS money line | Friday 23 Oct, 9:30 PM ET, Moody Center, Austin | same | same — FL-166 |
| `RGU-609576` | Bulls v Ulster — Bulls, 1.53 | Bulls 3rd, 11 pts, 126/54, +72; Ulster 11th, 8 pts, 88/93; Bulls 57-15 Lions; Ulster 26-26 Munster | [URC table 2026/27](https://stats.unitedrugby.com/match-centre/table/2026-27) | **verified, every figure** |
| `RGU-609578` | Leinster v Munster — Leinster, 1.44 | Leinster 10th, 8 pts, 75/58, beat Cardiff 29-5; Munster 9th, 9 pts, 72/74, drew 26-26 Ulster | URC table | **verified, every figure** |
| `RGU-609580` | Stormers v Scarlets — Stormers, 1.58 | Stormers 4th, 11 pts, 81/54, +27; Scarlets 12th, 7 pts, 68/85, −17; **“both clubs opened Round 3 badly”** | URC table (Round 3 strip: DHL Stadium STO 39–SHA 22; Parc y Scarlets SCA 27–BEN 26) | table figures verified; **the two results were reversed — both clubs won** — FL-164 |
| `GFA-3530` | St Finbarrs v Nemo Rangers — St Finbarrs, 1.62 | final 25 Oct, 4.00pm, Páirc Uí Chaoimh; Barrs +31 (116/85) over five games incl. 4-23 to 1-11 v Carbery and 2-12 to 0-16 v Clonakilty; Nemo +19 (98/79) | [Cork GAA final page](https://gaacork.ie/event/mccarthy-insurance-group-premier-senior-football-championship-final/), [results hub](https://gaacork.ie/results/), [Premier SFC competition page](https://gaacork.ie/league/215999) | **verified, including the arithmetic**: Barrs group 63-55, SF 18-16, QF 35-14 = 116/85 (+31); Nemo group 57-43, QF 23-20, SF 18-16 = 98/79 (+19) |
| `VOL-36997` | Perugia v Pordenone — Perugia, 1.58 | “Sunday 25 October at 17:00 UTC **at PalaBarton (confirmed verbatim on … Match #30002)**”; Reggers 18, Semeniuk 13; visitors “newly promoted”, D'heer 19 v Monza | [Match #30002](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30002/), [Match #30000](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30000/) | date/clock/teams and both scorers verified (Perugia won 3-2 at Cuneo: 25-18, 7-25, 15-25, 25-21, 23-25); **the arena name, the “verbatim” attribution, “newly promoted” and the D'heer figure are not on the cited pages** — FL-167 |

Two HIGH pieces had already kicked off by the time of this pass and were re-read as well, because
they are still what the archive publishes:

| row | assertion | verdict |
|---|---|---|
| `RGU-609577` | Connacht 14th, 5 pts, 56/84; Glasgow 36-19 Connacht on 9 Oct; Zebre 12-29 Edinburgh | **verified, every figure** |
| `RGU-609579` | Edinburgh 1st, 14 pts, 80/54, +26; Lions 7th, 9 pts, 77/102; Lions “crushed 57-15 **at home**” | table figures verified; **the fixture was at Loftus Versfeld, the Bulls' ground — the Lions were away** — FL-165 |

**Total: 10 HIGH pieces re-read; six fully verified (one of them, `BSB-160789`, was rewritten on `main` during the pass and the current text was re-read and verified here); four repaired (FL-164…FL-167).**

---

## 3. Register entries raised

| id | severity | one-line |
|---|---|---|
| `FL-163` | high | 177 of 180 OLBG source links repeated the final path segment and 404'd; repaired to the served href and pinned by a test |
| `FL-164` | high | `RGU-609580` reversed both URC Round 3 results (Stormers won 39-22, Scarlets 27-26) while the root track's `RGU-11` had them right |
| `FL-165` | medium | `RGU-609579` placed the Lions “at home” in a match played at Loftus Versfeld |
| `FL-166` | medium | both NBA HIGH pieces cited `nba.com/schedule?date=2026-10-22` for 23 October games; the official check behind their clocks quotes the 23 October page |
| `FL-167` | medium | `VOL-36997` said the arena was “confirmed verbatim” by a page that names only “Perugia, Italy”, and carried two details that page does not support |

All five are published on **Flagged for Review** on both tracks with their source links. None blocks
publication; none changes a price, a selection, a probability or a confidence grade.

---

## 4. Gates run on the final tree (`main` `3f126e6` + this branch)

| gate | result |
|---|---|
| `python3 -m unittest discover -s tests` | **184 tests OK**, 25 skipped (dated pins); 14 of them new in `tests/test_audit_e6a228f9.py` |
| `scripts/check.py` | PASS — 53 fixture rows, hosts, blank fields, unique IDs, internal links |
| `scripts/check_links.py` | PASS — 108 pages, 2 266 local links, **0 broken** |
| `scripts/check_board.py` | PASS — 359 rows, 311 fixtures, 270 verified, 310 priced, 85 pieces |
| `tools/check_site.py` | PASS — 20 pages, 180 fixtures, 180 lines, 12 HIGH, 31 pieces, 157 register items |
| rebuild determinism | `live_refresh.py` → `build_dataset.py` → `originate.py` → `build_site.py` re-run with no diff |

The pipeline was run in the CI order (`build.py`, `build_gap_sports.py`, `model.py`,
`brief_coverage.py`, `build_site.py`, `check_board.py`, then the `/olbg/` track, then the `site/`
assembly and `build_site.py --snapshot`). `scripts/update.py` and `scripts/discovery.py` were **not**
run: both fetch live feeds that this sandbox cannot reach, and `update.py` withholds every row from
`matches` when a fetch fails, so running it here would have emptied the official feed rather than
refreshed it. The committed `data/current.json` (19:13Z, from CI) is unchanged by this pass.

---

## 5. Limitations recorded honestly

1. **No new OLBG listing was captured.** `www.olbg.com` is unreachable from this sandbox (`curl`
   fails) and the OLBG listings render their rows client-side, so the page-retrieval path returns
   “No tips found.” for every sport. Individual **event** pages *do* render, which is what made the
   link verification above possible, but enumeration of new fixtures was not. The board therefore
   still rests on the 17:00Z capture and the 16:30Z v2 supplement.
2. **NBA standings were not re-read.** `nba.com` renders client-side through this path, so the
   records the two basketball pieces cite (BOS 0-1, NYK 0-1, HOU 1-0, SAS 0-1) are carried from the
   22 October check in `data/release_checks.json`, not re-verified today. That is why only the
   schedule citations were repaired.
3. **Three pieces still cite a bare homepage** — `GAF-02` (`https://www.maighcuilinn.com/`) and
   `VOL-37002` / `VOL-37003` (`https://cbv.com.br/`). All three are analysis, not HIGH, and their
   unsupported claims were removed under FL-159; the weak citation remains. Not raised again.
4. **Expired rows still 404.** OLBG withdraws event pages once an event closes, so a row captured
   earlier in the day can have a correct link that now 404s. That is the source's behaviour, not a
   link defect; the capture remains the evidence, and the `/olbg/` release gate marks the row as
   past its start rather than presenting it as live.
5. **Five-per-sport is still not met** (12 live HIGH across the board at this pass, shortfall 59).
   This pass did not manufacture picks to close it: grading a fixture HIGH requires official current
   form for both sides, and that could not be re-read for most sports here.
