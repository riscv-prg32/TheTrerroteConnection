/*
 * The Trerrote Connection - PRG32 portable cartridge.
 *
 * A tribute game for the myth of many generations, il Grande Maestro Tony Tammaro.
 * Unofficial: see README.md and docs/originality.md.
 *
 * The rules are in tr_core.h and the sequencer in tr_music.h. This file shows the
 * game. The renderer works one screen row at a time:
 *
 *   1. A row buffer in cartridge memory is filled with the row's background: a band
 *      of a view (run-length rows, decoded one at a time) or the road's spans.
 *   2. Every sprite crossing that row is scaled into the buffer, far to near.
 *   3. Text goes on top, and the part of the row that changed reaches the firmware as
 *      runs of one indexed colour (see send_row).
 *
 * So nothing is ever erased, and no full picture is held in the cartridge's 64 KiB.
 * Pixels sent to the display are what limits the frame rate on the ESP32-C6, so each
 * row tracks the span that changed, and the sky and the road are flushed separately: a
 * palm's top then travels as a small box, not as a band across the whole screen. Portable cartridges have no relocations: no pointer may appear
 * in initialised static data (tools/check_relocatable.py proves it).
 */
#include "prg32.h"
#include <stddef.h>

/* The cartridge is linked with -nostdlib; the compiler may still emit calls
 * to these two for structure copies and clears. */
#ifndef TR_HOST
void *memset(void *dst, int value, size_t n) __attribute__((optimize("no-tree-loop-distribute-patterns")));
void *memcpy(void *dst, const void *src, size_t n) __attribute__((optimize("no-tree-loop-distribute-patterns")));
void *memset(void *dst, int value, size_t n) {
    unsigned char *d = (unsigned char *)dst;
    while (n--) *d++ = (unsigned char)value;
    return dst;
}
void *memcpy(void *dst, const void *src, size_t n) {
    unsigned char *d = (unsigned char *)dst;
    const unsigned char *s = (const unsigned char *)src;
    while (n--) *d++ = *s++;
    return dst;
}
#endif

#define TR_NOTE_ON(ch, inst, note, vol, pan) \
    prg32_audio_note_on_pan((uint8_t)(ch), (uint8_t)(inst), (uint8_t)(note), (uint8_t)(vol), (int8_t)(pan))
#define TR_NOTE_OFF(ch) prg32_audio_note_off((uint8_t)(ch))

#include "gen/art.inc"
#include "gen/music.inc"
#include "tr_core.h"
#include "tr_music.h"

#define SCORE_GAME "TRERROTE"
#define TICK_MS 33u
#define MAX_CATCH_UP 3u
#define HORIZON 96
#define HUD_H 16
#define PARALLAX 24
#define MAX_SPRITES 44
#define MAX_ROW_RUNS 80
#define PALETTE_SIZE (FIXED_COUNT + VIEW_COLORS)
#define IDLE_TO_DEMO_TICKS 300
#define DEMO_TICKS 1200

enum {
    APP_TRIBUTE, APP_TITLE, APP_INTRO, APP_LOADING, APP_PLAY, APP_PAUSE, APP_FERRY, APP_CARD,
    APP_ENDING, APP_GAMEOVER
};
enum { LOWER_ROAD, LOWER_SEA, LOWER_SAND };
enum { TINT_NONE, TINT_RED, TINT_LEMON, TINT_WHITE, TINT_PURPLE, TINT_GREEN, TINT_PINK, TINT_CREAM, TINT_TAN };

typedef struct {
    int16_t x, y, w, h;
    uint16_t stepx, stepy;
    uint8_t id, tint;
    int8_t shear;       /* pixels of lean over the sprite's height, for a tilting load */
} spr_t;

static struct {
    uint8_t line[VIEW_W + 8];
    uint8_t src[256];
    uint16_t palette[PALETTE_SIZE];
    uint8_t cell[PALETTE_SIZE];     /* each colour's index on the framebuffer */
    prg32_indexed_sprite_t row;

    /* The text layer: one colour per line. */
    char text[25][41];
    uint8_t text_color[25];
    uint8_t text_big[25];
    uint8_t text_panel[25];

    spr_t cur[MAX_SPRITES], prev[MAX_SPRITES];
    int count, prev_count;
    uint8_t dirty[PRG32_GAME_H];      /* 0 clean, 1 whole row, 2 only rx0..rx1 */
    int16_t rx0[PRG32_GAME_H], rx1[PRG32_GAME_H];

    /* The road as computed for this frame: one entry per row. */
    int16_t center[TR_ROWS + 1];
    uint8_t width[TR_ROWS + 1], ground_l[TR_ROWS + 1], ground_r[TR_ROWS + 1], surface[TR_ROWS + 1];
    int32_t z_row[TR_ROWS + 1];
    int16_t unit[TR_ROWS + 1];
    /* The road as last sent, to know which part of each row has changed. */
    int16_t shown_left[TR_ROWS + 1], shown_right[TR_ROWS + 1];
    uint8_t shown_ground_l[TR_ROWS + 1], shown_ground_r[TR_ROWS + 1];

    uint8_t app, demo, view, view_shown, lower, hud;
    int16_t shift, shift_shown;
    int32_t road_pos_shown;
    int16_t road_x_shown;
    uint32_t app_tick, best;
    uint32_t last_input, last_ms, tick_accum, pending_pressed;
    uint8_t load_count, engine_timer, intro_level;

    uint32_t hud_seconds, hud_score;
    int hud_melons, hud_food, hud_bar, hud_msg, msg_timer, msg_shown;
    tr_music_t music;
} v;

static tr_game_t game;

/* ---- colours ------------------------------------------------------------ */

/* The same quantiser as the firmware (and tools/palette.py): the palette cell
 * that an RGB565 value will land in on the indexed framebuffer. */
static uint8_t cube_index(uint16_t color) {
    static const uint16_t named[8] = {0x0000, 0xffff, 0xf800, 0x07e0, 0x001f, 0xffe0, 0x07ff, 0xf81f};
    for (uint8_t i = 0; i < 8; ++i)
        if (color == named[i]) return i;
    unsigned r = ((color >> 11) & 31u) * 5u / 31u;
    unsigned g = ((color >> 5) & 63u) * 5u / 63u;
    unsigned b = (color & 31u) * 5u / 31u;
    return (uint8_t)(16u + r * 36u + g * 6u + b);
}

/* Row y has changed between x0 and x1. A row already marked whole stays whole. */
static void mark_span(int y, int x0, int x1) {
    if (y < 0 || y >= PRG32_GAME_H || v.dirty[y] == 1) return;
    if (x0 < 0) x0 = 0;
    if (x1 > PRG32_GAME_W) x1 = PRG32_GAME_W;
    if (x0 >= x1) return;
    if (v.dirty[y] == 0) {
        v.dirty[y] = 2;
        v.rx0[y] = (int16_t)x0;
        v.rx1[y] = (int16_t)x1;
    } else {
        if (x0 < v.rx0[y]) v.rx0[y] = (int16_t)x0;
        if (x1 > v.rx1[y]) v.rx1[y] = (int16_t)x1;
    }
}

static void dirty_all(void) {
    for (int y = 0; y < PRG32_GAME_H; ++y) v.dirty[y] = 1;
}

/* Every colour of a view becomes exact in its own palette cell. */
static void view_load(int n) {
    v.view = (uint8_t)n;
    v.view_shown = (uint8_t)n;
    for (int i = 0; i < FIXED_COUNT; ++i) v.palette[i] = fixed_palette[i];
    for (int i = 0; i < VIEW_COLORS; ++i) v.palette[FIXED_COUNT + i] = view_palette[n * VIEW_COLORS + i];
    for (int i = 0; i < PALETTE_SIZE; ++i) {
        v.cell[i] = cube_index(v.palette[i]);
        prg32_palette_set(v.cell[i], v.palette[i]);
    }
    dirty_all();
}

/* ---- the text layer --------------------------------------------------------- */

static void text_clear_line(int y) {
    int changed = v.text_big[y] || v.text_panel[y];
    for (int x = 0; x < 40; ++x) {
        if (v.text[y][x] != ' ') changed = 1;
        v.text[y][x] = ' ';
    }
    v.text_big[y] = 0;
    v.text_panel[y] = 0;
    if (changed) {
        int top = y * 8, bottom = top + 16;
        if (bottom > PRG32_GAME_H) bottom = PRG32_GAME_H;
        for (int r = top; r < bottom; ++r) v.dirty[r] = 1;
    }
}

