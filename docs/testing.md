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

One ESP32-C6 prototype on firmware `c14d1dd-dirty`, with the display's picture read back through `/api/screenshot.bmp`.
The cartridge was stored in slot `cart6`, replacing one of six identical copies of `devicedemo`.

| Check | Result |
|---|---|
| Loads and runs from the slot | Yes, repeatedly |
| Tribute, title, intro, Naples views, mid-leg view change, pause, attract on a loaded leg | Pictures as designed |
| Frame rate | See [graphics.md](graphics.md): about 17 fps driving, 12 to 20 in attract, 30 on static screens |
| Three-press sequences reaching play | 12 of 12 in 1.0.1. In 1.0.0, a press was seen to be lost |
| Free heap across the runs | Stable, about 180 KB |

## Not done

- **The whole journey has not been driven on the board.** The ferries, the loading scene, legs 2 to 5, and the ending have run only on the host and, in part, QEMU.
- **Physical buttons untested:** keys came from the device protocol, which firmware treats the same way, but feel is untested.
- **Never play-tested by people.** All balance figures come from an autoplayer. The controls may feel wrong, and balance was tuned at a nominal 30 fps of control.
- **Nobody has listened to the music,** on any host, including the board's speaker. See [audio.md](audio.md).
- **Stereo not heard on an Audio Plus build:** verified only as a stereo render through the firmware mixer.
- **Views not compared with reference photographs.** See [art.md](art.md).
- **PRG32 was not pinned.** The builder and headers were at `2ef2ac1`, the board at `c14d1dd-dirty`, and the QEMU flash image was the one already in `build-qemu/`. Rebuild from one pinned commit before release.
