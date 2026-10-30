/*
 * tr_core.h - the rules of The Trerrote Connection. No PRG32 call in this file.
 *
 * The world is a road of segments, each about a metre long. Distances along the
 * road are Q8 fixed point (256 = one segment). The lateral position x is in units
 * where +-256 is the edge of a full-width road. The includer provides the road
 * tables of src/gen/art.inc, so tests run the same rules on the workstation.
 *
 * What happens is reported in events[], and the cartridge turns those into sound
 * and pictures: the rules never know how they are shown.
 */
#ifndef TR_CORE_H
#define TR_CORE_H

#include <stdint.h>

#define TR_ROWS 104            /* rows of road on screen */
#define TR_ZK 200              /* distance in segments x row number is constant */
#define TR_PLAYER_ROW 88
#define TR_PLAYER_Z ((TR_ZK << 8) / TR_PLAYER_ROW)
#define TR_DRAW_SEGS 64
#define TR_SPD_MAX 150         /* Q8 segments per tick: 60 km/h */
#define TR_TICKS_PER_SEC 30
#define TR_MELONS_FULL 24
#define TR_DELIVERY 4          /* melons handed over at each stall */
#define TR_FOODS 5

#define TR_MAX_CARS 8
#define TR_MAX_LOOSE 8
#define TR_MAX_THIEVES 3
#define TR_MAX_EVENTS 8
#define TR_MAX_SECTIONS 16

#define TR_IN_LEFT 1u
#define TR_IN_RIGHT 2u
#define TR_IN_GAS 4u
#define TR_IN_BRAKE 8u
#define TR_IN_HORN 16u

enum { GROUND_PAVE, GROUND_SEA, GROUND_SAND, GROUND_GRASS, GROUND_TUFF };
enum { DECO_NONE, DECO_PALM, DECO_PINE, DECO_LAMP, DECO_HOUSE, DECO_UMBRELLA };
enum { ANCHOR_STALL, ANCHOR_FOOD };
enum { STYLE_JAM, STYLE_LANES, STYLE_TAMARRI, STYLE_TRUCK, STYLE_EVERYTHING };
enum { CAR_NONE, CAR_PLAIN, CAR_TAMARRO, CAR_SCOOTER, CAR_TRUCK };
enum { PH_READY, PH_PLAY, PH_ARRIVE, PH_DONE, PH_TIMEUP, PH_NOMELONS };
enum { MELON_FREE, MELON_FLYING, MELON_ROLLING, MELON_REST };
enum { THIEF_FREE, THIEF_COMING, THIEF_LEAVING, THIEF_FLEEING };
enum {
    EV_NONE, EV_BUMP, EV_CRASH, EV_SCRAPE, EV_SPILL, EV_RECOVER, EV_STOLEN, EV_DELIVER, EV_FOOD,
    EV_HORN, EV_GO, EV_ARRIVE, EV_TIME_LOW, EV_COUNT
};

typedef struct {
    uint16_t len;
    int8_t curve;
    uint8_t width, ground_l, ground_r, deco_l, deco_r, period, traffic, holes;
} tr_section_t;

typedef struct {
    int32_t z;
    int16_t x, spd, target_x;
    uint8_t kind, tint, anim, cooldown;
} tr_car_t;

typedef struct {
    int32_t z;
    int16_t x, h, vz, vx, vh;
    uint8_t state, age;
} tr_loose_t;

typedef struct {
    int32_t z;
    int16_t x;
    uint8_t state, target, anim, carrying, tint;
} tr_thief_t;

typedef struct {
    uint8_t type;
    int16_t x;
    uint16_t value;
} tr_event_t;

typedef struct {
    uint8_t level, phase, style;
    uint16_t length;               /* segments */
    uint16_t sec_start[TR_MAX_SECTIONS + 1];
    uint8_t sec_count, sec_first;
    uint8_t anchor_first, anchor_count;
    uint16_t anchor_taken;

    int32_t pos;                   /* the camera's distance along the road, Q8 */
    int16_t x, spd;
    int8_t steer;                  /* -1, 0, 1, for the picture */
    uint8_t off_road, bump, hit_cooldown, horn_cooldown, horn;
    int16_t slosh;                 /* 0..255: how far the load has shifted */
    int16_t curve_now;
    uint32_t last_seg;

    uint32_t ticks, time_limit;    /* ticks */
    uint16_t phase_timer;

    uint8_t melons, delivered, stolen, food_next;
    uint32_t score, leg_score;
    uint8_t time_warned;

    tr_car_t cars[TR_MAX_CARS];
    tr_loose_t loose[TR_MAX_LOOSE];
    tr_thief_t thieves[TR_MAX_THIEVES];
    uint16_t spawn_timer;

    uint32_t rng;
    tr_event_t events[TR_MAX_EVENTS];
    uint8_t event_count;
} tr_game_t;