static void text_clear(void) {
    for (int y = 0; y < 25; ++y) text_clear_line(y);
}

static int text_len(const char *s) {
    int n = 0;
    while (s[n]) ++n;
    return n;
}

static void text_at(int x, int y, const char *s, int color) {
    int whole = v.text_color[y] != color || v.text_big[y];
    v.text_color[y] = (uint8_t)color;
    for (; *s && x < 40; ++s, ++x) {
        if (x < 0 || v.text[y][x] == *s) continue;
        v.text[y][x] = *s;
        /* A changing clock should not cost a whole row. One pixel more for the shadow. */
        for (int r = 0; r < 8; ++r) mark_span(y * 8 + r, x * 8, x * 8 + 9);
    }
    if (whole) {
        int bottom = v.text_big[y] ? 16 : 8;
        for (int r = 0; r < bottom && y * 8 + r < PRG32_GAME_H; ++r) v.dirty[y * 8 + r] = 1;
    }
}

static void text_center(int y, const char *s, int color) {
    text_at((40 - text_len(s)) / 2, y, s, color);
}

/* A panel gives a line a solid background: reading comes first. */
static void text_panel(int y0, int y1) {
    for (int y = y0; y <= y1; ++y) {
        text_clear_line(y);
        v.text_panel[y] = 1;
        for (int r = 0; r < 8; ++r) v.dirty[y * 8 + r] = 1;
    }
}

/* Twice the size: 20 characters across, 16 pixels high. */
static void text_big(int y, const char *s, int color) {
    text_clear_line(y);
    v.text_big[y] = 1;
    text_at((20 - text_len(s)) / 2, y, s, color);
    for (int r = 0; r < 16; ++r) v.dirty[y * 8 + r] = 1;
}

static void number_text(char *out, uint32_t value, int digits) {
    for (int i = digits - 1; i >= 0; --i) {
        out[i] = (char)('0' + value % 10u);
        value /= 10u;
    }
    out[digits] = 0;
}

static void text_number(int x, int y, uint32_t value, int digits, int color) {
    char buffer[12];
    number_text(buffer, value, digits);
    text_at(x, y, buffer, color);
}

static const uint8_t *glyph_of(char c) {
    int k = (int)(unsigned char)c - 32;
    return font_bits + ((k < 0 || k >= 64) ? 0 : font_ascii[k]) * 8;
}

static void draw_text_row(uint8_t *line, int y) {
    int cy = y >> 3, row = y & 7;
    if (v.text_panel[cy]) {
        for (int x = 0; x < PRG32_GAME_W; ++x) line[x] = C_INK;
    }
    if (cy > 0 && v.text_big[cy - 1]) {
        cy -= 1;
        row += 8;
    }
    if (v.text_big[cy]) {
        int color = v.text_color[cy], gy = row >> 1, shadow = (row - 2) >> 1;
        for (int c = 0; c < 20; ++c) {
            char ch = v.text[cy][c];
            if (ch == ' ') continue;
            const uint8_t *g = glyph_of(ch);
            unsigned bits = g[gy], under = row >= 2 ? g[shadow] : 0;
            int left = c * 16;
            for (int k = 0; k < 8; ++k) {
                int px = left + k * 2;
                if ((under >> (7 - k)) & 1u) line[px + 2] = line[px + 3] = C_INK;
                if ((bits >> (7 - k)) & 1u) line[px] = line[px + 1] = (uint8_t)color;
            }
        }
        return;
    }
    int color = v.text_color[cy];
    int panel = v.text_panel[cy] || (v.hud && y < HUD_H);
    for (int c = 0; c < 40; ++c) {
        char ch = v.text[cy][c];
        if (ch == ' ') continue;
        const uint8_t *g = glyph_of(ch);
        unsigned bits = g[row], under = row > 0 ? g[row - 1] : 0;
        int left = c * 8;
        for (int k = 0; k < 8; ++k) {
            if (!panel && ((under >> (7 - k)) & 1u) && left + k + 1 < PRG32_GAME_W) line[left + k + 1] = C_INK;
            if ((bits >> (7 - k)) & 1u) line[left + k] = (uint8_t)color;
        }
    }
}

/* ---- sprites -------------------------------------------------------------- */

static void sprite_add(int id, int x, int y, int w, int h, int tint, int shear) {
    if (v.count == MAX_SPRITES || w < 1 || h < 1) return;
    if (x + w + 8 <= 0 || x - 8 >= PRG32_GAME_W || y >= PRG32_GAME_H || y + h <= 0) return;
    spr_t *s = &v.cur[v.count++];
    s->id = (uint8_t)id;
    s->x = (int16_t)x;
    s->y = (int16_t)y;
    s->w = (int16_t)w;
    s->h = (int16_t)h;
    s->stepx = (uint16_t)(((unsigned)spr_w[id] << 8) / (unsigned)w);
    s->stepy = (uint16_t)(((unsigned)spr_h[id] << 8) / (unsigned)h);
    s->tint = (uint8_t)tint;
    s->shear = (int8_t)shear;
}

/* A run-length row: (index << 3) | run, or run 0 and the run in the next byte. */
static void decode_row(const uint8_t *data, uint8_t *out, int width, int base) {
    int x = 0;
    while (x < width) {
        unsigned b = *data++;
        unsigned run = b & 7u;
        uint8_t value = (uint8_t)((b >> 3) + (unsigned)base);
        if (!run) run = *data++;
        while (run--) out[x++] = value;
    }
}

/* A view row: (index << 2) | run, 64 colours, or run 0 and the run in the next byte. */
static void decode_view_row(const uint8_t *data, uint8_t *out, int width, int base) {
    int x = 0;
    while (x < width) {
        unsigned b = *data++;
        unsigned run = b & 3u;
        uint8_t value = (uint8_t)((b >> 2) + (unsigned)base);
        if (!run) run = *data++;
        while (run--) out[x++] = value;
    }
}

static void tint_colors(int tint, uint8_t *a, uint8_t *b) {
    switch (tint) {
    case TINT_RED: *a = C_RED; *b = C_REDD; break;
    case TINT_LEMON: *a = C_LEMON; *b = C_ORANGE; break;
    case TINT_WHITE: *a = C_WHITE; *b = C_GREY; break;
    case TINT_PURPLE: *a = C_PURPLE; *b = C_NAVY; break;
    case TINT_GREEN: *a = C_MELON; *b = C_MELOND; break;
    case TINT_PINK: *a = C_PINK; *b = C_SKIND; break;
    case TINT_CREAM: *a = C_CREAM; *b = C_SAND2; break;
    case TINT_TAN: *a = C_SKIN; *b = C_TAN; break;
    default: *a = C_BLUE; *b = C_BLUED; break;
    }
}

static void blit_sprite_row(const spr_t *s, uint8_t *line, int y) {
    int id = s->id;
    int sy = ((y - s->y) * s->stepy) >> 8;
    if (sy >= spr_h[id]) sy = spr_h[id] - 1;
    decode_row(spr_data + spr_rows[spr_first[id] + sy], v.src, spr_w[id], 0);
    int x = s->x;
    if (s->shear) x += s->shear * (s->h - (y - s->y)) / s->h;
    int dx0 = 0, dx1 = s->w;
    if (x < 0) dx0 = -x;
    if (x + dx1 > PRG32_GAME_W) dx1 = PRG32_GAME_W - x;
    unsigned sx = (unsigned)dx0 * s->stepx;
    uint8_t a, b;
    tint_colors(s->tint, &a, &b);
    int tinted = s->tint != TINT_NONE;
    uint8_t *dst = line + x + dx0;
    for (int dx = dx0; dx < dx1; ++dx, sx += s->stepx) {
        uint8_t c = v.src[sx >> 8];
        if (c == SPR_TRANSPARENT) {
            ++dst;
            continue;
        }
        if (tinted) {
            if (c == C_BLUE) c = a;
            else if (c == C_BLUED) c = b;
        }
        *dst++ = c;
    }
}

/* ---- the road --------------------------------------------------------------- */

/* Each row of road is a slice at distance TR_ZK / row. Walking up the screen means
 * walking along the road: curve accumulates as a second difference, the classic
 * cheap way to bend a road with no 3D at all. */
