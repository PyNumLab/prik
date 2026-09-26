"""Generated overload sets, generics, and defined operators reload from their contracts."""

from pathlib import Path

from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.printer_models import (
    OPERATOR_F90_SOURCE,
    generate_pyi,
    generate_wrapper,
    parse_pyi_text,
    rendered_source,
)

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def test_emit_and_load_module_and_type_bound_overload_sets():
    source = (NATIVE_FIXTURES / "emit_and_load_module_and_type_bound_overload_sets.f90").read_text(encoding="utf-8")
    code = generate_pyi(source)

    assert "from typing import overload" not in code
    assert code.count('@overload("convert_integer")\ndef convert(') == 1
    assert code.count('@overload("convert_real")\ndef convert(') == 1
    assert code.count('    @bind("set")\n    @overload("set_integer")\n    def set(') == 1
    assert code.count('    @bind("set")\n    @overload("set_real")\n    def set(') == 1
    assert '@overload("convert_integer")\n@native_call' not in code
    assert '    @overload("set_integer")\n    @native_call' not in code

    loaded = parse_pyi_text(code, module_name="generic_mod")
    assert [(item.name, len(item.procedures)) for item in loaded.overload_sets] == [("convert", 2)]
    assert [procedure.name for procedure in loaded.overload_sets[0].procedures] == [
        "convert_integer",
        "convert_real",
    ]
    assert loaded.imports == []
    assert [(item.name, len(item.procedures)) for item in loaded.classes[0].overload_sets] == [("set", 2)]
    assert [procedure.name for procedure in loaded.classes[0].overload_sets[0].procedures] == [
        "set_integer",
        "set_real",
    ]
    assert {procedure.native_name for procedure in loaded.classes[0].overload_sets[0].procedures} == {"set"}


def test_private_module_generic_specifics_bind_overload_candidates_to_public_generic():
    source = """
module generic_mod
  implicit none
  private
  public :: convert
  interface convert
    module procedure convert_integer, convert_real
  end interface convert
contains
  integer function convert_integer(value)
    integer :: value
    convert_integer = value
  end function convert_integer
  real function convert_real(value)
    real :: value
    convert_real = value
  end function convert_real
end module generic_mod
"""

    code = generate_pyi(source)

    assert code.count('@bind("convert")\n@overload("convert_integer")') == 1
    assert code.count('@bind("convert")\n@overload("convert_real")') == 1
    loaded = parse_pyi_text(code, module_name="generic_mod")
    assert [procedure.native_name for procedure in loaded.overload_sets[0].procedures] == [
        "convert",
        "convert",
    ]
    assert emit_module(loaded) == code


def test_public_type_bound_generic_specifics_do_not_emit_bind():
    source = """
module generic_mod
  type :: box
  contains
    procedure :: set_integer
    procedure :: set_real
    generic :: set => set_integer, set_real
  end type box
contains
  subroutine set_integer(self, value)
    class(box) :: self
    integer :: value
  end subroutine set_integer
  subroutine set_real(self, value)
    class(box) :: self
    real :: value
  end subroutine set_real
end module generic_mod
"""

    code = generate_pyi(source)

    assert '    @bind("set")' not in code
    assert code.count('    @overload("set_integer")\n    def set(') == 1
    assert code.count('    @overload("set_real")\n    def set(') == 1
    loaded = parse_pyi_text(code, module_name="generic_mod")
    assert [procedure.native_name for procedure in loaded.classes[0].overload_sets[0].procedures] == [
        "set_integer",
        "set_real",
    ]


def test_defined_operator_pyi_round_trip_preserves_native_links_without_fortran_source():
    """Operators and assignment survive the contract and still reach their native specifics."""
    semantic_module = fortran_module_to_semantic_module(
        parse_fortran_source(OPERATOR_F90_SOURCE.read_text(), filename=str(OPERATOR_F90_SOURCE))
    )
    code = emit_module(semantic_module)

    assert '@overload("add_real_vector")' in code
    assert "def __radd__(" in code
    assert '@overload("assign_vector_real")' in code
    assert "def assign(" in code
    assert "left: Annotated[Addr(vector)" not in code
    assert "left: vector" in code
    assert '-> Returns["left", vector]: ...' in code
    assert "right: Float64\n    ) -> vector: ..." in code
    assert '@overload("dot_vectors")' in code
    assert "def operator_dot(" in code
    assert '@overload("equivalent_vector_offset", generic="operator(.eqv.)")' in code
    assert '@overload("not_equivalent_vector_integer", generic="operator(.neqv.)")' in code
    assert "from typing import overload" not in code

    loaded = parse_pyi_text(code, module_name=semantic_module.name)
    assert emit_module(loaded) == code

    generated = generate_wrapper(loaded)
    fortran_wrapper = rendered_source(generated, ".f90")
    c_wrapper = rendered_source(generated, ".c")
    assert "left + right" in fortran_wrapper
    assert "left = right" in fortran_wrapper
    assert "left .eqv. right" in fortran_wrapper
    assert " .neqv. " in fortran_wrapper
    assert "def __add__(self, *args, **kwargs):" in c_wrapper
    assert "def __ne__(self, *args, **kwargs):" in c_wrapper


def test_generic_specifics_with_projected_outputs_round_trip():
    """A generic whose specifics project an `intent(out)` reloads from its contract.

    The declaration states the public signature, so the output the projection
    turned into a result is not one of the arguments it accepts. Comparing the
    declaration against the specific's native arguments rejected every such
    generic, which is the common shape in numerical Fortran.
    """
    source = (NATIVE_FIXTURES / "generic_specifics_with_projected_outputs_round_trip.f90").read_text(encoding="utf-8")

    code = generate_pyi(source)
    assert '@overload("ink_default")' in code
    assert '@overload("ink_extended")' in code

    module = pyi_text_to_semantic_module(code, module_name="projected_generic_mod")
    overloads = [item for item in module.overload_sets if item.name == "ink"]
    assert len(overloads) == 1
    assert [procedure.name for procedure in overloads[0].procedures] == ["ink_default", "ink_extended"]


def test_dotted_comparison_spelling_survives_contract_replay_into_the_bridge_import():
    """A compiler matches `use, only:` by spelling, so `.EQ.` stays `.EQ.` through the contract."""
    source = """
module handles
  implicit none
  private
  public :: handle_t, operator(.EQ.), operator(.LT.)
  type :: handle_t
    integer :: val = 0
  end type handle_t
  interface operator (.EQ.)
    module procedure handle_eq
  end interface operator (.EQ.)
  interface operator (.LT.)
    module procedure handle_lt
  end interface operator (.LT.)
contains
  logical function handle_eq(a, b)
    type(handle_t), intent(in) :: a, b
    handle_eq = a%val == b%val
  end function handle_eq
  logical function handle_lt(a, b)
    type(handle_t), intent(in) :: a, b
    handle_lt = a%val < b%val
  end function handle_lt
end module handles
"""
    semantic_module = fortran_module_to_semantic_module(parse_fortran_source(source, filename="handles.f90"))
    pyi = emit_module(semantic_module)
    loaded = parse_pyi_text(pyi, module_name=semantic_module.name)

    assert '@overload("handle_eq", generic="operator (.EQ.)")' in pyi
    assert '@overload("handle_lt", generic="operator (.LT.)")' in pyi
    assert emit_module(loaded) == pyi
    bridge = rendered_source(generate_wrapper(loaded), ".f90")
    assert "operator (.EQ.)" in bridge and "operator (.LT.)" in bridge
