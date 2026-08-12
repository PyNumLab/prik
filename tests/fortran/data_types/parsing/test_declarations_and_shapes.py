"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

import pytest
from prik.parsers.fortran import parse_fortran_file, parse_fortran_project
from tests.fortran._support.parser_procedures import (
    COMPILE_TIME_EXPRESSION_SOURCE,
    collect_project_procedure_signatures,
    parse_fortran_modules,
)
from prik.parsers.fortran.parser import FortranParser


def test_builtin_datatypes_preserve_positional_and_keyword_kinds():
    code = """
subroutine builtin_kinds(i1, i2, r1, r2, c1, c2, l1, l2, ch1, ch2)
  integer(4), intent(in) :: i1
  integer(kind=8), intent(in) :: i2
  real(8), intent(in) :: r1
  real(kind=c_double), intent(in) :: r2
  complex(16), intent(in) :: c1
  complex(kind=c_double_complex), intent(in) :: c2
  logical(1), intent(in) :: l1
  logical(kind=c_bool), intent(in) :: l2
  character(1), intent(in) :: ch1
  character(len=1, kind=c_char), intent(in) :: ch2
end subroutine builtin_kinds
"""

    args = {arg.name: arg for arg in parse_fortran_file(code, filename="builtin_kinds.f90").procedures[0].arguments}

    assert args["i1"].base_type == "integer"
    assert args["i1"].kind == "4"
    assert args["i2"].kind == "8"
    assert args["r1"].base_type == "real"
    assert args["r1"].kind == "8"
    assert args["r2"].kind == "c_double"
    assert args["c1"].base_type == "complex"
    assert args["c1"].kind == "16"
    assert args["c2"].kind == "c_double_complex"
    assert args["l1"].base_type == "logical"
    assert args["l1"].kind == "1"
    assert args["l2"].kind == "c_bool"
    assert args["ch1"].base_type == "character"
    assert args["ch1"].kind == "1"
    assert args["ch2"].kind == "len=1, kind=c_char"


def test_builtin_star_kind_declarations_preserve_all_intrinsic_kinds():
    code = """
subroutine star_kinds(i1, i2, r1, r2, c1, c2, l1, l2, ch1, ch2)
  integer*4 i1
  integer*8 :: i2
  real*4 r1
  real*8 :: r2
  complex*8 c1
  complex*16 :: c2
  logical*1 l1
  logical*4 :: l2
  character*8 ch1
  character*(*) :: ch2
end subroutine star_kinds
"""

    args = {arg.name: arg for arg in parse_fortran_file(code, filename="star_kinds.f90").procedures[0].arguments}

    assert args["i1"].base_type == "integer"
    assert args["i1"].kind == "4"
    assert args["i1"].declared_storage_bits == 32
    assert args["i2"].kind == "8"
    assert args["i2"].declared_storage_bits == 64
    assert args["r1"].base_type == "real"
    assert args["r1"].kind == "4"
    assert args["r1"].declared_storage_bits == 32
    assert args["r2"].kind == "8"
    assert args["r2"].declared_storage_bits == 64
    assert args["c1"].base_type == "complex"
    assert args["c1"].kind == "8"
    assert args["c1"].declared_storage_bits == 64
    assert args["c2"].kind == "16"
    assert args["c2"].declared_storage_bits == 128
    assert args["l1"].base_type == "logical"
    assert args["l1"].kind == "1"
    assert args["l1"].declared_storage_bits == 8
    assert args["l2"].kind == "4"
    assert args["l2"].declared_storage_bits == 32
    assert args["ch1"].base_type == "character"
    assert args["ch1"].kind == "8"
    assert args["ch1"].character_length_syntax is True
    assert args["ch1"].declared_storage_bits is None
    assert args["ch2"].kind == "*"
    assert args["ch2"].character_length_syntax is True


def test_legacy_character_star_kind_sets_length_metadata_when_character_prefix_is_preparsed():
    parsed = FortranParser()._parse_declaration_left("character*8", parse_character_star=False)

    assert parsed is not None
    declaration, attributes = parsed
    assert declaration.base_type == "character"
    assert declaration.kind == "8"
    assert declaration.character_length_syntax is True
    assert attributes == []


