from x2py.contracts import Addr, Arg, Float64, Int32, native_call

class particle:
    def __init__(
        self,
        *,
        id: Int32 = ...,
        mass: Float64 = ...
    ) -> None: ...

    id: Int32
    mass: Float64
    position: Float64[3]

class vector3:
    def __init__(self) -> None: ...

    values: Float64[3]

counter: Int32

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def init_particle(
    p: particle,
    pid: Int32,
    mass: Float64,
    x: Float64,
    y: Float64,
    z: Float64
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3))])
def kinetic_energy(
    p: particle,
    vx: Float64,
    vy: Float64,
    vz: Float64
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def scale_vector(
    v: Float64[::],
    alpha: Float64
) -> None: ...

def dot3(
    a: Float64[3],
    b: Float64[3]
) -> Float64: ...

def fill_identity3(
    a: Float64[3, 3]
) -> None: ...

def normalize_particle(
    p: particle
) -> None: ...
