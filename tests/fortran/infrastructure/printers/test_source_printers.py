"""Fortran source-printer line-wrapping contracts.

Generated Fortran must stay within the free-form 132-column limit, and every
continuation must be placed where it cannot change what the statement means.
"""

from __future__ import annotations

import re

import pytest

from prik.codegen import (
    CodeExpression,
    FortranAssignment,
    FortranCall,
    FortranFunction,
    FortranIf,
    FortranModule,
    FortranPointerAssignment,
)
from prik.printers import FortranSourcePrinter

_SLICES = ", ".join(f"1:values_upper_bound_{axis} + 1:values_stride_{axis}" for axis in range(4))
_LONG_SUM = " + ".join(f"value_{index}" for index in range(20))
_PADDING = "x" * 40


def _nested_assignment(expression: str) -> FortranModule:
    return FortranModule(
        "nested_lines",
        procedures=(
            FortranFunction(
                "nested",
                body=(
                    FortranIf(
                        CodeExpression("outer"),
                        body=(
                            FortranIf(
                                CodeExpression("inner"),
                                body=(FortranAssignment("result", CodeExpression(expression)),),
                            ),
                        ),
                    ),
                ),
                is_subroutine=True,
            ),
        ),
    )


@pytest.mark.parametrize(
    ("node", "present", "absent"),
    [
        pytest.param(
            FortranCall(
                "native_scale",
                (CodeExpression(f"values_base({_SLICES})"), CodeExpression(f"out_base({_SLICES})")),
            ),
            ("& values_base(&", "&   1:values_upper_bound_3 + 1:values_stride_3), &", "& out_base(&"),
            (),
            id="parenthesized_call_arguments",
        ),
        pytest.param(
            FortranPointerAssignment("values", CodeExpression(f"values_base({_SLICES})")),
            ("values => values_base(&", "& 1:values_upper_bound_3 + 1:values_stride_3)"),
            (),
            id="pointer_array_section",
        ),
        pytest.param(
            FortranAssignment("result", CodeExpression(_LONG_SUM)),
            (" &\n  & ",),
            (),
            id="unstructured_statement",
        ),
        pytest.param(
            _nested_assignment(_LONG_SUM),
            ("       & ",),
            (),
            id="after_nested_indentation",
        ),
        # A nested call's commas belong to it, so the outer break skips them.
        pytest.param(
            FortranAssignment(
                "destination",
                CodeExpression(f"compute_total(first_{_PADDING}, max(second_term, third_term), fourth_{_PADDING})"),
            ),
            ("& max(second_term, third_term), &",),
            (),
            id="call_breaks_at_its_own_arguments",
        ),
        # Fortran resumes a continued literal after the next line's `&`, so a
        # break at a comma inside quotes would change the literal's characters.
        pytest.param(
            FortranAssignment(
                "destination",
                CodeExpression(f"build_message(prefix_{_PADDING}, 'alpha, beta', suffix_{_PADDING})"),
            ),
            ("'alpha, beta'",),
            ("'alpha, &",),
            id="never_inside_a_character_literal",
        ),
    ],
)
def test_fortran_source_printer_continues_long_statements_at_safe_points(node, present, absent):
    source = FortranSourcePrinter().doprint(node)

    for fragment in present:
        assert fragment in source
    for fragment in absent:
        assert fragment not in source
    assert max(map(len, source.splitlines())) <= 132


@pytest.mark.parametrize("quote", ("'", '"'))
def test_fortran_source_printer_continues_long_literals_without_changing_their_value(quote: str):
    encoded_value = f"{'x' * 110} literal whitespace {quote * 2}{'y' * 160}"
    statement = f"result = {quote}{encoded_value}{quote}"

    source = FortranSourcePrinter().doprint(
        FortranAssignment("result", CodeExpression(f"{quote}{encoded_value}{quote}"))
    )
    reconstructed = source.replace("result = &\n  & ", "result = ")
    reconstructed = re.sub(r"&\n\s*&", "", reconstructed)

    assert reconstructed == statement
    assert max(map(len, source.splitlines())) <= 132
    for current, following in zip(source.splitlines(), source.splitlines()[1:], strict=False):
        following_content = following.lstrip().removeprefix("&")
        assert not (current[-2:-1] == quote and following_content[:1] == quote)


def test_fortran_source_printer_rejects_an_overlong_token_without_a_safe_break():
    with pytest.raises(ValueError, match=r"free-form limit is 132"):
        FortranSourcePrinter().doprint(FortranAssignment("result", CodeExpression("x" * 134)))
