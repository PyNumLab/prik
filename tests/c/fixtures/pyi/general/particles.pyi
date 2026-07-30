from x2py.contracts import CStruct, Float64, Int, private

class particle(CStruct):
    id: Int
    x: Float64[3]

current_particle: private[particle]

def particle_touch(
    p: particle
) -> None: ...

def particle_reset(
    p: particle
) -> None: ...

def particle_move(
    p: particle,
    delta: Float64[3]
) -> None: ...

def particle_current() -> particle: ...
