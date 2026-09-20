"""Native handles preserve the NumPy dtype for target-dependent primitives."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module, _build_text_and_import, _compiler

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


SOURCE = (NATIVE_FIXTURES / "fextended_handle_dtypes.f90").read_text(encoding="utf-8")

SIZE_SOURCE = (NATIVE_FIXTURES / "fsize_handle.f90").read_text(encoding="utf-8")

SIZE_CONTRACT = """\
from prik.contracts import Allocatable, SizeT

values: Allocatable[SizeT[:]]

def setup() -> None: ...

def total() -> SizeT: ...
"""


def _build_module(tmp_path: Path):
    return _build_text_and_import(
        SOURCE,
        "fextended_handle_dtypes.f90",
        tmp_path,
        {
            "bind_c_fextended_handle_dtypes_wrapper.f90",
            "fextended_handle_dtypes_wrapper.c",
            "fextended_handle_dtypes_wrapper.h",
        },
    )


def test_native_handles_support_long_double_and_complex(tmp_path: Path):
    if Path(_compiler()).name.lower() == "ifx":
        pytest.skip("ifx long double is wider than the host NumPy longdouble")
    module = _build_module(tmp_path)
    module.setup()

    real_values = module.real_values
    assert real_values.to_numpy().dtype == np.dtype(np.longdouble)
    assert module.sum_real(real_values) == np.longdouble(3)

    complex_values = module.complex_values
    assert complex_values.associated is True
    assert complex_values.shape == (2,)
    assert module.sum_complex(complex_values) == np.clongdouble(3 - 3j)


def test_size_t_contract_handles_use_numpy_uintp(tmp_path: Path):
    module, _ = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="fsize_handle",
        source_text=SIZE_SOURCE,
        contract_text=SIZE_CONTRACT,
    )
    module.setup()

    values = module.values
    assert values.to_numpy().dtype == np.dtype(np.uintp)
    assert module.total() == np.uintp(12)