static void road_compute(void) {
    uint32_t pos = (uint32_t)game.pos;
    int index = 0;
    tr_section_t s = tr_section_read(game.sec_first);
    int dx = 0, x = 0;
    for (int r = TR_ROWS; r >= 1; --r) {
        uint32_t seg = (pos + (uint32_t)v.z_row[r]) >> 8;
        while (index + 1 < game.sec_count && seg >= game.sec_start[index + 1]) {
            ++index;
            s = tr_section_read(game.sec_first + index);
        }
        dx += s.curve;
        x += dx;
        v.center[r] = (int16_t)(PRG32_GAME_W / 2 + (x >> 8) - ((game.x * v.unit[r]) >> 8));
        v.width[r] = s.width;
        v.ground_l[r] = s.ground_l;
        v.ground_r[r] = s.ground_r;
        v.surface[r] = s.surface;
    }
}

/* Flat, deliberately: bands of ground passing at speed would make every row change
 * from edge to edge, and the display cannot afford it. The road's own surface carries
 * the sense of speed. */
static uint8_t ground_color(int ground) {
    static const uint8_t colors[5] = {C_PAVE, C_SEA, C_SAND, C_GRASS, C_TUFF};
    return colors[ground];
}

static int road_half(int r) { return (v.unit[r] * v.width[r]) >> 4; }
static int road_kerb(int half) { return half / 12 + 1; }

static void fill(uint8_t *line, int x0, int x1, uint8_t color) {
    if (x0 < 0) x0 = 0;
    if (x1 > PRG32_GAME_W) x1 = PRG32_GAME_W;
    for (int x = x0; x < x1; ++x) line[x] = color;
}

/* Road units (+-256 at the edge of a full road) to a screen column on row r. */
static int road_x(int r, int units) { return v.center[r] + ((units * v.unit[r]) >> 8); }

static uint32_t seg_hash(uint32_t seg) { return (seg + 977u * game.level) * 2654435761u; }

/* No rumble strips: a kerb of grey stone, the street's own surface, its own marks.
 * Basoli are the basalt blocks of the old streets, laid in staggered courses. */
static void draw_road_row(uint8_t *line, int r) {
    uint32_t z = (uint32_t)game.pos + (uint32_t)v.z_row[r];
    uint32_t seg = z >> 8;
    int center = v.center[r];
    int half = road_half(r);
    int kerb = road_kerb(half);
    int ground_l = v.ground_l[r], ground_r = v.ground_r[r];
    fill(line, 0, center - half - kerb, ground_color(ground_l));
    fill(line, center + half + kerb, PRG32_GAME_W, ground_color(ground_r));
    /* A kerb only where there is a pavement or a wall; elsewhere the tarmac just ends. */
    uint8_t kl = ground_l == GROUND_PAVE || ground_l == GROUND_TUFF ? C_KERB : C_KERBD;
    uint8_t kr = ground_r == GROUND_PAVE || ground_r == GROUND_TUFF ? C_KERB : C_KERBD;
    fill(line, center - half - kerb, center - half, kl);
    fill(line, center + half, center + half + kerb, kr);
    int edge = 256 * v.width[r] / 16;
    int surface = v.surface[r];
    if (surface == SURFACE_BASOLI) {
        fill(line, center - half, center + half, C_BASALT);
        if (((z >> 6) & 3u) == 0) {
            fill(line, center - half, center + half, C_JOINT);       /* the course's joint */
        } else if (v.unit[r] > 20) {
            int offset = (seg & 1u) ? 40 : 0;
            for (int u = -edge + offset + 40; u < edge; u += 80) {
                int x = road_x(r, u);
                fill(line, x, x + 1 + (v.unit[r] >> 7), C_JOINT);
            }
        }
        return;
    }
    fill(line, center - half, center + half, C_ROAD);
    int mark = half / 48 + 1;
    if (surface == SURFACE_WORN) {
        /* Patched and patched again: a rectangle of darker tarmac on some segments. */
        uint32_t h = seg_hash(seg >> 1);
        if (((h >> 28) & 3u) == 0) {
            int u0 = (int)((h >> 8) & 255u) * 2 * edge / 255 - edge, u1 = u0 + 50 + (int)((h >> 16) & 63u);
            if (u1 > edge) u1 = edge;
            fill(line, road_x(r, u0), road_x(r, u1), C_PATCH);
        }
        if (((z >> 10) & 1u) && ((h >> 20) & 3u)) fill(line, center - mark, center + mark, C_LINE);
        return;
    }
    /* Clean asphalt: a dashed centre line, continuous edge lines, and in town the
     * zebra crossings that nobody stops at. */
    int town = ground_l == GROUND_PAVE || ground_r == GROUND_PAVE;
    if (town && (seg % 140u) < 3u) {
        for (int u = -edge + 16; u < edge - 16; u += 64) fill(line, road_x(r, u), road_x(r, u + 32), C_LINE);
        return;
    }
    if (((z >> 10) & 1u)) fill(line, center - mark, center + mark, C_LINE);
    int edge_mark = half / 64 + 1;
    fill(line, center - half + edge_mark, center - half + 2 * edge_mark, C_LINE);
    fill(line, center + half - 2 * edge_mark, center + half - edge_mark, C_LINE);
}

/* Road-space position to sprite: `world_w` and `world_h` are its size in screen
 * pixels at the player's row. */
static void place(int id, int z_ahead, int x, int lift, int world_w, int world_h, int tint) {
    if (z_ahead < 8) return;
    int r = (TR_ZK << 8) / z_ahead;
    if (r < 2) return;
    if (r > TR_ROWS) {
        if (r > TR_ROWS + 40) return;
        r = TR_ROWS;
    }
    int w = world_w * r / TR_PLAYER_ROW, h = world_h * r / TR_PLAYER_ROW;
    int cx = v.center[r] + ((x * v.unit[r]) >> 8);
    int y = HORIZON + r - h - (lift * r) / TR_PLAYER_ROW;
    sprite_add(id, cx - w / 2, y, w, h, tint, 0);
}

static void deco_add(int deco, uint32_t seg, int z, int side, int width) {
    int edge = 256 * width / 16;
    switch (deco) {
    case DECO_PALM: place(SPR_PALM, z, side * (edge + 66), 0, 120, 216, 0); break;
    case DECO_PINE: place(SPR_PINE, z, side * (edge + 190), 0, 196, 208, 0); break;
    case DECO_LAMP: place(SPR_LAMP, z, side * (edge + 28), 0, 48, 170, 0); break;
    case DECO_HOUSE:
        place((seg / 7u) & 1u ? SPR_HOUSE2 : SPR_HOUSE, z, side * (edge + 150), 0, 168, 224,
              (seg / 5u) % 3u ? TINT_PINK + (seg / 5u) % 4u : TINT_NONE);
        break;
    case DECO_UMBRELLA: place(SPR_UMBRELLA, z, side * (edge + 100 + (int)(seg % 40u)), 0, 92, 100, TINT_NONE); break;
    case DECO_SHRINE: place(SPR_SHRINE, z, side * (edge + 46), 30, 64, 100, 0); break;
    case DECO_BINS: place(SPR_BINS, z, side * (edge + 70), 0, 116, 72, 0); break;
    case DECO_WASHING: place(SPR_WASHING, z, 0, 150, 2 * edge * 154 / 256 + 60, 38, 0); break;
    case DECO_PARKED: {
        static const uint8_t tints[4] = {TINT_RED, TINT_WHITE, TINT_GREEN, TINT_NONE};
        place(SPR_CAR, z, side * (edge + 46), 0, 72, 50, tints[(seg >> 2) & 3u]);
        break;
    }
    default: break;
    }
}

/* Near objects first while the list has room, then sorted back to front. */
static void sort_far_to_near(int first) {
    /* Insertion sort on the bottom edge: a farther object has a higher bottom. */
    for (int i = first + 1; i < v.count; ++i) {
        spr_t tmp = v.cur[i];
        int bottom = tmp.y + tmp.h, k = i - 1;
        while (k >= first && v.cur[k].y + v.cur[k].h > bottom) {
            v.cur[k + 1] = v.cur[k];
            --k;
        }
        v.cur[k + 1] = tmp;
    }
}

