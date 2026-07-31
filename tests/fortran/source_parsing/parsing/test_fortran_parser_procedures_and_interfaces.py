"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from tests.fortran._support.parser_procedures import (
    FortranFunctionCall,
    FortranSlice,
    FortranVariable,
    collect_project_procedure_signatures,
    parse_fortran_block_data,
    parse_fortran_file,
    parse_fortran_modules,
    parse_fortran_programs,
    parse_fortran_project,
    parse_fortran_submodules,
    pytest,
)


def test_subroutine_signature_with_intent_and_dimension():
    code = """
module linalg_mod
contains
pure subroutine axpy(n, a, x, y)
  integer, intent(in) :: n
  real(kind=8), intent(in) :: a
  real(kind=8), intent(in), dimension(:) :: x
  real(kind=8), intent(inout) :: y(:)
end subroutine axpy
end module linalg_mod
"""
    parsed = parse_fortran_file(code)
    signatures = parsed.modules[0].procedures
    assert len(signatures) == 1

    sig = signatures[0]
    assert sig.module == "linalg_mod"
    assert sig.name == "axpy"
    assert sig.kind == "subroutine"
    assert "pure" in sig.attributes

    n, a, x, y = sig.arguments
    assert n.base_type == "integer"
    assert a.base_type == "real"
    assert a.kind == "8"
    assert x.rank == 1
    assert x.shape == [":"]
    assert y.rank == 1
    assert y.shape == [":"]


def test_function_result_and_use_statement():
    code = """
function norm2(x) result(res)
  use iso_c_binding, only: c_double
  real(kind=c_double), intent(in) :: x(:)
  real(kind=c_double) :: res
end function norm2
"""
    signatures = parse_fortran_file(code).procedures
    sig = signatures[0]
    assert sig.kind == "function"
    assert sig.result is not None
    assert sig.result.name == "res"
    assert sig.result.base_type == "real"
    assert sig.uses["iso_c_binding"] == ["c_double"]
    assert sig.arguments[0].shape == [":"]


def test_fixed_form_and_interface_detection():
    code = """
      subroutine saxpy(n,x,y)
      integer, intent(in) :: n
      real, dimension(n), intent(in) :: x
      real, dimension(n), intent(inout) :: y
      end
      interface
        subroutine cb(i)
          integer, intent(in) :: i
        end subroutine cb
      end interface
"""
    parsed = parse_fortran_file(code, filename="legacy.f")
    assert len(parsed.procedures) == 1
    assert parsed.procedures[0].name == "saxpy"
    assert parsed.procedures[0].arguments[1].shape == ["n"]
    assert len(parsed.interfaces) == 1
    assert parsed.interfaces[0].procedures[0].in_interface is True

    parsed = parse_fortran_file(code, filename="legacy.f77")
    assert len(parsed.procedures) == 1
    assert parsed.procedures[0].name == "saxpy"
    assert len(parsed.interfaces) == 1

    parsed = parse_fortran_file(code, filename="legacy.f90")
    assert len(parsed.procedures) == 1
    assert parsed.procedures[0].name == "saxpy"
    assert parsed.procedures[0].arguments[1].shape == ["n"]
    assert len(parsed.interfaces) == 1
    assert parsed.interfaces[0].procedures[0].in_interface is True


def test_module_contains_procedure_and_type_children():
    code = """
module m1
  integer :: cfg
  type :: particle
    integer :: id
  end type particle
contains
  subroutine add1(n, x)
    integer, intent(in) :: n
    real, intent(inout) :: x(:)
  end subroutine add1
end module m1
"""
    modules = parse_fortran_modules(code)
    assert len(modules) == 1
    mod = modules[0]
    assert mod.name == "m1"
    assert mod.filename is None
    assert [p.name for p in mod.procedures] == ["add1"]
    assert mod.procedures[0].arguments[0].procedure == "add1"
    assert [t.name for t in mod.derived_types] == ["particle"]


