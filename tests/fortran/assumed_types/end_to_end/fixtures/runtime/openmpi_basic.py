"""Executed by the Open MPI integration test under two or more ranks."""

import numpy as np

from prik_openmpi_f08 import mpi_f08 as mpi


mpi.mpi_init()
assert isinstance(mpi.mpi_comm_world, mpi.Mpi_Comm)
assert isinstance(mpi.mpi_int, mpi.Mpi_Datatype)
assert isinstance(mpi.mpi_sum, mpi.Mpi_Op)
assert isinstance(mpi.mpi_status_ignore, mpi.Mpi_Status)
rank, rank_error = mpi.mpi_comm_rank(mpi.mpi_comm_world)
size, size_error = mpi.mpi_comm_size(mpi.mpi_comm_world)
rank, size = int(rank), int(size)
assert rank_error is None and size_error is None and size >= 2
mpi.mpi_barrier(mpi.mpi_comm_world)

if rank == 0:
    sent = np.array([3, 5, 7, 11], dtype=np.int32)
    mpi.mpi_send(sent, np.int32(sent.size), mpi.mpi_int, np.int32(1), np.int32(13), mpi.mpi_comm_world)
elif rank == 1:
    received = np.empty(4, dtype=np.int32)
    mpi.mpi_recv(
        received,
        np.int32(received.size),
        mpi.mpi_int,
        np.int32(0),
        np.int32(13),
        mpi.mpi_comm_world,
        mpi.mpi_status_ignore,
    )
    np.testing.assert_array_equal(received, [3, 5, 7, 11])

values = np.array([rank + 1, rank + 2], dtype=np.int32)
expected = np.array([size * (size + 1) // 2, size * (size + 3) // 2], dtype=np.int32)
reduced = np.empty_like(values)
mpi.mpi_allreduce(values, reduced, np.int32(values.size), mpi.mpi_int, mpi.mpi_sum, mpi.mpi_comm_world)
np.testing.assert_array_equal(reduced, expected)
floats = np.array([float(rank + 1)], dtype=np.float64)
float_reduced = np.empty_like(floats)
mpi.mpi_allreduce(
    floats,
    float_reduced,
    np.int32(floats.size),
    mpi.mpi_double_precision,
    mpi.mpi_sum,
    mpi.mpi_comm_world,
)
np.testing.assert_array_equal(float_reduced, [float(expected[0])])

in_place = values.copy()
assert isinstance(mpi.mpi_in_place, np.ndarray) and mpi.mpi_in_place.shape == ()
mpi.mpi_allreduce(
    mpi.mpi_in_place,
    in_place,
    np.int32(in_place.size),
    mpi.mpi_int,
    mpi.mpi_sum,
    mpi.mpi_comm_world,
)
np.testing.assert_array_equal(in_place, expected)
mpi.mpi_finalize()
print(f"Open MPI rank {rank}: communication passed", flush=True)
