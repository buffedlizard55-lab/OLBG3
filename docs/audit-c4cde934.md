# Audit — session-c4cde934 (task-46), 2026-10-23T16:18Z

## Scope claimed
Freshness audit at the real 2026-10-23 clock, expired-pick safety, full check suite,
FL registration, rebuild of the `/olbg/` track, PR/merge/Pages. No new fixture, form,
injury or price claim was added, because no new official-source verification pass for
23-Oct fixtures was completed; unconfirmable items stay blank/`unverified` (see FL-131).

## Sources read this session
| Read at | Source | Use |
|---|---|---|
| 2026-10-23T16:18Z | https://www.olbg.com/betting-tips | Re-read only. It still rendered the 22-Oct slate labelled "Today" (e.g. TB Rays @ MIL Brewers, event 160789; Jonny Clayton, event 32335), inconsistent with the calendar clock. **No fixture was re-dated from that label.** |
| 2026-10-23 (repo) | `data/lines.json`, `data/flagged.json`, `scripts/board_dates.py`, `scripts/release.py`, `tools/originate.py`, `tools/check_site.py` | Line-by-line mechanism audit below |

## Findings (line by line)
1. **Pre-rebuild failure (real defect, now repaired by rebuild):** `python3 tools/check_site.py`
   on the committed `/olbg/` track FAILED: "high pick ICH-199940/199931/199933/199941/199932
   kick-off 2026-10-22 has already passed" (`tools/check_site.py:278`, real UTC date via `build_date()`).
2. **Mechanism verified:** `tools/originate.py:496-503` already demotes any row whose
   `date_iso < BUILD_DATE` (`kick_off_passed_archived`); the committed data was simply a
   22-Oct build. Re-running the documented pipeline on 23-Oct: HIGH **22 → 17**.
3. **Root track measured, not silently rebuilt:** `scripts/board_dates.py:snapshot_utc()`
   is deterministic (newest stored official observation, 2026-10-22T22:10Z) by design for
   byte-reproducible CI. Measuring at `OLBG_NOW_UTC=2026-10-23T16:18Z` through
   build/gap/model/brief/build_site leaves **4 root HIGH**; published pages also re-check
   expiry in the browser (`assets/release.js`). The override build was reverted, not committed.
4. **Remaining `/olbg/` HIGH (17, all start ≥ 2026-10-23, all 1.40–101.00, all prob < 0.70):**
   Basketball 5, Rugby Union 5, Baseball 1, Cricket 1, Darts 1, Gaelic Football 1, Golf 1,
   Motor Racing 1, Volleyball 1. Tennis, Snooker, Handball, Rugby League, Greyhounds and
   Ice Hockey have **0** — the brief's 5-per-sport target for 2026-10-23 is **unmet** (FL-131).
5. **Not done, honestly:** no new 23-Oct OLBG harvest rows, no new ≥30-word predictions,
   no injury/form claims. "Greater than 70%" market-price picks were not manufactured;
   the band/probability gates in `tools/check_site.py` were re-run and pass.

## Verification performed
- `python3 -m unittest discover -s tests` — see COORDINATION.md final record.
- `python3 scripts/check_board.py`, `tools/check_site.py`, `scripts/check.py`, `scripts/check_links.py` — see COORDINATION.md.
- New regression test: `tests/test_audit_c4cde934.py` (no expired HIGH, FL-131 present, demoted ids flagged).

## Irregularities flagged
- **FL-131** (new, `needs review`, on Flagged for Review): expired 22-Oct HIGH picks at the
  23-Oct clock; five-per-sport target unmet for 2026-10-23; OLBG all-sports page still
  labelling the 22-Oct slate "Today" at re-read.
