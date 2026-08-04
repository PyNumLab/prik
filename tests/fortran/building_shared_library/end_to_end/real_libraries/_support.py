"""Shared source discovery and build helpers for real-library showcases."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from prik import build_fortran_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


def real_library_source_dir(library: str) -> Path:
    """Locate one configured or sibling real-library source directory."""
    environment_name = f"PRIK_{library.upper()}_SOURCE_DIR"
    configured = os.environ.get(environment_name)
    source_dir = Path(configured).expanduser() if configured else REPOSITORY_ROOT.parent / library / "src"
    if not source_dir.is_dir():
        pytest.skip(f"{library} source directory is unavailable: set {environment_name}")
    return source_dir


def build_real_fortran_library(
    library: str,
    sources: list[Path],
    build_dir: Path,
):
    """Build and import one actual third-party source set through the public API."""
    if shutil.which("gfortran") is None:
        pytest.skip("gfortran is required for real-library showcases")
    if not sources or any(not source.is_file() for source in sources):
        pytest.skip(f"{library} checkout does not contain the expected source files")
    result = build_fortran_extension(
        sources,
        output_dir=build_dir,
        output_name=f"prik_{library}_showcase",
    )
    assert result.shared_library.exists()
    return _import_from_build_dir(result.module_name, result.output_dir)
