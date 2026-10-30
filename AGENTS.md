# AGENTS.md

Guidance for automated coding agents and maintainers of The Trerrote Connection.

## Rules that are easy to break

- **It is a tribute, and it says so.** The tribute screen comes first, the tribute and "unofficial" are stated
  in the README, the metadata and the colophon, and tests check them. Do not weaken this.
- **No Tony Tammaro material.** No melody, lyric, recording, photograph or likeness, however short. New music
  is composed from nothing, and is never written by following or varying one of his songs.
- **Rules live in `src/tr_core.h`, with no PRG32 calls.** Anything that decides a score, a move or a collision
  goes there and gets a test in `tests/test_core.c`.
- **One source per build:** `src/trerrote.c` includes the rest. Do not add compiler flags.
- **No pointers in initialised static data.** `tools/check_relocatable.py` enforces it.
- **No libc, no floats, no 64-bit division** in cartridge code.
- **`src/gen/*`, `audio/audio.json` and `assets/png/*` are generated.** Edit `tools/` and rebuild.
- **Text is capitals and the glyphs of `FONT_ORDER`** in `tools/build_art.py`, 40 characters per line at most.
- **Colours go through `tools/palette.py`:** two colours on a screen may not share a cube cell.
- **A row that changes must be marked dirty.** `tests/test_game.c` compares the panel with a clean repaint.
- **Never publish** to the Cartridge Store from scripts. No credentials in the repository.
- **Do not modify the PRG32 checkout.** Report firmware findings in `docs/firmware-notes.md`.
- **Do not test on an attached board without asking:** it overwrites a cartridge slot.
- **Keep claims honest:** a number in `docs/` is measured, observed or estimated, and says which.

## Workflow

```bash
tests/run_tests.sh shots
```

```bash
scripts/build.sh && scripts/pack-store-bundle.sh
```

```bash
scripts/check_hosts.sh
```

Then `scripts/make_docs_data.sh`, and update the numbers quoted in `docs/`, when gameplay, art or audio change.
