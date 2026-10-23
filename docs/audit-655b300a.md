# Audit — session-655b300a, task-54 (2026-10-23, 21:26Z–22:05Z)

Evening re-read of every official page behind the live high-confidence picks, one repair, five
disclosures, and a plainly stated reason why no new fixture was added.

- **Branch:** `arena/655b300a-olbg3` (Arena-locked name) — claim committed as `5a6ba3b` on `main` `6241660`.
- **Observation clock for this pass:** `2026-10-23T21:30:00Z`, one stamp for a read window that ran
  21:28Z–21:36Z. The page-retrieval tool returns content without a clock, so a single stamp is
  recorded rather than per-page minutes invented. Every read is listed in
  `data/raw/probe-655b300a/reads.json`.
- **Build clock:** the pipeline's own `scripts/publication_clock.py` value, `21:37Z` when this pass
  was written. **The first draft of this document, and every receipt behind it, carried `22:40Z` —
  63 minutes into the future. It was withdrawn and re-dated; see §8 and `FL-190`.**

## 1. Retrieval boundary (what this sandbox can and cannot reach)

`curl` from the shell still fails against every external host (`SSL_ERROR_SYSCALL`), so all reads use
the harness retriever. Unlike earlier passes, that route **did** reach the official JSON feeds as
well as OLBG's HTML, which is what made a real re-verification possible:

| Host | Reachable in this pass | Used for |
|---|---|---|
| `statsapi.mlb.com` | yes | World Series schedule, club standings, postseason results |
| `api-web.nhle.com` | yes | NHL schedule (`/v1/schedule/now`) and standings for 2026-10-23 |
| `api.nhle.com` | yes | league stats service, as the comparator in FL-187 |
| `www.unitedrugby.com` / `stats.unitedrugby.com` | yes | Round 4 kick-offs and the league table |
| `www.legavolley.it` | yes | SuperLega Giornata 1 set scores |
| `gaacork.ie` | yes | Cork PSFC final page |
| `www.nba.com` | yes | 23 October schedule |
| `cdn.nba.com` | **no** | failed; fixture times taken from `www.nba.com` instead |
| `www.olbg.com` | HTML yes, listing rows **no** | see FL-185 |

## 2. The eight live selections, re-read line by line

Root track and `/olbg/` track share fixtures; the table below is by unique fixture.

| Fixture | Live rows | Officially confirmed this pass | Result |
|---|---|---|---|
| TB Rays @ MIL Brewers, World Series Game 1 | `BSB-01`, `BSB-160789` | `gamePk 849805`, `gameDate 2026-10-24T00:00:00Z`, American Family Field; Brewers 103-59, 832 scored, 618 allowed; NLCS 4-0 over the Dodgers (clincher 6-4 on 15 Oct); ALCS Rays 4-2 after losing Game 1; preview's Martinez 24-9 and Misiorowski 1.80/252/0.80/104.8 mph/11 days/4⅓ innings | **all verified, no change** |
| MTL Canadiens @ CHI Blackhawks | `IHO-199984` | `startTimeUTC 2026-10-24T00:00:00Z`, United Center; MTL 4-3-2, 30/34, home 3-2-1, road 1-1-1, streak OT1; CHI 3-6-0, 21/36, home 3-2-0 | **all verified, no change** |
| TBL Lightning @ COL Avalanche | `IHO-199985` | `startTimeUTC 2026-10-24T01:00:00Z`, Ball Arena; COL 5-4-1, 41/31, home 3-1-1, streak L2; TBL 7-2-0, 31/23, road 2-2-0, streak W3; goals-for leaderboard CAR 47, EDM 47, TOR 43, BOS 42 | **all verified, no change** |
| Leinster v Munster | `RGU-14`, `RGU-609578` | Round 4, Sat 24 Oct, KO 18.00 IRE & UK; Leinster 8 pts (75/58), Munster 9 pts (72/74); Round 3 LEI 29-5 CAR, ULS 26-26 MUN | **ordinals wrong — repaired (FL-184)** |
| DHL Stormers v Scarlets | `RGU-609580` | Sat 24 Oct 15.00 IRE & UK, DHL Stadium; Stormers 11 pts (81/54); Scarlets 7 pts (68/85); Round 3 STO 39-22 SHA, SCA 27-26 BEN | **ordinals wrong — repaired (FL-184)** |
| Vodacom Bulls v Ulster | `RGU-609576` | Sat 24 Oct 12.45 IRE & UK, Loftus Versfeld; Bulls 11 pts (126/54); Ulster 8 pts (88/93); Round 3 BUL 57-15 LIO, ULS 26-26 MUN | **ordinals wrong — repaired (FL-184)** |
| Perugia v Prata (and the other two SuperLega ties) | `VOL-27`, `VOL-36997`, `VOL-28`, `VOL-29` | Giornata 1: Cuneo 2-3 Perugia (Perugia 114 points to 95); Prata 3-1 Monza (94 to 91); Verona 0-3 Civitanova (78 to 65); Padova 0-3 Piacenza (56 to 75); all three fixtures fixed for 25 October | **all verified, no change** |
| Nemo Rangers v St Finbarrs | `GAF-01`, `GFA-3530` | Sunday 25 Oct, 4.00pm, SuperValu Páirc Uí Chaoimh (calendar `20261025T160000`, `ctz=Europe/Dublin`); Nemo 1-15 to 0-16 and 1-20 to 1-17; Barrs 2-12 to 0-16 plus the quoted "convincing" Carbery win | **all verified, no change** |
| NY Knicks @ BOS Celtics; HOU Rockets @ SA Spurs | `BKB-534842`, `BKB-534841` | TD Garden 7:00 PM ET; Moody Center, Austin 9:30 PM ET | **fixtures and times verified; records and scoring lines not re-read — stated, not implied** |

