# Publication link audit — session 931c2e71

Audit date: 2026-10-22, approximately 20:54 UTC. Baseline: `13f31f4`.

## Delivered change

The previous local-link check scanned root HTML, root `sports/`, and generated
`site/`. It omitted the committed `olbg/` publication tree and skipped all
fragment-only links. It also treated an existing directory without an index as
a successful link and used a double-quote-only regular expression.

`scripts/check_links.py` now parses HTML attributes, covers both publication
methods, checks fragment IDs and legacy named anchors, decodes escaped paths,
requires directory indexes, and rejects paths escaping each publication root.
Project-absolute `/OLBG3/` links are resolved separately for the artifact and
legacy publishers. External URLs are not fetched and are **not verified** by
this tool. Six regression tests exercise these boundaries.

## Reproduced checks

- 75 unit tests pass, including six new publication-link tests.
- Full root pipeline: build, gap sports, model, build site, check board — pass.
- Full `/olbg/` pipeline: build dataset, originate, build site, check site — pass.
- Root snapshot regeneration and feed checker — pass.
- Combined scan: **106 HTML pages, 1,964 local links, zero broken targets or fragments**.
- Pipeline regeneration produces no tracked data or site changes.

This is structural validation, not a line-by-line factual verification of source
contents. Repository assertions have not been upgraded or independently renewed.

## Measured brief gaps, not new sporting facts

The baseline root board has 265 rows (217 fixtures and 48 outright/race rows),
242 priced rows, and 73 written pieces including analysis. The secondary board
has 298 rows/lines and 53 written pieces including analysis. The tracks overlap;
their counts must not be added together as unique fixtures. The shared register
contains 98 historical/current review items.

At the stored publication clock, the root board has 20 HIGH rows. Re-assessing
those same rows at approximately 20:54 UTC using the **unchanged stored clock
evidence** leaves 14 eligible. This does not establish source accuracy, current
availability, or that the matches are actually running. A passed scheduled start
is not proof of a result. The pages include browser-side expiry; static snapshot
counts are not a live feed.

| Sport | Root captured rows | Stored HIGH rows | HIGH rows eligible at audit time using stored clock evidence |
|---|---:|---:|---:|
| Baseball | 1 | 1 | 1 |
| Basketball | 30 | 4 | 1 |
| Cricket | 16 | 1 | 1 |
| Darts | 17 | 1 | 1 |
| Gaelic Football | 6 | 1 | 1 |
| Golf | 10 | 0 | 0 |
| Greyhounds | 22 | 0 | 0 |
| Handball | 31 | 1 | 0 |
| Ice Hockey | 25 | 7 | 5 |
| Motor Racing | 4 | 0 | 0 |
| Rugby League | 3 | 0 | 0 |
| Rugby Union | 16 | 1 | 1 |
| Snooker | 14 | 0 | 0 |
| Tennis | 40 | 0 | 0 |
| Volleyball | 30 | 3 | 3 |

These are repository counts, **not independently verified sports-source values**.
Five verified match predictions per sport per day has not been achieved. Some
sports have only outright/race entries. Complete fixture coverage, all available
markets, calibrated probabilities, current form, recent history and every
prediction's factual support have not been independently established this session.
HIGH is a heuristic evidence grade, not a validated win probability. Model prices
are estimates, not official facts or observed bookmaker offers. Do not manufacture
five picks or equate odds-band membership with a demonstrated betting edge.

## Sources and manual review

- [Original OLBG discovery target](https://www.olbg.com/betting-tips).
  Direct shell retrieval failed with curl exit 35 / SSL_ERROR_SYSCALL.
- Official sports hosts are outside this environment's outbound allowlist.
  **No new sports facts, quotes, official values, or verification timestamps were
  created. Fresh factual verification remains unverified.** Missing confirmation
  cannot be replaced with a passing URL/schema check.
- [Existing public Flagged for Review](https://buffedlizard55-lab.github.io/OLBG3/flagged.html),
  particularly FL-077 for the already-published source-access limitation.
- [Root row-level official evidence links](https://buffedlizard55-lab.github.io/OLBG3/verification.html).
  These are inherited claims requiring manual review, not sources re-read here.
- [Secondary track](https://buffedlizard55-lab.github.io/OLBG3/olbg/).
- [Workflow and deployment records](https://github.com/buffedlizard55-lab/OLBG3/actions).
  GitHub Pages API currently reports legacy main/root publication. Deployment
  outcomes will be recorded in `COORDINATION.md` after merge. Direct live-site HTTP
  smoke testing cannot be claimed from this sandbox; the workflow runs route
  smoke tests from GitHub's runner.

## Parallel-session boundary

After the initial claim, GitHub Actions revealed concurrent evening claims on
`arena/c038b7f4-olbg3`, `arena/22fd95c8-olbg3` and `arena/1cdf1d14-olbg3`.
Their coordination files were read through the GitHub contents API. Therefore
this session makes **no shared navigation, README, fixture-data, prediction,
release-clock, or generated-site edits**. It supplies only the independent link
checker, its tests, this report, and its own appended coordination log. Sibling
sessions own new harvesting and brief-coverage accounting. The default git fetch
refspec exposes only main, so absence of remote tracking branches is not proof
that no parallel session exists.