static int tr_abs(int v) { return v < 0 ? -v : v; }

static uint32_t tr_rand(tr_game_t *g) {
    uint32_t x = g->rng;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    g->rng = x;
    return x;
}

static void tr_event(tr_game_t *g, int type, int x, unsigned value) {
    if (g->event_count == TR_MAX_EVENTS) return;
    tr_event_t *e = &g->events[g->event_count++];
    e->type = (uint8_t)type;
    e->x = (int16_t)x;
    e->value = (uint16_t)value;
}

/* ---- the road ------------------------------------------------------------- */

static tr_section_t tr_section_read(int absolute_index) {
    const uint8_t *d = section_data + absolute_index * SECTION_BYTES;
    tr_section_t s;
    s.len = (uint16_t)(d[0] | (d[1] << 8));
    s.curve = (int8_t)d[2];
    s.width = d[3];
    s.ground_l = d[4];
    s.ground_r = d[5];
    s.deco_l = d[6];
    s.deco_r = d[7];
    s.period = d[8];
    s.traffic = d[9];
    s.holes = d[10];
    return s;
}

/* Which section holds a segment. Beyond the end, the road just goes on as the last. */
static int tr_section_index(const tr_game_t *g, uint32_t seg) {
    int i = 0;
    while (i + 1 < g->sec_count && seg >= g->sec_start[i + 1]) ++i;
    return i;
}

static tr_section_t tr_section_at(const tr_game_t *g, uint32_t seg) {
    return tr_section_read(g->sec_first + tr_section_index(g, seg));
}

/* A pothole is a property of its segment, not an object: no memory, no spawning. */
static int tr_pothole_x(const tr_game_t *g, uint32_t seg, int holes, int width) {
    if (!holes || seg < 40 || seg + 20 >= g->length) return -9999;
    uint32_t h = (seg + 17u * (uint32_t)g->level) * 2654435761u;
    if (((h >> 24) & 255u) * 3u >= (uint32_t)holes * 2u) return -9999;
    int span = 180 * width / 16;
    return (int)((h >> 12) & 255u) * 2 * span / 255 - span;
}

static int tr_edge(int width) { return 256 * width / 16; }

static int tr_blocked_ground(int ground) { return ground == GROUND_SEA || ground == GROUND_TUFF; }

/* ---- starting a leg --------------------------------------------------------- */

static void tr_load_level(tr_game_t *g, int level) {
    const uint16_t *row = level_table[level];
    g->level = (uint8_t)level;
    g->phase = PH_READY;
    g->phase_timer = 75;
    g->sec_first = (uint8_t)row[0];
    g->sec_count = (uint8_t)row[1];
    g->anchor_first = (uint8_t)row[2];
    g->anchor_count = (uint8_t)row[3];
    g->anchor_taken = 0;
    g->length = row[4];
    g->time_limit = (uint32_t)row[5] * TR_TICKS_PER_SEC;
    g->style = (uint8_t)row[10];
    uint16_t at = 0;
    for (int i = 0; i < g->sec_count; ++i) {
        g->sec_start[i] = at;
        at = (uint16_t)(at + tr_section_read(g->sec_first + i).len);
    }
    g->sec_start[g->sec_count] = at;
    g->pos = 0;
    g->x = 0;
    g->spd = 0;
    g->steer = 0;
    g->off_road = 0;
    g->bump = 0;
    g->hit_cooldown = 0;
    g->horn_cooldown = 0;
    g->horn = 0;
    g->slosh = 0;
    g->curve_now = 0;
    g->last_seg = 0;
    g->ticks = 0;
    g->time_warned = 0;
    g->leg_score = 0;
    g->spawn_timer = 30;
    for (int i = 0; i < TR_MAX_CARS; ++i) g->cars[i].kind = CAR_NONE;
    for (int i = 0; i < TR_MAX_LOOSE; ++i) g->loose[i].state = MELON_FREE;
    for (int i = 0; i < TR_MAX_THIEVES; ++i) g->thieves[i].state = THIEF_FREE;
    g->event_count = 0;
    if (row[11]) g->melons = TR_MELONS_FULL;
}

static void tr_new_game(tr_game_t *g, int level, uint32_t seed) {
    uint8_t *raw = (uint8_t *)g;
    for (unsigned i = 0; i < sizeof(*g); ++i) raw[i] = 0;
    g->rng = seed ? seed : 0x9E3779B9u;
    tr_load_level(g, level);
    if (level >= 2) g->melons = TR_MELONS_FULL;   /* the demo may start anywhere */
}

