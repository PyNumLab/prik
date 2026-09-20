from pathlib import Path

from prik.parsers.fortran import parse_fortran_file, parse_fortran_project

PARSING_FIXTURES = Path(__file__).parents[1] / "infrastructure" / "parsing" / "fixtures" / "support"


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


COMPILE_TIME_EXPRESSION_SOURCE = (PARSING_FIXTURES / "compile_time_expression_examples.f90").read_text(encoding="utf-8")


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
