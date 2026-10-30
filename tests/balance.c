/*
 * A Monte Carlo study of the journey with the autoplayer: one CSV row per leg.
 *
 *   balance <runs>
 *
 * The autoplayer is a yardstick, not a person: it sees everything and reacts in one
 * tick, but it has no plan beyond the next few metres. The numbers compare legs and
 * tuning choices. They do not say how hard the game feels. See docs/balance.md.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "../src/gen/art.inc"
#include "../src/tr_core.h"

int main(int argc, char **argv) {
    int runs = argc > 1 ? atoi(argv[1]) : 1000;
    static tr_game_t g;
    long reached[LEVEL_COUNT] = {0}, passed[LEVEL_COUNT] = {0}, timeouts[LEVEL_COUNT] = {0}, empty[LEVEL_COUNT] = {0};
    double ticks[LEVEL_COUNT] = {0}, lost[LEVEL_COUNT] = {0};
    long finished = 0, fed = 0, score = 0, delivered = 0;
    for (int i = 0; i < runs; ++i) {
        tr_new_game(&g, 0, 1u + (uint32_t)i * 2654435761u);
        int alive = 1;
        for (int l = 0; l < LEVEL_COUNT && alive; ++l) {
            if (l) tr_load_level(&g, l);
            int stolen_before = g.stolen;
            reached[l]++;
            while (g.phase < PH_DONE) tr_tick(&g, tr_bot_input(&g));
            lost[l] += g.stolen - stolen_before;
            if (g.phase == PH_DONE) {
                passed[l]++;
                ticks[l] += g.ticks;
            } else {
                if (g.phase == PH_TIMEUP) timeouts[l]++;
                else empty[l]++;
                alive = 0;
            }
        }
        finished += alive;
        if (alive) {
            fed += g.food_next >= TR_FOODS;
            score += g.score;
            delivered += g.delivered + g.melons;
        }
    }
    printf("leg,reached,passed,timeouts,out_of_melons,mean_seconds,limit_seconds,mean_stolen\n");
    for (int l = 0; l < LEVEL_COUNT; ++l)
        printf("%d,%ld,%ld,%ld,%ld,%.1f,%d,%.2f\n", l + 1, reached[l], passed[l], timeouts[l], empty[l],
               passed[l] ? ticks[l] / passed[l] / TR_TICKS_PER_SEC : 0.0, level_table[l][5], reached[l] ? lost[l] / reached[l] : 0.0);
    fprintf(stderr, "journeys %d: finished %ld, Patrizia fed %ld, mean melons delivered %.1f, mean score %.0f\n", runs, finished, fed,
            finished ? (double)delivered / finished : 0.0, finished ? (double)score / finished : 0.0);
    return 0;
}
