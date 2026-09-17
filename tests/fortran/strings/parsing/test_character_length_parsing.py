"""Declaration parsing, interfaces, and less common scope edges."""

from prik.parsers.fortran import parse_fortran_file
from prik.parsers.fortran.models import FortranVariable


def test_character_entity_lengths_and_assumed_bounds_are_preserved():
    code = """
      subroutine label(name, table)
      character name*6
      real table(0:)
      end
"""

    sig = parse_fortran_file(code, filename="label.f").procedures[0]
    args = {arg.name: arg for arg in sig.arguments}

    assert args["name"].base_type == "character"
    assert args["name"].kind == "6"
    assert args["name"].character_length_syntax is True
    assert args["table"].shape == ["0:"]
    assert args["table"].lbound == ["0"]
    assert args["table"].ubound == [None]


def test_a_character_selector_separates_a_comma_bearing_kind_from_its_length():
    """Either selector expression may hold commas, so both are read whole."""
    parsed = parse_fortran_file(
        """\
module selector_mod
  use iso_c_binding, only : c_char
  implicit none
  character(len=8, kind=max(c_char, 1)) :: spread_out
end module selector_mod
""",
        filename="selector.f90",
    )
    declared = parsed.modules[0].variables[0]

    assert declared.character_length_expression == "8"
    assert declared.character_kind_expression == "max(c_char, 1)"
    assert declared.character_length_syntax is False


def test_a_character_model_states_only_the_selector_it_records():
    """The `kind` text alone cannot say whether it spells a length or a kind.

    Every producer of a character model records its selector through one
    reader, so a model built without one states neither -- which is what a
    bare `character` declaration means -- rather than leaving a second reader
    to guess from the joined text.
    """
    bare = FortranVariable(name="text", base_type="character", kind="c_char")

    assert bare.character_length_expression is None
    assert bare.character_kind_expression is None
    assert bare.character_length_syntax is False

    named = FortranVariable(name="text", base_type="character", kind="len=12, kind=c_char")
    named.record_character_selector("(len=12, kind=c_char)")

    assert named.character_length_expression == "12"
    assert named.character_kind_expression == "c_char"
    assert named.character_length_syntax is False

    positional = FortranVariable(name="text", base_type="character", kind="8")
    positional.record_character_selector("(8)")

    assert positional.character_length_expression == "8"
    assert positional.character_kind_expression is None
    assert positional.character_length_syntax is True
