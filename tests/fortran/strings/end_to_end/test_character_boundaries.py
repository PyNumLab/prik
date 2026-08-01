"""Fixed-form and modern scalar character argument/result tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _assert_legacy_string_examples,
    _assert_modern_string_examples,
    _sole_native_module,
)
from prik import build_pyi_extension

FIXTURES = Path(__file__).parent / "fixtures"
STRING_LEGACY_SOURCE = FIXTURES / "fstrings.f"
STRING_F90_SOURCE = FIXTURES / "fstrings_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"

pytestmark = pytest.mark.fortran_end_to_end


def _build_contract_module(contract: Path, native_object: Path, output_dir: Path, symbol: str):
    """Build one edited character contract through the canonical wrapper plan."""
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    return package if hasattr(package, symbol) else _sole_native_module(package)


def test_legacy_fortran_character_arguments_and_results(pyi_parity_build_mode: str, tmp_path: Path):
    module = _build_source_or_generated_pyi_and_import(
        STRING_LEGACY_SOURCE,
        tmp_path,
        {
            "bind_c_fstrings_wrapper.f90",
            "fstrings_wrapper.c",
            "fstrings_wrapper.h",
        },
        CONTRACT_FIXTURES / "fstrings",
        pyi_parity_build_mode,
    )

    _assert_legacy_string_examples(module)


def test_modern_fortran_character_arguments_and_results(
    pyi_parity_build_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    module = _build_source_or_generated_pyi_and_import(
        STRING_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fstrings_f90_wrapper.f90",
            "fstrings_f90_wrapper.c",
            "fstrings_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fstrings_f90",
        pyi_parity_build_mode,
    )

    _assert_modern_string_examples(module)
    assert module.string_len_assumed("") == 0
    assert module.string_len_assumed("café") == 5
    with pytest.raises(TypeError, match="str"):
        module.string_len_assumed(b"bytes")
    with pytest.raises(TypeError, match="embedded NUL"):
        module.string_len_assumed("a\0b")

    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent(labels) == 16
    assert module.fixed_array_extent(np.empty(0, dtype="S8")) == 0
    with pytest.raises(TypeError):
        module.fixed_array_extent(np.array([b"short"], dtype="S7"))
    with pytest.raises(TypeError):
        module.fixed_array_extent(np.array([[b"label"]], dtype="S8"))

    monkeypatch.setenv("PRIK_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError):
        module.string_result_deferred("failure")
    with pytest.raises(MemoryError, match="Unable to allocate copy-return output string"):
        module.string_result_fixed()


def test_edited_modern_string_contract_wraps_full_axis_spelling_set(tmp_path: Path):
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        CONTRACT_FIXTURES / "fstrings_f90_axes" / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_axes_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert module.string_len_assumed("variable length") == 15
    assert module.string_len_fixed("short   ") == 5
    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent(labels) == 16

    label = np.array("abcdefgh", dtype="S8")
    assert module.rewrite_storage(label) is None
    assert label[()] == b"Ybcdefg?"