/* ---- melons on the loose ---------------------------------------------------- */

static void tr_score(tr_game_t *g, unsigned points) {
    g->score += points;
    g->leg_score += points;
}

/* The Ape stops, the melons do not: they fly on along the road. */
static void tr_spill(tr_game_t *g, int count, int speed, int side) {
    for (int k = 0; k < count && g->melons; ++k) {
        tr_loose_t *m = 0;
        for (int i = 0; i < TR_MAX_LOOSE; ++i)
            if (g->loose[i].state == MELON_FREE) {
                m = &g->loose[i];
                break;
            }
        g->melons--;
        if (!m) {
            g->stolen++;      /* no room to show it: it is gone already */
            continue;
        }
        m->state = MELON_FLYING;
        m->age = 0;
        m->z = g->pos + TR_PLAYER_Z + 120;
        m->x = (int16_t)(g->x + (int)(tr_rand(g) & 63u) - 32);
        m->h = 300;
        m->vz = (int16_t)(speed + 30 + (int)(tr_rand(g) & 63u));
        m->vx = (int16_t)(side * 5 + (int)(tr_rand(g) & 7u) - 4);
        m->vh = (int16_t)(40 + (int)(tr_rand(g) & 31u));
        tr_event(g, EV_SPILL, g->x, g->melons);
    }
}

static void tr_call_thief(tr_game_t *g, int melon) {
    /* The melon's owner has changed, as far as the pavement is concerned. */
    const tr_loose_t *m = &g->loose[melon];
    for (int i = 0; i < TR_MAX_THIEVES; ++i) {
        if (g->thieves[i].state == THIEF_COMING && g->thieves[i].target == melon) return;
    }
    for (int i = 0; i < TR_MAX_THIEVES; ++i) {
        tr_thief_t *t = &g->thieves[i];
        if (t->state != THIEF_FREE) continue;
        tr_section_t s = tr_section_at(g, (uint32_t)(m->z >> 8));
        int side = m->x < 0 ? -1 : 1;
        t->state = THIEF_COMING;
        t->target = (uint8_t)melon;
        t->z = m->z;
        t->x = (int16_t)(side * (tr_edge(s.width) + 90));
        t->anim = 0;
        t->carrying = 0;
        t->tint = (uint8_t)(tr_rand(g) & 3u);
        return;
    }
}

static void tr_loose_update(tr_game_t *g) {
    int player_z = g->pos + TR_PLAYER_Z;
    for (int i = 0; i < TR_MAX_LOOSE; ++i) {
        tr_loose_t *m = &g->loose[i];
        if (m->state == MELON_FREE) continue;
        if (m->age < 255) m->age++;
        m->z += m->vz;
        m->x = (int16_t)(m->x + m->vx);
        if (m->state == MELON_FLYING) {
            m->h = (int16_t)(m->h + m->vh);
            m->vh = (int16_t)(m->vh - 14);
            if (m->h <= 0) {
                m->h = 0;
                m->vh = (int16_t)(-m->vh / 2);
                m->vz = (int16_t)(m->vz * 3 / 4);
                m->vx = (int16_t)(m->vx / 2);
                if (m->vh < 24) {
                    m->state = MELON_ROLLING;
                    m->vh = 0;
                    tr_call_thief(g, i);
                }
            }
        } else if (m->state == MELON_ROLLING) {
            m->vz = (int16_t)(m->vz - m->vz / 8 - 1);
            if (m->vz <= 2) {
                m->vz = 0;
                m->vx = 0;
                m->state = MELON_REST;
            }
        }
        tr_section_t s = tr_section_at(g, (uint32_t)(m->z >> 8));
        int edge = tr_edge(s.width) + 40;
        if (m->x > edge) m->x = (int16_t)edge;
        if (m->x < -edge) m->x = (int16_t)-edge;

        /* Driving over it puts it back on the load. */
        int dz = m->z - player_z;
        if (m->age > 18 && m->h < 100 && dz > -110 && dz < 170 && tr_abs(m->x - g->x) < 90) {
            m->state = MELON_FREE;
            g->melons++;
            tr_score(g, 50);
            tr_event(g, EV_RECOVER, m->x, g->melons);
            continue;
        }
        /* Left behind the camera: somebody has it by now. */
        if (m->z < g->pos - 256) {
            m->state = MELON_FREE;
            g->stolen++;
            tr_event(g, EV_STOLEN, m->x, g->stolen);
            continue;
        }
        /* Any car that reaches it keeps it. */
        for (int c = 0; c < TR_MAX_CARS; ++c) {
            const tr_car_t *car = &g->cars[c];
            if (car->kind != CAR_NONE && m->h < 80 && tr_abs(car->z - m->z) < 200 && tr_abs(car->x - m->x) < 60) {
                m->state = MELON_FREE;
                g->stolen++;
                tr_event(g, EV_STOLEN, m->x, g->stolen);
                break;
            }
        }
    }
}

