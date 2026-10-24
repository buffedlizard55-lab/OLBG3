# session-09ecce40 — task-56: a fresh 2026-10-24 board, the executive-summary site, and 22 new sourced predictions

Claimed 2026-10-24T17:12Z on `arena/09ecce40-olbg3`, before any edit. Register items **FL-199…FL-202**.

## What the previous site did, and why it was unclear

Seven pages described the same research under four different labels — "feed track", "board track",
"`/olbg/` lines track" and "brief coverage" — and each had its own navigation. The landing page
opened with a paragraph about publication gates, not with a pick. A reader could not answer three
questions in under a minute: *what is a pick here*, *which are today's best*, and *where is the
reasoning*. The HIGH table that did exist was several tables down, and its prices were the only
numbers on the page, with nothing saying whether a price was ours or OLBG's.

Two concrete defects compounded it. The board still carried the **2026-10-23 slate** — every HIGH
pick was a match that had already started — and the words "model" and "verified" (which the brief
bans from published prose) were used throughout the reader-facing copy.

## What this pass changed

**A fresh capture, not a refreshed page.** A runner capture requested through `.harvest/request.json`
landed as `data/raw/live-20261024T1715Z`: all 18 in-scope listings, HTTP 200, **197 active tip cards
across 14 sports**, captured 17:08:24Z. Golf's listing served no card (`No tips found.`); every other
sport carried at least one. The official probe (`data/raw/official-20261024T1709Z`) returned the NHL
schedule and standings, the MLB schedule and standings, and eight governing-body text pages; the NBA
structured endpoint returned nothing, so the NBA fixture clocks were read from `nba.com/schedule`
and recorded by hand with the page's own ET label.

`data/meta.json` was repointed to the new harvest, which is the one-line change that moves the whole
board from yesterday's fixtures to today's.

**Twenty-two new predictions, each tied to an official page.**

| Sport | New HIGH pieces | Official evidence used |
| --- | --- | --- |
| Basketball (NBA) | 4 | `nba.com/schedule?date=2026-10-24` (tip times printed in ET), `nba.com/standings`, and the league's `Injury-Report_2026-10-24_01_00PM.pdf` |
| Ice Hockey (NHL) | 3 | `api-web.nhle.com/v1/standings/2026-10-24` (records, L10, home/road splits, goals for/against) and the same day's schedule payload |
| (already published, re-published on today's board) | 15 | Handball 2, Volleyball 3, Rugby Union 1, Gaelic 1, Motor Racing 1 — these fixtures are on 25–29 October, so yesterday's write-ups remain the current analysis |

Nothing was promoted to reach a number. The five-a-day target is met by **no** sport today and that
is stated on the summary page and in `FL-202`, with the mechanical reason in each cell.

**A site that answers the two questions first.** `tools/build_dashboard.py` builds:

* `index.html` — executive summary: capture clock, five headline numbers, a "start here" card, the
  complete high-confidence table (time, sport, match, **our pick**, our price, OLBG price, grade,
  sources, link to the write-up) and a coverage table naming every shortfall;
* `picks.html` — every selection, filterable by sport and grade;
* `matches.html` — every captured fixture with our money line, handicap and total, and a badge
  showing whether the start is an official clock or only OLBG's;
* `written.html` — the full predictions, one card per match, each fact linked;
* `sport/<slug>.html` — one page per sport for all 15 sports;
* `review.html` — unverified clocks and the flag register;
* `sources.html` — the rules, and the complete list of sources the live board uses.

Every row on every page carries a source link. Where the listing printed a price for the *other*
side, the table prints that side's name next to it (`3.50 (Dragons)`) so a reader cannot mistake
OLBG's price for ours on the same selection.

The builder runs **after** `scripts/build_site.py --snapshot` in `pages.yml` and writes both
publication trees itself, so a rebuild is byte-identical whichever order the two builders run in.

## Verification performed

* **15 live HIGH picks**, each with: an official, timezone-qualified start recorded in
  `data/release_checks.json`; a fixture record in `data/verifications.json`; a price inside
  −250…+10000; a win probability under 70%; and a prediction of 66–135 words.
* **NBA clocks re-derived from the printed local time, not from OLBG.** The first attempt stored the
  ET clock in the UTC field and produced a 03:30Z start for a 23:30Z tip; the release gate refused
  it (`start_utc` came back `None` with reason "Source check is later than the publication clock"),
  which is what caught the error. The records now carry the printed local clock (`19:30`) plus
  `timezone: ET`, and `release.py` converts it.
* **Clock stamps read from the system, never typed.** A first draft stamped the observations
  `17:30Z` against a sandbox clock of `17:13Z`; every stamp was re-read from `datetime.now(UTC)`.
* **Full suite:** 315 tests, 72 skipped, all passing. The skips are the dated 2026-10-23 pins, which
  now use the repository's own `archive_guard.pins()` convention (FL-144) instead of asserting that
  yesterday's slate is still live.
* `scripts/check_board.py` PASS, `tools/check_site.py` PASS, `scripts/check.py` PASS,
  `scripts/check_links.py` PASS: **129 pages, 2,593 local links, 0 broken**.

## Irregularities published rather than smoothed over

* **FL-199** — Basketball totals are originated at a flat 163.5 points for NBA games, which is not a
  plausible NBA total. No write-up quotes a total; the column is published and named as unusable
  rather than replaced by an invented number.
* **FL-200** — Two older low-graded Volleyball analysis pieces (VOL-37002/VOL-37003) share 31
  verbatim eight-word runs. They are another session's published text; they are labelled analysis,
  not picks, and are reported rather than silently rewritten.
* **FL-201** — OLBG's own `startDate` sits one hour late on two late NBA games and seven minutes late
  on the NHL slate. The official clock is used for grading; OLBG's value is preserved verbatim.
* **FL-202** — The five-per-sport target is met by no sport today; the shortfall is published with
  the reason in the same cell.

## What was not done, and why

Tennis (6 fixtures), Cricket (14), Darts (7) and Snooker (1) were captured and priced but **not**
graded HIGH, because their governing-body pages print venue-local times without a zone label
(`atptour.com`'s Almaty final reads "Not Before 15:00" with a "Use Local Time Zone" toggle, and says
nothing about which zone that is). Converting that to UTC would mean inventing a zone, which the
brief and this repository's release gate both forbid. They remain on `matches.html` at their lower
grade, with the OLBG clock labelled as such.
