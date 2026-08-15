"""Compiled direct and mixed enumeration/constant entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_enumerations_all_direct_route_keeps_integer_constants_and_abi(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "enumerations_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"enumerations_direct_bind_c_f90_wrapper.c", "enumerations_direct_bind_c_f90_wrapper.h"},
        FIXTURES / "contracts" / "enumerations_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert (module.stopped, module.ready, module.running, module.terminal) == tuple(
        np.int32(value) for value in (-1, 0, 4, 5)
    )
    assert module.direct_round_trip(module.running) == np.int32(4)
    assert module.direct_next(module.running) == np.int32(5)
    assert not hasattr(module, "Enum")


def test_enumerations_mixed_route_adapts_only_ordinary_operation(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "enumerations_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "enumerations_mixed_bind_c_f90_wrapper.c",
            "enumerations_mixed_bind_c_f90_wrapper.h",
            "bind_c_enumerations_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "enumerations_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_round_trip(module.running) == np.int32(4)
    assert module.adapted_next(module.running) == np.int32(5)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_enumerations_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_next" in bridge
        assert "direct_round_trip" not in bridge


def test_enumerations_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "enumerations_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_round_trip(", "@nogil\ndef direct_round_trip(").replace(
        "def adapted_next(", "@nogil\ndef adapted_next("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    assert module.direct_round_trip(module.running) == np.int32(4)
    assert module.adapted_next(module.running) == np.int32(5)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_next" in bridge
    assert "function bind_c_direct_round_trip" not in bridge