def test_module_contains_interfaces():
    code = """
module m1
  interface apply
    subroutine do_apply(n)
      integer, intent(in) :: n
    end subroutine do_apply
  end interface
end module m1
"""
    mod = parse_fortran_modules(code)[0]
    assert len(mod.interfaces) == 1
    iface = mod.interfaces[0]
    assert iface.name == "apply"
    assert iface.module == "m1"
    assert [p.name for p in iface.procedures] == ["do_apply"]


def test_duplicate_function_result_declaration_raises_error():
    code = """
real function f(x)
  real :: x
  real :: f
end function f
"""
    with pytest.raises(ValueError, match="Duplicate declaration"):
        _ = parse_fortran_file(code, filename="dup_result.f90").procedures


def test_duplicate_function_result_with_result_keyword_raises_error():
    code = """
real function f(x) result(res)
  real :: x
  real :: res
end function f
"""
    with pytest.raises(ValueError, match="Duplicate declaration"):
        _ = parse_fortran_file(code, filename="dup_result_kw.f90").procedures


def test_duplicate_procedure_name_same_scope_raises_error():
    code = """
subroutine work(n)
  integer, intent(in) :: n
end subroutine work

function work(n) result(out)
  integer, intent(in) :: n
  integer :: out
end function work
"""
    with pytest.raises(ValueError, match="Duplicate procedure name"):
        _ = parse_fortran_file(code, filename="dup_proc.f90").procedures


def test_duplicate_procedure_name_same_module_scope_raises_error():
    code = """
module m
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work
  function work(n) result(out)
    integer, intent(in) :: n
    integer :: out
  end function work
end module m
"""
    with pytest.raises(ValueError, match="Duplicate procedure name"):
        _ = parse_fortran_file(code, filename="dup_mod_proc.f90").procedures


def test_implicit_none_allows_external_dummy_procedure_argument():
    code = """
subroutine fdjac1(fcn, n)
  implicit none
  integer, intent(in) :: n
  external :: fcn
end subroutine fdjac1
"""
    sig = parse_fortran_file(code, filename="fdjac1.f90").procedures[0]
    assert sig.arguments[0].name == "fcn"
    assert sig.arguments[0].base_type == "procedure"


def test_external_attribute_and_later_type_declaration_do_not_conflict():
    code = """
subroutine lapack_style(slamch)
  implicit none
  external slamch
  real slamch
end subroutine lapack_style
"""
    sig = parse_fortran_file(code, filename="lapack_style.f90").procedures[0]
    assert sig.arguments[0].name == "slamch"
    assert sig.arguments[0].base_type == "real"


def test_external_dummy_keeps_recursive_attribute_metadata():
    code = """
recursive function apply_once(f, x) result(y)
  implicit none
  real, external :: f
  real, intent(in) :: x
  real :: y
  y = f(x)
end function apply_once
"""
    sig = parse_fortran_file(code, filename="apply_once.f90").procedures[0]
    assert sig.kind == "function"
    assert "recursive" in sig.attributes
    assert sig.arguments[0].name == "f"
    assert sig.arguments[0].base_type == "real"


def test_external_dummy_keeps_interface_context_metadata():
    code = """
interface
  subroutine driver(fcn, x)
    implicit none
    external :: fcn
    real, intent(in) :: x
  end subroutine driver
end interface
"""
    parsed = parse_fortran_file(code, filename="iface_external.f90")
    sig = parsed.interfaces[0].procedures[0]
    assert sig.in_interface is True
    assert sig.arguments[0].name == "fcn"
    assert sig.arguments[1].name == "x"
    assert sig.arguments[1].base_type == "real"


def test_external_function_dummy_with_explicit_result_type_is_parsed():
    code = """
subroutine apply_cb(f, x, y)
  implicit none
  real, intent(in) :: x
  real, intent(out) :: y
  real, external :: f
  y = f(x)
end subroutine apply_cb
"""
    sig = parse_fortran_file(code, filename="apply_cb.f90").procedures[0]
    f_arg = sig.arguments[0]
    assert f_arg.name == "f"
    assert f_arg.base_type == "real"


