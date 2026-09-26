"""Compiled direct and mixed standalone-entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
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