static void tr_thieves_update(tr_game_t *g) {
    for (int i = 0; i < TR_MAX_THIEVES; ++i) {
        tr_thief_t *t = &g->thieves[i];
        if (t->state == THIEF_FREE) continue;
        t->anim++;
        if (t->z < g->pos - 256) {
            t->state = THIEF_FREE;
            continue;
        }
        tr_section_t s = tr_section_at(g, (uint32_t)(t->z >> 8));
        int edge = tr_edge(s.width);
        int home = t->x < 0 ? -(edge + 120) : edge + 120;
        if (t->state == THIEF_COMING) {
            tr_loose_t *m = &g->loose[t->target];
            if (m->state == MELON_FREE) {
                t->state = THIEF_LEAVING;
                continue;
            }
            t->z += (m->z - t->z) / 4;
            int dx = m->x - t->x;
            int step = 5;
            if (tr_abs(dx) <= step) {
                t->x = m->x;
                if (m->h < 40) {
                    m->state = MELON_FREE;
                    g->stolen++;
                    t->carrying = 1;
                    t->state = THIEF_LEAVING;
                    tr_event(g, EV_STOLEN, t->x, g->stolen);
                }
            } else {
                t->x = (int16_t)(t->x + (dx > 0 ? step : -step));
            }
        } else {
            int dir = home > t->x ? 1 : -1;
            t->x = (int16_t)(t->x + dir * (t->state == THIEF_FLEEING ? 10 : 6));
            if (tr_abs(t->x) >= edge + 110) {
                if (t->state == THIEF_FLEEING && !t->carrying && t->anim > 40 && g->loose[t->target].state != MELON_FREE) {
                    t->state = THIEF_COMING;   /* back for another try */
                } else if (t->state != THIEF_FLEEING || t->anim > 40) {
                    t->state = THIEF_FREE;
                }
            }
        }
        /* Nobody gets run over in this game: they jump clear, and swear. */
        int dz = t->z - (g->pos + TR_PLAYER_Z);
        if (dz > -90 && dz < 220 && tr_abs(t->x - g->x) < 70) t->x = (int16_t)(t->x + (t->x < g->x ? -12 : 12));
    }
}

/* ---- traffic ------------------------------------------------------------------ */

static int tr_car_half(int kind) {
    return kind == CAR_TRUCK ? 80 : kind == CAR_SCOOTER ? 26 : 56;
}

static tr_car_t *tr_car_slot(tr_game_t *g) {
    for (int i = 0; i < TR_MAX_CARS; ++i)
        if (g->cars[i].kind == CAR_NONE) return &g->cars[i];
    return 0;
}

static int tr_truck_on_road(const tr_game_t *g) {
    for (int i = 0; i < TR_MAX_CARS; ++i)
        if (g->cars[i].kind == CAR_TRUCK) return 1;
    return 0;
}

static void tr_spawn_one(tr_game_t *g, int kind, int z, int lane_x, int spd) {
    tr_car_t *c = tr_car_slot(g);
    if (!c) return;
    for (int i = 0; i < TR_MAX_CARS; ++i) {
        const tr_car_t *o = &g->cars[i];
        if (o->kind != CAR_NONE && tr_abs(o->z - z) < 6 * 256 && tr_abs(o->x - lane_x) < 90) return;
    }
    c->kind = (uint8_t)kind;
    c->z = z;
    c->x = (int16_t)lane_x;
    c->target_x = (int16_t)lane_x;
    c->spd = (int16_t)spd;
    c->tint = (uint8_t)(tr_rand(g) & 3u);
    c->anim = 0;
    c->cooldown = 0;
}

