"""Real Open MPI source to generated contract to two-rank execution.

The test runs the commands the Open MPI ``mpi_f08`` tutorial shows: generate
a restricted contract from the configured Open MPI sources, build it against
the installation without compiling any Open MPI source, and run the tutorial's
program under the Open MPI launcher.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

import pytest


pytestmark = pytest.mark.fortran_end_to_end
# The tutorial displays this program; the test runs it as written.
RUNTIME = Path(__file__).parent / "fixtures" / "runtime" / "mpi_example.py"
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
# ``ompi_info`` reports these for the configure run that built the
# installation, and a configured tree records the same values, so they
# identify that run: its date, host, user, and exact command line.
CONFIGURE_IDENTITY = ("timestamp", "host", "user", "cli")


def _unavailable(reason: str) -> NoReturn:
    """Skip locally, but fail where ``PRIK_OPENMPI_REQUIRED`` says Open MPI is provisioned."""
    if os.environ.get("PRIK_OPENMPI_REQUIRED") == "1":
        pytest.fail(reason)
    pytest.skip(reason)


def _tool_output(command: Sequence[str], purpose: str) -> str:
    """Return one Open MPI helper command's output, or report the helper unavailable.

    A helper that is missing, cannot run, fails, or hangs leaves the
    installation unusable for this test, which is not a test failure unless
    Open MPI was required.
    """
    try:
        completed = subprocess.run(list(command), check=True, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        _unavailable(f"{purpose} is unavailable: `{shlex.join(command)}` failed ({error})")
    return completed.stdout


def _field(text: str, pattern: str, purpose: str) -> str:
    """Return the one value ``pattern`` captures in ``text``, or report it unavailable."""
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        _unavailable(f"{purpose} is not recorded")
    return match.group(1).strip()


def _installed_configuration(info: str) -> dict[str, object]:
    """Return the installation's version and the identity of the configure run that built it."""
    identity: dict[str, object] = {
        "version": _field(info, r"^ompi:version:full:(.+)$", "the installed Open MPI version"),
    }
    for key in CONFIGURE_IDENTITY:
        value = _field(info, rf"^config:{key}:(.*)$", f"the installed Open MPI configure {key}")
        identity[key] = shlex.split(value) if key == "cli" else value.strip('"')
    return identity


def _tree_configuration(source: Path, build: Path) -> dict[str, object]:
    """Return a configured tree's version and the identity of the configure run that produced it."""
    try:
        version_text = (source / "VERSION").read_text(encoding="utf-8")
        makefile = (build / "Makefile").read_text(encoding="utf-8")
        version_header = (build / "opal/include/opal/version.h").read_text(encoding="utf-8")
    except OSError as error:
        _unavailable(f"the configured Open MPI tree records no configuration: {error}")
    parts = [
        _field(version_text, rf"^{part}=(\d+)$", f"the Open MPI source {part} version")
        for part in ("major", "minor", "release")
    ]
    cli = _field(version_header, r'^#define OPAL_CONFIGURE_CLI "(.*)"$', "the configured tree's configure command line")
    identity: dict[str, object] = {"version": ".".join(parts), "cli": shlex.split(cli.replace("\\'", "'"))}
    for key, variable in (("timestamp", "DATE"), ("host", "HOST"), ("user", "USER")):
        identity[key] = _field(
            makefile, rf"^OPAL_CONFIGURE_{variable} = (.*)$", f"the configured tree's configure {key}"
        )
    return identity


