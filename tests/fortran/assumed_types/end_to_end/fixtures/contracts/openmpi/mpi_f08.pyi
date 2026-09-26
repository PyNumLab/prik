from prik.contracts import Annotated, AnyNative, Arg, Flat, Hidden, Int32, ReadOnly, Return, bind, native_call, raises
from .mpi_f08_types import (
    Mpi_Comm,
    Mpi_Datatype,
    Mpi_Op,
    Mpi_Status,
    mpi_any_source,
    mpi_any_tag,
    mpi_comm_world,
    mpi_in_place,
    mpi_int,
    mpi_max,
    mpi_status_ignore,
    mpi_sum,
)

@raises(status="ierror", success=0)
@bind("MPI_Init")
@native_call([Hidden("ierror", Int32)])
def init() -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Finalize")
@native_call([Hidden("ierror", Int32)])
def finalize() -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Comm_rank")
@native_call([Arg(0), Return("rank", 0), Hidden("ierror", Int32)])
def comm_rank(comm: Mpi_Comm) -> Int32: ...

@raises(status="ierror", success=0)
@bind("MPI_Comm_size")
@native_call([Arg(0), Return("size", 0), Hidden("ierror", Int32)])
def comm_size(comm: Mpi_Comm) -> Int32: ...

@raises(status="ierror", success=0)
@bind("MPI_Barrier")
@native_call([Arg(0), Hidden("ierror", Int32)])
def barrier(comm: Mpi_Comm) -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Send")
@native_call([Arg(0), Int32(Arg(0).size), Arg(1), Arg(2), Arg(3), Arg(4), Hidden("ierror", Int32)])
def send(
    buf: Annotated[AnyNative[Flat], ReadOnly],
    datatype: Mpi_Datatype,
    dest: Int32,
    tag: Int32,
    comm: Mpi_Comm,
) -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Recv")
@native_call([Arg(0), Int32(Arg(0).size), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Hidden("ierror", Int32)])
def recv(
    buf: AnyNative[Flat],
    datatype: Mpi_Datatype,
    source: Int32,
    tag: Int32,
    comm: Mpi_Comm,
    status: Mpi_Status,
) -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Bcast")
@native_call([Arg(0), Int32(Arg(0).size), Arg(1), Arg(2), Arg(3), Hidden("ierror", Int32)])
def bcast(buffer: AnyNative[Flat], datatype: Mpi_Datatype, root: Int32, comm: Mpi_Comm) -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Reduce")
@native_call([Arg(0), Arg(1), Int32(Arg(1).size), Arg(2), Arg(3), Arg(4), Arg(5), Hidden("ierror", Int32)])
def reduce(
    sendbuf: Annotated[AnyNative[Flat], ReadOnly],
    recvbuf: AnyNative[Flat],
    datatype: Mpi_Datatype,
    op: Mpi_Op,
    root: Int32,
    comm: Mpi_Comm,
) -> None: ...

@raises(status="ierror", success=0)
@bind("MPI_Allreduce")
@native_call([Arg(0), Arg(1), Int32(Arg(1).size), Arg(2), Arg(3), Arg(4), Hidden("ierror", Int32)])
def allreduce(
    sendbuf: Annotated[AnyNative[Flat], ReadOnly],
    recvbuf: AnyNative[Flat],
    datatype: Mpi_Datatype,
    op: Mpi_Op,
    comm: Mpi_Comm,
) -> None: ...

__all__ = [
    "init",
    "finalize",
    "comm_rank",
    "comm_size",
    "barrier",
    "send",
    "recv",
    "bcast",
    "reduce",
    "allreduce",
    "Mpi_Comm",
    "Mpi_Datatype",
    "Mpi_Op",
    "Mpi_Status",
    "mpi_any_source",
    "mpi_any_tag",
    "mpi_comm_world",
    "mpi_in_place",
    "mpi_int",
    "mpi_max",
    "mpi_status_ignore",
    "mpi_sum",
]