static void tr_spawn_traffic(tr_game_t *g) {
    if (g->spawn_timer) {
        g->spawn_timer--;
        return;
    }
    uint32_t seg = (uint32_t)(g->pos >> 8) + 60;
    if (seg + 30 >= g->length) return;
    tr_section_t s = tr_section_at(g, seg);
    g->spawn_timer = (uint16_t)(s.traffic ? (g->style == STYLE_JAM ? 16 + 120 / (s.traffic + 1) : 34 + 260 / (s.traffic + 1)) + (tr_rand(g) & 15u) : 40);
    if (!s.traffic) return;
    int z = (int)seg << 8;
    int lane = 128 * s.width / 16;
    int x = (tr_rand(g) & 1u) ? lane : -lane;
    uint32_t r = tr_rand(g) & 15u;
    switch (g->style) {
    case STYLE_JAM:
        /* The jam on the Lungomare: slow, and two abreast with luck between them. */
        tr_spawn_one(g, CAR_PLAIN, z, x, 28 + (int)(tr_rand(g) & 31u));
        if (s.traffic >= 10 && (tr_rand(g) & 1u)) tr_spawn_one(g, CAR_PLAIN, z + 128, -x, 24 + (int)(tr_rand(g) & 31u));
        break;
    case STYLE_LANES:
        if (r < 11) tr_spawn_one(g, CAR_SCOOTER, z, x / 2, 80);
        else tr_spawn_one(g, CAR_PLAIN, z, x / 2, 66);
        break;
    case STYLE_TAMARRI:
        if (r < 6) tr_spawn_one(g, CAR_TAMARRO, z, x, 92);
        else if (r < 11) tr_spawn_one(g, CAR_SCOOTER, z, x, 104);
        else tr_spawn_one(g, CAR_PLAIN, z, x, 70);
        break;
    case STYLE_TRUCK:
        if (r < 5 && !tr_truck_on_road(g)) tr_spawn_one(g, CAR_TRUCK, z, x * 3 / 4, 72);
        else if (r < 9) tr_spawn_one(g, CAR_TAMARRO, z, x, 96);
        else tr_spawn_one(g, CAR_PLAIN, z, x, 72);
        break;
    default:
        if (r < 3 && !tr_truck_on_road(g)) tr_spawn_one(g, CAR_TRUCK, z, x * 3 / 4, 74);
        else if (r < 7) tr_spawn_one(g, CAR_TAMARRO, z, x, 96);
        else if (r < 11) tr_spawn_one(g, CAR_SCOOTER, z, x, 108);
        else tr_spawn_one(g, CAR_PLAIN, z, x, 70);
        break;
    }
    /* While melons are about, a scooter may come up from behind to see. */
    if (g->melons && g->style >= STYLE_TAMARRI && (tr_rand(g) & 15u) == 0)
        tr_spawn_one(g, CAR_SCOOTER, g->pos - 200, g->x > 0 ? -lane : lane, TR_SPD_MAX + 30);
}

static void tr_traffic_update(tr_game_t *g) {
    int player_z = g->pos + TR_PLAYER_Z;
    for (int i = 0; i < TR_MAX_CARS; ++i) {
        tr_car_t *c = &g->cars[i];
        if (c->kind == CAR_NONE) continue;
        c->anim++;
        int spd = c->spd;
        /* The queue: stop and go, in a wave down the road. */
        if (g->style == STYLE_JAM && (((uint32_t)(c->z >> 11) + (g->ticks >> 6)) & 3u) == 0) spd = spd / 3;
        /* Nobody drives into the car ahead, except you. */
        for (int k = 0; k < TR_MAX_CARS; ++k) {
            const tr_car_t *o = &g->cars[k];
            if (k == i || o->kind == CAR_NONE) continue;
            int dz = o->z - c->z;
            if (dz > 0 && dz < 5 * 256 && tr_abs(o->x - c->x) < 90 && o->spd < spd) spd = o->spd;
        }
        c->z += spd;
        tr_section_t s = tr_section_at(g, (uint32_t)(c->z >> 8));
        int lane = 128 * s.width / 16;
        if (c->kind == CAR_SCOOTER) {
            /* A scooter weaves because it can. */
            if ((c->anim & 63u) == 0) c->target_x = (int16_t)((int)(tr_rand(g) & 255u) * 2 * lane / 255 - lane);
        } else if (c->kind == CAR_TAMARRO) {
            /* Tamarri cut you up as soon as they are ahead of you. */
            if ((c->anim & 127u) == 0 && c->z > player_z + 2048) {
                int t = g->x;
                if (t > lane) t = lane;
                if (t < -lane) t = -lane;
                c->target_x = (int16_t)t;
            }
        } else {
            if (c->target_x > lane) c->target_x = (int16_t)lane;
            if (c->target_x < -lane) c->target_x = (int16_t)-lane;
        }
        int dx = c->target_x - c->x;
        int step = c->kind == CAR_SCOOTER ? 3 : 2;
        if (tr_abs(dx) <= step) c->x = c->target_x;
        else c->x = (int16_t)(c->x + (dx > 0 ? step : -step));
        if (c->cooldown) c->cooldown--;
        if (c->z < g->pos - 512 || c->z > g->pos + (TR_DRAW_SEGS + 30) * 256) c->kind = CAR_NONE;
    }
}

