"""Maintainer-only complete-surface checks that reuse the LAPACK example build."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..routine_inventory import EXPECTED_LAPACK_PROCEDURES
from examples.lapack.tests.helpers import assert_runtime_smoke
from prik.parsers.fortran.parser import parse_fortran_file
from prik.preprocessing import PreprocessingConfig, preprocess_source


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
NATIVE_ROOT = Path(__file__).resolve().parents[1] / "native"
FORTRAN_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}
PREPROCESSED_FORTRAN_SUFFIXES = {suffix.upper() for suffix in FORTRAN_SUFFIXES}


def _source_for_parser(path: Path) -> str:
    if path.suffix in PREPROCESSED_FORTRAN_SUFFIXES:
        return preprocess_source(
            path,
            language="fortran",
            config=PreprocessingConfig(mode="compiler", compiler="gfortran"),
        ).source
    return path.read_text(encoding="utf-8")


def _source_procedure_exports() -> set[tuple[str | None, str]]:
    expected: set[tuple[str | None, str]] = set()
    for path in sorted(NATIVE_ROOT.iterdir()):
        if not path.is_file() or path.suffix.lower() not in FORTRAN_SUFFIXES:
            continue
        parsed = parse_fortran_file(_source_for_parser(path), filename=path.name)
        expected.update((None, procedure.name.lower()) for procedure in parsed.procedures)
        for module in parsed.modules:
            expected.update((module.name.lower(), procedure.name.lower()) for procedure in module.procedures)
    return expected


def test_ci_complete_prik_surface_reuses_example_extension(prik_lapack):
    expected = _source_procedure_exports()
    assert len(expected) == EXPECTED_LAPACK_PROCEDURES
    assert all(getattr(prik_lapack, name, None) is not None for name in ("la_constants", "la_xisnan"))

    missing = []
    for namespace, name in sorted(expected, key=lambda item: (item[0] or "", item[1])):
        owner = prik_lapack if namespace is None else getattr(prik_lapack, namespace, None)
        if owner is None or not callable(getattr(owner, name, None)):
            missing.append(".".join(filter(None, (namespace, name))))
    assert missing == []
    assert_runtime_smoke(prik_lapack)
