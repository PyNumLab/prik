"""Install a wheel built from the checkout for packaging-facing tests.

What a distribution ships and what it advertises to other build tools are
properties of an installation, not of the source tree, so a test that makes
such a claim must ask an installed interpreter. Building and installing the
wheel once per session keeps that evidence affordable.
"""

import importlib
import os
import site
import subprocess
import sys
import venv
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.fortran._support.paths import REPO_ROOT


UNAVAILABLE_MARKERS = (
    "No module named pip",
    "No module named build",
    "No matching distribution found",
    "Could not find a version that satisfies",
    "Could not fetch URL",
    "Temporary failure in name resolution",
    "Network is unreachable",
    "Connection timed out",
)

_INSTALLATIONS: list[TemporaryDirectory] = []


def clean_environment() -> dict[str, str]:
    """Return an environment that cannot reach the checkout through PYTHONPATH."""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return environment


@cache
def _workspace() -> Path:
    """Return one directory that outlives every test in this session."""
    installation = TemporaryDirectory(prefix="prik-installed-wheel-")
    _INSTALLATIONS.append(installation)
    return Path(installation.name)


@cache
def prik_wheel() -> Path:
    """Return a wheel built from the checkout, built once per session."""
    distribution_dir = _workspace() / "dist"
    wheel_build = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(distribution_dir), "."],
        cwd=REPO_ROOT,
        env=clean_environment(),
        capture_output=True,
        text=True,
    )
    if wheel_build.returncode != 0:
        wheel_output = wheel_build.stderr.strip() or wheel_build.stdout.strip()
        if any(marker.lower() in wheel_output.lower() for marker in UNAVAILABLE_MARKERS):
            pytest.skip(f"isolated wheel construction is unavailable: {wheel_output}")
        pytest.fail(f"isolated wheel construction failed:\n{wheel_output}")
    wheels = tuple(distribution_dir.glob("prik-*.whl"))
    if not wheels:
        pytest.skip("isolated wheel construction produced no wheel")
    return wheels[0]


@cache
def installed_prik_python() -> Path:
    """Return the interpreter of an environment holding a freshly built wheel."""
    wheel = prik_wheel()
    environment = clean_environment()
    environment_dir = _workspace() / "installed"
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment_dir)
    installed_python = environment_dir / "bin" / "python"
    install = subprocess.run(
        [str(installed_python), "-m", "pip", "install", "--no-deps", str(wheel)],
        env=environment,
        capture_output=True,
        text=True,
    )
    if install.returncode != 0:
        pytest.fail(f"installing the built wheel failed:\n{install.stderr.strip() or install.stdout.strip()}")
    _share_runtime_dependencies(environment_dir)
    return installed_python


def _share_runtime_dependencies(environment_dir: Path) -> None:
    """Make the wheel's runtime dependencies importable in the new environment.

    The wheel is installed without its dependencies, so the environment reads
    them from the interpreter that built it. ``system_site_packages`` shares
    only the interpreter's system directories, and the commands under test run
    isolated, which drops the per-user directory a development install commonly
    writes to. The directories holding those dependencies are named here so the
    environment resolves them wherever this interpreter found them.
    """
    required = ("immutabledict", "numpy", "filelock")
    roots = {
        str(Path(module.__file__).resolve().parent.parent)
        for module in (importlib.import_module(name) for name in required)
        if module.__file__
    }
    site_packages = tuple(Path(environment_dir).glob("lib/python*/site-packages"))
    if not site_packages:
        return
    shared = [root for root in sorted(roots) if root not in _DEFAULT_SITE_DIRECTORIES]
    if shared:
        (site_packages[0] / "_prik_runtime_dependencies.pth").write_text("\n".join(shared) + "\n", encoding="utf-8")


_DEFAULT_SITE_DIRECTORIES = frozenset(site.getsitepackages())


def installed_run(*command: str) -> str:
    """Return what one command prints from inside the installed environment."""
    result = subprocess.run(command, env=clean_environment(), capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(
            f"installed command failed: {' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def installed_output(program: str) -> str:
    """Return what one program prints from the installed interpreter."""
    return installed_run(str(installed_prik_python()), "-I", "-c", program)
