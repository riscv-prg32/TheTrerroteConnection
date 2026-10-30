#!/usr/bin/env python3
"""The indexed colour model of The Trerrote Connection.

PRG32's ESP32-C6 framebuffer holds one 8-bit palette index per pixel. Every
RGB565 colour a cartridge passes to the firmware is quantised to a cell of the
system palette's 6x6x6 cube (`prg32_gfx_index_for_rgb565_unlocked`). The entry
of that cell can be overwritten with `prg32_palette_set`, which gives a free
choice of exact colours under one condition: two colours on screen at the same
time must not fall in the same cell. `solve()` meets that condition for the
FIXED colours below plus each view's own colours, and `check()` proves it.

Adapted from tools/palette.py of You Have Got Pizza: Deluxe Edition (PRG32
project family, MIT).
"""
from __future__ import annotations


def rgb565(hex_rgb: str) -> int:
    v = int(hex_rgb.lstrip("#"), 16)
    r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def rgb888(value: int) -> tuple[int, int, int]:
    r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
    return ((r * 527 + 23) >> 6, (g * 259 + 33) >> 6, (b * 527 + 23) >> 6)


NAMED = (0x0000, 0xFFFF, 0xF800, 0x07E0, 0x001F, 0xFFE0, 0x07FF, 0xF81F)


def cube_index(color: int) -> int:
    """Exact port of prg32_gfx_index_for_rgb565_unlocked()."""
    if color in NAMED:
        return NAMED.index(color)
    r = ((color >> 11) & 31) * 5 // 31
    g = ((color >> 5) & 63) * 5 // 63
    b = (color & 31) * 5 // 31
    return 16 + r * 36 + g * 6 + b


# Colours shared by every screen: road, ground, sprites, interface. Their order
# is the order of the first FIXED_COUNT entries of the cartridge's line palette.
FIXED = {
    "ink": "#15121c",     # outlines, tyres, HUD band
    "cream": "#fff6df",   # text, highlights, road lines
    "lemon": "#ffd84a",   # highlighted text, signs
    "skin": "#eeb088",
    "skind": "#a8664a",
    "red": "#d92b25",     # kerbs, tail lights, melon flesh
    "redd": "#7d1a20",
    "blue": "#7cc4e0",    # the Ape's body: the classic pale blue
    "blued": "#3d7ea6",
    "navy": "#1d3a6b",
    "grey": "#a8aab2",    # chrome, trucks' shadow side
    "greyd": "#5f626c",
    "white": "#e8e6dc",   # trucks, mozzarella
    "melon": "#2f8f3d",   # watermelon rind
    "melond": "#14532b",
    "orange": "#ef8a1f",
    "brown": "#6b4326",
    "tan": "#c7985c",     # provola, crates
    "pink": "#e77fa8",
    "purple": "#6a3d98",
    "road": "#55565c",    # asphalt, two tones
    "road2": "#494a51",
    "line": "#d9d8cc",    # lane paint
    "pave": "#b3a896",    # pavement, two tones
    "pave2": "#a0957f",
    "sea": "#2a7ea8",     # sea beside the road, two tones
    "sea2": "#3392b8",
    "sand": "#e3c78d",    # beach, two tones
    "sand2": "#d4b478",
    "grass": "#4d8a3a",   # verge, two tones
    "grass2": "#3f7732",
    "tuff": "#b08a4e",    # the yellow tuff of Naples
}
FIXED_COUNT = len(FIXED)
assert FIXED_COUNT == 32
VIEW_COLORS = 32          # each view adds up to this many: 64 in the line palette


def _cell_bounds(cell: int):
    """Inclusive RGB565 channel ranges that quantise to one cube cell."""
    v = cell - 16
    r, g, b = v // 36, (v // 6) % 6, v % 6

    def span(level: int, top: int) -> tuple[int, int]:
        values = [c for c in range(top + 1) if c * 5 // top == level]
        return values[0], values[-1]
    return span(r, 31), span(g, 63), span(b, 31)


def _nearest_in_cell(color: int, cell: int) -> int:
    (r0, r1), (g0, g1), (b0, b1) = _cell_bounds(cell)
    r = min(max((color >> 11) & 31, r0), r1)
    g = min(max((color >> 5) & 63, g0), g1)
    b = min(max(color & 31, b0), b1)
    return (r << 11) | (g << 5) | b


def distance(a: int, b: int) -> int:
    ra, ga, ba = rgb888(a)
    rb, gb, bb = rgb888(b)
    return 2 * (ra - rb) ** 2 + 4 * (ga - gb) ** 2 + 3 * (ba - bb) ** 2


ALIAS_LIMIT = 500


def solve(wanted: list[int], taken: dict[int, int] | None = None) -> list[int]:
    """Give every colour its own cube cell, moving as little as possible.

    A colour whose cell is free keeps its value. A colour nearly equal to the
    holder of its cell becomes that holder. Any other collision moves it to the
    nearest colour of the nearest free cell. Deterministic.
    """
    holders = dict(taken or {})
    out: list[int] = []
    for color in wanted:
        cell = cube_index(color)
        if cell in holders and distance(color, holders[cell]) <= ALIAS_LIMIT:
            out.append(holders[cell])
            continue
        if color in NAMED or cell in holders:
            best = None
            for candidate in range(16, 232):
                if candidate in holders:
                    continue
                moved = _nearest_in_cell(color, candidate)
                if moved in NAMED or cube_index(moved) != candidate:
                    continue
                cost = distance(color, moved)
                if best is None or cost < best[0]:
                    best = (cost, moved, candidate)
            assert best is not None
            color, cell = best[1], best[2]
        holders[cell] = color
        out.append(color)
    return out


FIXED_RGB565 = solve([rgb565(v) for v in FIXED.values()])
FIXED_INDEX = {name: i for i, name in enumerate(FIXED)}


def fixed_holders() -> dict[int, int]:
    return {cube_index(c): c for c in FIXED_RGB565}


def solve_view(colors: list[int]) -> list[int]:
    """Final RGB565 values of a view's colours, next to the fixed ones."""
    return solve(colors, fixed_holders())


def check(palette: list[int]) -> int:
    """Colours of one screen may share a cube cell only if they are equal."""
    seen: dict[int, int] = {}
    failures = 0
    for value in palette:
        cell = cube_index(value)
        if cell in seen and seen[cell] != value:
            failures += 1
        seen[cell] = value
    return failures


if __name__ == "__main__":
    n = check(FIXED_RGB565)
    print(f"palette: {FIXED_COUNT} fixed colours, {n} collisions")
    raise SystemExit(1 if n else 0)
