"""Compiled direct and mixed optional-scalar entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_optional_all_direct_route_distinguishes_absent_none_and_present(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "optional_arguments_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "optional_arguments_direct_bind_c_f90_wrapper.c",
            "optional_arguments_direct_bind_c_f90_wrapper.h",
        },
        FIXTURES / "contracts" / "optional_arguments_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.optional_state() == np.int32(0)
    assert module.optional_state(None) == np.int32(0)
    assert module.optional_state(np.float64(1.5)) == np.int32(1)
    assert module.add_optional(None) == np.float64(4.0)
    assert module.add_optional(np.float64(1.5)) == np.float64(5.5)

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "optional_arguments_direct_bind_c_f90_wrapper.c").read_text(
            encoding="utf-8"
        )
        assert "int32_t optional_state(double * value);" in binding
        assert "void add_optional(double * value, double * total);" in binding


def test_optional_mixed_route_adapts_only_optional_value_dummy(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "optional_arguments_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "optional_arguments_mixed_bind_c_f90_wrapper.c",
            "optional_arguments_mixed_bind_c_f90_wrapper.h",
            "bind_c_optional_arguments_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "optional_arguments_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_optional_state() == np.int32(0)
    assert module.direct_optional_state(np.float64(2.0)) == np.int32(1)
    assert module.adapted_optional_value_state() == np.int32(0)
    assert module.adapted_optional_value_state(None) == np.int32(0)
    assert module.adapted_optional_value_state(np.float64(2.0)) == np.int32(2)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_optional_arguments_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_optional_value_state" in bridge
        assert "direct_optional_state" not in bridge
