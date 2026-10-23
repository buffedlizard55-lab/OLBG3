# Audit — `session-d26daaf0` (task-54), night pass 2026-10-23

**Branch:** `arena/d26daaf0-olbg3` (Arena-fixed) · **Claimed** 2026-10-23T21:27Z against `main` `6241660`
**Register items:** **FL-191**, **FL-192** (drafted as FL-191/FL-192; renumbered because `session-a87a3681`
published FL-191…FL-183 first — `original_id` keeps the draft numbers)

---

## 1. What this pass set out to do, and what changed its shape

The committed capture chain was the `2026-10-23T17:22Z` observation. At claim time it was `21:27Z`, so the
board's live picks described fixtures that had already kicked off, and `data/brief_coverage.json` on
`6241660` read `live_high_union 12`, `sports_meeting_target: 0`, `shortfall_to_target: 63`. The task was a
fresh capture for the 24 Oct window, official re-verification, and in-band HIGH picks with write-ups.

Two things changed the shape of the pass, and both are recorded rather than smoothed over.

### 1a. A claim made in the pre-flight check was too strong, and is corrected here

The claim asserted that because the harness page-retriever reaches `olbg.com` where the sandbox shell does
not (`FL-077`), "a genuine fresh listing harvest is possible here". **That is false for the listing pages.**
At `21:30Z` the retriever returned, for every one of `/betting-tips`, `/Tennis/3`, `/Basketball/4`,
`/Basketball/NBA/4`, `/Ice_Hockey/NHL/13`, `/Golf/5`, `/Cricket/7` and `/Snooker/8`, an intact SEO body with
`No tips found.` where the tips table should be. The committed `16:30Z`/`17:00Z` captures, taken on a GitHub
Actions runner, carry fully populated tables at the same URLs. The retriever is usable for editorial,
event and governing-body pages; it is **not** a substitute for a runner capture on listing pages.

### 1b. The listings really are empty overnight — now established three independent ways

| Clock | Route | Result |
|---|---|---|
| 2026-10-23T19:35Z | runner capture, `session-ebe6dc9c` | all 18 listings HTTP 200, zero tip cards |
| 2026-10-23T21:30Z | harness page-retriever, this session | `No tips found.` on all 8 pages read |
| 2026-10-23T21:30Z | runner capture `data/raw/live-20261023T2135Z` | 18/18 HTTP 200, 220–309 KB each, **0** cards, `parse_gaps: {}` |

`parse_gaps` being empty is the part that matters: the pages were read successfully, they simply held no
cards. This is OLBG's overnight state, not a read failure and not a sandbox limitation.

The one listing that references a live event is **Golf**: `/betting-tips/Golf/5` links
`event_id=101904` — *"Butterfield Bermuda Championship at Port Royal Golf Course (22nd to 25th October)"*.
It appears in the page's editorial *This Week's PGA Tour Course History* section, **not** in a tips card, so
it carries no price, no tip split and no market, and cannot be priced from this capture without inventing
those. It is noted, not boarded.

### 1c. Sibling sessions held the data scope

`session-a87a3681` claimed the daily 2026-10-24 coverage pass at ~21:28Z (scope: `.harvest/request.json`,
new `data/raw/**`, `data/predictions*.json`, `data/official.json`, `data/verifications.json`,
`data/release_checks.json`, `data/flagged.json`, `data/publication.json`, `README.md`, generated outputs) and
merged **PR #156**. `session-655b300a` opened **PR #157** on a task it also numbered `task-54`. This pass
therefore narrowed to files neither claimed — `scripts/**` and its own new test module — and did not
duplicate their harvest, verification or editorial work.

---

## 2. FL-191 — an empty capture became a zero-row harvest that name-based resolution could publish

**Severity:** high · **Status:** corrected · **Reproduced, not inferred.**

`scripts/extract_listings.py` called `write_tsv()` unconditionally, so a capture with no tip cards produced
`data/raw/olbg-harvest-20261023T2135Z.tsv` — six comment lines, zero data rows. `scripts/live_refresh.py`
chose captures with `max(candidates, key=lambda p: p.name)`; its own docstring said *"the newest one by name
wins"*. The empty file therefore became the pipeline's harvest.

Two consequences, both demonstrated on this tree:

1. **CI would have gone red.** `tests/test_live_20261023.py::test_live_capture_is_the_newest` pinned the
   newest harvest filename. Running the documented pipeline produced:
   `AssertionError: 'olbg-harvest-20261023T2135Z.tsv' != 'olbg-harvest-20261023T1700Z.tsv'`. In
   `.github/workflows/pages.yml` the unit-test step runs **after** `live_refresh.py`, so an ordinary
   overnight empty capture would fail the publish job.
2. **The board could have been emptied.** Any resolver using "newest harvest TSV" instead of
   `data/meta.json["harvest_file"]` would have replaced all 180 published `/olbg/` rows with nothing. Only
   the fact that `tools/build_dataset.py` happens to read the pinned `harvest_file` prevented it — luck, not
   a guard.

**Relation to FL-180.** `session-a87a3681` had already made the test tolerate the empty file by filtering to
files that carry rows, and asserted the empty file exists. That treats the symptom and leaves both causes
live. This repair fixes the causes, and updates that test to assert the **stronger** invariant — no zero-row
harvest file may exist at all. FL-180's stated intent ("the empty later capture is kept as evidence rather
than deleted"; "the primary harvest is the newest capture that actually carries rows") is preserved and
strengthened: the evidence now lives in the capture directory (18 served HTML pages + `manifest.json` +
`extract-report.json`), where it cannot be mistaken for a harvest, and with the guard in place *newest by
name* and *newest with rows* can no longer diverge. The attribution comment is kept and extended, not
replaced.

**The repair.**

- `scripts/extract_listings.py`: on zero rows, write `extract-report.json` (the proof the listings were empty
  rather than unread), remove any stale zero-row file at the target path so a re-run is byte-stable, and exit
  `EMPTY_CAPTURE = 3` **without** creating a harvest. `--allow-empty` restores the old behaviour when an empty
  TSV is genuinely the wanted artifact.
- `scripts/live_refresh.py`: walk captures newest-first, skip any that yields no rows, fall back to the newest
  that does. `--check` reports the same choice side-effect free. If no capture carries rows, the step says so
  and changes nothing, leaving `data/meta.json["harvest_file"]` as the live primary.

**One further consequence found by running it, and handled rather than shipped.** With the fallback in place,
`verify_live.py` finally ran against real rows and rewrote `data/release_checks.json` wholesale — 1,294 lines,
including the accumulated `policy` history and the top-level `checked_at`. `scripts/check_board.py` then failed
on `BSB-01`, `IHO-199984` and `IHO-199985` with *"HIGH stored release differs from current evidence:
checked_at"*, because the pipeline computes the board (`scripts/model.py`, `tools/originate.py`) **before**
this step, so re-stamping afterwards desynchronises the stored release blocks from the evidence the integrity
check recomputes. That check is correct and was not weakened. Instead `live_refresh.py` now re-verifies only
when the capture it settles on is **newer** than the one behind the committed primary harvest; falling back to
an already-published capture means "no new capture arrived", and re-running the probe would rewrite evidence
without adding a fact. Renewing a source observation stays a deliberate data change, made and rebuilt as one.

---

## 3. FL-192 — `--out` outside the repository crashed after writing the file

**Severity:** low · **Status:** corrected · **Provenance: found by writing the FL-191 tests, not in review.**

`extract_listings.py` guarded its *capture* path with `is_relative_to(ROOT)` but printed its *harvest* path
with a bare `out.relative_to(ROOT)`. Reproduced:

```
$ python scripts/extract_listings.py --capture data/raw/live-20261023T1700Z --out /tmp/x.tsv
ValueError: '/tmp/x.tsv' is not in the subpath of '/home/user/OLBG3' …
```

The file was written, then the summary line raised and the script exited 1 — which `live_refresh.py` reads as
"extraction failed" and aborts the whole step on. No committed data was affected; every call site in the
repository passes a `--out` inside `data/raw`. Both paths now use one `display_path()` helper, so the
inconsistency cannot recur.

---

## 3b. FL-193 — the empty listings are an absence of tips, not a client-render gap

**Severity:** medium · **Status:** needs review · **Qualifies a published flag; corrects no value.**

`FL-185` (`session-655b300a`) explains the empty tips tables as client-side rendering. Comparing two
committed captures taken by the same script, the same `OLBG3Audit/1.0` user agent and the same URL
settles it the other way:

