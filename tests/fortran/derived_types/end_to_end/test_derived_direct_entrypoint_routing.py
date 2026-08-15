"""Compiled opaque derived-object direct and mixed entrypoint evidence."""

import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_derived_all_direct_route_keeps_generated_type_support_separate(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "derived_types_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "derived_types_direct_bind_c_f90_wrapper.c",
            "derived_types_direct_bind_c_f90_wrapper.h",
            "bind_c_derived_types_direct_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "derived_types_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    value = module.point(x=np.float64(1.5), y=np.float64(2.5))
    references_before = sys.getrefcount(value)
    assert module.direct_sum(value) == np.float64(4.0)
    shifted = module.direct_shift(value, np.float64(2.0))
    assert shifted is None
    assert (value.x, value.y) == (np.float64(3.5), np.float64(4.5))
    assert sys.getrefcount(value) == references_before

    if pyi_parity_build_mode == "source":
        support = (
            (tmp_path / "source_build" / "bind_c_derived_types_direct_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_prik_create_point" in support
        assert "bind_c_prik_destroy_point" in support
        assert "direct_sum" not in support
        assert "direct_shift" not in support

        binding = (tmp_path / "source_build" / "derived_types_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "double direct_sum(void * value);" in binding
        assert "void direct_shift(void * value, double delta);" in binding
        assert "struct point" not in binding


def test_derived_mixed_route_adapts_only_by_value_aggregate(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "derived_types_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "derived_types_mixed_bind_c_f90_wrapper.c",
            "derived_types_mixed_bind_c_f90_wrapper.h",
            "bind_c_derived_types_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "derived_types_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    value = module.point(x=np.float64(2.0), y=np.float64(3.0))
    assert module.direct_sum(value) == np.float64(5.0)
    assert module.adapted_sum_by_value(value) == np.float64(5.0)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_derived_types_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_sum_by_value" in bridge
        assert "direct_sum" not in bridge


def test_derived_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "derived_types_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_sum(", "@nogil\ndef direct_sum(").replace(
        "def adapted_sum_by_value(", "@nogil\ndef adapted_sum_by_value("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    value = module.point(x=np.float64(2.0), y=np.float64(3.0))
    assert module.direct_sum(value) == np.float64(5.0)
    assert module.adapted_sum_by_value(value) == np.float64(5.0)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_sum_by_value" in bridge
    assert "function bind_c_direct_sum" not in bridge
