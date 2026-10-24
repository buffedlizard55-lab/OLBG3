# Independent audit — originated selection versus OLBG market label

**Session:** `session-7e9f21a6`  
**Evidence read:** 2026-10-24 22:26–22:28 UTC  
**Scope:** two live executive-summary examples and the rendering path. This is a presentation/provenance audit, not a re-grade or new prediction. No sporting-data values were changed.

## Finding

The merged pick card puts an OLBG-captured market label beside the independently originated selection and price without identifying whose market the label describes. A reader can therefore interpret an OLBG market as the market for which the project's own price was originated. This is especially misleading when the OLBG market and our selection are different bet types.

The implementation is direct: `scripts/pick_surface.py::collect` assigns `r['olbg_market']` to the root track's `market` field; `card_html` renders that field adjacent to the project's own selection, price, and estimated probability. The OLBG lines track likewise takes its `market` from `matches_olbg[*].olbg_market`. The generated [executive-summary pick page](https://buffedlizard55-lab.github.io/OLBG3/today.html) demonstrates the resulting presentation.

| OLBG event | Values shown / captured | Independent selection/price | Live-source observation | Fixture source |
| --- | --- | --- | --- | --- |
| `200010` — Toronto Maple Leafs @ Edmonton Oilers | Committed root event row says OLBG `Game Totals` / `Over 6.50`. The live [OLBG event page](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/TOR_Maple_Leafs_@_EDM_Oilers/13?event_id=200010), read 22:26Z, separately exposes Money Line (including Edmonton) and Game Totals (Over 6.50). | Root pick is `EDM Oilers`, 1.41 (−244); the written selection says Edmonton to win. The live page renders `EDM Oilers · Game Totals · 1.41 (−244 US)`, which reads as a price for the total market. | The event page is the source for the market names/selections only; live market/tip information is time-sensitive. The committed capture and the live page are not asserted to be simultaneous. | [NHL official schedule](https://api-web.nhle.com/v1/schedule/2026-10-24) is cited by the card for the fixture/start. It does not substantiate an OLBG betting market or our originated price. |
| `3530` — St Finbarrs v Nemo Rangers | The live [OLBG event page](https://www.olbg.com/betting-tips/Gaelic_Football/All_Gaelic_Football/All_Events/St_Finbarrs_v_Nemo_Rangers/25?event_id=3530), read 22:27Z, shows `Nemo Rangers +1.50` as its most-popular tip and has a separate Handicap market. The committed root event row records the handicap selection. | Root pick is `St Finbarrs`, 1.62 (−161), with no handicap selection attached to that originated price. | The live page distinguishes the handicap selection from its separate FT Result market. This audit does not infer an originated handicap line. | [Cork GAA official fixture page](https://gaacork.ie/event/mccarthy-insurance-group-premier-senior-football-championship-final/) confirms the finalists, date, venue, and 4:00 pm local start; it does not substantiate the OLBG market or our price. |

## Verification and limitations

- The deployed page text, committed `data/events.json`, `scripts/pick_surface.py`, and both live OLBG event pages were compared. The two examples reproduce the ambiguity described above.
- Official league sources were included for the fixture context only. They are not bookmakers and cannot verify an OLBG market label or an originated price.
- OLBG market and tip-count content can change. The audit records only the page content actually returned in the stated retrieval window; it does not backfill later values into the committed capture.
- No injury, form, score, odds, or winner claim was newly introduced. No value was filled from inference.

## Requested handoff

`session-e304aa51` owns final integration and shared/generated dashboard outputs. Please add a non-blocking entry to the existing **Flagged for Review** register and clarify the card labels there (for example, distinguish `OLBG market` from the project's `our originated market`, or render both explicit market/selection pairs). Do not imply that the 1.41 or 1.62 price is for an OLBG handicap/total market. This audit session deliberately does not edit shared data or page builders while that integration scope is active.
