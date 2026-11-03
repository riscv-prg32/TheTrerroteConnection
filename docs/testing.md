# Testing

## Run for this release

| Check | How | Result |
|---|---|---|
| Rules | `tests/test_core.c`, under ASan and UBSan | See `docs/data/render.txt` |
| Whole cartridge | `tests/test_game.c`: every screen, a full journey through real buttons | See `docs/data/render.txt` |
| Render invariant | Panel compared with a clean repaint every third frame, in all screens | No mismatch |
| Palette | Every colour of every view exact in its cell; every row decodes to its width | Pass |
| Position independence | `tools/check_relocatable.py`: linked at two addresses, bytes identical | Pass |
| PRG32 QEMU firmware | `scripts/check_hosts.sh`: boots, loads, plays, pauses, audio captured | Pass, observed in screenshots |
| PRG32-QT core | Headless, 600 frames | Pass |
| Store format | `tools/validate_bundle.py`, with the Store's own ingestion code when available | See below |
| Reproducible build | Built and packed twice, `dist/SHA256SUMS` compared | See `reproduce.md` |
| Physical ESP32-C6 | Upload over USB, remote keys, firmware frame counter, HTTP screenshots | See below |

## On the board

One ESP32-C6 prototype, with the display's picture read back through `/api/screenshot.bmp` and the frame rate from
the firmware's own frame counter in `/api/runtime`. The cartridge is stored in slot `cart6`.

### Release 1.1.0 (2026-11-04)

Firmware `c53c491-dirty`, 128 KiB profile, the same PRG32 commit that built the cartridges. The ESP32-C6 cartridge was
taken out of `dist/the-trerrote-connection-1.1.0-store.zip` (SHA-256 identical to `dist/SHA256SUMS`) and uploaded over
USB to `cart6`, replacing the earlier build of this game. Keys came from a script over the device protocol: one blind
run, then two runs that steered by reading the road out of `/api/screenshot.bmp`.

| Check | Result |
|---|---|
| Upload from the bundle, run from the slot | Yes, three starts |
| Tribute, title, attract on Ischia, briefing, leg 1, pause | Pictures as designed |
| Leg 1: crossing, setts, street lamps, double-parked cars, traffic, roadside line, view change to the Molo Beverello | Pictures as designed |
| Timer running out before the Molo: missed-ferry screen, then the leg's briefing again | Works as designed |
| A press during the attract mode | Back to the tribute screen, as the code intends |
| Frame rate, leg 1 driving (blind run) | 15.7 to 27.5 fps, median about 21.9, ten 3 to 5 s windows (measured). Part of it was on the pavement |
| Frame rate, attract / paused | 21.7 / 30.6 fps (measured, one window each) |

Every HTTP screenshot stalls the game for about half a second, so the steered runs give no frame rates (3 and 16 fps
on average, screenshot stalls included). The steered drive was too slow to reach the Molo in time, so the ferry,
Ischia and later legs were not seen in this run.

### Pre-release build (2026-11-04)

Firmware `82b8925` with the 128 KiB profile; cartridge built with PRG32 at `cc795dc`. Uploaded over USB, keys sent
over the device protocol. One session, keys pressed by hand from a script, not the scripted run used for 1.0.1.

| Check | Result |
|---|---|
| Loads and runs from the slot | Yes, three uploads |
| Title, intro, leg 1 from the start line, attract on Baia Domizia | Pictures as designed |
| Leg 1 driving: timer, progress bar, traffic, asphalt to setts | Works as designed |
| Single A presses from title to play | Each advanced one screen, none lost (3 sequences) |
| Frame rate, attract and menus | 20 to 30 fps, measured over 5 s windows |
| Frame rate, leg 1 driving | 15.7 to 25.6 fps, median about 18.5, measured over six 5 s windows |
| Free heap | Stable, about 116 KB (the 128 KiB profile reserves more for the cartridge) |

Once, opening the USB port failed with "resource busy" and the port vanished for a few seconds before coming back.
It was not repeated, and it is not known whether the board reset. The firmware's `performance` command returns no
results for this cartridge, which has no performance suite; the frame counter was used instead.

### Release 1.0.1

Firmware `c14d1dd-dirty`. The cartridge replaced one of six identical copies of `devicedemo` in `cart6`.

| Check | Result |
|---|---|
| Loads and runs from the slot | Yes, repeatedly |
| Tribute, title, intro, Naples views, mid-leg view change, pause, attract on a loaded leg | Pictures as designed |
| Frame rate | See [graphics.md](graphics.md): about 17 fps driving, 12 to 20 in attract, 30 on static screens |
| Three-press sequences reaching play | 12 of 12 in 1.0.1. In 1.0.0, a press was seen to be lost |
| Free heap across the runs | Stable, about 180 KB |

## Not done

- **On the board, 1.1.0 has been seen only in leg 1:** the menus, leg 1 to just before the Molo Beverello, pause and
  the missed ferry. A stall stop has not been seen on the board in this version.
- **The whole journey has not been driven on the board.** The ferries, the loading scene, legs 2 to 6, and the ending have run only on the host and, in part, QEMU.
- **Physical buttons untested:** keys came from the device protocol, which firmware treats the same way, but feel is untested.
- **Never play-tested by people.** All balance figures come from an autoplayer. The controls may feel wrong, and balance was tuned at a nominal 30 fps of control.
- **Nobody has listened to the music,** on any host, including the board's speaker. See [audio.md](audio.md).
- **Stereo not heard on an Audio Plus build:** verified only as a stereo render through the firmware mixer.
- **Views not compared with reference photographs.** See [art.md](art.md).
- **PRG32 was not pinned.** For the current source the builder was at `cc795dc` and the board at `82b8925`; for 1.0.1 the builder and headers were at `2ef2ac1`, the board at `c14d1dd-dirty`, and the QEMU flash image was the one already in `build-qemu/`. The 1.1.0 cartridges and bundle were built with PRG32 at `c53c491` (with an uncommitted `dependencies.lock` change in that checkout), checked on its QEMU image and on PRG32-QT `7683be1`; the board ran firmware `c53c491-dirty` for the 1.1.0 run and `82b8925` for the pre-release run, whose cartridge was built at `cc795dc`.
