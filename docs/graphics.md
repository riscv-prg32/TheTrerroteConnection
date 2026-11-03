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

Each screen has up to 112 colours: 48 fixed (32 for sprites and interface, 16 for road and ground) and 64 for its
view. The fixed colours are tuned so each has a cell of its own; a few share a value on purpose (the road's grey is
also a sprite's dark grey), which the rule allows.

**Choosing the view's colours.** A first attempt quantised each painting by median cut, then moved colours to free
cells. Hues shifted badly: skies went pink. `reduce_view()` in `tools/build_art.py` starts from the cube instead:

1. Group pixels by the cell they fall in; each group's mean is an exact colour of that cell.
2. A group in a cell held by a fixed colour becomes that colour.
3. Merge the cheapest group into its nearest neighbour until 64 remain.

No colour ever crosses a cell, so no hue changes.

## 2. Pictures as rows

Views are 368 x 80 (320 plus 24 each side for parallax), sprites up to 160 wide. Sprites use `(index << 3) | run`
(32 colours, index 31 transparent), views `(index << 2) | run` (64 colours); in both, run 0 means the next byte holds
the length. Each row can be decoded on its own, in any
order, through a table of offsets, and identical rows share one encoding. There's no compression across rows, because
random access is the point: a row can be restored with no copy of the picture in memory.

## 3. The road

Each screen row `r` below the horizon is a slice of road at distance `200 / r` segments. Walking up the screen walks
along the road, and the bend accumulates as a second difference (`dx += curve; x += dx`): the cheap way the arcade
machines of the 1980s bent a road, with no 3D maths. What a row shows depends on the section's surface: dashed
centre and edge lines on asphalt, the joints of basalt setts every few segments, patches on worn asphalt, zebra
crossings in town. The kerb is a pavement edge, coloured by the ground beside it. No stripes alternate, and nothing
changes from edge to edge unless the road moves.

Objects are projected the other way, `r = 200 / distance`, and sized in proportion to `r`. Sprites are scaled by
nearest neighbour as they are copied, so one small source covers every distance. Potholes are a hash of the segment
number: no memory and no spawning, and asking twice gets the same answer. The horizon drifts against bends by up
to 24 pixels; there are no hills.

## 4. The row compositor

For each row marked dirty, `draw_row()`:

1. fills a 376-byte buffer in cartridge memory with the background: a decoded view row, or the road's spans;
2. copies in, far to near, each sprite that crosses the row;
3. adds the text;
4. sends the part that changed as runs of one indexed colour (`prg32_gfx_rect_indexed`), or, if the row is very busy, as an 8-bit indexed sprite.

Why this shape:

- **Memory.** A 320 x 104 picture of the road alone would take half the cartridge's RAM. This needs one row.
- **No flicker, no erasing.** A row is replaced in one step, and a moved sprite's old pixels vanish because the row is rebuilt.
- **One path.** Sprites over the sky, over the road, and text over both all work the same way.

A row must be redrawn when a sprite on it changes (now or last frame), when text on it changes, when the horizon
shifts, and, for road rows, when the road has moved. Each of these marks a span of the row, or all of it. `tests/test_game.c` compares the panel with a clean repaint
every third frame, in every screen.

## 5. Cost, measured on the board

The first version was tested on a physical ESP32-C6 (prototype board, firmware `c14d1dd-dirty`, SPI at 27 MHz) only
after release, and an estimate here had said about 25 fps. It ran at about 10. Frame rates below come from the
firmware's own frame counter, read over HTTP, with the same scripted run each time.

| Version | Title | Leg 1, driving | Autoplayer, loaded |
|---|---:|---:|---:|
| Row as an 8-bit sprite, whole rows | 15 fps | 10 to 12 fps | 9 to 13 fps |
| Rows as runs of colour | 19 fps | 13 to 14 fps | 11 to 14 fps |
| Changed spans, 13 flushes a frame | 7.5 fps | 4 to 5 fps | not comparable |
| Changed spans, **two flushes a frame** (current) | 20 fps | **17 to 18 fps** | 12 to 20 fps |

What this taught, in order of cost:

1. **Pixels on the display dominate.** From these runs, about 1.5 to 2 microseconds per pixel, not the 0.62 assumed
   earlier. It fits PRG32's own figure of about 150 ms for a full panel. At that price, the screen can't be repainted at
   any useful rate, so what matters is how few pixels change.
2. **A flush has a large fixed cost.** Thirteen flushes took about 90 ms longer than one, roughly 7 ms each, inferred
   from the frame rates. That rules out many small boxes. See [firmware-notes.md](firmware-notes.md).
3. **Row copying is the smaller cost:** about 14 ms a frame, inferred from the gain when it went away.

So the renderer now tracks, per row, the span that changed: the road's extent now and last frame, plus any sprites.
This is why the ground beside the road is flat and no longer alternates in bands: moving bands would change every row
from edge to edge. Kerbs and road marks carry the sense of speed. Sky and road are flushed separately, so a palm top doesn't
drag a full-width band of sky along with the road.

**The table measures 1.0.1.** The street of the current source sends fewer pixels in the host's panel model (33,604
per frame in play on average, against 37,371 before; modelled, not timed). On the board (firmware `82b8925`, 128 KiB
profile) it measured 15.7 to 25.6 fps driving leg 1, median about 18.5, over six 5-second windows, and 20 to 30 fps in
attract and the menus. That is at least as fast as 1.0.1, but it was a different firmware and a hand-driven session,
not the scripted run above, so the two are not strictly comparable. See [testing.md](testing.md).

The fixed timestep holds game speed down to about 10 fps (three ticks a frame). Below that the game runs slightly
slow. Busy scenes with pines and houses reached a low of about 12 fps in these runs, so the margin is real but not large.
