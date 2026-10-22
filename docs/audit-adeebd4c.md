# Independent repository-state audit — 22 October 2026, 12:04 UTC

## Result and verification boundary

This is a structural audit, **not a fresh line-by-line factual verification**.
The environment permits outbound connections to GitHub and package registries only.
A direct request to https://www.pdc.tv/ failed with curl exit 35 (SSL connection failure).
No claim about the availability of that website outside this sandbox follows from that result.

Official sources retained for manual review include:
- PDC: https://www.pdc.tv/
- MLB schedule: https://www.mlb.com/schedule/2026-10-23
- NHL standings: https://api-web.nhle.com/v1/standings/2026-10-22
- WST match centre: https://www.wst.tv/matches/
- All row-specific links remain on the site's Verification, Source health and Flagged for Review pages.

These URLs were **not successfully retrieved in this audit**. Existing source quotes,
verified labels and checked-at values describe inherited records, not new observations.
No source timestamp, match fact, form statistic, probability, prediction or betting line
was updated on the strength of a passing validator. No missing factual values were filled.
The captured board cannot be certified complete or current, and model confidence is not
a calibrated winning probability or evidence of a bookmaker edge. Verification of every
available market and every prediction's factual accuracy remains incomplete.

## Reproduced checks

- 60 unit tests passed (59 inherited plus file-closure regression test).
- Root board validator: 230 rows, 202 fixtures, 28 outright/race records, 210 priced;
  217 stored official confirmations and 67 written pieces. These counts are stored states,
  not independently certified facts. Fixture verification includes 193 official and nine
  club-official records according to the stored classifications.
- Separate OLBG track: 275 rows and originated-line records, 47 written pieces,
  22 model-high eligible rows at the stored snapshot clock. Track counts are not additive
  unique fixture coverage and do not imply that selections are still eligible at reading time.
- Full existing pipeline rebuilt both site tracks successfully.
- Source-feed validator passed with 40 stored official-feed fixture rows; its betting fields
  remain blank by design.
- Combined local-link scan: 85 pages, 1,529 local links checked, zero broken links.
  This does not test external source URLs or factual entailment.

## Repairs

1. Corrected stale README counts without rewriting inherited audit history.
2. Fixed an unclosed source JSON handle in `snapshot_utc()` using a context manager.
   Added a regression test asserting that the file context exits; clock semantics unchanged.
3. Published FL-077 on both generated Flagged for Review pages to make the current
   independent-verification limit visible to readers.

## Publishing

The existing site uses GitHub Pages' legacy main-branch root publisher, confirmed through
GitHub's Pages API. Keep the repository's configured publication mode; do not assume that
an Actions artifact deploy ran when it was skipped. PR, check and Pages build results are
recorded in `COORDINATION.md`. Live HTTP smoke testing of github.io is also outside this
sandbox's network allowlist; Pages API build status is not equivalent to a browser smoke test.
