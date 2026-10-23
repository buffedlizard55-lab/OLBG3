# Audit — `session-a87a3681`, late evening 2026-10-23 → 24 October coverage pass

Claimed as `task-a87a3681-daily-20261024-coverage` on the shared board at 21:35Z against `main`
`6241660`. One open sibling PR (#137) exists and is already subsumed by `main`; it was not touched.

## What this sandbox can and cannot do

The page-retrieval tool **can** read `olbg.com` and the governing bodies from here, which is what
previous passes recorded as impossible for the shell. Confirmed this pass by reading the OLBG hub,
two OLBG sport listings, the NBA schedule and standings, the URC fixture list and table, PDC, Cork
GAA and Volleyball World. The shell still has no route (`curl` is 403/SSL-blocked), so no OLBG HTML
capture can be produced locally; the CI capture workflow was triggered instead
(`.harvest/request.json`, 21:35Z, run 40026987297).

## Read this pass, in order, with what each established

| # | Source | What it established |
|---|---|---|
| 1 | `https://www.olbg.com/betting-tips` | Hub page served; **"No tips found."** — no listing rows in the served text |
| 2 | `https://www.olbg.com/betting-tips/Ice_Hockey/13` and `/Ice_Hockey/NHL/13` | Both sport pages served fully; both render **"No tips found."** at 21:30Z |
| 3 | `https://www.nba.com/schedule?date=2026-10-23` | All 12 Friday games with venue and **ET** tip-off: CHI@MIL 7:00 PM ET was already live; ATL@CHA, DAL@IND, MIN@ORL, NYK@BOS, TOR@WAS 7:00; DET@MIA 8:00; HOU@SAS and NOP@UTA 9:30; MEM@GSW, LAC@LAL, POR@SAC 10:00 |
| 4 | `https://www.nba.com/standings` | 2026-27 records: PHI and OKC 2-0; ATL, CHA, IND, MIN, TOR, WAS, DET, HOU, POR, LAL, LAC, MEM 1-0; NYK, BOS, ORL, MIA, DAL, SAS, UTA, GSW, SAC 0-1, with home/road and streak columns |
| 5 | `https://www.unitedrugby.com/latest/news/2026-27-fixtures-in-full/` | Round 4 Saturday 24 Oct: Bulls v Ulster 12.45, Stormers v Scarlets 15.00, Benetton v Glasgow 15.00, **Leinster v Munster "TBC, Dublin" 18.00**, Ospreys v Dragons 19.45, all **IRE & UK** |
| 6 | `https://stats.unitedrugby.com/match-centre/table/2026-27` | Table **after Friday's Round 4 games**: Edinburgh 19 pts (4 GP), Sharks 15 (4), Glasgow 13 (3), Bulls 11 (126-54), Stormers 11 (81-54), Connacht 10 (4), Cardiff 9, Lions 9, Dragons 9, Munster 9 (72-74), Leinster 8 (75-58), Ulster 8 (88-93), Scarlets 7 (68-85), Ospreys 6, Benetton 5, Zebre 2 |
| 7 | `https://gaacork.ie/event/mccarthy-insurance-group-premier-senior-football-championship-final/` | Final Sunday 25 Oct, **4.00pm**, SuperValu Páirc Uí Chaoimh; Nemo 1-15 to 0-16 Carrigaline and 1-20 to 1-17 Castlehaven; St Finbarrs 2-12 to 0-16 Clonakilty; Carbery win described with **no scoreline** |
| 8 | `https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30000/` | Perugia's Round 1: 3-2 at Cuneo (25-18, 7-25, 15-25, 25-21, 23-25), Reggers 18, Semeniuk 13, Perugia block 7 — the Perugia write-up's statistics are supported |
| 9 | `https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30003/` | Trentino v Cisterna, Trento, 25 Oct, "17:00 Local Time"; Upcoming module prints **17:00 (UTC) / 13:00 (GMT-04:00) / 18:00 (Local Time)** — internally inconsistent |
| 10 | `https://www.pdc.tv/news/2026/october/19/...schedule-confirmed/` | Consent wall in the retriever (8 chunks of cookie policy, no article text) — darts clocks **not** re-read |
| 11 | `https://www.premiershiprugby.com/fixtures`, `https://site.api.espn.com/.../scoreboard?dates=20261022` | Premiership page is client-rendered (no fixtures in the served text); ESPN returned a 7-chunk JSON payload that is not an official league source, so nothing was taken from either |

No page produced a fixture, price, kick-off or grade that is not quoted above.

## Defects found and repaired (register FL-177 … FL-183)

| Flag | Severity | Finding | Repair |
|---|---|---|---|
| `FL-177` | high | `GFA-3530` published a Carbery quarter-final scoreline (`4-23 to 1-11`) and a `+31` five-game aggregate that the Cork GAA page does not print. This is the same claim class as `FL-172`, so the earlier repair never reached the `/olbg/` piece. | Prose now quotes only the printed scorelines and says the Carbery margin is not printed. Selection, price and grade unchanged. |
| `FL-178` | medium | `RGU-609578` asserted "Aviva Stadium" while the URC fixture list prints **TBC, Dublin**. | Rewritten as a Dublin venue the URC lists as TBC. |
| `FL-179` | medium | `BKB-534841` quoted two individual scoring lines (Durant 30, Castle 24) that neither cited NBA page contains. | Removed; the piece now rests on records, streaks, venue and the tip split. |
| `FL-180` | medium | Every in-scope OLBG listing rendered "No tips found." this evening, so no fresh fixture capture displaced the 17:00Z capture. | Disclosed; a CI capture was requested for evidence; nothing inferred from the empty pages. |
| `FL-181` | medium | Volleyball World's three-zone print disagrees with itself, and the two SuperLega records derived from it assign different UTC times to matches at the same local hour (36994 → 16:00, 36997 → 17:00). | Disclosed; 36994 re-certified only at the UTC figure the page prints, with the note attached; neither start is treated as certain. |
| `FL-182` | high | Five-per-sport target still unmet: 17 distinct live picks against 75. | Published with the per-sport structural reasons; nothing promoted to close it. |
| `FL-183` | low | The five new NBA picks rest on one or two games of evidence. | Disclosed in the register. |

## Picks added (seven, all in band, all with official timezone-qualified clocks)

| Row | Selection | Our price | Prob. | Clock source |
|---|---|---|---|---|
| `BKB-536035` | Atlanta Hawks ML | 1.62 (-161) | 0.585 | nba.com, 7:00 PM ET |
| `BKB-536037` | Indiana Pacers ML | 1.47 (-204) | 0.645 | nba.com, 7:00 PM ET |
| `BKB-536036` | Minnesota Timberwolves ML | 1.58 (-172) | 0.600 | nba.com, 7:00 PM ET |
| `BKB-536034` | Toronto Raptors ML | 1.54 (-185) | 0.615 | nba.com, 7:00 PM ET |
| `BKB-536038` | Detroit Pistons ML | 1.58 (-172) | 0.600 | nba.com, 8:00 PM ET |
| `ICH-199984` | Montreal Canadiens ML | 1.47 (-213) | 0.645 | api-web.nhle.com, 2026-10-24T00:00Z |
| `ICH-199985` | Colorado Avalanche ML | 1.67 (-149) | 0.570 | api-web.nhle.com, 2026-10-24T01:00Z |

Each carries a written selection of 90–140 words citing the official record it is built on, plus
the OLBG market and tip split. No injury claim is made anywhere in the seven, because no injury
report was read.

## Verification run on the final tree

```
python3 tools/build_dataset.py     # 180 rows
python3 tools/originate.py         # high=15 medium=32 low=133
python3 tools/build_site.py        # 20 pages
python3 tools/check_site.py        # PASS (180 fixtures, 15 HIGH, 38 pieces, 175 flags)
python3 scripts/model.py           # root: 250 verified / 61 unverified, 231 handicaps, 115 totals
python3 scripts/brief_coverage.py  # union 17 HIGH, 1 sport meets five, shortfall 58
python3 scripts/build_site.py      # 34 board pages
python3 scripts/check_board.py     # PASS
python3 scripts/check_links.py     # 0 broken
python3 -m unittest discover -s tests  # 242 tests OK (25 dated-pin skips)
```

Two sibling tests were updated rather than bypassed: `tests/test_audit_beb7787b.py` pinned the URC
observation stamp to 17:02Z (this pass re-read the same page at 21:32Z and renewed only the stamp,
so the assertion is now a floor), and `tests/test_audit_ebe6dc9c.py` asserted that `BKB-17` was the
only verified, upcoming, in-band, non-HIGH root row — renewing the SuperLega clock adds `VOL-26`,
which is deliberately **not** promoted because of `FL-181`.
