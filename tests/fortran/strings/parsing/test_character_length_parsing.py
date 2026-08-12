"""Declaration parsing, interfaces, and less common scope edges."""

from prik.parsers.fortran import parse_fortran_file


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
