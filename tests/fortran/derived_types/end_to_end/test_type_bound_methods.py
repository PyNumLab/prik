"""Derived-type field and type-bound method runtime evidence."""

from pathlib import Path

import pytest

from tests.fortran._support.wrapper_build import (
    _assert_modern_class_examples,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
CLASS_F90_SOURCE = FIXTURES / "native" / "fclasses_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_modern_fortran_derived_type_exposes_class_and_type_bound_methods(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        CLASS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fclasses_f90_wrapper.f90",
            "fclasses_f90_wrapper.c",
            "fclasses_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fclasses_f90",
        pyi_parity_build_mode,
    )

    assert "make(n, fill_value) -> vector_store" in module.vector_store.make.__doc__
    assert "n : int64" in module.vector_store.make.__doc__
    assert "wrapped native instance" not in module.vector_store.make.__doc__
    _assert_modern_class_examples(module)
