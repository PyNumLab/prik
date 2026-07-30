#include "modern_math_physics.h"

#include <math.h>

int modern_counter = 0;
static double hidden_scale = 1.0;

void init_particle(modern_particle *p, int pid, double mass, double x, double y, double z)
{
    p->id = pid;
    p->mass = mass;
    p->position[0] = x;
    p->position[1] = y;
    p->position[2] = z;
    modern_counter += 1;
}

double kinetic_energy(const modern_particle *p, double vx, double vy, double vz)
{
    return 0.5 * p->mass * (vx * vx + vy * vy + vz * vz) * hidden_scale;
}

void scale_vector(int n, double v[static 1], double alpha)
{
    for (int i = 0; i < n; ++i) {
        v[i] = alpha * v[i];
    }
}

double dot3(const double a[static 3], const double b[static 3])
{
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

void fill_identity3_modern(double a[static 3][3])
{
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            a[row][col] = row == col ? 1.0 : 0.0;
        }
    }
}

void normalize_particle(modern_particle *p)
{
    double n = sqrt(dot3(p->position, p->position));
    if (n > 0.0) {
        p->position[0] /= n;
        p->position[1] /= n;
        p->position[2] /= n;
    }
}
