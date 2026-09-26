"""An mpi4py-style Python API over the PRIK-generated Open MPI extension.

It illustrates the shape of mpi4py rather than all of it: every buffer is an
np.int32 array sent as MPI_INT, and no receive reports a status.
"""

import atexit

import numpy as np

from prik_openmpi_f08 import mpi_f08 as _mpi

# Ranks and tags are np.int32, the type the contract takes: the extension
# returns them as np.int32, and so are these constants and defaults.
ANY_SOURCE = _mpi.mpi_any_source
ANY_TAG = _mpi.mpi_any_tag
IN_PLACE = _mpi.mpi_in_place
SUM = _mpi.mpi_sum
MAX = _mpi.mpi_max
_ZERO = np.int32(0)
_INT = _mpi.mpi_int
_STATUS_IGNORE = _mpi.mpi_status_ignore


class Comm:
    """A communicator, with the methods mpi4py spells for it."""

    def __init__(self, handle):
        self.handle = handle

    def Get_rank(self):
        return _mpi.comm_rank(self.handle)

    def Get_size(self):
        return _mpi.comm_size(self.handle)

    def Barrier(self):
        _mpi.barrier(self.handle)

    def Send(self, buf, dest, tag=_ZERO):
        _mpi.send(buf, _INT, dest, tag, self.handle)

    def Recv(self, buf, source=ANY_SOURCE, tag=ANY_TAG):
        _mpi.recv(buf, _INT, source, tag, self.handle, _STATUS_IGNORE)

    def Bcast(self, buf, root=_ZERO):
        _mpi.bcast(buf, _INT, root, self.handle)

    def Reduce(self, sendbuf, recvbuf, op=SUM, root=_ZERO):
        _mpi.reduce(sendbuf, recvbuf, _INT, op, root, self.handle)

    def Allreduce(self, sendbuf, recvbuf, op=SUM):
        _mpi.allreduce(sendbuf, recvbuf, _INT, op, self.handle)


COMM_WORLD = Comm(_mpi.mpi_comm_world)

# Like mpi4py, MPI starts when this module is imported and stops at exit.
_mpi.init()
atexit.register(_mpi.finalize)