The two basketball pieces are the one gap in this pass: their win-loss records, Durant's 30-point
opener and Castle's 24 points were not re-read, because the standings page was not fetched inside
the budget. That is written down here and in `data/official.json` rather than left to look verified.

## 3. The repair (FL-184)

Five ordinals, four write-ups. They were correct when written and were overtaken at about 21:00Z,
when the three Friday Round 4 matches finished and moved the table:

| Row | Published | Table on 23 Oct |
|---|---|---|
| `RGU-14`, `RGU-609578` | Leinster tenth, Munster ninth | Leinster **11th**, Munster **10th** |
| `RGU-609580` | Stormers fourth, Scarlets twelfth | Stormers **5th**, Scarlets **13th** |
| `RGU-609576` | Bulls third, Ulster eleventh | Bulls **4th**, Ulster **12th** |

Every other figure in those four pieces — points, points-for, points-against and each Round 3
scoreline — still agrees with the table and was left alone. The phrase "after Round 3" was replaced
with "published on 23 October", because the table now carries four rounds for Edinburgh, Cardiff,
Connacht and Zebre.

**The model was not repriced, and here is why that is safe.** The six clubs behind these picks carry
identical points, points-for and points-against in the stored 21 October table and the 23 October
table; only their ordinal moved, because four *other* clubs played. The probability inputs behind
the published prices are therefore unchanged. That check is recorded in
`data/official.json → reread_20261023T2130.urc_table_position_check`.

## 4. Disclosures recorded instead of repaired

| Flag | What it is | Why it is not a repair |
|---|---|---|
| `FL-185` | OLBG's public listings render their tables client-side: `/betting-tips`, `/Tennis/3` and `/Ice_Hockey/13` all return "No tips found" while the same site's event pages render in full | A repair would mean inventing fixtures. Recorded with the three URLs and the exact page text |
| `FL-186` | OLBG marks every market on tonight's Canadiens–Blackhawks page "Expired" at 21:30Z, with the NHL start still 1h20m away | OLBG's label is not evidence of a start; our clock comes from the NHL's UTC timestamp |
| `FL-187` | The NHL's standings service and its stats service disagree on season totals (MTL 30 v 28 goals for, COL 31 v 30 against, EDM 47 v 46) | Moving a quoted figure to match a *different* official source is exactly the over-correction recorded as FL-171. Both write-ups stay pinned to the endpoint they cite |
| `FL-188` | Five-a-day target re-measured at 21:35Z: 0 of 15 sports reach it, shortfall 63 of 75, 12 unique live fixtures in 6 sports | Nothing was promoted to close it. `CRK-17` and `HBL-28` stay medium because the ICC and the Danish league print only reader-zone or unlabelled clocks |
| `FL-189` | The retriever served the MLB Game 1 preview under the title "undefined" and a different canonical path | The facts were corroborated against MLB's own schedule and standings feeds before use |

## 5. What was deliberately not done

- **No new fixtures.** With no readable listing, adding a fixture would mean claiming an OLBG row
  that cannot be pointed at. `FL-185` publishes the blocker instead.
- **No clock renewal.** `scripts/verify_live.py` rebuilds `data/release_checks.json` deterministically
  from the committed probe payload, so an editorial renewal is overwritten on the next build. Rather
  than fake durability, the file was left byte-identical; the 16:28Z–19:36Z observations were already
  inside their 24-hour window at the 21:37Z build clock, so no live selection needed renewing.
