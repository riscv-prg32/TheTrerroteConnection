#!/usr/bin/env python3
"""Store art, from the game's own sources and from a real emulator frame.

  python3 tools/make_store_art.py [frame.png]

assets/store/icon.png        64 x 64: the Trerrote from behind, with its load
assets/store/screenshot.png  320 x 200: a frame captured from the QEMU firmware,
                             palettised so that it stays small in the cartridge
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PIL import Image  # noqa: E402

import art_sprites as sp  # noqa: E402
import palette as pal  # noqa: E402


def stamp(img: Image.Image, g: sp.G, ox: int, oy: int) -> None:
    for y, row in enumerate(g.p):
        for x, c in enumerate(row):
            if c:
                img.putpixel((ox + x, oy + y), pal.rgb888(pal.FIXED_RGB565[pal.FIXED_INDEX[c]]))


def icon() -> Image.Image:
    img = Image.new("RGB", (64, 64), (118, 186, 226))
    for y in range(44, 64):
        for x in range(64):
            img.putpixel((x, y), (73, 74, 81))
    ape, melon = sp.ape(), sp.melon()
    stamp(img, ape, 2, 14)
    px = (4, 14, 24, 34, 44, 9, 19, 29, 39, 14, 24, 34)
    py = (21, 21, 21, 21, 21, 13, 13, 13, 13, 5, 5, 5)
    for x, y in zip(px, py):
        stamp(img, melon, 2 + x, 14 + y)
    return img


def main() -> int:
    out = ROOT / "assets/store"
    out.mkdir(parents=True, exist_ok=True)
    icon().quantize(24, dither=Image.Dither.NONE).save(out / "icon.png", optimize=True)
    if len(sys.argv) > 1:
        frame = Image.open(sys.argv[1]).convert("RGB")
        if frame.size == (320, 240):   # strip the firmware bands
            frame = frame.crop((0, 20, 320, 220))
        frame.quantize(32, dither=Image.Dither.NONE).save(out / "screenshot.png", optimize=True)
    print({p.name: p.stat().st_size for p in out.glob("*.png")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