static void tr_collide_cars(tr_game_t *g) {
    if (g->hit_cooldown) {
        g->hit_cooldown--;
        return;
    }
    int player_z = g->pos + TR_PLAYER_Z;
    for (int i = 0; i < TR_MAX_CARS; ++i) {
        tr_car_t *c = &g->cars[i];
        if (c->kind == CAR_NONE) continue;
        int dz = c->z - player_z;
        if (dz < -120 || dz > 220) continue;
        int reach = tr_car_half(c->kind) + 44;
        if (tr_abs(c->x - g->x) >= reach) continue;
        int before = g->spd;
        int ahead = c->z > player_z;
        if (ahead && before <= c->spd) continue;
        int loss = c->kind == CAR_TRUCK ? 3 : 1;
        g->spd = (int16_t)(ahead ? c->spd * 3 / 4 : before);
        if (c->kind == CAR_TRUCK && ahead) g->spd = (int16_t)(c->spd / 3);
        g->bump = 12;
        g->hit_cooldown = 30;
        c->z += 200;
        c->spd = (int16_t)(c->spd + 14);
        g->x = (int16_t)(g->x + (g->x < c->x ? -16 : 16));
        tr_event(g, EV_CRASH, g->x, (unsigned)c->kind);
        tr_spill(g, loss, before, g->x < c->x ? -1 : 1);
        return;
    }
}

/* ---- the road surface under the Ape ------------------------------------------- */

static void tr_cross_segment(tr_game_t *g, uint32_t seg) {
    tr_section_t s = tr_section_at(g, seg);
    int hole = tr_pothole_x(g, seg, s.holes, s.width);
    if (hole != -9999 && tr_abs(hole - g->x) < 76 && !g->hit_cooldown) {
        int before = g->spd;
        g->spd = (int16_t)(g->spd * 3 / 4);
        g->bump = 8;
        g->hit_cooldown = 14;
        tr_event(g, EV_BUMP, hole, seg);
        tr_spill(g, 1, before, hole < g->x ? 1 : -1);
    }
    for (int i = 0; i < g->anchor_count; ++i) {
        if ((g->anchor_taken >> i) & 1u) continue;
        const uint8_t *a = anchor_data + (g->anchor_first + i) * 4;
        if ((uint32_t)(a[1] | (a[2] << 8)) != seg) continue;
        int where = (int8_t)a[3];
        if (a[0] == ANCHOR_STALL) {
            /* The stall's bay is on its own half of the road. */
            if (where * g->x > 30 && g->melons) {
                int n = g->melons < TR_DELIVERY ? g->melons : TR_DELIVERY;
                g->melons = (uint8_t)(g->melons - n);
                g->delivered = (uint8_t)(g->delivered + n);
                tr_score(g, (unsigned)n * 250u);
                g->anchor_taken |= (uint16_t)(1u << i);
                tr_event(g, EV_DELIVER, g->x, (unsigned)n);
            }
        } else if (g->food_next < TR_FOODS && tr_abs(where - g->x) < 90) {
            tr_event(g, EV_FOOD, g->x, g->food_next);
            g->food_next++;
            tr_score(g, 300);
            g->anchor_taken |= (uint16_t)(1u << i);
        }
    }
}

static int tr_melons_alive(const tr_game_t *g) {
    if (g->melons) return 1;
    for (int i = 0; i < TR_MAX_LOOSE; ++i)
        if (g->loose[i].state != MELON_FREE) return 1;
    return 0;
}

/* ---- one 33 ms tick -------------------------------------------------------------- */

