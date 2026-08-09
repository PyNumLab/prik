"""Direct public-API coverage for declaration-expression utility stages."""

from __future__ import annotations

import pytest

from prik.utilities.declaration_expressions import (
    ArrayExpressionSource,
    DeclarationExpressionCall,
    ResolvedDeclarationExtent,
    canonicalize_declaration_extent,
    declaration_expression_call_sites,
    declaration_expression_calls,
    declaration_extent_references,
    declaration_extent_uses_power,
    evaluate_integer_expression,
    fortran_extent_to_python,
    is_declaration_expression_helper,
    is_public_declaration_expression,
    render_declaration_extent,
    resolve_declaration_extent,
    split_declaration_assignment,
    split_dimension_bounds,
    split_top_level_expression,
)


def test_source_helpers_keep_nested_syntax_intact() -> None:
    """Split only outer declaration delimiters and assignments."""
    assert split_top_level_expression("first, call('a,b'), [third, fourth]", ",") == [
        "first",
        "call('a,b')",
        "[third, fourth]",
    ]
    assert split_top_level_expression("'first''part', second", ",") == ["'first''part'", "second"]
    assert split_top_level_expression("first::Strided:upper", ":") == ["first", "", "Strided", "upper"]
    with pytest.raises(ValueError, match="one character"):
        split_top_level_expression("value", "::")

    assert split_dimension_bounds("") == (None, None)
    assert split_dimension_bounds("upper") == ("1", "upper")
    assert split_dimension_bounds("lower:upper") == ("lower", "upper")
    assert split_dimension_bounds(":upper") == (None, "upper")
    assert split_dimension_bounds("lower:") == ("lower", None)
    assert split_dimension_bounds("lower:max(first:second, upper)") == ("lower", "max(first:second, upper)")

    assert split_declaration_assignment("value = merge(first, second, mask)") == (
        "value",
        "merge(first, second, mask)",
    )
    assert split_declaration_assignment("pointer => target") == ("pointer", "target")
    assert split_declaration_assignment("value == other") == ("value == other", None)
    assert split_declaration_assignment("value = size(array, dim=1)") == ("value", "size(array, dim=1)")
    assert split_declaration_assignment("character = 'a''b'") == ("character", "'a''b'")


