/*
 * tr_music.h - the cartridge's sequencer and effects player.
 *
 * The classic pattern/order design of the 8-bit trackers: a pattern is one 4/4 bar
 * of 16 sixteenth notes, and for each voice a song lists one (pattern, transposition)
 * pair per bar. No PRG32 call is made directly: the includer defines TR_NOTE_ON and
 * TR_NOTE_OFF, so the host tests can log what would be played.
 *
 * The tempo is a whole number of 33 ms frames per step, so no step is ever
 * longer than another. Channel 6 is for effects and channel 7 for the engine, except
 * on the title, whose song uses all eight voices.
 *
 * Adapted from src/pz_music.h of You Have Got Pizza: Deluxe Edition (PRG32 family, MIT).
 */
#ifndef TR_MUSIC_H
#define TR_MUSIC_H

#include <stdint.h>

#define TR_SFX_CHANNEL 6
#define TR_ENGINE_CHANNEL 7
#define TR_MUSIC_VOICES 8
#define TR_VOICE_HEADER 7

typedef struct {
    const uint8_t *song;
    uint8_t playing, bars, voices, loop;
    uint8_t fps, tempo_cut;
    uint8_t bar, step, frames;
    uint8_t mute_mask;
    uint8_t note_count[TR_MUSIC_VOICES];
    int8_t swing[TR_MUSIC_VOICES];
    const uint8_t *sfx;
    uint8_t sfx_frames;
    int8_t sfx_pan;
    int8_t sfx_transpose;
    uint8_t finished;
} tr_music_t;

static void tr_music_silence(tr_music_t *m) {
    for (int v = 0; v < TR_MUSIC_VOICES; ++v) {
        if (m->playing && v < m->voices) TR_NOTE_OFF(v);
    }
}

/* Start a song; a voice in song_data[]: 7 header bytes, then bars * 2. */
static void tr_music_play(tr_music_t *m, int song) {
    tr_music_silence(m);
    const uint8_t *d = song_data + song_offsets[song];
    m->song = d;
    m->fps = d[0];
    m->bars = d[1];
    m->voices = d[2];
    m->loop = d[3];
    m->bar = 0;
    m->step = 0;
    m->frames = 1;
    m->playing = 1;
    m->finished = 0;
    m->tempo_cut = 0;
    m->mute_mask = 0;
    for (int v = 0; v < TR_MUSIC_VOICES; ++v) {
        m->note_count[v] = 0;
        m->swing[v] = 1;
    }
}

static void tr_music_stop(tr_music_t *m) {
    tr_music_silence(m);
    m->playing = 0;
}

static const uint8_t *tr_voice(const tr_music_t *m, int v) {
    return m->song + 4 + v * (TR_VOICE_HEADER + m->bars * 2);
}

static void tr_music_step(tr_music_t *m) {
    for (int v = 0; v < m->voices; ++v) {
        const uint8_t *h = tr_voice(m, v);
        const uint8_t *order = h + TR_VOICE_HEADER + m->bar * 2;
        uint8_t value = music_patterns[order[0] * MUSIC_STEPS + m->step];
        if ((m->mute_mask >> v) & 1u) {
            if (value >= 12 || value == MUSIC_OFF) TR_NOTE_OFF(v);
            continue;
        }
        if (v == TR_SFX_CHANNEL && m->sfx) continue;
        if (value == MUSIC_OFF) {
            TR_NOTE_OFF(v);
        } else if (value != MUSIC_HOLD) {
            int note = value;
            int instrument = h[0];
            if (h[2] && value >= h[2]) instrument = h[1];          /* drum split */
            if (h[2] == 0) note += (int8_t)order[1];                /* transposition */
            if (h[3] > 1) instrument += m->note_count[v] % h[3];    /* pulse-width sweep */
            m->note_count[v]++;
            int pan = (int8_t)h[5];
            if (h[6]) {                                             /* ping-pong */
                m->swing[v] = (int8_t)-m->swing[v];
                pan += m->swing[v] * (int)h[6];
            }
            TR_NOTE_ON(v, instrument, note, h[4], pan);
        }
    }
    if (++m->step >= MUSIC_STEPS) {
        m->step = 0;
        if (++m->bar >= m->bars) {
            m->bar = 0;
            if (!m->loop) {
                tr_music_stop(m);
                m->finished = 1;
            }
        }
    }
}

/* A new effect replaces the one sounding: the latest event is the one to hear. */
static void tr_sfx_play(tr_music_t *m, int sfx, int pan, int transpose) {
    m->sfx = sfx_data + sfx_offsets[sfx];
    m->sfx_frames = 1;
    m->sfx_pan = (int8_t)pan;
    m->sfx_transpose = (int8_t)transpose;
}

/* Call once per frame. */
static void tr_music_tick(tr_music_t *m) {
    if (m->playing && --m->frames == 0) {
        int fps = m->fps - m->tempo_cut;
        m->frames = (uint8_t)(fps < 2 ? 2 : fps);
        tr_music_step(m);
    }
    const uint8_t *s = m->sfx;
    if (s && --m->sfx_frames == 0) {
        if (s[0] == 255) {
            m->sfx = 0;
            return;
        }
        TR_NOTE_ON(TR_SFX_CHANNEL, s[0], s[1] + m->sfx_transpose, 230, m->sfx_pan);
        m->sfx_frames = s[2];
        m->sfx = s + 3;
    }
}

#endif