static void tr_tick(tr_game_t *g, uint32_t input) {
    g->event_count = 0;
    switch (g->phase) {
    case PH_READY:
        if (--g->phase_timer == 0) {
            g->phase = PH_PLAY;
            tr_event(g, EV_GO, 0, 0);
        }
        return;
    case PH_ARRIVE:
        /* Over the line the Ape coasts on with the brake half on. */
        g->pos += g->spd;
        if (g->spd > 40) g->spd = (int16_t)(g->spd - 2);
        g->x = (int16_t)(g->x - g->x / 16);
        tr_traffic_update(g);
        if (--g->phase_timer == 0) g->phase = PH_DONE;
        return;
    case PH_PLAY:
        break;
    default:
        return;
    }

    g->ticks++;
    if (g->ticks >= g->time_limit) {
        g->phase = PH_TIMEUP;
        g->spd = 0;
        return;
    }
    uint32_t left = g->time_limit - g->ticks;
    if (left <= 10 * TR_TICKS_PER_SEC && (left % TR_TICKS_PER_SEC) == 0) tr_event(g, EV_TIME_LOW, 0, left / TR_TICKS_PER_SEC);

    /* Pedals. The two-stroke runs out of breath near the top. */
    if (input & TR_IN_BRAKE) g->spd = (int16_t)(g->spd - 6);
    else if (input & TR_IN_GAS) g->spd = (int16_t)(g->spd + (g->spd < 90 ? 3 : g->spd < 125 ? 2 : 1));
    else g->spd = (int16_t)(g->spd - 1);
    if (g->spd < 0) g->spd = 0;

    uint32_t seg = (uint32_t)((g->pos + TR_PLAYER_Z) >> 8);
    tr_section_t s = tr_section_at(g, seg);
    int max_speed = TR_SPD_MAX;
    int edge = tr_edge(s.width);

    /* Steering. Three wheels: willing, but only while moving. */
    g->steer = 0;
    if (g->spd > 8) {
        int rate = ((g->spd * 3) >> 5) + 2;
        if (input & TR_IN_LEFT) {
            g->x = (int16_t)(g->x - rate);
            g->steer = -1;
        }
        if (input & TR_IN_RIGHT) {
            g->x = (int16_t)(g->x + rate);
            g->steer = (int8_t)(g->steer + 1);
        }
    }
    /* The bend pushes outward, harder with speed. */
    g->curve_now = s.curve;
    g->x = (int16_t)(g->x - (s.curve * g->spd >> 6));

    /* The load shifts in bends. Past a point, a melon leaves. */
    if (g->melons) {
        int force = tr_abs(s.curve) * g->spd;
        if (force > 520) g->slosh = (int16_t)(g->slosh + ((force - 520) >> 5));
        else if (g->slosh > 0) g->slosh = (int16_t)(g->slosh - 2);
        if (g->slosh < 0) g->slosh = 0;
    } else {
        g->slosh = 0;
    }

    /* Off the tarmac: walls and the sea stop you, everything else just slows you. */
    g->off_road = 0;
    if (g->x > edge || g->x < -edge) {
        int ground = g->x > 0 ? s.ground_r : s.ground_l;
        if (tr_blocked_ground(ground)) {
            int limit = edge - 8;
            g->x = (int16_t)(g->x > 0 ? limit : -limit);
            if (g->spd > 40) {
                g->spd = (int16_t)(g->spd - 3);
                if ((g->ticks & 7u) == 0) tr_event(g, EV_SCRAPE, g->x, 0);
                if (g->melons) g->slosh = (int16_t)(g->slosh + 5);
            }
        } else {
            g->off_road = 1;
            max_speed = 66;
            if (g->spd > 66) {
                g->spd = (int16_t)(g->spd - 4);
                if (g->melons) g->slosh = (int16_t)(g->slosh + 6);
            }
            if (g->x > edge + 150) g->x = (int16_t)(edge + 150);
            if (g->x < -edge - 150) g->x = (int16_t)(-edge - 150);
        }
    }
    if (g->spd > max_speed) g->spd = (int16_t)max_speed;

    if (g->slosh >= 256) {
        g->slosh = 90;
        tr_spill(g, 1, g->spd, s.curve > 0 ? -1 : 1);
    }

    /* The horn: thieves scatter, and the car in front may even move over. */
    if (g->horn_cooldown) g->horn_cooldown--;
    if (g->horn) g->horn--;
    if ((input & TR_IN_HORN) && !g->horn_cooldown) {
        g->horn_cooldown = 24;
        g->horn = 8;
        tr_event(g, EV_HORN, g->x, 0);
        for (int i = 0; i < TR_MAX_THIEVES; ++i) {
            tr_thief_t *t = &g->thieves[i];
            if (t->state == THIEF_COMING && t->z - g->pos < 40 * 256) {
                t->state = THIEF_FLEEING;
                t->anim = 0;
            }
        }
        for (int i = 0; i < TR_MAX_CARS; ++i) {
            tr_car_t *c = &g->cars[i];
            if (c->kind == CAR_NONE || c->kind == CAR_TRUCK) continue;
            int dz = c->z - (g->pos + TR_PLAYER_Z);
            if (dz > 0 && dz < 16 * 256 && tr_abs(c->x - g->x) < 110) {
                int lane = 128 * s.width / 16;
                c->target_x = (int16_t)(c->x > g->x ? lane : -lane);
            }
        }
    }

    /* Forward. */
    g->pos += g->spd;
    if (g->bump) g->bump--;
    uint32_t now = (uint32_t)((g->pos + TR_PLAYER_Z) >> 8);
    for (uint32_t k = g->last_seg + 1; k <= now; ++k) tr_cross_segment(g, k);
    g->last_seg = now;

    tr_spawn_traffic(g);
    tr_traffic_update(g);
    tr_collide_cars(g);
    tr_loose_update(g);
    tr_thieves_update(g);

    if (now >= g->length) {
        uint32_t left_s = left / TR_TICKS_PER_SEC;
        tr_score(g, left_s * 20u + (uint32_t)g->melons * 50u);
        g->phase = PH_ARRIVE;
        g->phase_timer = 60;
        tr_event(g, EV_ARRIVE, 0, left_s);
        return;
    }
    /* An empty Ape that delivered nothing has no reason to go on. One that has
     * delivered everything it could still has a beach to reach. */
    if (g->level >= 1 && !g->delivered && !tr_melons_alive(g)) g->phase = PH_NOMELONS;
}

