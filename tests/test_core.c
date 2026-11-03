/*
 * The rules alone, on the workstation: no PRG32 at all.
 * Scripted situations, then the autoplayer driving the whole journey on many seeds.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../src/gen/art.inc"
#include "../src/tr_core.h"

static int failures, checks;
#define CHECK(cond) do { ++checks; if (!(cond)) { ++failures; printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #cond); } } while (0)

static tr_game_t g;

static void play(uint32_t input, int ticks) {
    for (int i = 0; i < ticks; ++i) tr_tick(&g, input);
}

static void start(int level) {
    tr_new_game(&g, level, 1234);
    g.phase_timer = 1;
    tr_tick(&g, 0);
    CHECK(g.phase == PH_PLAY);
    /* no traffic: these scripts look at one thing at a time */
    g.spawn_timer = 60000;
}

static int count_events(int type) {
    int n = 0;
    for (int i = 0; i < g.event_count; ++i) n += g.events[i].type == type;
    return n;
}

static void test_tables(void) {
    CHECK(LEVEL_COUNT == 6);
    for (int l = 0; l < LEVEL_COUNT; ++l) {
        tr_new_game(&g, l, 1);
        CHECK(g.length == level_table[l][4]);
        CHECK(g.sec_count <= TR_MAX_SECTIONS);
        CHECK(g.sec_start[g.sec_count] == g.length);
        CHECK(tr_section_index(&g, 0) == 0);
        CHECK(tr_section_index(&g, g.length + 100u) == g.sec_count - 1);
    }
    CHECK(tr_abs(-5) == 5);
    CHECK(TR_PLAYER_Z == (200 << 8) / 88);
}

static void test_driving(void) {
    start(0);
    play(TR_IN_GAS, 200);
    CHECK(g.spd == TR_SPD_MAX);
    int before = g.pos;
    play(TR_IN_GAS, 10);
    CHECK(g.pos > before);
    play(TR_IN_BRAKE, 60);
    CHECK(g.spd == 0);
    /* No steering at a standstill. */
    int x = g.x;
    play(TR_IN_LEFT, 10);
    CHECK(g.x == x);
    /* The sea is a wall on the right of the Lungomare. */
    play(TR_IN_GAS | TR_IN_RIGHT, 120);
    CHECK(g.x <= 256);
}

static void test_clock(void) {
    start(0);
    play(0, (int)g.time_limit);
    CHECK(g.phase == PH_TIMEUP);
    int ticks = (int)g.ticks;
    play(0, 10);
    CHECK((int)g.ticks == ticks);
}

static void test_spill_and_recover(void) {
    start(2);
    CHECK(g.melons == TR_MELONS_FULL);
    g.spd = 120;
    tr_spill(&g, 1, 120, 1);
    CHECK(g.melons == TR_MELONS_FULL - 1);
    int free_slots = 0;
    for (int i = 0; i < TR_MAX_LOOSE; ++i) free_slots += g.loose[i].state == MELON_FREE;
    CHECK(free_slots == TR_MAX_LOOSE - 1);
    /* It flies ahead of the Ape, as momentum demands. */
    CHECK(g.loose[0].z > g.pos + TR_PLAYER_Z);
    int z = g.loose[0].z;
    g.spd = 0;
    for (int i = 0; i < 80; ++i) {
        g.loose[0].x = (int16_t)g.x + 300;   /* out of reach for now */
        tr_loose_update(&g);
    }
    CHECK(g.loose[0].z > z);
    CHECK(g.loose[0].state != MELON_FLYING);
    /* Driving over it brings it back. */
    g.loose[0].state = MELON_REST;
    g.loose[0].h = 0;
    g.loose[0].age = 200;
    g.loose[0].z = g.pos + TR_PLAYER_Z + 50;
    g.loose[0].x = g.x;
    tr_loose_update(&g);
    CHECK(g.melons == TR_MELONS_FULL);
    CHECK(g.loose[0].state == MELON_FREE);
}