| Capture | Bytes | `div.grd.tip` cards | `itemprop="startDate"` |
|---|---|---|---|
| `live-20261023T1700Z` / `betting-tips_Tennis_3.html` | 333,779 | **8** | **8** |
| `live-20261023T2135Z` / `betting-tips_Tennis_3.html` | 294,198 | **0** | **0** |

The later page still carries 22 `event_id` hrefs from navigation and editorial links, and its
`extract-report.json` records `parse_gaps: {}` across all 18 listings, so nothing failed to parse. If the
table were rendered only in the browser, the 17:00Z capture could not have carried 8 cards.

The distinction is not academic. A rendering gap would mean tips exist that this project cannot see; an
absence of tips means OLBG's tipsters had posted nothing for the overnight window, and the five-per-sport
shortfall at that hour is a property of the source rather than of this pipeline. `FL-185`'s account of the
harness retriever receiving an un-hydrated shell is not disputed and is consistent with this — what FL-193
adds is that the **runner** route shows the same empty state, so the retriever is not why the board could not
be refreshed. Pinned by `test_the_empty_state_is_an_absence_of_tips_not_a_client_render_gap`.

---

## 4. Verification performed

Every gate below was run on this branch after the repairs, in the documented CI order
(`publication_clock` → `update` → `discovery` → `build` → `build_gap_sports` → `model` → `live_refresh` →
`build_dataset` → `originate` → `brief_coverage` → `build_site` → `check_board` → `tools/build_site` →
`tools/check_site` → snapshot → unit tests → `check` → `check_links`):

| Gate | Result |
|---|---|
| `python -m unittest discover -s tests` | **257 tests OK**, 25 dated-archive skips, 0 failures |
| `scripts/check_board.py` | PASS — 359 rows / 311 fixtures / 48 outright / 270 verified / 310 priced / 85 predictions; every HIGH inside −250…+10000 with a live kick-off and a write-up |
| `tools/check_site.py` | PASS — 180 fixtures / 180 lines / 38 predictions / **177** flagged |
| `scripts/check.py` | PASS |
| `scripts/check_links.py` | PASS — 108 pages / 2,260 local links / **0 broken** |
| `scripts/live_refresh.py --check` | names the empty capture as skipped; selects `live-20261023T1700Z` (196 cards) |
| `scripts/live_refresh.py` | skips the empty capture, re-extracts the primary **byte-identically**, skips re-verification, churns nothing but the deletion of the zero-row TSV |

New regression coverage in `tests/test_audit_d26daaf0.py` (15 tests) pins: the 18-listing/0-card evidence;
the distinct exit code; no harvest written for an empty capture; stale zero-row removal; `--allow-empty`;
`--out` outside the repo; a populated capture unaffected; no committed harvest TSV with zero rows;
`cards_in`; newest-first ordering; the `--check` choice; and that the published row count stays 180.

---

## 5. What this pass did **not** do, stated plainly

- **No new fixtures, prices, grades or write-ups.** The listings carried none to harvest. The five-per-sport
  target is still unmet and remains published as a shortfall (`FL-180`…`FL-183`, standing `FL-102`/`FL-131`
  family). Nothing was promoted, priced from an assumption, or carried over to look like coverage.
- **No source observation was renewed.** `data/verifications.json`, `data/official.json` and
  `data/release_checks.json` are untouched by this pass.
- **No sibling file was rewritten.** `data/flagged.json` is a 44-line append of two new items and nothing
  else; `.harvest/request.json` was resolved to `session-a87a3681`'s version at rebase; the duplicate
  `21:35Z` capture this session's request produced was dropped in favour of the one already merged on `main`,
  so no near-identical evidence was added twice.
- **PR #137** (`arena/22dbc477-olbg3`) was left for its owner, as two prior integration sessions adjudicated it.

## 6. Irregularities flagged for review

1. **FL-191 / FL-192** — both corrected, published on Flagged for Review with their sources.
2. **Pipeline ordering is fragile.** `live_refresh.py` sits *after* `model.py`/`originate.py` in
   `pages.yml`, so any step that renews release evidence invalidates the board just computed. This pass worked
   around it by not renewing evidence in that position; the durable fix is to move `live_refresh.py` before
   `model.py`. That file is outside this session's claimed scope, so it is **logged here as a request** rather
   than edited.
3. **Three sessions numbered a task `task-54`/`task-51`-style independently**, and two published into
   FL-191…FL-183 within minutes of each other. The renumber-on-rebase convention with `original_id` held, but
   the board has no way to reserve a range before pushing.
