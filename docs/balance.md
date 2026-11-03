# Balance

`tests/balance.c` runs the autoplayer over 1,000 whole journeys. Results are in `docs/data/balance.csv` and
`docs/data/journey.txt`.

The autoplayer sees everything and reacts within a tick, but plans only a few metres ahead. These figures are useful to
compare legs and tuning choices. **They don't say how hard the game feels to a person**, and no person has played it.
Expect humans to do worse in traffic and better at planned recovery of melons.

## What the study changed

The first tuning, on the five-leg journey of 1.0, could not be finished at all: 0 of 300 journeys, with 11 to 14 hits a leg. Successive changes:

| Change | Why |
|---|---|
| Fewer spawned cars outside the jam | Traffic filled all eight slots on legs 3 to 5 |
| Tamarri re-aim every 4 s, only when well ahead | They were unavoidable |
| One melon per hit (truck: three) | Two a hit emptied the Ape by leg 4 |
| Empty after delivering no longer ends the game | It punished good deliveries, ending 60% of runs reaching leg 5 |

## Result

The autoplayer now finishes about 95% of journeys over the six legs, with all five foods, delivering about 16 melons
(measured over 1,000 journeys; see the CSV for current numbers). Almost all the failures are time running out on the
last leg. Time limits leave it 10 to 18 seconds' margin per leg, by intent: tight for a machine, and probably
tighter than that for a person. If play-testers run out of time, widen
`time` in `tools/levels.py` first.
