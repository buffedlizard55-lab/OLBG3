# OLBG3

Two layers, one published site, built by two sessions working the same repository:

| Layer | What it is | Where it is published |
|---|---|---|
| **Sports dashboard** (this session, `arena/9590abcf-olbg3`) | Reverse-engineered OLBG fixture coverage for the sports in scope, **our own originated lines** for every fixture, confidence-rated picks, verified long-form predictions for the high-confidence calls, and a flagged-for-review register. | site root — https://buffedlizard55-lab.github.io/OLBG3/ |
| **Research desk** (earlier session, `arena/90bbe96f-olbg3`) | Official-feed collectors for NHL / MLB / NBA, hourly refresh, raw evidence artifacts, link and coverage audits. Deliberately withholds picks under a stricter evidence gate. | https://buffedlizard55-lab.github.io/OLBG3/research/ |

Nothing from the research desk was deleted or overwritten. One Pages artifact is produced by
`.github/workflows/pages.yml`: the dashboard at the root, the research desk at `/research/`.

---

## Scope (dashboard layer)

Included — 15 sports: Cricket, Tennis, Basketball, Snooker, Darts, Rugby Union, Rugby League,
Ice Hockey, Baseball, Volleyball, Handball, Golf, Motor Racing, Gaelic Football, Greyhounds.

Excluded, exactly as briefed: soccer/football, boxing, UFC, MMA, American football, hurling,
horse racing, cycling, specials. Each excluded sport was located on OLBG first and its rows are
kept in `data/excluded.json`, so the exclusion is evidence-backed rather than silent.

**Open disagreement between the two sessions:** the research desk interpreted "football" broadly
and excluded Gaelic football; this layer treats Gaelic football as a separate sport, includes it,
and tags every Gaelic row `ambiguous_exclusion: true` so the block can be deleted in one step.
Flagged as FL-001 for your decision.

## Dashboard data

| Layer | Contents | Where |
|---|---|---|
| Raw harvest | 137 fixtures transcribed from 15 OLBG sport listings, with the exact URL per row | `data/raw/olbg-harvest-20261021.tsv` |
| Structured data | fixtures + verification records + exclusion evidence | `data/matches.json`, `data/verifications.json`, `data/excluded.json` |
| Our lines | probability, pick, price, handicap, total, confidence, flags for every fixture | `data/lines.json` |
| Predictions | 5 high-confidence predictions, 71–80 words, every fact sourced | `data/predictions.json` |
| Review register | 17 flagged items with sources | `data/flagged.json` |
| Site | 21 static pages | `docs/` |

### How a number gets on the site

1. **Harvest** — the OLBG listing for each included sport is transcribed verbatim, including the tip
   count (`7/7`), the percentage OLBG prints, and the market it highlighted.
2. **Verify** — an official or primary source is retrieved for the fixture where possible. Only then
   is competition, venue or start time filled in. `competition: null` with
   `competition_status: "not_stated_by_source"` means OLBG never said it and no source was found.
3. **Originate** — the tip split is shrunk with a Beta(2,2) prior, shifted by a sport-specific home
   edge, converted to a price at a 5% theoretical hold, and turned into a handicap
   (`−Φ⁻¹(p) × σ_sport`) and a total line. Full parameter tables: `data/model.md`.
4. **Rate** — `high` only with a verified prediction; `medium` for a winner market with ≥5 tips and
   `|p − 0.5| ≥ 0.08`; everything else is `low` on purpose.
5. **Publish** — `tools/build_site.py` renders `docs/`; `tools/check_site.py` fails the build on a
   broken link, an unreviewed external host, a table row without a source, or a prediction under
   30 words.

## Reproduce

```bash
python3 tools/build_dataset.py   # TSV + verifications -> data/matches.json
python3 tools/originate.py       # matches -> data/lines.json
python3 tools/build_site.py      # data -> docs/
python3 tools/check_site.py      # integrity checks
```

Dashboard layer: Python 3.11+, standard library only, no dependencies.

Research desk layer (unchanged, see its own notes below): `python scripts/update.py`,
`python -m unittest discover -s tests -v`, `python scripts/build.py`, `python scripts/check.py`.

## Honest limitations

* **Pagination.** OLBG hides further fixtures behind "Load More Tips". Only the first page of every
  sport was captured, so absence from this dataset does not mean a fixture does not exist (FL-008).
* **Timezone.** OLBG prints clock times with no timezone, and they are internally inconsistent —
  snooker and greyhound rows behave like US Eastern, an NHL row cannot. Listed times are stored as
  raw strings and never used as a scheduled start (FL-002).
* **Competition names.** OLBG does not name the competition on most domestic listings. 26 of 137
  rows could be tied to a competition from a source; the other 111 are blank, not guessed (FL-006).
* **The model's only real input is crowd sentiment.** Tip distributions measure what OLBG's
  community did, not team strength. `medium` means "lopsided crowd, non-trivial sample", not "we
  have an edge". `data/model.md` says this plainly.
* **Sandbox networking.** `curl https://www.olbg.com/` fails in this environment with
  `SSL_ERROR_SYSCALL`, so pages were retrieved with the agent's page-retrieval tool and transcribed
  by hand with timestamps. A future run with direct HTTP access should re-harvest and diff (FL-014).

## Research desk notes (preserved verbatim from the earlier session)

Independent, source-first sports dashboard. Not affiliated with OLBG. Upcoming seven-day UTC
window; NHL coverage limited to the week the API returns. Each fixture's participants/time/status
are extracted from the linked official JSON feed; raw payloads are saved under `data/evidence/`
and archived by the workflow, not committed. Generated site is not tracked; `data/current.json` is
a bootstrap snapshot only. Sources: `api-web.nhle.com/v1/schedule/now`,
`statsapi.mlb.com/api/v1/schedule`, `cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json`.

---

Betting is 18+. Nothing here is advice; the lines are a documented model, not market prices.
