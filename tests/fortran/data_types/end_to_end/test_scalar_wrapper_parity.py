"""Primitive-scalar source/contract parity for fixed-form externals and a free-form module."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _assert_fmath_examples,
    _build_source_or_generated_pyi_and_import,
    wrapper_source,
)

DATA_TYPE_CONTRACTS = Path(__file__).parent / "fixtures" / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.mark.parametrize(
    ("filename", "contract"),
    [("fmath.f", "fmath"), ("fmath_f90.f90", "fmath_f90")],
    ids=["fixed-form-externals", "free-form-module"],
)
def test_fmath_scalar_sources_build_from_source_and_generated_contract(
    filename: str,
    contract: str,
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = wrapper_source(filename)
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            f"bind_c_{source.stem}_wrapper.f90",
            f"{source.stem}_wrapper.c",
            f"{source.stem}_wrapper.h",
        },
        DATA_TYPE_CONTRACTS / contract,
        pyi_parity_build_mode,
    )

    _assert_fmath_examples(module)
    with pytest.raises(TypeError, match="argument"):
        module.add_r8("not-a-real", np.float64(1.0))
    np.testing.assert_allclose(
        module.add_r8(np.float64(1.5), np.float64(2.25)),
        (np.float64(3.75), np.float64(1.5), np.float64(2.25)),
    )
