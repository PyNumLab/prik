"""Compiled numeric and C-Boolean array direct-route evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_arrays_all_direct_route_preserves_dtype_values_and_mutation(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "arrays_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"arrays_direct_bind_c_f90_wrapper.c", "arrays_direct_bind_c_f90_wrapper.h"},
        FIXTURES / "contracts" / "arrays_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64, order="F")
    assert module.sum_values(np.int32(values.size), values) == np.float64(6.0)
    scaled = module.scale_values(np.int32(values.size), values)
    np.testing.assert_array_equal(values, np.array([2.0, 4.0, 6.0], dtype=np.float64))
    if scaled is not None:
        np.testing.assert_array_equal(scaled, values)

    flags = np.array([True, True, False], dtype=np.bool_, order="F")
    assert bool(module.all_flags(np.int32(flags.size), flags)) is False
    inverted = module.invert_flags(np.int32(flags.size), flags)
    np.testing.assert_array_equal(flags, np.array([False, False, True], dtype=np.bool_))
    if inverted is not None:
        np.testing.assert_array_equal(inverted, flags)

    empty = np.empty(0, dtype=np.float64)
    assert module.sum_values(np.int32(0), empty) == np.float64(0.0)

    matrix = np.ones((2, 3), dtype=np.float64, order="F")
    matrix_result = module.scale_matrix(np.int32(2), np.int32(3), matrix)
    np.testing.assert_array_equal(matrix, np.full((2, 3), 3.0, dtype=np.float64, order="F"))
    if matrix_result is not None:
        np.testing.assert_array_equal(matrix_result, matrix)

    with pytest.raises(TypeError, match="dtype"):
        module.sum_values(np.int32(3), np.ones(3, dtype=np.float32))
    with pytest.raises(TypeError):
        module.sum_values(np.int32(3), np.ones((3, 1), dtype=np.float64, order="F"))
    with pytest.raises(TypeError, match="incompatible shape"):
        module.sum_values(np.int32(4), np.ones(3, dtype=np.float64))
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale_matrix(
            np.int32(2),
            np.int32(3),
            np.ones((2, 3), dtype=np.float64, order="C"),
        )

    read_only = np.ones(3, dtype=np.float64)
    read_only.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.scale_values(np.int32(3), read_only)

    backing = np.zeros(3 * np.dtype(np.float64).itemsize + 1, dtype=np.uint8)
    unaligned = np.ndarray((3,), dtype=np.float64, buffer=backing, offset=1)
    assert not unaligned.flags.aligned
    with pytest.raises(TypeError, match="aligned"):
        module.sum_values(np.int32(3), unaligned)

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "arrays_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "double sum_values(int32_t n, double * values);" in binding
        assert "void invert_flags(int32_t n, bool * values);" in binding
        assert "void scale_matrix(int32_t rows, int32_t columns, double * values);" in binding


def test_arrays_mixed_route_keeps_only_ordinary_array_adapter(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "arrays_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "arrays_mixed_bind_c_f90_wrapper.c",
            "arrays_mixed_bind_c_f90_wrapper.h",
            "bind_c_arrays_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "arrays_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64, order="F")
    assert module.direct_sum(np.int32(3), values) == np.float64(6.0)
    assert module.adapted_sum(np.int32(3), values) == np.float64(6.0)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_arrays_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_sum" in bridge
        assert "direct_sum" not in bridge


def test_arrays_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "arrays_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_sum(", "@nogil\ndef direct_sum(").replace(
        "def adapted_sum(", "@nogil\ndef adapted_sum("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64, order="F")
    assert module.direct_sum(np.int32(3), values) == np.float64(6.0)
    assert module.adapted_sum(np.int32(3), values) == np.float64(6.0)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_sum" in bridge
    assert "function bind_c_direct_sum" not in bridge
