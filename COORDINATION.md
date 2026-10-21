# Coordination board

Session: `arena/3c4244bd-olbg3` (Arena-managed branch; this repository has no additional agent/session identifier exposed).

## Tasks

| Task | Status | Owner | File scope |
|---|---|---|---|
| Establish verified-data boundaries, source register, and static GitHub Pages dashboard skeleton | done (scaffold only; no match facts verified) | arena/3c4244bd-olbg3 | `COORDINATION.md`, `README.md`, `index.html`, `sports.html`, `assets/`, `data/`, `.nojekyll`, `.github/workflows/pages.yml` |
| Populate scheduled match records, originate lines, and verified picks | needs review | arena/3c4244bd-olbg3 | `data/` |
| Final integration, build/link checks, and GitHub Pages publication | in progress | arena/3c4244bd-olbg3 | shared site files, GitHub Pages settings/deployment |

## Scope and constraints

- The checkout initially contained only `README.md`; no prior task board or agent claims existed.
- User requested full current fixtures and independently originated betting lines. Do not invent fixtures, odds, results, current form, injury information, or predictions. Data remains blank/explicitly unverified until an official source can be inspected and cited per row.
- This session is confined to the Arena-provided branch `arena/3c4244bd-olbg3`; repository/session instructions prohibit switching to the separately requested `session-&lt;id&gt;/&lt;task&gt;` branch.
- Initial source access is limited to GitHub-related hosts, so direct OLBG and sports governing-body pages cannot be inspected here. Links in the dashboard are discovery/reference links, not claims that their present contents were independently verified.

## Verification and irregularities

- Initial review: repository contained only a seven-byte README and no application, datasets, workflows, or `COORDINATION.md`.
- No match-level claims have been verified. Current fixtures, market prices/lines, form, match histories, and high-confidence picks are unverified/not populated. The dashboard must surface this explicitly instead of fabricating values.
- Dashboard verification performed: `node --check` passed for both browser scripts; Python validated JSON parsing, unique provisional category IDs, HTTPS source-link shape, existing local assets, and all five landing-page fragment links; `git diff --check` passed. These are build/data-structure checks, not validation of live sports facts or remote sites.
- Data contains zero match records, so there are no match-table rows lacking an official source. Each future row schema requires `matchSourceUrl`; every market schema requires source URLs and verification timestamp.
- Provisional source-discovery links recorded in `data/sports.json` (all unaccessed/unverified in this session): Badminton World Federation (`https://bwfbadminton.com/`), MLB (`https://www.mlb.com/`), NBA (`https://www.nba.com/`), ICC (`https://www.icc-cricket.com/`), PDC (`https://www.pdc.tv/`), PGA TOUR (`https://www.pgatour.com/`), NHL (`https://www.nhl.com/`), World Rugby (`https://www.world.rugby/`), World Snooker Tour (`https://www.wst.tv/`), ITTF (`https://www.ittf.com/`), ITF (`https://www.itftennis.com/`), and FIVB (`https://www.fivb.com/`). These are not represented as verified event citations.
- Irregularities: direct OLBG, governing-body, and event pages could not be accessed under the available network restrictions; sport scope is incomplete/provisional; no schedule, market, line, form, history or prediction has been verified. These are exposed in the site's Flagged for Review panel and README.
- A local static preview is running on port 8000. GitHub Pages deployment, PR creation/merge, and live status are not reported as complete unless confirmed through GitHub tooling.
