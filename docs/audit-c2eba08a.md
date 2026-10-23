# Audit record — `session-c2eba08a` / task 51

**Date:** 2026-10-23 UTC  
**Scope:** browser release-state UI only  
**Branch:** `arena/c2eba08a-olbg3`  
**Base:** `3f126e6173b6a12c1955ffc9bd180ca141582381`

## Finding

The static pages use the CSS class `pill high` for two different visible concepts:

1. the confidence badge whose text is `HIGH`; and
2. the separate odds-band badge whose text is `in band`.

`assets/release.js` correctly expires a page element once its stored `data-expires-at`
cutoff is reached, but its original selector changed **every** `.pill.high` descendant to
`ANALYSIS`. On an expired pick that also changed the odds-band badge. The resulting page
could imply that the originated price had stopped being in the requested band, even though
expiry only means that the publication window ended. This was a presentation defect, not a
change to a fixture, price, source observation, confidence input, or prediction.

The affected markup is present in the current root dashboard and prediction cards. The
same asset is published in the root board and in both tracked OLBG asset trees.

## Repair

The expiry handler now reads the badge label before mutating it. Only a badge with the
semantic `badge-high` class or the exact visible label `HIGH` is changed to `ANALYSIS`.
The `in band` badge is left untouched. The three tracked copies are byte-identical:

- [`assets/release.js`](https://github.com/buffedlizard55-lab/OLBG3/blob/arena/c2eba08a-olbg3/assets/release.js)
- [`olbg/assets/release.js`](https://github.com/buffedlizard55-lab/OLBG3/blob/arena/c2eba08a-olbg3/olbg/assets/release.js)
- [`olbg-board/assets/release.js`](https://github.com/buffedlizard55-lab/OLBG3/blob/arena/c2eba08a-olbg3/olbg-board/assets/release.js)

No sports row, official source URL, odds value, confidence input, prediction text, or
Flagged for Review item was changed by this task. The source-linked sporting evidence
remains available for manual review on the [Source health page](https://buffedlizard55-lab.github.io/OLBG3/source-health.html)
and the [Flagged for Review page](https://buffedlizard55-lab.github.io/OLBG3/flagged.html).

## Verification performed

- Compared all three tracked `release.js` copies byte-for-byte.
- Confirmed the root dashboard and prediction pages contain separate `HIGH` and `in band`
  labels inside expiring current-pick markup.
- Confirmed the root and OLBG prediction pages load their local release asset.
- Added `tests/test_release_ui_c2eba08a.py`, which checks asset synchronization, the guarded
  mutation contract, the generated markup contract, and the four published page references.
- Ran the repository unit suite and the documented structural checkers after rebuilding
  locally. The sandbox cannot reach OLBG.com or the governing-body sites directly, so this
  pass did not claim any new live sports verification; network-empty feed output was not
  retained in the patch.

## Irregularities / follow-up

- This repair does not refresh the dated OLBG capture or extend the five-picks-per-sport
  coverage. Those are data and scheduled-refresh responsibilities already recorded on the
  coordination board.
- The browser layer can prevent a stale HIGH label from surviving its cutoff, but it cannot
  certify a source, settle a match, or turn an expired research item into a recommendation.
  The release banner and row-level source-health evidence remain the authority for those
  limitations.
