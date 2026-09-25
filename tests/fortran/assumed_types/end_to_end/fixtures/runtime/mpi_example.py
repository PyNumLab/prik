import numpy as np

import prik_mpi as MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Python objects travel pickled.
if rank == 0:
    comm.send({"a": 7, "b": 3.14}, dest=1, tag=11)
elif rank == 1:
    data = comm.recv(source=0, tag=11)
    print(f"rank 1 received {data}")

# NumPy arrays travel as buffers, with an explicit MPI datatype ...
if rank == 0:
    data = np.arange(4, dtype="i")
    comm.Send([data, MPI.INT], dest=1, tag=77)
elif rank == 1:
    data = np.empty(4, dtype="i")
    status = MPI.Status()
    comm.Recv([data, MPI.INT], source=MPI.ANY_SOURCE, tag=77, status=status)
    print(f"rank 1 received {data.tolist()} from rank {status.Get_source()}")

# ... or with the datatype taken from the array.
data = np.arange(3, dtype=np.float64) if rank == 0 else np.empty(3, dtype=np.float64)
comm.Bcast(data, root=0)

# Collectives: every rank contributes.
values = np.array([rank + 1, rank + 2], dtype="i")
total = np.empty_like(values)
comm.Allreduce(values, total, op=MPI.SUM)
largest = np.empty_like(values)
comm.Reduce(values, largest, op=MPI.MAX, root=0)
comm.Allreduce(MPI.IN_PLACE, values, op=MPI.SUM)

comm.Barrier()
print(f"rank {rank} of {size}: bcast {data.tolist()}, sum {total.tolist()}, in place {values.tolist()}")
if rank == 0:
    print(f"rank 0 max {largest.tolist()}")
