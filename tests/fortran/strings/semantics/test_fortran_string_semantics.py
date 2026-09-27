"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

import pytest

from prik.semantics.fortran2ir import collect_semantic_compile_time_requirements, fortran_module_to_semantic_module
from tests.fortran._support.semantic_conversion import get_function
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_scalar_character_inout_is_projected_as_replacement_return():
    parsed = parse_fortran_source(
        """
module chars
contains
  subroutine normalize(name)
    character(len=8), intent(inout) :: name
  end subroutine normalize
end module chars
"""
    )

    func = get_function(fortran_module_to_semantic_module(parsed), "normalize")
    mapping = func.projection[0]

    assert func.arguments[0].semantic_type.name == "String"
    assert mapping.python_position == 0
    assert mapping.native_position == 0
    assert mapping.result_position == 0


def test_a_character_length_keeps_the_commas_its_own_expression_holds():
    """The selector's two expressions are separated, not split back apart.

    `len=` and `kind=` are one parenthesized selector, and either may hold a
    comma of its own, so finding the length inside a joined spelling cuts an
    expression such as `max(4, n)` short at its first comma.
    """
    parsed = parse_fortran_source(
        """
module selector_mod
  use iso_c_binding, only : c_char
  implicit none
contains
  subroutine take(n, name)
    integer, intent(in) :: n
    character(len=max(4, n), kind=c_char), intent(in) :: name
  end subroutine take
end module selector_mod
""",
        filename="selector_mod.f90",
    )

    function = get_function(fortran_module_to_semantic_module(parsed.modules[0]), "take")
    argument = next(item for item in function.arguments if item.name == "name")

    assert argument.semantic_type.metadata["fortran_character_length"] == "max(4, n)"


def test_every_character_declaration_form_states_its_own_length():
    """Separating the length leaves the ordinary spellings reading as before."""
    parsed = parse_fortran_source(
        """
module forms_mod
  implicit none
  integer, parameter :: fixed = 6
contains
  subroutine forms(a, b, c, d, e)
    character(len=16), intent(in) :: a
    character(8), intent(in) :: b
    character(*), intent(in) :: c
    character(len=fixed), intent(in) :: d
    character, intent(in) :: e
  end subroutine forms
end module forms_mod
""",
        filename="forms_mod.f90",
    )

    function = get_function(fortran_module_to_semantic_module(parsed.modules[0]), "forms")
    lengths = {item.name: item.semantic_type.metadata.get("fortran_character_length") for item in function.arguments}

    assert lengths == {"a": "16", "b": "8", "c": "*", "d": "6", "e": "1"}


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        pytest.param("selected_char_kind('ISO_10646')", "UString", id="iso-10646"),
        pytest.param("ucs4", "UString", id="iso-10646-parameter"),
        pytest.param("selected_char_kind('ASCII')", "String", id="ascii"),
        pytest.param("selected_char_kind('DEFAULT')", "String", id="default"),
        pytest.param("c_char", "String", id="c-char"),
    ],
)
def test_character_kind_selects_the_string_width(kind: str, expected: str):
    """A character kind names UCS-4 or the one-byte kind without a compiler probe.

    The kind is read from the character set it selects, never from a kind
    number, which each compiler assigns for itself.
    """
    parsed = parse_fortran_source(
        f"""
module kinds
  use iso_c_binding, only: c_char
  integer, parameter :: ucs4 = selected_char_kind('ISO_10646')
contains
  function copy(text) result(out)
    character(kind={kind}, len=4), intent(in) :: text
    character(kind={kind}, len=4) :: out
    out = text
  end function copy
end module kinds
"""
    )

    func = get_function(fortran_module_to_semantic_module(parsed), "copy")

    assert func.arguments[0].semantic_type.name == expected
    assert func.return_type.name == expected


NUMERIC_KIND_SOURCE = """
module kinds
contains
  subroutine take(text)
    character(kind=4, len=4), intent(in) :: text
  end subroutine take
end module kinds
"""


@pytest.mark.parametrize(
    ("ucs4_number", "expected"),
    [
        pytest.param(4, "UString", id="compiler-numbers-ucs4-as-4"),
        pytest.param(-1, None, id="compiler-without-ucs4"),
    ],
)
def test_numeric_character_kind_reads_the_compiler_character_sets(ucs4_number: int, expected: str | None):
    """A numeric kind is whichever character set the target compiler numbers that way."""
    parsed = parse_fortran_source(NUMERIC_KIND_SOURCE)
    requirements = collect_semantic_compile_time_requirements(parsed)
    assert {item["expression"] for item in requirements if item["code"] == "character_set"} == {
        "selected_char_kind('DEFAULT')",
        "selected_char_kind('ASCII')",
        "selected_char_kind('ISO_10646')",
    }
    probed = {
        "selected_char_kind('DEFAULT')": 1,
        "selected_char_kind('ASCII')": 1,
        "selected_char_kind('ISO_10646')": ucs4_number,
    }

    if expected is None:
        with pytest.raises(ValueError, match="numbers no default, ASCII, or ISO_10646 character set as kind 4"):
            fortran_module_to_semantic_module(parsed, compile_time_values=probed)
        return
    func = get_function(fortran_module_to_semantic_module(parsed, compile_time_values=probed), "take")
    assert func.arguments[0].semantic_type.name == expected
