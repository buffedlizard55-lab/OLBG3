# Audit — session-f00f1bf2, 2026-10-24 (task-57)

Scope: publish the written picks that the committed evidence actually supports, re-read the
official pages that can be read, and record every irregularity found along the way. No row was
re-timed by hand and no value was inferred.

## 1. What this session actually read

The shell sandbox has no outbound network (FL-077). This session's page reader does, so pages were
read through it and the URL, the read time and the exact quoted fragments were committed to
`data/raw/fetched-20261024T2240Z-f00f1bf2/manifest.json`. Anything not in that manifest is not
quoted in prose.

| Page | Read | Used for |
| --- | --- | --- |
| `https://www.ecb.co.uk/matches/113501/overview` | 22:3xZ | PAK v ENG venue, series name, squads; start printed as "13:00 (Local), 04:00 (Your Time)" |
| `https://wtafiles.wtatennis.com/pdf/draws/2026/1056/MDS.pdf` | 22:35Z | Tokyo main draw: seeds, four wildcards, first-round pairings |
| `https://www.pcb.com.pk/news-detail/...brook-s-record-double-ton-goes-in-vain.html` | 22:3xZ | Brook's record double century in a losing cause; Sri Lanka's second-highest ODI chase |
| `https://cricket.co.za/upcoming-match/world-sports-betting-eastern-storm-vs-csa-high-performance/` | 22:25Z | Pro20 Cup fixture, Willowmoore Park, 13:00 |
| `https://api-web.nhle.com/v1/schedule/2026-10-24` | 19:08:16Z (committed probe) | Ten games, explicit `Z` start instants |
| `https://api-web.nhle.com/v1/standings/2026-10-24` | 19:08:16Z (committed probe) | Records, goals for/against, home/road splits, streaks |

The NHL payloads are the repository's own committed captures under
`data/raw/official-20261024T1908Z/json/`, so every figure reused below is reproducible offline.

## 2. Published this session

Four high-confidence pieces, each with two distinct reviewed official documents and a live release
check:

| Row | Selection | Price | Estimate | Evidence |
| --- | --- | --- | --- | --- |
| `ICH-200001` | Vegas Golden Knights | 1.47 (−213) | 64% | NHL schedule + NHL standings |
| `ICH-200004` | Detroit Red Wings | 1.47 (−213) | 64% | NHL schedule + NHL standings |
| `ICH-200009` | Utah Mammoth | 1.47 (−213) | 65% | NHL schedule + NHL standings |
| `HAN-12136` | SC Magdeburg | 1.68 (−147) | 56% | EHF playing-times PDF + EHF standings |

Every quoted figure was re-checked against the committed payload: VGK 8‑4‑0, 46/36, road 3‑2‑0,
streak L2; CBJ 3‑5‑0, 20/29, home 3‑3‑0, L2; DET 4‑3‑3, road 1‑0‑2, W1; CGY 3‑6‑0, 19/38, W2;
UTA 7‑4‑0, 41/36, home 3‑1‑0, L1; TBL 7‑3‑0, 34/29, road 2‑3‑0, L1. Magdeburg 1st in Group F,
5‑0‑0, 176:140, 10 points; Kriens‑Luzern 3rd, 2‑0‑3, 158:161.

Five pieces are published as labelled analysis, not picks, because the source that carries the
fixture does not carry a zone-qualified clock: `CRI-188838` (ECB prints local and reader time only),
`CRI-188848` (CSA prints 13:00, host not on the reviewed clock list), and `TEN-902172`,
`TEN-902173`, `TEN-902175` (the WTA draw prints no clocks at all).

Two candidate figures were removed before publication because no read page supported them: an ODI
"fastest double century off 114 balls" detail and the WTA singles rankings of two players. The
draw's seed numbers stayed, because they are printed on the document.

## 3. Irregularities flagged (not hidden, not resolved by guessing)

- **FL-218** `CRI-188835`: the verification record is keyed to "Mpumalanga Rhinos vs CSA High
  Performance" while the published row is "South Africa vs Australia". Different fixture, inherited
  label. No pick was published on it.
