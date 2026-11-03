# The Trerrote Connection

**A tribute game for the myth of many generations: il Grande Maestro Tony Tammaro.**

Tony Tammaro is the Neapolitan singer-songwriter who, since his *Prima cassetta di musica tamarra* in 1989, has
made several generations laugh at, and with, the tamarri. This game is a homage to him and to that world, for the
[PRG32](https://github.com/riscv-prg32/PRG32) RISC-V console. Enjoy the tamarro vibes!

> **This is an unofficial tribute**, made by fans with affection. It was not made, endorsed or reviewed by Tony
> Tammaro, and it contains none of his music, lyrics, recordings or images. The soundtrack is original. His official
> site is [tonytammaro.com](https://www.tonytammaro.com). See [docs/originality.md](docs/originality.md).

![The Lungomare of Naples](docs/media/leg1_b.png)

You drive a Trerrote, the three-wheeled Ape Car, and you deliver watermelons.

| | Leg | What it asks of you |
|---|---|---|
| 1 | **Villa Comunale → Molo Beverello**, Naples | Beat the traffic jam and catch the ferry to Ischia |
| 2 | **Ischia**, loaded with 24 melons, down to the port | Narrow lanes and many turns: take them too fast and the melons leave |
| 3 | **Pozzuoli → Casoria** | Stop at the stalls to sell, past *la monnezza della gente* and the double-parked cars |
| 4 | **Casoria → Torregaveta** | Down the Asse Mediano and back to the sea, where the tamarri give way to nobody |
| 5 | **Torregaveta → Mondragone** | Potholes, tamarri, and the mozzarella truck |
| 6 | **Mondragone → Baia Domizia** | All of it at once, with the sun going down, and Patrizia waiting at the finish |

**A melon that falls keeps going.** Hit something and the Ape stops but the melon flies on along the road. Drive over
it to get it back, before a passer-by or another car does. The horn scatters the thieves, and sometimes even moves the
car in front. Along the way, pick up what Patrizia ordered, in order: **mozzariella, provola, ricotta, caciotta** and
a **frittatina di maccheroni**. She is waiting at Baia Domizia, and she is hungry.

**This is not a race.** The road is a Neapolitan street: basalt cobbles, pavements, double-parked cars with
their hazards on, Vespas, washing hung across the lane. A melon stall wants you to pull over on its side and stop,
and the mellonaro takes the melons one at a time. The top of the screen is the delivery docket: time, melons on
board, takings, and how far along the route you are.

| | |
|---|---|
| ![Tribute](docs/media/tribute.png) | ![Title](docs/media/title.png) |
| ![Ischia](docs/media/leg2_b.png) | ![The Domitiana](docs/media/leg4_a.png) |
| ![Loading](docs/media/loading.png) | ![Ferry](docs/media/ferry1.png) |

On screen the game speaks Italian, as it should.

## Controls

| Input | Action |
|---|---|
| Joystick left / right | Steer |
| A | Accelerate |
| B or joystick down | Brake |
| Joystick up | Horn |
| START | Pause; on the title, the high scores |

In QEMU: `w a s d`, `j` for A, `k` for B, and Enter.

## What it shows off

- **Eight-bit indexed colour:** every row reaches the firmware as an indexed sprite, with exact palettes solved against the firmware's quantiser: up to 112 colours per screen, 48 fixed and 64 for the view.
- **Eight views of the real places**, painted by code: Castel dell'Ovo and Vesuvius, the Maschio Angioino, the Castello Aragonese, the Serapeum of Pozzuoli, the palazzoni and San Mauro of Casoria, the tuff of Torregaveta, Monte Petrino, the pines of Baia Domizia. About 3.6 to 5.9 KB each.
- **A pseudo-3D street in a 128 KiB cartridge:** a row compositor that holds one row in memory, not one frame. Nothing is ever erased, so nothing flickers.
- **Eight SID-like voices:** an original soundtrack in the manner of Neapolitan cassette pop, stereo effects that follow the action, and an engine that coughs like a two-stroke. It plays in mono on the default firmware and in stereo on an Audio Plus build.
- **Evidence:** millions of test checks, a repaint test of the renderer, a Monte Carlo balance study, and a build meant to reproduce byte for byte.

## Status

Release 1.1.0, which needs the 128 KiB cartridge profile, runs on the PRG32 firmware under QEMU and on the PRG32-QT core, and passes the Cartridge Store's own ingestion check. An earlier build of the same source, with an older PRG32, has run on a physical ESP32-C6 through the menus and leg 1, at about 18.5 frames per second driving (median, measured). Release 1.0.1 ran there at about 17 frames per second in play. **It has not been played by people, the whole journey has not been driven on the board, and nobody has heard the soundtrack.** See [docs/testing.md](docs/testing.md).

## Download

| File | For |
|---|---|
| [Cartridge Store bundle, 1.1.0](https://github.com/riscv-prg32/TheTrerroteConnection/raw/main/dist/the-trerrote-connection-1.1.0-store.zip) | Submitting to the Store (not yet submitted; see [docs/store_publishing.md](docs/store_publishing.md)) |
| [ESP32-C6 cartridge](https://github.com/riscv-prg32/TheTrerroteConnection/raw/main/dist/the-trerrote-connection-esp32c6.prg32) | A PRG32 console |
| [QEMU cartridge](https://github.com/riscv-prg32/TheTrerroteConnection/raw/main/dist/the-trerrote-connection-qemu.prg32) | The PRG32 QEMU firmware |
| [Gameplay preview, 60 s with sound](https://github.com/riscv-prg32/TheTrerroteConnection/raw/main/docs/media/preview.mp4) (MP4, 1.7 MB) | Watching: recorded in PRG32 QEMU, tribute to leg 1 |

Checksums are in [dist/SHA256SUMS](dist/SHA256SUMS).

## Build

With [PRG32](https://github.com/riscv-prg32/PRG32) as a sibling checkout and the ESP-IDF RISC-V toolchain installed:

```bash
tests/run_tests.sh
```

```bash
scripts/build.sh && scripts/pack-store-bundle.sh
```

Full instructions: [docs/reproduce.md](docs/reproduce.md).

## Documentation

Start at [docs/index.md](docs/index.md).

## License

The code and original assets are MIT. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff). The MIT license covers this game only: it grants nothing over Tony Tammaro's name or work.