def _configured_openmpi() -> tuple[Path, Path, str, str]:
    """Find configured sources, and the installation they were configured for."""
    source_text = os.environ.get("PRIK_OPENMPI_SOURCE")
    build_text = os.environ.get("PRIK_OPENMPI_BUILD")
    if not source_text or not build_text:
        _unavailable("set PRIK_OPENMPI_SOURCE and PRIK_OPENMPI_BUILD to a matching configured Open MPI tree")
    source, build = Path(source_text), Path(build_text)
    mpifort = os.environ.get("PRIK_OPENMPI_MPIFORT") or shutil.which("mpifort")
    launcher = os.environ.get("PRIK_OPENMPI_LAUNCHER") or shutil.which("mpirun")
    if not mpifort or not launcher:
        _unavailable("Open MPI Fortran compiler wrapper and launcher are required")
    # Only the entry source is named; the modules it uses are discovered.
    for path in (
        source / "ompi/mpi/fortran/use-mpi-f08/mpi-f08.F90",
        build / "ompi/mpi/fortran/configure-fortran-output.h",
    ):
        if not path.is_file():
            _unavailable(f"configured Open MPI semantic input is unavailable: {path}")

    beside = Path(mpifort).with_name("ompi_info")
    ompi_info = str(beside) if beside.is_file() else shutil.which("ompi_info")
    if ompi_info is None:
        _unavailable("ompi_info is unavailable beside mpifort or on PATH")
    info = _tool_output([ompi_info, "--parsable"], "ompi_info")
    if re.search(r"^bindings:use_mpi_f08:yes$", info, flags=re.MULTILINE) is None:
        _unavailable("the installed Open MPI does not provide the mpi_f08 module")
    installed = _installed_configuration(info)
    configured = _tree_configuration(source, build)
    # The generated Fortran sources and headers follow the configure run, so
    # a tree of the same version configured differently -- other flags, other
    # options, another compiler -- would describe another interface.
    if configured != installed:
        differing = sorted(key for key in installed if installed[key] != configured.get(key))
        _unavailable(
            "the configured Open MPI tree is not the one the installation was configured from "
            f"(differs in {', '.join(differing)})"
        )

    launcher_version = _tool_output([launcher, "--version"], "the Open MPI launcher")
    if installed["version"] not in launcher_version:
        _unavailable(f"the launcher does not belong to Open MPI {installed['version']}")
    return source, build, mpifort, launcher


def test_openmpi_f08_contract_replay_and_two_rank_communication(tmp_path: Path) -> None:
    """The tutorial's contract, build, and program run against a real Open MPI."""
    source, build, mpifort, launcher = _configured_openmpi()
    contract = tmp_path / "contract"
    exports = tmp_path / "mpi_exports.txt"
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
        timeout=300,
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

    def showme(flag: str) -> list[str]:
        return shlex.split(_tool_output([mpifort, f"--showme:{flag}"], f"mpifort --showme:{flag}"))

    # The underlying compiler command may take more than one token, such as a
    # launcher before the compiler, which is not a compiler plus flags.
    command = showme("command")
    if len(command) != 1:
        _unavailable(f"mpifort --showme:command is a multi-token command {command}; pass one compiler executable")
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(contract / "__init__.pyi"),
            "--compiler",
            command[0],
            f"--wrapper-fortran-flags={shlex.join(showme('compile'))}",
            "--native-library",
            *showme("libs"),
            "--native-library-dir",
            *showme("libdirs"),
            "--out",
            "prik_openmpi_f08",
            "--out-dir",
            str(tmp_path / "extension"),
            "--jobs",
            "2",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
        cwd=tmp_path,
    )
    payload = json.loads(built.stdout)
    # Only PRIK's bridge and binding compile; Open MPI's own sources do not.
    assert payload["native_build_plan"]["compilation_units"] == []
    assert sorted(Path(path).name for path in payload["generated_files"] if path.endswith(".o")) == [
        "bind_c_prik_openmpi_f08_wrapper.o",
        "prik_openmpi_f08_wrapper.o",
    ]
    bridge = (tmp_path / "extension" / "bind_c_prik_openmpi_f08_wrapper.f90").read_text(encoding="utf-8")
    assert "use mpi_f08_interfaces, only:" in bridge
    assert "=> MPI_Allreduce" in bridge and "=> MPI_Send" in bridge

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(tmp_path / "extension"), env.get("PYTHONPATH", ""))))
    env["LD_LIBRARY_PATH"] = os.pathsep.join((*showme("libdirs"), env.get("LD_LIBRARY_PATH", "")))
    completed = subprocess.run(
        [launcher, "-n", "2", sys.executable, str(RUNTIME)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = completed.stdout.splitlines()
    assert "rank 1 received [3, 5, 7, 11]" in output
    for rank in (0, 1):
        assert f"rank {rank} of 2: sum [3, 5], in place [3, 5], total [41.0]" in output
