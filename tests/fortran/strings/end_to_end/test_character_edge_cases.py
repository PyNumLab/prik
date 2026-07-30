"""Character copy-in/copy-out, length, Unicode, and NUL tests."""

from pathlib import Path

import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_pyi_extension

FIXTURES = Path(__file__).parent / "fixtures"
CHARACTER_EDGES_F90_SOURCE = FIXTURES / "fcharacter_edges_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"

pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture
def compiled_character_edges_module(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    return _build_source_or_generated_pyi_and_import(
        CHARACTER_EDGES_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fcharacter_edges_f90_wrapper.f90",
            "fcharacter_edges_f90_wrapper.c",
            "fcharacter_edges_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fcharacter_edges_f90",
        pyi_parity_build_mode,
    )


def test_fortran_character_edge_cases_follow_copy_in_copy_out_policy(
    compiled_character_edges_module,
    monkeypatch: pytest.MonkeyPatch,
):
    module = compiled_character_edges_module

    original = "abc     "
    assert module.fixed_inout(original) == "Zbc    !"
    assert original == "abc     "
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.fixed_inout("abc")
    assert module.fixed_inout("abcdefgh") == "Zbcdefg!"
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.fixed_inout("abcdefghi")
    assert module.assumed_inout("abc") == "Qbc"
    assert module.assumed_inout("") == ""
    assert module.optional_inout() is None
    assert module.optional_inout(None) is None
    assert module.optional_inout("abc") == "Pbc"
    assert module.make_out() == "go    "
    assert module.unicode_echo("café") == "café"

    with pytest.raises(TypeError, match="embedded NUL"):
        module.assumed_inout("a\0b")
    with pytest.raises(TypeError, match="embedded NUL"):
        module.unicode_echo("a\0b")

    monkeypatch.setenv("X2PY_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError, match="Unable to allocate copy-return output string"):
        module.make_out()
    assert module.optional_inout() is None
    assert module.optional_inout(None) is None
    with pytest.raises(MemoryError, match="Unable to allocate mutable string buffer for argument name"):
        module.assumed_inout("abc")
    with pytest.raises(MemoryError, match="Unable to allocate mutable string buffer for argument label"):
        module.optional_inout("abc")


def test_fixed_string_replacement_and_identity_use_canonical_plan(
    tmp_path: Path,
    monkeypatch,
):
    """Replay projected and discarded mutation against one existing native routine."""
    native_object = _compile_native_object(CHARACTER_EDGES_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "fixed_string_writeback"
    contract_package.mkdir()
    (contract_package / "__init__.pyi").write_text(
        "from .fcharacter_edges_f90 import fixed_discard, fixed_replacement\n",
        encoding="utf-8",
    )
    (contract_package / "fcharacter_edges_f90.pyi").write_text(
        """from x2py.contracts import Returns, String, bind

@bind("fixed_inout")
def fixed_replacement(name: String[8]) -> Returns["name", String[8]]: ...

@bind("fixed_inout")
def fixed_discard(name: String[8]) -> None: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    module = package if hasattr(package, "fixed_replacement") else _sole_native_module(package)

    original = "abc     "
    assert module.fixed_replacement(original) == "Zbc    !"
    assert original == "abc     "
    assert module.fixed_discard(original) is None
    assert original == "abc     "
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.fixed_replacement("abc")
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.fixed_discard("abcdefghi")

    monkeypatch.setenv("X2PY_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError, match="Unable to allocate mutable string buffer for argument name"):
        module.fixed_replacement("abc     ")
