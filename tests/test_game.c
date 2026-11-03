/*
 * The whole cartridge on the workstation: flow, rendering and sound.
 *
 *   test_game [shots-dir]   also writes screens as PPM (tests/run_tests.sh converts)
 *
 * The heart of it is the render invariant: after a frame, the panel model must equal
 * a clean repaint of every row from the game state. A row that changed but was not
 * marked dirty fails this test at the exact frame it appears.
 */
#include "host/host_prg32.h"
#include "../src/trerrote.c"

#include <stdlib.h>

static int failures, checks;
#define CHECK(cond) do { ++checks; if (!(cond)) { ++failures; printf("FAIL %s:%d %s (frame %lu, app %d)\n", __FILE__, __LINE__, #cond, frames, v.app); } } while (0)

static unsigned long frames, sampled;
static uint64_t game_pixels, game_frames, max_frame_pixels;
static const char *shots;
static int check_every = 3;

static long render_mismatch(void) {
    static uint16_t before[PRG32_GAME_H][PRG32_GAME_W];
    memcpy(before, host_panel, sizeof before);
    uint64_t spi = host_spi_pixels, presents = host_presents;
    uint32_t frame_pixels = host_frame_pixels;
    for (int y = 0; y < PRG32_GAME_H; ++y) draw_row(y, 0, PRG32_GAME_W);
    prg32_gfx_present();
    long diff = 0;
    for (int y = 0; y < PRG32_GAME_H; ++y)
        for (int x = 0; x < PRG32_GAME_W; ++x) diff += before[y][x] != host_panel[y][x];
    host_spi_pixels = spi;
    host_presents = presents;
    host_frame_pixels = frame_pixels;
    return diff;
}

static void frame_ms(uint32_t buttons, uint32_t ms) {
    host_input = buttons;
    host_ms += ms;
    host_frame_pixels = 0;
    trerrote_update();
    trerrote_draw();
    prg32_gfx_present();   /* the firmware's own present at the end of a frame */
    ++frames;
    if (v.app == APP_PLAY) {
        game_pixels += host_frame_pixels;
        game_frames++;
        if (host_frame_pixels > max_frame_pixels) max_frame_pixels = host_frame_pixels;
    }
    if (frames % (unsigned long)check_every == 0) {
        ++sampled;
        long diff = render_mismatch();
        if (diff) {
            ++failures;
            printf("FAIL render mismatch of %ld pixels at frame %lu, app %d\n", diff, frames, v.app);
        }
    }
}

static void frame(uint32_t buttons) { frame_ms(buttons, 33); }

static void wait_frames(int n) {
    for (int i = 0; i < n; ++i) frame(0);
}

static void press(uint32_t b) {
    frame(b);
    frame(0);
}

static void shot(const char *name) {
    if (!shots) return;
    char path[300];
    snprintf(path, sizeof path, "%s/%s.ppm", shots, name);
    FILE *f = fopen(path, "wb");
    if (!f) return;
    fprintf(f, "P6\n320 200\n255\n");
    for (int y = 0; y < 200; ++y)
        for (int x = 0; x < 320; ++x) {
            uint16_t c = host_panel[y][x];
            unsigned char rgb[3] = {(unsigned char)(((c >> 11) * 527 + 23) >> 6),
                                    (unsigned char)((((c >> 5) & 63) * 259 + 33) >> 6),
                                    (unsigned char)(((c & 31) * 527 + 23) >> 6)};
            fwrite(rgb, 1, 3, f);
        }
    fclose(f);
}

static uint32_t bot_buttons(void) {
    uint32_t in = tr_bot_input(&game), b = 0;
    if (in & TR_IN_LEFT) b |= PRG32_BTN_LEFT;
    if (in & TR_IN_RIGHT) b |= PRG32_BTN_RIGHT;
    if (in & TR_IN_GAS) b |= PRG32_BTN_A;
    if (in & TR_IN_BRAKE) b |= PRG32_BTN_B;
    return b;
}

/* The bot plays a leg through the real buttons; a shot at the chosen progress. */
static int play_leg(const char *name, int shot_at) {
    char label[60];
    int taken = 0, longest = 40000;
    while (v.app == APP_PLAY && longest--) {
        frame(bot_buttons());
        int progress = (int)((game.pos >> 8) * 100 / game.length);
        if (!taken && progress >= shot_at) {
            snprintf(label, sizeof label, "%s_a", name);
            shot(label);
            taken = 1;
        }
        if (taken == 1 && progress >= shot_at + 40) {
            snprintf(label, sizeof label, "%s_b", name);
            shot(label);
            taken = 2;
        }
        /* On the last leg Patrizia waits at the finish: she must be on screen. */
        if (taken == 2 && game.level == LEVEL_COUNT - 1 && (int)game.length - (int)(game.pos >> 8) <= TR_PLAYER_Z / 256 + 8) {
            int seen = 0;
            for (int i = 0; i < v.count; ++i) seen |= v.cur[i].id == SPR_PATRIZIA;
            CHECK(seen);
            shot("patrizia");
            taken = 3;
        }
    }
    frame(0);   /* let go of the pedals */
    return v.app;
}

