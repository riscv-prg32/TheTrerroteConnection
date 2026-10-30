# Graphics

## 1. Indexed colour with exact palettes

On the ESP32-C6, PRG32's game surface is 64,000 bytes of 8-bit palette indices, expanded to RGB565 only while a
dirty strip is sent to the ILI9341. A colour passed as RGB565 is first *quantised* to a cell of the system
palette's 6x6x6 cube. That gives a technique: if colour **C** falls in cell **q(C)**, then

```c
prg32_palette_set(q(C), C);
```

makes that cell show exactly C. The one condition is that **two different colours on screen at once must not share
a cell**. QEMU keeps a direct-colour surface, which shows the value as it is, so both displays get the same picture.

Each screen has up to 64 colours: 32 fixed for road, ground, sprites and interface, and 32 for its view.

**Choosing the view's colours.** A first attempt quantised each painting by median cut, then moved colours to free
cells. Hues shifted badly: skies went pink. `reduce_view()` in `tools/build_art.py` starts from the cube instead:

1. Group pixels by the cell they fall in; each group's mean is an exact colour of that cell.
2. A group in a cell held by a fixed colour becomes that colour.
3. Merge the cheapest group into its nearest neighbour until 32 remain.

No colour ever crosses a cell, so no hue changes.

## 2. Pictures as rows

Views are 368 x 80 (320 plus 24 each side for parallax), sprites up to 96 wide. Both use one code:
`(index << 3) | run`, with run 0 meaning the next byte holds the length. Each row can be decoded on its own, in any
order, through a table of offsets, and identical rows share one encoding. There's no compression across rows, because
random access is the point: a row can be restored with no copy of the picture in memory.

## 3. The road

Each screen row `r` below the horizon is a slice of road at distance `200 / r` segments. Walking up the screen walks
along the road, and the bend accumulates as a second difference (`dx += curve; x += dx`): the cheap way the arcade
machines of the 1980s bent a road, with no 3D maths. Segments alternate in pairs for the stripes.

Objects are projected the other way, `r = 200 / distance`, and sized in proportion to `r`. Sprites are scaled by
nearest neighbour as they are copied, so one small source covers every distance. Potholes are a hash of the segment
number: no memory and no spawning, and asking twice gets the same answer. The horizon drifts against bends by up
to 24 pixels; there are no hills.

## 4. The row compositor

For each row marked dirty, `draw_row()`:

1. fills a 376-byte buffer in cartridge memory with the background: a decoded view row, or the road's spans;
2. copies in, far to near, each sprite that crosses the row;
3. adds the text;
4. sends the row to the firmware as a one-row, 8-bit indexed sprite.

Why this shape:

- **Memory.** A 320 x 104 picture of the road alone would take half the cartridge's RAM. This needs one row.
- **No flicker, no erasing.** A row is replaced in one step, and a moved sprite's old pixels vanish because the row is rebuilt.
- **One path.** Sprites over the sky, over the road, and text over both all work the same way.

A row must be redrawn when a sprite on it changes (now or last frame), when text on it changes, when the horizon
shifts, and, for road rows, when the road has moved. `tests/test_game.c` compares the panel with a clean repaint
every third frame, in every screen.

## 5. Cost

Measured in the host model and on the PRG32-QT core's ESP32-C6 model; see [testing.md](testing.md):

| Quantity | Value | Kind |
|---|---|---|
| Cartridge CPU per frame, mean / peak | About 5 ms / 11 ms | Modelled by PRG32-QT, attract mode; cartridge code only |
| Firmware's copy of each row | Perhaps 7 to 10 ms | Estimated from the loop's length: about 25 instructions per pixel |
| Pixels sent per frame in play, mean | About 44,000 of 64,000 | Measured, host panel model |
| Display time at 0.62 us per pixel | About 27 ms mean, 40 ms peak | Estimated; the per-pixel figure is from a sibling project |

Together that suggests about 25 frames per second on hardware, with the fixed timestep holding game speed. **This has not been measured on a board**, and it is the first thing to check there. If it's too slow, a
higher horizon would cut road rows, and alternating ground colours could be dropped so narrow rows need less.

A finding along the way is in [firmware-notes.md](firmware-notes.md): the firmware has a `memcpy` fast path for 8-bit
rows which this palette can't reach.
