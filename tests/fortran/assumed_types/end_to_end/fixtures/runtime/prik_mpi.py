"""An mpi4py-style Python API over the PRIK-generated Open MPI extension."""

import atexit
import pickle

import numpy as np

from prik_openmpi_f08 import mpi_f08 as _mpi

# Ranks, tags, and counts are np.int32, the type the contract takes, from the
# start: the extension returns them as np.int32, the constants and defaults
# here are np.int32, and arithmetic with Python integers keeps the type. So
# they pass straight to the contract, never converted.
ANY_SOURCE = _mpi.mpi_any_source
ANY_TAG = _mpi.mpi_any_tag
_ZERO = np.int32(0)
IN_PLACE = _mpi.mpi_in_place
STATUS_IGNORE = _mpi.mpi_status_ignore
BYTE = _mpi.mpi_byte
INT = _mpi.mpi_int
DOUBLE = _mpi.mpi_double
SUM = _mpi.mpi_sum
MAX = _mpi.mpi_max

# The MPI datatype of each NumPy element type, for buffers given without one.
_DATATYPES = {np.dtype(np.uint8): BYTE, np.dtype(np.int32): INT, np.dtype(np.float64): DOUBLE}

def _message(buf):
    """Return a buffer's array and MPI datatype; ``buf`` is an array or ``[array, datatype]``."""
    if isinstance(buf, np.ndarray):
        return buf, _DATATYPES[buf.dtype]
    array, datatype = buf
    return array, datatype


class Status:
    """What MPI reports about a received message, filled in by the call given it."""

    def __init__(self):
        self._native = _mpi.Mpi_Status()

    @property
    def source(self):
        return self._native.mpi_source

    @property
    def tag(self):
        return self._native.mpi_tag

    def Get_source(self):
        return self.source

    def Get_tag(self):
        return self.tag

    def Get_count(self, datatype=BYTE):
        return _mpi.get_count(self._native, datatype)


def _native_status(status):
    """Return the status MPI fills in; without one, MPI_STATUS_IGNORE, as in mpi4py."""
    return STATUS_IGNORE if status is None else status._native


class Comm:
    """A communicator, with the methods mpi4py spells for it."""

    def __init__(self, handle):
        self.handle = handle

    def Get_rank(self):
        return _mpi.comm_rank(self.handle)

    def Get_size(self):
        return _mpi.comm_size(self.handle)

    rank = property(Get_rank)
    size = property(Get_size)

    def Barrier(self):
        _mpi.barrier(self.handle)

    def Send(self, buf, dest, tag=_ZERO):
        array, datatype = _message(buf)
        _mpi.send(array, datatype, dest, tag, self.handle)

    def Recv(self, buf, source=ANY_SOURCE, tag=ANY_TAG, status=None):
        array, datatype = _message(buf)
        _mpi.recv(array, datatype, source, tag, self.handle, _native_status(status))

    def Probe(self, source=ANY_SOURCE, tag=ANY_TAG, status=None):
        _mpi.probe(source, tag, self.handle, _native_status(status))
        return True

    def Bcast(self, buf, root=_ZERO):
        array, datatype = _message(buf)
        _mpi.bcast(array, datatype, root, self.handle)

    def Reduce(self, sendbuf, recvbuf, op=SUM, root=_ZERO):
        array, datatype = _message(recvbuf)
        _mpi.reduce(sendbuf, array, datatype, op, root, self.handle)

    def Allreduce(self, sendbuf, recvbuf, op=SUM):
        array, datatype = _message(recvbuf)
        _mpi.allreduce(sendbuf, array, datatype, op, self.handle)

    # Python objects travel pickled, as with mpi4py's lowercase methods.
    def send(self, obj, dest, tag=_ZERO):
        self.Send(np.frombuffer(pickle.dumps(obj), dtype=np.uint8), dest, tag)

    def recv(self, buf=None, source=ANY_SOURCE, tag=ANY_TAG, status=None):
        status = status if status is not None else Status()
        self.Probe(source, tag, status)
        data = np.empty(status.Get_count(BYTE), dtype=np.uint8)
        self.Recv(data, status.source, status.tag, status)
        return pickle.loads(data.tobytes())


COMM_WORLD = Comm(_mpi.mpi_comm_world)

# Like mpi4py, MPI starts when this module is imported and stops at exit.
_mpi.init()
atexit.register(_mpi.finalize)