static void add_player(void) {
    int bob = game.bump ? -((game.bump >> 1) & 3) : ((game.spd > 10 && (v.app_tick & 2u)) ? -1 : 0);
    int lean = game.steer * 3 + (game.curve_now > 2 ? -2 : game.curve_now < -2 ? 2 : 0);
    int wobble = game.slosh > 120 ? (((v.app_tick >> 1) & 1u) ? 3 : -3) : 0;
    int x = PRG32_GAME_W / 2 - 30, y = HORIZON + TR_PLAYER_ROW - 48 + bob;
    sprite_add(SPR_APE, x, y, 60, 48, 0, lean);
    /* The load, layer on layer: what is left of it can be counted. */
    static const int8_t px[12] = {4, 14, 24, 34, 44, 9, 19, 29, 39, 14, 24, 34};
    static const int8_t py[12] = {21, 21, 21, 21, 21, 13, 13, 13, 13, 5, 5, 5};
    int shown = (game.melons + 1) / 2;
    if (shown > 12) shown = 12;
    for (int i = 0; i < shown; ++i)
        sprite_add(SPR_MELON, x + px[i] + (lean * (48 - py[i])) / 48 + (i >= 5 ? wobble : 0), y + py[i], 12, 11, 0, 0);
}

static void build_road_sprites(void) {
    uint32_t base = (uint32_t)game.pos >> 8;
    int first = v.count;
    /* No banner across the road: the white sign where the town begins. */
    int sign_z = ((int)game.length << 8) - game.pos;
    if (sign_z > 40 && sign_z < TR_DRAW_SEGS << 8) {
        int id = SPR_SIGN0 + game.level;
        tr_section_t s = tr_section_at(&game, game.length - 1u);
        place(id, sign_z, tr_edge(s.width) + 30 + spr_w[id], 0, spr_w[id] * 12 / 5, 82, 0);
    }
    /* Traffic. */
    for (int i = 0; i < TR_MAX_CARS; ++i) {
        const tr_car_t *c = &game.cars[i];
        int z = c->z - game.pos;
        if (c->kind == CAR_NONE || z < 40 || z > TR_DRAW_SEGS << 8) continue;
        static const uint8_t car_tint[4] = {TINT_RED, TINT_WHITE, TINT_GREEN, TINT_NONE};
        static const uint8_t tam_tint[4] = {TINT_LEMON, TINT_PURPLE, TINT_RED, TINT_LEMON};
        if (c->kind == CAR_PLAIN) place(SPR_CAR, z, c->x, 0, 72, 50, car_tint[c->tint & 3u]);
        else if (c->kind == CAR_TAMARRO) place(SPR_TAMARRO, z, c->x, 0, 76, 53, tam_tint[c->tint & 3u]);
        else if (c->kind == CAR_TRUCK) place(SPR_TRUCK, z, c->x, 0, 122, 127, 0);
        else if (c->kind == CAR_PARKED)
            place((v.app_tick >> 3) & 1u ? SPR_CAR_HAZARD : SPR_CAR, z, c->x, 0, 72, 50, car_tint[c->tint & 3u]);
        else place(SPR_SCOOTER, z, c->x, 0, 36, 56, tam_tint[c->tint & 3u]);
    }
    /* Melons on the road, and those who want them. */
    for (int i = 0; i < TR_MAX_LOOSE; ++i) {
        const tr_loose_t *m = &game.loose[i];
        if (m->state != MELON_FREE) place(SPR_MELON, m->z - game.pos, m->x, m->h >> 3, 22, 20, 0);
    }
    for (int i = 0; i < TR_MAX_THIEVES; ++i) {
        const tr_thief_t *t = &game.thieves[i];
        if (t->state == THIEF_FREE) continue;
        static const uint8_t thief_tint[4] = {TINT_NONE, TINT_RED, TINT_LEMON, TINT_PURPLE};
        place((t->anim >> 2) & 1u ? SPR_PERSON1 : SPR_PERSON0, t->z - game.pos, t->x, 0, 28, 54, thief_tint[t->tint & 3u]);
        if (t->carrying) place(SPR_MELON, t->z - game.pos, t->x, 56, 22, 20, 0);
    }
    /* Stalls, and the next food on the road. */
    for (int i = 0; i < game.anchor_count; ++i) {
        const uint8_t *a = anchor_data + (game.anchor_first + i) * 4;
        int z = (((int)a[1] | ((int)a[2] << 8)) << 8) - game.pos;
        if (z < 40 || z > TR_DRAW_SEGS << 8) continue;
        int where = (int8_t)a[3];
        if (a[0] == ANCHOR_STALL) {
            tr_section_t s = tr_section_at(&game, (uint32_t)((game.pos + z) >> 8));
            place(SPR_STAND, z, where * (tr_edge(s.width) + 80), 0, 144, 118, 0);
        } else if (!((game.anchor_taken >> i) & 1u) && game.food_next < TR_FOODS) {
            place(SPR_FOOD0 + game.food_next, z, where, 6 + (int)((v.app_tick >> 3) & 3u), 36, 36, 0);
        }
    }
    /* At the end of the journey Patrizia waits by the road, waving. */
    if (game.level == LEVEL_COUNT - 1) {
        int z = ((int)game.length << 8) - game.pos;
        tr_section_t s = tr_section_at(&game, game.length - 1u);
        if (z >= 40 && z <= TR_DRAW_SEGS << 8)
            place(SPR_PATRIZIA, z, tr_edge(s.width) + 40, (int)((v.app_tick >> 3) & 1u) * 4, 40, 58, 0);
    }
    /* Potholes and the roadside, walking away from the camera. */
    int sec = tr_section_index(&game, base);
    tr_section_t s = tr_section_read(game.sec_first + sec);
    for (uint32_t k = 0; k < TR_DRAW_SEGS; ++k) {
        uint32_t seg = base + k;
        while (sec + 1 < game.sec_count && seg >= game.sec_start[sec + 1]) {
            ++sec;
            s = tr_section_read(game.sec_first + sec);
        }
        int z = (int)(seg << 8) - game.pos;
        if (z < 96) continue;
        if (k < 40) {
            int hole = tr_pothole_x(&game, seg, s.holes, s.width);
            if (hole != -9999) place(SPR_POTHOLE, z, hole, 0, 92, 25, 0);
        }
        if (seg % s.period == 0) {
            if (s.deco_l) deco_add(s.deco_l, seg, z, -1, s.width);
            if (s.deco_r && s.deco_r != DECO_WASHING) deco_add(s.deco_r, seg + 3, z, 1, s.width);
            else if (s.deco_r == DECO_WASHING && s.deco_l != DECO_WASHING) deco_add(DECO_WASHING, seg, z, 1, s.width);
        }
    }
    sort_far_to_near(first);
    /* The Ape is at its fixed row: anything nearer the camera is drawn after it. */
    int nearer = v.count;
    for (int i = first; i < v.count; ++i) {
        if (v.cur[i].y + v.cur[i].h > HORIZON + TR_PLAYER_ROW) {
            nearer = i;
            break;
        }
    }
    int moved = v.count - nearer;
    if (moved > 0 && moved <= 12) {
        spr_t tail[12];
        for (int i = 0; i < moved; ++i) tail[i] = v.cur[nearer + i];
        v.count = nearer;
        add_player();
        for (int i = 0; i < moved; ++i) if (v.count < MAX_SPRITES) v.cur[v.count++] = tail[i];
    } else {
        add_player();
    }
}

/* ---- the row compositor ------------------------------------------------------ */

/* Hand a finished row to the firmware. Most rows are a few long runs of one colour,
 * and a rectangle fills its pixels with memset, where an 8-bit sprite goes through a
 * per-pixel loop and rebuilds its palette map first: on the ESP32-C6 that was the
 * largest cost of a frame. A very busy row (a skyline, say) is cheaper as a sprite. */
static void send_row(const uint8_t *line, int y, int x0, int x1) {
    int runs = 1;
    for (int x = x0 + 1; x < x1 && runs <= MAX_ROW_RUNS; ++x) runs += line[x] != line[x - 1];
    if (runs > MAX_ROW_RUNS) {
        v.row.pixels = line + x0;
        v.row.width = (uint16_t)(x1 - x0);
        prg32_sprite_draw_indexed(x0, y, &v.row, 0);
        return;
    }
    int x = x0;
    while (x < x1) {
        uint8_t color = line[x];
        int end = x + 1;
        while (end < x1 && line[end] == color) ++end;
        prg32_gfx_rect_indexed(x, y, end - x, 1, v.cell[color]);
        x = end;
    }
}

