---
title: Wrap a prebuilt Open MPI mpi_f08 installation
description: Generate a restricted Fortran contract and build a Python extension against Open MPI
audience: users
prerequisites: configured Open MPI source tree and matching installed Open MPI development files
related: ../guide/wrapping-modules.md, ../reference/cli-commands.md, ../reference/pyi-format.md
status: maintained
publication: reviewed
---

# Wrap Open MPI `mpi_f08`

Use a configured Open MPI source tree and the corresponding installed Open MPI
toolchain. PRIK reads `mpi-f08.F90` and finds the sources of the modules it
uses in the source and build trees, whatever their names and layout in your
Open MPI version, to generate a contract; the extension compiles against the
installed modules and libraries.

Set `PRIK_OPENMPI_SOURCE` to the matching Open MPI source root and
`PRIK_OPENMPI_BUILD` to its build root. Use a tree that has been built with
`make`, which generates the Fortran includes the sources read, such as
`configure-fortran-output.h` and `sizeof_f08.h`; `configure` also generates some
module sources into the build tree, so search both trees. Confirm that
`mpifort --showme:version` reports the same Open MPI version as the source
tree, and configure the tree with the Fortran compiler the installation was
built with, which `ompi_info --parsable` reports as `compiler:fortran:absolute`.

Select the public facade's small initial API:

```bash
cat > exports.txt <<'EOF'
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
EOF

python3 -m prik generate --pyi \
  "$PRIK_OPENMPI_SOURCE/ompi/mpi/fortran/use-mpi-f08/mpi-f08.F90" \
  --module-source-dir "$PRIK_OPENMPI_SOURCE" \
  --module-source-dir "$PRIK_OPENMPI_BUILD" \
  --export-symbols exports.txt --out contract --compiler mpifort \
  -I "$PRIK_OPENMPI_BUILD" \
  -I "$PRIK_OPENMPI_BUILD/ompi/mpi/fortran/use-mpi-f08" \
  -I "$PRIK_OPENMPI_BUILD/ompi/mpi/fortran/use-mpi-f08/mod" \
  -I "$PRIK_OPENMPI_SOURCE" \
  -I "$PRIK_OPENMPI_BUILD/ompi/include" \
  -I "$PRIK_OPENMPI_SOURCE/ompi/include"
```

Build from the generated `contract/__init__.pyi`. Query the installed wrapper
compiler for its compiler command, module and include directories, remaining
compile flags, and ordered link arguments. The compiler command must be a single
executable; a command such as `ccache gfortran` is not a compiler plus flags:

```python
import shlex
import subprocess

from prik.pipeline.build import NativeLinkItem, build_pyi_extension


def show(option):
    return shlex.split(subprocess.check_output(["mpifort", option], text=True))


command, compile_flags = show("--showme:command"), show("--showme:compile")
if len(command) != 1:
    raise SystemExit(f"mpifort wraps the multi-token command {command}; set one compiler executable")
build_pyi_extension(
    "contract/__init__.pyi",
    input_compiler=command[0],
    native_include_dirs=show("--showme:incdirs"),
    wrapper_fortran_flags=compile_flags,
    native_link_items=[NativeLinkItem("linker_argument", flag) for flag in show("--showme:link")],
    native_linker_language="fortran",
    output_name="prik_openmpi_f08",
    output_dir="build/openmpi",
)
```

Run a Python program under the matching Open MPI launcher. The selected
functions live in `prik_openmpi_f08.mpi_f08`; Fortran `Int32` arguments such as
counts and ranks use `numpy.int32` values. NumPy arrays provide the storage for
choice buffers. In the tested Open MPI 4.1.2 and 5.0.11 configurations, `mpi_in_place` is
a concrete integer module object exposed as a live rank-zero NumPy view, so
pass that view directly to `mpi_allreduce`.
A two-rank example lives at
`tests/fortran/assumed_types/end_to_end/fixtures/runtime/openmpi_basic.py`.
Run it with `PYTHONPATH=build/openmpi orterun -n 2 python3` followed by that
path, or use the matching Open MPI `mpirun` launcher. It exercises
send/receive, ordinary and in-place all-reduce, and the selected communicator
and datatype objects.

The choice-buffer ABI follows the configured interface declaration:
`TYPE(*), DIMENSION(*)` passes a raw address, while assumed-shape and
assumed-rank declarations pass a C descriptor. Arrays of derived MPI handles,
persistent callbacks, and nonblocking buffer-lifetime management are outside
this initial surface.
