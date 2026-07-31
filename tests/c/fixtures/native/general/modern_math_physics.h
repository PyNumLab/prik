#ifndef X2PY_GENERAL_MODERN_MATH_PHYSICS_H
#define X2PY_GENERAL_MODERN_MATH_PHYSICS_H

extern int modern_counter;

struct modern_particle {
    int id;
    double mass;
    double position[3];
};

struct vector3 {
    double values[3];
};

typedef struct modern_particle modern_particle;
typedef struct vector3 vector3;

void init_particle(modern_particle *p, int pid, double mass, double x, double y, double z);
double kinetic_energy(const modern_particle *p, double vx, double vy, double vz);
void scale_vector(int n, double v[static 1], double alpha);
double dot3(const double a[static 3], const double b[static 3]);
void fill_identity3_modern(double a[static 3][3]);
void normalize_particle(modern_particle *p);

#endif
