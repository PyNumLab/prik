"""Compiled standard-descriptor direct and mixed entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from prik.contracts import Allocatable, Float64, Pointer
from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_descriptors_all_direct_route_preserves_three_states_and_handle_mutation(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "allocatables_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "allocatables_direct_bind_c_f90_wrapper.c",
            "allocatables_direct_bind_c_f90_wrapper.h",
            "bind_c_allocatables_direct_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "allocatables_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    values = Allocatable[Float64[:]]()
    assert module.direct_optional_state() == np.int32(0)
    assert module.direct_optional_state(None) == np.int32(0)
    assert module.direct_optional_state(values) == np.int32(1)
    assert module.direct_allocate(values) is values
    np.testing.assert_array_equal(values.to_numpy(), np.array([1.0, 2.0, 3.0], dtype=np.float64))
    assert module.direct_optional_state(values) == np.int32(2)

    pointer = Pointer[Float64[:]]()
    assert pointer.associated is False
    assert module.direct_pointer_sum(pointer) == np.float64(-1.0)

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "allocatables_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "int32_t direct_optional_state(CFI_cdesc_t * values);" in binding
        assert "void direct_allocate(CFI_cdesc_t * values);" in binding
        support = (
            (tmp_path / "source_build" / "bind_c_allocatables_direct_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_owned" in support
        assert "direct_optional_state" not in support
        assert "direct_allocate" not in support
        assert "direct_pointer_sum" not in support

    pointer.close()
    values.close()


def test_descriptors_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "allocatables_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_allocate(", "@nogil\ndef direct_allocate(").replace(
        "def adapted_sum(", "@nogil\ndef adapted_sum("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    values = Allocatable[Float64[:]]()
    assert module.direct_allocate(values) is values
    assert module.adapted_sum(values) == np.float64(6.0)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_sum" in bridge
    assert "subroutine bind_c_direct_allocate" not in bridge
    values.close()


def test_descriptors_mixed_route_adapts_only_ordinary_descriptor_operation(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "allocatables_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "allocatables_mixed_bind_c_f90_wrapper.c",
            "allocatables_mixed_bind_c_f90_wrapper.h",
            "bind_c_allocatables_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "allocatables_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    values = Allocatable[Float64[:]]()
    assert module.direct_allocate(values) is values
    assert module.adapted_sum(values) == np.float64(6.0)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_allocatables_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_sum" in bridge
        assert "direct_allocate" not in bridge

    values.close()
