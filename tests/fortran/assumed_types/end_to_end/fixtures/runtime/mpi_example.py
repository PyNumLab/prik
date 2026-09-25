import numpy as np

from prik_openmpi_f08 import mpi_f08 as mpi

mpi.mpi_init()
world = mpi.mpi_comm_world

rank, _ = mpi.mpi_comm_rank(world)
size, _ = mpi.mpi_comm_size(world)
rank, size = int(rank), int(size)

# Point to point: rank 0 sends four integers, rank 1 receives them.
if rank == 0:
    sent = np.array([3, 5, 7, 11], dtype=np.int32)
    mpi.mpi_send(sent, np.int32(sent.size), mpi.mpi_int, np.int32(1), np.int32(13), world)
elif rank == 1:
    received = np.empty(4, dtype=np.int32)
    mpi.mpi_recv(
        received,
        np.int32(received.size),
        mpi.mpi_int,
        np.int32(0),
        np.int32(13),
        world,
        mpi.mpi_status_ignore,
    )
    print(f"rank 1 received {received.tolist()}")

# Collective: every rank contributes and every rank receives the sum.
values = np.array([rank + 1, rank + 2], dtype=np.int32)
reduced = np.empty_like(values)
mpi.mpi_allreduce(values, reduced, np.int32(values.size), mpi.mpi_int, mpi.mpi_sum, world)

readings = np.array([20.0 + rank], dtype=np.float64)
total = np.empty_like(readings)
mpi.mpi_allreduce(readings, total, np.int32(readings.size), mpi.mpi_double_precision, mpi.mpi_sum, world)

# In place: MPI_IN_PLACE as the send buffer reduces the receive buffer itself.
in_place = values.copy()
mpi.mpi_allreduce(mpi.mpi_in_place, in_place, np.int32(in_place.size), mpi.mpi_int, mpi.mpi_sum, world)

mpi.mpi_barrier(world)
print(f"rank {rank} of {size}: sum {reduced.tolist()}, in place {in_place.tolist()}, total {total.tolist()}")
mpi.mpi_finalize()
