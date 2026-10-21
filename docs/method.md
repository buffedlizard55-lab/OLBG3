# Method

## 1. Capture
For each in-scope sport, the OLBG listing page was read and the events transcribed into `data/sports/<sport>.json`, one record per fixture, keeping the exact strings OLBG shows (start, market, selection, tip count, percentage) and the event URL. Nothing is normalised except team-name aliases (below).

## 2. Verify
Each fixture was looked for on the competition's own site. Where found, the official wording went into `data/official.json` with the URL, and the row is marked `verified` on the site. Where not found, the row stays `unverified` and is listed on Flagged for Review.

Verified in this pass: 4 URC fixtures (URC official Match Centre), 2 NHL games (NHL.com schedule), 4 NBA games (NBA.com schedule).

## 3. Originate lines — `scripts/model.py`

| Market | Rule |
|---|---|
| Win (URC) | exp_home = mean(home PF/G, away PA/G) + 3.0; exp_away = mean(away PF/G, home PA/G); margin = exp_home − exp_away; sd = 13 pts → win/draw/loss probabilities via the normal CDF (draw = ±0.5 band). |
| Win (NHL) | exp_goals per side from official standings GF/G and GA/G; home +0.15 goals; P(home) = logistic(1.0 × goal diff). |
| Win (everything else) | Probability = OLBG consensus tip share, capped to [2%, 98%] because 0% and 100% cannot be priced. No draw is priced. |
| Handicap | Line = projected margin forced to a half-point; our standard 1.91 both ways. Only where a projected margin exists. |
| Total | Line = projected combined score floored to the next half point; 1.91 both ways. Only where an official scoring baseline exists. |
| Overround | 5% total, allocated proportionally. |

**Disclosed assumptions** (chosen constants, not measured facts): rugby home advantage +3.0 points; rugby margin sd 13.0; NHL home advantage +0.15 goals; logistic slope 1.0. They are printed on the method page of the site as well.

## 4. Pick and grade
Pick = highest model probability. Confidence is a 3-factor score:

| Factor | Points |
|---|---|
| Fixture verified against an official source | +2 |
| Official current-form data for **both** sides | +2 |
| Model probability of the pick ≥ 65% | +2 (or +1 if ≥ 55%) |

HIGH ≥ 6 · MEDIUM 3–5 · LOW ≤ 2. A consensus-only row can score at most 4 and in practice scores 2 → LOW.

## 5. Predictions
Written only for HIGH picks (13 of 114 rows after the 2026-10-21 re-verification; 5 before it, and one of those five, IHO-01, was withdrawn). Each prediction names the selection, the team/player, current form and recent results, and links the official source for every factual claim. Comparative claims ("best differential", "third-worst conceded") were re-checked against the official table before publishing. On 2026-10-21 the whole set was re-read against the official URC, Pro D2, Top 14, ICEHL, SHL and NHL pages: eight predictions were corrected (wrong league positions, a wrong round number, a mislabelled average, an unsupported "division-high" claim, and an unattributed quotation) and one was withdrawn. Claims that could not be traced to an official or primary page were deleted rather than reworded.

## 6. Build and check
`python3 scripts/model.py && python3 scripts/build_site.py && python3 scripts/check_links.py`
The link checker fails the build on any broken local link (17 pages, 150 local links, 0 broken at release).
