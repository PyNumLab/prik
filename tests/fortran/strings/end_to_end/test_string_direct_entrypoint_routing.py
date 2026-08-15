"""Compiled direct and mixed scalar-character entrypoint evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_strings_all_direct_route_preserves_value_mutation_and_validation(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "strings_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"strings_direct_bind_c_f90_wrapper.c", "strings_direct_bind_c_f90_wrapper.h"},
        FIXTURES / "contracts" / "strings_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_char_code("A") == np.int32(65)
    assert module.direct_uppercase("b") == "B"
    with pytest.raises(TypeError, match="embedded NUL"):
        module.direct_char_code("\0")
    with pytest.raises(TypeError):
        module.direct_char_code("é")

    buffer = np.array([b"a", b"\0", b"z"], dtype="S1")
    assert module.direct_buffer_sum(np.int32(buffer.size), buffer) == np.int32(ord("a") + ord("z"))
    replacement = module.direct_uppercase_buffer(np.int32(buffer.size), buffer)
    np.testing.assert_array_equal(buffer, np.array([b"A", b"\0", b"Z"], dtype="S1"))
    if replacement is not None:
        np.testing.assert_array_equal(replacement, buffer)

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "strings_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "int32_t direct_char_code(char ch);" in binding
        assert "void direct_uppercase(char * ch);" in binding
        assert "int32_t direct_buffer_sum(int32_t n, char * text);" in binding
        assert "void direct_uppercase_buffer(int32_t n, char * text);" in binding


def test_strings_mixed_route_keeps_only_fixed_length_adapter(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "strings_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "strings_mixed_bind_c_f90_wrapper.c",
            "strings_mixed_bind_c_f90_wrapper.h",
            "bind_c_strings_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "strings_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_char_code("C") == np.int32(67)
    assert module.adapted_fixed_code("D   ") == np.int32(68)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_strings_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_fixed_code" in bridge
        assert "direct_char_code" not in bridge


def test_strings_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "strings_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_char_code(", "@nogil\ndef direct_char_code(").replace(
        "def adapted_fixed_code(", "@nogil\ndef adapted_fixed_code("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    assert module.direct_char_code("C") == np.int32(67)
    assert module.adapted_fixed_code("D   ") == np.int32(68)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_fixed_code" in bridge
    assert "function bind_c_direct_char_code" not in bridge