static void test_thief(void) {
    start(2);
    g.spd = 0;
    tr_spill(&g, 1, 200, 1);
    int stolen = g.stolen;
    /* The Ape stays put: a thief must arrive, take it and walk away. */
    int seen = 0;
    for (int i = 0; i < 400; ++i) {
        tr_loose_update(&g);
        tr_thieves_update(&g);
        for (int k = 0; k < TR_MAX_THIEVES; ++k) seen |= g.thieves[k].state != THIEF_FREE;
    }
    CHECK(seen);
    CHECK(g.stolen == stolen + 1);
    CHECK(g.melons == TR_MELONS_FULL - 1);
}

static void test_horn_scatters(void) {
    start(2);
    g.spd = 0;
    tr_spill(&g, 1, 200, 1);
    /* Long enough to land and be noticed, not long enough to be reached. */
    for (int i = 0; i < 60; ++i) {
        tr_loose_update(&g);
        tr_thieves_update(&g);
        int waiting = 0;
        for (int k = 0; k < TR_MAX_THIEVES; ++k) waiting += g.thieves[k].state == THIEF_COMING;
        if (waiting) break;
    }
    int coming = 0;
    for (int k = 0; k < TR_MAX_THIEVES; ++k) coming += g.thieves[k].state == THIEF_COMING;
    CHECK(coming == 1);
    tr_tick(&g, TR_IN_HORN);
    CHECK(count_events(EV_HORN) == 1);
    int fleeing = 0;
    for (int k = 0; k < TR_MAX_THIEVES; ++k) fleeing += g.thieves[k].state == THIEF_FLEEING;
    CHECK(fleeing == 1);
    /* The horn needs breath. */
    tr_tick(&g, TR_IN_HORN);
    CHECK(count_events(EV_HORN) == 0);
}

static void test_potholes(void) {
    start(3);
    /* A pothole belongs to its segment: asked twice, the same answer. */
    int found = 0;
    for (uint32_t seg = 40; seg < g.length; ++seg) {
        tr_section_t s = tr_section_at(&g, seg);
        int a = tr_pothole_x(&g, seg, s.holes, s.width), b = tr_pothole_x(&g, seg, s.holes, s.width);
        CHECK(a == b);
        if (a != -9999) {
            ++found;
            CHECK(tr_abs(a) <= tr_edge(s.width));
        }
    }
    CHECK(found > 5);
    CHECK(found < (int)g.length / 4);
    /* Hitting one costs speed and a melon. */
    for (uint32_t seg = 200; seg < g.length; ++seg) {
        tr_section_t s = tr_section_at(&g, seg);
        int hole = tr_pothole_x(&g, seg, s.holes, s.width);
        if (hole == -9999) continue;
        g.x = (int16_t)hole;
        g.spd = 140;
        g.hit_cooldown = 0;
        g.melons = 10;
        tr_cross_segment(&g, seg);
        CHECK(g.spd < 140);
        CHECK(g.melons < 10);
        break;
    }
}

static void test_anchors(void) {
    /* Pozzuoli to Casoria, then Casoria to Torregaveta. */
    int stalls = 0, foods = 0;
    for (int l = 2; l <= 3; ++l) {
        start(l);
        for (int i = 0; i < g.anchor_count; ++i) {
            const uint8_t *a = anchor_data + (g.anchor_first + i) * 4;
            uint32_t seg = (uint32_t)(a[1] | (a[2] << 8));
            int where = (int8_t)a[3];
            if (a[0] == ANCHOR_STALL) {
                /* The wrong side of the road delivers nothing. */
                g.x = (int16_t)(-where * 100);
                int m = g.melons;
                tr_cross_segment(&g, seg);
                CHECK(g.melons == m);
                g.x = (int16_t)(where * 100);
                tr_cross_segment(&g, seg);
                CHECK(g.melons == m - TR_DELIVERY);
                ++stalls;
            } else {
                int next = g.food_next;
                g.x = (int16_t)where;
                tr_cross_segment(&g, seg);
                CHECK(g.food_next == next + 1);
                /* It is taken: passing again does nothing. */
                tr_cross_segment(&g, seg);
                CHECK(g.food_next == next + 1);
                ++foods;
            }
        }
    }
    CHECK(stalls == 2);
    CHECK(foods == 4);
}

