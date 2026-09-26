---
title: Wrap Open MPI mpi_f08 for Python
description: Turn a reviewed part of Open MPI's Fortran mpi_f08 interface into an mpi4py-style Python MPI API
audience: users
prerequisites: an Open MPI installation with mpi_f08, and the configured Open MPI source and build trees it was built from
related: ../guide/wrapping-modules.md, ../guide/callbacks.md, ../reference/cli-commands.md, ../reference/pyi-format.md
status: maintained
publication: reviewed
---

# Wrap Open MPI `mpi_f08` for Python

This tutorial turns a reviewed part of Open MPI's real Fortran `mpi_f08`
interface into a Python MPI API modeled on [mpi4py](https://mpi4py.readthedocs.io),
the standard Python binding of MPI. At the end, this program runs under
`mpirun`:

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/runtime/mpi_example.py -->
```python
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
```

If you know mpi4py, you know this program: `COMM_WORLD`, `Get_rank`,
`Send`/`Recv`, `Bcast`, `Reduce`, `Allreduce`, `MPI.SUM`, and `MPI.IN_PLACE`
are all spelled as mpi4py spells them. Replace `import prik_mpi as MPI` with
`from mpi4py import MPI` and the same program runs under mpi4py and prints
the same lines.

Two layers make this work:

- **The extension PRIK generates.** Every MPI routine, handle type, and
  constant the program reaches comes from the declarations in Open MPI's
  Fortran sources, and every call enters the installed Open MPI library through
  generated code. You shape that native API by editing a generated `.pyi`
  contract: hiding counts that follow from the buffers, turning error codes
  into exceptions, returning results instead of filling output arguments.
- **A short Python module, `prik_mpi.py`.** It gives the native API mpi4py's
  shape: a `Comm` class with methods and keyword defaults. It is ordinary
  Python over the generated functions, with no C and no `ctypes`, and it is
  kept small on purpose: an illustration of the approach, not a complete MPI
  binding.

## 1. See what PRIK reads

`mpi_f08` is an ordinary Fortran module that gathers other modules:

```fortran
module mpi_f08
  use mpi_f08_types
  use mpi_f08_interfaces
  use pmpi_f08_interfaces
  use mpi_f08_callbacks
  use mpi_f08_interfaces_callbacks
end module mpi_f08
```

The handle types and predefined objects are declared in those modules:

```fortran
type(MPI_Comm), parameter     :: MPI_COMM_WORLD = MPI_Comm(OMPI_MPI_COMM_WORLD)
type(MPI_Op), parameter       :: MPI_SUM        = MPI_Op(OMPI_MPI_SUM)
type(MPI_Datatype), parameter :: MPI_INT        = MPI_Datatype(OMPI_MPI_INT)

integer MPI_ANY_SOURCE
parameter (MPI_ANY_SOURCE=-1)

integer, bind(C, name="mpi_fortran_in_place_") :: MPI_IN_PLACE
type(MPI_Status), bind(C, name="mpi_fortran_status_ignore_") :: MPI_STATUS_IGNORE
```

and each MPI routine is a generic interface over its specific procedures:

```fortran
interface MPI_Allreduce
  subroutine MPI_Allreduce_f08(sendbuf, recvbuf, count, datatype, op, comm, ierror)
    use :: mpi_f08_types, only : MPI_Datatype, MPI_Op, MPI_Comm
    type(*), dimension(*), intent(in) :: sendbuf
    type(*), dimension(*) :: recvbuf
    integer, intent(in) :: count
    type(MPI_Datatype), intent(in) :: datatype
    type(MPI_Op), intent(in) :: op
    type(MPI_Comm), intent(in) :: comm
    integer, optional, intent(out) :: ierror
  end subroutine MPI_Allreduce_f08
end interface MPI_Allreduce
```

These excerpts are simplified from Open MPI 5.0. PRIK does not need to be
told where each declaration lives. It starts from the entry source
`mpi-f08.F90`, follows every `use` to the source that defines that module, and
continues through the modules those use. File names play no part: Open MPI
declares its types in `mpi_f08_types` in one release series and in a
configure-generated `mpi_types` module in another, and PRIK finds whichever
the sources declare. Some of these declarations, such as `MPI_IN_PLACE` above,
are in headers that Open MPI's `configure` writes into its build tree.

## 2. Choose a small native surface

`mpi_f08` publishes hundreds of routines and constants. Start with a reviewed
subset instead of all of them. Save the Fortran identities to publish in
`mpi_exports.txt`:

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/contracts/openmpi/mpi_exports.txt -->
```text
mpi_f08::MPI_Init
mpi_f08::MPI_Finalize
mpi_f08::MPI_Comm_rank
mpi_f08::MPI_Comm_size
mpi_f08::MPI_Barrier
mpi_f08::MPI_Send
mpi_f08::MPI_Recv
mpi_f08::MPI_Bcast
mpi_f08::MPI_Reduce
mpi_f08::MPI_Allreduce
mpi_f08::MPI_COMM_WORLD
mpi_f08::MPI_INT
mpi_f08::MPI_SUM
mpi_f08::MPI_MAX
mpi_f08::MPI_IN_PLACE
mpi_f08::MPI_STATUS_IGNORE
mpi_f08::MPI_ANY_SOURCE
mpi_f08::MPI_ANY_TAG
```

These are the routines and objects behind the mpi4py names the program uses.
The program does not name `MPI_STATUS_IGNORE`; `Recv` passes it, since this
small API reports no status.

Selecting symbols this way is not an MPI feature. `--export-symbols` accepts
module-qualified public symbols from any Fortran project -- procedures,
generics, and module variables -- and here every name is qualified by
`mpi_f08`, the facade that re-exports it. PRIK publishes exactly those names
and keeps whatever supporting declarations they need, such as the handle types
their signatures name, without publishing the rest of the API.

## 3. Generate the contract

PRIK reads the Fortran declarations from a configured Open MPI source tree and
its build tree, which must be the ones your installed Open MPI was built from;
[why it must match](#why-the-configured-tree-must-match-the-installation)
comes later. Point two shell variables at them:

```bash
OMPI_SRC=/path/to/openmpi-5.0.11
OMPI_BUILD=/path/to/openmpi-5.0.11/build
```

Generate the contract from the one entry source, letting PRIK discover the
modules it uses under both trees:

```bash
python3 -m prik generate --pyi \
  "$OMPI_SRC/ompi/mpi/fortran/use-mpi-f08/mpi-f08.F90" \
  --module-source-dir "$OMPI_SRC" \
  --module-source-dir "$OMPI_BUILD" \
  --export-symbols mpi_exports.txt \
  --out contract \
  --compiler mpifort \
  -I "$OMPI_BUILD" \
  -I "$OMPI_BUILD/ompi/mpi/fortran/use-mpi-f08" \
  -I "$OMPI_BUILD/ompi/mpi/fortran/use-mpi-f08/mod" \
  -I "$OMPI_SRC" \
  -I "$OMPI_BUILD/ompi/include" \
  -I "$OMPI_SRC/ompi/include"
```

The Open MPI sources are preprocessed Fortran that includes headers from both
trees: the hand-written ones stay in the source tree, and the configured ones
are generated into the build tree beside them. The `-I` options name those
directories so PRIK reads each source exactly as the Fortran compiler did.

PRIK reads these sources to learn their declarations. It does not compile
them.

## 4. Read the generated contract

The `contract/` directory holds one editable `.pyi` file per Fortran module the
selection needs. `contract/mpi_f08.pyi` publishes the selected names:

```python
from .mpi_f08_types import mpi_any_source, mpi_any_tag, mpi_comm_world, mpi_in_place, mpi_int, mpi_max, mpi_status_ignore, mpi_sum
from .mpi_f08_interfaces import mpi_allreduce, mpi_barrier, mpi_bcast, mpi_comm_rank, mpi_comm_size, mpi_finalize, mpi_init, mpi_recv, mpi_reduce, mpi_send
from .mpi_types import Mpi_Comm, Mpi_Datatype, Mpi_Op, Mpi_Status
```

These excerpts come from Open MPI 5.0, which declares the handle types in
`mpi_types`. Open MPI 4.1 declares them in `mpi_f08_types`, so there they are
imported from that module and written as `mpi_f08_types.Mpi_Datatype` and so
on. The predefined objects become typed module attributes in
`contract/mpi_f08_types.pyi`:

```python
mpi_any_source: Final[Int32] = -1

mpi_comm_world: Final[Mpi_Comm]

mpi_sum: Final[Mpi_Op]

mpi_int: Final[Mpi_Datatype]

mpi_in_place: Int32[()]

mpi_status_ignore: Mpi_Status
```

and each selected routine keeps its Fortran interface in
`contract/mpi_f08_interfaces.pyi`:

```python
@overload("mpi_allreduce_f08")
def mpi_allreduce(
    sendbuf: Annotated[AnyNative[Flat], ReadOnly],
    recvbuf: AnyNative[Flat],
    count: Int32,
    datatype: mpi_types.Mpi_Datatype,
    op: mpi_types.Mpi_Op,
    comm: mpi_types.Mpi_Comm,
    ierror: Int32[()] = ...
) -> Returns["ierror", Int32[()]] | None: ...
```

`MPI_Allreduce` is a generic whose one specific is `MPI_Allreduce_f08`, so
`mpi_allreduce` is an overload of the specific declared as `mpi_allreduce_f08`
in the same file, and a call to it calls that specific.

Four mappings are worth a closer look.

**Handles are concrete types.** `Mpi_Comm`, `Mpi_Datatype`, `Mpi_Op`, and
`Mpi_Status` are the derived types Open MPI declares, with their real
components. For example, `Mpi_Comm` holds the one integer handle Open MPI
stores, and `Mpi_Status` the source, tag, and error of a message:

```python
class Mpi_Status:
    def __init__(
        self,
        *,
        mpi_source: Int32 = ...,
        mpi_tag: Int32 = ...,
        mpi_error: Int32 = ...
    ) -> None: ...

    mpi_source: Int32
    mpi_tag: Int32
    mpi_error: Int32
```

A handle argument accepts only an object of its own type, and the predefined
handles are `Final` module constants.

**`MPI_IN_PLACE` is native storage.** Its declaration is a C-bound integer
module variable, so it becomes rank-zero native integer storage, `Int32[()]`.
Python sees `mpi_in_place` as a live NumPy scalar view of Open MPI's own
`MPI_IN_PLACE` variable. Passing that view as a buffer passes the address of
that variable, which is how Open MPI recognizes an in-place operation.
Nothing here knows about MPI: it is the same mapping any Fortran module
variable declared this way receives.

**`MPI_STATUS_IGNORE` is an `Mpi_Status` object.** It is declared as a
C-bound module variable of type `MPI_Status`, so it keeps that type: it is not
a generic buffer, and it is accepted wherever an `Mpi_Status` is. Passing a
module variable passes the variable itself, not a copy, so Open MPI receives
its own `MPI_STATUS_IGNORE` and recognizes it by address.

**Choice buffers are `AnyNative`.** The send and receive buffers of MPI
routines are `type(*)` dummies, which accept data of any type, so they become
`AnyNative[Flat]`: any NumPy array, passed as a raw address. `AnyNative`
appears only for these assumed-type dummies; `MPI_IN_PLACE` is a concrete
module object with a concrete type.

This contract already builds, and its functions are Fortran's: every count
is an argument, every routine takes and returns the optional `ierror`, and
`MPI_Comm_rank` returns the rank together with that error code.

## 5. Edit the facade into a Python API

The contract is yours to edit. Replace `contract/mpi_f08.pyi`, the facade the
extension publishes, with this one:

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/contracts/openmpi/mpi_f08.pyi -->
```python
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
```

Each function still calls the Fortran routine it names; only its Python face
changes. `@native_call` lists the native arguments in Fortran order and says
where each one comes from:

| Edit | Example | Effect in Python |
| --- | --- | --- |
| `@bind("MPI_Send")` on `def send` | every function | The Python name differs from the Fortran name it calls. |
| `Int32(Arg(0).size)` | `count` of `MPI_Send` | The count is computed from the buffer, so the caller does not pass it. |
| `Return("rank", 0)` | `rank` of `MPI_Comm_rank` | The output argument becomes the return value: `comm_rank` returns the rank. |
| `Hidden("ierror", Int32)` with `@raises(status="ierror", success=0)` | every function | The error code is not an argument; a nonzero code raises an exception. |

`recv` keeps its `status` as an argument. A caller that wants the status
passes an `Mpi_Status` for Open MPI to fill in; one that does not passes
`mpi_status_ignore`, which tells Open MPI not to.

The facade imports its handle types and constants from
`mpi_f08_types` in both Open MPI 4.1 and 5.0: in 5.0 that module re-exports
them from `mpi_types`, and PRIK follows the re-export to the declaration. So
the same edited file serves both release series.

## 6. Build from the contract

The contract, not the Open MPI sources, is what the extension is built from:

```text
Open MPI Fortran sources
        |
PRIK semantic analysis
        |
restricted .pyi contract, edited into the API you want
        |
PRIK wrapper generation
        |
Python extension linked to the installed Open MPI
```

Build `contract/__init__.pyi`, asking the installed `mpifort` wrapper for the
compiler it wraps, the flags that find Open MPI's Fortran modules, and the
libraries to link:

```bash
python3 -m prik contract/__init__.pyi \
  --compiler "$(mpifort --showme:command)" \
  --wrapper-fortran-flags="$(mpifort --showme:compile)" \
  --native-library $(mpifort --showme:libs) \
  --native-library-dir $(mpifort --showme:libdirs) \
  --out prik_openmpi_f08 \
  --out-dir build
```

This compiles in `build/` and writes `prik_openmpi_f08.so`, a stable copy of
the extension, in the current directory; the rest of this tutorial works in
that directory and imports the extension from there. The build compiles only
the bridge and binding PRIK generates; no Open MPI source is compiled. The
installed Open MPI already provides the implementation, and the extension
links against its libraries. `--compiler` takes the compiler `mpifort` runs
rather than `mpifort` itself because PRIK identifies a Fortran compiler's
family from its executable name.

The extension can already run MPI:

```python
import numpy as np

from prik_openmpi_f08 import mpi_f08

mpi_f08.init()
values = np.array([1, 2], dtype=np.int32)
total = np.empty_like(values)
mpi_f08.allreduce(values, total, mpi_f08.mpi_int, mpi_f08.mpi_sum, mpi_f08.mpi_comm_world)
mpi_f08.finalize()
```

## 7. Add the mpi4py-style layer

A contract describes native calls. What mpi4py adds on top of MPI is a Python
object model, and that belongs in Python. Save this module as `prik_mpi.py`
in the same directory as `prik_openmpi_f08.so`. It is deliberately small: one
datatype and no status, enough to show the shape.

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/runtime/prik_mpi.py -->
```python
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
```

Everything in it calls the generated functions of step 5:

- **Objects and methods.** `Comm` wraps an `Mpi_Comm` handle and spells
  mpi4py's methods; `COMM_WORLD` wraps `mpi_comm_world`. Each method is one
  call to a generated function.
- **One datatype.** Every buffer is an `np.int32` array, so every call passes
  `MPI_INT`.
- **No status.** `Recv` always passes `MPI_STATUS_IGNORE`, as mpi4py does when
  it is given no status.
- **Defaults and `np.int32` values.** `tag`, `source=ANY_SOURCE`, `root`,
  and `op=SUM` are keyword defaults. Ranks and tags are the `np.int32` values
  the contract's `Int32` arguments take from the start -- `Get_rank` returns
  one, `ANY_SOURCE` and the defaults are, and `rank + 1` stays one -- so they
  pass straight through. Converting a plain integer on every call would cost
  more than a small MPI call.
- **Lifetime.** As with mpi4py, importing the module initializes MPI, and MPI
  is finalized when the interpreter exits.

## 8. Run it under Open MPI

Save the program from the top of this page as `mpi_example.py` in the same
directory, beside `prik_mpi.py` and `prik_openmpi_f08.so`, and start two ranks
there with the installed Open MPI launcher:

```bash
mpirun -n 2 python3 mpi_example.py
```

The two ranks print these lines, each rank's lines in order but the ranks in
whichever order they finish:

```text
rank 1 received [0, 1, 2, 3]
rank 0 of 2: bcast [0, 1, 2], sum [3, 5], in place [3, 5]
rank 0 max [2, 3]
rank 1 of 2: bcast [0, 1, 2], sum [3, 5], in place [3, 5]
```

Here is what happened. `mpirun` started two Python processes as MPI ranks.
Each call went through `prik_mpi.py`, then PRIK's generated binding and
bridge, straight into the installed Open MPI library. The NumPy arrays crossed
the boundary as native buffers: `Recv` wrote into rank 1's `data`, `Bcast`
into every rank's `data`, and each reduction into its receive array directly.
No part of Open MPI was rebuilt.

With `from mpi4py import MPI` in place of `import prik_mpi as MPI`, mpi4py
runs the same program and prints the same lines.

## How fast it is

Time per call, compared with mpi4py:

| Call | mpi4py | Generated functions | `prik_mpi.py` |
| --- | ---: | ---: | ---: |
| `Allreduce`, 1 integer | 1.26 µs | 0.85 µs (33% faster) | 1.14 µs (10% faster) |
| `Allreduce`, 1,024 integers | 2.62 µs | 2.10 µs (20% faster) | 2.40 µs (9% faster) |
| `Allreduce`, 1,048,576 integers | 3.04 ms | 2.82 ms (about the same) | 2.81 ms (about the same) |
| `Barrier` | 0.35 µs | 0.49 µs (41% slower) | 0.52 µs (49% slower) |
| `Get_rank` | 34 ns | 289 ns (about 9× slower) | 307 ns (about 9× slower) |

These were measured on a local machine, with two ranks on it: an AMD Ryzen 5
5600H laptop (x86-64, 6 cores and 12 threads, up to 4.28 GHz, 7 GB of memory)
running Ubuntu 22.04, with Python 3.10, NumPy 2.2, GCC and gfortran 11.4,
Open MPI 5.0.11, and mpi4py 4.1.2.

## Why the configured tree must match the installation

`mpi_f08` is not the same text in every Open MPI build. `configure` decides
details of the Fortran interface for the compiler and options it is given, and
writes some of the Fortran sources and headers PRIK reads -- the
`MPI_IN_PLACE` declaration shown earlier is one of them. Two builds of the
same Open MPI version with the same `gfortran` but different Fortran flags can
therefore declare different interfaces. PRIK has to read the declarations of
the build it links against, so the source and build trees must be the ones
that installation was configured from; the version number alone does not
guarantee that.

Open MPI records each configure run in the installation and in the build tree,
so you can compare them. The installation reports when, where, by whom, and
with which command line it was configured:

```bash
ompi_info --parsable | grep '^config:\(timestamp\|host\|user\|cli\)'
```

and the build tree records the same run:

```bash
grep '^OPAL_CONFIGURE_\(DATE\|HOST\|USER\)' "$OMPI_BUILD/Makefile"
grep OPAL_CONFIGURE_CLI "$OMPI_BUILD/opal/include/opal/version.h"
```

The simplest way to have a matching pair is to build Open MPI yourself and
keep its trees:

```bash
tar -xjf openmpi-5.0.11.tar.bz2
mkdir openmpi-5.0.11/build && cd openmpi-5.0.11/build
../configure --prefix="$HOME/openmpi-5.0.11" --enable-mpi-fortran=usempif08 FC=gfortran
make -j4 && make install
```

PRIK's Open MPI integration test runs the commands in this tutorial and checks
this relationship before it starts: it requires the configured tree and the
installation to record the same configure run. Continuous integration runs it
against Open MPI 4.1.8 and 5.0.11 built this way. Those are the configurations
exercised in CI, not the only ones that can work.

## Limitations

This tutorial selected eighteen names; the rest of `mpi_f08` works the same
way when you select it, within these limits of what PRIK supports today:

- **Arrays of handles.** Routines taking an array of derived-type values, such
  as the request and status arrays of `MPI_Waitall`, are not supported:
  building a contract that selects one stops with an error naming the
  argument.
- **Stored callbacks.** PRIK passes a Python callable as a callback that is
  valid only during the call it is passed to. MPI keeps some callbacks for
  later -- the copy and delete functions of `MPI_Comm_create_keyval`, or the
  function given to `MPI_Op_create` -- and calls them after that call has
  returned, which is not supported. See [Callbacks](../guide/callbacks.md).
- **Nonblocking buffers.** Routines such as `MPI_Isend` wrap, but the
  operation keeps using its buffer after the call returns. PRIK does not hold
  on to that NumPy array, so your program must keep it alive and unchanged
  until the operation completes. This is also why `prik_mpi.py` offers no
  `Isend` or `Irecv`: mpi4py's request objects keep their buffers alive, and
  a faithful imitation would need arrays of requests, the first limitation.

`prik_mpi.py` is an illustration, not a complete binding. Its buffers are
contiguous `np.int32` arrays only -- a strided view is refused with a
`TypeError` -- and it reports no status. Ranks and tags must be `np.int32`,
as in the program above; a plain Python `int` is refused with a `TypeError`,
where mpi4py accepts one. It has none of mpi4py's other datatypes,
communicators, pickled-object methods, or `MPI.Exception`: under Open MPI's
default error handler an MPI error aborts the job, and otherwise a nonzero
`ierror` raises the exception the contract's `@raises` produces. Each of these
is more Python over the same kind of generated calls, or more names in the
export list.
