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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", choices=("direct", "facade", "mpi4py"))
    backend = parser.parse_args().backend

    if backend != "mpi4py":
        mpi4py.rc.initialize = False
        mpi4py.rc.finalize = False
    from mpi4py import MPI as timer_mpi

    if backend == "direct":
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
        rank_call = "mpi.comm_rank(comm)"
        barrier_call = "mpi.barrier(comm)"
        allreduce_call = "mpi.allreduce(send, recv, datatype, op, comm)"
    elif backend == "facade":
        import prik_mpi as mpi

        comm = mpi.COMM_WORLD
        barrier = comm.Barrier
        rank = int(comm.Get_rank())
        ranks = int(comm.Get_size())
        datatype = None
        op = mpi.SUM
        rank_call = "comm.Get_rank()"
        barrier_call = "comm.Barrier()"
        allreduce_call = "comm.Allreduce(send, recv, op=op)"
    else:
        mpi = timer_mpi
        comm = mpi.COMM_WORLD
        barrier = comm.Barrier
        rank = int(comm.Get_rank())
        ranks = int(comm.Get_size())
        datatype = None
        op = mpi.SUM
        rank_call = "comm.Get_rank()"
        barrier_call = "comm.Barrier()"
        allreduce_call = "comm.Allreduce(send, recv, op=op)"

    results: dict[str, float] = {}

    def measure(
        statement: str, iterations: int, *, send: np.ndarray | None = None, recv: np.ndarray | None = None
    ) -> float:
        timer = timeit.Timer(
            statement,
            timer=timer_mpi.Wtime,
            globals={"mpi": mpi, "comm": comm, "send": send, "recv": recv, "datatype": datatype, "op": op},
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
        send = np.full(size, rank + 1, dtype=np.int32)
        recv = np.empty_like(send)
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
