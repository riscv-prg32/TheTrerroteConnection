#!/usr/bin/env python3
"""Compose and encode the soundtrack of The Trerrote Connection.

  python3 tools/build_audio.py

Outputs (deterministic; both are committed):
  audio/audio.json   the SID-like instruments, for PRG32's AUD0 packer
  src/gen/music.inc  patterns, order lists and effects for src/tr_music.h

Every melody below was written for this game and appears nowhere else. It is
*in the spirit of* the Neapolitan cassette pop that Tony Tammaro parodies and
celebrates: the oom-pah of a drum machine and an organ, mandolin tremolo, minor
keys with the Neapolitan chord, a shameless modulation when the chorus comes
round. Those are the conventions of a genre, shared by everybody; no melody,
lyric or arrangement of any existing song is quoted or adapted. See
docs/originality.md. No sample is used: every sound is an oscillator.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = 16   # one pattern: a bar of 4/4 in sixteenth notes
HOLD, OFF = 0, 1

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def synth(wave: int, width: int, cutoff: int, resonance: int) -> int:
    """PRG32_AUDIO_SYNTH_ID: waveform 0 triangle, 1 saw, 2 pulse, 3 noise."""
    return 0x8000 | (resonance << 10) | (cutoff << 6) | (width << 2) | wave


TRI, SAW, PULSE, NOISE = 0, 1, 2, 3

# name, wave, pulse width, cutoff, resonance, attack, decay, sustain, release.
# Envelope bytes follow the firmware law: time_ms = 1 + v * v * 2000 / 65025.
INSTRUMENTS = [
    ("bass", TRI, 8, 10, 1, 0, 64, 70, 22),
    ("organ_l", PULSE, 5, 13, 1, 0, 50, 30, 22),
    ("organ_r", PULSE, 10, 13, 1, 0, 50, 30, 22),
    ("lead_a", PULSE, 3, 15, 2, 2, 72, 150, 30),
    ("lead_b", PULSE, 5, 15, 2, 2, 72, 150, 30),
    ("lead_c", PULSE, 7, 15, 2, 2, 72, 150, 30),
    ("mandolin", PULSE, 4, 15, 2, 0, 36, 0, 12),
    ("kick", NOISE, 8, 2, 3, 0, 40, 0, 10),
    ("snare", NOISE, 8, 13, 0, 0, 28, 0, 10),
    ("echo", PULSE, 8, 12, 1, 3, 56, 0, 24),
    ("pad", TRI, 8, 13, 0, 22, 70, 170, 70),
    ("engine", PULSE, 3, 7, 3, 0, 26, 0, 6),
    ("sfx_horn", PULSE, 8, 15, 1, 0, 80, 180, 12),
    ("sfx_thud", NOISE, 8, 2, 2, 0, 44, 0, 12),
    ("sfx_crash", NOISE, 8, 9, 1, 0, 76, 0, 30),
    ("sfx_chime", TRI, 8, 15, 0, 0, 62, 0, 40),
    ("sfx_zap", SAW, 8, 12, 3, 0, 34, 0, 12),
    ("sfx_boat", SAW, 8, 6, 2, 12, 110, 200, 60),
]
INST = {row[0]: i for i, row in enumerate(INSTRUMENTS)}

CHORDS = {"Am": (9, "min"), "Dm": (2, "min"), "Gm": (7, "min"), "Em": (4, "min"), "Bm": (11, "min"),
          "E7": (4, "dom"), "A7": (9, "dom"), "C7": (0, "dom"),
          "C": (0, "maj"), "F": (5, "maj"), "G": (7, "maj"), "D": (2, "maj"), "Bb": (10, "maj"), "Eb": (3, "maj")}
TONES = {"min": (0, 3, 7), "maj": (0, 4, 7), "dom": (0, 4, 7, 10)}


def midi(token: str) -> int:
    name, octave = token[:-1], int(token[-1])
    return 12 * (octave + 1) + NOTE[name]


def melody(line: str, tremolo: bool = False) -> list[int]:
    """'A4:2 C5:2 -:4' into one byte per step; tremolo restrikes long notes, as a mandolin does."""
    out: list[int] = []
    for token in line.split():
        name, _, dur = token.partition(":")
        length = int(dur or 1)
        if name == "-":
            out += [OFF] + [HOLD] * (length - 1)
        elif tremolo:
            out += [midi(name)] * length
        else:
            out += [midi(name)] + [HOLD] * (length - 1)
    if len(out) != STEPS:
        raise SystemExit(f"pattern {line!r} has {len(out)} steps, not {STEPS}")
    return out


# ---- the themes ----------------------------------------------------------------

# "L'inno del mellone": the title. Pompous, as a proper anthem must be.
TITLE = {
    "fps": 4, "loop": True, "tremolo": True,
    "chart": ["Am", "Dm", "G", "C", "F", "Bb", "E7", "Am", "Am", "Dm", "G", "C", "F", "E7", "Am", "Am"],
    "lead": [
        "E5:3 E5:1 A5:4 C6:6 B5:2",
        "A5:3 A5:1 F5:4 D6:6 C6:2",
        "B5:3 B5:1 G5:4 D6:6 B5:2",
        "C6:3 C6:1 G5:4 E5:6 G5:2",
        "A5:3 A5:1 C6:4 F6:6 E6:2",
        "D6:3 D6:1 Bb5:4 F5:6 G5:2",
        "G#5:3 G#5:1 B5:4 D6:4 B5:2 G#5:2",
        "A5:8 E5:4 -:4",
        "E5:3 E5:1 A5:4 C6:6 B5:2",
        "A5:3 A5:1 F5:4 D6:6 C6:2",
        "B5:3 B5:1 G5:4 D6:6 B5:2",
        "C6:3 C6:1 G5:4 E5:6 G5:2",
        "C6:3 C6:1 A5:4 F5:6 A5:2",
        "B5:3 B5:1 G#5:4 E5:6 G#5:2",
        "A5:4 C6:4 E6:6 D6:2",
        "C6:4 A5:4 A4:4 -:4",
    ],
}

# Via Caracciolo in the morning traffic: hectic, in A minor.
LUNGOMARE = {
    "fps": 3, "loop": True,
    "chart": ["Am", "Am", "E7", "Am", "Dm", "Am", "E7", "Am", "C", "G", "Am", "E7", "F", "Bb", "E7", "Am"],
    "lead": [
        "A4:2 C5:2 E5:4 C5:2 B4:2 A4:4",
        "E5:2 F5:2 E5:4 C5:2 B4:2 A4:4",
        "G#4:2 B4:2 E5:4 D5:2 B4:2 G#4:4",
        "A4:2 B4:2 C5:2 E5:2 A5:6 -:2",
        "A5:2 G5:2 F5:4 D5:2 E5:2 F5:4",
        "E5:2 D5:2 C5:4 A4:2 B4:2 C5:4",
        "B4:2 D5:2 G#5:4 E5:2 D5:2 B4:4",
        "A4:4 E5:4 A5:4 -:4",
        "G5:2 E5:2 C5:4 E5:2 G5:2 C6:4",
        "B5:2 G5:2 D5:4 G5:2 B5:2 D6:4",
        "C6:2 A5:2 E5:4 A5:2 C6:2 E6:4",
        "D6:2 B5:2 G#5:4 E5:2 G#5:2 B5:4",
        "C6:2 A5:2 F5:4 A5:2 C6:2 F6:4",
        "D6:2 Bb5:2 F5:4 Bb5:2 D6:2 F6:4",
        "E6:2 D6:2 B5:2 G#5:2 E5:4 G#5:4",
        "A5:4 E5:2 C5:2 A4:4 -:4",
    ],
}

# The lanes of Ischia: sunny, skipping, in F, with a little hesitation in every bar.
ISCHIA = {
    "fps": 4, "loop": True,
    "chart": ["F", "Dm", "Bb", "C", "F", "Dm", "Gm", "C7", "Am", "Dm", "Gm", "C", "Bb", "C", "F", "F"],
    "lead": [
        "C5:3 F5:3 A5:2 F5:2 G5:2 A5:4",
        "A5:3 F5:3 D5:2 F5:2 E5:2 D5:4",
        "D5:3 F5:3 Bb5:2 F5:2 G5:2 Bb5:4",
        "G5:3 E5:3 C5:2 E5:2 F5:2 G5:4",
        "C6:3 A5:3 F5:2 A5:2 G5:2 F5:4",
        "F5:3 D5:3 A4:2 D5:2 E5:2 F5:4",
        "G5:3 Bb5:3 D6:2 Bb5:2 A5:2 G5:4",
        "E5:3 G5:3 Bb5:2 G5:2 F5:2 E5:4",
        "E5:3 A5:3 C6:2 A5:2 G5:2 E5:4",
        "F5:3 A5:3 D6:2 A5:2 G5:2 F5:4",
        "D5:3 G5:3 Bb5:2 G5:2 F5:2 D5:4",
        "E5:3 G5:3 C6:2 G5:2 E5:2 C5:4",
        "D5:2 F5:2 Bb5:4 D6:2 Bb5:2 F5:4",
        "E5:2 G5:2 C6:4 E6:2 C6:2 G5:4",
        "A5:2 C6:2 F6:4 C6:2 A5:2 F5:4",
        "F5:4 C5:4 F4:4 -:4",
    ],
}

# The Domitiana: the road tune, D minor, a nagging repeated note like a horn in a queue.
STRADA = {
    "fps": 3, "loop": True,
    "chart": ["Dm", "Dm", "Bb", "A7", "Gm", "Dm", "A7", "Dm", "F", "C", "Dm", "A7", "Bb", "Eb", "A7", "Dm"],
    "lead": [
        "D5:2 D5:1 D5:1 F5:2 A5:2 F5:2 G5:2 E5:2 D5:2",
        "A5:2 A5:1 A5:1 G5:2 F5:2 D5:4 -:4",
        "Bb5:2 Bb5:1 Bb5:1 A5:2 G5:2 F5:2 D5:2 F5:4",
        "A5:2 G5:2 E5:2 C#5:2 A4:4 C#5:2 E5:2",
        "G5:2 G5:1 G5:1 Bb5:2 G5:2 D5:4 G5:4",
        "F5:2 F5:1 F5:1 A5:2 F5:2 D5:4 A4:4",
        "C#5:2 E5:2 A5:2 G5:2 E5:2 C#5:2 A4:4",
        "D5:4 A5:4 D6:4 -:4",
        "C6:2 C6:1 C6:1 A5:2 F5:2 C5:4 F5:4",
        "C6:2 C6:1 C6:1 G5:2 E5:2 C5:4 G5:4",
        "D6:2 D6:1 D6:1 A5:2 F5:2 D5:4 A5:4",
        "C#6:2 C#6:1 C#6:1 A5:2 E5:2 C#5:4 E5:4",
        "D6:2 Bb5:2 F5:2 D5:2 F5:2 Bb5:2 D6:4",
        "Eb6:2 Bb5:2 G5:2 Eb5:2 G5:2 Bb5:2 Eb6:4",
        "E6:2 C#6:2 A5:2 E5:2 G5:2 E5:2 C#5:4",
        "D5:4 F5:4 D5:4 -:4",
    ],
}

# Toward Baia Domizia at sunset: unashamedly romantic, the mandolin trembling.
TRAMONTO = {
    "fps": 4, "loop": True, "tremolo": True,
    "chart": ["G", "Em", "C", "D", "G", "Em", "Am", "D", "C", "D", "Bm", "Em", "Am", "D", "G", "G"],
    "lead": [
        "D5:4 G5:4 B5:6 A5:2",
        "G5:4 E5:4 B4:6 E5:2",
        "C5:4 E5:4 G5:6 E5:2",
        "F#5:4 A5:4 D6:6 C6:2",
        "B5:4 G5:4 D5:6 G5:2",
        "B5:4 G5:4 E5:6 G5:2",
        "A5:4 C6:4 E6:6 D6:2",
        "D6:4 A5:4 F#5:8",
        "E6:4 C6:4 G5:6 A5:2",
        "F#6:4 D6:4 A5:6 C6:2",
        "D6:4 B5:4 F#5:6 A5:2",
        "G5:4 B5:4 E6:6 D6:2",
        "C6:4 A5:4 E5:6 G5:2",
        "F#5:4 A5:4 D6:8",
        "D6:4 B5:4 G5:8",
        "G5:4 D5:4 G4:4 -:4",
    ],
}

JINGLES = {
    # Three, two, one: and off, like everybody else at a green light.
    "ready": {"fps": 3, "chart": ["C", "G"], "lead": [
        "C5:4 -:4 C5:4 -:4",
        "G5:4 -:4 B5:2 D6:2 G6:4",
    ]},
    # The melons going aboard, one bounce at a time.
    "load": {"fps": 3, "chart": ["F", "C", "F", "F"], "lead": [
        "F5:2 A5:2 C6:2 A5:2 F5:2 A5:2 C6:2 F6:2",
        "E5:2 G5:2 C6:2 G5:2 E5:2 G5:2 C6:2 E6:2",
        "F5:2 A5:2 C6:2 F6:2 A6:2 F6:2 C6:2 A5:2",
        "F6:4 C6:2 A5:2 F5:4 -:4",
    ]},
    # Aboard the ferry, rocking on the swell.
    "ferry": {"fps": 5, "chart": ["C", "G", "F", "C", "F", "C", "G", "C"], "lead": [
        "E5:4 G5:4 C6:6 B5:2",
        "D5:4 G5:4 B5:6 A5:2",
        "C5:4 F5:4 A5:6 G5:2",
        "E5:4 G5:4 C6:8",
        "F5:4 A5:4 C6:6 A5:2",
        "G5:4 E5:4 C5:6 E5:2",
        "D5:4 G5:4 B5:4 D6:4",
        "C6:4 G5:4 C5:4 -:4",
    ]},
    "clear": {"fps": 3, "chart": ["F", "C", "F"], "lead": [
        "C5:2 F5:2 A5:2 C6:2 F6:4 C6:4",
        "E6:2 C6:2 G5:2 E5:2 G5:2 C6:2 E6:4",
        "F6:8 C6:4 -:4",
    ]},
    # The tragic ending of a sceneggiata: over-acted, on purpose.
    "gameover": {"fps": 6, "chart": ["Am", "Bb", "E7", "Am"], "lead": [
        "E5:6 C5:2 A4:8",
        "F5:6 D5:2 Bb4:8",
        "E5:4 D5:4 B4:2 G#4:2 E4:4",
        "A4:8 -:8",
    ]},
    "ending": {"fps": 4, "chart": ["C", "F", "G", "C", "Am", "F", "G", "C"], "lead": [
        "G4:2 C5:2 E5:2 G5:2 C6:4 G5:4",
        "A5:2 C6:2 F6:4 C6:2 A5:2 F5:4",
        "G5:2 B5:2 D6:4 G6:2 D6:2 B5:4",
        "C6:2 E6:2 G6:4 E6:2 C6:2 G5:4",
        "A5:2 C6:2 E6:4 C6:2 A5:2 E5:4",
        "F5:2 A5:2 C6:4 F6:2 C6:2 A5:4",
        "G5:2 B5:2 D6:2 F6:2 G6:4 B5:4",
        "C6:8 G5:4 -:4",
    ]},
}

ALL_SONGS = {"title": TITLE, "lungomare": LUNGOMARE, "ischia": ISCHIA, "strada": STRADA, "tramonto": TRAMONTO, **JINGLES}


def chord_tone_check(name: str, song: dict) -> list[str]:
    """The notes on beats 1 and 3 must belong to the chord: a checked rule of the style."""
    problems = []
    for bar, (chart, line) in enumerate(zip(song["chart"], song["lead"])):
        root, quality = CHORDS[chart]
        allowed = {(root + t) % 12 for t in TONES[quality]}
        steps = melody(line)
        for strong in (0, 8):
            note = steps[strong]
            if note >= 12 and note % 12 not in allowed:
                problems.append(f"{name} bar {bar + 1} step {strong}: {note} not in {chart}")
    return problems


class Encoder:
    def __init__(self) -> None:
        self.patterns: list[tuple[int, ...]] = []

    def add(self, steps: list[int]) -> int:
        key = tuple(steps)
        if key not in self.patterns:
            self.patterns.append(key)
        return self.patterns.index(key)


# ---- accompaniment, derived from the chart by fixed rules --------------------------

def bass_pattern(variant: int, approach: int) -> list[int]:
    """Written on A, transposed with the chord. Variant 0 is the oom: root on beat 1,
    fifth on beat 3. Variant 1 walks: root, third, fifth, sixth. Both end on a
    chromatic step into the next bar's root, `approach` semitones from this one."""
    a = midi("A2")
    p = [HOLD] * STEPS
    if variant == 0:
        p[0], p[3], p[8], p[11] = a, OFF, a + 7, OFF
    else:
        p[0], p[4], p[8], p[11] = a, a + 3, a + 7, a + 9
    target = a + approach
    while target - a > 6:
        target -= 12
    while target - a < -6:
        target += 12
    p[14] = target - 1 if target > a else target + 1
    return p


