# Independent structural audit — 2026-10-22

## What was checked

The existing dashboard was rebuilt from committed inputs, not from newly retrieved sports sources.
All 64 unit tests passed. Both tracks' validators passed. The combined local-link scan checked
85 pages and 1,529 links with zero broken local targets. External links and their factual contents
were **not** verified. The regenerated tracked outputs were unchanged.

The root board contains 230 rows (202 fixture rows and 28 outright/race rows), 210 priced rows,
and 67 written pieces including analysis. The separate `/olbg/` board contains 275 rows and
47 pieces. These are separate datasets, not additive coverage. Structural checks report
217 inherited verified labels and 12 unverified root rows; this audit does not independently
endorse those labels. Confidence grades are not calibrated win probabilities or proof of value.

## Defect repaired

`release.assess` previously accepted any nonempty source string and quote as official start-time
evidence. It now requires an explicit allowlisted HTTPS hostname, no credentials, and only the
default/443 port. Suffix-spoofed hosts, malformed URLs, nontext and whitespace-only quotes fail
closed with blank UTC start and expiry. Exact source clocks must be HH:MM; embedded offsets
cannot silently be overwritten by the separate timezone field. Four new regression tests cover
these boundaries. All current release source hosts remain accepted, so no match facts, source
observation timestamps, prose or confidence labels changed.

The host list is a structural trust boundary drawn from existing release evidence, not fresh
verification that any page contains the stored quote. Adding a new official source requires an
explicit code review; an unknown host cannot automatically release a HIGH pick.

## Source access and manual review

This environment permits outbound network access only to GitHub and package registries.
Consequently a fresh complete OLBG discovery and official-source, line-by-line factual audit
cannot be completed here. No new matches, bookmaker odds, official form claims or prediction
prose were invented. This remains published as **FL-077** on the
[Flagged for Review page](https://buffedlizard55-lab.github.io/OLBG3/flagged.html).

Existing official clock references for manual inspection include:
- [MLB schedule](https://www.mlb.com/schedule/2026-10-23)
- [EuroLeague preview](https://www.euroleaguebasketball.net/en/euroleague/news/game-center-round-7-el2627/)
- [ICC match](https://www.icc-cricket.com/matches/274659/afghanistan-vs-zimbabwe)
- [PDC schedule](https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/)

These are inherited references, not sources freshly retrieved in this session. The complete
row-specific manual-review links remain in `data/release_checks.json`, the verification pages,
and the sport tables. No claim of exhaustive sport/market coverage is made. Model-originated
prices must not be presented as observed bookmaker offers.

## Publication

GitHub Pages API reported `build_type: legacy`, `status: built` and the existing site URL
https://buffedlizard55-lab.github.io/OLBG3/ before this change. Final PR, CI and deployment results
are recorded in `COORDINATION.md`. Direct public-site HTTP/browser testing is unavailable
under this sandbox's allowlist; GitHub deployment success is not a live content inspection.
