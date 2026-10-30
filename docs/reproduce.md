# Reproducing every artefact

The build is meant to be deterministic: with the same tool versions it should reproduce `dist/SHA256SUMS` byte for byte.
It has been verified by building and packing twice on one machine, not yet on a second one.

## 1. Environment

| Component | Version | Needed for |
|---|---|---|
| OS | macOS (Apple Silicon); Linux should work, untested | Everything |
| PRG32 | `riscv-prg32/PRG32` around `2ef2ac1` (see [testing.md](testing.md)) | Builder, headers, mixer sources |
| RISC-V toolchain | `riscv32-esp-elf-gcc` from ESP-IDF | Building; another compiler changes the bytes |
| Python | 3.12, with Pillow 11.3 | Art, scripts |
| C compiler | Any C99 compiler with ASan and UBSan | Host tests |
| Espressif QEMU | With the PRG32 QEMU firmware built | QEMU runs only |
| ffmpeg | Any recent | Preview and audio renders only |

## 2. Layout

Repositories are siblings. Each location can be overridden with `PRG32_REPO`, `PRG32_QT_REPO` or `CARTRIDGE_STORE_REPO`.

## 3. Test, build, pack

```bash
tests/run_tests.sh shots
```

```bash
scripts/build.sh && scripts/pack-store-bundle.sh
```

```bash
cd dist && shasum -a 256 -c SHA256SUMS
```

## 4. Run

From this repository, a scripted run. The flash image is copied to a temporary directory:

```bash
scripts/qemu_preview.py --script smoke --out build/qemu-smoke
```

To play by hand, from the PRG32 checkout:

```bash
python3 -m prg32 qemu upload ../TheTrerroteConnection/dist/the-trerrote-connection-qemu.prg32 --flash build-qemu/qemu_flash.bin
```

```bash
python3 -m prg32 qemu run
```

The firmware boots into its setup menu: choose *Run cartridge*, then the cartridge.

## 5. Documentation data and Store media

```bash
scripts/make_docs_data.sh
```

```bash
scripts/qemu_preview.py --script preview --video --out build/qemu-preview
```

```bash
python3 tools/make_store_art.py build/qemu-preview/store.png
```

Media come from a real time-dependent run, and the attract leg depends on the clock, so they are **not
bit-reproducible**. They are committed inputs. Since the screenshot goes into the cartridge, rebuild afterwards.
