---
title: Wrap Open MPI mpi_f08 for Python
description: Generate a Python extension from Open MPI's Fortran mpi_f08 sources and give it an mpi4py-style Python API
audience: users
prerequisites: Python with PRIK and NumPy, a GNU Fortran and GCC pair, and Open MPI built from source as shown below
related: ../guide/wrapping-modules.md, ../guide/callbacks.md, ../reference/cli-commands.md, ../reference/pyi-format.md
status: maintained
publication: reviewed
---

# Wrap Open MPI `mpi_f08` for Python

PRIK reads Open MPI's Fortran `mpi_f08` sources and generates a Python
extension that calls the installed Open MPI library. You write no C, Cython,
or `ctypes`. You edit the generated `.pyi` contract into the Python signatures
you want, add a short Python module in the style of
[mpi4py](https://mpi4py.readthedocs.io), and this program runs under
`mpirun`:

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/runtime/mpi_example.py -->
```python
import numpy as np

import prik_mpi as MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

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

It is also a valid mpi4py program: replace `import prik_mpi as MPI` with
`from mpi4py import MPI` and mpi4py prints the same lines.

You build two APIs on the way:

- **The wrapped API**, `prik_openmpi_f08`: the extension PRIK generates from
  Open MPI's declarations and your edited contract. Every call goes straight
  into Open MPI.
- **The Python API**, `prik_mpi.py`: about fifty lines of Python that give the
  wrapped API mpi4py's `Comm` object and keyword defaults.

On small messages both are faster than mpi4py; see
[Compare call times](#compare-call-times).

## What you need

- Linux or macOS, with Python 3.10 or later, NumPy, and PRIK installed; see
  [Installation](../getting-started/installation.md).
- GNU Fortran and GCC of the same version; CI uses version 13.
- Open MPI and mpi4py, built as shown in the next section.
- The files this tutorial uses, from the PRIK repository:
  [`mpi_exports.txt`](https://github.com/PyNumLab/prik/blob/main/tests/fortran/assumed_types/end_to_end/fixtures/contracts/openmpi/mpi_exports.txt),
  [`mpi_f08.pyi`](https://github.com/PyNumLab/prik/blob/main/tests/fortran/assumed_types/end_to_end/fixtures/contracts/openmpi/mpi_f08.pyi),
  [`prik_mpi.py`](https://github.com/PyNumLab/prik/blob/main/tests/fortran/assumed_types/end_to_end/fixtures/runtime/prik_mpi.py),
  [`mpi_example.py`](https://github.com/PyNumLab/prik/blob/main/tests/fortran/assumed_types/end_to_end/fixtures/runtime/mpi_example.py), and
  [`openmpi_f08.py`](https://github.com/PyNumLab/prik/blob/main/benchmarks/openmpi_f08.py). Each is also shown in
  full below. Download them into an empty working directory:

```bash
PRIK_RAW=https://raw.githubusercontent.com/PyNumLab/prik/main
for file in \
  tests/fortran/assumed_types/end_to_end/fixtures/contracts/openmpi/mpi_exports.txt \
  tests/fortran/assumed_types/end_to_end/fixtures/contracts/openmpi/mpi_f08.pyi \
  tests/fortran/assumed_types/end_to_end/fixtures/runtime/prik_mpi.py \
  tests/fortran/assumed_types/end_to_end/fixtures/runtime/mpi_example.py \
  benchmarks/openmpi_f08.py; do
  curl -fsSLO "$PRIK_RAW/$file"
done
```

## Install Open MPI and mpi4py

This tutorial uses [Open MPI 5.0.11](https://www.open-mpi.org/software/ompi/v5.0/);
CI also tests Open MPI 4.1.8, on Linux and macOS. Build it from source and
keep its source and configured build trees: PRIK reads them to generate the
contract, then links the extension to the same installation. Run these
commands in one shell, from your working directory:

```bash
OMPI_ROOT="$HOME/openmpi-5.0.11"
TUTORIAL_DIR="$PWD"
mkdir -p "$OMPI_ROOT/source" "$OMPI_ROOT/build" "$OMPI_ROOT/toolchain"
ln -sf "$(command -v gfortran-13)" "$OMPI_ROOT/toolchain/gfortran"
ln -sf "$(command -v gcc-13)" "$OMPI_ROOT/toolchain/gcc"
export PATH="$OMPI_ROOT/toolchain:$PATH"
curl -fsSLO https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.11.tar.bz2
tar -xjf openmpi-5.0.11.tar.bz2 -C "$OMPI_ROOT/source" --strip-components=1
cd "$OMPI_ROOT/build"
../source/configure --prefix="$OMPI_ROOT/install" --enable-mpi-fortran=usempif08 CC=gcc FC=gfortran
make -j2 && make install
cd "$TUTORIAL_DIR"
export PATH="$OMPI_ROOT/install/bin:$PATH"
export LD_LIBRARY_PATH="$OMPI_ROOT/install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export DYLD_LIBRARY_PATH="$OMPI_ROOT/install/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
OMPI_SRC="$OMPI_ROOT/source"
OMPI_BUILD="$OMPI_ROOT/build"
```

Then build mpi4py against this Open MPI rather than installing a prebuilt
wheel, and check that both report Open MPI 5.0.11:

```bash
MPI4PY_BUILD_MPICC="$OMPI_ROOT/install/bin/mpicc" \
  python3 -m pip install --no-cache-dir --no-binary=mpi4py mpi4py==4.1.2
mpirun --version
python3 -c 'from mpi4py import MPI; print(MPI.Get_library_version())'
```

Use this installation's `mpifort` and `mpirun` throughout. For Open MPI 4.1.8,
change `5.0.11` to `4.1.8` and `v5.0` to `v4.1` in these commands.

## 1. Choose what to wrap

`mpi_f08` is an ordinary Fortran module that gathers others. Its handle types
and predefined objects are Fortran declarations:

```fortran
type(MPI_Comm), parameter     :: MPI_COMM_WORLD = MPI_Comm(OMPI_MPI_COMM_WORLD)
type(MPI_Op), parameter       :: MPI_SUM        = MPI_Op(OMPI_MPI_SUM)
type(MPI_Datatype), parameter :: MPI_INT        = MPI_Datatype(OMPI_MPI_INT)

integer, bind(C, name="mpi_fortran_in_place_") :: MPI_IN_PLACE
type(MPI_Status), bind(C, name="mpi_fortran_status_ignore_") :: MPI_STATUS_IGNORE
```

and each MPI routine is a generic interface:

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

`mpi_f08` publishes hundreds of names. `mpi_exports.txt` selects the ones
the program needs, each qualified by the module that publishes it:

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

PRIK publishes exactly these names and keeps the declarations they depend on,
such as the handle types in their signatures. `--export-symbols` works this
way for any Fortran project; nothing here is specific to MPI.

## 2. Generate the contract

Point PRIK at the one entry source. It follows each `use` to the source that
defines that module, under both Open MPI trees:

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

The `-I` directories are where Open MPI's Fortran sources find their headers,
some of which `configure` wrote into the build tree. PRIK reads the sources
to learn their declarations; it does not compile them.

## 3. Read the contract

`contract/` holds one editable `.pyi` file per Fortran module the selection
needs. The predefined objects keep their Fortran types, in
`contract/mpi_f08_types.pyi`:

```python
mpi_any_source: Final[Int32] = -1

mpi_comm_world: Final[Mpi_Comm]

mpi_sum: Final[Mpi_Op]

mpi_int: Final[Mpi_Datatype]

mpi_in_place: Int32[()]

mpi_status_ignore: Mpi_Status
```

and each routine keeps its Fortran interface, in
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

These excerpts come from Open MPI 5.0, which declares the handle types in
`mpi_types`; Open MPI 4.1 declares them in `mpi_f08_types`. Three mappings
matter for MPI:

- **Handles are typed objects.** `Mpi_Comm`, `Mpi_Datatype`, `Mpi_Op`, and
  `Mpi_Status` are Open MPI's derived types with their real fields, and a
  handle argument accepts only its own type.
- **Buffers are `AnyNative`.** MPI's `type(*)` buffers accept any contiguous
  NumPy array, passed by address.
- **Special objects are Open MPI's own.** `mpi_in_place` and
  `mpi_status_ignore` are live views of Open MPI's `MPI_IN_PLACE` and
  `MPI_STATUS_IGNORE` variables. Passing one passes that variable's address,
  which is how Open MPI recognizes it.

This contract already builds. Its functions are still Fortran's, though: every
count is an argument, and every call returns an error code.

## 4. Edit the contract into a Python API

Replace `contract/mpi_f08.pyi`, the module the extension publishes, with the
edited file you downloaded:

```bash
cp mpi_f08.pyi contract/mpi_f08.pyi
```

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

Each function still calls the Fortran routine it names; only its Python
signature changes. `@native_call` lists the Fortran arguments in order and
says where each comes from:

| Edit | Example | Effect in Python |
| --- | --- | --- |
| `@bind("MPI_Send")` on `def send` | every function | The Python name differs from the Fortran name it calls. |
| `Int32(Arg(0).size)` | `count` of `MPI_Send` | The count comes from the buffer, so the caller does not pass it. |
| `Return("rank", 0)` | `rank` of `MPI_Comm_rank` | The output argument becomes the return value. |
| `Hidden("ierror", Int32)` with `@raises(status="ierror", success=0)` | every function | The error code is not an argument; a nonzero code raises an exception. |

The same file works with Open MPI 4.1 and 5.0.

## 5. Build the wrapped API

Build the edited contract, asking `mpifort` for the compiler, flags, and
libraries of your Open MPI:

```bash
python3 -m prik contract/__init__.pyi \
  --compiler "$(mpifort --showme:command)" \
  --wrapper-fortran-flags="$(mpifort --showme:compile)" \
  --native-library $(mpifort --showme:libs) \
  --native-library-dir $(mpifort --showme:libdirs) \
  --out prik_openmpi_f08 \
  --out-dir build
```

This writes `prik_openmpi_f08.so` in the working directory. Only the code
PRIK generates is compiled; the extension links to the installed Open MPI.
`--compiler` takes the compiler `mpifort` runs, because PRIK recognizes a
compiler by its executable name.

The wrapped API already runs MPI:

```python
import numpy as np

from prik_openmpi_f08 import mpi_f08

mpi_f08.init()
values = np.array([1, 2], dtype=np.int32)
total = np.empty_like(values)
mpi_f08.allreduce(values, total, mpi_f08.mpi_int, mpi_f08.mpi_sum, mpi_f08.mpi_comm_world)
mpi_f08.finalize()
```

## 6. Add the Python API

mpi4py's object model is Python, so the Python API is plain Python over the
wrapped API. `prik_mpi.py`, downloaded beside `prik_openmpi_f08.so`, is
deliberately small:

<!-- prik-doc-source: tests/fortran/assumed_types/end_to_end/fixtures/runtime/prik_mpi.py -->
```python
"""An mpi4py-style Python API over the PRIK-generated Open MPI extension.

It illustrates the shape of mpi4py rather than all of it: every buffer is an
np.int32 array sent as MPI_INT, and no receive reports a status.
"""

import atexit

import numpy as np

from prik_openmpi_f08 import mpi_f08 as _mpi

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

- `Comm` wraps an `Mpi_Comm` handle and spells mpi4py's methods; each method
  is one call to the wrapped API.
- Every buffer is an `np.int32` array sent as `MPI_INT`, and `Recv` passes
  `MPI_STATUS_IGNORE`, as mpi4py does when given no status.
- As with mpi4py, importing the module starts MPI, and exiting stops it.

## 7. Run it

Run the program from the top of this page with two ranks:

```bash
mpirun -n 2 python3 mpi_example.py
```

The ranks print these lines, in whichever order they finish:

```text
rank 1 received [0, 1, 2, 3]
rank 0 of 2: bcast [0, 1, 2], sum [3, 5], in place [3, 5]
rank 0 max [2, 3]
rank 1 of 2: bcast [0, 1, 2], sum [3, 5], in place [3, 5]
```

Each call went from `prik_mpi.py` through the wrapped API into Open MPI, and
the NumPy arrays crossed as native buffers, written in place by `Recv`,
`Bcast`, and the reductions.

Run the same program with mpi4py to compare:

```bash
sed 's/^import prik_mpi as MPI$/from mpi4py import MPI/' mpi_example.py > mpi4py_example.py
mpirun -n 2 python3 mpi4py_example.py
```

It prints the same lines.

## Compare call times

`openmpi_f08.py` times the same operations through each API:

```bash
for api in wrapped python mpi4py; do
  mpirun -n 2 python3 openmpi_f08.py "$api"
done
```

It reports nanoseconds per call for `Allreduce` with 1, 1,024, and 1,048,576
`np.int32` values, `Barrier`, and `Get_rank`, timing every API the same way:
one prepared call per loop iteration, the same buffer placement, and mpi4py's
`MPI.Wtime`. On an AMD Ryzen 5 5600H with Ubuntu 22.04.5, Open MPI 5.0.11 built
with GNU Fortran 11.4, and mpi4py 4.1.2 built against it, the median of five
runs was:

| Operation | mpi4py | Wrapped API | Python API |
| --- | ---: | ---: | ---: |
| `Allreduce`, 1 `int32` | 1.037 µs | 0.697 µs (33% faster) | 0.841 µs (19% faster) |
| `Allreduce`, 1,024 `int32` values | 2.314 µs | 1.779 µs (23% faster) | 2.027 µs (12% faster) |
| `Allreduce`, 1,048,576 `int32` values | 2.719 ms | 2.752 ms (about the same) | 2.827 ms (about the same) |
| `Barrier` | 0.330 µs | 0.328 µs (about the same) | 0.428 µs (30% slower) |
| `Get_rank` | 30 ns | 145 ns (about 5× slower) | 236 ns (about 8× slower) |

`Get_rank` is the cheapest call, so its time is almost all the overhead of
making a call. That overhead is small, but higher through PRIK than through
mpi4py, and can be optimized later. Timings vary by machine; compare APIs on
one machine and one Open MPI installation.

## Limitations

The eighteen names selected here are a start; the rest of `mpi_f08` wraps the
same way when you select it, within these limits:

- **Arrays of handles**, such as the request and status arrays of
  `MPI_Waitall`, are not supported yet; selecting one stops the build with an
  error naming the argument.
- **Stored callbacks** are not supported: a Python callback is valid only
  during the call it is passed to, and MPI keeps some for later, such as the
  functions given to `MPI_Comm_create_keyval` or `MPI_Op_create`. See
  [Callbacks](../guide/callbacks.md).
- **Nonblocking buffers** must stay alive: routines such as `MPI_Isend` wrap,
  but your program must keep the array alive and unchanged until the operation
  completes.

`prik_mpi.py` illustrates the approach rather than covering mpi4py. It takes
contiguous `np.int32` buffers and `np.int32` ranks and tags only, where mpi4py
also accepts other datatypes and plain Python integers, and it reports no
status. More of mpi4py is more Python over the same kind of wrapped calls, or
more names in `mpi_exports.txt`.