static void assert_tribute_text(void) {
    /* The tribute must be stated plainly, in the game, before anything else. */
    int found_name = 0, found_maestro = 0, found_unofficial = 0;
    for (int y = 0; y < 25; ++y) {
        if (strstr(v.text[y], "TONY TAMMARO")) found_name = 1;
        if (strstr(v.text[y], "IL GRANDE MAESTRO")) found_maestro = 1;
        if (strstr(v.text[y], "NON UFFICIALE")) found_unofficial = 1;
    }
    CHECK(found_name);
    CHECK(found_maestro);
    CHECK(found_unofficial);
}

static void test_full_game(void) {
    /* A first frame paints the tribute. */
    trerrote_init();
    CHECK(v.app == APP_TRIBUTE);
    assert_tribute_text();
    wait_frames(4);
    shot("tribute");
    CHECK(host_bad_tile_calls == 0);
    press(PRG32_BTN_A);
    CHECK(v.app == APP_TITLE);
    wait_frames(40);
    shot("title");
    press(PRG32_BTN_A);
    CHECK(v.app == APP_INTRO);
    wait_frames(4);
    shot("intro1");
    press(PRG32_BTN_A);
    CHECK(v.app == APP_PLAY);
    wait_frames(4);
    shot("ready");
    wait_frames(80);
    CHECK(game.phase == PH_PLAY);
    frame(PRG32_BTN_A | PRG32_BTN_START);
    CHECK(v.app == APP_PAUSE);
    wait_frames(4);
    shot("pause");
    press(PRG32_BTN_START);
    CHECK(v.app == APP_PLAY);

    for (int leg = 0; leg < LEVEL_COUNT; ++leg) {
        char name[8];
        snprintf(name, sizeof name, "leg%d", leg + 1);
        int app = play_leg(name, leg == 0 ? 30 : 25);
        if (app == APP_GAMEOVER) {
            printf("journey ended on leg %d: melons %d time %lu\n", leg + 1, game.melons, (unsigned long)game.ticks);
            shot("gameover");
            press(PRG32_BTN_A);
            CHECK(v.app == APP_TRIBUTE);
            return;
        }
        CHECK(app == APP_CARD);
        char label[40];
        snprintf(label, sizeof label, "card%d", leg + 1);
        wait_frames(3);
        shot(label);
        press(PRG32_BTN_A);
        if (leg == 0 || leg == 1) {
            CHECK(v.app == APP_FERRY);
            wait_frames(180);
            snprintf(label, sizeof label, "ferry%d", leg + 1);
            shot(label);
            press(PRG32_BTN_A);
        }
        if (leg < LEVEL_COUNT - 1) {
            CHECK(v.app == APP_INTRO);
            wait_frames(3);
            snprintf(label, sizeof label, "intro%d", leg + 2);
            shot(label);
            press(PRG32_BTN_A);
            if (leg == 0) {
                CHECK(v.app == APP_LOADING);
                wait_frames(100);
                shot("loading");
                wait_frames(220);
            }
            CHECK(v.app == APP_PLAY);
            wait_frames(90);
        }
    }
    CHECK(v.app == APP_ENDING);
    wait_frames(10);
    shot("ending");
    CHECK(host_score_submits == 1);
    wait_frames(70);
    press(PRG32_BTN_A);
    CHECK(v.app == APP_TRIBUTE);
    assert_tribute_text();
}

static void test_attract_and_timeout(void) {
    trerrote_init();
    press(PRG32_BTN_A);
    CHECK(v.app == APP_TITLE);
    wait_frames(IDLE_TO_DEMO_TICKS + 3);
    CHECK(v.app == APP_PLAY && v.demo);
    wait_frames(200);
    shot("demo");
    press(PRG32_BTN_A);
    CHECK(v.app == APP_TRIBUTE);

    /* Do nothing on the first leg: the ferry leaves. */
    trerrote_init();
    press(PRG32_BTN_A);
    press(PRG32_BTN_A);
    press(PRG32_BTN_A);
    CHECK(v.app == APP_PLAY);
    int guard = 5000;
    while (v.app == APP_PLAY && guard--) frame(0);
    CHECK(v.app == APP_GAMEOVER);
    wait_frames(4);
    shot("missed_ferry");
    press(PRG32_BTN_START);
    CHECK(v.app == APP_TRIBUTE);
}

