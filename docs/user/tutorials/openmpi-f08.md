---
title: Wrap Open MPI mpi_f08 for Python
description: Turn a reviewed part of Open MPI's Fortran mpi_f08 interface into a Python MPI API
audience: users
prerequisites: an Open MPI installation with mpi_f08, and the configured Open MPI source and build trees it was built from
related: ../guide/wrapping-modules.md, ../guide/callbacks.md, ../reference/cli-commands.md, ../reference/pyi-format.md
status: maintained
publication: reviewed
---

# Wrap Open MPI `mpi_f08` for Python

This tutorial starts from Open MPI's real Fortran `mpi_f08` interface and turns
a small, reviewed part of it into a Python MPI API. At the end, an ordinary
Python program runs under `mpirun` and communicates through it:

```python
import numpy as np

from prik_openmpi_f08 import mpi_f08 as mpi

mpi.mpi_init()
world = mpi.mpi_comm_world
rank, _ = mpi.mpi_comm_rank(world)

values = np.array([rank + 1, rank + 2], dtype=np.int32)
reduced = np.empty_like(values)
mpi.mpi_allreduce(values, reduced, np.int32(values.size), mpi.mpi_int, mpi.mpi_sum, world)

mpi.mpi_finalize()
```

Nothing in this API is written by hand. Every function, handle type, and
constant is generated from the declarations in Open MPI's Fortran sources, and
every call enters the installed Open MPI library. If you know `mpi4py`, the
result will feel familiar: Python code driving the native MPI implementation.
It is not `mpi4py`, though. PRIK exposes the selected Fortran interface as it
is declared, so the names and argument lists are those of `mpi_f08`.

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

## 2. Choose a small Python surface

`mpi_f08` publishes hundreds of routines and constants. Start with a reviewed
subset instead of all of them. Save the Fortran identities to publish in
`mpi_exports.txt`:

```text
mpi_f08::MPI_Init
mpi_f08::MPI_Finalize
mpi_f08::MPI_Comm_rank
mpi_f08::MPI_Comm_size
mpi_f08::MPI_Barrier
mpi_f08::MPI_Send
mpi_f08::MPI_Recv
mpi_f08::MPI_Allreduce
mpi_f08::MPI_COMM_WORLD
mpi_f08::MPI_INT
mpi_f08::MPI_DOUBLE_PRECISION
mpi_f08::MPI_SUM
mpi_f08::MPI_IN_PLACE
mpi_f08::MPI_STATUS_IGNORE
```

This one list covers every kind of declaration the example needs: generic
procedures such as `MPI_Allreduce`, derived-type module objects such as
`MPI_COMM_WORLD`, datatype and operator constants, status storage, and the
special native storage `MPI_IN_PLACE`.

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

## 4. Read the contract

The `contract/` directory holds one editable `.pyi` file per Fortran module the
selection needs. `contract/mpi_f08.pyi` publishes the selected names:

```python
from .mpi_f08_types import mpi_comm_world, mpi_double_precision, mpi_in_place, mpi_int, mpi_status_ignore, mpi_sum
from .mpi_f08_interfaces import mpi_allreduce, mpi_barrier, mpi_comm_rank, mpi_comm_size, mpi_finalize, mpi_init, mpi_recv, mpi_send
from .mpi_types import Mpi_Comm, Mpi_Datatype, Mpi_Op, Mpi_Status
```

These excerpts come from Open MPI 5.0, which declares the handle types in
`mpi_types`. Open MPI 4.1 declares them in `mpi_f08_types`, so there they are
imported from that module and written as `mpi_f08_types.Mpi_Datatype` and so
on. The predefined objects become typed module attributes in
`contract/mpi_f08_types.pyi`:

```python
mpi_comm_world: Final[Mpi_Comm]

mpi_sum: Final[Mpi_Op]

mpi_int: Final[Mpi_Datatype]

mpi_double_precision: Final[Mpi_Datatype]

mpi_in_place: Int32[()]

mpi_status_ignore: Mpi_Status
```

