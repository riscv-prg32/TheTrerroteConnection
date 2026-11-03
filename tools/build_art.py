#!/usr/bin/env python3
"""Build every picture and road of the cartridge from the text sources in tools/.

  python3 tools/build_art.py

Outputs (deterministic; both are committed):
  src/gen/art.inc      palettes, views, sprites, font, levels
  assets/png/*.png     previews of the sprites and of each view as the panel shows it

Pictures are stored as run-length rows that can be decoded one at a time, in any
order: the cartridge never holds a whole picture in memory. See docs/graphics.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PIL import Image  # noqa: E402

import art_scenes as sc  # noqa: E402
import art_sprites as sp  # noqa: E402
import font8  # noqa: E402
import levels as lv  # noqa: E402
import palette as pal  # noqa: E402

FONT_ORDER = list(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:!?.,-+/'")
TRANSPARENT = pal.FIXED_INDEX["tuff"]   # no sprite uses the tuff colour


# ---- reducing a painting to the firmware's cube --------------------------------

def _to565(rgb) -> int:
    return ((rgb[0] >> 3) << 11) | ((rgb[1] >> 2) << 5) | (rgb[2] >> 3)


def reduce_view(img: Image.Image, count: int = pal.VIEW_COLORS):
    """Choose `count` colours that each own one cube cell, and map the picture.

    Pixels are first grouped by the cell they fall in, so every group's mean is
    an exact colour of that cell. A group in a cell held by a fixed colour simply
    becomes that colour. The smallest groups are then merged into their nearest
    neighbour until `count` remain. Nothing is moved across cells, so no colour
    changes hue, which is what a first, naive palette did.
    """
    w, h = img.size
    px = img.load()
    fixed = pal.fixed_holders()
    groups: dict[int, list[int]] = {}   # cell -> [n, r, g, b]
    cell_of = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            rgb = px[x, y]
            cell = pal.cube_index(_to565(rgb))
            if cell < 16:               # a pure named colour: use its cube cell instead
                cell = 16 + (rgb[0] * 6 // 256) * 36 + (rgb[1] * 6 // 256) * 6 + rgb[2] * 6 // 256
            cell_of[y][x] = cell
            g = groups.setdefault(cell, [0, 0, 0, 0])
            g[0] += 1
            g[1] += rgb[0]
            g[2] += rgb[1]
            g[3] += rgb[2]

    def color(cell: int) -> int:
        if cell in fixed:
            return fixed[cell]
        g = groups[cell]
        mean = _to565((g[1] // g[0], g[2] // g[0], g[3] // g[0]))
        value = pal._nearest_in_cell(mean, cell)
        return value if value not in pal.NAMED else value ^ 1

    merged: dict[int, int] = {}
    live = sorted(groups)
    while len(live) > count:
        # Merge the group that costs least: population times distance to its nearest.
        best = None
        for a in live:
            for b in live:
                if a == b:
                    continue
                cost = groups[a][0] * pal.distance(color(a), color(b))
                if best is None or cost < best[0]:
                    best = (cost, a, b)
        _, a, b = best
        merged[a] = b
        for k in range(4):
            groups[b][k] += groups[a][k]
        live.remove(a)

    def final(cell: int) -> int:
        while cell in merged:
            cell = merged[cell]
        return cell

    live = sorted(live, key=lambda c: -groups[c][0])
    index = {cell: i for i, cell in enumerate(live)}
    colors = [color(c) for c in live]
    pixels = [[index[final(cell_of[y][x])] for x in range(w)] for y in range(h)]
    while len(colors) < count:
        colors.append(colors[0])
    assert pal.check(pal.FIXED_RGB565 + colors) == 0
    return colors, pixels


def encode_rows(rows: list[list[int]]) -> tuple[list[int], list[int]]:
    """(index << 3) | run, run 1..7; run 0 means the next byte holds a longer run.

    Identical rows share one encoding: skies are mostly flat bands.
    """
    data: list[int] = []
    seen: dict[tuple, int] = {}
    offsets = []
    for row in rows:
        key = tuple(row)
        if key in seen:
            offsets.append(seen[key])
            continue
        seen[key] = len(data)
        offsets.append(len(data))
        x = 0
        while x < len(row):
            run = 1
            while x + run < len(row) and row[x + run] == row[x] and run < 255:
                run += 1
            if run < 8:
                data.append((row[x] << 3) | run)
            else:
                data += [row[x] << 3, run]
            x += run
    return offsets, data


def c_bytes(data, per: int = 24) -> str:
    data = list(data)
    return "\n".join("    " + ",".join(str(v) for v in data[i:i + per]) + "," for i in range(0, len(data), per))


def array(ctype: str, name: str, values) -> str:
    values = list(values)
    return f"static const {ctype} {name}[{len(values)}] = {{\n{c_bytes(values)}\n}};"


def rgb_of_fixed(name: str):
    return pal.rgb888(pal.FIXED_RGB565[pal.FIXED_INDEX[name]])


def main() -> int:
    if lv.check():
        return 1
    (ROOT / "src/gen").mkdir(parents=True, exist_ok=True)
    png = ROOT / "assets/png"
    png.mkdir(parents=True, exist_ok=True)
    out = ["/* Generated by tools/build_art.py. Do not edit: change the sources in tools/. */"]
    out.append(f"#define FIXED_COUNT {pal.FIXED_COUNT}\n#define VIEW_COLORS {pal.VIEW_COLORS}")
    out.append(f"#define VIEW_W {sc.W}\n#define VIEW_H {sc.H}\n#define VIEW_COUNT {len(sc.VIEWS)}")
    out += [f"#define VIEW_{name.upper()} {n}" for n, (name, _, _) in enumerate(sc.VIEWS)]
    out.append(f"#define SPR_TRANSPARENT {TRANSPARENT}")
    for name, i in pal.FIXED_INDEX.items():
        out.append(f"#define C_{name.upper()} {i}")
    out.append(array("uint16_t", "fixed_palette", pal.FIXED_RGB565))

    # Views.
    view_pal: list[int] = []
    view_rows: list[int] = []
    view_data: list[int] = []
    sheet = Image.new("RGB", (sc.W, (sc.H + 2) * len(sc.VIEWS)))
    for n, (name, _, painter) in enumerate(sc.VIEWS):
        colors, pixels = reduce_view(painter())
        offsets, data = encode_rows(pixels)
        view_pal += colors
        view_rows += [len(view_data) + o for o in offsets]
        view_data += data
        print(f"view {name:12} {len(data):5d} bytes")
        for y in range(sc.H):
            for x in range(sc.W):
                sheet.putpixel((x, n * (sc.H + 2) + y), pal.rgb888(colors[pixels[y][x]]))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(png / "views.png")
    assert len(view_data) < 65536
    out.append(array("uint16_t", "view_palette", view_pal))
    out.append(array("uint16_t", "view_rows", view_rows))
    out.append(array("uint8_t", "view_data", view_data))

    # Sprites.
    spr_rows: list[int] = []
    spr_data: list[int] = []
    spr_w, spr_h, spr_first = [], [], []
    tiles = []
    for i, (name, make) in enumerate(sp.SPRITES):
        g = make()
        for row in g.p:
            for c in row:
                assert c != "tuff" and (c is None or c in pal.FIXED_INDEX), (name, c)
        rows = [[pal.FIXED_INDEX[c] if c else TRANSPARENT for c in row] for row in g.p]
        offsets, data = encode_rows(rows)
        spr_w.append(g.w)
        spr_h.append(g.h)
        spr_first.append(len(spr_rows))
        spr_rows += [len(spr_data) + o for o in offsets]
        spr_data += data
        out.append(f"#define SPR_{name} {i}")
        tiles.append(g)
    out.append(f"#define SPR_COUNT {len(sp.SPRITES)}")
    out.append(array("uint8_t", "spr_w", spr_w))
    out.append(array("uint8_t", "spr_h", spr_h))
    out.append(array("uint16_t", "spr_first", spr_first))
    out.append(array("uint16_t", "spr_rows", spr_rows))
    out.append(array("uint8_t", "spr_data", spr_data))
    print(f"sprites: {len(sp.SPRITES)}, {len(spr_data)} + {2 * len(spr_rows)} bytes")

    # Sprite sheet preview.
    cols, x, y, rowh = 320, 2, 2, 0
    prev = Image.new("RGB", (cols, 240), (70, 80, 90))
    for g in tiles:
        if x + g.w + 2 > cols:
            x, y, rowh = 2, y + rowh + 2, 0
        for py, row in enumerate(g.p):
            for px_, c in enumerate(row):
                if c:
                    prev.putpixel((x + px_, y + py), rgb_of_fixed(c))
        x += g.w + 2
        rowh = max(rowh, g.h)
    prev.resize((cols * 3, 720), Image.NEAREST).save(png / "sprites.png")

    # Font.
    glyphs: list[int] = []
    for ch in FONT_ORDER:
        rows = font8.FONT[ch].split("|")
        for row in rows:
            value = 0
            for i, c in enumerate(row):
                if c == "#":
                    value |= 0x80 >> i
            glyphs.append(value)
        glyphs += [0] * (8 - len(rows))
    ascii_map = [FONT_ORDER.index(chr(k)) if chr(k) in FONT_ORDER else 0 for k in range(32, 96)]
    out.append(array("uint8_t", "font_bits", glyphs))
    out.append(array("uint8_t", "font_ascii", ascii_map))

    # Levels.
    out.append(f"#define LEVEL_COUNT {len(lv.LEVELS)}")
    sec_bytes: list[int] = []
    level_rows: list[int] = []
    anchors: list[int] = []
    names: list[int] = []
    for level in lv.LEVELS:
        first = len(sec_bytes) // lv_SECTION
        for s in level["sections"]:
            sec_bytes += [s[0] & 255, s[0] >> 8, s[1] & 255, s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9]]
        first_anchor = len(anchors) // 4
        for kind, seg, where in level["anchors"]:
            anchors += [kind, seg & 255, seg >> 8, where & 255]
        total = lv.length(level)
        level_rows.append([first, len(level["sections"]), first_anchor, len(level["anchors"]), total, level["time"],
                           level["views"][0], level["views"][1], level["swap"], lv.SONGS.index(level["song"]),
                           lv.STYLES.index(level["style"]), 1 if level["melons"] > 0 else 0])
        for key in ("name", "dest"):
            names += [ord(c) for c in level[key].ljust(16, "\0")]
    out.append(f"#define SECTION_BYTES {lv_SECTION}")
    out.append(array("uint8_t", "section_data", sec_bytes))
    out.append(array("uint8_t", "anchor_data", anchors))
    out.append(f"static const uint16_t level_table[{len(lv.LEVELS)}][12] = {{")
    for row in level_rows:
        out.append("    {" + ",".join(str(v) for v in row) + "},")
    out.append("};")
    out.append(array("uint8_t", "level_names", names))
    (ROOT / "src/gen/art.inc").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"art: views {len(view_data) + 2 * len(view_rows) + 2 * len(view_pal)} B, "
          f"sprites {len(spr_data) + 2 * len(spr_rows)} B, font {len(glyphs)} B, "
          f"levels {len(sec_bytes) + len(anchors) + len(names) + 24 * len(lv.LEVELS)} B")
    return 0


lv_SECTION = 11

if __name__ == "__main__":
    raise SystemExit(main())
