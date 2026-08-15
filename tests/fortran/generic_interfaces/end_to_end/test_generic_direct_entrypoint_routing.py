"""Compiled per-candidate generic direct and mixed entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_generic_all_direct_route_selects_each_candidate_independently(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "generic_interfaces_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "generic_interfaces_direct_bind_c_f90_wrapper.c",
            "generic_interfaces_direct_bind_c_f90_wrapper.h",
        },
        FIXTURES / "contracts" / "generic_interfaces_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.convert(np.int32(4)) == np.int32(5)
    assert module.convert(np.float64(4.0)) == np.float64(4.5)
    assert module.increment(np.int32(4)) == np.int32(5)
    assert module.increment(np.float64(4.0)) == np.float64(4.5)

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "generic_interfaces_direct_bind_c_f90_wrapper.c").read_text(
            encoding="utf-8"
        )
        assert "direct_convert_integer" in binding
        assert "direct_convert_real" in binding
        assert "direct_increment_integer" in binding
        assert "direct_increment_real" in binding


def test_generic_mixed_route_adapts_only_ordinary_candidate(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "generic_interfaces_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "generic_interfaces_mixed_bind_c_f90_wrapper.c",
            "generic_interfaces_mixed_bind_c_f90_wrapper.h",
            "bind_c_generic_interfaces_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "generic_interfaces_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.convert(np.int32(4)) == np.int32(5)
    assert module.convert(np.float64(4.0)) == np.float64(4.5)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_generic_interfaces_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_convert_real" in bridge
        assert "convert_integer" not in bridge


def test_generic_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "generic_interfaces_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def convert_integer(", "@nogil\ndef convert_integer(")
    contract = contract.replace("def convert_real(", "@nogil\ndef convert_real(")
    contract = contract.replace("def convert(", "@nogil\ndef convert(")
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    assert module.convert(np.int32(4)) == np.int32(5)
    assert module.convert(np.float64(4.0)) == np.float64(4.5)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_convert_real" in bridge
    assert "function bind_c_convert_integer" not in bridge
