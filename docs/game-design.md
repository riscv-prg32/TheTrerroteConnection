# Game design

## The journey

Five legs, each against the clock, on a road measured in segments of about a metre (`tools/levels.py`).

| Leg | From, to | Length | Time | Traffic style | View, then |
|---|---|---:|---:|---|---|
| 1 | Villa Comunale, Molo Beverello | 1,340 | 90 s | The jam | Lungomare, Porto |
| 2 | Ischia Alta, Ischia Porto | 1,060 | 112 s | Lanes | Ischia |
| 3 | Pozzuoli, Torregaveta | 1,280 | 96 s | Tamarri | Pozzuoli, Torregaveta |
| 4 | Torregaveta, Mondragone | 1,420 | 105 s | Mozzarella truck | Torregaveta, Mondragone |
| 5 | Mondragone, Baia Domizia | 1,440 | 100 s | Everything | Mondragone, Baia Domizia |

Between them: the ferry to Ischia, the loading of the 24 melons, the ferry to Pozzuoli.

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

- **Stalls** are on one side of the road, and you must be on that half as you pass. Each takes four melons, for 250 points each. There are five, so 20 of the 24 melons have a stall, and four are your margin.
- **Foods** must be collected in order: mozzariella, provola, ricotta, caciotta, frittatina di maccheroni. Only the next one shows on the road, and it reappears at the next place on the list if missed. There are 13 such places for 5 foods.
- **At Baia Domizia** whatever is left is sold on the beach for 200 points each. All five foods fed to Patrizia is worth 5,000, and decides which ending you see.

## How it ends

- **Time runs out:** on the first two legs, *hai perso il traghetto*. Afterwards, *tempo scaduto*.
- **No melons, none on the road, none ever delivered:** *nemmeno un mellone*. An Ape that has delivered but is empty still drives on to the beach.

## Tuning choices

The first version ended the game whenever the load reached zero. That punished good deliveries, since delivering
all you have empties the Ape, and it sank 60% of the autoplayer runs that reached leg 5. The rule above replaced it.
See [balance.md](balance.md).
