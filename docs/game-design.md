# Game design

## The journey

Six legs, each against the clock, on a road measured in segments of about a metre (`tools/levels.py`).

| Leg | From, to | Length | Time | Traffic style | View, then |
|---|---|---:|---:|---|---|
| 1 | Villa Comunale, Molo Beverello | 1,340 | 92 s | The jam | Lungomare, Porto |
| 2 | Ischia Alta, Ischia Porto | 1,060 | 114 s | Lanes | Ischia |
| 3 | Pozzuoli, Casoria | 1,080 | 90 s | Tamarri | Pozzuoli, Casoria |
| 4 | Casoria, Torregaveta | 1,010 | 86 s | Tamarri | Casoria, Torregaveta |
| 5 | Torregaveta, Mondragone | 1,420 | 116 s | Mozzarella truck | Torregaveta, Mondragone |
| 6 | Mondragone, Baia Domizia | 1,440 | 110 s | Everything | Mondragone, Baia Domizia |

Between them: the ferry to Ischia, the loading of the 24 melons, the ferry to Pozzuoli. From Pozzuoli the road goes inland
by the Tangenziale to Casoria, then back to the sea by the Asse Mediano, Licola and Cuma. At the end of the last
leg Patrizia waits by the road at Baia Domizia.

## The street, not a race track

The game keeps the behind-the-vehicle road of the arcade racers because it is the right way to show a load that
shifts in bends, and drops most of the rest. There are no rumble strips, no checkpoints, no finish banner and no
other racers. Each section of a leg (`tools/levels.py`) says:

- **its surface:** asphalt with dashed lines, *basoli* (the dark basalt setts of old Naples and Ischia, drawn with
  their joints), or worn asphalt with patches;
- **what stands at each side:** palms, pines, lamps, houses, beach umbrellas, a votive shrine, rubbish bins, washing
  hung across the lane on a line, or double-parked cars;
- **how many cars are double-parked.** A parked car sits in the lane with its hazards blinking. Traffic steers round
  it; the Ape stops dead against it and spills a melon, and the horn does not move it.

In town, zebra crossings come every 140 segments. A leg ends at the road sign of the town it reaches. The top of
the screen is a delivery docket on cream paper: time as minutes and seconds, melons on board, takings, and the
route with the Ape's position along it.

## The Ape

Top speed is 60 km/h. The two-stroke runs out of breath near the top. Steering works only when moving. The road's
bends push it outward, so it can't hold a hard bend flat out, however hard you steer.

## The melons

The load is what the game is about, and it can be counted on the back of the Ape.

- **Bends shift it.** Force is |curve| times speed. Above a threshold, a load meter fills without being displayed, except that the pile starts to wobble; when full, one melon leaves on the outside of the bend. Scraping a wall or leaving the road adds to it.
- **Hits shed it.** A pothole or car costs one melon, and the truck costs three.
- **Momentum carries it on.** The Ape loses speed and the melon doesn't, so the melon flies ahead, bounces and rolls.
- **You can get it back** by driving over it.
- **Everyone else wants it.** A passer-by runs out from the nearer side as soon as it lands, and any car that reaches it keeps it. Whatever is left behind the camera is gone. The horn makes thieves run off, and they may come back.

Nobody is ever run over: pedestrians jump clear.

## Stalls and foods

- **Stalls** are on one side of the road. To sell, pull over to that half and stop in the stall's bay, from 6 segments before it to 3 after. The mellonaro takes one melon about every quarter of a second (8 ticks), up to four, for 250 points each, and says thanks. Drive off early and you keep the rest; drive past without stopping and the stall is lost. There are five, so 20 of the 24 melons have a stall, and four are your margin. The docket says which side the next stall is on.
- **Foods** must be collected in order: mozzariella, provola, ricotta, caciotta, frittatina di maccheroni. Only the next one shows on the road, and it reappears at the next place on the list if missed. There are 13 such places for 5 foods.
- **At Baia Domizia** whatever is left is sold on the beach for 200 points each. All five foods fed to Patrizia is worth 5,000, and decides which ending you see.

## How it ends

- **Time runs out:** on the first two legs, *hai perso il traghetto*. Afterwards, *tempo scaduto*.
- **No melons, none on the road, none ever delivered:** *nemmeno un mellone*. An Ape that has delivered but is empty still drives on to the beach.

## Tuning choices

The first version ended the game whenever the load reached zero. That punished good deliveries, since delivering
all you have empties the Ape, and it sank 60% of the autoplayer runs that reached the last leg. The rule above replaced it.
See [balance.md](balance.md).

In 1.0 a stall took its four melons as the Ape drove past on the right half, at any speed: a checkpoint by
another name. Stopping makes a delivery a decision, costs time the limits now allow for, and gives the street
its rhythm of driving and pulling over.