and each selected routine keeps its Fortran interface in
`contract/mpi_f08_interfaces.pyi`:

```python
@bind("MPI_Allreduce")
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

Three mappings are worth a closer look.

**Handles are concrete types.** `Mpi_Comm`, `Mpi_Datatype`, `Mpi_Op`, and
`Mpi_Status` are the derived types Open MPI declares, with their real
components. For example, `Mpi_Comm` holds the one integer handle Open MPI
stores:

```python
class Mpi_Comm:
    def __init__(
        self,
        *,
        mpi_val: Int32 = ...
    ) -> None: ...
```

A handle argument accepts only an object of its own type, and the predefined
handles are `Final` module constants.

**`MPI_IN_PLACE` is native storage.** Its declaration is a C-bound integer
module variable, so it becomes rank-zero native integer storage, `Int32[()]`.
Python sees `mpi.mpi_in_place` as a live NumPy scalar view of Open MPI's own
`MPI_IN_PLACE` variable. Passing that view as a buffer passes the address of
that variable, which is how Open MPI recognizes an in-place operation.
Nothing here knows about MPI: it is the same mapping any Fortran module
variable declared this way receives.

**Choice buffers are `AnyNative`.** The send and receive buffers of MPI
routines are `type(*)` dummies, which accept data of any type, so they become
`AnyNative[Flat]`: any NumPy array, passed as a raw address. `AnyNative`
appears only for these assumed-type dummies; `MPI_IN_PLACE` is a concrete
module object with a concrete type.

The trailing `ierror` argument is optional. Leave it out and the call returns
`None` instead of the error code; Open MPI's default error handler aborts on
errors anyway.

## 5. Build from the contract

The contract, not the Open MPI sources, is what the extension is built from:

```text
Open MPI Fortran sources
        |
PRIK semantic analysis
        |
restricted, editable .pyi contract
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

This writes `prik_openmpi_f08.so` in the current directory. It compiles only
the bridge and binding PRIK generates; no Open MPI source is compiled. The
installed Open MPI already provides the implementation, and the extension
links against its libraries. `--compiler` takes the compiler `mpifort` runs
rather than `mpifort` itself because PRIK identifies a Fortran compiler's
family from its executable name.

## 6. Write an MPI program

This program uses every selected routine: rank 0 sends a NumPy array to
rank 1, and then every rank takes part in three reductions, the last one in
place.

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/runtime/mpi_example.py -->
```python
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
```

Two details follow from the contract:

- Counts, ranks, and tags are Fortran `INTEGER` values, which the contract
  declares as `Int32`. Pass them as `np.int32`, the exact NumPy type, and use
  `np.int32` arrays with `mpi_int` and `np.float64` arrays with
  `mpi_double_precision`, so the element type matches the MPI datatype.
- `mpi_comm_rank` returns its result with the optional error code, which is
  `None` when omitted, so `rank, _ = ...` unpacks it. `rank` is a NumPy
  integer; `int(rank)` gives a plain Python value.

Save it as `mpi_example.py` beside `prik_openmpi_f08.so`.

## 7. Run it under Open MPI

Start two ranks with the installed Open MPI launcher:

```bash
mpirun -n 2 python3 mpi_example.py
```

The two ranks print these lines, in whichever order they finish:

```text
rank 1 received [3, 5, 7, 11]
rank 0 of 2: sum [3, 5], in place [3, 5], total [41.0]
rank 1 of 2: sum [3, 5], in place [3, 5], total [41.0]
```

Here is what happened. `mpirun` started two Python processes as MPI ranks.
Each call went through PRIK's generated binding and bridge straight into the
installed Open MPI library. The NumPy arrays crossed the boundary as native
buffers: `mpi_recv` wrote into rank 1's `received`, and each `mpi_allreduce`
wrote into `reduced`, `total`, and `in_place` directly. No part of Open MPI
was rebuilt.

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

This tutorial selected fourteen names; the rest of `mpi_f08` works the same
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
  until the operation completes.