def test_normalization_and_inspection_preserve_expression_provenance() -> None:
    """Translate known inquiries while leaving unknown calls available to policy."""
    arrays = {"source": ArrayExpressionSource(rank=2, lower_bounds=("0", "2"))}

    assert fortran_extent_to_python("size(source)", arrays) == "source.size"
    assert fortran_extent_to_python("size(source, dim=2)", arrays) == "source.shape[1]"
    assert fortran_extent_to_python("shape(source)", arrays) == "source.shape"
    assert fortran_extent_to_python("rank(source)", arrays) == "source.ndim"
    assert fortran_extent_to_python("lbound(source, 2)", arrays) == "2 if source.shape[1] > 0 else 1"
    assert (
        fortran_extent_to_python("ubound(source, 2)", arrays) == "2 + source.shape[1] - 1 if source.shape[1] > 0 else 0"
    )
    assert fortran_extent_to_python("ubound(source, 1) - lbound(source, 1) + 1", arrays) == "source.shape[0]"
    assert fortran_extent_to_python("mod(n, 3)", arrays) == "n % 3"
    assert fortran_extent_to_python("merge(first, second, mask)", arrays) == "first if mask else second"
    assert fortran_extent_to_python("product((/ 2, 3 /))", arrays) == "2 * 3"
    assert fortran_extent_to_python("product(shape(source))", arrays) == "source.size"
    assert fortran_extent_to_python("sum((/ 2, 3 /))", arrays) == "sum([2, 3])"
    assert fortran_extent_to_python("maxval((/ 2, 3 /))", arrays) == "max([2, 3])"
    assert fortran_extent_to_python("minval((/ 2, 3 /))", arrays) == "min([2, 3])"
    assert fortran_extent_to_python("extent_for(n, kind=4)", arrays) == "extent_for(n)"
    assert fortran_extent_to_python("size(unknown, dim=1)", arrays) == "size(unknown, dim=1)"
    assert fortran_extent_to_python("size(source, dim=3)", arrays) == "source.shape[2]"
    assert fortran_extent_to_python("size()", arrays) == "size()"
    assert fortran_extent_to_python("size(source, dim=index)", arrays) == "size(source, dim=index)"
    assert fortran_extent_to_python("size(source, dim=1, DIM=2)", arrays) == "size(source, dim=1, DIM=2)"
    assert fortran_extent_to_python("shape(source, 1, 2)", arrays) == "shape(source, 1, 2)"
    assert fortran_extent_to_python("size(source + 1)", arrays) == "size(source + 1)"
    assert (
        fortran_extent_to_python("lbound(source)", arrays)
        == "(0 if source.shape[0] > 0 else 1, 2 if source.shape[1] > 0 else 1)"
    )
    assert fortran_extent_to_python("ubound(source)", arrays) == (
        "(0 + source.shape[0] - 1 if source.shape[0] > 0 else 0, 2 + source.shape[1] - 1 if source.shape[1] > 0 else 0)"
    )
    assert fortran_extent_to_python("lbound(source, 3)", arrays) == "lbound(source, 3)"
    assert fortran_extent_to_python("ubound(source, 1) - lbound(source, 2) + 1", arrays) == (
        "(0 + source.shape[0] - 1 if source.shape[0] > 0 else 0) - (2 if source.shape[1] > 0 else 1) + 1"
    )
    assert fortran_extent_to_python("len('a''b')", arrays) == "len('ab')"
    assert fortran_extent_to_python("rank(source, 1)", arrays) == "rank(source, 1)"
    assert fortran_extent_to_python("not valid (") == "not valid ("

    assert canonicalize_declaration_extent("n + 3 - n") == "3"
    assert canonicalize_declaration_extent("n + n - n") == "n"
    assert canonicalize_declaration_extent("not valid (") == "not valid ("
    assert declaration_expression_calls("extent_for(n) + helpers.other(m)") == ("extent_for", "helpers.other")
    assert declaration_expression_call_sites("extent_for(n) + helpers.other(m, 1)") == (
        DeclarationExpressionCall("extent_for", 1),
        DeclarationExpressionCall("helpers.other", 2),
    )
    assert declaration_expression_calls("not valid (") == ("<invalid>",)
    assert declaration_expression_call_sites("not valid (") == (DeclarationExpressionCall("<invalid>", 0),)
    assert declaration_extent_references("n + max(m, 1)") == ("n", "m")
    assert declaration_extent_references("values.shape[0]") == ("<invalid>",)
    assert declaration_extent_references("not valid (") == ("<invalid>",)
    assert declaration_extent_references("::Strided") == ()
    assert declaration_extent_uses_power("n ** 2")
    assert not declaration_extent_uses_power("not valid (")
    assert is_declaration_expression_helper("SUM")
    assert not is_declaration_expression_helper("helpers.sum")


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("n + values.shape[1]", True),
        ("max(1, n)", True),
        ("helpers.extent_for(n)", True),
        ("n if flag else m", True),
        ("sum([n, m])", True),
        ("values.shape[index]", False),
        ("values.unknown", False),
        ("len(values, default=0)", False),
        ("factory()(n)", False),
        ("1.5", False),
        ("not valid (", False),
    ],
)
def test_public_expression_grammar_rejects_unsupported_syntax(expression: str, expected: bool) -> None:
    """Keep public grammar validation separate from producer-role binding."""
    assert is_public_declaration_expression(expression) is expected


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("abs(-3)", 3),
        ("max(3, 7, 4)", 7),
        ("min(3, 7, 4)", 3),
        ("modulo(8, 3)", 2),
        ("product((/ 2, 3, 4 /))", 24),
        ("sum((/ 2, 3, 4 /))", 9),
        ("maxval((/ 2, 3, 4 /))", 4),
        ("minval((/ 2, 3, 4 /))", 2),
        ("merge(4, 2, .true.)", 4),
        ("int(2.9)", 2),
        ("len('abc')", 3),
        ("len_trim('a  ')", 1),
        ("iachar('A')", 65),
        ("2 ** 3", 8),
        ("3 if 1 < 2 else 4", 3),
        ("True and not False", 1),
        ("False or True", 1),
        ("1 == 1 == 1", 1),
        ("1 != 2", 1),
        ("1 >= 1", 1),
        ("1 <= 1", 1),
        ("+3", 3),
        ("1 // 1", 1),
        ("1 << 1", None),
        ("~1", None),
        ("int(2.9, kind=4)", 2),
        ("int(2, base=10)", None),
        ("abs(1, 2)", None),
        ("iachar('')", None),
        ("len(1)", None),
        ("sum((/ /))", None),
        ("1 / 0", None),
        ("max()", None),
        ("unknown(3)", None),
        ("'not an integer result'", None),
    ],
)
def test_compile_time_evaluator_only_executes_supported_integer_expressions(
    expression: str, expected: int | None
) -> None:
    """Exercise the intrinsic subset and its no-exception failure sentinel."""
    assert evaluate_integer_expression(expression) == expected


