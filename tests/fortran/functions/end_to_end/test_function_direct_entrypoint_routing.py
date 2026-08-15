"""Compiled direct and mixed standalone-entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_standalone_all_direct_route_uses_native_symbols_without_adapter(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "standalone_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"standalone_direct_bind_c_f90_wrapper.c", "standalone_direct_bind_c_f90_wrapper.h"},
        FIXTURES / "contracts" / "standalone_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.standalone_direct(np.int32(4)) == np.int32(6)
    assert module.standalone_output(np.int32(4)) == np.int32(12)

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "standalone_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "standalone_direct_symbol" in binding


def test_standalone_mixed_route_adapts_only_ordinary_external(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "standalone_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "standalone_mixed_bind_c_f90_wrapper.c",
            "standalone_mixed_bind_c_f90_wrapper.h",
            "bind_c_standalone_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "standalone_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.standalone_direct(np.int32(4)) == np.int32(6)
    assert module.standalone_adapted(np.int32(4)) == np.int32(7)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_standalone_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_standalone_adapted" in bridge
        assert "standalone_direct" not in bridge


def test_standalone_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "standalone_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / "__init__.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def standalone_direct(", "@nogil\ndef standalone_direct(").replace(
        "def standalone_adapted(", "@nogil\ndef standalone_adapted("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    assert module.standalone_direct(np.int32(4)) == np.int32(6)
    assert module.standalone_adapted(np.int32(4)) == np.int32(7)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_standalone_adapted" in bridge
    assert "function bind_c_standalone_direct" not in bridge
