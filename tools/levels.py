#!/usr/bin/env python3
"""The six legs of the journey, as sections of road.

A section is (length in segments, curve, road width, left ground, right ground,
left decoration, right decoration, decoration period, traffic, potholes,
surface, double parking). A segment is about a metre: at the Ape's 60 km/h the
road passes at 0.59 segments per 33 ms tick. `curve` runs from -8 (hard left)
to +8; `width` is in sixteenths of a normal two-lane road. Traffic, potholes
and double parking are densities from 0 to 15. The surface is asphalt, the
basalt basoli of the old streets, or asphalt worn to patches.
`anchors` are (kind, segment, side or lateral position): delivery stalls, where
the Ape has to stop, and places where the next food can lie. Run this file to
check the tables.
"""
from __future__ import annotations

# Ground codes: the colour pairs in the cartridge's ground table.
PAVE, SEA, SAND, GRASS, TUFF = 0, 1, 2, 3, 4
WALL = TUFF   # the foot of a wall of houses
# Decoration codes: 0 is none; the others are DECO_* in src/tr_core.h.
NONE, PALM, PINE, LAMP, HOUSE, UMB, SHRINE, BINS, WASH, PARKED = range(10)
# Surfaces: SURFACE_* in src/tr_core.h.
ASPH, BASOLI, WORN = 0, 1, 2
FULL, NARROW, ALLEY = 16, 11, 9
STALL, FOOD = 0, 1
LEFT, RIGHT = -1, 1

