"""Real Open MPI source to generated contract to two-rank execution."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import pytest

from prik.pipeline.build import NativeLinkItem, build_pyi_extension


pytestmark = pytest.mark.fortran_end_to_end
RUNTIME = Path(__file__).parent / "fixtures" / "runtime" / "openmpi_basic.py"
EXPORTS = (
    "MPI_Init",
    "MPI_Finalize",
    "MPI_Comm_rank",
    "MPI_Comm_size",
    "MPI_Barrier",
    "MPI_Send",
    "MPI_Recv",
    "MPI_Allreduce",
    "MPI_COMM_WORLD",
    "MPI_INT",
    "MPI_DOUBLE_PRECISION",
    "MPI_SUM",
    "MPI_IN_PLACE",
    "MPI_STATUS_IGNORE",
)


def _unavailable(reason: str) -> NoReturn:
    """Skip locally, but fail where ``PRIK_OPENMPI_REQUIRED`` says Open MPI is provisioned."""
    if os.environ.get("PRIK_OPENMPI_REQUIRED") == "1":
        pytest.fail(reason)
    pytest.skip(reason)


def _configured_openmpi() -> tuple[Path, Path, str, str, str]:
    """Find matching configured sources, wrapper compiler, and Open MPI launcher."""
    source_text = os.environ.get("PRIK_OPENMPI_SOURCE")
    build_text = os.environ.get("PRIK_OPENMPI_BUILD")
    if not source_text or not build_text:
        _unavailable("set PRIK_OPENMPI_SOURCE and PRIK_OPENMPI_BUILD to a matching configured Open MPI tree")
    source, build = Path(source_text), Path(build_text)
    mpifort = os.environ.get("PRIK_OPENMPI_MPIFORT") or shutil.which("mpifort")
    launcher = os.environ.get("PRIK_OPENMPI_LAUNCHER") or shutil.which("orterun") or shutil.which("mpirun")
    if not mpifort or not launcher:
        _unavailable("Open MPI Fortran compiler wrapper and launcher are required")
    # Only the entry source is named; the modules it uses are discovered.
    for path in (
        source / "ompi/mpi/fortran/use-mpi-f08/mpi-f08.F90",
        build / "ompi/mpi/fortran/configure-fortran-output.h",
    ):
        if not path.is_file():
            _unavailable(f"configured Open MPI semantic input is unavailable: {path}")
    version_file = (source / "VERSION").read_text(encoding="utf-8")
    parts = [re.search(rf"^{part}=(\d+)$", version_file, flags=re.MULTILINE) for part in ("major", "minor", "release")]
    if any(part is None for part in parts):
        _unavailable("Open MPI source version could not be read")
    version = ".".join(part.group(1) for part in parts if part is not None)
    compiler_version = subprocess.check_output([mpifort, "--showme:version"], text=True)
    launcher_version = subprocess.check_output([launcher, "--version"], text=True)
    if (
        f"Open MPI {version}" not in compiler_version
        or version not in launcher_version
        or not any(label in launcher_version for label in ("Open MPI", "OpenRTE"))
    ):
        _unavailable("configured sources, mpifort, and launcher must belong to the same Open MPI version")
    _require_same_fortran_configuration(build, mpifort)
    return source, build, mpifort, launcher, version


def _require_same_fortran_configuration(build: Path, mpifort: str) -> None:
    """Require the configured tree and the installation to share their Fortran build.

    One version configured twice can generate different Fortran sources and
    headers, so the tree the contract is read from must have been configured
    with the Fortran compiler the installation was built with, and the
    installation must provide the ``mpi_f08`` module.
    """
    ompi_info = Path(mpifort).with_name("ompi_info")
    info = subprocess.check_output([str(ompi_info) if ompi_info.is_file() else "ompi_info", "--parsable"], text=True)
    installed = re.search(r"^compiler:fortran:absolute:(.+)$", info, flags=re.MULTILINE)
    configured_header = build / "opal/include/opal_config.h"
    configured = (
        re.search(r'^#define OMPI_FC_ABSOLUTE "([^"]+)"', configured_header.read_text(encoding="utf-8"), re.MULTILINE)
        if configured_header.is_file()
        else None
    )
    if re.search(r"^bindings:use_mpi_f08:yes", info, flags=re.MULTILINE) is None:
        _unavailable("the installed Open MPI does not provide the mpi_f08 module")
    if (
        installed is None
        or configured is None
        or Path(installed.group(1).strip()).resolve() != Path(configured.group(1)).resolve()
    ):
        _unavailable("the configured Open MPI tree and the installation were built with different Fortran compilers")


def test_openmpi_f08_contract_replay_and_two_rank_communication(tmp_path: Path) -> None:
    """The selected facade and native storage survive a real .pyi replay build."""
    source, build, mpifort, launcher, _version = _configured_openmpi()
    contract = tmp_path / "contract"
    exports = tmp_path / "exports.txt"
    exports.write_text("".join(f"mpi_f08::{symbol}\n" for symbol in EXPORTS), encoding="utf-8")
    includes = (
        build,
        build / "ompi/mpi/fortran/use-mpi-f08",
        build / "ompi/mpi/fortran/use-mpi-f08/mod",
        source,
        build / "ompi/include",
        source / "ompi/include",
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source / "ompi/mpi/fortran/use-mpi-f08/mpi-f08.F90"),
            "--module-source-dir",
            str(source),
            "--module-source-dir",
            str(build),
            "--export-symbols",
            str(exports),
            "--out",
            str(contract),
            "--compiler",
            mpifort,
            *(part for include in includes for part in ("-I", str(include))),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )
    facade = (contract / "mpi_f08.pyi").read_text(encoding="utf-8")
    types = (contract / "mpi_f08_types.pyi").read_text(encoding="utf-8")
    interfaces = (contract / "mpi_f08_interfaces.pyi").read_text(encoding="utf-8")
    assert all(f'"{symbol.lower()}"' in facade for symbol in EXPORTS)
    assert all(f'"Mpi_{name}"' in facade for name in ("Comm", "Datatype", "Op", "Status"))
    assert "mpi_waitall" not in facade
    assert "mpi_in_place: Int32[()]" in types
    assert "mpi_comm_world: Final[Mpi_Comm]" in types
    assert "mpi_sum: Final[Mpi_Op]" in types
    assert "mpi_int: Final[Mpi_Datatype]" in types
    assert "mpi_status_ignore: Mpi_Status" in types
    # Where the handle types are declared depends on the Open MPI version.
    declarations = "".join(path.read_text(encoding="utf-8") for path in contract.glob("*.pyi"))
    assert all(f"class Mpi_{name}" in declarations for name in ("Comm", "Datatype", "Op", "Status"))
    assert "AnyNative[" in interfaces and '@overload("mpi_send_f08")\ndef mpi_send(' in interfaces

    def show(flag: str) -> list[str]:
        return shlex.split(subprocess.check_output([mpifort, flag], text=True))

    # The underlying compiler command may take more than one token, such as a
    # launcher before the compiler, which is not a compiler plus flags.
    command, compile_flags = show("--showme:command"), show("--showme:compile")
    if len(command) != 1:
        _unavailable(f"mpifort --showme:command is a multi-token command {command}; pass one compiler executable")
    include_dirs = [*show("--showme:incdirs"), *(flag[2:] for flag in compile_flags if flag.startswith("-I"))]
    result = build_pyi_extension(
        contract / "__init__.pyi",
        input_compiler=command[0],
        native_include_dirs=list(dict.fromkeys(include_dirs)),
        wrapper_fortran_flags=[flag for flag in compile_flags if not flag.startswith("-I")],
        native_link_items=[NativeLinkItem("linker_argument", flag) for flag in show("--showme:link")],
        native_linker_language="fortran",
        output_name="prik_openmpi_f08",
        output_dir=tmp_path / "extension",
        jobs=2,
    )
    assert result.native_build_plan is not None and not result.native_build_plan.compilation_units
    bridge = next(path for path in result.generated_sources if path.suffix == ".f90").read_text(encoding="utf-8")
    assert "use mpi_f08_interfaces, only:" in bridge
    assert "=> MPI_Allreduce" in bridge and "=> MPI_Send" in bridge
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(result.output_dir), env.get("PYTHONPATH", ""))))
    env["LD_LIBRARY_PATH"] = os.pathsep.join((*show("--showme:libdirs"), env.get("LD_LIBRARY_PATH", "")))
    completed = subprocess.run(
        [launcher, "-n", "2", sys.executable, str(RUNTIME)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.stdout.count("communication passed") == 2