def test_kind_resolution_from_imported_module_across_files():
    files = {
        "kinds.f90": """
module my_kinds
  integer, parameter :: rk = selected_real_kind(15, 307)
end module my_kinds
""",
        "solver.f90": """
module solver
contains
subroutine step(x)
  use my_kinds, only: rk
  real(kind=rk), intent(inout) :: x(:)
end subroutine step
end module solver
""",
    }
    signatures = collect_project_procedure_signatures(files)
    step = next(s for s in signatures if s.name == "step")
    assert step.arguments[0].kind == "selected_real_kind(15, 307)"


def test_module_variables_and_use_statements():
    code = """
module cfg
  use iso_c_binding, only: c_int
  integer(kind=c_int), parameter :: nmax = 32
  real(kind=8), dimension(3) :: origin
end module cfg
"""
    modules = parse_fortran_modules(code)
    assert len(modules) == 1
    mod = modules[0]
    assert mod.name == "cfg"
    assert mod.uses["iso_c_binding"] == ["c_int"]
    assert [v.name for v in mod.variables] == ["nmax", "origin"]
    assert mod.variables[0].is_parameter is True
    assert mod.variables[1].is_parameter is False
    assert mod.variables[1].shape == ["3"]


def test_fixed_form_parameter_statement_after_typed_constants():
    code = """
      subroutine cst(a)
      real a
      real zero, one
      parameter ( zero = 0.0e+0, one = 1.0e+0 )
      a = a + one - zero
      end
"""
    sigs = parse_fortran_file(code, filename="legacy.f").procedures
    assert len(sigs) == 1
    assert sigs[0].variables == {}


def test_duplicate_declaration_raises_error():
    code = """
subroutine dup(x)
  real :: x
  integer :: x
end subroutine dup
"""
    with pytest.raises(ValueError, match="Duplicate declaration"):
        _ = parse_fortran_file(code, filename="dup.f90").procedures


def test_fixed_form_parameter_without_typed_declaration_raises_error():
    code = """
      subroutine cst(a)
      implicit none
      real a
      parameter ( zero = 0.0e+0 )
      end
"""
    with pytest.raises(ValueError, match="Unknown datatype for PARAMETER symbol"):
        _ = parse_fortran_file(code, filename="legacy.f").procedures


def test_fixed_form_parameter_without_typed_declaration_allowed_with_implicit_typing():
    code = """
      subroutine cst()
      parameter ( one = 1.0e+0 )
      end
"""
    sigs = parse_fortran_file(code, filename="legacy.f").procedures
    assert len(sigs) == 1
    assert sigs[0].variables["one"].base_type == "real"
    assert sigs[0].variables["one"].value == "1"


def test_modern_parameter_without_typed_declaration_uses_implicit_typing():
    code = """
subroutine cst()
  parameter (ival = 2)
end subroutine cst
"""
    sig = parse_fortran_file(code, filename="modern.f90").procedures[0]
    assert sig.variables["ival"].base_type == "integer"
    assert sig.variables["ival"].value == "2"


def test_duplicate_initialized_declaration_raises_error():
    code = """
subroutine dup_init()
  integer :: x = 1
  integer :: x = 2
end subroutine dup_init
"""
    with pytest.raises(ValueError, match="Duplicate declaration"):
        _ = parse_fortran_file(code, filename="dup_init.f90").procedures


def test_legacy_star_kind_parameter_symbol_is_recognized():
    code = """
      subroutine zgbmv_like()
      complex*16 one
      parameter (one = (1.0d+0,0.0d+0))
      end
"""
    sig = parse_fortran_file(code, filename="legacy.f").procedures[0]
    assert sig.variables == {}


def test_legacy_star_kind_parameter_list_with_implicit_none_is_recognized():
    code = """
      subroutine zgejsv_like()
      implicit none
      complex*16 czero, cone
      parameter ( czero = (0.0d0,0.0d0), cone = (1.0d0,0.0d0) )
      end
"""
    sig = parse_fortran_file(code, filename="legacy.f").procedures[0]
    assert sig.variables == {}