static void draw_row(int y, int x0, int x1) {
    uint8_t *line = v.line;
    if (y >= HORIZON) {
        int r = y - HORIZON + 1;
        if (v.lower == LOWER_ROAD) {
            draw_road_row(line, r);
        } else if (v.lower == LOWER_SEA) {
            uint8_t c = ((y + (int)(v.app_tick >> 3)) >> 2) & 1u ? C_SEA : C_SEA2;
            fill(line, 0, PRG32_GAME_W, c);
        } else {
            fill(line, 0, PRG32_GAME_W, y & 8 ? C_SAND : C_SAND2);
        }
    } else if (v.hud && y < HUD_H) {
        /* The delivery note: cream paper, a ruled line under it. */
        fill(line, 0, PRG32_GAME_W, y == HUD_H - 1 ? C_KERBD : C_CREAM);
    } else {
        int row = y - HUD_H;
        if (row < 0) row = 0;
        decode_view_row(view_data + view_rows[v.view * VIEW_H + row], line, VIEW_W, FIXED_COUNT);
        line += PARALLAX + v.shift;
    }
    for (int i = 0; i < v.count; ++i) {
        const spr_t *s = &v.cur[i];
        /* Trees stop at the HUD band; only the HUD's own 8 x 8 icons live there. */
        if (y >= s->y && y < s->y + s->h && (!v.hud || y >= HUD_H || s->h == 8)) blit_sprite_row(s, line, y);
    }
    draw_text_row(line, y);
    send_row(line, y, x0, x1);
}

static void mark_sprite(const spr_t *s) {
    int y0 = s->y < 0 ? 0 : s->y, y1 = s->y + s->h;
    if (y1 > PRG32_GAME_H) y1 = PRG32_GAME_H;
    int lean = s->shear < 0 ? -s->shear : s->shear;
    for (int y = y0; y < y1; ++y) mark_span(y, s->x - lean, s->x + s->w + lean);
}

static void render(void) {
    int n = v.count > v.prev_count ? v.count : v.prev_count;
    for (int i = 0; i < n; ++i) {
        if (i < v.count && i < v.prev_count) {
            const spr_t *a = &v.cur[i], *b = &v.prev[i];
            if (a->id == b->id && a->x == b->x && a->y == b->y && a->w == b->w && a->h == b->h &&
                a->tint == b->tint && a->shear == b->shear) continue;
        }
        if (i < v.count) mark_sprite(&v.cur[i]);
        if (i < v.prev_count) mark_sprite(&v.prev[i]);
    }
    if (v.shift != v.shift_shown) {
        v.shift_shown = v.shift;
        for (int y = v.hud ? HUD_H : 0; y < HORIZON; ++y) v.dirty[y] = 1;
    }
    if (v.lower == LOWER_ROAD && (game.pos != v.road_pos_shown || game.x != v.road_x_shown)) {
        v.road_pos_shown = game.pos;
        v.road_x_shown = game.x;
        for (int r = 1; r <= TR_ROWS; ++r) {
            int half = road_half(r), reach = half + road_kerb(half) + 1;
            int left = v.center[r] - reach, right = v.center[r] + reach;
            int y = HORIZON + r - 1;
            if (v.ground_l[r] != v.shown_ground_l[r] || v.ground_r[r] != v.shown_ground_r[r]) v.dirty[y] = 1;
            mark_span(y, left < v.shown_left[r] ? left : v.shown_left[r], right > v.shown_right[r] ? right : v.shown_right[r]);
            v.shown_left[r] = (int16_t)left;
            v.shown_right[r] = (int16_t)right;
            v.shown_ground_l[r] = v.ground_l[r];
            v.shown_ground_r[r] = v.ground_r[r];
        }
    }
    int sent = 0;
    for (int y = 0; y < PRG32_GAME_H; ++y) {
        if (v.dirty[y]) {
            int whole = v.dirty[y] == 1;
            draw_row(y, whole ? 0 : v.rx0[y], whole ? PRG32_GAME_W : v.rx1[y]);
            v.dirty[y] = 0;
            sent = 1;
        }
        /* Two boxes, no more: on the board a present costs milliseconds before its
         * first pixel, and 13 bands a frame measured 5 fps (docs/graphics.md). */
        if (sent && y == HORIZON - 1) {
            prg32_gfx_present();
            sent = 0;
        }
    }
    for (int i = 0; i < v.count; ++i) v.prev[i] = v.cur[i];
    v.prev_count = v.count;
}

/* ---- HUD ----------------------------------------------------------------------- */

static void hud_reset(void) {
    text_at(0, 0, "TEMPO", C_INK);
    text_at(13, 0, "MELLONI", C_INK);
    text_at(25, 0, "INCASSO", C_INK);
    v.hud_seconds = 0xFFFFFFFFu;
    v.hud_score = 0xFFFFFFFFu;
    v.hud_melons = -1;
    v.hud_food = -1;
    v.hud_bar = -1;
    v.hud_msg = -1;
    v.msg_timer = 0;
    v.msg_shown = -1;
}

enum { MSG_NONE, MSG_STALL_LEFT, MSG_STALL_RIGHT, MSG_SELLING, MSG_SOLD, MSG_MISSED, MSG_PARKED };

/* One line of advice under the note, in the sky: what the street wants of you now. */
static void hud_message(void) {
    int msg = MSG_NONE;
    if (v.msg_timer) {
        v.msg_timer--;
        msg = v.hud_msg;
    } else if (game.phase == PH_PLAY && game.melons) {
        int d = 0, stall = tr_next_stall(&game, &d);
        if (game.stall_now >= 0) {
            msg = MSG_SELLING;
        } else if (stall >= 0 && d <= 45 && d >= -TR_STALL_AFTER) {
            msg = (int8_t)anchor_data[(game.anchor_first + stall) * 4 + 3] < 0 ? MSG_STALL_LEFT : MSG_STALL_RIGHT;
        }
    }
    int key = msg * 16 + (msg == MSG_SELLING ? game.stall_given : 0);
    if (key == v.msg_shown) return;
    v.msg_shown = key;
    char sold[24] = "VENDUTI 0 DI 4";
    switch (msg) {
    case MSG_STALL_LEFT: text_center(3, "BANCARELLA A SINISTRA: FERMATI", C_LEMON); break;
    case MSG_STALL_RIGHT: text_center(3, "BANCARELLA A DESTRA: FERMATI", C_LEMON); break;
    case MSG_SELLING:
        sold[8] = (char)('0' + game.stall_given);
        sold[13] = (char)('0' + TR_DELIVERY);
        text_center(3, "                              ", C_CREAM);
        text_center(3, sold, C_CREAM);
        break;
    case MSG_SOLD: text_center(3, "GRAZIE, A LA PROSSIMA!", C_CREAM); break;
    case MSG_MISSED: text_center(3, "BANCARELLA PERSA!", C_LEMON); break;
    case MSG_PARKED: text_center(3, "CHI HA PARCHEGGIATO QUA?", C_CREAM); break;
    default: text_clear_line(3); break;
    }
}

static void hud_say(int msg, int ticks) {
    v.hud_msg = msg;
    v.msg_timer = ticks;
    v.msg_shown = -1;
    text_clear_line(3);
}

static void hud_update(void) {
    uint32_t left = game.ticks < game.time_limit ? (game.time_limit - game.ticks + TR_TICKS_PER_SEC - 1) / TR_TICKS_PER_SEC : 0;
    if (left != v.hud_seconds) {
        v.hud_seconds = left;
        char clock[6];
        clock[0] = (char)('0' + left / 60u % 10u);
        clock[1] = ':';
        clock[2] = (char)('0' + left % 60u / 10u);
        clock[3] = (char)('0' + left % 10u);
        clock[4] = 0;
        text_at(6, 0, clock, C_INK);
    }
    if (game.melons != v.hud_melons) {
        v.hud_melons = game.melons;
        text_number(21, 0, game.melons, 2, C_INK);
    }
    if (game.score != v.hud_score) {
        v.hud_score = game.score;
        text_number(33, 0, game.score, 6, C_INK);
    }
    /* The second line: the route, a little Ape along it, and where it goes. */
    int bar = (int)((game.pos >> 8) * 11 / game.length);
    if (bar > 10) bar = 10;
    if (bar != v.hud_bar) {
        v.hud_bar = bar;
        char route[12];
        for (int i = 0; i < 11; ++i) route[i] = i == bar ? 'A' : i < bar ? '-' : '.';
        route[11] = 0;
        text_at(13, 1, route, C_INK);
    }
    hud_message();
}

