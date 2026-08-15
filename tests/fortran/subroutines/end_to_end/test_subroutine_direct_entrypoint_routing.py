"""Compiled direct and mixed reference/output entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_subroutine_all_direct_route_preserves_reference_and_projected_results(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "subroutines_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"subroutines_direct_bind_c_f90_wrapper.c", "subroutines_direct_bind_c_f90_wrapper.h"},
        FIXTURES / "contracts" / "subroutines_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_reference(np.int32(2)) == np.int32(12)
    assert module.direct_outputs(np.int32(3)) == (np.int32(4), np.int32(6), np.int32(7))

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "subroutines_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "int32_t direct_reference(int32_t * value);" in binding
        assert "void direct_outputs(int32_t * value, int32_t * doubled, int32_t * status);" in binding


def test_subroutine_mixed_route_matches_results_and_adapts_only_ordinary_operation(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "subroutines_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "subroutines_mixed_bind_c_f90_wrapper.c",
            "subroutines_mixed_bind_c_f90_wrapper.h",
            "bind_c_subroutines_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "subroutines_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    expected = (np.int32(4), np.int32(6))
    assert module.direct_outputs(np.int32(3)) == expected
    assert module.adapted_outputs(np.int32(3)) == expected

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_subroutines_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_outputs" in bridge
        assert "direct_outputs" not in bridge


def test_subroutine_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "subroutines_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_outputs(", "@nogil\ndef direct_outputs(").replace(
        "def adapted_outputs(", "@nogil\ndef adapted_outputs("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    expected = (np.int32(4), np.int32(6))
    assert module.direct_outputs(np.int32(3)) == expected
    assert module.adapted_outputs(np.int32(3)) == expected
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_outputs" in bridge
    assert "subroutine bind_c_direct_outputs" not in bridge
