#include "particles.h"

static struct particle current_particle;

void particle_touch(struct particle *p)
{
    if (p != 0) {
        current_particle = *p;
    }
}

void particle_reset(particle *p)
{
    if (p != 0) {
        p->id = 0;
        p->x[0] = 0.0;
        p->x[1] = 0.0;
        p->x[2] = 0.0;
    }
}

void particle_move(particle *p, const double delta[static 3])
{
    if (p != 0) {
        p->x[0] += delta[0];
        p->x[1] += delta[1];
        p->x[2] += delta[2];
    }
}

const struct particle *particle_current(void)
{
    return &current_particle;
}