def pah_pattern(tone: int, held: bool) -> list[int]:
    """The pah: an organ stab on every off-beat; or, for contrast, a chord held on
    beats 1 and 3. Written on A, transposed."""
    n = midi("A3") + tone
    p = [HOLD] * STEPS
    if held:
        p[0], p[7], p[8], p[15] = n, OFF, n, OFF
    else:
        for k in (2, 6, 10, 14):
            p[k], p[k + 1] = n, OFF
    return p


def arp_pattern(tones: tuple[int, ...], down: bool) -> list[int]:
    """Mandolin figure, sixteenths up the chord, or down it."""
    a = midi("A4")
    t = list(tones)[:3]
    seq = [t[0], t[1], t[2], t[0] + 12] if not down else [t[0] + 12, t[2], t[1], t[0]]
    return [a + v for v in seq * 4]


KICK, SNARE, HAT, CRASH = 40, 74, 88, 96


def drum_pattern(kind: int) -> list[int]:
    """The boom-chick of a drum machine bought at the local music shop in 1986.
    Kind 0 is the groove, 1 ends a phrase with a fill, 2 opens one with a crash."""
    p = [KICK, HOLD, HAT, HOLD, SNARE, HOLD, HAT, KICK, KICK, HOLD, HAT, HOLD, SNARE, HOLD, HAT, HAT]
    if kind == 1:
        p[10:] = [SNARE, HOLD, SNARE, SNARE, SNARE, SNARE]
    elif kind == 2:
        p[0] = CRASH
    return p


