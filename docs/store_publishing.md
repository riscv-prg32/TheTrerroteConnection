# Cartridge Store

`scripts/pack-store-bundle.sh` builds `dist/the-trerrote-connection-1.0.1-store.zip`: both cartridges, icon, splash, and a
manifest generated from `metadata/`. `tools/validate_bundle.py` checks it, using the Store's own ingestion code when
`../CartridgeStore` and its requirements are available.

Download it from [the repository](https://github.com/riscv-prg32/TheTrerroteConnection/raw/main/dist/the-trerrote-connection-1.0.1-store.zip); its SHA-256 is in `dist/SHA256SUMS`.

**The bundle has not been submitted.** Publishing is a separate, authenticated, human decision, and no script here
contacts a Store. Before publishing, read [originality.md](originality.md), especially the point on asking Tony Tammaro.
