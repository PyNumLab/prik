from x2py.contracts import CStruct, Float64, Int, private

class modern_particle(CStruct):
    id: Int
    mass: Float64
    position: Float64[3]

class vector3(CStruct):
    values: Float64[3]

modern_counter: Int

hidden_scale: private[Float64] = 1.0

def init_particle(
    p: modern_particle,
    pid: Int,
    mass: Float64,
    x: Float64,
    y: Float64,
    z: Float64
) -> None: ...

def kinetic_energy(
    p: modern_particle,
    vx: Float64,
    vy: Float64,
    vz: Float64
) -> Float64: ...

def scale_vector(
    n: Int,
    v: Float64[1],
    alpha: Float64
) -> None: ...

def dot3(
    a: Float64[3],
    b: Float64[3]
) -> Float64: ...

def fill_identity3_modern(
    a: Float64[3, 3]
) -> None: ...

def normalize_particle(
    p: modern_particle
) -> None: ...