def transpose_for(root: int) -> int:
    t = (root - 9) % 12
    return t - 12 if t > 6 else t


def encode_song(enc: Encoder, song: dict, voices: list[str]) -> dict:
    orders: dict[str, list[tuple[int, int]]] = {v: [] for v in voices}
    leads = [melody(line, song.get("tremolo", False)) for line in song["lead"]]
    plain = [melody(line) for line in song["lead"]]
    bars = len(song["chart"])
    for bar, chart in enumerate(song["chart"]):
        root, quality = CHORDS[chart]
        t = transpose_for(root)
        tones = TONES[quality]
        nxt = CHORDS[song["chart"][(bar + 1) % bars]][0]
        # Sections: the second half answers the first with a different accompaniment.
        second = bars >= 8 and bar >= bars // 2
        phrase_end = bar % 4 == 3
        for v in voices:
            if v == "bass":
                orders[v].append((enc.add(bass_pattern(1 if second else 0, (nxt - root) % 12)), t))
            elif v == "organ_l":
                orders[v].append((enc.add(pah_pattern(tones[1], second and not phrase_end)), t))
            elif v == "organ_r":
                orders[v].append((enc.add(pah_pattern(tones[2], second and not phrase_end)), t))
            elif v == "lead":
                orders[v].append((enc.add(leads[bar]), 0))
            elif v == "arp":
                orders[v].append((enc.add(arp_pattern(tones, second)), t))
            elif v == "perc":
                kind = 1 if phrase_end and bars >= 4 else 2 if bar % 8 == 0 and bars >= 8 else 0
                orders[v].append((enc.add(drum_pattern(kind)), 0))
            elif v == "echo":
                prev = plain[bar - 1] if bar else [HOLD] * STEPS
                delayed = prev[-3:] + plain[bar][:-3]
                orders[v].append((enc.add([HOLD if n == OFF else n for n in delayed]), 0))
            elif v == "pad":
                orders[v].append((enc.add([midi("A3") + tones[0]] + [HOLD] * (STEPS - 1)), t))
    return orders


