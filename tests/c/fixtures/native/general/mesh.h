#ifndef X2PY_GENERAL_MESH_H
#define X2PY_GENERAL_MESH_H

#include <stddef.h>

struct node {
    int id;
    double xyz[3];
};

struct mesh {
    size_t nnodes;
    struct node *nodes;
};

typedef struct node node;
typedef struct mesh mesh;

void node_move(struct node *node, const double delta[static 3]);
int mesh_init(struct mesh *mesh, size_t nnodes);
void mesh_clear(struct mesh *mesh);
struct node *mesh_node_at(struct mesh *mesh, size_t index);

#endif