def test_local_parameter_kind_used_in_argument_declaration():
    code = """
subroutine saxpy(x)
  integer, parameter :: rk = selected_real_kind(15, 307)
  real(kind=rk), intent(inout) :: x(:)
end subroutine saxpy
"""
    sig = parse_fortran_file(code).procedures[0]
    assert sig.arguments[0].kind in {"rk", "selected_real_kind(15, 307)"}


def test_parse_namespace_dependency_resolution(tmp_path):
    dep = tmp_path / "kinds.f90"
    user = tmp_path / "solver.f90"
    user.write_text(
        """
module solver
  use my_kinds, only: rk
contains
subroutine step(x)
  real(kind=rk), intent(inout) :: x(:)
end subroutine step
end module solver
""",
        encoding="utf-8",
    )
    dep.write_text(
        """
module my_kinds
  integer, parameter :: rk = selected_real_kind(15, 307)
end module my_kinds
""",
        encoding="utf-8",
    )

    ns = parse_fortran_project({str(p.name): p.read_text(encoding="utf-8") for p in tmp_path.glob("*.f90")})
    assert len(ns.files) == 2
    assert "my_kinds" in ns.modules
    assert "solver" in ns.modules
    step = next(s for s in ns.procedures.values() if s.name == "step")
    assert step.arguments[0].kind == "selected_real_kind(15, 307)"


@pytest.mark.parametrize(
    ("base_type", "type_spec", "expected"),
    [
        ("real", "", None),
        ("real", "()", None),
        ("real", "(8)", "8"),
        ("real", "(kind = selected_real_kind(15, 307))", "selected_real_kind(15, 307)"),
        ("real", "(kind=merge(8, 4, enabled=.true.))", "merge(8, 4, enabled=.true.)"),
        ("real", "(len=5)", None),
        ("character", "(len=8)", "len=8"),
        ("character", "(len=8, kind=c_char)", "len=8, kind=c_char"),
    ],
)
def test_extract_kind_from_type_spec_contract(base_type, type_spec, expected):
    from prik.parsers.fortran.type_resolver import extract_kind_from_type_spec

    assert extract_kind_from_type_spec(base_type, type_spec) == expected


def test_compiler_dependent_parameter_expressions_remain_symbolic_with_value_at_module_level():
    files = {
        "kinds.f90": """
module kinds_mod
  integer, parameter :: ip = selected_int_kind(9)
contains
  subroutine use_kind_expr(x)
    real, dimension(1:ip), intent(inout) :: x
  end subroutine use_kind_expr
end module kinds_mod
"""
    }
    sig = collect_project_procedure_signatures(files)[0]
    assert sig.arguments[0].shape == ["1:ip"]
    assert sig.arguments[0].shape == ["1:ip"]
    assert sig.arguments[0].shape == ["1:ip"]


def test_local_compiler_dependent_parameter_expressions_remain_symbolic_with_value():
    code = """
subroutine use_local_kind_expr(x)
  integer, parameter :: ip = selected_int_kind(9)
  real, dimension(1:ip), intent(inout) :: x
end subroutine use_local_kind_expr
"""
    sig = parse_fortran_file(code).procedures[0]
    assert sig.arguments[0].shape == ["1:ip"]
    assert sig.arguments[0].shape == ["1:ip"]
    assert sig.arguments[0].shape == ["1:ip"]


def test_compile_time_parameter_expression_resolves_deep_dependency_chains():
    files = {
        "dims.f90": """
module dims_mod
  integer, parameter :: n0 = 1
  integer, parameter :: n1 = n0 + 1
  integer, parameter :: n2 = n1 + 1
  integer, parameter :: n3 = n2 + 1
  integer, parameter :: n4 = n3 + 1
  integer, parameter :: n5 = n4 + 1
contains
  subroutine use_expr(x)
    integer, intent(inout) :: x(1:n5)
  end subroutine use_expr
end module dims_mod
"""
    }
    sig = collect_project_procedure_signatures(files)[0]
    assert sig.arguments[0].shape[0].startswith("1:")