def test_ignore_local_variables_in_signatures():
    code = """
subroutine update(n, x)
  integer, intent(in) :: n
  real, intent(inout) :: x(n)
  integer :: i
  real :: tmp
end subroutine update
"""
    sig = parse_fortran_file(code).procedures[0]
    assert [a.name for a in sig.arguments] == ["n", "x"]
    assert sig.arguments[0].base_type == "integer"
    assert sig.arguments[1].base_type == "real"


def test_ignore_internal_procedures_in_contains_block():
    code = """
subroutine outer(x)
  real, intent(inout) :: x
contains
  subroutine inner(y)
    real, intent(inout) :: y
  end subroutine inner
end subroutine outer
"""
    sigs = parse_fortran_file(code).procedures
    assert len(sigs) == 1
    assert sigs[0].name == "outer"


def test_recursive_function_and_result_keyword_variants():
    code = """
recursive function fact(n) results(res)
  integer, intent(in) :: n
  integer :: res
end function fact
"""
    sig = parse_fortran_file(code).procedures[0]
    assert "recursive" in sig.attributes
    assert sig.result is not None
    assert sig.result.name == "res"


def test_structured_shape_preserves_slices_and_function_calls():
    code = """
subroutine derived_shape(src, x, y)
  real, intent(in) :: src(:,:)
  real, intent(inout), dimension(0:size(src, 1)-1, lbound(src, 2):ubound(src, 2)) :: x
  real, intent(inout) :: y(1:n:2)
end subroutine derived_shape
"""
    sig = parse_fortran_file(code).procedures[0]
    args = {arg.name: arg for arg in sig.arguments}

    assert args["x"].shape == ["0:size(src, 1)-1", "lbound(src, 2):ubound(src, 2)"]
    shape = args["x"].structured_shape
    assert shape.raw == args["x"].shape
    assert isinstance(shape.dimensions[0], FortranSlice)
    assert shape.dimensions[0].lower == "0"
    assert shape.dimensions[0].upper == "size(src, 1)-1"
    assert isinstance(shape.dimensions[1], FortranSlice)
    assert isinstance(shape.dimensions[1].lower, FortranFunctionCall)
    assert shape.dimensions[1].lower.name == "lbound"
    assert shape.dimensions[1].lower.arguments == ["src", "2"]
    assert isinstance(shape.dimensions[1].upper, FortranFunctionCall)
    assert shape.dimensions[1].upper.name == "ubound"

    y_dim = args["y"].structured_shape.dimensions[0]
    assert isinstance(y_dim, FortranSlice)
    assert (y_dim.lower, y_dim.upper, y_dim.stride) == ("1", "n", "2")


def test_fortran_variable_spec_expressions_parse_function_calls():
    var = FortranVariable(
        name="work",
        kind="selected_real_kind(15)",
        value="size(work, 1)",
    )

    assert isinstance(var.kind_expression, FortranFunctionCall)
    assert var.kind_expression.name == "selected_real_kind"
    assert var.kind_expression.arguments == ["15"]
    assert isinstance(var.value_expression, FortranFunctionCall)
    assert var.value_expression.name == "size"
    assert var.value_expression.arguments == ["work", "1"]


def test_local_parameters_in_contained_procedures_do_not_leak_across_signatures():
    files = {
        "dims.f90": """
module dims_mod
  integer, parameter :: n = 3
contains
  subroutine a()
    integer, parameter :: n = 9
  end subroutine a

  subroutine b(x)
    real, intent(inout) :: x(1:n)
  end subroutine b
end module dims_mod
"""
    }

    sig = collect_project_procedure_signatures(files)[0]
    assert sig.name == "a"
    sig_b = collect_project_procedure_signatures(files)[1]
    assert sig_b.name in {"a", "b"}
    if sig_b.name == "b":
        assert sig_b.arguments[0].shape == ["1:n"]


