import pytest

from x2py.parsers.fortran.models import FortranFunctionCall, FortranSlice, FortranUseMapping, FortranVariable

from x2py import FortranParseError, parse_fortran_file, parse_fortran_project


def collect_project_procedure_signatures(files):
    return list(parse_fortran_project(files).procedures.values())


def parse_fortran_modules(code, filename=None):
    return parse_fortran_file(code, filename=filename).modules


def parse_fortran_module(code, filename=None):
    return parse_fortran_modules(code, filename=filename)[0]


def parse_fortran_submodules(code, filename=None):
    return parse_fortran_file(code, filename=filename).submodules


def parse_fortran_submodule(code, filename=None):
    return parse_fortran_submodules(code, filename=filename)[0]


def parse_fortran_programs(code, filename=None):
    return parse_fortran_file(code, filename=filename).programs


def parse_fortran_program(code, filename=None):
    return parse_fortran_programs(code, filename=filename)[0]


def parse_fortran_block_data(code, filename=None):
    return parse_fortran_file(code, filename=filename).block_data_units


def parse_fortran_block_data_unit(code, filename=None):
    return parse_fortran_block_data(code, filename=filename)[0]


def parse_fortran_interfaces(code, filename=None):
    return parse_fortran_file(code, filename=filename).interfaces


def parse_fortran_interface(code, filename=None):
    return parse_fortran_interfaces(code, filename=filename)[0]


COMPILE_TIME_EXPRESSION_SOURCE = """
module compile_time_expression_examples
  use iso_fortran_env, only: real64
  implicit none

  integer, parameter :: n = 10
  integer, parameter :: m = 5
  integer, parameter :: expr_int = 2 * n + m - 3
  integer, parameter :: abs_value = abs(-12)
  integer, parameter :: max_value = max(3, 7, 2)
  integer, parameter :: mod_value = mod(17, 5)
  integer, parameter :: len_value = len("abcdef")
  integer, parameter :: len_trim_value = len_trim("abc   ")
  integer, parameter :: char_code = iachar("A")
  integer, parameter :: cast_int = int(3.9)

  character(len=len("compile")) :: length_from_len
  character(len=n) :: length_from_parameter
  character(len=len_trim("abc   ")) :: length_from_len_trim

  real(real64) :: array_from_parameter(n)
  real(real64) :: array_from_expression(2 * n + 1)
  integer :: matrix_from_constants(m, n)
  integer, parameter :: small_array(3) = [1, 2, 3]

  type :: buffer_type(k, n)
     integer, kind :: k
     integer, len  :: n
     real(kind=k) :: values(n)
  end type buffer_type

  type(buffer_type(real64, 4)) :: compile_time_buffer
end module compile_time_expression_examples
"""


def collect_signature_shape_symbols(signature):
    import re

    symbols = set()
    for arg in signature.arguments:
        for dim in arg.shape:
            symbols.update(re.findall(r"[A-Za-z_]\w*", dim))
    return symbols


def evaluate_signature_shapes(signature, symbol_values=None):
    from dataclasses import replace
    import re

    symbol_values = symbol_values or {}
    out = replace(signature)
    out.arguments = [replace(a) for a in signature.arguments]
    for a in out.arguments:
        a.shape = list(a.shape)
        for i, dim in enumerate(a.shape):
            for k, v in symbol_values.items():
                dim = re.sub(rf"\b{re.escape(str(k))}\b", str(v), dim)
            a.shape[i] = dim
    return out


__all__ = (
    "COMPILE_TIME_EXPRESSION_SOURCE",
    "FortranFunctionCall",
    "FortranParseError",
    "FortranSlice",
    "FortranUseMapping",
    "FortranVariable",
    "collect_project_procedure_signatures",
    "collect_signature_shape_symbols",
    "evaluate_signature_shapes",
    "parse_fortran_block_data",
    "parse_fortran_block_data_unit",
    "parse_fortran_file",
    "parse_fortran_interfaces",
    "parse_fortran_module",
    "parse_fortran_modules",
    "parse_fortran_program",
    "parse_fortran_programs",
    "parse_fortran_project",
    "parse_fortran_submodule",
    "parse_fortran_submodules",
    "pytest",
)
