#!/usr/bin/env python3
"""All the sprites, drawn with small primitives on a grid of fixed-colour names.

The Ape, the traffic, the street life of Naples and the five foods. Sizes are
source pixels, close to the size each thing has on screen when it is nearest, so
the cartridge mostly scales down. `.` (None) is transparent. Slots that the
cartridge recolours at run time are drawn in "blue" and "blued" (see tint_* in
src/trerrote.c), the economy of indexed hardware. Only the first 31 fixed
colours exist for sprites (tools/palette.py).
"""
from __future__ import annotations

import math

MINI = {  # 3 x 5 capitals for lettering painted on vehicles and signs
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
    "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "L": "100100100100111", "M": "101111111101101", "N": "110101101101101",
    "O": "010101101101010", "P": "110101110100100", "R": "110101110101101", "S": "011100010001110",
    "T": "111010010010010", "U": "101101101101111", "V": "101101101101010", "Z": "111001010100111",
    "'": "010010000000000", " ": "000000000000000",
}


class G:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.p: list[list[str | None]] = [[None] * w for _ in range(h)]

    def put(self, x: float, y: float, c: str | None) -> "G":
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c
        return self

    def get(self, x: int, y: int) -> str | None:
        return self.p[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def rect(self, x: float, y: float, w: float, h: float, c: str | None) -> "G":
        for py in range(int(y), int(y + h)):
            for px in range(int(x), int(x + w)):
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

    def outline(self, c: str = "ink") -> "G":
        """A one-pixel rim where the sprite meets transparency: it reads on any ground."""
        edge = []
        for y in range(self.h):
            for x in range(self.w):
                if self.p[y][x] is None and any(self.get(x + dx, y + dy) not in (None, c)
                                                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge.append((x, y))
        for x, y in edge:
            self.p[y][x] = c
        return self

    def shade(self, x0: int, x1: int, frm: str, to: str, every: int = 1) -> "G":
        """Replace one colour by another in a band of columns: the shadow side."""
        for y in range(self.h):
            for x in range(max(x0, 0), min(x1, self.w)):
                if self.p[y][x] == frm and (every == 1 or (x + y) % every == 0):
                    self.p[y][x] = to
        return self

    def dither(self, x: int, y: int, w: int, h: int, frm: str, to: str) -> "G":
        for py in range(y, y + h):
            for px in range(x, x + w):
                if self.get(px, py) == frm and (px + py) % 2 == 0:
                    self.put(px, py, to)
        return self


# ---- the load ------------------------------------------------------------------

def melon() -> G:
    g = G(12, 11)
    g.disc(6, 5.5, 6, 5.5, "melon")
    for x in (2.5, 5.5, 6.5, 9.5):
        for y in range(1, 10):
            if g.get(int(x), y):
                g.put(x, y, "melond")
    for y in range(11):
        for x in range(12):
            if g.p[y][x] and ((x + 0.5 - 6) / 6) ** 2 + ((y + 0.5 - 5.5) / 5.5) ** 2 > 0.8:
                g.p[y][x] = "melond"
    g.put(3, 2, "cream").put(4, 2, "greyl").put(3, 3, "greyl")
    return g


# ---- the Ape --------------------------------------------------------------------

def ape(hazard: bool = False) -> G:
    """The Trerrote from behind and a little above: the cab, the open bed, two rear wheels.

    The camera sits higher than a racing game's, so the bed's floor shows: the
    melons are drawn on it one by one by the cartridge.
    """
    g = G(60, 48)
    # The cab: rounded roof seen from above, the rear window, the driver.
    g.poly([(13, 7), (17, 1), (43, 1), (47, 7), (47, 22), (13, 22)], "blue")
    g.poly([(17, 1), (43, 1), (45, 4), (15, 4)], "glass")             # light on the roof
    g.rect(13, 7, 2, 15, "blued").rect(45, 7, 2, 15, "blued")
    g.poly([(18, 7), (21, 5), (39, 5), (42, 7), (42, 17), (18, 17)], "navy")
    g.disc(30, 11, 4.5, 4.5, "hair")                                   # the driver's head
    g.rect(25, 14, 10, 3, "red")                                       # his shirt
    g.rect(37, 9, 1, 4, "red").put(37, 13, "redd")                     # the corno on the mirror string
    g.rect(18, 7, 2, 2, "glass")
    # Mirrors on their stalks.
    g.rect(7, 6, 5, 4, "shade").rect(8, 7, 3, 2, "glass").rect(11, 9, 3, 1, "greyd")
    g.rect(48, 6, 5, 4, "shade").rect(49, 7, 3, 2, "glass").rect(46, 9, 3, 1, "greyd")
    # The bed, seen from above: sides, the worn wooden floor the load sits on.
    g.rect(3, 20, 54, 14, "blue")
    g.rect(5, 21, 50, 11, "brownl")
    for y in (23, 26, 29):
        g.rect(5, y, 50, 1, "brown")
    g.rect(5, 21, 50, 1, "shade")
    g.rect(3, 20, 54, 1, "glass")
    g.rect(3, 20, 2, 14, "blued").rect(55, 20, 2, 14, "blued")
    # The tailgate with its chains, the lights, the plate.
    g.rect(2, 31, 56, 10, "blue")
    g.rect(2, 31, 56, 1, "glass")
    g.rect(2, 39, 56, 2, "blued")
    g.line(4, 31, 9, 34, "greyd").line(56, 31, 51, 34, "greyd")
    lamp = "orange" if hazard else "red"
    g.rect(4, 33, 6, 4, "red").rect(5, 34, 2, 1, "redl")
    g.rect(50, 33, 6, 4, "red").rect(53, 34, 2, 1, "redl")
    g.rect(4, 37, 3, 1, lamp).rect(53, 37, 3, 1, lamp)
    g.rect(21, 33, 18, 6, "white").rect(21, 33, 18, 1, "denim")
    g.text(22, 34, "NA", "ink")
    g.text(31, 34, "TR", "ink")
    # Chassis, wheels with their mudguards, the little exhaust.
    g.rect(8, 41, 44, 2, "shade")
    for x in (3, 46):
        g.rect(x, 37, 11, 11, "ink").rect(x + 2, 39, 7, 7, "shade").rect(x + 4, 41, 3, 3, "grey")
        g.rect(x, 36, 11, 2, "blued")
    g.rect(38, 42, 5, 2, "grey").put(42, 42, "greyl")
    return g.outline()


# ---- traffic ------------------------------------------------------------------------

def car(hazard: bool = False) -> G:
    """A small, square Neapolitan utility car from behind, recoloured at run time."""
    g = G(64, 44)
    g.poly([(10, 18), (15, 3), (32, 3), (32, 20), (10, 20)], "blue")
    g.poly([(13, 18), (17, 6), (32, 6), (32, 17), (13, 17)], "navy")
    g.poly([(17, 6), (32, 6), (32, 8), (16, 9)], "denim")              # sky in the rear window
    g.rect(2, 18, 30, 17, "blue")
    g.rect(2, 18, 30, 1, "glass")
    g.rect(2, 30, 30, 5, "blued")
    lamp = "orange" if hazard else "redd"
    g.rect(4, 21, 9, 6, "red").rect(5, 22, 3, 2, "redl").rect(4, 27, 9, 2, lamp)
    g.rect(0, 35, 32, 3, "shade")
    g.rect(3, 34, 11, 10, "ink").rect(5, 36, 7, 6, "shade")
    g.rect(2, 16, 3, 3, "shade")                                       # wing mirror
    g.mirror()
    g.rect(24, 24, 16, 5, "white").rect(25, 25, 14, 3, "greyl")          # the plate
    g.rect(26, 26, 2, 1, "ink").rect(30, 26, 4, 1, "ink").rect(36, 26, 2, 1, "ink")
    g.rect(40, 37, 4, 2, "grey")
    g.rect(14, 37, 36, 1, "greyd")
    return g.outline()


def tamarro_car() -> G:
    """Same car with everything added that nobody asked for."""
    g = G(64, 44)
    g.poly([(11, 20), (15, 7), (32, 7), (32, 22), (11, 22)], "blue")
    g.poly([(13, 20), (17, 9), (32, 9), (32, 20)], "ink")                # tinted to black
    g.rect(17, 10, 4, 1, "greyd")
    g.rect(1, 20, 31, 13, "blue")
    g.rect(1, 20, 31, 1, "lemon")                                       # a stripe, gold
    g.rect(4, 23, 9, 4, "red").rect(5, 24, 6, 1, "redl")
    g.rect(1, 29, 31, 3, "blued")
    g.rect(0, 32, 32, 3, "shade")
    g.rect(1, 31, 12, 13, "ink").rect(3, 33, 8, 8, "grey").rect(5, 35, 4, 4, "greyl")   # wide rims
    g.rect(0, 42, 32, 2, "purple")                                       # the underglow
    g.rect(3, 12, 3, 9, "ink")                                           # the spoiler's legs
    g.rect(0, 9, 32, 3, "lemon").rect(0, 9, 32, 1, "gold")
    g.mirror()
    g.rect(20, 26, 24, 5, "shade")                                       # the subwoofer grille
    for x in (22, 28, 34, 40):
        g.rect(x, 27, 3, 3, "greyd")
    for x in (14, 19, 41, 46):                                           # four exhausts
        g.rect(x, 33, 4, 3, "grey").put(x + 1, 34, "ink")
    return g.outline()


def truck() -> G:
    """The mozzarella truck: a refrigerated box, a buffalo painted on its doors."""
    g = G(96, 100)
    g.rect(0, 0, 96, 76, "white")
    g.rect(0, 0, 96, 3, "greyl")
    g.rect(88, 0, 8, 76, "greyl")
    g.dither(80, 0, 8, 76, "white", "greyl")
    g.rect(0, 70, 96, 6, "grey")
    g.rect(47, 4, 2, 64, "grey")                                          # the doors' seam
    for x in (40, 54):
        g.rect(x, 26, 2, 16, "greyd")                                     # handles
    # The lettering, in the dairy's blue.
    g.rect(4, 6, 88, 18, "navy")
    g.text(9, 9, "MOZZARELLA", "white").text(13, 16, "DI BUFALA", "white")
    # A buffalo's head: broad, dark, the horns curving out and back.
    for side in (-1, 1):
        g.poly([(48 + side * 8, 42), (48 + side * 20, 36), (48 + side * 28, 40), (48 + side * 26, 46),
                (48 + side * 22, 41), (48 + side * 10, 47)], "greyd")
        g.poly([(48 + side * 20, 36), (48 + side * 28, 40), (48 + side * 27, 42), (48 + side * 21, 38)], "greyl")
        g.disc(48 + side * 13, 47, 4, 2.5, "shade")                     # the ears
    g.disc(48, 50, 10, 10, "shade")
    g.poly([(40, 52), (56, 52), (54, 64), (42, 64)], "shade")
    g.disc(48, 62, 7, 5, "greyd")                                     # the muzzle
    g.disc(45, 62, 1.5, 1.2, "ink").disc(51, 62, 1.5, 1.2, "ink")
    g.disc(43, 49, 1.6, 1.6, "cream").disc(53, 49, 1.6, 1.6, "cream")
    g.put(43, 49, "ink").put(53, 49, "ink")
    g.rect(46, 41, 4, 3, "hair")
    # Chassis, lights, plate, twin wheels.
    g.rect(0, 76, 96, 6, "shade")
    g.rect(4, 77, 10, 4, "red").rect(82, 77, 10, 4, "red").rect(5, 78, 4, 1, "redl").rect(83, 78, 4, 1, "redl")
    g.rect(36, 77, 24, 5, "white").rect(38, 78, 20, 3, "greyl")
    for x in (3, 66):
        g.rect(x, 82, 27, 18, "ink").rect(x + 3, 85, 9, 12, "shade").rect(x + 15, 85, 9, 12, "shade")
    g.rect(30, 82, 36, 4, "greyd")
    return g.outline()


def scooter() -> G:
    """Three on a scooter, nobody in a helmet: seen from behind."""
    g = G(28, 44)
    g.disc(14, 5, 4.5, 4.5, "hair")                                       # the driver
    g.rect(11, 9, 6, 2, "skin")
    g.rect(7, 11, 14, 9, "blue").rect(7, 11, 14, 1, "glass")
    g.rect(4, 12, 3, 7, "skin").rect(21, 12, 3, 7, "skin")
    g.rect(1, 11, 4, 2, "greyd").rect(23, 11, 4, 2, "greyd")              # handlebar ends
    g.disc(14, 15, 4, 4, "hair")                                          # the second, a boy
    g.rect(9, 19, 10, 8, "blued").rect(12, 19, 4, 1, "gold")              # and his gold chain
    g.disc(8, 20, 2.5, 2.5, "hair").rect(6, 22, 5, 5, "pink")             # the third, a girl, side-saddle
    g.rect(8, 27, 12, 6, "shade")                                         # seat and tail
    g.rect(10, 28, 8, 2, "red").rect(11, 28, 3, 1, "redl")
    g.rect(6, 28, 3, 7, "greyd").rect(19, 28, 3, 7, "greyd")
    g.rect(12, 33, 4, 11, "ink").rect(13, 35, 2, 7, "shade")
    g.rect(18, 34, 4, 2, "grey")
    return g.outline()


# ---- people --------------------------------------------------------------------------

def person(step: int) -> G:
    """A passer-by, walking. Shirt in the tint slots: everyone dresses differently."""
    g = G(20, 38)
    g.disc(10, 5, 4, 4.5, "skin")
    g.disc(10, 3, 4.5, 3, "hair")
    g.put(8, 6, "skind").put(12, 6, "skind")
    g.rect(5, 10, 10, 13, "blue")
    g.rect(5, 10, 10, 1, "blued").rect(13, 11, 2, 12, "blued")
    g.rect(3, 11, 2, 9 - 2 * step, "skin").rect(15, 11, 2, 7 + 2 * step, "skin")
    g.rect(5, 23, 10, 3, "denim")
    g.rect(5, 26, 4, 9 - 3 * step, "denim").rect(11, 26, 4, 6 + 3 * step, "denim")
    g.rect(4, 35 - 3 * step, 5, 3, "shade").rect(11, 32 + 3 * step, 5, 3, "shade")
    return g.outline()


def patrizia() -> G:
    """She has been waiting at the beach all summer, and she is hungry."""
    g = G(32, 46)
    g.disc(16, 10, 11, 10, "hair")                                        # a great deal of hair
    g.disc(14, 6, 5, 3, "brown")
    g.disc(16, 10, 6, 7, "skin")
    g.rect(10, 7, 12, 3, "ink").rect(11, 8, 4, 1, "greyd").rect(17, 8, 4, 1, "greyd")   # sunglasses
    g.rect(14, 14, 4, 1, "red")
    g.rect(13, 17, 6, 3, "skin")
    g.rect(9, 19, 14, 16, "pink")
    for y in (21, 25, 29, 33):
        g.rect(9, y, 14, 1, "cream")
    g.rect(5, 20, 4, 12, "skin").rect(23, 20, 4, 12, "skin")
    g.rect(3, 15, 3, 6, "skin").rect(26, 15, 3, 6, "skin")                 # waving both arms
    g.rect(2, 13, 4, 3, "skinl").rect(26, 13, 4, 3, "skinl")
    g.rect(11, 35, 4, 8, "skin").rect(17, 35, 4, 8, "skin")
    g.rect(10, 43, 5, 3, "lemon").rect(17, 43, 5, 3, "lemon")
    g.rect(20, 22, 2, 8, "gold")                                          # her bag strap
    return g.outline()


# ---- the road -----------------------------------------------------------------------

def pothole() -> G:
    """A Neapolitan buca: broken edges, and last night's rain still in it."""
    g = G(48, 13)
    g.disc(24, 6.5, 24, 6.5, "greyd")
    g.disc(24, 7, 20, 5, "shade")
    g.disc(25, 7.5, 16, 3.5, "denim")
    g.rect(15, 7, 10, 1, "glass")
    for x, y in ((2, 4), (6, 10), (44, 3), (41, 10), (12, 1), (33, 1)):
        g.rect(x, y, 3, 2, "greyd")
    return g


def food(kind: int) -> G:
    g = G(20, 20)
    if kind == 0:     # mozzariella: a white ball with its knot, in its whey
        g.disc(10, 12, 9, 8, "white")
        g.disc(7, 9, 4, 3, "cream")
        g.rect(8, 1, 4, 4, "white").rect(7, 4, 6, 1, "greyl")
        g.disc(14, 16, 3, 2, "greyl")
    elif kind == 1:   # provola: the smoked pear shape, tied with a string
        g.disc(10, 13, 8, 7, "tan")
        g.disc(9, 6, 4, 4.5, "tan")
        g.disc(13, 15, 4, 3.5, "brownl")
        g.disc(7, 10, 2, 2, "lemon")
        g.rect(5, 8, 10, 1, "brown").rect(9, 0, 1, 3, "ink")
    elif kind == 2:   # ricotta: the dome marked by its basket
        g.poly([(3, 18), (6, 5), (14, 5), (17, 18)], "white")
        g.disc(10, 5, 4.5, 2.5, "cream")
        for y in range(8, 18, 2):
            g.rect(4, y, 12, 1, "greyl")
        for x in (6, 10, 14):
            g.put(x, 9, "cream").put(x, 13, "cream")
    elif kind == 3:   # caciotta: a pale round with a wedge cut out
        g.disc(10, 10, 9, 9, "gold")
        g.disc(10, 10, 7.5, 7.5, "lemon")
        g.disc(10, 10, 6, 6, "cream")
        g.poly([(10, 10), (19, 2), (20, 10)], None)
        g.line(10, 10, 18, 3, "tan").line(10, 10, 18, 10, "tan")
        g.put(6, 7, "tan").put(7, 14, "tan").put(12, 14, "tan")
    else:             # frittatina di maccheroni: breaded, golden, split to show the pasta
        g.disc(10, 10, 9, 8, "orange")
        g.disc(10, 10, 6.5, 5.5, "lemon")
        for y in range(6, 15, 2):
            g.rect(5, y, 10, 1, "cream")
        g.line(6, 6, 14, 14, "red")
        for x, y in ((2, 7), (17, 12), (11, 2), (4, 15), (15, 4)):
            g.put(x, y, "brown")
    return g.outline()


def stand() -> G:
    """The mellonaro's stall: striped awning, the hand-painted board, a pyramid of
    melons and the red slices on ice, the scale he never uses."""
    g = G(88, 72)
    for x in range(0, 88, 11):
        g.rect(x, 0, 6, 12, "red").rect(x + 6, 0, 5, 12, "cream")
    for x in range(0, 88, 11):                                           # scalloped edge
        g.disc(x + 3, 12, 3, 2, "red").disc(x + 8.5, 12, 2.5, 2, "cream")
    g.rect(0, 0, 88, 1, "redd")
    g.rect(3, 14, 3, 58, "brown").rect(82, 14, 3, 58, "brown")
    g.rect(14, 16, 60, 13, "lemon").rect(14, 16, 60, 1, "gold").rect(14, 28, 60, 1, "gold")
    g.text(30, 20, "MELLONI", "redd")
    g.rect(16, 18, 4, 9, "red").rect(68, 18, 4, 9, "red")
    # The counter and the pyramid.
    g.rect(2, 52, 84, 20, "tan").rect(2, 52, 84, 2, "brownl").dither(2, 54, 84, 18, "tan", "brownl")
    for row, (y, xs) in enumerate(((47, (8, 20, 32, 44)), (39, (14, 26, 38)), (31, (20, 32)))):
        for x in xs:
            g.disc(x + 6, y + 5, 6.5, 5.5, "melon")
            g.rect(x + 3, y + 1, 1, 9, "melond").rect(x + 7, y, 1, 10, "melond")
            g.put(x + 3, y + 2, "greyl")
    # Slices, red and white with black seeds, on the right.
    for k, x in enumerate((58, 66, 74)):
        g.poly([(x, 50), (x + 8, 50), (x + 4, 40)], "red")
        g.rect(x, 50, 8, 2, "melon").rect(x, 49, 8, 1, "cream")
        g.put(x + 3, 46, "ink").put(x + 5, 45, "ink").put(x + 4, 47, "ink")
    # The scale.
    g.rect(64, 30, 14, 2, "grey").rect(70, 32, 2, 8, "greyd").disc(71, 36, 4, 3, "greyl")
    return g.outline()


def sign(name: str) -> G:
    """The white sign that marks where a town begins, black on white, two posts."""
    w = max(4 * len(name) + 8, 40)
    g = G(w, 34)
    g.rect(0, 0, w, 15, "ink")
    g.rect(1, 1, w - 2, 13, "white")
    g.rect(2, 2, w - 4, 11, "ink")
    g.rect(3, 3, w - 6, 9, "white")
    g.text((w - 4 * len(name) + 1) // 2, 5, name, "ink")
    g.rect(6, 15, 2, 19, "greyd").rect(w - 8, 15, 2, 19, "greyd")
    g.rect(6, 15, 1, 19, "grey").rect(w - 8, 15, 1, 19, "grey")
    return g


# ---- the roadside ----------------------------------------------------------------------

def palm() -> G:
    g = G(60, 108)
    for y in range(27, 108):
        x = 28 + (y - 27) * 2 // 80
        g.rect(x, y, 2, 1, "brown").put(x + 2, y, "brownl").put(x + 3, y, "tan")
    for y in range(32, 106, 6):
        g.rect(28, y, 5, 1, "brown").put(32, y + 1, "shade")
    for ang, ln in ((190, 29), (160, 30), (130, 27), (100, 22), (75, 22), (45, 27), (18, 30), (-10, 29)):
        a = math.radians(ang)
        ex, ey = 30 + math.cos(a) * ln, 27 - math.sin(a) * ln * 0.7 + ln * 0.35
        mx, my = 30 + math.cos(a) * ln * 0.55, 27 - math.sin(a) * ln * 0.7
        for k in range(-2, 3):
            g.line(30, 27 + k * 0.5, mx, my + k, "melon")
            g.line(mx, my + k, ex, ey + k * 0.6, "melond" if abs(k) == 2 else "melon" if k else "olive")
    g.disc(30, 28, 4, 3, "brown").put(29, 30, "orange").put(31, 31, "orange")
    return g.outline("melond")


def pine() -> G:
    """The umbrella pine of the Domitian coast: a flat dark crown on a bare trunk."""
    g = G(98, 104)
    g.rect(46, 38, 6, 66, "brown").rect(50, 38, 2, 66, "shade").rect(46, 38, 1, 66, "brownl")
    g.line(48, 50, 26, 30, "brown").line(48, 49, 26, 29, "brown").line(50, 48, 72, 28, "brown").line(50, 47, 72, 27, "brown")
    g.disc(49, 20, 48, 18, "melond")
    for x, y, rx, ry in ((24, 15, 18, 8), (49, 10, 22, 8), (74, 16, 17, 8), (34, 25, 16, 6), (64, 26, 16, 6)):
        g.disc(x, y, rx, ry, "olive")
    for x, y, rx, ry in ((22, 11, 9, 3), (48, 6, 12, 3), (70, 12, 8, 3)):
        g.disc(x, y, rx, ry, "melon")
    g.dither(1, 26, 96, 12, "olive", "melond")
    return g


def lamp() -> G:
    """The cast-iron lamp-post of the seafront, a lantern on a curled arm."""
    g = G(24, 84)
    g.rect(10, 12, 4, 72, "shade").rect(10, 12, 1, 72, "greyd")
    g.rect(8, 74, 8, 10, "ink").rect(7, 80, 10, 4, "shade")
    g.line(12, 14, 4, 8, "shade").line(4, 8, 4, 12, "shade")
    g.line(12, 14, 20, 8, "shade").line(20, 8, 20, 12, "shade")
    for x in (1, 17):
        g.poly([(x, 12), (x + 6, 12), (x + 5, 20), (x + 1, 20)], "lemon")
        g.rect(x, 11, 7, 2, "ink").rect(x + 2, 20, 3, 2, "ink")
        g.rect(x + 2, 13, 2, 5, "cream")
    g.disc(12, 10, 2, 3, "ink")
    return g


def house(kind: int = 0) -> G:
    """A palazzo of the narrow streets: shutters, a balcony, washing, a shop below."""
    g = G(84, 112)
    g.rect(0, 0, 84, 112, "blue")
    if kind:
        g.dither(0, 0, 84, 112, "blue", "blued")
    g.rect(0, 0, 84, 4, "brownl").rect(0, 4, 84, 2, "brown")              # cornice
    g.rect(78, 0, 6, 112, "blued")
    for y in (12, 50):
        for x in (8, 46):
            g.rect(x, y, 24, 28, "greyl")                                   # stone frame
            g.rect(x + 2, y + 2, 20, 26, "hair")
            g.rect(x + 2, y + 2, 6, 26, "olive").rect(x + 16, y + 2, 6, 26, "olive")   # green shutters
            for sy in range(y + 4, y + 28, 3):
                g.rect(x + 2, sy, 6, 1, "melond").rect(x + 16, sy, 6, 1, "melond")
    # A balcony with its railing and a pot of geraniums.
    g.rect(4, 40, 76, 3, "greyl").rect(4, 43, 76, 1, "shade")
    for x in range(6, 80, 4):
        g.rect(x, 33, 1, 7, "shade")
    g.rect(4, 32, 76, 1, "shade")
    g.rect(60, 28, 8, 5, "rust").disc(64, 27, 5, 3, "melon").put(62, 26, "red").put(66, 25, "red").put(64, 24, "redl")
    # Washing on a line, of course.
    g.line(0, 46, 83, 47, "shade")
    for x, c, h in ((10, "white", 9), (22, "red", 7), (34, "lemon", 10), (50, "white", 8), (62, "pink", 9)):
        g.rect(x, 47, 9, h, c).rect(x, 47, 9, 1, "greyl" if c != "white" else "grey")
    # The ground floor: a basso with its door open, a shop sign.
    g.rect(0, 84, 84, 28, "greyl")
    g.rect(0, 84, 84, 2, "shade")
    g.rect(8, 90, 26, 22, "shade").rect(10, 92, 22, 20, "hair")
    g.rect(44, 88, 32, 10, "cream").rect(44, 88, 32, 1, "gold")
    g.text(47, 91, "SALUMERIA" if kind else "TABACCHI", "navy")
    g.rect(48, 100, 24, 12, "brown").rect(49, 101, 22, 11, "brownl")
    return g


def umbrella() -> G:
    g = G(46, 50)
    g.rect(22, 16, 2, 34, "greyl").rect(23, 16, 1, 34, "grey")
    g.poly([(0, 18), (23, 0), (46, 18)], "red")
    for x0 in (7, 30):
        g.poly([(x0, 18), (23, 0), (x0 + 8, 18)], "cream")
    for x in range(0, 46, 8):
        g.disc(x + 4, 18, 4, 2, "red" if (x // 8) % 2 == 0 else "cream")
    g.rect(0, 18, 46, 1, "redd")
    return g


def shrine() -> G:
    """An edicola votiva: a niche in the wall, a painted Madonna, flowers and a lamp."""
    g = G(36, 56)
    g.rect(0, 0, 36, 56, "greyl")
    g.rect(0, 0, 36, 2, "grey").rect(34, 0, 2, 56, "grey")
    g.poly([(4, 14), (18, 3), (32, 14)], "rust")                          # the little roof
    g.rect(6, 14, 24, 28, "gold")
    g.rect(8, 16, 20, 24, "navy")
    g.disc(18, 23, 4, 4.5, "skinl")                                       # the face
    g.poly([(11, 40), (18, 26), (25, 40)], "glass")                       # her blue mantle
    g.poly([(14, 40), (18, 30), (22, 40)], "white")
    g.disc(18, 18, 6, 2, "lemon")
    g.rect(16, 18, 4, 1, "gold")
    g.rect(4, 42, 28, 4, "grey")
    for x, c in ((7, "red"), (11, "white"), (15, "pink"), (21, "red"), (25, "lemon"), (29, "white")):
        g.disc(x, 41, 2, 2, c).put(x, 43, "melon")
    g.rect(16, 46, 4, 6, "redd").rect(17, 44, 2, 2, "orange")             # the votive lamp
    return g


def bins() -> G:
    """La monnezza della gente: green bins, and the bags that did not fit."""
    g = G(64, 40)
    for x in (2, 32):
        g.rect(x, 6, 28, 30, "olive")
        g.rect(x, 6, 28, 3, "melond").rect(x + 24, 9, 4, 27, "melond")
        g.rect(x + 3, 12, 20, 2, "melond")
        g.rect(x + 2, 36, 5, 4, "ink").rect(x + 21, 36, 5, 4, "ink")
        g.poly([(x - 1, 6), (x + 2, 0), (x + 26, 0), (x + 29, 6)], "melond")
    for x, y, c in ((0, 30, "shade"), (12, 32, "greyd"), (26, 28, "shade"), (40, 31, "denim"), (52, 30, "shade"), (58, 34, "greyd")):
        g.disc(x + 6, y + 4, 6.5, 5, c).rect(x + 5, y - 1, 2, 2, c)
    g.disc(46, 2, 7, 4, "shade").rect(45, -1, 2, 3, "shade")                # one on the lid
    g.rect(20, 36, 6, 3, "white").rect(34, 37, 5, 2, "red")
    return g.outline()


def washing() -> G:
    """A line of washing strung across the street, from balcony to balcony."""
    g = G(160, 26)
    for x in range(160):
        g.put(x, 2 + int(5 * math.sin(math.pi * x / 159)), "shade")
    colors = ("white", "red", "lemon", "white", "denim", "pink", "white", "glass", "red", "white", "lemon", "white")
    for k, c in enumerate(colors):
        x = 6 + k * 13
        y = 3 + int(5 * math.sin(math.pi * x / 159))
        h = 9 + (k * 7) % 8
        g.rect(x, y, 10, h, c)
        g.rect(x, y, 10, 1, "greyl" if c != "white" else "grey")
        if k % 3 == 0:
            g.rect(x + 3, y + h - 3, 4, 3, None)                             # a pair of trousers
    return g


def ferry() -> G:
    """The Ischia boat in profile: a bow door, two decks, the blue funnel."""
    g = G(160, 60)
    g.poly([(2, 32), (156, 32), (148, 56), (12, 56)], "white")
    g.poly([(8, 46), (152, 46), (148, 56), (12, 56)], "navy")
    g.rect(6, 44, 146, 2, "red")
    g.rect(0, 26, 18, 7, "grey")
    g.rect(30, 16, 104, 16, "cream")
    g.rect(30, 29, 104, 3, "grey")
    for x in range(36, 130, 8):
        g.rect(x, 19, 5, 5, "navy").rect(x, 19, 5, 1, "glass")
    g.rect(52, 6, 52, 10, "white")
    g.rect(55, 9, 46, 3, "navy")
    g.rect(112, 0, 14, 16, "navy").rect(112, 3, 14, 3, "cream")
    g.rect(98, 32, 44, 12, "shade")                                          # the car deck, where the Ape rides
    g.line(4, 26, 30, 16, "greyd")
    return g.outline("navy")


# name -> builder. The order is the order of the SPR_* constants.
SIGNS = ["MOLO BEVERELLO", "ISCHIA PORTO", "CASORIA", "TORREGAVETA", "MONDRAGONE", "BAIA DOMIZIA"]
SPRITES = [
    ("MELON", melon),
    ("APE", ape),
    ("CAR", car),
    ("CAR_HAZARD", lambda: car(True)),
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
    ("PALM", palm),
    ("PINE", pine),
    ("LAMP", lamp),
    ("HOUSE", lambda: house(0)),
    ("HOUSE2", lambda: house(1)),
    ("UMBRELLA", umbrella),
    ("SHRINE", shrine),
    ("BINS", bins),
    ("WASHING", washing),
    ("FERRY", ferry),
    ("PATRIZIA", patrizia),
] + [(f"SIGN{i}", (lambda n: lambda: sign(n))(name)) for i, name in enumerate(SIGNS)]