def test_role_resolution_reuses_completed_roles_and_names_blockers() -> None:
    """Bind scalars, array inquiries, and native calls without guessing missing roles."""
    scalar_roles = {"n": ("number", "number_role"), "m": ("count", "count_role")}
    array_roles = {"values": ("values", ("value_role_0", "value_role_1"))}
    callable_roles = {"extent_for": ("prik_extent_for", "extent_role")}

    assert resolve_declaration_extent("::Strided", scalar_roles, array_roles) == ResolvedDeclarationExtent("::Strided")
    assert resolve_declaration_extent("n + values.shape[1]", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "n + __prik_extent_values_1",
        ("n", "__prik_extent_values_1"),
        ("number_role", "value_role_1"),
    )
    assert resolve_declaration_extent("values.size", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "__prik_extent_values_0 * __prik_extent_values_1",
        ("__prik_extent_values_0", "__prik_extent_values_1"),
        ("value_role_0", "value_role_1"),
    )
    assert resolve_declaration_extent("values.ndim", scalar_roles, array_roles) == ResolvedDeclarationExtent("2")
    assert resolve_declaration_extent("len(values)", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "__prik_extent_values_0", ("__prik_extent_values_0",), ("value_role_0",)
    )
    assert resolve_declaration_extent("sum(values.shape)", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "__prik_extent_values_0 + __prik_extent_values_1",
        ("__prik_extent_values_0", "__prik_extent_values_1"),
        ("value_role_0", "value_role_1"),
    )
    assert resolve_declaration_extent("max(values.shape)", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "max(__prik_extent_values_0, __prik_extent_values_1)",
        ("__prik_extent_values_0", "__prik_extent_values_1"),
        ("value_role_0", "value_role_1"),
    )
    assert resolve_declaration_extent(
        "extent_for(n)", scalar_roles, array_roles, callable_roles
    ) == ResolvedDeclarationExtent(
        "prik_extent_for(n)",
        ("n",),
        ("number_role",),
        ("prik_extent_for",),
        ("extent_role",),
    )
    assert resolve_declaration_extent("other(n)", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "other(n)", ("other()",), blockers=("other()",)
    )
    assert resolve_declaration_extent("len(n)", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "len(n)", ("n",), blockers=("n",)
    )
    assert resolve_declaration_extent("values.shape[3]", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "values.shape[3]", ("<invalid>",), blockers=("<invalid>",)
    )
    assert resolve_declaration_extent("missing", scalar_roles, array_roles).blockers == ("missing",)
    assert resolve_declaration_extent("missing.size", scalar_roles, array_roles).blockers == ("missing",)
    assert resolve_declaration_extent("values.shape[index]", scalar_roles, array_roles).blockers == ("<invalid>",)
    assert resolve_declaration_extent("missing.shape[0]", scalar_roles, array_roles).blockers == ("missing",)
    assert resolve_declaration_extent("max(n, other=m)", scalar_roles, array_roles).blockers == ("max()",)
    assert resolve_declaration_extent("helper.other(n)", scalar_roles, array_roles).blockers == ("helper.other()",)
    assert resolve_declaration_extent("len()", scalar_roles, array_roles).blockers == ("<invalid>",)
    assert resolve_declaration_extent("abs(n, m)", scalar_roles, array_roles).blockers == ("abs()",)
    assert resolve_declaration_extent("sum(missing.shape)", scalar_roles, array_roles).blockers == ("missing",)
    assert resolve_declaration_extent("sum([n, m])", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "n + m", ("n", "m"), ("number_role", "count_role")
    )
    assert resolve_declaration_extent("max([n, m])", scalar_roles, array_roles) == ResolvedDeclarationExtent(
        "max(n, m)", ("n", "m"), ("number_role", "count_role")
    )