def test_submodule_procedures_and_namespace_dependencies(tmp_path):
    parent = tmp_path / "parent.f90"
    child = tmp_path / "child.f90"
    parent.write_text(
        """
module parent_mod
  integer, parameter :: rk = 8
  interface
    module subroutine scale(x)
      real(kind=rk), intent(inout) :: x(:)
    end subroutine scale
  end interface
end module parent_mod
""",
        encoding="utf-8",
    )
    child.write_text(
        """
submodule (parent_mod) child_impl
contains
  module subroutine scale(x)
    real(kind=8), intent(inout) :: x(:)
  end subroutine scale
end submodule child_impl
""",
        encoding="utf-8",
    )

    namespace = parse_fortran_project({str(p.name): p.read_text(encoding="utf-8") for p in tmp_path.glob("*.f90")})
    assert len(namespace.files) == 2
    assert len(namespace.submodules) == 1
    submodule = namespace.submodules["child_impl"]
    assert submodule.name == "child_impl"
    assert submodule.parent == "parent_mod"
    assert submodule.ancestor is None
    assert [p.name for p in submodule.procedures] == ["scale"]
    assert submodule.procedures[0].module == "child_impl"


def test_submodule_module_procedure_stub_and_additional_program_units():
    code = """
submodule (ancestor_mod:parent_impl) child_impl
  use iso_c_binding, only: c_int
  integer(kind=c_int) :: counter
contains
  module procedure reset_counter
  end procedure reset_counter
end submodule child_impl

program driver
  use ancestor_mod
  integer :: ierr
end program driver

block data init_data
  integer :: seed
end block data init_data
"""
    submodules = parse_fortran_submodules(code)
    assert len(submodules) == 1
    submodule = submodules[0]
    assert submodule.parent == "parent_impl"
    assert submodule.ancestor == "ancestor_mod"
    assert submodule.uses["iso_c_binding"] == ["c_int"]
    assert [v.name for v in submodule.variables] == ["counter"]
    assert [(p.name, p.kind) for p in submodule.procedures] == [("reset_counter", "module procedure")]

    programs = parse_fortran_programs(code)
    assert len(programs) == 1
    assert programs[0].name == "driver"
    assert programs[0].uses["ancestor_mod"] == []
    assert [v.name for v in programs[0].variables] == ["ierr"]

    block_data = parse_fortran_block_data(code)
    assert len(block_data) == 1
    assert block_data[0].name == "init_data"
    assert [v.name for v in block_data[0].variables] == ["seed"]


def test_procedure_dummy_declaration_tracks_local_interface_kind():
    code = """
subroutine caller(cb)
  procedure(local_cb) :: cb
end subroutine caller
"""
    sig = parse_fortran_file(code).procedures[0]
    cb = next(a for a in sig.arguments if a.name == "cb")
    assert cb.base_type == "procedure"
    assert cb.kind == "local_cb"


def test_procedure_dummy_declaration_with_imported_interface_keeps_kind_unresolved():
    code = """
subroutine caller(cb)
  import :: ext_cb
  procedure(ext_cb) :: cb
end subroutine caller
"""
    sig = parse_fortran_file(code).procedures[0]
    cb = next(a for a in sig.arguments if a.name == "cb")
    assert cb.base_type == "procedure"
    assert cb.kind == ""
    assert "import(ext_cb)" in sig.attributes


def test_parse_fortran_modules_rejects_standalone_procedure_entrypoint():
    code = """
subroutine lonely(x)
  integer, intent(in) :: x
end subroutine lonely
"""
    assert parse_fortran_modules(code) == []


def test_module_parser_ignores_procedure_local_variables():
    code = """
module no_leak
  integer :: module_value
contains
  subroutine worker(x)
    integer, intent(in) :: x
    real :: local_value
  end subroutine worker
end module no_leak
"""
    mod = parse_fortran_modules(code)[0]
    assert [v.name for v in mod.variables] == ["module_value"]
