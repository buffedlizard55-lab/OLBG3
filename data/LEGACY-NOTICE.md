# Legacy draft — not published, not source-checked

`master_matches.json` and its generator `build_full_database.py` are a **legacy draft** from an early
pass. Nothing in the repository renders them, and they are **not** part of the published board.

Why this notice exists: the file previously marked 71 of its 76 rows `Verified` and 48 of them `High`
confidence, and its `prediction_text` fields quote precise figures — for example "won seven consecutive
EuroLeague home fixtures by an average of 11.2 points" — while the `official_source_url` on those rows is
a competition homepage such as `https://www.euroleaguebasketball.net/eurocup/` or
`https://www.atptour.com/en/scores`. A homepage cannot support a fixture-level or statistic-level claim,
so the labels were wrong. They have been replaced with `legacy draft - not source-checked`, and each row
now carries `superseded_by` pointing at the data that is actually published.

What is published instead:

| Data | Rows | Used by |
|---|---|---|
| `data/events.json` | 114 two-sided fixtures | `scripts/build_site.py` (board) |
| `data/gap_sports.json` | 23 outright/race markets | `scripts/build_site.py` (board) |
| `data/matches.json` | 137 OLBG rows as captured | `tools/build_site.py` (audit track at `/olbg/`) |

If you want to keep the legacy narratives, they need to be re-researched against fixture-level official
pages and re-graded. Until then, treat every number in `master_matches.json` as unverified. The
`Flagged for Review` page lists this file as a finding with the same link.
