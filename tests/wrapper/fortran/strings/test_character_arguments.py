"""Fixed-form and modern scalar character argument/result tests."""

from pathlib import Path
import shutil

import numpy as np
import pytest

from tests.wrapper.fortran._support import (
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _assert_legacy_string_examples,
    _assert_modern_string_examples,
    _sole_native_module,
    wrapper_source,
)
from x2py import build_pyi_extension

STRING_LEGACY_SOURCE = wrapper_source("fstrings.f")
STRING_F90_SOURCE = wrapper_source("fstrings_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"


def _build_contract_module(contract: Path, native_object: Path, output_dir: Path, symbol: str):
    """Build one edited character contract through the canonical wrapper plan."""
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    return package if hasattr(package, symbol) else _sole_native_module(package)


def test_legacy_fortran_character_arguments_and_results(pyi_parity_build_mode: str, tmp_path: Path):
    module = _build_source_or_generated_pyi_and_import(
        STRING_LEGACY_SOURCE,
        tmp_path,
        {
            "bind_c_fstrings_wrapper.f90",
            "fstrings_wrapper.c",
            "fstrings_wrapper.h",
        },
        CONTRACT_FIXTURES / "fstrings",
        pyi_parity_build_mode,
    )

    _assert_legacy_string_examples(module)


def test_modern_fortran_character_arguments_and_results(pyi_parity_build_mode: str, tmp_path: Path):
    module = _build_source_or_generated_pyi_and_import(
        STRING_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fstrings_f90_wrapper.f90",
            "fstrings_f90_wrapper.c",
            "fstrings_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fstrings_f90",
        pyi_parity_build_mode,
    )

    _assert_modern_string_examples(module)


def test_edited_modern_string_contract_wraps_full_axis_spelling_set(tmp_path: Path):
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        CONTRACT_FIXTURES / "fstrings_f90_axes" / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_axes_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert module.string_len_assumed("variable length") == 15
    assert module.string_len_fixed("short   ") == 5
    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent(labels) == 16

    label = np.array("abcdefgh", dtype="S8")
    assert module.rewrite_storage(label) is None
    assert label[()] == b"Ybcdefg?"


def test_fixed_width_character_arrays_use_canonical_plan(tmp_path: Path):
    """Replay one ordinary fixed-width NumPy bytes array without descriptors."""
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "character_array"
    shutil.copytree(CONTRACT_FIXTURES / "fstrings_f90_axes", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "from .fstrings_f90 import fixed_array_extent\n",
        encoding="utf-8",
    )
    module = _build_contract_module(
        contract_package / "__init__.pyi", native_object, tmp_path / "build", "fixed_array_extent"
    )

    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent(labels) == 16
    assert module.fixed_array_extent(np.empty(0, dtype="S8")) == 0

    with pytest.raises(TypeError):
        module.fixed_array_extent(np.array([b"short"], dtype="S7"))
    with pytest.raises(TypeError):
        module.fixed_array_extent(np.array([[b"label"]], dtype="S8"))


def test_raw_fixed_width_character_arrays_use_canonical_plan(tmp_path: Path):
    """Replay one fixed-width character array through its raw address contract."""
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "raw_character_array"
    contract_package.mkdir()
    (contract_package / "__init__.pyi").write_text(
        "from .fstrings_f90 import fixed_array_extent_raw\n",
        encoding="utf-8",
    )
    (contract_package / "fstrings_f90.pyi").write_text(
        """from x2py.contracts import Addr, Int32, String, bind

@bind("fixed_array_extent")
def fixed_array_extent_raw(labels: Addr(String[8][2])) -> Int32: ...
""",
        encoding="utf-8",
    )
    module = _build_contract_module(
        contract_package / "__init__.pyi", native_object, tmp_path / "build", "fixed_array_extent_raw"
    )

    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent_raw(labels.ctypes.data) == 16
    with pytest.raises(TypeError):
        module.fixed_array_extent_raw(labels)


def test_required_scalar_string_inputs_use_canonical_plan(tmp_path: Path):
    """Reuse the existing modern string unit through one scalar-input-only entry."""
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "string_inputs"
    shutil.copytree(CONTRACT_FIXTURES / "fstrings_f90", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "\n".join(
            (
                "from .fstrings_f90 import char_code_default",
                "from .fstrings_f90 import char_code_len1",
                "from .fstrings_f90 import char_code_kind1",
                "from .fstrings_f90 import char_code_c_char",
                "from .fstrings_f90 import string_len_fixed",
                "from .fstrings_f90 import string_len_assumed",
                "from .fstrings_f90 import string_len_c_char",
                "",
            )
        ),
        encoding="utf-8",
    )
    module = _build_contract_module(
        contract_package / "__init__.pyi", native_object, tmp_path / "build", "char_code_default"
    )

    assert module.char_code_default("A") == ord("A")
    assert module.char_code_len1(np.str_("B")) == ord("B")
    assert module.char_code_kind1("C") == ord("C")
    assert module.char_code_c_char("D") == ord("D")
    assert module.string_len_fixed("short   ") == 5
    assert module.string_len_assumed("variable length") == 15
    assert module.string_len_assumed("") == 0
    assert module.string_len_assumed("café") == 5
    assert module.string_len_c_char("c-char  ") == 6

    with pytest.raises(TypeError, match="str"):
        module.string_len_assumed(b"bytes")
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.string_len_fixed("short")
    with pytest.raises(TypeError, match="embedded NUL"):
        module.string_len_assumed("a\0b")


def test_deferred_allocatable_string_results_use_canonical_plan(
    tmp_path: Path,
    monkeypatch,
):
    """Replay a nullable rank-zero descriptor result as a copied Python string."""
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "deferred_string_result"
    shutil.copytree(CONTRACT_FIXTURES / "fstrings_f90", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "from .fstrings_f90 import string_result_deferred\n",
        encoding="utf-8",
    )
    module = _build_contract_module(
        contract_package / "__init__.pyi", native_object, tmp_path / "build", "string_result_deferred"
    )

    assert module.string_result_deferred("dynamic") == "dynamic-deferred"
    assert module.string_result_deferred("café") == "café-deferred"

    monkeypatch.setenv("X2PY_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError):
        module.string_result_deferred("failure")


def test_deferred_character_array_handles_use_canonical_plan(tmp_path: Path):
    """Keep runtime element width and projected identity on one shared handle path."""
    module_name = "deferred_character_handles_plan"
    source = tmp_path / f"{module_name}.f90"
    source.write_text(
        f"""
module {module_name}
  use iso_c_binding, only: c_char
contains
  subroutine make_names(names)
    character(kind=c_char, len=:), allocatable, intent(out) :: names(:)
    allocate(character(kind=c_char, len=3) :: names(2))
    names = [character(kind=c_char, len=3) :: "red", "sky"]
  end subroutine make_names

  function make_names_function() result(names)
    character(kind=c_char, len=:), allocatable :: names(:)
    allocate(character(kind=c_char, len=4) :: names(2))
    names = [character(kind=c_char, len=4) :: "gold", "blue"]
  end function make_names_function

  subroutine maybe_name(flag, name)
    integer(kind=4), intent(in) :: flag
    character(kind=c_char, len=:), allocatable, intent(out) :: name
    if (flag /= 0) then
      allocate(character(kind=c_char, len=4) :: name)
      name = "blue"
    end if
  end subroutine maybe_name

  subroutine replace_names(names)
    character(kind=c_char, len=:), allocatable, intent(inout) :: names(:)
    integer :: count
    count = 2
    if (allocated(names)) count = size(names)
    if (allocated(names)) deallocate(names)
    allocate(character(kind=c_char, len=5) :: names(count))
    names = "     "
    if (count >= 1) names(1) = "red"
    if (count >= 2) names(2) = "blue"
  end subroutine replace_names
end module {module_name}
""",
        encoding="utf-8",
    )
    contract = tmp_path / f"{module_name}.pyi"
    contract.write_text(
        """
from x2py.contracts import Allocatable, Arg, Int32, Return, Returns, String, native_call

@native_call([Return("names", 0)])
def make_names() -> Allocatable[String[:][:]]: ...

def make_names_function() -> Allocatable[String[:][:]]: ...

@native_call([Arg(0), Allocatable(Return("name", 0))])
def maybe_name(flag: Int32) -> String | None: ...

def replace_names(
    names: Allocatable[String[:][:]],
) -> Returns["names", Allocatable[String[:][:]]]: ...
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native_character_handles")
    module = _build_contract_module(contract, native_object, tmp_path / "build", "make_names")
    handle = module.make_names()
    assert handle.allocated is True
    assert handle.dtype == np.dtype("S3")
    assert handle.to_numpy().tolist() == [b"red", b"sky"]

    assert module.replace_names(handle) is handle
    assert handle.dtype == np.dtype("S5")
    assert handle.to_numpy().tolist() == [b"red  ", b"blue "]

    direct_handle = module.make_names_function()
    assert direct_handle.allocated is True
    assert direct_handle.dtype == np.dtype("S4")
    assert direct_handle.to_numpy().tolist() == [b"gold", b"blue"]
    assert module.maybe_name(np.int32(0)) is None
    assert module.maybe_name(np.int32(1)) == "blue"


def test_fixed_string_results_use_canonical_plan(tmp_path: Path, monkeypatch):
    """Replay existing fixed direct results through a result-only contract entry."""
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "string_results"
    shutil.copytree(CONTRACT_FIXTURES / "fstrings_f90", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "\n".join(
            (
                "from .fstrings_f90 import char_result_default",
                "from .fstrings_f90 import char_result_c_char",
                "from .fstrings_f90 import string_result_fixed",
                "from .fstrings_f90 import string_result_padded",
                "from .fstrings_f90 import string_result_c_char",
                "",
            )
        ),
        encoding="utf-8",
    )
    module = _build_contract_module(
        contract_package / "__init__.pyi", native_object, tmp_path / "build", "char_result_default"
    )

    assert module.char_result_default() == "M"
    assert module.char_result_c_char() == "C"
    assert module.string_result_fixed() == "MODERN!!"
    assert module.string_result_padded() == "PAD     "
    assert module.string_result_c_char() == "C-CHAR!!"

    monkeypatch.setenv("X2PY_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError, match="Unable to allocate copy-return output string"):
        module.string_result_fixed()