LEVELS = [
    {   # Naples: Villa Comunale along via Caracciolo and via Partenope to Molo Beverello.
        "name": "VILLA COMUNALE", "dest": "MOLO BEVERELLO", "time": 92, "views": (0, 1), "swap": 760, "song": "LUNGOMARE",
        "style": "jam", "melons": 0,
        "sections": [
            (120, 0, FULL, PAVE, SEA, PALM, NONE, 18, 2, 0, ASPH, 0),
            (140, 1, FULL, PAVE, SEA, PALM, NONE, 18, 6, 1, ASPH, 2),
            (160, -2, FULL, PAVE, SEA, PALM, LAMP, 16, 11, 1, BASOLI, 3),
            (120, 0, FULL, PAVE, SEA, LAMP, LAMP, 16, 14, 2, BASOLI, 4),
            (120, 3, FULL, PAVE, SEA, PARKED, LAMP, 14, 10, 2, BASOLI, 4),
            (100, -1, FULL, WALL, PAVE, HOUSE, BINS, 12, 8, 2, BASOLI, 6),
            (160, -3, FULL, WALL, PAVE, SHRINE, PARKED, 12, 13, 3, BASOLI, 6),
            (140, 2, FULL, WALL, PAVE, HOUSE, LAMP, 12, 15, 3, WORN, 5),
            (120, 0, FULL, PAVE, SEA, LAMP, NONE, 16, 12, 2, ASPH, 3),
            (160, 1, FULL, PAVE, SEA, LAMP, NONE, 16, 6, 1, ASPH, 1),
        ],
        "anchors": [],
    },
    {   # Ischia: down from the hills through the lanes to the port, every turn a tilt.
        "name": "ISCHIA ALTA", "dest": "ISCHIA PORTO", "time": 114, "views": (2, 2), "swap": 0, "song": "ISCHIA",
        "style": "lanes", "melons": 24,
        "sections": [
            (90, 0, NARROW, WALL, WALL, HOUSE, HOUSE, 7, 0, 0, BASOLI, 0),
            (70, 5, NARROW, WALL, WALL, WASH, HOUSE, 7, 1, 1, BASOLI, 0),
            (60, -6, ALLEY, WALL, WALL, HOUSE, SHRINE, 6, 0, 1, BASOLI, 0),
            (70, 7, ALLEY, WALL, WALL, WASH, HOUSE, 6, 1, 2, BASOLI, 0),
            (50, 0, NARROW, GRASS, WALL, NONE, HOUSE, 7, 1, 1, WORN, 0),
            (70, -7, ALLEY, GRASS, WALL, PINE, HOUSE, 7, 2, 2, WORN, 0),
            (60, 6, ALLEY, WALL, WALL, HOUSE, WASH, 6, 1, 1, BASOLI, 0),
            (60, -5, NARROW, WALL, GRASS, SHRINE, PINE, 7, 2, 2, BASOLI, 0),
            (70, 7, ALLEY, WALL, WALL, WASH, HOUSE, 6, 1, 2, BASOLI, 0),
            (60, -7, ALLEY, WALL, WALL, HOUSE, HOUSE, 6, 1, 2, BASOLI, 0),
            (80, 4, NARROW, WALL, SEA, HOUSE, NONE, 7, 3, 1, WORN, 0),
            (70, -6, NARROW, WALL, SEA, BINS, LAMP, 7, 2, 2, WORN, 2),
            (70, 5, NARROW, WALL, WALL, HOUSE, PARKED, 7, 3, 1, BASOLI, 3),
            (70, -4, FULL, PAVE, SEA, LAMP, LAMP, 12, 4, 1, ASPH, 2),
            (110, 0, FULL, PAVE, SEA, PALM, LAMP, 14, 3, 0, ASPH, 1),
        ],
        "anchors": [(FOOD, 300, -96), (FOOD, 620, 96), (FOOD, 900, 0)],
    },
    {   # Pozzuoli by via Napoli and Bagnoli, up the Tangenziale past Capodichino to Casoria.
        "name": "POZZUOLI", "dest": "CASORIA", "time": 90, "views": (3, 4), "swap": 620, "song": "STRADA",
        "style": "tamarri", "melons": -1,
        "sections": [
            (110, 0, FULL, PAVE, SEA, LAMP, NONE, 14, 4, 2, BASOLI, 3),
            (120, 2, FULL, TUFF, SEA, NONE, LAMP, 14, 6, 3, WORN, 1),
            (120, -2, FULL, WALL, PAVE, HOUSE, BINS, 12, 8, 3, WORN, 5),
            (130, 3, FULL, PAVE, PAVE, LAMP, LAMP, 14, 10, 4, ASPH, 0),
            (120, -1, FULL, WALL, WALL, HOUSE, PARKED, 12, 9, 4, WORN, 6),
            (130, 0, FULL, PAVE, GRASS, BINS, NONE, 14, 8, 5, WORN, 3),
            (120, 2, NARROW, WALL, WALL, SHRINE, HOUSE, 10, 6, 6, BASOLI, 5),
            (120, -3, NARROW, WALL, PAVE, WASH, PARKED, 10, 7, 5, BASOLI, 6),
            (110, 0, FULL, PAVE, PAVE, HOUSE, LAMP, 12, 6, 3, WORN, 4),
        ],
        "anchors": [(STALL, 380, RIGHT), (FOOD, 540, -80), (FOOD, 820, 80)],
    },
    {   # Casoria down the Asse Mediano, past Giugliano and Licola, by Cuma to Torregaveta.
        "name": "CASORIA", "dest": "TORREGAVETA", "time": 86, "views": (4, 5), "swap": 640, "song": "STRADA",
        "style": "tamarri", "melons": -1,
        "sections": [
            (120, 0, FULL, WALL, PAVE, HOUSE, PARKED, 12, 7, 4, WORN, 6),
            (140, -2, FULL, PAVE, GRASS, LAMP, NONE, 16, 9, 5, ASPH, 0),
            (140, 1, FULL, GRASS, GRASS, LAMP, LAMP, 16, 10, 5, ASPH, 0),
            (120, 3, FULL, PAVE, GRASS, BINS, PINE, 12, 8, 6, WORN, 3),
            (130, -3, FULL, GRASS, GRASS, PINE, PINE, 14, 6, 6, WORN, 1),
            (130, 2, NARROW, GRASS, SAND, PINE, UMB, 14, 5, 5, WORN, 1),
            (120, -4, NARROW, TUFF, SAND, NONE, UMB, 14, 5, 4, ASPH, 0),
            (110, 0, FULL, PAVE, SAND, SHRINE, UMB, 12, 5, 2, ASPH, 2),
        ],
        "anchors": [(FOOD, 300, 0), (STALL, 520, LEFT), (FOOD, 800, -80)],
    },
    {   # The Domitiana north: Licola, Castel Volturno, Mondragone. Long and full of holes.
        "name": "TORREGAVETA", "dest": "MONDRAGONE", "time": 116, "views": (5, 6), "swap": 900, "song": "STRADA",
        "style": "truck", "melons": -1,
        "sections": [
            (120, 1, FULL, TUFF, SAND, NONE, UMB, 14, 4, 3, ASPH, 0),
            (160, -2, FULL, GRASS, SAND, PINE, UMB, 14, 6, 6, WORN, 1),
            (180, 0, FULL, GRASS, GRASS, PINE, BINS, 16, 7, 8, WORN, 0),
            (160, 3, FULL, GRASS, GRASS, PINE, LAMP, 16, 8, 8, WORN, 0),
            (160, -2, FULL, PAVE, GRASS, HOUSE, PINE, 14, 9, 9, WORN, 4),
            (160, 0, FULL, GRASS, GRASS, PINE, PINE, 14, 8, 10, WORN, 0),
            (160, 4, FULL, GRASS, SAND, PINE, UMB, 14, 7, 9, WORN, 1),
            (160, -3, FULL, PAVE, SAND, SHRINE, UMB, 14, 7, 7, ASPH, 2),
            (160, 0, FULL, PAVE, SAND, PARKED, UMB, 12, 6, 4, ASPH, 4),
        ],
        "anchors": [(STALL, 420, LEFT), (FOOD, 560, 90), (FOOD, 820, -90), (STALL, 1060, RIGHT), (FOOD, 1240, 0)],
    },
    {   # Mondragone to Baia Domizia: the last stretch among the pines, the sun going down.
        "name": "MONDRAGONE", "dest": "BAIA DOMIZIA", "time": 110, "views": (6, 7), "swap": 900, "song": "TRAMONTO",
        "style": "everything", "melons": -1,
        "sections": [
            (140, 0, FULL, PAVE, SAND, PARKED, UMB, 12, 7, 4, BASOLI, 5),
            (160, 3, FULL, GRASS, SAND, PINE, UMB, 14, 9, 7, WORN, 1),
            (160, -4, FULL, GRASS, GRASS, PINE, PINE, 12, 10, 9, WORN, 0),
            (160, 2, FULL, GRASS, GRASS, PINE, BINS, 12, 11, 10, WORN, 0),
            (160, 0, NARROW, GRASS, GRASS, PINE, PINE, 12, 8, 10, WORN, 0),
            (160, -3, FULL, GRASS, SAND, PINE, UMB, 12, 10, 8, ASPH, 1),
            (160, 4, FULL, GRASS, SAND, SHRINE, UMB, 10, 9, 7, ASPH, 1),
            (160, -2, FULL, PAVE, SAND, PALM, UMB, 10, 7, 4, ASPH, 3),
            (180, 0, FULL, PAVE, SAND, PALM, UMB, 10, 4, 1, ASPH, 2),
        ],
        "anchors": [(FOOD, 300, 0), (STALL, 500, RIGHT), (FOOD, 740, -90), (FOOD, 1040, 90), (FOOD, 1240, 0)],
    },
]