# Voice table: instrument, alternate instrument above `split`, how many consecutive
# instruments its notes cycle through, volume, pan, auto-pan swing.
VOICES = {
    "bass": ("bass", 0, 0, 1, 205, 2, 0),
    "organ_l": ("organ_l", 0, 0, 1, 150, -56, 0),
    "organ_r": ("organ_r", 0, 0, 1, 150, 56, 0),
    "lead": ("lead_a", 0, 0, 3, 178, 1, 14),
    "arp": ("mandolin", 0, 0, 1, 104, 1, 48),
    "perc": ("kick", "snare", 60, 1, 150, 1, 28),
    "echo": ("echo", 0, 0, 1, 124, 54, 0),
    "pad": ("pad", 0, 0, 1, 118, -50, 0),
}
GAME_VOICES = ["bass", "organ_l", "organ_r", "lead", "arp", "perc"]
TITLE_VOICES = GAME_VOICES + ["echo", "pad"]
JINGLE_VOICES = ["bass", "organ_l", "organ_r", "lead", "perc"]

# Effects: (instrument, note, frames) steps, played on the effect channel.
SFX = {
    "horn": [("sfx_horn", 79, 3), ("sfx_horn", 84, 5)],
    "bump": [("sfx_thud", 40, 2), ("sfx_thud", 34, 2)],
    "crash": [("sfx_crash", 44, 2), ("sfx_thud", 34, 2), ("sfx_crash", 38, 3)],
    "scrape": [("sfx_crash", 70, 1), ("sfx_crash", 76, 1)],
    "spill": [("sfx_zap", 76, 1), ("sfx_zap", 82, 1), ("sfx_zap", 88, 1), ("sfx_thud", 46, 1)],
    "recover": [("sfx_chime", 72, 1), ("sfx_chime", 76, 1), ("sfx_chime", 79, 2)],
    "stolen": [("sfx_zap", 79, 2), ("sfx_zap", 74, 2), ("sfx_zap", 67, 2), ("sfx_zap", 60, 3)],
    "deliver": [("sfx_chime", 67, 2), ("sfx_chime", 72, 2), ("sfx_chime", 76, 2), ("sfx_chime", 84, 4)],
    "food": [("sfx_chime", 79, 1), ("sfx_chime", 83, 1), ("sfx_chime", 86, 1), ("sfx_chime", 91, 3)],
    "ferry": [("sfx_boat", 43, 22), ("sfx_boat", 43, 3)],
    "tick": [("sfx_chime", 91, 1)],
    # One melon sold: the till's bell and the drawer.
    "sold": [("sfx_chime", 84, 1), ("sfx_chime", 91, 2), ("sfx_thud", 52, 1)],
    # Driven past a stall: the mellonaro's disappointed "eh!".
    "missed": [("sfx_horn", 67, 3), ("sfx_horn", 63, 5)],
    "menu": [("sfx_chime", 79, 1)],
}


