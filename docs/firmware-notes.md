# Notes on the firmware

Things this project found in PRG32, from reading the source. The PRG32 checkout was not modified. These are for the
maintainers to judge, and none blocks the game. See also the notes of *You Have Got Pizza: Deluxe Edition*, which apply here too.

## 1. The 8-bit sprite fast path can't be reached with a full palette

`draw_compact_sprite()` in `components/prg32/prg32_sprite.c` has a `memcpy` path for 8-bit rows when the palette is an
identity: every `palette[i]` must quantise to `i`. But `prg32_gfx_index_for_rgb565_unlocked()` only returns 0 to 7 and 16
to 231, so entries 8 to 15 can never match. The path is reachable only with 8 colours or fewer.

**Effect here:** each row takes the per-pixel loop and rebuilds a 64-entry map first, about 100 times a frame: perhaps
7 to 10 ms a frame, by a rough estimate from the loop's length. **Suggestion:** an entry point that
takes a row of raw framebuffer indices would turn this into a `memcpy` for any game like this one.
**Status:** read from the source, not measured on a board.

## 2. `prg32_palette_set` differs between displays

On the ILI9341 backend it dirties the whole viewport; on QEMU it affects later indexed draws. This game sets a palette
and repaints every row in the same frame, so both look the same. A view change therefore costs one full-screen
transfer on hardware.