- **No repricing.** Published prices, probabilities and grades are unchanged in this pass.
- **No change to a sibling's work.** `assets/release.js` and its mirrors, the workflows, the release
  gate logic, the parsers and every sibling register item are untouched.

## 6. Verification performed

```
python3 -m unittest discover -s tests        → 271 tests, OK, 25 skips (29 new in this pass)
python3 scripts/check_board.py               → PASS (359 rows / 311 fixtures / 48 outright / 270 verified / 310 priced / 85 predictions)
python3 tools/check_site.py                  → PASS (20 pages / 180 fixtures / 8 HIGH / 31 pieces / 174 flags)
python3 scripts/check.py                     → PASS (53 fixture rows)
python3 scripts/check_links.py               → PASS (108 pages / 2,260 local links / 0 broken)
python3 scripts/build_site.py --snapshot     → root snapshot refreshed; "11th on 8 points" present in predictions.html
```

## 7. Sources read (all https, all quoted in `data/raw/probe-655b300a/reads.json`)

- Lega Pallavolo Serie A, regular-season calendar (the authority on home side and local clock) — <https://www.legavolley.it/calendario/?idCampionato=999>
- MLB schedule service — <https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-30>
- MLB standings, NL — <https://statsapi.mlb.com/api/v1/standings?leagueId=104&season=2026>
- MLB postseason results — <https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-11&endDate=2026-10-22>
- MLB Game 1 preview — <https://www.mlb.com/news/rays-brewers-world-series-game-1-starting-lineups-and-pitching-matchup>
- NHL schedule — <https://api-web.nhle.com/v1/schedule/2026-10-23>
- NHL standings — <https://api-web.nhle.com/v1/standings/2026-10-23>
- NHL stats service (comparator) — <https://api.nhle.com/stats/rest/en/team/summary>
- URC fixtures — <https://www.unitedrugby.com/latest/news/2026-27-fixtures-in-full/>
- URC table — <https://stats.unitedrugby.com/match-centre/table/2026-27>
- SuperLega results — <https://www.legavolley.it/risultati/?IdCampionato=999>
- Cork GAA final — <https://gaacork.ie/event/mccarthy-insurance-group-premier-senior-football-championship-final/>
- NBA schedule, 23 October — <https://www.nba.com/schedule?date=2026-10-23>
- OLBG all-sports listing, Tennis and Ice Hockey listings, and the MTL @ CHI event page (see FL-185, FL-186)

## 8. The SuperLega home-away question, settled from the league's own calendar

Earlier passes left one item open: whether `VOL-27`, `VOL-28` and `VOL-29` named the right home side.
The matrix on `legavolley.it/risultati` puts the date of a fixture in the cell where that row's team
hosts that column's team. Read as "venue v opponent" it appears to put Padova at home to Civitanova
and Verona at home to Monza — the reverse of what is published. That reading is wrong, and acting on
it would have flipped two high-confidence picks.

The dated calendar settles it, because it prints a venue on every line:

| Row | Official calendar entry | Published | Verdict |
|---|---|---|---|
| `VOL-27` | 2ª Giornata #7, Sun 25/10 18:00, **Sir Susa Scai Perugia (Casa)** v Tinet Prata, Pala Barton Energy, Perugia | Perugia at home | **confirmed** |
| `VOL-28` | #10, Sun 25/10 18:00, **Cucine Lube Civitanova (Casa)** v Pallavolo Padova, Eurosuole Forum, Civitanova Marche | Civitanova at home | **confirmed** |
| `VOL-29` | #12, Sun 25/10 18:00, **Vero Volley Monza (Casa)** v Rana Verona, OpiquadArena, Monza | Monza at home | **confirmed** |

**The clocks were right too, and that resolves a sibling's open flag.** Italy returns to CET on 25
October, so 18:00 local is 17:00Z — exactly what all three rows carry. The same arithmetic resolves
`FL-181` (`session-a87a3681`): Volleyball World prints "17:00 (UTC) / 13:00 (GMT-04:00) / 18:00 (Local
Time)" for the same round, and its own page header says "25 Oct 2026 – 17:00 Local Time" for the tie
the league lists at 17:00 local, i.e. 16:00Z. The two committed starts — `VOL-36994` at 16:00Z and
`VOL-36997` at 17:00Z — are the league's times; the broadcaster's "(UTC)" line is the one that is
wrong. Nothing was moved, and the note was added to `FL-181` as an additive cross-reference rather
than by editing that session's entry.

