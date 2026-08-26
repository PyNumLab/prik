"""Primitive-scalar source/contract parity and wrapper-plan runtime tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _assert_fmath_examples,
    _build_source_or_generated_pyi_and_import,
    _build_source_wrapper_plan_and_import,
    wrapper_source,
)

DATA_TYPE_CONTRACTS = Path(__file__).parent / "fixtures" / "contracts"
SCALAR_FIXED_SOURCE = wrapper_source("fmath.f")
SCALAR_F90_SOURCE = wrapper_source("fmath_f90.f90")
pytestmark = pytest.mark.fortran_end_to_end


def test_fortran_wrapper_pipeline_builds_importable_extension(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        SCALAR_FIXED_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_wrapper.f90",
            "fmath_wrapper.c",
            "fmath_wrapper.h",
        },
        DATA_TYPE_CONTRACTS / "fmath",
        pyi_parity_build_mode,
    )

    _assert_fmath_examples(module)


@pytest.mark.parametrize(
    "source",
    [SCALAR_FIXED_SOURCE, SCALAR_F90_SOURCE],
    ids=["fixed-form-externals", "free-form-module"],
)
def test_fmath_scalar_sources_use_canonical_wrapper_plan(
    tmp_path: Path,
    source: Path,
):
    expected_generated_sources = {
        f"bind_c_{source.stem}_wrapper.f90",
        f"{source.stem}_wrapper.c",
        f"{source.stem}_wrapper.h",
    }
    wrapper_root, wrapper_result = _build_source_wrapper_plan_and_import(
        source,
        tmp_path / "build",
        unwrap_namespace=False,
    )

    if source == SCALAR_F90_SOURCE:
        assert not hasattr(wrapper_root, "add_r8")
        assert hasattr(wrapper_root, "fmath_f90")
        module = wrapper_root.fmath_f90
    else:
        assert hasattr(wrapper_root, "add_r8")
        module = wrapper_root

    assert {path.name for path in wrapper_result.generated_sources} == expected_generated_sources
    assert any(path.name == f"{source.stem}_wrapper.h" for path in wrapper_result.generated_files)
    assert any(
        path.name == "prik_binding.h" and path.parent.name == "binding_support"
        for path in wrapper_result.generated_files
    )
    assert wrapper_result.compiled is True
    assert wrapper_result.shared_library.exists()

    _assert_fmath_examples(module)
    error_type, message = _scalar_conversion_failure(module)
    assert error_type is TypeError
    assert "argument" in message


def _scalar_conversion_failure(module) -> tuple[type[BaseException], str]:
    with pytest.raises(TypeError) as error_info:
        module.add_r8("not-a-real", np.float64(1.0))

    np.testing.assert_allclose(
        module.add_r8(np.float64(1.5), np.float64(2.25)),
        (np.float64(3.75), np.float64(1.5), np.float64(2.25)),
    )
    return type(error_info.value), str(error_info.value)


def test_f90_wrapper_pipeline_builds_importable_extension(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        SCALAR_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_f90_wrapper.f90",
            "fmath_f90_wrapper.c",
            "fmath_f90_wrapper.h",
        },
        DATA_TYPE_CONTRACTS / "fmath_f90",
        pyi_parity_build_mode,
    )

    _assert_fmath_examples(module)
