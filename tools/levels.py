#!/usr/bin/env python3
"""The five legs of the journey, as sections of road.

A section is (length in segments, curve, road width, left ground, right ground,
left decoration, right decoration, decoration period, traffic, potholes). A
segment is about a metre: at the Ape's 60 km/h the road passes at 0.59 segments
per 33 ms tick. `curve` runs from -8 (hard left) to +8; `width` is in sixteenths
of a normal two-lane road. Traffic and potholes are densities from 0 to 15.
`anchors` are (kind, segment, side or lateral position): delivery stalls and
places where the next food can lie. Run this file to check the tables.
"""
from __future__ import annotations

# Ground codes: the colour pairs in the cartridge's ground_a/ground_b tables.
PAVE, SEA, SAND, GRASS, TUFF = 0, 1, 2, 3, 4
WALL = TUFF   # the foot of a wall of houses
# Decoration codes: 0 is none; the others are DECO_* in src/tr_core.h.
NONE, PALM, PINE, LAMP, HOUSE, UMB = 0, 1, 2, 3, 4, 5
FULL, NARROW, ALLEY = 16, 11, 9
STALL, FOOD = 0, 1
LEFT, RIGHT = -1, 1

LEVELS = [
    {   # Naples: Villa Comunale along via Caracciolo and via Partenope to Molo Beverello.
        "name": "VILLA COMUNALE", "dest": "MOLO BEVERELLO", "time": 90, "views": (0, 1), "swap": 760, "song": "LUNGOMARE",
        "style": "jam", "melons": 0,
        "sections": [
            (120, 0, FULL, PAVE, SEA, PALM, NONE, 18, 2, 0),
            (140, 1, FULL, PAVE, SEA, PALM, NONE, 18, 6, 1),
            (160, -2, FULL, PAVE, SEA, PALM, LAMP, 16, 11, 1),
            (120, 0, FULL, PAVE, SEA, LAMP, LAMP, 16, 14, 2),
            (120, 3, FULL, PAVE, SEA, PALM, LAMP, 16, 10, 2),
            (100, -1, FULL, WALL, PAVE, HOUSE, LAMP, 12, 8, 2),
            (160, -3, FULL, WALL, PAVE, HOUSE, LAMP, 12, 13, 3),
            (140, 2, FULL, WALL, PAVE, HOUSE, LAMP, 12, 15, 3),
            (120, 0, FULL, PAVE, SEA, LAMP, NONE, 16, 12, 2),
            (160, 1, FULL, PAVE, SEA, LAMP, NONE, 16, 6, 1),
        ],
        "anchors": [],
    },
    {   # Ischia: down from the hills through the lanes to the port, every turn a tilt.
        "name": "ISCHIA ALTA", "dest": "ISCHIA PORTO", "time": 112, "views": (2, 2), "swap": 0, "song": "ISCHIA",
        "style": "lanes", "melons": 24,
        "sections": [
            (90, 0, NARROW, WALL, WALL, HOUSE, HOUSE, 7, 0, 0),
            (70, 5, NARROW, WALL, WALL, HOUSE, HOUSE, 7, 1, 1),
            (60, -6, ALLEY, WALL, WALL, HOUSE, HOUSE, 6, 0, 1),
            (70, 7, ALLEY, WALL, WALL, HOUSE, HOUSE, 6, 1, 2),
            (50, 0, NARROW, GRASS, WALL, NONE, HOUSE, 7, 1, 1),
            (70, -7, ALLEY, GRASS, WALL, PINE, HOUSE, 7, 2, 2),
            (60, 6, ALLEY, WALL, WALL, HOUSE, HOUSE, 6, 1, 1),
            (60, -5, NARROW, WALL, GRASS, HOUSE, PINE, 7, 2, 2),
            (70, 7, ALLEY, WALL, WALL, HOUSE, HOUSE, 6, 1, 2),
            (60, -7, ALLEY, WALL, WALL, HOUSE, HOUSE, 6, 1, 2),
            (80, 4, NARROW, WALL, SEA, HOUSE, NONE, 7, 3, 1),
            (70, -6, NARROW, WALL, SEA, HOUSE, LAMP, 7, 2, 2),
            (70, 5, NARROW, WALL, WALL, HOUSE, HOUSE, 7, 3, 1),
            (70, -4, FULL, PAVE, SEA, LAMP, LAMP, 12, 4, 1),
            (110, 0, FULL, PAVE, SEA, PALM, LAMP, 14, 3, 0),
        ],
        "anchors": [(FOOD, 300, -96), (FOOD, 620, 96), (FOOD, 900, 0)],
    },
    {   # Pozzuoli along via Napoli and the Lucrino shore to Torregaveta.
        "name": "POZZUOLI", "dest": "TORREGAVETA", "time": 96, "views": (3, 4), "swap": 800, "song": "STRADA",
        "style": "tamarri", "melons": -1,
        "sections": [
            (120, 0, FULL, PAVE, SEA, LAMP, NONE, 14, 4, 2),
            (130, 2, FULL, TUFF, SEA, NONE, LAMP, 14, 6, 3),
            (110, -3, FULL, PAVE, SEA, HOUSE, LAMP, 12, 6, 4),
            (130, 4, FULL, PAVE, SAND, PALM, UMB, 12, 7, 4),
            (120, 0, FULL, GRASS, SAND, PINE, UMB, 14, 8, 5),
            (140, -3, FULL, GRASS, SEA, PINE, NONE, 16, 6, 6),
            (150, 3, NARROW, TUFF, SEA, NONE, NONE, 16, 5, 6),
            (130, -4, NARROW, TUFF, SAND, NONE, UMB, 14, 5, 5),
            (120, 1, FULL, PAVE, SAND, HOUSE, UMB, 12, 7, 4),
            (130, 0, FULL, PAVE, SAND, LAMP, UMB, 12, 5, 2),
        ],
        "anchors": [(STALL, 340, RIGHT), (FOOD, 480, -80), (FOOD, 700, 80), (STALL, 880, LEFT), (FOOD, 1050, 0)],
    },
    {   # The Domitiana north: Licola, Castel Volturno, Mondragone. Long and full of holes.
        "name": "TORREGAVETA", "dest": "MONDRAGONE", "time": 105, "views": (4, 5), "swap": 900, "song": "STRADA",
        "style": "truck", "melons": -1,
        "sections": [
            (120, 1, FULL, TUFF, SAND, NONE, UMB, 14, 4, 3),
            (160, -2, FULL, GRASS, SAND, PINE, UMB, 14, 6, 6),
            (180, 0, FULL, GRASS, GRASS, PINE, PINE, 16, 7, 8),
            (160, 3, FULL, GRASS, GRASS, PINE, LAMP, 16, 8, 8),
            (160, -2, FULL, PAVE, GRASS, HOUSE, PINE, 14, 9, 9),
            (160, 0, FULL, GRASS, GRASS, PINE, PINE, 14, 8, 10),
            (160, 4, FULL, GRASS, SAND, PINE, UMB, 14, 7, 9),
            (160, -3, FULL, PAVE, SAND, LAMP, UMB, 14, 7, 7),
            (160, 0, FULL, PAVE, SAND, HOUSE, UMB, 12, 6, 4),
        ],
        "anchors": [(STALL, 420, LEFT), (FOOD, 560, 90), (FOOD, 820, -90), (STALL, 1060, RIGHT), (FOOD, 1240, 0)],
    },
    {   # Mondragone to Baia Domizia: the last stretch among the pines, the sun going down.
        "name": "MONDRAGONE", "dest": "BAIA DOMIZIA", "time": 100, "views": (5, 6), "swap": 900, "song": "TRAMONTO",
        "style": "everything", "melons": -1,
        "sections": [
            (140, 0, FULL, PAVE, SAND, HOUSE, UMB, 12, 7, 4),
            (160, 3, FULL, GRASS, SAND, PINE, UMB, 14, 9, 7),
            (160, -4, FULL, GRASS, GRASS, PINE, PINE, 12, 10, 9),
            (160, 2, FULL, GRASS, GRASS, PINE, PINE, 12, 11, 10),
            (160, 0, NARROW, GRASS, GRASS, PINE, PINE, 12, 8, 10),
            (160, -3, FULL, GRASS, SAND, PINE, UMB, 12, 10, 8),
            (160, 4, FULL, GRASS, SAND, PINE, UMB, 10, 9, 7),
            (160, -2, FULL, PAVE, SAND, PALM, UMB, 10, 7, 4),
            (180, 0, FULL, PAVE, SAND, PALM, UMB, 10, 4, 1),
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
            if not (-8 <= s[1] <= 8 and s[2] in (FULL, NARROW, ALLEY) and 0 <= s[8] <= 15 and 0 <= s[9] <= 15 and s[7] > 0):
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
