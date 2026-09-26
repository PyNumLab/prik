import numpy as np

import prik_mpi as MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Buffers are np.int32 arrays, and ranks and tags are np.int32 too:
# Get_rank returns one, and rank + 1 stays one.
ROOT = np.int32(0)
TAG = np.int32(77)

# Point to point: rank 0 sends four integers to rank 1.
if rank == 0:
    data = np.arange(4, dtype=np.int32)
    comm.Send(data, dest=rank + 1, tag=TAG)
elif rank == 1:
    data = np.empty(4, dtype=np.int32)
    comm.Recv(data, source=rank - 1, tag=TAG)
    print(f"rank 1 received {data.tolist()}")

# Broadcast: rank 0's values reach every rank.
data = np.arange(3, dtype=np.int32) if rank == 0 else np.empty(3, dtype=np.int32)
comm.Bcast(data, root=ROOT)

# Reductions: every rank contributes.
values = np.array([rank + 1, rank + 2], dtype=np.int32)
total = np.empty_like(values)
comm.Allreduce(values, total, op=MPI.SUM)
largest = np.empty_like(values)
comm.Reduce(values, largest, op=MPI.MAX, root=ROOT)
comm.Allreduce(MPI.IN_PLACE, values, op=MPI.SUM)

comm.Barrier()
print(f"rank {rank} of {size}: bcast {data.tolist()}, sum {total.tolist()}, in place {values.tolist()}")
if rank == 0:
    print(f"rank 0 max {largest.tolist()}")