Round 1 was re-read at the same time and agrees with every figure already published: Verona 0-3
Civitanova, Modena 0-3 Trentino, Padova 0-3 Piacenza, Cisterna 3-0 Milano, Cuneo 2-3 Perugia, Prata
3-1 Monza.

## 9. This pass's own defect: a stamp written from memory, not from the clock

The first revision of every receipt, register entry and audit line in this pass carried the
observation stamp `2026-10-23T22:40Z`. The build clock was `21:37Z`. The stamp was therefore a
statement about a read that had not happened yet — while the reads themselves were real and had
finished a few minutes earlier.

It was caught by the test this pass added, on its first run against the real clock:
`TestReadReceipts::test_observation_clock_is_dated_and_not_in_the_future` asserts that
`reads.json → observation_clock_utc` is not later than `data/publication.json → publication_as_of`.
It failed exactly as it should:

```
AssertionError: '2026-10-23T22:40:00Z' not less than or equal to '2026-10-23T21:37:00Z'
```

**What was re-dated, and what was not.** The stamp, and only the stamp: `reads.json`, the
`data/official.json` block (renamed `reread_20261023T2240` → `reread_20261023T2130`), the
`FL-184`–`FL-189` entries, this document and the README paragraph. Every quoted figure, source URL
and prose repair stands unchanged, because each was read before it was written. `FL-190` records it
in the register rather than letting a silent edit hide it — the same standard this project applies
to every other session's dated evidence.

**The lesson, since it generalises:** a stamp is a *claim about when evidence existed*, so it has to
be read from the clock like any other value, never typed from an estimate. The sandbox clock is the
only clock this environment has; the CI runner advances `data/publication.json` itself at the start
of every build, which is why a hand-written stamp can disagree with it by an hour and go unnoticed
until a test asks the question.

## 10. A second, independent read — from the repository's own runner

This session's push triggered the `Live OLBG listing capture` workflow, which committed a probe of its own:
`data/raw/official-20261023T2144Z`. That gave a second official read of the three clock-critical fixtures,
76 minutes after the retriever pass and from a completely different network:

| Row | 16:28Z probe | 21:44Z runner probe | Verdict |
|---|---|---|---|
| `IHO-199984` | MTL @ CHI `2026-10-24T00:00:00Z` | game 2026020166, same start, `gameState FUT` | **confirmed twice** |
| `IHO-199985` | TBL @ COL `2026-10-24T01:00:00Z` | game 2026020167, same start, `gameState FUT` | **confirmed twice** |
| `BSB-01` | gamePk 849805, `2026-10-24T00:00:00Z` | gamePk 849805, same start, American Family Field | **confirmed twice** |

The same probe yields the next fixtures for those clubs — Game 2 of the World Series (`849802`) is
`2026-10-25T00:00:00Z` at the same ballpark, and the Canadiens, Avalanche and Blackhawks all play again on
25–26 October — none of which is used here, because a fixture the OLBG capture does not carry cannot be
priced. The probe's `nba_schedule` request returned **403**, the same block recorded elsewhere as FL-046.

**Why no release clock was renewed from it.** `scripts/verify_live.py` only writes a certified clock when a
fixture in the probe matches a row in the harvest it is given, and the 21:35Z harvest carried **zero tip
rows** (six comment lines, no data) because OLBG rendered nothing. It reported `matched fixtures: 0`, so
nothing was renewed — correctly. The 16:28Z–19:36Z observations remain the newest certified readings and are
well inside their 24-hour window, so every live pick is still eligible on the evidence it cites.

## 11. Publication

- **PR:** [#157](https://github.com/buffedlizard55-lab/OLBG3/pull/157) — CI `Verify and publish dashboard` success on
  head `d9b480a` (run 40028859199); `Live OLBG listing capture` run 40028660939 ran alongside it.
- **Merged:** 2026-10-23T21:46:30Z as `88d8ed8`, immediately, per the standing instruction not to wait for review.
  One rebase was needed: `session-a87a3681` merged PR #158 while this pass was running, so the branch was
  re-merged onto `db7c864` and rebuilt before the final push.
- **Pages:** `Verify and publish dashboard` **success** on `main`, `pages-build-deployment` **success**, and the Pages
  API reports **built** at `8f91051` (2026-10-23T21:49:15Z).
- **Deployed content checked in `origin/main`, not inferred from a green tick:** both flagged pages carry FL-184 and
  FL-190, the register holds 182 items, `predictions.html` carries "sit 11th on 8 points" and
  `olbg/predictions.html` "Leinster eleventh on eight points", and neither page carries the superseded ordinals.
