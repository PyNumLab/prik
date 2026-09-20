"""Declaration parsing, interfaces, and less common scope edges."""

from prik.parsers.fortran import parse_fortran_file
from prik.parsers.fortran.models import FortranFile, FortranVariable
from prik.semantics.fortran2ir import FortranToIRConverter, collect_semantic_compile_time_requirements


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


def test_a_recorded_selector_is_what_semantics_reads_for_a_character_kind():
    """The recorded selector is the authority, not the legacy `kind` field.

    A model built through the recorder alone leaves that field empty, so
    consulting it first would report the default character kind while the
    model plainly states another one.
    """
    converter = FortranToIRConverter()

    recorded = FortranVariable(name="x", base_type="character")
    recorded.record_character_selector("(kind=c_char)")

    assert recorded.kind == ""
    assert converter._semantic_kind_key(recorded) == "c_char"
    assert converter._target_type_key(recorded) == ("character", "c_char")

    unsupported = FortranVariable(name="x", base_type="character")
    unsupported.record_character_selector("(kind=bad)")
    requirements = collect_semantic_compile_time_requirements(FortranFile(variables=[unsupported]))

    assert [(item["symbol"], item["kind"], item["expression"]) for item in requirements] == [("x", "bad", "bad")]
