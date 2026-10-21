# Scope

## Excluded (as instructed)

Soccer / football · American football · Boxing · UFC / MMA · Hurling · Horse racing · Cycling · Specials (TV, politics, awards).

## Included (11 sports with rows)

Tennis · Basketball · Ice Hockey · Cricket · Baseball · Volleyball · Darts · Snooker · Rugby Union · Handball · Gaelic Football.
Rugby League is also listed as in-scope but had **no dated fixtures** on OLBG at capture time (outrights only), so it contributes zero rows.

## Eligible but NOT captured in this pass (disclosed gap)

Golf · Motor racing · Greyhound racing · Esports.

They are not in the exclusion list, so they *should* be covered. They are race/tournament markets rather than two-sided fixtures and need a different schema (field, heat, outright). They are named here and on the Flagged for Review page rather than quietly dropped.

## Row count

114 fixtures, 10 verified against an official competition source, 104 published unverified with the OLBG event link attached.

## Rules applied to every cell

| Rule | Applied how |
|---|---|
| No inference | Competition, venue and time zone are left blank when OLBG does not state them. |
| No rounding of official values | Official wording is copied verbatim into `data/official.json` and onto the verification page. |
| Discrepancies are logged, not fixed | A 7–10 minute start-time offset between OLBG and the official schedule is recorded as a finding. |
| Nothing verified without a link | 10 rows carry an official link; the rest are marked `unverified`. |
| Our prices are ours | Every price is labelled model output, never a bookmaker quote. |
