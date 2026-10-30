# Audio

## The instrument

PRG32 offers eight mixer voices at 22,050 Hz, with SID-like procedural instruments: triangle, saw, pulse or noise,
a 4-bit pulse width, a resonant filter and an ADSR envelope. Eighteen are defined in `tools/build_audio.py` and
shipped in a 184-byte AUD0 block. No samples or recordings are used.

## Voices

| Channel | Role | Pan |
|---|---|---|
| 0 | Bass | Centre |
| 1, 2 | Organ off-beats (third, fifth) | Left, right |
| 3 | Lead, cycling through three pulse widths | Slight motion |
| 4 | Mandolin figure | Ping-pong |
| 5 | Drum machine: kick, snare, hats on one channel | Slight motion |
| 6 | Effects, panned to where they happen (on the title, an echo of the lead) | Follows the event |
| 7 | The engine (on the title, a pad) | Centre |

**The engine** is the small joke of the sound design: one short pulse note per firing, faster and higher with
speed. A two-stroke sings by coughing, so the note's restart is the sound.

## The sequencer

Pattern/order lists, as on 8-bit trackers: a pattern is a 4/4 bar of 16 sixteenths, and a song lists one (pattern,
transposition) pair per voice per bar. Tempo is a whole number of 33 ms frames per step. Adapted from *You Have Got
Pizza: Deluxe Edition*, whose [audio notes](https://github.com/riscv-prg32/YouHaveGotPizza-DeluxeEdition) explain why
a cartridge sequencer is used instead of the firmware's tracker. Total: 1,968 bytes of patterns, 1,792 of order
lists, 108 of effects.

## The score

Written for this game. Only melodies and chord charts are written by hand, and the accompaniment follows fixed rules
in the tool. Melodies must use chord tones on beats 1 and 3, checked at build time.

| Song | Key | Step | Quarter tempo | Used |
|---|---|---:|---:|---|
| L'inno del mellone | A minor | 4 frames | 114 BPM | Tribute, title |
| Lungomare | A minor | 3 frames | 152 BPM | Leg 1 |
| Ischia | F major | 4 frames | 114 BPM | Leg 2 |
| Strada | D minor | 3 frames | 152 BPM | Legs 3, 4 |
| Tramonto | G major | 4 frames | 114 BPM | Leg 5 |
| Six jingles | various | 3 to 6 frames | | Ready, loading, ferry, arrival, game over, ending |

The style is that of Neapolitan cassette pop: oom-pah from a drum machine and organ, mandolin tremolo, minor keys,
the Neapolitan chord (B flat in A minor, E flat in D minor). Those are common conventions of a genre.
[originality.md](originality.md) says how the line against copying was held.

## Measured

Through the firmware's own mixer (`tests/render_music.c`): see `docs/data/audio_metrics.csv`. Peaks are about 10,500
to 12,100 of 32,767, so nothing clips. Stereo correlation is 0.91 to 0.93, a fairly narrow image.

**Nobody has listened to this yet.** An AI composed it from theory and measurements; whether it is any good, and
whether the mix and the engine's level are right, needs a pair of ears. Renders are in `docs/media/*.m4a`.
