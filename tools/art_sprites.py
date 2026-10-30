#!/usr/bin/env python3
"""All the sprites, drawn with small primitives on a grid of fixed-colour names.

The Ape, the traffic, the street life and the five foods. Sizes are source
pixels; the cartridge scales everything at run time on the road. `.` (None) is
transparent. Slots that the cartridge recolours at run time are drawn in "blue"
and "blued" (see tint_* in src/trerrote.c), the economy of indexed hardware.
"""
from __future__ import annotations

import math

MINI = {  # 3 x 5 capitals for lettering painted on vehicles and signs
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
    "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "L": "100100100100111", "M": "101111111101101", "N": "110101101101101",
    "O": "010101101101010", "P": "110101110100100", "R": "110101110101101", "S": "011100010001110",
    "T": "111010010010010", "U": "101101101101111", "V": "101101101101010", "Z": "111001010100111",
    " ": "000000000000000",
}


class G:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.p: list[list[str | None]] = [[None] * w for _ in range(h)]

    def put(self, x: int, y: int, c: str | None) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x: int, y: int, w: int, h: int, c: str | None) -> "G":
        for py in range(y, y + h):
            for px in range(x, x + w):
                self.put(px, py, c)
        return self

    def disc(self, cx: float, cy: float, rx: float, ry: float, c: str | None) -> "G":
        for y in range(self.h):
            for x in range(self.w):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, c)
        return self

    def line(self, x0: float, y0: float, x1: float, y1: float, c: str | None) -> "G":
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            self.put(round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), c)
        return self

    def poly(self, pts: list[tuple[float, float]], c: str | None) -> "G":
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 <= y + 0.5 < y1) or (y1 <= y + 0.5 < y0):
                    xs.append(x0 + (y + 0.5 - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                for x in range(round(a), round(b)):
                    self.put(x, y, c)
        return self

    def text(self, x: int, y: int, s: str, c: str) -> "G":
        for ch in s:
            bits = MINI[ch]
            for k, b in enumerate(bits):
                if b == "1":
                    self.put(x + k % 3, y + k // 3, c)
            x += 4
        return self

    def mirror(self) -> "G":
        """Copy the left half onto the right: vehicles from behind are symmetric."""
        for row in self.p:
            for x in range(self.w // 2):
                row[self.w - 1 - x] = row[x]
        return self


def melon() -> G:
    g = G(12, 11)
    g.disc(6, 5.5, 6, 5.5, "melon")
    for x, w in ((2, 1), (5, 2), (9, 1)):
        g.line(x + 0.5, 1, x + 0.5, 10, "melond")
        if w == 2:
            g.line(x + 1.5, 1, x + 1.5, 10, "melond")
    for y in range(11):
        for x in range(12):
            if g.p[y][x] and ((x + 0.5 - 6) / 6) ** 2 + ((y + 0.5 - 5.5) / 5.5) ** 2 > 0.86:
                g.p[y][x] = "melond"
    g.put(3, 2, "cream")
    g.put(4, 2, "grass")
    g.put(3, 3, "grass")
    return g


def ape() -> G:
    """The Trerrote from behind: cab, empty bed, tailgate, two rear wheels."""
    g = G(60, 48)
    # Cab: a rounded roof and rear window, seen over the bed.
    g.poly([(14, 8), (18, 1), (42, 1), (46, 8), (46, 24), (14, 24)], "blue")
    g.rect(19, 0, 22, 1, "blued")
    g.rect(14, 8, 2, 16, "blued")
    g.rect(44, 8, 2, 16, "blued")
    g.poly([(18, 8), (21, 4), (39, 4), (42, 8), (42, 18), (18, 18)], "navy")
    g.disc(30, 12, 5, 5, "ink")       # the driver's head
    g.rect(25, 15, 10, 3, "red")      # the driver's shirt
    # Mirrors.
    g.rect(7, 8, 5, 3, "ink").rect(12, 9, 3, 1, "greyd")
    g.rect(48, 8, 5, 3, "ink").rect(45, 9, 3, 1, "greyd")
    # The bed: sides and the shadow the load sits in.
    g.rect(3, 21, 54, 13, "brown")
    g.rect(3, 21, 2, 13, "blue")
    g.rect(55, 21, 2, 13, "blue")
    # The tailgate.
    g.rect(2, 30, 56, 11, "blue")
    g.rect(2, 30, 56, 1, "cream")
    g.rect(2, 39, 56, 2, "blued")
    g.rect(4, 32, 6, 4, "red").rect(5, 33, 2, 1, "orange")
    g.rect(50, 32, 6, 4, "red").rect(53, 33, 2, 1, "orange")
    g.rect(21, 33, 18, 5, "cream")
    g.text(22, 33, "NA", "ink")
    g.rect(31, 33, 7, 5, "cream")
    g.text(31, 33, "TR", "ink")
    # Chassis, wheels, the little exhaust.
    g.rect(8, 41, 44, 3, "ink")
    g.rect(4, 38, 10, 10, "ink").rect(6, 40, 6, 6, "greyd").rect(8, 42, 2, 2, "grey")
    g.rect(46, 38, 10, 10, "ink").rect(48, 40, 6, 6, "greyd").rect(50, 42, 2, 2, "grey")
    g.rect(38, 42, 4, 2, "grey")
    return g


def car() -> G:
    g = G(40, 28)
    g.poly([(6, 12), (10, 2), (20, 2), (20, 14), (6, 14)], "blue")
    g.poly([(9, 12), (12, 4), (20, 4), (20, 12)], "navy")
    g.rect(1, 12, 19, 11, "blue")
    g.rect(1, 12, 19, 1, "cream")
    g.rect(1, 20, 19, 3, "blued")
    g.rect(2, 15, 6, 3, "red")
    g.rect(2, 15, 2, 1, "orange")
    g.rect(0, 23, 20, 2, "ink")
    g.rect(2, 22, 7, 6, "ink")
    g.mirror()
    g.rect(15, 16, 10, 3, "cream")
    return g


def tamarro_car() -> G:
    """Same car with everything added that nobody asked for."""
    g = G(40, 28)
    g.poly([(7, 13), (10, 5), (20, 5), (20, 15), (7, 15)], "blue")
    g.poly([(9, 13), (12, 7), (20, 7), (20, 13)], "ink")
    g.rect(0, 13, 20, 9, "blue")
    g.rect(0, 13, 20, 1, "lemon")
    g.rect(3, 16, 5, 3, "red")
    g.rect(0, 20, 20, 2, "blued")
    g.rect(0, 22, 20, 2, "ink")
    g.rect(1, 21, 7, 7, "ink")
    g.rect(2, 23, 5, 3, "grey")
    g.rect(0, 26, 20, 1, "purple")      # the underglow
    g.rect(2, 9, 2, 5, "ink")            # the spoiler
    g.rect(0, 7, 20, 2, "lemon")
    g.mirror()
    g.rect(13, 19, 14, 3, "ink")         # the subwoofer grille
    g.rect(14, 20, 2, 1, "grey").rect(19, 20, 2, 1, "grey").rect(24, 20, 2, 1, "grey")
    g.rect(29, 22, 3, 2, "grey").rect(33, 22, 3, 2, "grey")   # four exhausts
    g.rect(8, 22, 3, 2, "grey").rect(4, 22, 3, 2, "grey")
    return g


def truck() -> G:
    g = G(56, 60)
    g.rect(0, 0, 56, 46, "white")
    g.rect(0, 0, 56, 2, "cream")
    g.rect(52, 0, 4, 46, "grey")
    g.rect(0, 42, 56, 4, "grey")
    g.rect(27, 2, 1, 40, "grey")
    g.text(5, 6, "MOZZARELLA", "navy")
    g.text(13, 13, "DI BUFALA", "navy")
    # A buffalo's face on the doors.
    g.disc(28, 28, 7, 7, "ink").disc(28, 31, 4, 3, "greyd")
    g.rect(24, 28, 2, 2, "cream").rect(30, 28, 2, 2, "cream")
    g.line(21, 23, 15, 19, "ink").line(15, 19, 13, 23, "ink")
    g.line(35, 23, 41, 19, "ink").line(41, 19, 43, 23, "ink")
    g.rect(0, 46, 56, 4, "ink")
    g.rect(3, 47, 6, 3, "red").rect(47, 47, 6, 3, "red")
    g.rect(21, 47, 14, 3, "cream")
    g.rect(2, 50, 14, 10, "ink").rect(5, 52, 8, 6, "greyd")
    g.rect(40, 50, 14, 10, "ink").rect(43, 52, 8, 6, "greyd")
    g.rect(16, 50, 24, 3, "greyd")
    return g


def scooter() -> G:
    """Two tamarri without a helmet between them, seen from behind."""
    g = G(24, 36)
    g.disc(12, 4, 4, 4, "brown")          # driver's hair
    g.rect(9, 7, 6, 2, "skin")
    g.rect(6, 9, 12, 8, "blue")           # his vest
    g.rect(4, 10, 2, 6, "skin").rect(18, 10, 2, 6, "skin")
    g.rect(2, 9, 3, 1, "grey").rect(19, 9, 3, 1, "grey")
    g.disc(12, 12, 3.5, 3.5, "ink")       # the passenger's head
    g.rect(8, 15, 8, 8, "blued")
    g.rect(10, 15, 4, 1, "lemon")         # gold chain, always
    g.rect(7, 22, 10, 6, "ink")           # seat and tail
    g.rect(9, 23, 6, 2, "red")
    g.rect(5, 23, 3, 6, "greyd").rect(16, 23, 3, 6, "greyd")
    g.rect(10, 28, 4, 8, "ink").rect(11, 30, 2, 4, "greyd")
    return g


def person(step: int) -> G:
    g = G(16, 30)
    g.disc(8, 4, 3.5, 4, "skin")
    g.disc(8, 2.5, 4, 2.5, "brown")
    g.rect(4, 8, 8, 11, "blue")
    g.rect(4, 8, 8, 1, "blued")
    g.rect(2, 9, 2, 8 - 2 * step, "skin")
    g.rect(12, 9, 2, 6 + 2 * step, "skin")
    g.rect(4, 19, 8, 3, "navy")
    g.rect(4, 22, 3, 6 - 2 * step, "navy").rect(9, 22, 3, 4 + 2 * step, "navy")
    g.rect(3, 28 - 2 * step, 4, 2, "ink").rect(9, 26 + 2 * step, 4, 2, "ink")
    return g


def patrizia() -> G:
    """She has been waiting at the beach all summer, and she is hungry."""
    g = G(24, 34)
    g.disc(12, 7, 8, 7, "brown")          # a great deal of hair
    g.disc(12, 7, 4.5, 5, "skin")
    g.rect(8, 5, 8, 2, "ink")             # sunglasses
    g.rect(11, 10, 3, 1, "red")
    g.rect(10, 12, 4, 2, "skin")
    g.rect(7, 14, 10, 12, "pink")
    g.rect(7, 16, 10, 1, "cream").rect(7, 20, 10, 1, "cream").rect(7, 24, 10, 1, "cream")
    g.rect(4, 15, 3, 9, "skin").rect(17, 15, 3, 9, "skin")
    g.rect(2, 13, 2, 3, "skin").rect(20, 13, 2, 3, "skin")
    g.rect(9, 26, 3, 6, "skin").rect(13, 26, 3, 6, "skin")
    g.rect(8, 32, 4, 2, "lemon").rect(13, 32, 4, 2, "lemon")
    return g


def pothole() -> G:
    g = G(32, 10)
    g.disc(16, 5, 16, 5, "greyd")
    g.disc(16, 5.5, 13, 3.8, "ink")
    g.rect(9, 6, 8, 1, "road2")
    g.line(0, 4, 3, 5, "ink").line(28, 3, 31, 6, "ink")
    return g


def food(kind: int) -> G:
    g = G(16, 16)
    if kind == 0:     # mozzariella: a white ball with its knot
        g.disc(8, 9, 7, 6.5, "white")
        g.disc(6, 7, 3, 2.5, "cream")
        g.rect(7, 1, 3, 3, "white").rect(6, 3, 5, 1, "grey")
        g.disc(11, 12, 2.5, 1.5, "grey")
    elif kind == 1:   # provola: the smoked pear shape, tied with a string
        g.disc(8, 10, 6, 5.5, "tan")
        g.disc(7, 4.5, 3, 3.5, "tan")
        g.disc(10, 12, 3, 2.5, "brown")
        g.rect(4, 6, 8, 1, "brown")
        g.rect(7, 0, 1, 2, "ink")
    elif kind == 2:   # ricotta: the basket-marked dome
        g.poly([(3, 14), (5, 4), (11, 4), (13, 14)], "white")
        g.disc(8, 4, 3.5, 2, "cream")
        for y in range(6, 14, 2):
            g.rect(4, y, 9, 1, "grey")
        for x in (5, 8, 11):
            g.put(x, 7, "cream")
            g.put(x, 11, "cream")
    elif kind == 3:   # caciotta: a pale round with a wedge cut out
        g.disc(8, 8, 7, 7, "lemon")
        g.disc(8, 8, 5.5, 5.5, "cream")
        g.poly([(8, 8), (15, 2), (16, 8)], None)
        g.line(8, 8, 14, 3, "tan").line(8, 8, 14, 8, "tan")
        g.put(5, 6, "tan")
        g.put(6, 11, "tan")
    else:             # frittatina di maccheroni: breaded, golden, split to show the pasta
        g.disc(8, 8, 7, 6.5, "orange")
        g.disc(8, 8, 5, 4.5, "lemon")
        for y in range(5, 12, 2):
            g.rect(4, y, 8, 1, "cream")
        g.line(5, 5, 11, 11, "red")
        g.put(2, 6, "brown")
        g.put(13, 10, "brown")
        g.put(9, 2, "brown")
    return g


def stand() -> G:
    """The mellonaro's stall, with the red slices on show."""
    g = G(44, 36)
    for x in range(0, 44, 8):
        g.rect(x, 0, 4, 8, "red")
        g.rect(x + 4, 0, 4, 8, "cream")
    g.rect(0, 7, 44, 1, "ink")
    g.rect(2, 8, 2, 28, "brown").rect(40, 8, 2, 28, "brown")
    g.rect(6, 10, 32, 8, "lemon")
    g.text(9, 12, "MELLONI", "ink")
    g.rect(2, 26, 40, 10, "tan")
    g.rect(2, 26, 40, 1, "brown")
    for x in (5, 15, 25):
        g.disc(x + 5, 24, 5, 4.5, "melon")
        g.rect(x + 3, 21, 1, 7, "melond")
        g.rect(x + 7, 21, 1, 7, "melond")
    g.poly([(34, 26), (41, 26), (37, 20)], "red")
    return g


def gate() -> G:
    """Arrivo: the chequered banner across the road."""
    g = G(64, 32)
    g.rect(0, 0, 3, 32, "ink").rect(61, 0, 3, 32, "ink")
    g.rect(0, 2, 64, 14, "cream")
    for y in (2, 12):
        for x in range(0, 64, 4):
            g.rect(x, y, 2, 2, "ink")
            g.rect(x + 2, y + 2, 2, 2, "ink")
    g.text(19, 7, "ARRIVO", "red")
    return g


def palm() -> G:
    g = G(40, 72)
    g.line(20, 71, 19, 18, "brown").line(21, 71, 20, 18, "brown").line(22, 71, 21, 18, "tan")
    for y in range(24, 71, 5):
        g.rect(19, y, 4, 1, "ink")
    for ang, ln in ((185, 19), (150, 20), (120, 18), (90, 14), (60, 18), (30, 20), (-5, 19)):
        a = math.radians(ang)
        ex, ey = 20 + math.cos(a) * ln, 18 - math.sin(a) * ln * 0.75 + ln * 0.25
        mx, my = 20 + math.cos(a) * ln * 0.55, 18 - math.sin(a) * ln * 0.7
        for k in range(-1, 2):
            g.line(20, 18 + k, mx, my + k, "melon")
            g.line(mx, my + k, ex, ey + k, "grass" if k else "melond")
    g.disc(20, 19, 3, 2, "brown")
    return g


def pine() -> G:
    g = G(56, 60)
    g.rect(26, 22, 4, 38, "brown").rect(29, 22, 1, 38, "ink")
    g.line(27, 28, 14, 17, "brown").line(29, 28, 42, 17, "brown")
    g.disc(28, 12, 27, 11, "melond")
    for x, y, rx, ry in ((14, 9, 10, 5), (28, 6, 12, 5), (42, 10, 9, 5), (20, 15, 9, 3), (36, 16, 9, 3)):
        g.disc(x, y, rx, ry, "melon")
    g.disc(20, 5, 5, 2, "grass").disc(36, 7, 5, 2, "grass")
    return g


def lamp() -> G:
    g = G(16, 64)
    g.rect(7, 8, 2, 56, "greyd").rect(6, 56, 4, 8, "ink")
    g.rect(2, 6, 12, 2, "greyd")
    g.rect(1, 8, 4, 3, "cream").rect(11, 8, 4, 3, "cream")
    return g


def house() -> G:
    """A wall of the narrow streets, with shutters and the washing out."""
    g = G(48, 64)
    g.rect(0, 0, 48, 64, "blue")
    g.rect(0, 0, 48, 2, "brown")
    g.rect(44, 0, 4, 64, "blued")
    g.rect(0, 52, 48, 12, "pave2")
    g.rect(0, 52, 48, 1, "greyd")
    for y in (6, 28):
        for x in (6, 28):
            g.rect(x, y, 12, 14, "ink")
            g.rect(x, y, 4, 14, "melon").rect(x + 8, y, 4, 14, "melon")
    g.rect(4, 20, 16, 2, "ink").rect(26, 20, 16, 2, "ink")
    g.rect(16, 54, 16, 10, "brown").rect(16, 54, 16, 1, "ink")
    # Washing on a line, of course.
    g.line(0, 24, 47, 24, "ink")
    for x, c, h in ((6, "cream", 5), (14, "red", 4), (26, "lemon", 5), (36, "cream", 4)):
        g.rect(x, 25, 6, h, c)
    return g


def umbrella() -> G:
    g = G(28, 32)
    g.rect(13, 10, 2, 22, "brown")
    g.poly([(0, 12), (14, 0), (28, 12)], "red")
    g.poly([(5, 12), (14, 0), (9, 12)], "cream")
    g.poly([(19, 12), (14, 0), (23, 12)], "cream")
    return g


def ferry() -> G:
    """The Ischia boat in profile: a bow door, two decks, the blue funnel."""
    g = G(96, 36)
    g.poly([(2, 20), (94, 20), (88, 34), (8, 34)], "white")
    g.rect(4, 28, 88, 2, "navy")
    g.rect(0, 16, 12, 5, "grey")
    g.rect(20, 10, 62, 10, "cream")
    g.rect(20, 18, 62, 2, "grey")
    for x in range(24, 80, 6):
        g.rect(x, 12, 3, 3, "navy")
    g.rect(32, 4, 30, 6, "white")
    g.rect(34, 6, 26, 2, "navy")
    g.rect(68, 0, 8, 10, "navy").rect(68, 2, 8, 2, "cream")
    g.rect(60, 20, 26, 8, "ink")          # the car deck, where the Ape rides
    return g


# name -> list of frames. The order is the order of the SPR_* constants.
SPRITES = [
    ("MELON", melon),
    ("APE", ape),
    ("CAR", car),
    ("TAMARRO", tamarro_car),
    ("TRUCK", truck),
    ("SCOOTER", scooter),
    ("PERSON0", lambda: person(0)),
    ("PERSON1", lambda: person(1)),
    ("POTHOLE", pothole),
    ("FOOD0", lambda: food(0)),
    ("FOOD1", lambda: food(1)),
    ("FOOD2", lambda: food(2)),
    ("FOOD3", lambda: food(3)),
    ("FOOD4", lambda: food(4)),
    ("STAND", stand),
    ("GATE", gate),
    ("PALM", palm),
    ("PINE", pine),
    ("LAMP", lamp),
    ("HOUSE", house),
    ("UMBRELLA", umbrella),
    ("FERRY", ferry),
    ("PATRIZIA", patrizia),
]