/* A press that lands on a frame too short to run a tick must not be lost. */
static void test_short_frames_keep_presses(void) {
    trerrote_init();
    wait_frames(3);
    CHECK(v.app == APP_TRIBUTE);
    v.tick_accum = 0;
    frame_ms(PRG32_BTN_A, 2);
    CHECK(v.app == APP_TRIBUTE);   /* no tick yet */
    frame_ms(0, 2);
    frame_ms(0, 33);
    CHECK(v.app == APP_TITLE);
    /* And one press acts once, however the frames fall. */
    CHECK(v.pending_pressed == 0);
    wait_frames(3);
    CHECK(v.app == APP_TITLE);
}

/* Irregular frames, as on hardware, must not disturb the picture either. */
static void test_irregular_frames(void) {
    trerrote_init();
    press(PRG32_BTN_A);
    press(PRG32_BTN_A);
    press(PRG32_BTN_A);
    CHECK(v.app == APP_PLAY);
    wait_frames(80);
    static const uint8_t lengths[6] = {100, 7, 66, 41, 12, 108};
    for (int i = 0; i < 600 && v.app == APP_PLAY; ++i) frame_ms(bot_buttons(), lengths[i % 6]);
    CHECK(v.app == APP_PLAY);
}

/* Busy rows and plain rows take different paths to the firmware: same picture. */
static void test_row_paths_agree(void) {
    trerrote_init();
    uint8_t line[VIEW_W + 8];
    for (int k = 0; k < 2; ++k) {
        for (int x = 0; x < PRG32_GAME_W; ++x)
            line[x] = (uint8_t)(k ? (x / 40) % 8 : (x * 7) % PALETTE_SIZE);   /* few runs, many runs */
        send_row(line, 50, 0, PRG32_GAME_W);
        for (int x = 0; x < PRG32_GAME_W; ++x) CHECK(host_fb[50][x] == v.cell[line[x]]);
    }
}

static void test_all_views_palette(void) {
    /* Every colour of a view must be exact on the indexed framebuffer. */
    for (int n = 0; n < VIEW_COUNT; ++n) {
        view_load(n);
        for (int i = 0; i < PALETTE_SIZE; ++i) {
            uint8_t cell = cube_index(v.palette[i]);
            CHECK(host_palette[cell] == v.palette[i]);
        }
    }
    /* Each row of each view decodes to exactly its width. */
    for (int n = 0; n < VIEW_COUNT; ++n) {
        for (int row = 0; row < VIEW_H; ++row) {
            memset(v.line, 255, sizeof v.line);
            decode_view_row(view_data + view_rows[n * VIEW_H + row], v.line, VIEW_W, FIXED_COUNT);
            for (int x = 0; x < VIEW_W; ++x) CHECK(v.line[x] >= FIXED_COUNT && v.line[x] < PALETTE_SIZE);
            CHECK(v.line[VIEW_W] == 255);
        }
    }
}

static void test_sound(void) {
    int by_channel[8] = {0};
    for (int i = 0; i < host_note_count; ++i) {
        const host_note_t *n = &host_notes[i];
        CHECK(n->channel < 8);
        if (n->kind) {
            by_channel[n->channel]++;
            CHECK(n->instrument < 18);
            CHECK(n->note >= 12 && n->note <= 108);
        }
    }
    int voices = 0;
    for (int c = 0; c < 8; ++c) voices += by_channel[c] > 0;
    printf("sound: %d notes on %d channels (engine %d)\n", host_note_count, voices, by_channel[TR_ENGINE_CHANNEL]);
    CHECK(voices == 8);
}

int main(int argc, char **argv) {
    if (argc > 1) shots = argv[1];
    test_all_views_palette();
    test_full_game();
    test_sound();
    test_attract_and_timeout();
    test_short_frames_keep_presses();
    test_irregular_frames();
    test_row_paths_agree();
    printf("render: %lu frames, %lu repaint comparisons; in play %.0f panel pixels per frame on average, %llu at most\n",
           frames, sampled, game_frames ? (double)game_pixels / game_frames : 0.0, (unsigned long long)max_frame_pixels);
    printf("game: %d checks, %d failures; sizeof(v)=%zu sizeof(game)=%zu\n", checks, failures, sizeof v, sizeof game);
    return failures ? 1 : 0;
}