- **FL-219** `TEN-902207`: OLBG lists Rybakina v Fernandez; the official WTA draw gives Rybakina a
  bye and Fernandez a match against wildcard Himeno Sakatsume. The fixture on OLBG has no support in
  the governing body's draw, so it stays unpicked.
- **FL-220** Golf: two reads of `/betting-tips/Golf/5` returned "No tips found." while the Bermuda
  Championship's third round was live. Nothing to publish.
- **FL-221** Snooker: same empty listing; the single captured card had already finished.
- **FL-222** Greyhounds: 83 captured cards, none upcoming at the capture clock.
- **FL-223** `ICH-200003` / `IHO-200003`: the two tracks back opposite sides of BUF @ WSH. Disclosed,
  not hand-resolved.
- **FL-224** Basketball, Darts and the two cricket clocks: NBA endpoints returned 403/500 and its
  games page renders client-side; PDC sits behind a consent wall; ECB and CSA print local clocks
  without a zone. These sports stay analysis-only until a governing body prints a zone.

## 4. Honest state of the daily target

The brief asks for five high-confidence picks per sport across fifteen sports. The measured number
after this build is on the **Brief coverage** page; it is short of 75, and the page states the
mechanical reason per sport. Nine sports have no publishable high-confidence pick today because the
listing was empty (Golf, Snooker), the cards had passed (Greyhounds), or the only available clock is
not timezone-qualified (Basketball, Darts, Tennis, and the two cricket cards above). Publishing a
pick against a clock that cannot be checked would break the brief's first rule, so those sports
publish analysis and a flag instead.

## 5. Gates run on this build

| Gate | Result |
| --- | --- |
| `scripts/check_board.py` | PASS — every row sourced, prices recompute, HIGH inside the band with a live kick-off and a written piece |
| `tools/check_site.py` | All checks passed — 20 pages, hosts reviewed, links internal |
| `scripts/check.py` | PASS — 52 fixture rows, official hosts, blank fields, unique ids |
| `scripts/check_links.py` | 110 pages, 2894 local links, 0 broken |
| `python3 -m unittest discover -s tests` | OK (401 tests, 26 skipped) — `tests/test_audit_f00f1bf2.py` added by this session |

## 6. Sources for manual review

- https://www.ecb.co.uk/matches/113501/overview
- https://wtafiles.wtatennis.com/pdf/draws/2026/1056/MDS.pdf
- https://cricket.co.za/upcoming-match/world-sports-betting-eastern-storm-vs-csa-high-performance/
- https://www.pcb.com.pk/news-detail/sri-lanka-seal-second-highest-chase-in-odi-history-as-brook-s-record-double-ton-goes-in-vain.html
- https://api-web.nhle.com/v1/schedule/2026-10-24
- https://api-web.nhle.com/v1/standings/2026-10-24
- https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf
- https://ehfcl.eurohandball.com/men/2026-27/standings/

## 7. Clock-dependent pins repaired (FL-201 class)

Three pins were armed to go red simply because fixtures kicked off, which is what turned the first
PR build red at 22:39Z:

- `tests/test_audit_a30d9bdb.py::test_nhl_picks_are_high_and_written` demanded HIGH on every
  batch row forever. It now allows a row to leave HIGH only after its own dated start has passed at
  the build clock, and then requires the piece to read as analysis with its prose intact.
- `tests/test_audit_f00f1bf2.py` (this session's own) evaluated the live release gate against the
  moving clock; it now evaluates at the batch's certification instant (2026-10-24T22:45Z).
- `tests/test_audit_170e6805.py::test_shortfalls_published_not_hidden` asserted an identity that
  stops holding once any sport exceeds five picks; main's own repair of the clamped form was kept.

A fourth, genuine divergence is *not* repaired and is flagged instead (**FL-225**): with the clock
moved to 2026-10-25T12:00Z, `today.html`'s live table shows 8 rows against 6 recomputed live picks.
At the shipping clock both agree, so it is recorded for the next refresh rather than patched blind.
