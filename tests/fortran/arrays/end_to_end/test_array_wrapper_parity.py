"""Primitive-array source/contract parity and wrapper-plan runtime tests."""

from pathlib import Path

import pytest

from tests.fortran._support.wrapper_build import (
    _assert_array_rejects_strided_views,
    _assert_fmath_array_examples,
    _build_and_import,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
CONTRACTS = FIXTURES / "contracts"
ARRAY_FIXED_SOURCE = FIXTURES / "native" / "fmath_arrays.f"
ARRAY_F90_SOURCE = FIXTURES / "native" / "fmath_arrays_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end


def test_fortran_array_wrapper_pipeline_matches_fmath_results_with_contiguous_arrays(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ARRAY_FIXED_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_arrays_wrapper.f90",
            "fmath_arrays_wrapper.c",
            "fmath_arrays_wrapper.h",
        },
        CONTRACTS / "fmath_arrays",
        pyi_parity_build_mode,
    )

    _assert_fmath_array_examples(module, strided=False)
    _assert_array_rejects_strided_views(module, "SQUARE_R4")


def test_f90_array_wrapper_distinguishes_contiguous_and_strided_contracts(tmp_path: Path):
    """The source build tells contiguous and strided dummies of every kind apart.

    This is the largest array fixture, so it builds once, from source. Its
    generated contract is compared with the reviewed fixture by
    `tests/fortran/arrays/pipeline/test_generated_array_contracts.py`, and
    replaying generated contracts is proven by every other parity test here.
    """
    source_dir = tmp_path / "source_build"
    source_dir.mkdir()
    module = _build_and_import(
        ARRAY_F90_SOURCE,
        source_dir,
        {
            "bind_c_fmath_arrays_f90_wrapper.f90",
            "fmath_arrays_f90_wrapper.c",
            "fmath_arrays_f90_wrapper.h",
        },
    )

    _assert_fmath_array_examples(module, suffix="_CONTIGUOUS", strided=False)
    _assert_array_rejects_strided_views(module, "SQUARE_R4_CONTIGUOUS")
    _assert_fmath_array_examples(module, suffix="_STRIDED", strided=True)
