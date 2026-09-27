"""Compare the tutorial's three APIs against one Open MPI installation.

Run each backend separately with two ranks from the directory containing the
generated extension and ``prik_mpi.py``. Rank zero prints one JSON record.
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import timeit

import mpi4py
import numpy as np


def aligned_int32(size: int, byte_offset: int) -> np.ndarray:
    """Give each backend the same buffer placement modulo 4 KiB."""
    page_bytes = 4_096
    item_bytes = np.dtype(np.int32).itemsize
    backing = np.empty(size + page_bytes // item_bytes, dtype=np.int32)
    start = ((byte_offset - backing.ctypes.data % page_bytes) % page_bytes) // item_bytes
    return backing[start : start + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", choices=("wrapped", "python", "mpi4py"))
    backend = parser.parse_args().backend

    if backend != "mpi4py":
        mpi4py.rc.initialize = False
        mpi4py.rc.finalize = False
    from mpi4py import MPI as timer_mpi

    if backend == "wrapped":
        from prik_openmpi_f08 import mpi_f08 as mpi

        mpi.init()
        atexit.register(mpi.finalize)
        comm = mpi.mpi_comm_world

        def barrier() -> None:
            mpi.barrier(comm)

        rank = int(mpi.comm_rank(comm))
        ranks = int(mpi.comm_size(comm))
        datatype = mpi.mpi_int
        op = mpi.mpi_sum
        rank_fn = mpi.comm_rank
        barrier_fn = mpi.barrier
        allreduce_fn = mpi.allreduce
        rank_call = "rank_fn(comm)"
        barrier_call = "barrier_fn(comm)"
        allreduce_call = "allreduce_fn(send, recv, datatype, op, comm)"
    elif backend == "python":
        import prik_mpi as mpi

        comm = mpi.COMM_WORLD
        barrier = comm.Barrier
        rank = int(comm.Get_rank())
        ranks = int(comm.Get_size())
        datatype = None
        op = mpi.SUM
        rank_fn = comm.Get_rank
        barrier_fn = comm.Barrier
        allreduce_fn = comm.Allreduce
        rank_call = "rank_fn()"
        barrier_call = "barrier_fn()"
        allreduce_call = "allreduce_fn(send, recv, op=op)"
    else:
        mpi = timer_mpi
        comm = mpi.COMM_WORLD
        barrier = comm.Barrier
        rank = int(comm.Get_rank())
        ranks = int(comm.Get_size())
        datatype = None
        op = mpi.SUM
        rank_fn = comm.Get_rank
        barrier_fn = comm.Barrier
        allreduce_fn = comm.Allreduce
        rank_call = "rank_fn()"
        barrier_call = "barrier_fn()"
        allreduce_call = "allreduce_fn(send, recv, op=op)"

    results: dict[str, float] = {}

    def measure(
        statement: str, iterations: int, *, send: np.ndarray | None = None, recv: np.ndarray | None = None
    ) -> float:
        timer = timeit.Timer(
            statement,
            timer=timer_mpi.Wtime,
            globals={
                "comm": comm,
                "send": send,
                "recv": recv,
                "datatype": datatype,
                "op": op,
                "rank_fn": rank_fn,
                "barrier_fn": barrier_fn,
                "allreduce_fn": allreduce_fn,
            },
        )
        barrier()
        timer.timeit(number=min(iterations, 100))
        samples = []
        for _ in range(5):
            barrier()
            samples.append(timer.timeit(number=iterations) * 1e9 / iterations)
            barrier()
        return min(samples)

    for size, iterations in ((1, 20_000), (1_024, 20_000), (1_048_576, 8)):
        send = aligned_int32(size, 0)
        send.fill(rank + 1)
        recv = aligned_int32(size, 2_048)
        results[f"allreduce_{size}"] = measure(allreduce_call, iterations, send=send, recv=recv)
        expected = ranks * (ranks + 1) // 2
        if int(recv[0]) != expected or int(recv[-1]) != expected:
            raise AssertionError(f"Allreduce produced an incorrect result for {size} values")

    results["barrier"] = measure(barrier_call, 20_000)
    results["get_rank"] = measure(rank_call, 200_000)
    if rank == 0:
        print(
            json.dumps(
                {
                    "backend": backend,
                    "mpi_version": os.environ.get("OPENMPI_VERSION"),
                    "timer": "mpi4py.MPI.Wtime",
                    "ranks": ranks,
                    "ns_per_call": results,
                }
            )
        )


if __name__ == "__main__":
    main()