/* There must be enough chances on the road for all five foods and all the stalls. */
static void test_journey_has_enough(void) {
    int foods = 0, stalls = 0;
    for (int l = 0; l < LEVEL_COUNT; ++l) {
        for (int i = 0; i < level_table[l][3]; ++i) {
            const uint8_t *a = anchor_data + (level_table[l][2] + i) * 4;
            if (a[0] == ANCHOR_FOOD) ++foods;
            else ++stalls;
        }
    }
    CHECK(foods >= TR_FOODS);
    CHECK(stalls * TR_DELIVERY <= TR_MELONS_FULL);
}

static void test_no_melons_ends_it(void) {
    start(2);
    g.melons = 0;
    tr_tick(&g, 0);
    CHECK(g.phase == PH_NOMELONS);
    /* Having delivered, an empty Ape still drives on to the beach. */
    start(2);
    g.melons = 0;
    g.delivered = 4;
    tr_tick(&g, 0);
    CHECK(g.phase == PH_PLAY);
    /* On the first leg there is nothing to lose yet. */
    start(0);
    tr_tick(&g, 0);
    CHECK(g.phase == PH_PLAY);
}

/* The autoplayer over the whole journey, with invariants at every tick. */
static int run_journey(uint32_t seed, int *food, int *delivered, int *stolen, int *melons_left) {
    tr_new_game(&g, 0, seed);
    int done = 1;
    for (int l = 0; l < LEVEL_COUNT && done; ++l) {
        if (l) tr_load_level(&g, l);
        for (long t = 0; t < 40000; ++t) {
            tr_tick(&g, tr_bot_input(&g));
            CHECK(g.spd >= 0 && g.spd <= TR_SPD_MAX + 1);
            CHECK(g.x >= -700 && g.x <= 700);
            CHECK(g.event_count <= TR_MAX_EVENTS);
            if (g.phase == PH_DONE) break;
            if (g.phase == PH_TIMEUP || g.phase == PH_NOMELONS) {
                done = 0;
                break;
            }
        }
    }
    *food = g.food_next;
    *delivered = g.delivered;
    *stolen = g.stolen;
    *melons_left = g.melons;
    return done;
}

static void test_journeys(void) {
    int finished = 0, all_food = 0, runs = 300;
    long food_sum = 0, delivered_sum = 0, stolen_sum = 0, left_sum = 0;
    for (int i = 0; i < runs; ++i) {
        int food, delivered, stolen, left;
        finished += run_journey(1000u + (uint32_t)i * 7919u, &food, &delivered, &stolen, &left);
        all_food += food == TR_FOODS;
        food_sum += food;
        delivered_sum += delivered;
        stolen_sum += stolen;
        left_sum += left;
    }
    printf("journeys: %d runs, %d finished, %d with all foods; mean food %.2f delivered %.1f stolen %.1f left %.1f\n",
           runs, finished, all_food, (double)food_sum / runs, (double)delivered_sum / runs,
           (double)stolen_sum / runs, (double)left_sum / runs);
    CHECK(finished > 0);
    CHECK(all_food > 0);
}

int main(void) {
    test_tables();
    test_driving();
    test_clock();
    test_spill_and_recover();
    test_thief();
    test_horn_scatters();
    test_potholes();
    test_anchors();
    test_journey_has_enough();
    test_no_melons_ends_it();
    test_journeys();
    printf("core: %d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
