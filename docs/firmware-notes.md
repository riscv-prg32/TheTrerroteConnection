# Notes on the firmware

Things this project found in PRG32, from reading the source. The PRG32 checkout was not modified. These are for the
maintainers to judge, and none blocks the game. See also the notes of *You Have Got Pizza: Deluxe Edition*, which apply here too.

## 1. Every present turns the RGB LED off

`prg32_gfx_present()` in `components/prg32/prg32_display_ili9341.c` ends with
`prg32_shared_rgb_led_off()`, which initialises the LED driver, sends the "off" colour, releases the driver and returns
the shared pin to the LCD. It runs on every present, even when nothing has been lit.

**Effect here:** 13 presents a frame measured 5 fps, against 17 for two, so about 7 ms each, inferred. The source reads as
the likely cause, but the time was not attributed by a profiler. It rules out the many-small-boxes technique, which
otherwise suits this display, and which *You Have Got Pizza: Deluxe Edition* relies on.
**Suggestion:** only do this when the LED was on.

## 2. Pixels cost about three times the wire time

SPI at 27 MHz needs about 0.6 us per pixel, but these runs imply 1.5 to 2 us: `prg32_gfx_present()` expands 8 rows
into a buffer and sends them with a polling transmit. `PRG32_LCD_FLUSH_ROWS` and DMA with a queued transaction look
worth measuring. **Status:** inferred from frame rates on one board; a stage-by-stage measurement would settle it.

## 3. The 8-bit sprite fast path can't be reached with a full palette

`draw_compact_sprite()` in `components/prg32/prg32_sprite.c` has a `memcpy` path for 8-bit rows when the palette is an
identity: every `palette[i]` must quantise to `i`. But `prg32_gfx_index_for_rgb565_unlocked()` only returns 0 to 7 and 16
to 231, so entries 8 to 15 can never match. The path is reachable only with 8 colours or fewer. This game avoided the
per-pixel loop by using `prg32_gfx_rect_indexed`; going from sprite rows to runs gained about 25%.

## 4. `prg32_palette_set` differs between displays

On the ILI9341 backend it dirties the whole viewport; on QEMU it affects later indexed draws. This game sets a palette
and repaints every row in the same frame, so both look the same. A view change therefore costs one full-screen
transfer on hardware.
