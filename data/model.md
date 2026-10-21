# How our own lines are originated

Everything on the site under "our line", "our pick", "our price", "handicap" and "total"
is a **model output**, not a published market price. No bookmaker odds appear anywhere in
the retrieved OLBG pages, so nothing is copied. This file documents the model precisely
enough to reproduce every number in `data/lines.json` with `python3 tools/originate.py`.

## Inputs (facts, from the harvest)

| Input | Source | Notes |
|---|---|---|
| Tip split (`wins/total`) | OLBG listing, stored in `data/matches.json` | Copied verbatim; never recomputed. |
| Consensus selection | OLBG listing | Copied verbatim, including "Tie", "Over 9.50" and handicap selections. |
| Home / away | OLBG fixture name, split on ` vs `, ` v ` or ` @` | Purely mechanical. `A @ B` means A away, B home. |
| Sport | OLBG sport page the row came from | 15 included sports; see exclusions. |

## Step 1 — probability from the tip split

For fixtures where OLBG's most-tipped market is a winner/money-line market:

```
p_raw    = wins / total
p_shrunk = (wins + 2) / (total + 4)          # Beta(2,2) prior, strength 4
```

The prior pulls small samples toward even money: 1/1 becomes 0.60, 3/6 stays 0.50,
9/11 becomes 0.667, 7/7 becomes 0.818.

## Step 2 — home-field shift

```
p_model = sigmoid( logit(p_shrunk) + h )
```

`h` is applied positively when the consensus selection is the home side, negatively when
it is the away side, and is zero for neutral-venue sports. `h` values are our assumptions:

| Sport | h (logit) | implied home edge at even money |
|---|---|---|
| Rugby Union | 0.18 | 54.5% |
| Rugby League | 0.18 | 54.5% |
| Basketball | 0.16 | 54.0% |
| Ice Hockey | 0.13 | 53.2% |
| Handball | 0.12 | 53.0% |
| Volleyball | 0.12 | 53.0% |
| Gaelic Football | 0.10 | 52.5% |
| Baseball | 0.10 | 52.5% |
| Cricket | 0.05 | 51.2% |
| Tennis, Snooker, Darts, Golf, Motor Racing, Greyhounds | 0.00 | 50.0% |

## Step 3 — prices

```
fair odds      = 1 / p
our quoted price = 1 / (p × 1.05)     # 5% theoretical hold, rounded to 2dp
```

Both sides of the money line are quoted, so the pair overrounds to about 105%.

## Step 4 — handicap line

```
z  = Φ⁻¹(max(p_favourite, 1-p_favourite))     capped at 0.995
hc = -round_to_nearest_half(sigma × z)          (favourite gives the start)
```

`sigma` is our assumed standard deviation of the winning margin in the sport's own unit.
These are modelling assumptions, not measurements:

| Sport | unit | sigma |
|---|---|---|
| Cricket | runs | 25.0 |
| Basketball | points | 11.5 |
| Rugby League | points | 16.0 |
| Rugby Union | points | 13.5 |
| Handball | goals | 7.5 |
| Tennis | games | 4.0 |
| Darts | legs | 3.0 |
| Snooker | frames | 2.3 |
| Baseball | runs | 2.0 |
| Ice Hockey | goals | 1.8 |
| Volleyball | sets | 1.25 |
| Golf, Motor Racing, Greyhounds, Gaelic Football | — | no handicap line |

A 0 handicap is published as `0.0` (pick'em).

## Step 5 — total line

Totals are anchored to a sport baseline rather than to per-match scoring data, because we
could not verify per-match scoring rates, team pace, weather or injuries from official
sources for every fixture. Baselines: NBA 228.5 points, European basketball 165.5, ice
hockey 5.5 goals, baseball 8.5 runs, handball 58.5 goals, volleyball 4.5 sets, tennis 22.5
games, snooker 5.5 frames (best of seven), darts 10.5 legs (best of eleven), rugby union
48.5 points, T20 cricket 320.5 runs, ODI/one-day cricket 290.5 runs. Golf, motor racing,
greyhounds and Gaelic football get no total line.

## Step 6 — pick and confidence

* Pick = the side our model favours. When the OLBG row is not a winner market, we have no
  split for the money line, so the pick comes from the home edge alone and is flagged
  `no_split_on_winner_market`.
* Outright markets (tournaments, championships, races) get **no** price or probability,
  because field size is not published on the retrieved pages. The OLBG consensus is shown
  for reference and flagged.

| Label | Rule |
|---|---|
| **high** | The match has a verified long-form prediction in `data/predictions.json`, which requires verified form/results from an official or primary source. |
| **medium** | Winner market, at least 5 tips, and `|p_model − 0.5| ≥ 0.08`. |
| **low** | Everything else: tiny samples, non-winner OLBG rows, outrights, rows with no tip data. |

In this run: 5 high, 24 medium, 108 low, out of 137 rows.

## What the model deliberately does not do

* It does not invent a probability when OLBG published no split for the winner market.
* It does not convert a handicap or total consensus into a match probability.
* It does not read the display times as authoritative (see FL-002).
* It does not use unverified form, injuries, weather, team news or travel.

## Known limitations

The single input with real information content is OLBG's tip distribution, which is a
measure of crowd sentiment, not of team strength. The shrinkage and home-edge terms are
priors. Consequently a "medium" here means "the crowd is lopsided and the sample is not
trivial", not "we have an edge". A future version should replace the crowd input with
official results and scoring data, which this environment could not fetch at fixture level.
