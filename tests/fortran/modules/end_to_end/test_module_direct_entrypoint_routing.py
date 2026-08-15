"""Compiled direct procedures with independently generated module-state support."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_module_state_direct_route_emits_support_only_fortran(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "modules_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "modules_direct_bind_c_f90_wrapper.c",
            "modules_direct_bind_c_f90_wrapper.h",
            "bind_c_modules_direct_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "modules_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.limit == np.int32(12)
    assert module.counter == np.int32(3)
    assert module.direct_total(np.int32(4)) == np.int32(7)
    module.direct_set_counter(np.int32(9))
    assert module.counter == np.int32(9)
    assert module.direct_total(np.int32(4)) == np.int32(13)

    if pyi_parity_build_mode == "source":
        support = (
            (tmp_path / "source_build" / "bind_c_modules_direct_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_get_counter" in support
        assert "bind_c_set_counter" in support
        assert "direct_total" not in support
        assert "direct_set_counter" not in support


def test_module_state_mixed_route_separates_adapter_and_support_membership(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "modules_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "modules_mixed_bind_c_f90_wrapper.c",
            "modules_mixed_bind_c_f90_wrapper.h",
            "bind_c_modules_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "modules_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_total(np.int32(4)) == np.int32(7)
    assert module.adapted_total(np.int32(4)) == np.int32(7)
    module.counter = np.int32(8)
    assert module.direct_total(np.int32(4)) == np.int32(12)
    assert module.adapted_total(np.int32(4)) == np.int32(12)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_modules_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_get_counter" in bridge
        assert "bind_c_adapted_total" in bridge
        assert "direct_total" not in bridge


def test_module_state_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "modules_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_total(", "@nogil\ndef direct_total(").replace(
        "def adapted_total(", "@nogil\ndef adapted_total("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    assert module.direct_total(np.int32(4)) == np.int32(7)
    assert module.adapted_total(np.int32(4)) == np.int32(7)
    module.counter = np.int32(8)
    assert module.direct_total(np.int32(4)) == np.int32(12)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_get_counter" in bridge
    assert "bind_c_adapted_total" in bridge
    assert "function bind_c_direct_total" not in bridge