static void hud_sprites(void) {
    /* Patrizia's shopping list, left of the route. */
    for (int i = 0; i < TR_FOODS; ++i)
        if (i < game.food_next) sprite_add(SPR_FOOD0 + i, 1 + i * 10, 8, 8, 8, 0, 0);
}

static void hud_names(void) {
    char dest[17];
    const uint8_t *n = level_names + (unsigned)game.level * 32u + 16u;
    for (int i = 0; i < 16; ++i) dest[i] = (char)n[i];
    dest[16] = 0;
    text_at(25, 1, dest, C_INK);
}

/* ---- screens and flow ------------------------------------------------------------ */

static void clear_sprites(void) { v.count = 0; }

static void read_best(void) {
    prg32_score_t s;
    if (prg32_score_count(SCORE_GAME) > 0 && prg32_score_get(SCORE_GAME, 0, &s) == 0) v.best = s.score;
}

static void engine_silence(void) {
    prg32_audio_note_off(TR_ENGINE_CHANNEL);
    v.engine_timer = 0;
}

static void set_app(int app) {
    v.app = (uint8_t)app;
    v.app_tick = 0;
}

static void tribute_screen(void) {
    set_app(APP_TRIBUTE);
    v.demo = 0;
    v.hud = 0;
    v.lower = LOWER_SAND;
    v.shift = 0;
    view_load(VIEW_BAIA);
    text_clear();
    clear_sprites();
    text_panel(11, 24);
    text_center(1, "UN OMAGGIO A", C_CREAM);
    text_big(3, "IL GRANDE MAESTRO", C_LEMON);
    text_big(6, "TONY TAMMARO", C_CREAM);
    text_center(12, "MITO DI MOLTE GENERAZIONI", C_LEMON);
    text_center(14, "A TRIBUTE GAME TO THE MYTH", C_CREAM);
    text_center(15, "OF MANY GENERATIONS", C_CREAM);
    text_center(17, "GIOCO TRIBUTO NON UFFICIALE", C_CREAM);
    text_center(18, "CON TUTTO L'AFFETTO DEI FAN", C_CREAM);
    text_center(19, "NON CONTIENE SUE MUSICHE O TESTI:", C_CREAM);
    text_center(20, "COLONNA SONORA ORIGINALE", C_CREAM);
    text_center(22, "TONYTAMMARO.COM", C_LEMON);
    tr_music_play(&v.music, SONG_TITLE);
    prg32_band_set_game_info("TRIBUTE TO TONY TAMMARO");
}

static void title_screen(void) {
    set_app(APP_TITLE);
    v.demo = 0;
    v.hud = 0;
    v.lower = LOWER_ROAD;
    v.shift = 0;
    read_best();
    tr_new_game(&game, 0, 1);
    game.melons = TR_MELONS_FULL;
    game.spd = 60;
    view_load(VIEW_VILLA);
    text_clear();
    text_big(0, "THE TRERROTE", C_LEMON);
    text_big(2, "CONNECTION", C_CREAM);
    text_center(5, "OMAGGIO A TONY TAMMARO", C_CREAM);
    text_panel(24, 24);
    text_at(1, 24, "RECORD", C_CREAM);
    text_number(8, 24, v.best, 6, C_CREAM);
    text_at(27, 24, prg32_audio_get_mode() == PRG32_AUDIO_MODE_STEREO ? "STEREO 8 VOCI" : "MONO 8 VOCI", C_CREAM);
    /* Coming from the tribute screen, the anthem simply carries on. */
    if (!v.music.playing || v.music.song != song_data + song_offsets[SONG_TITLE]) tr_music_play(&v.music, SONG_TITLE);
    prg32_band_set_game_info("TRIBUTE TO TONY TAMMARO");
}

static void level_name_text(char *out, int level, int which) {
    const uint8_t *n = level_names + (unsigned)level * 32u + (which ? 16u : 0u);
    for (int i = 0; i < 16; ++i) out[i] = (char)n[i];
    out[16] = 0;
}

static void intro_screen(int level) {
    set_app(APP_INTRO);
    v.intro_level = (uint8_t)level;
    v.hud = 0;
    v.shift = 0;
    v.lower = level == 0 ? LOWER_SEA : LOWER_SAND;
    view_load(level_table[level][6]);
    text_clear();
    clear_sprites();
    char a[17], b[17];
    level_name_text(a, level, 0);
    level_name_text(b, level, 1);
    text_panel(13, 23);
    text_center(13, a, C_LEMON);
    text_center(14, "VERSO", C_CREAM);
    text_center(15, b, C_LEMON);
    switch (level) {
    case 0:
        text_center(17, "CORRI AL TRAGHETTO PER ISCHIA!", C_CREAM);
        text_center(18, "IL TRAFFICO NON TI ASPETTA", C_CREAM);
        break;
    case 1:
        text_center(17, "VICOLI STRETTI E TANTE CURVE:", C_CREAM);
        text_center(18, "PIANO O I MELLONI VOLANO VIA", C_CREAM);
        break;
    case 2:
        text_center(17, "FERMATI ALLE BANCARELLE E VENDI", C_CREAM);
        text_center(18, "ATTENTO A LA MONNEZZA DELLA GENTE", C_CREAM);
        break;
    case 3:
        text_center(17, "DALL'ASSE MEDIANO FINO AL MARE", C_CREAM);
        text_center(18, "I TAMARRI NON DANNO PRECEDENZA", C_CREAM);
        break;
    case 4:
        text_center(17, "BUCHE, TAMARRI E IL CAMION", C_CREAM);
        text_center(18, "DELLE MOZZARELLE", C_CREAM);
        break;
    default:
        text_center(17, "PATRIZIA HA FAME E ASPETTA", C_CREAM);
        text_center(18, "A BAIA DOMIZIA", C_CREAM);
        break;
    }
    text_center(20, "A: GAS  B: FRENO  SU: CLACSON", C_CREAM);
    if (level >= 2) text_center(21, "ALLA BANCARELLA: FERMO, DAL SUO LATO", C_CREAM);
    text_center(22, "PREMI A", C_LEMON);
}

static void play_screen(void) {
    set_app(APP_PLAY);
    v.hud = 1;
    v.lower = LOWER_ROAD;
    v.shift = 0;
    view_load(level_table[game.level][6]);
    text_clear();
    v.road_pos_shown = -1;
    hud_reset();
    hud_names();
    hud_update();
    text_center(11, "PRONTI...", C_LEMON);
    prg32_band_set_game_info("TRIBUTE TO TONY TAMMARO");
    tr_music_play(&v.music, SONG_READY);
}

static void start_level(int level, int fresh, uint32_t seed) {
    if (fresh) tr_new_game(&game, level, seed);
    else tr_load_level(&game, level);
    play_screen();
}

static void song_of_level(void) {
    static const uint8_t songs[4] = {SONG_LUNGOMARE, SONG_ISCHIA, SONG_STRADA, SONG_TRAMONTO};
    tr_music_play(&v.music, songs[level_table[game.level][9]]);
}

/* Ischia: the melons go aboard, in full view. */
static void loading_screen(void) {
    set_app(APP_LOADING);
    v.hud = 0;
    v.lower = LOWER_SAND;
    v.shift = 0;
    v.load_count = 0;
    view_load(VIEW_ISCHIA);
    text_clear();
    clear_sprites();
    text_panel(0, 1);
    text_center(0, "AD ISCHIA SI CARICA LA TRERROTE", C_LEMON);
    text_center(1, "24 MELLONI, UNO PER UNO", C_CREAM);
    tr_music_play(&v.music, SONG_LOAD);
}

static void ferry_screen(int destination_level) {
    set_app(APP_FERRY);
    v.hud = 0;
    v.lower = LOWER_SEA;
    v.shift = 0;
    view_load(level_table[destination_level][6]);
    text_clear();
    clear_sprites();
    text_panel(0, 1);
    text_center(0, "IN TRAGHETTO", C_LEMON);
    text_center(1, destination_level == 1 ? "DA NAPOLI A ISCHIA" : "DA ISCHIA A POZZUOLI", C_CREAM);
    tr_music_play(&v.music, SONG_FERRY);
    tr_sfx_play(&v.music, SFX_FERRY, 0, 0);
}

