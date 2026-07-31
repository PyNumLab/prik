"""Procedure and function header parsing behavior."""

import pytest

from x2py import FortranParseError, parse_fortran_file


def test_typed_function_result_headers_are_parsed_from_inline_fortran():
    code = """
module typed_result_mod
  type :: point
    real :: x
  end type point
contains
  type(point) function make_point()
  end function make_point

  class(point), pointer function current_point()
  end function current_point

  character(len=8) function label_name()
  end function label_name

  real(8) function weighted_value()
  end function weighted_value

  double precision function norm2()
  end function norm2

  double complex function complex_norm2()
  end function complex_norm2
end module typed_result_mod
"""

    procedures = {proc.name: proc for proc in parse_fortran_file(code).modules[0].procedures}

    assert procedures["make_point"].result.base_type == "derived"
    assert procedures["make_point"].result.kind == "point"
    assert procedures["current_point"].result.base_type == "derived"
    assert procedures["current_point"].result.kind == "point"
    assert procedures["label_name"].result.base_type == "character"
    assert procedures["label_name"].result.kind == "len=8"
    assert procedures["weighted_value"].result.base_type == "real"
    assert procedures["weighted_value"].result.kind == "8"
    assert procedures["norm2"].result.base_type == "real"
    assert procedures["norm2"].result.target_kind_expression == "kind(1.0d0)"
    assert procedures["complex_norm2"].result.base_type == "complex"
    assert procedures["complex_norm2"].result.target_kind_expression == "kind(1.0d0)"


def test_legacy_star_kind_function_headers_are_parsed_from_inline_fixed_form():
    code = """
      complex*16 function zdotc(n, zx, zy)
      integer n
      complex*16 zx(n), zy(n)
      zdotc = zx(1) * zy(1)
      end

      character*1 function trans_name(itrans)
      integer itrans
      trans_name = 'N'
      end

      character*(*) function any_name()
      any_name = 'x'
      end
"""

    procedures = {proc.name: proc for proc in parse_fortran_file(code, filename="legacy_funcs.f").procedures}

    assert procedures["zdotc"].result.base_type == "complex"
    assert procedures["zdotc"].result.kind == "16"
    assert procedures["zdotc"].result.declared_storage_bits == 128
    assert procedures["trans_name"].result.base_type == "character"
    assert procedures["trans_name"].result.kind == "1"
    assert procedures["trans_name"].result.character_length_syntax is True
    assert procedures["any_name"].result.base_type == "character"
    assert procedures["any_name"].result.kind == "*"
    assert procedures["any_name"].result.character_length_syntax is True


def test_no_argument_headers_without_parentheses_are_parsed():
    code = """
subroutine setup
end subroutine setup

integer function answer
  answer = 42
end function answer
"""

    procedures = {proc.name: proc for proc in parse_fortran_file(code).procedures}

    assert procedures["setup"].kind == "subroutine"
    assert procedures["setup"].arguments == []
    assert procedures["answer"].kind == "function"
    assert procedures["answer"].result.base_type == "integer"


def test_typed_nested_interface_function_marks_dummy_as_procedure():
    code = """
subroutine caller(cb)
  interface
    real function cb(x)
      real, intent(in) :: x
    end function cb
  end interface
end subroutine caller
"""

    sig = parse_fortran_file(code).procedures[0]

    assert sig.arguments[0].base_type == "procedure"


def test_unsupported_procedure_like_header_raises_instead_of_being_dropped():
    code = """
vector function make_value(x)
  integer, intent(in) :: x
end function make_value
"""

    with pytest.raises(FortranParseError, match="Unsupported function result type prefix 'vector'"):
        parse_fortran_file(code, filename="bad_header.f90")


def test_malformed_module_header_raises_instead_of_creating_bad_symbol():
    code = """
module :: bad_mod
end module bad_mod
"""

    with pytest.raises(FortranParseError, match="Unsupported or malformed module header"):
        parse_fortran_file(code, filename="bad_module_header.f90")


def test_malformed_public_procedure_headers_raise_from_source_lines():
    with pytest.raises(FortranParseError, match="Unsupported or malformed module procedure header"):
        parse_fortran_file(
            """
submodule (parent_mod) child_mod
contains
  module procedure reset(x)
end submodule child_mod
""",
            filename="bad_module_proc.f90",
        )

    with pytest.raises(FortranParseError, match="Unsupported or malformed procedure header"):
        parse_fortran_file(
            """
recursive, pure subroutine broken_header(x)
  integer :: x
end subroutine broken_header
""",
            filename="bad_proc_header.f90",
        )


def test_interface_finalizes_pending_procedure_at_end_interface_and_import_attrs():
    code = """
interface named_callback
  subroutine cb(x)
    import :: c_int
    integer(c_int), intent(in) :: x
end interface named_callback
"""

    iface = parse_fortran_file(code, filename="pending_interface.f90").interfaces[0]
    proc = iface.procedures[0]

    assert proc.name == "cb"
    assert "interface(named_callback)" in proc.attributes
    assert "import(c_int)" in proc.attributes
