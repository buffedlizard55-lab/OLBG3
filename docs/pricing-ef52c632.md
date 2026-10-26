# October 26 NHL pricing and fact receipts

Sources fetched by [runner 40394727276](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40394727276):
- [NHL schedule](https://api-web.nhle.com/v1/schedule/2026-10-26), `data/raw/official-20261026T2021Z/json/nhl_schedule.json`.
- [NHL standings](https://api-web.nhle.com/v1/standings/2026-10-26), `data/raw/official-20261026T2021Z/json/nhl_standings.json`.

The JSON receipt `data/pricing-ef52c632.json` records all inputs and arithmetic. For each team,
`q=(wins+1)/(gamesPlayed+2)`. Compute `L=qH*(1-qA)/(qH*(1-qA)+qA*(1-qH))`, then
`pH=.5+.5*(L-.5)+.03`. Select the larger side, round its probability to four places and
quote `round(.95/p,2)`. Smoothing, shrinkage and home adjustment are uncalibrated assumptions,
not sporting facts. Official data do not verify a betting probability. This is independent of
OLBG's printed odds; no value edge against a bookmaker is claimed.

| Official field / claim | Where checked |
| --- | --- |
| Both participants and UTC start | `gameWeek[].games[]`, awayTeam/homeTeam identifiers and startTimeUTC in NHL schedule |
| Overall record | `standings[]`: wins, losses, otLosses, gamesPlayed |
| Goals scored / allowed | goalFor, goalAgainst |
| Venue records | homeWins/homeLosses/homeOtLosses and roadWins/roadLosses/roadOtLosses |
| Last ten and streak | l10Wins/l10Losses/l10OtLosses, streakCode/streakCount |
| Injuries, lineup, starting goalie | Not established; no player absence/availability claim published |

Seven independently written pieces cover Rangers–Kings, Oilers–Red Wings, Flames–Maple Leafs,
Hurricanes–Bruins, Jets–Panthers, Stars–Devils and Predators–Islanders. Each cites both official
endpoints. Rangers and Oilers pass the existing HIGH research-grade threshold; the other five
are analysis rather than padding the quota. HIGH is neither a calibrated win rate nor a guarantee.

The original bodies and sources are durable in `data/patches/picks-ef52c632.json`. Patches do not
renew their own clocks: the shared gate expires the official observation after 24 hours or at
scheduled start. All seven OLBG clocks differ by seven minutes; the official clock governs release.