SONGS = ["LUNGOMARE", "ISCHIA", "STRADA", "TRAMONTO"]
STYLES = ["jam", "lanes", "tamarri", "truck", "everything"]


def length(level: dict) -> int:
    return sum(s[0] for s in level["sections"])


def check() -> int:
    errors = 0
    for n, level in enumerate(LEVELS):
        total = length(level)
        for s in level["sections"]:
            if not (-8 <= s[1] <= 8 and s[2] in (FULL, NARROW, ALLEY) and 0 <= s[8] <= 15 and 0 <= s[9] <= 15 and s[7] > 0
                    and len(s) == 12 and s[10] in (ASPH, BASOLI, WORN) and 0 <= s[11] <= 15 and 0 <= s[5] <= PARKED and 0 <= s[6] <= PARKED):
                print(f"level {n}: bad section {s}")
                errors += 1
        for kind, seg, _ in level["anchors"]:
            if not 60 <= seg < total - 60:
                print(f"level {n}: anchor at {seg} is outside the road ({total})")
                errors += 1
        if level["swap"] >= total or len(level["name"]) > 15 or len(level["dest"]) > 15:
            print(f"level {n}: bad swap or name")
            errors += 1
    return errors


if __name__ == "__main__":
    n = check()
    print(f"levels: {len(LEVELS)} legs, {sum(length(l) for l in LEVELS)} segments, {n} errors")
    raise SystemExit(1 if n else 0)
