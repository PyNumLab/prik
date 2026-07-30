#ifndef X2PY_GENERAL_PARTICLES_H
#define X2PY_GENERAL_PARTICLES_H

struct particle {
    int id;
    double x[3];
};

typedef struct particle particle;
typedef struct particle *particle_handle;

void particle_touch(struct particle *p);
void particle_reset(particle *p);
void particle_move(particle *p, const double delta[static 3]);
const struct particle *particle_current(void);

#endif
