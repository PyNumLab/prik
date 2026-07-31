from x2py.contracts import Addr, CStruct, Float64, Int, SizeT

class node(CStruct):
    id: Int
    xyz: Float64[3]

class mesh(CStruct):
    nnodes: SizeT
    nodes: Addr(node)

def node_move(
    node: node,
    delta: Float64[3]
) -> None: ...

def mesh_init(
    mesh: mesh,
    nnodes: SizeT
) -> Int: ...

def mesh_clear(
    mesh: mesh
) -> None: ...

def mesh_node_at(
    mesh: mesh,
    index: SizeT
) -> node: ...
