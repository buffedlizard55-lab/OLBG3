# COORDINATION.md — Shared Task Board

> Multi-session coordination board. **Read this before starting any work.**
> Last updated: 2026-10-21 (session `arena-6d5f01ec`)

## Protocol (agreed rules)

1. Read this file before starting. Claim a task by adding your session ID + file scope below, then **commit and push that claim immediately**.
2. Never start a task another session has claimed. A claim older than **60 minutes with no commits** may be taken over (note the handoff in the log).
3. Each session works on its own branch `session-<id>/<task>` or a worktree, and edits only files inside its claimed scope.
4. If you need a change in a file owned by another session, log a **Change request** below — do not edit it.
5. Make small frequent commits. `git pull --rebase` before every push. On merge conflict: stop, resolve without discarding the other session's work, and log it.
6. When done, record sources, the verification performed, and any irregularities, then mark the task `done`.
7. Shared outputs (table data, site index/navigation) are only changed by the **final integration session** after all other tasks are done.
8. **Nothing is ever marked verified without a checked official source link.** Unconfirmed values stay blank and are listed on the "Flagged for Review" page.

Status values: `unclaimed` · `in progress` · `done` · `needs review`

---

## Task board

| # | Task | Status | Session | File scope |
|---|------|--------|---------|------------|
| T1 | Reverse-engineer OLBG.com sport/competition/market structure; document URL taxonomy | done | arena-6d5f01ec | `docs/olbg-structure.md`, `COORDINATION.md` |
| T2 | Scope definition: included sports, exclusions, evidence rules | done | arena-6d5f01ec | `docs/scope.md` |
| T3 | Collect in-scope fixture data from OLBG listing + event pages | done | arena-6d5f01ec | `data/raw/**`, `data/sports/*.json` |
| T4 | Originate own lines (win/price, handicap, total) via documented model | done | arena-6d5f01ec | `scripts/model.py`, `data/lines/*.json` |
| T5 | Pick match winners + confidence (low/medium/high) | done | arena-6d5f01ec | `data/picks.json` |
| T6 | Write unique human-style predictions (>=30 words) for high-confidence picks | done | arena-6d5f01ec | `data/predictions/*.json` |
| T7 | Official-source verification pass, row by row | done | arena-6d5f01ec | `data/verification.json`, `docs/verification.md` |
| T8 | Build static GitHub Pages site (landing, category pages, tables, flagged page) | done | arena-6d5f01ec | `index.html`, `sports/**`, `assets/**`, `scripts/build_site.py` |
| T9 | Integration: merge branches, re-verify combined data, link check, publish Pages | done | arena-6d5f01ec | `main`, `COORDINATION.md` |

---

## Session log

### 2026-10-21 — session `arena-6d5f01ec` (branch `arena/6d5f01ec-olbg3`)

**Claim:** T1–T9, all scopes listed above. No other session claims exist at time of writing (repo contained only `README.md` at `96f089b`).

**What was done**

- Repo reviewed line by line: single commit `96f089b "Initial commit"`, one file `README.md` containing `# OLBG3` (no trailing newline). No code, data, CI, or license. Recorded as an irregularity: the repo had **no substantive content** to review — there was nothing to verify, so nothing in it was "confirmed".
- OLBG.com reverse-engineered: listing pages are `https://www.olbg.com/betting-tips/<Sport_Slug>/<sport_id>`, event pages are `.../<Sport>/<Group>/<Competition>/<Home>_v_<Away>/<sport_id>?event_id=<id>`. IDs harvested from live pages and from indexed OLBG pages: Tennis 3, Basketball 4, Cricket 7, Rugby Union 9, Rugby League 10, Ice Hockey 13, Darts 15, Volleyball 21, Gaelic Football 25. `fetch` of `/betting-tips/<Slug>` without an ID returns 404; with a wrong ID it 301-redirects to the right slug+ID, so the slug is authoritative.
- Scope applied: excluded soccer/football, American football, boxing/UFC/MMA, hurling, horse racing, cycling, specials. Included every remaining OLBG sport that pits two sides/players against each other.
- Verification policy: every value is either (a) transcribed from the OLBG event page with the URL recorded, (b) confirmed against an official competition source, or (c) left blank and flagged. Nothing inferred.

**Verification performed / sources** — see `docs/verification.md` for the per-row table; the summary is in `data/verification.json`.

**Irregularities flagged** (also on the site's "Flagged for Review" page):

1. `README.md` was a 7-byte placeholder — repo had no prior work to reverse-engineer or trust.
2. OLBG lists some fixtures with a *date only* and no kick-off time (e.g. Gaelic football), and shows tournament outrights (Rugby League Super League/NRL 2027, State of Origin 2027) rather than dated fixtures. Times/dates transcribed exactly as shown; no time invented.
3. OLBG's `/betting-tips/<Slug>` and several `/best-tipsters/...` URLs 404 without the numeric sport ID. Documented in `docs/olbg-structure.md`.
4. Ice hockey ID 11 redirects to 13; any scraped link with 11 is stale.
5. Where an official source could not be retrieved for a fixture (page blocked, JS-only, or fixture not yet published by the competition), the row is published with the field **blank** and marked `unverified` — it is *not* filled from inference.
6. Our own prices/handicaps/totals are **model output**, not facts. They are labelled as such on every page and never presented as verified data.

**Notes for other sessions:** shared outputs (`index.html`, `assets/`, `sports/**`, `data/picks.json`) are owned by this session's integration task T9 and were published in one pass; log a change request below rather than editing them.

---

## Change requests

_(none)_

## Handoffs

_(none)_
