"""The Open MPI integration workflow runs only against a matching installation, and says why not.

These tests stand in fake Open MPI tools and trees, so they run without Open
MPI: an unusable helper or a tree from another configure run skips the real
test locally, and fails it where ``PRIK_OPENMPI_REQUIRED=1`` says Open MPI is
provisioned.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest

from tests.fortran.assumed_types.end_to_end.test_openmpi_f08 import _configured_openmpi

CLI = "'--prefix=/opt/ompi' '--enable-mpi-fortran=usempif08' 'FC=gfortran'"
INFO = f"""ompi:version:full:5.0.11
config:user:builder
config:timestamp:"Fri Sep 25 11:13:48 UTC 2026"
config:host:buildhost
config:cli: {CLI}
bindings:use_mpi_f08:yes
"""


def _executable(path: Path, script: str) -> Path:
    path.write_text(f"#!/bin/sh\n{script}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _openmpi(tmp_path: Path, monkeypatch, *, ompi_info: str | None = None, cli: str = CLI) -> None:
    """Lay out a configured tree and an installation, and point the test at them."""
    source, build, bin_dir = tmp_path / "source", tmp_path / "build", tmp_path / "bin"
    for path in (
        source / "ompi/mpi/fortran/use-mpi-f08/mpi-f08.F90",
        build / "ompi/mpi/fortran/configure-fortran-output.h",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    (source / "VERSION").write_text("major=5\nminor=0\nrelease=11\n", encoding="utf-8")
    (build / "Makefile").write_text(
        "OPAL_CONFIGURE_DATE = Fri Sep 25 11:13:48 UTC 2026\n"
        "OPAL_CONFIGURE_HOST = buildhost\n"
        "OPAL_CONFIGURE_USER = builder\n",
        encoding="utf-8",
    )
    header = build / "opal/include/opal/version.h"
    header.parent.mkdir(parents=True)
    header.write_text(f'#define OPAL_CONFIGURE_CLI " {cli.replace(chr(39), chr(92) + chr(39))}"\n', encoding="utf-8")
    bin_dir.mkdir()
    mpifort = _executable(bin_dir / "mpifort", "exit 0")
    launcher = _executable(bin_dir / "mpirun", 'echo "mpirun (Open MPI) 5.0.11"')
    if ompi_info is not None:
        _executable(bin_dir / "ompi_info", ompi_info)
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("PRIK_OPENMPI_SOURCE", str(source))
    monkeypatch.setenv("PRIK_OPENMPI_BUILD", str(build))
    monkeypatch.setenv("PRIK_OPENMPI_MPIFORT", str(mpifort))
    monkeypatch.setenv("PRIK_OPENMPI_LAUNCHER", str(launcher))


def _info(text: str) -> str:
    """Return a script printing ``text``; ``PATH`` holds only the fake tools, so ``cat`` is named in full."""
    return f"{shutil.which('cat')} <<'EOF'\n{text}EOF"


@pytest.mark.parametrize(
    ("ompi_info", "reason"),
    [
        pytest.param(None, "ompi_info is unavailable", id="missing"),
        pytest.param("exit 3", "ompi_info is unavailable", id="failing"),
        pytest.param(
            _info(INFO.replace("config:host:buildhost\n", "")), "configure host is not recorded", id="incomplete"
        ),
        pytest.param(
            _info(INFO.replace("bindings:use_mpi_f08:yes\n", "")),
            "does not provide the mpi_f08 module",
            id="without-mpi-f08",
        ),
    ],
)
@pytest.mark.parametrize("required", [False, True], ids=["local", "required"])
def test_an_unusable_open_mpi_helper_skips_locally_and_fails_when_required(
    tmp_path: Path, monkeypatch, ompi_info: str | None, reason: str, required: bool
):
    _openmpi(tmp_path, monkeypatch, ompi_info=ompi_info)
    if required:
        monkeypatch.setenv("PRIK_OPENMPI_REQUIRED", "1")
    else:
        monkeypatch.delenv("PRIK_OPENMPI_REQUIRED", raising=False)

    with pytest.raises(pytest.fail.Exception if required else pytest.skip.Exception, match=reason):
        _configured_openmpi()


def test_a_tree_from_another_configure_run_does_not_match_the_installation(tmp_path: Path, monkeypatch):
    """Same version and compiler, but other flags: another configure run describes another interface."""
    _openmpi(tmp_path, monkeypatch, ompi_info=_info(INFO), cli=CLI + " 'FCFLAGS=-fdefault-integer-8'")
    monkeypatch.delenv("PRIK_OPENMPI_REQUIRED", raising=False)

    with pytest.raises(
        pytest.skip.Exception, match=r"not the one the installation was configured from \(differs in cli\)"
    ):
        _configured_openmpi()


def test_the_tree_an_installation_was_configured_from_matches_it(tmp_path: Path, monkeypatch):
    _openmpi(tmp_path, monkeypatch, ompi_info=_info(INFO))

    source, build, mpifort, launcher = _configured_openmpi()

    assert (source.name, build.name) == ("source", "build")
    assert os.path.basename(mpifort) == "mpifort" and os.path.basename(launcher) == "mpirun"
