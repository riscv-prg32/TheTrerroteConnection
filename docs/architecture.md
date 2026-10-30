# Architecture

| File | Role |
|---|---|
| `src/tr_core.h` | The rules: road, Ape, traffic, melons, thieves, autoplayer. No PRG32 calls |
| `src/tr_music.h` | Sequencer and effects: pattern/order lists, one effect channel |
| `src/trerrote.c` | The cartridge: flow between screens, HUD, road drawing, row compositor |
| `src/gen/art.inc` | Generated: palettes, views, sprites, font, level tables |
| `src/gen/music.inc` | Generated: patterns, songs, effects |
| `tools/` | Text sources of everything generated, and the release checks |
| `tests/` | Host tests that compile the real cartridge against the real PRG32 headers |

## One frame

The firmware calls `trerrote_update()`, `trerrote_draw()`, then presents.

**Update** runs a fixed 33 ms step as many times as the clock requires (three at most), so game and music keep
their speed on a slow host. Each step ticks the music, runs one screen's logic, and for play calls `tr_tick()`,
then turns its events into sound.

**Draw** rebuilds the sprite list from the game state, compares it with the last frame, marks the rows that
changed, and redraws just those rows. See [graphics.md](graphics.md).

## Why portable cartridges constrain the code

A cartridge is copied to whatever address the host chooses and has no relocation records. So no initialised
static data may hold a pointer, and strings and tables are reached PC-relative at run time. For the same reason,
`-fno-jump-tables` is imposed by the builder. `tools/check_relocatable.py` links the image at two addresses and
requires identical bytes.

The rules and the screen meet in one direction only: `tr_core.h` reports events, and `trerrote.c` decides what they
look and sound like. That is why tests and the balance study run the rules with no display at all.
