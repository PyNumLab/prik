"""Compiled raw-address lifetime, mutation, nullability, and mixed routing."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def _build(tmp_path: Path, stem: str):
    return _build_inline_pyi_contract_module(
        tmp_path,
        module_name=stem,
        source_text=(FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8"),
        contract_text=(FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8"),
    )


def test_raw_addresses_all_direct_route_preserves_pointer_value_and_caller_lifetime(tmp_path: Path):
    module, result = _build(tmp_path, "raw_addresses_direct_bind_c_f90")
    values = np.array([2.5], dtype=np.float64)

    assert module.pointer_state(0) == np.int32(0)
    assert module.pointer_state(values.ctypes.data) == np.int32(1)
    assert module.increment_pointer(values.ctypes.data) is None
    np.testing.assert_array_equal(values, np.array([3.5], dtype=np.float64))
    assert {path.name for path in result.generated_sources} == {
        "raw_addresses_direct_bind_c_f90_wrapper.c",
        "raw_addresses_direct_bind_c_f90_wrapper.h",
    }


def test_raw_addresses_mixed_route_adapts_only_ordinary_operation(tmp_path: Path):
    module, result = _build(tmp_path, "raw_addresses_mixed_bind_c_f90")
    values = np.array([2.5], dtype=np.float64)

    assert module.pointer_state(values.ctypes.data) == np.int32(1)
    assert module.adapted_value(np.int32(4)) == np.int32(7)
    bridge = (
        (result.output_dir / "bind_c_raw_addresses_mixed_bind_c_f90_wrapper.f90").read_text(encoding="utf-8").casefold()
    )
    assert "bind_c_adapted_value" in bridge
    assert "pointer_state" not in bridge
