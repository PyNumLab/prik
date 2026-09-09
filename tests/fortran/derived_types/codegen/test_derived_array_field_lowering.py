"""Bridge lowering for live views over fixed derived-type array fields."""

from __future__ import annotations

from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.printers.fortran import FortranSourcePrinter
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules


ARRAY_FIELD_SOURCE = """
module field_state
  use iso_fortran_env, only: real64
  implicit none

  type :: box
    real(real64) :: grid(2, 3)
  end type box

  type(box) :: plain_box
  type(box), target :: tgt_box
end module field_state
"""


def _bridge_source_for(source: str, module_name: str) -> str:
    parsed = parse_fortran_project({f"{module_name}.f90": source})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    return FortranSourcePrinter().visit(FortranBridgeGenerator().visit(plan))


def _bridge_source():
    return _bridge_source_for(ARRAY_FIELD_SOURCE, "field_state")


def test_owned_array_field_takes_its_address_through_the_owner_pointer():
    """An owner reached as a pointer makes its components addressable.

    The owner arrives as an address and is associated with a Fortran pointer, so
    its components are subobjects of a pointer target. `c_loc` may name them
    whatever the field's own declaration said, and no capture is needed.
    """
    source = _bridge_source()

    assert "result = c_loc(owner%grid)" in source
    assert "extent_0 = int(size(owner%grid, 1), c_int64_t)" in source


def test_plain_module_object_field_captures_its_address_in_c():
    """A plain module object is named directly, so nothing about it is a target.

    `c_loc` cannot name a member of a module object that was declared without
    `target`, so the address is taken on the C side, exactly as a non-addressable
    module array's is.
    """
    source = _bridge_source()

    assert "result = prik_capture_address(native_plain_box%grid)" in source
    assert "c_loc(native_plain_box%grid)" not in source


def _procedure(source: str, name: str) -> str:
    """Return the text of one generated procedure, by name."""
    start = source.index(f"function {name}(")
    return source[start : source.index(f"end function {name}", start)]


def test_array_field_getters_report_extents_instead_of_passing_a_descriptor():
    """A fixed field's rank and contiguity are known, so extents carry everything.

    The earlier lowering handed the component to a C consumer as a descriptor
    purely to reach its base address. A fixed component is contiguous and its
    rank is fixed, so the base pointer plus one extent per axis says the same
    thing without a callback round-trip, and the getter returns an address
    rather than driving a consumer.
    """
    source = _bridge_source()

    for name in ("bind_c_prik_field_box_grid_get", "bind_c_prik_module_field_plain_box_grid_get"):
        getter = _procedure(source, name)
        assert "type(c_ptr) :: result" in getter
        assert "c_funptr" not in getter
        assert "c_f_procpointer" not in getter

    # No descriptor-consumer interface is declared for an ordinary array field.
    assert "_grid_consumer" not in source


def test_deferred_character_pointer_field_uses_only_legal_inquiry_entrypoints():
    source = _bridge_source_for(
        """
module deferred_field_state
  implicit none
  type :: box
    character(len=:), pointer :: words(:) => null()
  end type box
  type(box) :: plain_box
end module deferred_field_state
""",
        "deferred_field_state",
    )

    shape = _procedure(source, "bind_c_prik_field_handle_box_words_shape")
    assert "logical(c_bool) :: result" in shape
    assert "result = associated(owner%words)" in shape
    assert "_words_consumer" not in source
    assert "character(kind=c_char, len=:), pointer, dimension(:), intent(inout)" not in source


def test_fixed_character_descriptor_fields_use_guarded_ordinary_projections():
    source = _bridge_source_for(
        """
module fixed_character_fields
  implicit none
  type :: box
    character(len=5), allocatable :: words(:)
    character(len=5), pointer :: aliases(:) => null()
  end type box
  type(box) :: plain_box
end module fixed_character_fields
""",
        "fixed_character_fields",
    )

    assert source.count("character(kind=c_char, len=*), dimension(:), intent(inout) :: value") == 4
    assert "if (allocated(owner%words)) then" in source
    assert "if (associated(owner%aliases)) then" in source
    assert "if (allocated(native_plain_box%words)) then" in source
    assert "if (associated(native_plain_box%aliases)) then" in source
