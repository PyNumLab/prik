"""Accessor-only layout and typed value-copy runtime evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
BIND_C_DERIVED_LAYOUT_F90_SOURCE = FIXTURES / "fbind_c_derived_layout_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_bind_c_derived_types_use_accessors_and_fortran_value_copy(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        BIND_C_DERIVED_LAYOUT_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fbind_c_derived_layout_f90_wrapper.f90",
            "fbind_c_derived_layout_f90_wrapper.c",
            "fbind_c_derived_layout_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fbind_c_derived_layout_f90",
        pyi_parity_build_mode,
    )

    if pyi_parity_build_mode == "source":
        bridge_source = (tmp_path / "source_build" / "bind_c_fbind_c_derived_layout_f90_wrapper.f90").read_text()

        assert "function bind_c_x2py_field_tagged_point_position_get" in bridge_source
        assert "subroutine bind_c_x2py_field_tagged_point_position_set" in bridge_source
        assert "function bind_c_x2py_field_tagged_point_weight_get" in bridge_source
        assert "subroutine bind_c_x2py_field_tagged_point_weight_set" in bridge_source
        assert "type(c_ptr), value :: bound_value" in bridge_source
        assert "type(x2py_type_tagged_point), pointer :: value" in bridge_source
        assert "result = native_score_by_value(value)" in bridge_source

    value = module.tagged_point()
    module.populate(
        value,
        np.float64(2.5),
        np.int32(4),
        np.complex128(3.0 + 2.0j),
    )

    position = value.position
    assert position.x == np.float64(2.5)
    assert position.axis == np.int32(4)
    assert value.weight == np.complex128(3.0 + 2.0j)

    assert module.score_by_value(value) == np.float64(109.5)
    assert position.x == np.float64(2.5)
