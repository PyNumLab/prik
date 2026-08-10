"""Tests split by stable ownership concept from `test_cli.py`."""

from pathlib import Path

import pytest

import prik.pipeline.preprocessing as preprocessing
from prik.pipeline.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
)


def test_preprocess_source_reparses_fortran_mapping_when_native_expansion_returns_none(monkeypatch, tmp_path: Path):
    source = tmp_path / "solver.F90"
    source.write_text("integer :: value\n", encoding="utf-8")
    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type("Done", (), {"returncode": 0, "stdout": "ignored\n", "stderr": ""})(),
    )
    monkeypatch.setattr(
        preprocessing,
        "expand_native_fortran_includes",
        lambda *_args, **_kwargs: ("integer :: value\n", [], [], []),
    )

    result = preprocessing.preprocess_source(
        source,
        language="fortran",
        config=PreprocessingConfig(mode="compiler", compiler=str(tmp_path / "gfortran")),
    )

    assert result.source_mappings == [
        preprocessing.SourceMapping(
            generated_line=1,
            original_path=str(source),
            original_line=1,
            include_stack=[str(source)],
        )
    ]


def test_preprocess_source_preserves_fortran_native_metadata(monkeypatch, tmp_path: Path):
    fortran_source = tmp_path / "solver.F90"
    private_include = tmp_path / "private.inc"
    fortran_source.write_text('include "private.inc"\n', encoding="utf-8")
    private_include.write_text("integer :: hidden\n", encoding="utf-8")
    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type(
            "Done",
            (),
            {"returncode": 0, "stdout": 'include "private.inc"\n', "stderr": ""},
        )(),
    )

    result = preprocessing.preprocess_source(
        fortran_source,
        language="fortran",
        config=PreprocessingConfig(
            mode="compiler",
            compiler=str(tmp_path / "gfortran"),
            private_includes=["private"],
        ),
    )

    assert [item.to_dict() for item in result.included_files] == [
        {
            "path": str(fortran_source),
            "included_by": None,
            "include_line": None,
            "mechanism": "cpp_include",
            "dependency_kind": "root",
            "exposure": "public",
        },
        {
            "path": str(private_include),
            "included_by": str(fortran_source.resolve()),
            "include_line": 1,
            "mechanism": "fortran_include",
            "dependency_kind": "project",
            "exposure": "private",
        },
    ]
    assert result.source_mappings == [
        preprocessing.SourceMapping(
            generated_line=1,
            original_path=str(fortran_source.resolve()),
            original_line=1,
            include_stack=[str(fortran_source.resolve())],
        ),
        preprocessing.SourceMapping(
            generated_line=2,
            original_path=str(private_include),
            original_line=1,
            include_stack=[str(private_include)],
        ),
        preprocessing.SourceMapping(
            generated_line=3,
            original_path=str(fortran_source.resolve()),
            original_line=1,
            include_stack=[str(fortran_source.resolve())],
        ),
    ]


def test_preprocess_source_reports_fortran_include_diagnostics(monkeypatch, tmp_path: Path):
    fortran_source = tmp_path / "solver.F90"
    fortran_source.write_text('include "missing.inc"\n', encoding="utf-8")
    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type(
            "Done",
            (),
            {"returncode": 0, "stdout": 'include "missing.inc"\n', "stderr": ""},
        )(),
    )

    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing.preprocess_source(
            fortran_source,
            language="fortran",
            config=PreprocessingConfig(
                mode="compiler",
                compiler=str(tmp_path / "gfortran"),
            ),
        )

    assert str(exc_info.value) == 'Fortran INCLUDE file "missing.inc" was not found'
    assert exc_info.value.category == "INCLUDE_NOT_FOUND"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "INCLUDE_NOT_FOUND",
            "message": 'Fortran INCLUDE file "missing.inc" was not found',
            "severity": "error",
            "path": str(fortran_source.resolve()),
            "line": 1,
            "command": [],
        }
    ]
