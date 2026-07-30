"""Recursive and reentrant native runtime call tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import, wrapper_source

RECURSION_SOURCE = wrapper_source("fruntime_recursion_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "runtime" / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_recursive_native_runtime_calls(pyi_parity_build_mode: str, tmp_path: Path):
    module = _build_source_or_generated_pyi_and_import(
        RECURSION_SOURCE,
        tmp_path,
        {
            "bind_c_fruntime_recursion_f90_wrapper.f90",
            "fruntime_recursion_f90_wrapper.c",
            "fruntime_recursion_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fruntime_recursion_f90",
        pyi_parity_build_mode,
    )

    assert module.factorial(np.int32(5)) == np.int32(120)
    assert [module.add_one(np.int32(i)) for i in range(5)] == [1, 2, 3, 4, 5]