static void card_screen(void) {
    set_app(APP_CARD);
    text_panel(7, 16);
    char b[17];
    level_name_text(b, game.level, 1);
    text_center(8, b, C_LEMON);
    text_center(9, "BOLLA DI CONSEGNA", C_CREAM);
    text_at(9, 11, "INCASSO TAPPA", C_CREAM);
    text_number(25, 11, game.leg_score, 6, C_CREAM);
    text_at(9, 12, "MELLONI A BORDO", C_CREAM);
    text_number(25, 12, game.melons, 6, C_CREAM);
    text_at(9, 13, "RUBATI FINORA", C_CREAM);
    text_number(25, 13, game.stolen, 6, C_CREAM);
    text_center(15, "PREMI A", C_LEMON);
    tr_music_play(&v.music, SONG_CLEAR);
}

static void gameover_screen(const char *why) {
    set_app(APP_GAMEOVER);
    engine_silence();
    text_panel(7, 15);
    text_center(8, why, C_LEMON);
    text_center(10, "CHE SCENEGGIATA...", C_CREAM);
    text_at(11, 12, "INCASSO", C_CREAM);
    text_number(20, 12, game.score, 6, C_CREAM);
    text_center(14, "PREMI A", C_LEMON);
    tr_music_play(&v.music, SONG_GAMEOVER);
    if (!v.demo && game.score) {
        if (game.score > v.best) v.best = game.score;
        prg32_score_submit_current_player(SCORE_GAME, game.score);
    }
}

static void ending_screen(void) {
    set_app(APP_ENDING);
    engine_silence();
    v.hud = 0;
    v.lower = LOWER_SAND;
    v.shift = 0;
    view_load(VIEW_BAIA);
    text_clear();
    clear_sprites();
    /* What is left on the Ape goes to the beach bars: the last delivery. */
    tr_score(&game, (unsigned)game.melons * 200u);
    game.delivered = (uint8_t)(game.delivered + game.melons);
    game.melons = 0;
    if (game.food_next >= TR_FOODS) tr_score(&game, 5000);
    text_panel(0, 1);
    text_center(0, "BAIA DOMIZIA", C_LEMON);
    if (game.food_next >= TR_FOODS) {
        text_center(1, "PATRIZIA HA MANGIATO TUTTO!", C_CREAM);
    } else {
        text_center(1, "PATRIZIA HA ANCORA FAME...", C_CREAM);
    }
    text_panel(22, 24);
    text_at(5, 22, "MELLONI", C_CREAM);
    text_number(13, 22, game.delivered, 2, C_CREAM);
    text_at(19, 22, "INCASSO", C_CREAM);
    text_number(27, 22, game.score, 6, C_CREAM);
    text_center(23, "GRAZIE, MAESTRO!", C_LEMON);
    tr_music_play(&v.music, SONG_ENDING);
    if (!v.demo && game.score) {
        if (game.score > v.best) v.best = game.score;
        prg32_score_submit_current_player(SCORE_GAME, game.score);
    }
}

/* ---- pictures of the screens that are not the road -------------------------------- */

static void loading_sprites(void) {
    int y = 120;
    sprite_add(SPR_STAND, 26, y - 6, 120, 98, 0, 0);
    sprite_add(SPR_PERSON0 + ((v.app_tick >> 3) & 1u), 148, y + 26, 30, 56, TINT_RED, 0);
    int shown = (v.load_count + 1) / 2;
    int x = 186, top = y + 26;
    sprite_add(SPR_APE, x, top, 60, 48, 0, 0);
    static const int8_t px[12] = {4, 14, 24, 34, 44, 9, 19, 29, 39, 14, 24, 34};
    static const int8_t py[12] = {21, 21, 21, 21, 21, 13, 13, 13, 13, 5, 5, 5};
    for (int i = 0; i < shown && i < 12; ++i) sprite_add(SPR_MELON, x + px[i], top + py[i], 12, 11, 0, 0);
    /* The one on its way, thrown as is the custom. */
    int phase = (int)(v.app_tick & 7u);
    if (v.load_count < TR_MELONS_FULL)
        sprite_add(SPR_MELON, 158 + phase * 6, top + 6 - (phase * (8 - phase)) / 2, 12, 11, 0, 0);
}

static void ferry_sprites(void) {
    int x = (int)(v.app_tick / 2) - 96;
    int y = 96 + (((v.app_tick >> 4) & 1u) ? 1 : 0);
    sprite_add(SPR_FERRY, x, y, 192, 72, 0, 0);
    sprite_add(SPR_APE, x + 138, y + 42, 24, 20, 0, 0);
}

static void ending_sprites(void) {
    int bounce = (v.app_tick >> 3) & 1u;
    sprite_add(SPR_UMBRELLA, 186, 90, 84, 96, TINT_NONE, 0);
    sprite_add(SPR_PATRIZIA, 196, 118 - (game.food_next >= TR_FOODS ? bounce * 3 : 0), 48, 68, 0, 0);
    sprite_add(SPR_APE, 40, 128, 60, 48, 0, 0);
    /* The five foods on the sand, or the empty places of those she did not get. */
    for (int i = 0; i < game.food_next; ++i) sprite_add(SPR_FOOD0 + i, 110 + (i % 3) * 22, 136 + (i / 3) * 18, 16, 16, 0, 0);
}

/* ---- events: what the rules said happened ------------------------------------------- */

static int pan_of(int x) {
    int pan = x * 48 / 256;
    if (pan > 60) pan = 60;
    if (pan < -60) pan = -60;
    return pan == 0 ? 1 : pan;
}

static void handle_events(void) {
    for (int i = 0; i < game.event_count; ++i) {
        const tr_event_t *e = &game.events[i];
        int pan = pan_of(e->x);
        switch (e->type) {
        case EV_BUMP: tr_sfx_play(&v.music, SFX_BUMP, pan, 0); break;
        case EV_CRASH:
            tr_sfx_play(&v.music, SFX_CRASH, pan, 0);
            if (e->value == CAR_PARKED) hud_say(MSG_PARKED, 45);
            break;
        case EV_SCRAPE: tr_sfx_play(&v.music, SFX_SCRAPE, pan, 0); break;
        case EV_SPILL: tr_sfx_play(&v.music, SFX_SPILL, pan, 0); break;
        case EV_RECOVER: tr_sfx_play(&v.music, SFX_RECOVER, pan, 0); break;
        case EV_STOLEN: tr_sfx_play(&v.music, SFX_STOLEN, pan, 0); break;
        case EV_DELIVER:
            tr_sfx_play(&v.music, SFX_SOLD, pan, e->value & 7);
            if (e->value >= TR_DELIVERY || !game.melons) hud_say(MSG_SOLD, 60);
            break;
        case EV_MISSED:
            tr_sfx_play(&v.music, SFX_MISSED, pan, 0);
            hud_say(MSG_MISSED, 60);
            break;
        case EV_FOOD: tr_sfx_play(&v.music, SFX_FOOD, pan, 0); break;
        case EV_HORN: tr_sfx_play(&v.music, SFX_HORN, 1, 0); break;
        case EV_TIME_LOW:
            tr_sfx_play(&v.music, SFX_TICK, 1, 0);
            v.music.tempo_cut = 1;
            break;
        case EV_GO:
            text_clear_line(11);
            song_of_level();
            break;
        case EV_ARRIVE:
            text_center(11, "ARRIVATO!", C_LEMON);
            tr_sfx_play(&v.music, SFX_DELIVER, 1, 0);
            break;
        default: break;
        }
    }
}

/* A two-stroke sings by coughing: one short pulse note per firing, faster and higher
 * with speed. Channel 7 belongs to it during play. */
static void engine_tick(void) {
    if (v.engine_timer) {
        v.engine_timer--;
        return;
    }
    int spd = game.spd;
    v.engine_timer = (uint8_t)(spd > 100 ? 1 : spd > 40 ? 2 : 3);
    int note = 33 + spd / 11;
    prg32_audio_note_on_pan(TR_ENGINE_CHANNEL, INST_ENGINE, (uint8_t)note, (uint8_t)(120 + spd / 3), 1);
}

/* The horizon drifts against the bend, then settles back when the road straightens. */
static void parallax_tick(void) {
    if (v.app_tick & 3u) return;
    int want = game.curve_now && game.spd > 30 ? (game.curve_now > 0 ? -PARALLAX : PARALLAX) : 0;
    if (v.shift < want) v.shift++;
    else if (v.shift > want) v.shift--;
}