def test_big_compile_time_expression_suite():
    files = {
        "exprs.f90": """
module expr_mod
  integer, parameter :: a = 8
  integer, parameter :: b = 3
  integer, parameter :: c = 2
  integer, parameter :: p_add = a + b
  integer, parameter :: p_sub = a - b
  integer, parameter :: p_mul = b * c
  integer, parameter :: p_div = a / c
  integer, parameter :: p_pow = c ** b
  integer, parameter :: p_mix = (a + b) * c - 1
contains
  subroutine all_exprs(x1, x2, x3, x4, x5, x6, x7, x8, x9)
    integer, intent(inout) :: x1(1:p_add)
    integer, intent(inout) :: x2(1:p_sub)
    integer, intent(inout) :: x3(1:p_mul)
    integer, intent(inout) :: x4(1:p_div)
    integer, intent(inout) :: x5(1:p_pow)
    integer, intent(inout) :: x6(0:p_mix)
    integer, intent(inout) :: x7(1:-(-a + b))
    integer, intent(inout) :: x8(1:(a+b)*(c+1)-1)
    integer, intent(inout) :: x9(1:(a-b)*(a-c))
  end subroutine all_exprs
end module expr_mod
"""
    }
    sig = collect_project_procedure_signatures(files)[0]
    assert [a.shape[0] for a in sig.arguments] == [
        "1:p_add",
        "1:p_sub",
        "1:p_mul",
        "1:p_div",
        "1:p_pow",
        "0:p_mix",
        "1:-(-a + b)",
        "1:(a+b)*(c+1)-1",
        "1:(a-b)*(a-c)",
    ]


def test_compile_time_expression_module_values_are_partially_evaluated():
    parsed = parse_fortran_file(COMPILE_TIME_EXPRESSION_SOURCE)
    module = parsed.modules[0]
    variables = {var.name: var for var in module.variables}

    assert variables["expr_int"].value == "22"
    assert variables["abs_value"].value == "12"
    assert variables["max_value"].value == "7"
    assert variables["mod_value"].value == "2"
    assert variables["len_value"].value == "6"
    assert variables["len_trim_value"].value == "3"
    assert variables["char_code"].value == "65"
    assert variables["cast_int"].value == "3"
    assert variables["length_from_len"].kind == "len=7"
    assert variables["length_from_parameter"].kind == "len=10"
    assert variables["length_from_len_trim"].kind == "len=3"
    assert variables["array_from_parameter"].shape == ["10"]
    assert variables["array_from_expression"].shape == ["21"]
    assert variables["matrix_from_constants"].shape == ["5", "10"]
    assert variables["small_array"].value == "[1, 2, 3]"
    assert variables["expr_int"].symbolic_value == "2 * n + m - 3"
    assert variables["small_array"].symbolic_value == "[1, 2, 3]"


def test_local_parameter_keeps_symbolic_value_after_project_resolution():
    project = parse_fortran_project(
        {
            "local_symbolic.f90": """
subroutine use_local_symbolic(x)
  integer, parameter :: m = selected_int_kind(9)
  real, intent(inout) :: x(m)
end subroutine use_local_symbolic
"""
        }
    )

    variables = project.procedures["use_local_symbolic"].variables

    assert variables["m"].value is None
    assert variables["m"].symbolic_value == "selected_int_kind(9)"


def test_unevaluated_module_parameter_keeps_symbolic_value_without_literal_value():
    parsed = parse_fortran_file(
        """
module selected_kind_mod
  integer, parameter :: rk = selected_real_kind(12)
contains
  subroutine scale(x)
    real(kind=rk), intent(inout) :: x
  end subroutine scale
end module selected_kind_mod
"""
    )
    module = parsed.modules[0]
    variables = {var.name: var for var in module.variables}

    assert variables["rk"].value is None
    assert variables["rk"].symbolic_value == "selected_real_kind(12)"
    assert module.procedures[0].arguments[0].kind == "selected_real_kind(12)"


def test_star_kind_is_parsed_in_modern_fortran_file():
    code = """
subroutine bad(x)
  real*8 :: x
end subroutine bad
"""
    proc = parse_fortran_file(code, filename="bad.f90").procedures[0]
    assert proc.arguments[0].base_type == "real"
    assert proc.arguments[0].kind == "8"