@pytest.mark.parametrize(
    ("expression", "target", "expected"),
    [
        ("n + m * 2", "c", "native_n + native_m * 2"),
        ("n ** 2", "c", "prik_extent_power((native_n), (2))"),
        ("n ** 2", "fortran", "native_n ** 2"),
        ("n % 3", "fortran", "mod((native_n), (3))"),
        ("n % 3", "c", "native_n % 3"),
        ("n * (m + limit)", "c", "native_n * (native_m + native_limit)"),
        ("n - (m - limit)", "fortran", "native_n - (native_m - native_limit)"),
        ("(n ** m) ** limit", "fortran", "(native_n ** native_m) ** native_limit"),
        ("n ** (m ** limit)", "c", "prik_extent_power((native_n), (prik_extent_power((native_m), (native_limit))))"),
        ("-(n + m)", "c", "-(native_n + native_m)"),
        ("+n", "fortran", "+native_n"),
        ("not flag", "fortran", ".not. (native_flag)"),
        ("not flag", "c", "! (native_flag)"),
        ("n and m or flag", "c", "((((native_n) && (native_m))) || (native_flag))"),
        ("n and m", "fortran", "((native_n) .and. (native_m))"),
        ("n or m", "fortran", "((native_n) .or. (native_m))"),
        ("n < m <= limit", "fortran", "(((native_n) .lt. (native_m)) .and. ((native_m) .le. (native_limit)))"),
        ("n == m", "c", "(((native_n) == (native_m)))"),
        ("n != m", "fortran", "(((native_n) .ne. (native_m)))"),
        ("n > m", "c", "(((native_n) > (native_m)))"),
        ("n >= m", "fortran", "(((native_n) .ge. (native_m)))"),
        ("n if flag else m", "c", "((native_flag) ? (native_n) : (native_m))"),
        ("n if flag else m", "fortran", "merge((native_n), (native_m), (native_flag))"),
        ("int(n)", "c", "((npy_intp)(native_n))"),
        ("int(n)", "fortran", "int(native_n)"),
        ("abs(n)", "fortran", "abs(native_n)"),
        ("abs(n)", "c", "((native_n) < 0 ? -(native_n) : (native_n))"),
        ("max(n, m, limit)", "fortran", "max(native_n, native_m, native_limit)"),
        (
            "max(n, m)",
            "c",
            "((native_n) > (native_m) ? (native_n) : (native_m))",
        ),
        ("min(n, m)", "c", "((native_n) < (native_m) ? (native_n) : (native_m))"),
        ("min(n, m)", "fortran", "min(native_n, native_m)"),
        ("extent_for(n)", "c", "native_extent_for(native_n)"),
        ("True", "c", "1"),
        ("False", "fortran", ".false."),
        ("...", "c", "..."),
    ],
)
def test_backend_renderer_preserves_completed_expression_semantics(
    expression: str,
    target: str,
    expected: str,
) -> None:
    """Render completed token expressions for each backend without re-planning policy."""
    substitutions = {
        "n": "native_n",
        "m": "native_m",
        "limit": "native_limit",
        "flag": "native_flag",
        "extent_for": "native_extent_for",
    }
    assert render_declaration_extent(expression, substitutions, target=target) == expected


def test_backend_renderer_rejects_invalid_target_and_unrenderable_syntax() -> None:
    """Expose API errors instead of inventing output for invalid completed input."""
    with pytest.raises(ValueError, match="unsupported declaration-expression target"):
        render_declaration_extent("n", {}, target="python")
    with pytest.raises(ValueError, match="invalid completed declaration expression"):
        render_declaration_extent("not valid (", {}, target="c")
    with pytest.raises(ValueError, match="unsupported completed declaration-expression node"):
        render_declaration_extent("[n]", {}, target="c")