def bytes_c(data, indent: str = "    ") -> str:
    data = list(data)
    return "\n".join(indent + ",".join(str(v) for v in data[i:i + 24]) + "," for i in range(0, len(data), 24))


def main() -> int:
    problems = []
    for name, song in ALL_SONGS.items():
        if len(song["chart"]) != len(song["lead"]):
            problems.append(f"{name}: chart and lead lengths differ")
        problems += chord_tone_check(name, song)
    if problems:
        print("\n".join(problems))
        return 1

    enc = Encoder()
    songs = [("TITLE", TITLE, TITLE_VOICES, True), ("LUNGOMARE", LUNGOMARE, GAME_VOICES, True),
             ("ISCHIA", ISCHIA, GAME_VOICES, True), ("STRADA", STRADA, GAME_VOICES, True),
             ("TRAMONTO", TRAMONTO, GAME_VOICES, True)]
    for name, song in JINGLES.items():
        songs.append((name.upper(), song, JINGLE_VOICES, False))

    blob: list[int] = []
    offsets: list[int] = []
    for name, song, voices, loop in songs:
        orders = encode_song(enc, song, voices)
        offsets.append(len(blob))
        bars = len(song["chart"])
        blob += [song["fps"], bars, len(voices), 1 if loop else 0]
        for v in voices:
            inst, alt, split, cycle, volume, pan, swing = VOICES[v]
            blob += [INST[inst], INST[alt] if alt else INST[inst], split, cycle, volume, pan & 255, swing]
            for pattern, transpose in orders[v]:
                blob += [pattern, transpose & 255]

    sfx_blob: list[int] = []
    sfx_offsets: list[int] = []
    for name, steps in SFX.items():
        sfx_offsets.append(len(sfx_blob))
        for inst, note, frames in steps:
            sfx_blob += [INST[inst], note, frames]
        sfx_blob.append(255)

    out = ["/* Generated by tools/build_audio.py. Do not edit: change the score. */"]
    for i, (name, *_rest) in enumerate(songs):
        out.append(f"#define SONG_{name} {i}")
    out.append(f"#define SONG_COUNT {len(songs)}\n#define MUSIC_STEPS {STEPS}\n#define MUSIC_HOLD {HOLD}\n#define MUSIC_OFF {OFF}")
    for i, name in enumerate(SFX):
        out.append(f"#define SFX_{name.upper()} {i}")
    out.append(f"#define SFX_COUNT {len(SFX)}")
    out.append(f"#define INST_ENGINE {INST['engine']}")
    flat = [b for p in enc.patterns for b in p]
    out.append(f"static const uint8_t music_patterns[{len(flat)}] = {{\n" + bytes_c(flat) + "\n};")
    out.append(f"static const uint16_t song_offsets[{len(offsets)}] = {{" + ",".join(map(str, offsets)) + "};")
    out.append(f"static const uint8_t song_data[{len(blob)}] = {{\n" + bytes_c(blob) + "\n};")
    out.append(f"static const uint8_t sfx_offsets[{len(sfx_offsets)}] = {{" + ",".join(map(str, sfx_offsets)) + "};")
    out.append(f"static const uint8_t sfx_data[{len(sfx_blob)}] = {{\n" + bytes_c(sfx_blob) + "\n};")
    (ROOT / "src/gen").mkdir(parents=True, exist_ok=True)
    (ROOT / "src/gen/music.inc").write_text("\n".join(out) + "\n", encoding="utf-8")

    instruments = []
    for name, wave, width, cutoff, res, a, d, s, r in INSTRUMENTS:
        instruments.append({"name": name, "sample_id": synth(wave, width, cutoff, res), "default_volume": 255,
                            "default_pan": 0, "attack": a, "decay": d, "sustain": s, "release": r})
    audio = {"samples": [], "instruments": instruments, "tracks": []}
    (ROOT / "audio").mkdir(exist_ok=True)
    (ROOT / "audio/audio.json").write_text(json.dumps(audio, indent=2) + "\n", encoding="utf-8")
    print(f"audio: {len(INSTRUMENTS)} instruments, {len(enc.patterns)} patterns ({len(flat)} B), "
          f"{len(songs)} songs ({len(blob)} B), {len(SFX)} effects ({len(sfx_blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
