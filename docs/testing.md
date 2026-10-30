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

## Not done

- **Never run on a physical ESP32-C6.** The frame rate is estimated. Display, input feel, and the speaker are all untested. No board was touched, so no cartridge slot was overwritten.
- **Never play-tested by people.** All balance figures come from an autoplayer. The controls may feel wrong.
- **Nobody has listened to the music.** See [audio.md](audio.md).
- **Stereo not heard on an Audio Plus build:** verified only as a stereo render through the firmware mixer.
- **Views not compared with reference photographs.** See [art.md](art.md).
- **PRG32 was not pinned.** The checkout was at `2ef2ac1` for the builder and headers, and it moved while this was being written. The QEMU flash image was the one already in `build-qemu/`, not rebuilt from that commit. Rebuild both from one pinned commit before release.