/* ---- the autoplayer: attract mode, tests and the balance study --------------------- */

static uint32_t tr_bot_input(const tr_game_t *g) {
    uint32_t in = TR_IN_GAS;
    int player_z = g->pos + TR_PLAYER_Z;
    uint32_t seg = (uint32_t)(player_z >> 8);
    tr_section_t here = tr_section_at(g, seg);
    tr_section_t soon = tr_section_at(g, seg + 12);
    int lane = 128 * here.width / 16;
    int best_cost = 1 << 30, target = g->x;
    int candidates[5];
    candidates[0] = -lane; candidates[1] = -lane / 2; candidates[2] = 0; candidates[3] = lane / 2; candidates[4] = lane;
    for (int k = 0; k < 5; ++k) {
        int x = candidates[k], cost = tr_abs(x - g->x) / 8;
        for (int i = 0; i < TR_MAX_CARS; ++i) {
            const tr_car_t *c = &g->cars[i];
            if (c->kind == CAR_NONE) continue;
            int dz = c->z - player_z;
            if (dz > -60 && dz < 18 * 256 && tr_abs(c->x - x) < tr_car_half(c->kind) + 60) cost += 400 - dz / 16;
        }
        for (int d = 1; d <= 9; ++d) {
            tr_section_t s = tr_section_at(g, seg + (uint32_t)d);
            int hole = tr_pothole_x(g, seg + (uint32_t)d, s.holes, s.width);
            if (hole != -9999 && tr_abs(hole - x) < 84) cost += 200;
        }
        for (int i = 0; i < TR_MAX_LOOSE; ++i) {
            const tr_loose_t *m = &g->loose[i];
            if (m->state != MELON_FREE && m->z > player_z && m->z - player_z < 22 * 256 && tr_abs(m->x - x) < 60) cost -= 150;
        }
        for (int i = 0; i < g->anchor_count; ++i) {
            if ((g->anchor_taken >> i) & 1u) continue;
            const uint8_t *a = anchor_data + (g->anchor_first + i) * 4;
            int aseg = a[1] | (a[2] << 8), where = (int8_t)a[3];
            int d = aseg - (int)seg;
            if (d < 1 || d > 30) continue;
            if (a[0] == ANCHOR_STALL) {
                if (where * x > 40 && g->melons) cost -= 300;
            } else if (g->food_next < TR_FOODS && tr_abs(where - x) < 60) {
                cost -= 300;
            }
        }
        if (cost < best_cost) {
            best_cost = cost;
            target = x;
        }
    }
    int diff = target - g->x;
    if (diff > 8) in |= TR_IN_RIGHT;
    else if (diff < -8) in |= TR_IN_LEFT;
    /* Brake for the bend when loaded; the load is the job. */
    int curve = tr_abs(here.curve) > tr_abs(soon.curve) ? tr_abs(here.curve) : tr_abs(soon.curve);
    int limit = g->melons ? 510 : 1100;
    if (curve * g->spd > limit) in = (in & ~TR_IN_GAS) | TR_IN_BRAKE;
    for (int i = 0; i < TR_MAX_CARS; ++i) {
        const tr_car_t *c = &g->cars[i];
        if (c->kind == CAR_NONE) continue;
        int dz = c->z - player_z;
        if (dz > 0 && dz < 7 * 256 && tr_abs(c->x - g->x) < tr_car_half(c->kind) + 50 && g->spd > c->spd) {
            in = (in & ~TR_IN_GAS) | TR_IN_BRAKE;
            if (!g->horn_cooldown) in |= TR_IN_HORN;   /* the Neapolitan indicator */
        }
    }
    /* Thieves on their way to a melon get the horn too. */
    for (int i = 0; i < TR_MAX_THIEVES; ++i)
        if (g->thieves[i].state == THIEF_COMING && !g->horn_cooldown) in |= TR_IN_HORN;
    return in;
}

#endif