/* ---- the three cartridge entry points ------------------------------------------------ */

void trerrote_init(void) {
    uint8_t *raw = (uint8_t *)&v;
    for (unsigned i = 0; i < sizeof(v); ++i) raw[i] = 0;
    v.row.palette = v.palette;
    v.row.palette_count = PALETTE_SIZE;
    v.row.width = PRG32_GAME_W;
    v.row.height = 1;
    v.row.frame_count = 1;
    v.row.bits_per_pixel = PRG32_SPRITE_BPP_8;
    v.row.transparent_index = -1;
    v.row.pixels = v.line;
    for (int r = 1; r <= TR_ROWS; ++r) {
        v.z_row[r] = (TR_ZK << 8) / r;
        v.unit[r] = (int16_t)((r * 448) >> 8);
    }
    for (int y = 0; y < 25; ++y) {
        for (int x = 0; x < 40; ++x) v.text[y][x] = ' ';
        v.text[y][40] = 0;
    }
    v.last_ms = prg32_ticks_ms();
    v.last_input = prg32_input_read();
    v.road_pos_shown = -1;
    tribute_screen();
}

static uint32_t to_core_input(uint32_t buttons) {
    uint32_t in = 0;
    if (buttons & PRG32_BTN_LEFT) in |= TR_IN_LEFT;
    if (buttons & PRG32_BTN_RIGHT) in |= TR_IN_RIGHT;
    if (buttons & PRG32_BTN_A) in |= TR_IN_GAS;
    if (buttons & (PRG32_BTN_B | PRG32_BTN_DOWN)) in |= TR_IN_BRAKE;
    if (buttons & PRG32_BTN_UP) in |= TR_IN_HORN;
    return in;
}

static void after_level(void) {
    int next = game.level + 1;
    if (next >= LEVEL_COUNT) {
        ending_screen();
    } else if (next == 1 || next == 2) {
        ferry_screen(next);
    } else {
        intro_screen(next);
    }
}

#define ANY_BUTTON (PRG32_BTN_A | PRG32_BTN_B | PRG32_BTN_START)

/* One 33 ms step of the application. */
static void update_step(uint32_t buttons, uint32_t pressed) {
    v.app_tick++;
    tr_music_tick(&v.music);

    switch (v.app) {
    case APP_TRIBUTE:
        if ((pressed & ANY_BUTTON) || v.app_tick > 300) title_screen();
        break;
    case APP_TITLE:
        game.pos += 34;
        if ((v.app_tick & 31u) == 0) {
            if (v.app_tick & 32u) text_center(7, "PREMI A", C_LEMON);
            else text_clear_line(7);
        }
        if (pressed & (PRG32_BTN_A | PRG32_BTN_B)) {
            tr_new_game(&game, 0, prg32_ticks_ms() * 2654435761u + 1u);
            intro_screen(0);
        } else if (pressed & PRG32_BTN_START) {
            tr_music_stop(&v.music);
            prg32_audio_stop_all();
            prg32_scoreboard_show(SCORE_GAME, "I MIGLIORI TRERROTISTI");
            v.last_input = prg32_input_read();
            title_screen();
        } else if (v.app_tick > IDLE_TO_DEMO_TICKS) {
            v.demo = 1;
            /* The attract mode shows the Ape loaded, so it skips the first leg. */
            start_level(1 + (int)(prg32_ticks_ms() >> 8) % (LEVEL_COUNT - 1), 1, prg32_ticks_ms() + 7u);
        }
        break;
    case APP_INTRO:
        if ((pressed & ANY_BUTTON) || v.app_tick > 600) {
            if (v.intro_level == 1) loading_screen();
            else start_level(v.intro_level, 0, 0);
        }
        break;
    case APP_LOADING:
        if ((v.app_tick & 7u) == 0 && v.load_count < TR_MELONS_FULL) {
            v.load_count++;
            tr_sfx_play(&v.music, SFX_RECOVER, 1, v.load_count & 7);
        }
        if ((pressed & ANY_BUTTON) || (v.load_count == TR_MELONS_FULL && v.app_tick > 240)) start_level(1, 0, 0);
        break;
    case APP_PLAY: {
        if (v.demo && (pressed || v.app_tick > DEMO_TICKS)) {
            tribute_screen();
            break;
        }
        if (!v.demo && (pressed & PRG32_BTN_START)) {
            set_app(APP_PAUSE);
            text_panel(11, 12);
            text_center(11, "IN PAUSA", C_LEMON);
            text_center(12, "OMAGGIO A TONY TAMMARO", C_CREAM);
            engine_silence();
            prg32_audio_stop_all();
            break;
        }
        tr_tick(&game, v.demo ? tr_bot_input(&game) : to_core_input(buttons));
        handle_events();
        if (game.phase == PH_PLAY && !v.music.playing) song_of_level();
        if (game.phase == PH_PLAY || game.phase == PH_ARRIVE) engine_tick();
        /* The view changes at the leg's turning point: new palette, whole screen. */
        int swap = level_table[game.level][8];
        if (swap && (game.pos >> 8) >= swap && v.view != level_table[game.level][7]) view_load(level_table[game.level][7]);
        parallax_tick();
        if (game.phase == PH_DONE) {
            engine_silence();
            if (v.demo) tribute_screen();
            else card_screen();
        } else if (game.phase == PH_TIMEUP) {
            if (v.demo) tribute_screen();
            else gameover_screen(game.level < 2 ? "HAI PERSO IL TRAGHETTO!" : "TEMPO SCADUTO!");
        } else if (game.phase == PH_NOMELONS) {
            if (v.demo) tribute_screen();
            else gameover_screen("NEMMENO UN MELLONE!");
        }
        break;
    }
    case APP_PAUSE:
        if (pressed & PRG32_BTN_START) {
            set_app(APP_PLAY);
            text_clear_line(11);
            text_clear_line(12);
            if (game.phase == PH_READY) text_center(11, "PRONTI...", C_LEMON);
            else song_of_level();
        }
        break;
    case APP_FERRY:
        if ((pressed & ANY_BUTTON) || v.app_tick > 780) intro_screen(game.level + 1);
        break;
    case APP_CARD:
        if ((pressed & ANY_BUTTON) || v.app_tick > 450) after_level();
        break;
    case APP_ENDING:
        if ((pressed & ANY_BUTTON) && v.app_tick > 60) tribute_screen();
        else if (v.app_tick > 1200) tribute_screen();
        break;
    default:
        if ((pressed & ANY_BUTTON) || v.app_tick > 600) tribute_screen();
        break;
    }
}

/* Fixed timestep: game and music always advance in whole 33 ms ticks of the wall
 * clock. A host that draws slowly shows fewer frames, but the game keeps its speed
 * and the music its tempo. At most a few ticks are replayed, so a pause in the
 * host (the modal scoreboard, say) never fast-forwards the game. */
void trerrote_update(void) {
    uint32_t buttons = prg32_input_read();
    /* A press waits for the next tick: a frame shorter than a tick runs none. */
    v.pending_pressed |= buttons & ~v.last_input;
    v.last_input = buttons;
    uint32_t now = prg32_ticks_ms();
    v.tick_accum += now - v.last_ms;
    v.last_ms = now;
    if (v.tick_accum > TICK_MS * MAX_CATCH_UP) v.tick_accum = TICK_MS * MAX_CATCH_UP;
    while (v.tick_accum >= TICK_MS) {
        v.tick_accum -= TICK_MS;
        uint32_t pressed = v.pending_pressed;
        v.pending_pressed = 0;
        update_step(buttons, pressed);
    }
}

void trerrote_draw(void) {
    v.count = 0;
    switch (v.app) {
    case APP_TITLE:
        road_compute();
        add_player();
        break;
    case APP_PLAY:
    case APP_PAUSE:
    case APP_CARD:
    case APP_GAMEOVER:
        road_compute();
        hud_update();
        build_road_sprites();
        hud_sprites();
        break;
    case APP_LOADING:
        loading_sprites();
        break;
    case APP_FERRY:
        ferry_sprites();
        if ((v.app_tick & 7u) == 0) {
            for (int y = HORIZON; y < PRG32_GAME_H; ++y) v.dirty[y] = 1;
        }
        break;
    case APP_ENDING:
        ending_sprites();
        break;
    default:
        break;
    }
    render();
}
