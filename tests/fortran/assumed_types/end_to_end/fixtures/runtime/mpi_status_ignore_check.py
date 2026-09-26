"""Open MPI receives MPI_STATUS_IGNORE as the predefined object itself.

PRIK passes a module variable argument as that variable's own storage. Open
MPI fills in every status it is given except MPI_STATUS_IGNORE, which it
recognizes by that address, so a receive through it leaves it untouched while
an ordinary status is filled in.
"""

import numpy as np

from prik_openmpi_f08 import mpi_f08 as mpi

mpi.init()
world = mpi.mpi_comm_world
ignore = mpi.mpi_status_ignore
if int(mpi.comm_rank(world)) == 0:
    for tag in (21, 22):
        mpi.send(np.arange(2, dtype=np.int32), mpi.mpi_int, np.int32(1), np.int32(tag), world)
else:
    data = np.empty(2, dtype=np.int32)
    status = mpi.Mpi_Status()
    mpi.recv(data, mpi.mpi_int, np.int32(0), np.int32(21), world, status)
    before = int(ignore.mpi_tag)
    mpi.recv(data, mpi.mpi_int, np.int32(0), np.int32(22), world, ignore)
    unchanged = int(ignore.mpi_tag) == before
    print(f"{type(ignore).__name__}: status tag {int(status.mpi_tag)}, ignored status unchanged {unchanged}")
mpi.finalize()
