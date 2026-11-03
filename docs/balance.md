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
| Time limits raised by 2 to 11 s | Stalls now need a stop, and double-parked cars block lanes |
| Autoplayer pulls over for stalls, ignores parked cars it is passing | It ran past stalls, and braked behind cars it could overtake |

## Result

The autoplayer now finishes 94% of journeys over the six legs (940 of 1,000), with all five foods, delivering 16.3
melons on average (measured; see the CSV for current numbers). All the failures are time running out, on the last two
legs: 46 on leg 5, 14 on leg 6. Time limits leave it 13 to 23 seconds' margin per leg on average, by intent: tight for a machine, and probably
tighter than that for a person. If play-testers run out of time, widen
`time` in `tools/levels.py` first.
