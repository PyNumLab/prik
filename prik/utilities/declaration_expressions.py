"""Shared declaration-expression parsing, normalization, resolution, and rendering.

Declaration owners provide Fortran-like bound text. Semantic conversion turns
that text into the public Python-expression dialect, post-IR policy binds every
visible value to a wrapper role, and code generators render the completed
expression for C or Fortran. Keeping those stages here prevents parsers,
policy, and generators from growing independent expression dialects.

The public entrypoints are grouped in the same order as that flow: source-text
splitting, source normalization, public-expression inspection, role binding,
compile-time evaluation, and backend rendering. This module does not decide
whether a producer is available at a wrapper boundary; callers supply those
completed role maps to :func:`resolve_declaration_extent`.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = (
    "ArrayExpressionSource",
    "DeclarationExpressionCall",
    "ResolvedDeclarationExtent",
    "canonicalize_declaration_extent",
    "declaration_expression_call_sites",
    "declaration_expression_calls",
    "declaration_extent_references",
    "declaration_extent_uses_power",
    "evaluate_integer_expression",
    "fortran_extent_to_python",
    "is_declaration_expression_helper",
    "is_public_declaration_expression",
    "render_declaration_extent",
    "resolve_declaration_extent",
    "split_declaration_assignment",
    "split_dimension_bounds",
    "split_top_level_expression",
)


_RUNTIME_DIMENSIONS = frozenset({":", "::Strided", "...", "Flat"})
_FORTRAN_RELATIONAL_OPERATORS = {
    ".eq.": "==",
    ".ne.": "!=",
    ".lt.": "<",
    ".le.": "<=",
    ".gt.": ">",
    ".ge.": ">=",
}
_FORTRAN_LOGICAL_OPERATORS = {
    ".and.": " and ",
    ".or.": " or ",
    ".not.": " not ",
    ".eqv.": " == ",
    ".neqv.": " != ",
}
_SUPPORTED_CALLS = frozenset({"abs", "int", "max", "min"})
_PUBLIC_CALLS = frozenset({*_SUPPORTED_CALLS, "len", "sum"})
_PUBLIC_ARRAY_ATTRIBUTES = frozenset({"size", "shape", "ndim"})
_PUBLIC_EXPRESSION_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Call,
    ast.Attribute,
    ast.Subscript,
    ast.List,
    ast.Tuple,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.MatMult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.LShift,
    ast.RShift,
    ast.BitOr,
    ast.BitXor,
    ast.BitAnd,
    ast.USub,
    ast.UAdd,
    ast.Invert,
    ast.Not,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)
_RESOLVED_EXTENT_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Call,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


# ============================================================================
# Public records
# ============================================================================


@dataclass(frozen=True)
class ArrayExpressionSource:
    """Describe one declared array referenced by another extent expression.

    Use this record in the ``arrays`` mapping passed to
    :func:`fortran_extent_to_python` when an expression queries an array with
    ``size``, ``shape``, ``rank``, ``lbound``, or ``ubound``. ``rank`` and
    source lower bounds preserve Fortran's declared index origin; omitted
    lower bounds use the language default of one.
    """

    rank: int
    lower_bounds: tuple[str | None, ...] = ()


@dataclass(frozen=True)
class DeclarationExpressionCall:
    """Describe one syntactically static declaration-expression call.

    :func:`declaration_expression_call_sites` returns these records before
    semantic conversion resolves a call to a native procedure or public helper.
    ``argument_count`` and ``has_keywords`` describe syntax only; they do not
    validate the native interface.
    """

    name: str
    argument_count: int
    has_keywords: bool = False


@dataclass(frozen=True)
class ResolvedDeclarationExtent:
    """Hold one public extent after its dependencies have been role-bound.

    ``expression`` contains backend-neutral reference tokens. ``references``
    and ``roles`` are parallel tuples consumed by wrapper plans; callable
    tuples do the same for native specification functions. ``blockers`` names
    syntax or values that policy could not supply, so callers can reject the
    declaration without guessing a producer.
    """

    expression: str
    references: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    callable_references: tuple[str, ...] = ()
    callable_roles: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


# ============================================================================
# Source declaration text
# ============================================================================


def split_top_level_expression(text: str, delimiter: str) -> list[str]:
    """Split ``text`` at one delimiter outside brackets and quoted literals.

    The returned pieces preserve nested calls, constructors, and substrings.
    Unbalanced syntax is deliberately preserved for the parser's normal
    diagnostic path instead of being repaired here.

    Raises:
        ValueError: If ``delimiter`` is not exactly one character.
    """
    if len(delimiter) != 1:
        raise ValueError("declaration-expression delimiters must be one character")

    parts: list[str] = []
    start = 0
    stack: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in "([{":
            stack.append(char)
        elif char in ")]}" and stack:
            stack.pop()
        elif char == delimiter and not stack:
            parts.append(text[start:index].strip())
            start = index + 1
        index += 1
    parts.append(text[start:].strip())
    return parts


def split_dimension_bounds(token: str) -> tuple[str | None, str | None]:
    """Return one dimension's outer lower and upper bound expressions.

    A dimension without an outer colon has Fortran's implicit lower bound one.
    Colons nested in calls, constructors, or subscripts remain part of the
    corresponding bound.
    """
    part = token.strip()
    if not part:
        return None, None
    bounds = split_top_level_expression(part, ":")
    if len(bounds) == 1:
        return "1", part
    lower = bounds[0].strip() or None
    upper = ":".join(bounds[1:]).strip() or None
    return lower, upper


def split_declaration_assignment(text: str) -> tuple[str, str | None]:
    """Split one entity declaration from its top-level initializer.

    Equals signs in nested inquiry keywords, comparisons, and constructors do
    not start an initializer. Both ordinary ``=`` and pointer ``=>`` forms are
    recognized; the returned initializer omits the assignment operator.
    """
    stack: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in "([{":
            stack.append(char)
        elif char in ")]}" and stack:
            stack.pop()
        elif char == "=" and not stack:
            previous = text[index - 1] if index else ""
            following = text[index + 1] if index + 1 < len(text) else ""
            if previous not in {"<", ">", "=", "/"} and following != "=":
                initializer_start = index + 1
                if following == ">":
                    initializer_start += 1
                return text[:index].strip(), text[initializer_start:].strip()
        index += 1
    return text.strip(), None


# ============================================================================
# Source-to-public normalization
# ============================================================================


def fortran_extent_to_python(
    expression: str,
    arrays: Mapping[str, ArrayExpressionSource] | None = None,
) -> str:
    """Translate a scalar Fortran extent to the semantic Python expression dialect.

    The conversion covers Fortran operators and wrapper-relevant array inquiry
    intrinsics. Unknown but Python-shaped calls are retained so policy can emit
    a precise unavailable-expression blocker. If the source cannot be parsed
    safely, the original spelling is returned unchanged as provenance.

    ``arrays`` maps the visible Fortran array name to its declared rank and
    lower bounds. Supply it when translating inquiry calls; omit it for scalar
    expressions with no declared-array context.
    """
    # Stage 1: make the source expression parseable without evaluating it.
    normalized = _python_parseable_fortran_expression(expression)
    tree = _parse_expression(normalized)
    if tree is None:
        return expression.strip()

    # Stage 2: translate only inquiries whose declared array facts are known.
    translator = _FortranExtentTranslator(arrays or {})
    translated = translator.visit(tree)
    ast.fix_missing_locations(translated)
    return ast.unparse(translated)


def canonicalize_declaration_extent(expression: str) -> str:
    """Cancel additive bound terms in one Python-form declaration extent.

    This consumes translated Python syntax and returns a concise equivalent.
    Syntax outside that grammar is preserved unchanged for the later policy
    diagnostic path.
    """
    parsed = _parse_expression(expression)
    if parsed is None:
        return expression
    return ast.unparse(_simplify_additive_expression(parsed.body))


# ============================================================================
# Public-expression inspection and role binding
# ============================================================================


def resolve_declaration_extent(
    expression: str,
    scalar_roles: Mapping[str, tuple[str, str]],
    array_roles: Mapping[str, tuple[str, tuple[str, ...]]],
    callable_roles: Mapping[str, tuple[str, str]] | None = None,
) -> ResolvedDeclarationExtent:
    """Bind one Python-form extent to visible scalar and array-extent roles.

    Runtime dimension markers require no roles. Invalid syntax, unsupported
    calls, nonliteral shape indices, and unavailable names are returned as
    blockers; the function never guesses a producer.

    ``scalar_roles`` maps a visible scalar spelling to its canonical source
    name and completed role. ``array_roles`` maps an array spelling to its
    canonical source name and one role per axis. ``callable_roles`` does the
    same for a specification-function token. The returned record is normally
    stored on completed policy and consumed by backend rendering.
    """
    # Stage 1: preserve caller-owned runtime dimension markers.
    if expression in _RUNTIME_DIMENSIONS:
        return ResolvedDeclarationExtent(expression)

    # Stage 2: parse the public expression before binding any producer roles.
    tree = _parse_expression(expression)
    if tree is None:
        return ResolvedDeclarationExtent(expression, ("<invalid>",), blockers=("<invalid>",))

    # Stage 3: replace visible array properties and calls with completed tokens.
    resolver = _ExtentRoleResolver(scalar_roles, array_roles, callable_roles or {})
    resolved = resolver.visit(tree)
    ast.fix_missing_locations(resolved)

    # Stage 4: reject incomplete output rather than inventing a backend value.
    if resolver.blockers or not _valid_resolved_extent(resolved, callable_names=frozenset(resolver.callables)):
        blockers = tuple(dict.fromkeys(resolver.blockers or ("<invalid>",)))
        return ResolvedDeclarationExtent(expression, blockers, blockers=blockers)

    # Stage 5: retain ordered source names alongside their role substitutions.
    return ResolvedDeclarationExtent(
        ast.unparse(resolved) if resolver.changed else expression,
        tuple(resolver.references),
        tuple(resolver.references.values()),
        tuple(resolver.callables),
        tuple(resolver.callables.values()),
    )


def declaration_extent_references(expression: str) -> tuple[str, ...]:
    """Return scalar names used by a role-free declaration extent.

    This compatibility helper is used before a callable's producer roles are
    known. Array properties and unsupported syntax return ``<invalid>`` so the
    later policy stage cannot accidentally treat them as scalar values.
    """
    if expression in _RUNTIME_DIMENSIONS:
        return ()
    tree = _parse_expression(expression)
    if tree is None:
        return ("<invalid>",)
    if not _valid_resolved_extent(tree):
        return ("<invalid>",)
    function_names = {
        node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    return tuple(
        dict.fromkeys(
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id not in function_names
        )
    )


def declaration_expression_calls(expression: str) -> tuple[str, ...]:
    """Return named call targets used by one Python-form declaration expression.

    The result preserves first-use order and includes both bare names and
    qualified targets such as ``sizes.extent_for``. Malformed or dynamically
    computed call targets are reported as ``<invalid>``. The helper only
    inspects syntax; semantic conversion decides whether a name is a built-in
    helper, a local native procedure, or an imported native procedure.
    """
    tree = _parse_expression(expression)
    if tree is None:
        return ("<invalid>",)
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _qualified_call_name(node.func)
        calls.append(name or "<invalid>")
    return tuple(dict.fromkeys(calls))


def declaration_expression_call_sites(expression: str) -> tuple[DeclarationExpressionCall, ...]:
    """Return ordered static call sites with arity and keyword presence.

    Use this syntax-only helper before native procedure identity is known. An
    invalid expression yields one ``<invalid>`` record; a dynamic callable name
    yields ``<invalid>`` at that call site while retaining its argument shape.
    """
    tree = _parse_expression(expression)
    if tree is None:
        return (DeclarationExpressionCall("<invalid>", 0),)
    return tuple(
        DeclarationExpressionCall(
            _qualified_call_name(node.func) or "<invalid>",
            len(node.args),
            bool(node.keywords),
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    )


def is_declaration_expression_helper(name: str) -> bool:
    """Return whether a bare call name belongs to the public helper dialect.

    Semantic name resolution should check native declarations and imports
    first, because a source language may explicitly shadow an intrinsic name.
    Qualified names are never treated as built-in helpers.
    """
    return "." not in name and name.casefold() in _PUBLIC_CALLS


def declaration_extent_uses_power(expression: str) -> bool:
    """Return whether parseable public text contains an integer power operation.

    Callers use this as a code-generation preparation hint. Invalid text simply
    returns ``False`` here; normal policy validation still owns its diagnostic.
    """
    tree = _parse_expression(expression)
    if tree is None:
        return False
    return any(isinstance(node, ast.Pow) for node in ast.walk(tree))


def is_public_declaration_expression(expression: str) -> bool:
    """Return whether text uses the documented Python declaration grammar.

    This syntactic check admits unresolved scalar names but restricts array
    attributes to ``size``, ``ndim``, and ``shape[index]`` forms. Policy later
    verifies that every name and array actually has a visible producer role.
    """
    tree = _parse_expression(expression)
    if tree is None:
        return False
    call_targets = _declaration_expression_call_target_attributes(tree)
    return all(_is_public_declaration_expression_node(node, call_targets) for node in ast.walk(tree))


def _declaration_expression_call_target_attributes(tree: ast.AST) -> set[int]:
    """Return attribute identities used as callable targets within one tree.

    Attribute calls are not array-property references. Identity tracking keeps
    the public grammar check from applying array-property rules to attributes
    inside a callable expression.
    """
    return {
        id(attribute)
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        for attribute in ast.walk(call.func)
        if isinstance(attribute, ast.Attribute)
    }


def _is_public_declaration_expression_node(node: ast.AST, call_targets: set[int]) -> bool:
    """Return whether one parsed node is valid in the public expression grammar.

    The call-target set identifies attributes belonging to a callable name rather
    than an array inquiry. This helper validates syntax only; producer roles and
    callable provenance remain policy-stage responsibilities.
    """
    if not isinstance(node, _PUBLIC_EXPRESSION_NODES) or not _is_integer_constant(node):
        return False
    if isinstance(node, ast.Call):
        return _qualified_call_name(node.func) is not None and not node.keywords
    if isinstance(node, ast.Attribute):
        return id(node) in call_targets or _is_public_array_attribute(node)
    if isinstance(node, ast.Subscript):
        return _is_public_shape_index(node)
    return True


def _is_public_array_attribute(node: ast.Attribute) -> bool:
    """Return whether an attribute is one documented bare array property."""
    return isinstance(node.value, ast.Name) and node.attr in _PUBLIC_ARRAY_ATTRIBUTES


def _is_public_shape_index(node: ast.Subscript) -> bool:
    """Return whether a subscript is one literal array.shape[index] inquiry."""
    return (
        isinstance(node.value, ast.Attribute)
        and node.value.attr == "shape"
        and isinstance(node.value.value, ast.Name)
        and isinstance(node.slice, ast.Constant)
        and _is_integer_constant(node.slice)
    )


# ============================================================================
# Compile-time evaluation
# ============================================================================


def evaluate_integer_expression(expression: str) -> int | None:
    """Evaluate a self-contained Fortran/Python integer declaration expression.

    Only literals, constructors, arithmetic, comparisons, Boolean operators,
    and the small pure intrinsic set implemented by ``_IntegerEvaluator`` are
    executed. Names, arbitrary calls, invalid operations, and nonintegral final
    values return ``None`` without side effects.

    Use it only for self-contained declarations such as parameter values. Its
    integer result can then replace source metadata; a ``None`` result means
    the source spelling must remain unresolved for a later stage.
    """
    normalized = _python_parseable_fortran_expression(expression)
    tree = _parse_expression(normalized)
    if tree is None:
        return None
    value = _IntegerEvaluator().evaluate(tree)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value if isinstance(value, int) else None


# ============================================================================
# Shared syntax helpers
# ============================================================================


def _parse_expression(expression: str) -> ast.Expression | None:
    """Parse one expression without exposing ``SyntaxError`` to policy callers.

    The helper consumes already-normalized or public expression text and
    returns an ``eval``-mode tree. It returns ``None`` only for syntax that the
    public caller must preserve, block, or reframe with its own diagnostic; it
    never modifies the supplied text.
    """
    try:
        return ast.parse(expression, mode="eval")
    except SyntaxError:
        return None


def _python_parseable_fortran_expression(expression: str) -> str:
    """Convert lexical Fortran syntax to equivalent parseable Python text.

    This consumes raw declaration text and performs no semantic inquiry
    translation. Unknown names and calls are intentionally retained for later
    provenance or policy diagnostics.
    """
    text = expression.strip()
    text = _replace_fortran_array_constructors(text)
    text = re.sub(r"(?i)(?<=\d)_[A-Za-z]\w*\b", "", text)
    text = re.sub(r"(?i)(?<=\d)_[0-9]+\b", "", text)
    text = re.sub(r"(?i)\b(\d+(?:\.\d*)?)[dD]([+-]?\d+)\b", r"\1e\2", text)
    text = re.sub(r"(?i)\.true\.", "True", text)
    text = re.sub(r"(?i)\.false\.", "False", text)
    for source, replacement in _FORTRAN_RELATIONAL_OPERATORS.items():
        text = re.sub(re.escape(source), replacement, text, flags=re.IGNORECASE)
    for source, replacement in _FORTRAN_LOGICAL_OPERATORS.items():
        text = re.sub(re.escape(source), replacement, text, flags=re.IGNORECASE)
    text = text.replace("/=", "!=")
    return text.replace("%", ".")


def _qualified_call_name(node: ast.AST) -> str | None:
    """Return a dotted static call target, or ``None`` for computed callables."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_call_name(node.value)
        return f"{parent}.{node.attr}" if parent is not None else None
    return None


def _replace_fortran_array_constructors(expression: str) -> str:
    """Replace legacy ``(/ ... /)`` constructors outside quoted literals."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(expression):
        char = expression[index]
        if quote is not None:
            output.append(char)
            if char == quote:
                if index + 1 < len(expression) and expression[index + 1] == quote:
                    output.append(expression[index + 1])
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            output.append(char)
            index += 1
        elif expression.startswith("(/", index):
            output.append("[")
            index += 2
        elif expression.startswith("/)", index):
            output.append("]")
            index += 2
        else:
            output.append(expression[index])
            index += 1
    return "".join(output)


def _simplify_additive_expression(expression: ast.expr) -> ast.expr:
    """Return an equivalent AST with repeated signed terms combined.

    The helper consumes one parsed Python-form expression and builds a new
    additive tree without mutating the original nodes. It preserves first-use
    order for symbolic terms, which keeps emitted declaration text stable.
    """
    terms: list[tuple[int, ast.expr]] = []

    def collect(node: ast.expr, sign: int = 1) -> None:
        """Flatten signed additive terms into source order."""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            collect(node.left, sign)
            collect(node.right, sign)
            return
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
            collect(node.left, sign)
            collect(node.right, -sign)
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            collect(node.operand, -sign)
            return
        terms.append((sign, node))

    collect(expression)
    constant = sum(
        sign * node.value
        for sign, node in terms
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)
    )
    symbolic = [
        (sign, node)
        for sign, node in terms
        if not (isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool))
    ]

    coefficients: dict[str, tuple[ast.expr, int]] = {}
    order: list[str] = []
    for sign, node in symbolic:
        key = ast.dump(node, include_attributes=False)
        if key not in coefficients:
            coefficients[key] = (node, 0)
            order.append(key)
        original, coefficient = coefficients[key]
        coefficients[key] = (original, coefficient + sign)

    result: ast.expr | None = None
    for key in order:
        node, coefficient = coefficients[key]
        for _ in range(abs(coefficient)):
            if result is None:
                result = node if coefficient > 0 else ast.UnaryOp(op=ast.USub(), operand=node)
            else:
                operator: ast.operator = ast.Add() if coefficient > 0 else ast.Sub()
                result = ast.BinOp(left=result, op=operator, right=node)

    if result is None:
        return ast.Constant(value=constant)
    if constant > 0:
        return ast.BinOp(left=result, op=ast.Add(), right=ast.Constant(value=constant))
    if constant < 0:
        return ast.BinOp(left=result, op=ast.Sub(), right=ast.Constant(value=-constant))
    return result


# ============================================================================
# Fortran inquiry translation
# ============================================================================


class _FortranExtentTranslator(ast.NodeTransformer):
    """Translate known Fortran inquiries using declared array facts.

    Instances own a case-insensitive snapshot of the caller's array mapping.
    They convert only syntactically valid inquiries for known arrays; unknown
    calls and malformed inquiry forms remain in the AST for later policy
    diagnostics instead of being guessed or evaluated.
    """

    def __init__(self, arrays: Mapping[str, ArrayExpressionSource]) -> None:
        """Index source arrays case-insensitively without mutating caller state."""
        self.arrays = {name.casefold(): source for name, source in arrays.items()}

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Recognize the canonical upper-minus-lower extent before recursion."""
        extent = self._bound_difference_extent(node)
        return self.generic_visit(node) if extent is None else ast.copy_location(extent, node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Translate one call, preserving unsupported forms for later stages.

        Array inquiries use stored declaration facts first. The remaining
        branches normalize safe intrinsic spellings and reductions, then leave
        arbitrary specification-function calls intact for semantic resolution.
        """
        name = node.func.id.casefold() if isinstance(node.func, ast.Name) else ""

        array_inquiry = self._translated_array_inquiry(name, node)
        if array_inquiry is not None:
            return ast.copy_location(array_inquiry, node)
        intrinsic = self._translated_intrinsic_call(name, node)
        if intrinsic is not None:
            return ast.copy_location(intrinsic, node)
        reduction = self._translated_reduction_call(name, node)
        if reduction is not None:
            return ast.copy_location(reduction, node)
        return self._normalize_untranslated_call(node)

    def _translated_array_inquiry(self, name: str, node: ast.Call) -> ast.AST | None:
        """Return a translated inquiry when the call uses a known array source.

        Unknown calls and malformed inquiry forms return None so the unchanged
        node retains semantic provenance for later diagnostics.
        """
        if name not in {"size", "shape", "rank", "lbound", "ubound"}:
            return None
        return self._array_inquiry(name, node)

    def _translated_intrinsic_call(self, name: str, node: ast.Call) -> ast.AST | None:
        """Return a direct Python equivalent for supported scalar intrinsics.

        The helper consumes only fully positional modulo and merge calls. Other
        spellings return None so generic traversal preserves their call identity.
        """
        if node.keywords:
            return None
        if name in {"mod", "modulo"} and len(node.args) == 2:
            return ast.BinOp(self.visit(node.args[0]), ast.Mod(), self.visit(node.args[1]))
        if name == "merge" and len(node.args) == 3:
            return ast.IfExp(self.visit(node.args[2]), self.visit(node.args[0]), self.visit(node.args[1]))
        return None

    def _translated_reduction_call(self, name: str, node: ast.Call) -> ast.AST | None:
        """Return a normalized reduction call for one supported unary reduction.

        Product receives additional shape and literal-constructor folding. Other
        reductions retain their argument after recursive inquiry translation.
        """
        if name not in {"product", "sum", "maxval", "minval"} or len(node.args) != 1:
            return None
        argument = self.visit(node.args[0])
        if name == "product":
            if isinstance(argument, ast.Attribute) and argument.attr == "shape":
                return ast.Attribute(argument.value, "size", ast.Load())
            if isinstance(argument, ast.List | ast.Tuple) and argument.elts:
                return self._fold_binary(list(argument.elts), ast.Mult())
        public_name = {"product": "product", "sum": "sum", "maxval": "max", "minval": "min"}[name]
        return ast.Call(ast.Name(public_name, ast.Load()), [argument], [])

    def _normalize_untranslated_call(self, node: ast.Call) -> ast.AST:
        """Normalize spelling and kind keywords while retaining an unresolved call.

        Arbitrary static call names must survive translation so semantic
        conversion can establish their native provenance instead of guessing.
        """
        if isinstance(node.func, ast.Name):
            node.func.id = node.func.id.casefold()
        node.keywords = [
            keyword for keyword in node.keywords if keyword.arg is None or keyword.arg.casefold() != "kind"
        ]
        return self.generic_visit(node)

    def _array_inquiry(self, name: str, node: ast.Call) -> ast.AST | None:
        """Return one public Python property expression for a valid inquiry.

        ``node`` must name a known array as its first positional argument. The
        result is ``None`` for unknown arrays, invalid DIM syntax, and
        out-of-range dimensions so the original call can remain diagnostic
        provenance rather than becoming a guessed expression.
        """
        source_node = node.args[0] if node.args else None
        if not isinstance(source_node, ast.Name):
            return None
        source_name = source_node.id
        source = self.arrays.get(source_name.casefold())
        if source is None:
            return None
        dimension = self._inquiry_dimension(name, node)
        if dimension is False:
            return None
        if name == "size":
            return self._array_size(source_name, dimension)
        if name == "shape":
            return ast.Attribute(ast.Name(source_name, ast.Load()), "shape", ast.Load())
        if name == "rank":
            return ast.Attribute(ast.Name(source_name, ast.Load()), "ndim", ast.Load())
        bounds = tuple(
            self._axis_bound(source_name, source, axis, upper=name == "ubound") for axis in range(source.rank)
        )
        if dimension is None:
            return ast.Tuple(bounds, ast.Load())
        if not 1 <= dimension <= source.rank:
            return None
        return bounds[dimension - 1]

    def _bound_difference_extent(self, node: ast.BinOp) -> ast.AST | None:
        """Translate ``ubound(a,d) - lbound(a,d) + 1`` directly to an extent."""
        if not (
            isinstance(node.op, ast.Add)
            and isinstance(node.right, ast.Constant)
            and _is_integer_constant(node.right)
            and int(node.right.value) == 1
            and isinstance(node.left, ast.BinOp)
            and isinstance(node.left.op, ast.Sub)
        ):
            return None
        upper = self._bound_inquiry_signature(node.left.left, "ubound")
        lower = self._bound_inquiry_signature(node.left.right, "lbound")
        if upper is None or upper != lower:
            return None
        source_name, dimension = upper
        return self._array_size(source_name, dimension)

    def _bound_inquiry_signature(self, node: ast.AST, name: str) -> tuple[str, int] | None:
        """Return one recognized scalar bound inquiry's source name and dimension."""
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id.casefold() == name
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id.casefold() in self.arrays
        ):
            return None
        dimension = self._inquiry_dimension(name, node)
        if not isinstance(dimension, int) or isinstance(dimension, bool):
            return None
        source_name = node.args[0].id
        source = self.arrays[source_name.casefold()]
        if not 1 <= dimension <= source.rank:
            return None
        return source_name, dimension

    @staticmethod
    def _inquiry_dimension(name: str, node: ast.Call) -> int | None | bool:
        """Return a one-based literal DIM, ``None``, or ``False`` for invalid syntax."""
        if not node.args:
            return False
        if name == "rank":
            return None if len(node.args) == 1 and not node.keywords else False
        dimension_node = None
        if name in {"size", "lbound", "ubound"}:
            if len(node.args) > 3:
                return False
            dimension_node = node.args[1] if len(node.args) >= 2 else None
        elif name == "shape":
            if len(node.args) > 2:
                return False
        seen_keywords: set[str] = set()
        for keyword in node.keywords:
            if keyword.arg is None:
                return False
            keyword_name = keyword.arg.casefold()
            if keyword_name in seen_keywords or keyword_name not in {"dim", "kind"}:
                return False
            seen_keywords.add(keyword_name)
            if keyword_name == "dim":
                if name not in {"size", "lbound", "ubound"} or dimension_node is not None:
                    return False
                dimension_node = keyword.value
        if dimension_node is None:
            return None
        if isinstance(dimension_node, ast.Constant) and _is_integer_constant(dimension_node):
            return int(dimension_node.value)
        return False

    @staticmethod
    def _array_size(source_name: str, dimension: int | None) -> ast.AST:
        """Return total size or one zero-based Python shape selection."""
        array = ast.Name(source_name, ast.Load())
        if dimension is None:
            return ast.Attribute(array, "size", ast.Load())
        return ast.Subscript(ast.Attribute(array, "shape", ast.Load()), ast.Constant(dimension - 1), ast.Load())

    def _axis_bound(
        self,
        source_name: str,
        source: ArrayExpressionSource,
        axis: int,
        *,
        upper: bool,
    ) -> ast.AST:
        """Build one lower or upper bound while preserving zero-extent rules.

        Missing source lower bounds become one. For a zero-sized runtime axis,
        Fortran inquiry semantics require lower bound one and upper bound zero;
        the returned conditional AST enforces those results without evaluating
        the runtime source array here.
        """
        lower_text = source.lower_bounds[axis] if axis < len(source.lower_bounds) else None
        lower_expression = fortran_extent_to_python(lower_text or "1", self.arrays)
        try:
            lower = ast.parse(lower_expression, mode="eval").body
        except SyntaxError:
            lower = ast.Name("__prik_invalid_lower_bound", ast.Load())
        extent = ast.Subscript(
            ast.Attribute(ast.Name(source_name, ast.Load()), "shape", ast.Load()),
            ast.Constant(axis),
            ast.Load(),
        )
        positive_extent = ast.Compare(extent, [ast.Gt()], [ast.Constant(0)])
        if not upper:
            return ast.IfExp(positive_extent, lower, ast.Constant(1))
        declared_upper = ast.BinOp(ast.BinOp(lower, ast.Add(), extent), ast.Sub(), ast.Constant(1))
        return ast.IfExp(positive_extent, declared_upper, ast.Constant(0))

    @staticmethod
    def _fold_binary(items: list[ast.AST], operator: ast.operator) -> ast.AST:
        """Fold nonempty constructor items left-to-right with ``operator``.

        Callers provide a nonempty sequence. The method creates a fresh binary
        tree and preserves source order, which is significant for stable text.
        """
        result = items[0]
        for item in items[1:]:
            result = ast.BinOp(result, operator, item)
        return result


# ============================================================================
# Compile-time AST evaluation
# ============================================================================


class _IntegerEvaluator:
    """Evaluate the side-effect-free compile-time subset of declaration syntax.

    This internal dispatcher never invokes arbitrary callables or resolves
    names. Every unsupported node, value, intrinsic signature, or arithmetic
    error becomes ``None`` so :func:`evaluate_integer_expression` can preserve
    its no-exception, no-side-effect contract.
    """

    def evaluate(self, node: ast.AST):
        """Return one supported AST value or ``None`` without mutating ``node``."""
        method = getattr(self, f"_evaluate_{type(node).__name__}", None)
        return None if method is None else method(node)

    def _evaluate_Expression(self, node: ast.Expression):
        """Evaluate an ``eval``-mode wrapper by delegating to its body node."""
        return self.evaluate(node.body)

    @staticmethod
    def _evaluate_Constant(node: ast.Constant):
        """Return a supported scalar literal without coercing its source value."""
        return node.value if isinstance(node.value, int | float | str | bool) else None

    def _evaluate_List(self, node: ast.List):
        """Evaluate a constructor list, failing if any element is unsupported."""
        return self._evaluate_sequence(node.elts)

    def _evaluate_Tuple(self, node: ast.Tuple):
        """Evaluate a constructor tuple using the same list representation."""
        return self._evaluate_sequence(node.elts)

    def _evaluate_sequence(self, nodes: list[ast.expr]):
        """Evaluate constructor items in order or return ``None`` after a failed item."""
        values = [self.evaluate(item) for item in nodes]
        return None if any(value is None for value in values) else values

    def _evaluate_BinOp(self, node: ast.BinOp):
        """Evaluate one supported numeric binary operation."""
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        if not isinstance(left, int | float) or not isinstance(right, int | float):
            return None
        operations = {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: left - right,
            ast.Mult: lambda: left * right,
            ast.Div: lambda: left / right,
            ast.FloorDiv: lambda: left // right,
            ast.Mod: lambda: left % right,
            ast.Pow: lambda: left**right,
        }
        operation = operations.get(type(node.op))
        if operation is None:
            return None
        try:
            return operation()
        except (OverflowError, ValueError, ZeroDivisionError):
            return None

    def _evaluate_UnaryOp(self, node: ast.UnaryOp):
        """Evaluate numeric signs and logical negation."""
        value = self.evaluate(node.operand)
        if isinstance(node.op, ast.Not):
            return None if value is None else not bool(value)
        if not isinstance(value, int | float):
            return None
        return -value if isinstance(node.op, ast.USub) else +value if isinstance(node.op, ast.UAdd) else None

    def _evaluate_Call(self, node: ast.Call):
        """Evaluate one supported side-effect-free Fortran intrinsic."""
        if not isinstance(node.func, ast.Name) or any(
            keyword.arg is None or keyword.arg.casefold() != "kind" for keyword in node.keywords
        ):
            return None
        arguments = [self.evaluate(argument) for argument in node.args]
        if any(argument is None for argument in arguments):
            return None
        try:
            return self._intrinsic_value(node.func.id.casefold(), arguments)
        except (OverflowError, ValueError, ZeroDivisionError):
            return None

    @staticmethod
    def _intrinsic_value(name: str, arguments: list[object]):
        """Return a supported intrinsic result or ``None`` for an invalid signature.

        ``arguments`` already contains recursively evaluated values. This method
        performs only local deterministic arithmetic and lets its caller turn
        arithmetic errors into the evaluator's ``None`` sentinel.
        """
        if name in {"abs", "max", "min", "mod", "modulo"}:
            return _IntegerEvaluator._numeric_intrinsic_value(name, arguments)
        if name in {"product", "sum", "maxval", "minval"} and len(arguments) == 1:
            return _IntegerEvaluator._reduction_value(name, arguments[0])
        if name == "merge" and len(arguments) == 3:
            return arguments[0] if bool(arguments[2]) else arguments[1]
        if name == "int" and arguments and isinstance(arguments[0], int | float):
            return int(arguments[0])
        if name in {"len", "len_trim", "iachar"}:
            return _IntegerEvaluator._string_intrinsic_value(name, arguments)
        return None

    @staticmethod
    def _numeric_intrinsic_value(name: str, arguments: list[object]):
        """Evaluate one numeric scalar intrinsic or return None for invalid inputs.

        Arguments remain generic because callers recursively evaluate expression
        nodes first. The supported names and arities match _intrinsic_value.
        """
        if not all(isinstance(argument, int | float) for argument in arguments):
            return None
        if name == "abs":
            return abs(arguments[0]) if len(arguments) == 1 else None
        if name in {"max", "min"}:
            if not arguments:
                return None
            return max(arguments) if name == "max" else min(arguments)
        if name in {"mod", "modulo"} and len(arguments) == 2:
            return arguments[0] % arguments[1]
        return None

    @staticmethod
    def _string_intrinsic_value(name: str, arguments: list[object]):
        """Evaluate one string inquiry intrinsic or return None for invalid inputs."""
        if len(arguments) != 1 or not isinstance(arguments[0], str):
            return None
        value = arguments[0]
        if name == "len":
            return len(value)
        if name == "len_trim":
            return len(value.rstrip())
        return ord(value[0]) if value else None

    @staticmethod
    def _reduction_value(name: str, values: object):
        """Reduce a nonempty numeric constructor or return ``None`` when invalid."""
        if not isinstance(values, list) or not values or not all(isinstance(value, int | float) for value in values):
            return None
        if name == "product":
            result = 1
            for value in values:
                result *= value
            return result
        if name == "sum":
            return sum(values)
        return max(values) if name == "maxval" else min(values)

    def _evaluate_BoolOp(self, node: ast.BoolOp):
        """Evaluate a Boolean conjunction or disjunction."""
        values = [self.evaluate(value) for value in node.values]
        if any(value is None for value in values):
            return None
        return all(map(bool, values)) if isinstance(node.op, ast.And) else any(map(bool, values))

    def _evaluate_IfExp(self, node: ast.IfExp):
        """Evaluate one conditional expression after its condition is known."""
        condition = self.evaluate(node.test)
        if condition is None:
            return None
        return self.evaluate(node.body if bool(condition) else node.orelse)

    def _evaluate_Compare(self, node: ast.Compare):
        """Evaluate a supported comparison chain left-to-right, or return ``None``."""
        values = [self.evaluate(node.left), *(self.evaluate(item) for item in node.comparators)]
        if any(value is None for value in values):
            return None
        operations = {
            ast.Gt: lambda left, right: left > right,
            ast.GtE: lambda left, right: left >= right,
            ast.Lt: lambda left, right: left < right,
            ast.LtE: lambda left, right: left <= right,
            ast.Eq: lambda left, right: left == right,
            ast.NotEq: lambda left, right: left != right,
        }
        for left, operator, right in zip(values[:-1], node.ops, values[1:], strict=True):
            operation = operations.get(type(operator))
            if operation is None or not operation(left, right):
                return False if operation is not None else None
        return True


# ============================================================================
# Public expression to completed roles
# ============================================================================


class _ExtentRoleResolver(ast.NodeTransformer):
    """Bind public-expression references to completed wrapper roles.

    The resolver snapshots case-insensitive scalar, array, and callable role
    maps. Visitor methods mutate only this instance's result collections and
    the visited AST; callers read ``references``, ``callables``, ``blockers``,
    and ``changed`` after one complete traversal.
    """

    def __init__(
        self,
        scalar_roles: Mapping[str, tuple[str, str]],
        array_roles: Mapping[str, tuple[str, tuple[str, ...]]],
        callable_roles: Mapping[str, tuple[str, str]],
    ) -> None:
        """Snapshot role maps and initialize ordered per-expression results.

        Input mappings are not mutated. Dict insertion order records first use
        for ``references`` and ``callables``; ``blockers`` preserves every
        diagnostic occurrence until the public wrapper deduplicates it.
        """
        self.scalar_roles = {name.casefold(): value for name, value in scalar_roles.items()}
        self.array_roles = {name.casefold(): value for name, value in array_roles.items()}
        self.callable_roles = {name.casefold(): value for name, value in callable_roles.items()}
        self.references: dict[str, str] = {}
        self.callables: dict[str, str] = {}
        self.blockers: list[str] = []
        self.changed = False

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Bind one scalar name or record that no visible integer role supplies it."""
        source = self.scalar_roles.get(node.id.casefold())
        if source is None:
            self.blockers.append(node.id)
            return node
        self.references.setdefault(node.id, source[1])
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        """Resolve ``array.size`` and ``array.ndim`` public properties."""
        if not isinstance(node.value, ast.Name):
            self.blockers.append("<invalid>")
            return node
        source = self.array_roles.get(node.value.id.casefold())
        if source is None:
            self.blockers.append(node.value.id)
            return node
        source_name, roles = source
        if node.attr == "size":
            return self._extent_product(source_name, roles)
        if node.attr == "ndim":
            self.changed = True
            return ast.copy_location(ast.Constant(len(roles)), node)
        self.blockers.append("<invalid>")
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Resolve one literal ``array.shape[index]`` reference."""
        value = node.value
        if not (
            isinstance(value, ast.Attribute)
            and value.attr == "shape"
            and isinstance(value.value, ast.Name)
            and isinstance(node.slice, ast.Constant)
            and _is_integer_constant(node.slice)
        ):
            self.blockers.append("<invalid>")
            return node
        source = self.array_roles.get(value.value.id.casefold())
        if source is None:
            self.blockers.append(value.value.id)
            return node
        index = int(node.slice.value)
        if index < 0:
            index += len(source[1])
        if not 0 <= index < len(source[1]):
            self.blockers.append("<invalid>")
            return node
        return self._extent_token(source[0], source[1], index, node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Resolve supported helpers or record an unsupported call by name.

        The resolver consumes a public Python-form call and either returns its
        role-bound expression or leaves it unchanged while adding a blocker.
        Naming an arbitrary specification function in that blocker is
        important: policy must not confuse it with malformed expression syntax.
        """
        # Stage 1: reject dynamic syntax before looking up any producer.
        call_name = _qualified_call_name(node.func)
        if call_name is None or node.keywords:
            self.blockers.append("<invalid>" if call_name is None else f"{call_name}()")
            return node
        resolved_callable = self._resolved_native_callable(call_name, node)
        if resolved_callable is not None:
            return resolved_callable
        if not isinstance(node.func, ast.Name):
            self.blockers.append(f"{call_name}()")
            return node
        name = node.func.id.casefold()
        if name == "len":
            return self._resolved_length_call(node)
        if name in {"sum", "max", "min"} and len(node.args) == 1:
            expanded = self._expanded_sequence_call(name, node.args[0], node)
            if expanded is not None:
                return expanded
        return self._resolved_scalar_helper_call(name, node)

    def _resolved_native_callable(self, call_name: str, node: ast.Call) -> ast.AST | None:
        """Return a tokenized call for one declaration callable, when registered.

        The callable-role mapping is the completed provenance input. A matching
        call records the referenced callable and recursively resolves arguments;
        no match returns None so built-in helper handling can continue.
        """
        callable_source = self.callable_roles.get(call_name.casefold())
        if callable_source is None:
            return None
        token, role = callable_source
        self.callables.setdefault(token, role)
        self.changed = True
        return ast.copy_location(
            ast.Call(
                func=ast.Name(id=token, ctx=ast.Load()),
                args=[self.visit(argument) for argument in node.args],
                keywords=[],
            ),
            node,
        )

    def _resolved_length_call(self, node: ast.Call) -> ast.AST:
        """Resolve one len call to its first declared extent or record a blocker."""
        if len(node.args) != 1 or not isinstance(node.args[0], ast.Name):
            self.blockers.append("<invalid>")
            return node
        source = self.array_roles.get(node.args[0].id.casefold())
        if source is None or not source[1]:
            self.blockers.append(node.args[0].id)
            return node
        return self._extent_token(source[0], source[1], 0, node)

    def _resolved_scalar_helper_call(self, name: str, node: ast.Call) -> ast.AST:
        """Validate a scalar helper, resolve its arguments, or record its blocker.

        This helper receives only bare names after array-specific reductions have
        been considered. It preserves existing invalid-call wording and performs
        no semantic interpretation beyond the public helper grammar.
        """
        if name not in _SUPPORTED_CALLS or (name in {"abs", "int"} and len(node.args) != 1):
            self.blockers.append(f"{node.func.id}()")
            return node
        if name in {"min", "max"} and len(node.args) < 2:
            self.blockers.append("<invalid>")
            return node
        node.func.id = name
        node.args = [self.visit(argument) for argument in node.args]
        return node

    def _expanded_sequence_call(self, name: str, argument: ast.AST, node: ast.Call) -> ast.AST | None:
        """Expand a fixed shape or constructor reduction to scalar helper syntax.

        The method returns ``None`` only when ``argument`` is not an expandable
        shape or constructor. For a recognized but unavailable or empty source,
        it records a blocker and returns the original call node unchanged.
        """
        items: list[ast.AST]
        if isinstance(argument, ast.Attribute) and argument.attr == "shape" and isinstance(argument.value, ast.Name):
            source = self.array_roles.get(argument.value.id.casefold())
            if source is None:
                self.blockers.append(argument.value.id)
                return node
            items = [self._extent_token(source[0], source[1], axis, node) for axis in range(len(source[1]))]
        elif isinstance(argument, ast.Tuple | ast.List):
            items = [self.visit(item) for item in argument.elts]
        else:
            return None
        self.changed = True
        if not items:
            self.blockers.append("<invalid>")
            return node
        if name == "sum":
            return self._fold_binary(items, ast.Add())
        return ast.Call(ast.Name(name, ast.Load()), items, [])

    def _extent_product(self, source_name: str, roles: tuple[str, ...]) -> ast.AST:
        """Return a product of role-backed axes, or a blocked placeholder for none."""
        if not roles:
            self.blockers.append("<invalid>")
            return ast.Constant(0)
        return self._fold_binary(
            [self._extent_token(source_name, roles, axis, ast.Name(source_name)) for axis in range(len(roles))],
            ast.Mult(),
        )

    def _extent_token(self, source_name: str, roles: tuple[str, ...], axis: int, node: ast.AST) -> ast.AST:
        """Record and return one stable backend-neutral extent token.

        ``axis`` is already bounds-checked by the caller. The token's first-use
        role is retained in ``references`` and the returned node copies the
        input location for stable unparsing and diagnostics.
        """
        token = f"__prik_extent_{source_name}_{axis}"
        self.references.setdefault(token, roles[axis])
        self.changed = True
        return ast.copy_location(ast.Name(token, ast.Load()), node)

    @staticmethod
    def _fold_binary(items: list[ast.AST], operator: ast.operator) -> ast.AST:
        """Fold nonempty items left-to-right with ``operator`` into a fresh AST."""
        result = items[0]
        for item in items[1:]:
            result = ast.BinOp(result, operator, item)
        return result


# ============================================================================
# Completed-expression validation and backend rendering
# ============================================================================


def _valid_resolved_extent(tree: ast.AST, *, callable_names: frozenset[str] = frozenset()) -> bool:
    """Return whether a role-bound AST belongs to the backend grammar.

    ``callable_names`` contains only tokens selected by completed policy. The
    check accepts no attributes, subscripts, keywords, or dynamic calls, so a
    backend can render the result without inferring declaration semantics.
    """
    for node in ast.walk(tree):
        if not isinstance(node, _RESOLVED_EXTENT_NODES) or not _is_integer_constant(node):
            return False
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name)
            or node.func.id not in _SUPPORTED_CALLS | callable_names
            or node.keywords
        ):
            return False
    return True


def _is_integer_constant(node: ast.AST) -> bool:
    """Accept integer and Boolean constants while rejecting other literal values."""
    return not isinstance(node, ast.Constant) or isinstance(node.value, bool | int)


class _ExtentRenderer:
    """Render one validated, role-bound expression for a backend dialect.

    The renderer consumes only output accepted by :func:`_valid_resolved_extent`.
    ``substitutions`` replaces completed policy tokens with backend-local names;
    unknown names remain scalar locals so callers retain their original output.
    """

    def __init__(self, substitutions: Mapping[str, str], target: str) -> None:
        """Store substitution lookups and a target already validated by the public API."""
        self.substitutions = substitutions
        self.target = target

    def render(self, node: ast.AST) -> str:
        """Render ``node`` recursively or raise ``ValueError`` for a policy-stage escape."""
        method = getattr(self, f"_render_{type(node).__name__}", None)
        if method is None:
            raise ValueError(f"unsupported completed declaration-expression node: {type(node).__name__}")
        return method(node)

    def _render_Name(self, node: ast.Name) -> str:
        """Substitute one completed role token or retain a scalar local name."""
        return self.substitutions.get(node.id, node.id)

    def _render_Constant(self, node: ast.Constant) -> str:
        """Render integer and Boolean constants in the target dialect."""
        if isinstance(node.value, bool):
            if self.target == "fortran":
                return ".true." if node.value else ".false."
            return "1" if node.value else "0"
        return str(node.value)

    def _render_BinOp(self, node: ast.BinOp) -> str:
        """Render arithmetic, modulo, and integer-power operations."""
        left = self._render_binary_operand(node.left, node.op, right=False)
        right = self._render_binary_operand(node.right, node.op, right=True)
        if isinstance(node.op, ast.Pow):
            if self.target == "c":
                return f"prik_extent_power(({left}), ({right}))"
            return f"{left} ** {right}"
        if isinstance(node.op, ast.Mod) and self.target == "fortran":
            return f"mod(({left}), ({right}))"
        operators = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "/",
            ast.Mod: "%",
        }
        return f"{left} {operators[type(node.op)]} {right}"

    def _render_binary_operand(
        self,
        node: ast.AST,
        parent_operator: ast.operator,
        *,
        right: bool,
    ) -> str:
        """Render an operand and group it only when shared precedence requires it."""
        text = self.render(node)
        if not isinstance(node, ast.BinOp):
            return text
        child_precedence = self._binary_precedence(node.op)
        parent_precedence = self._binary_precedence(parent_operator)
        same_precedence = child_precedence == parent_precedence
        if isinstance(parent_operator, ast.Pow):
            needs_grouping = child_precedence < parent_precedence or (not right and same_precedence)
        else:
            needs_grouping = child_precedence < parent_precedence or (right and same_precedence)
        return f"({text})" if needs_grouping else text

    @staticmethod
    def _binary_precedence(operator: ast.operator) -> int:
        """Return the shared C/Fortran arithmetic precedence tier for ``operator``."""
        if isinstance(operator, ast.Pow):
            return 3
        if isinstance(operator, ast.Mult | ast.Div | ast.FloorDiv | ast.Mod):
            return 2
        return 1

    def _render_UnaryOp(self, node: ast.UnaryOp) -> str:
        """Render signed and logical unary operations."""
        operand = self.render(node.operand)
        if isinstance(node.op, ast.Not):
            operator = ".not." if self.target == "fortran" else "!"
            return f"{operator} ({operand})"
        operator = "-" if isinstance(node.op, ast.USub) else "+"
        grouped = (
            f"({operand})" if isinstance(node.operand, ast.BinOp | ast.BoolOp | ast.Compare | ast.IfExp) else operand
        )
        return f"{operator}{grouped}"

    def _render_BoolOp(self, node: ast.BoolOp) -> str:
        """Render conjunctions and disjunctions with explicit grouping."""
        if self.target == "fortran":
            operator = ".and." if isinstance(node.op, ast.And) else ".or."
        else:
            operator = "&&" if isinstance(node.op, ast.And) else "||"
        return "(" + f" {operator} ".join(f"({self.render(value)})" for value in node.values) + ")"

    def _render_Compare(self, node: ast.Compare) -> str:
        """Render one Python comparison chain as pairwise conjunctions."""
        operands = [node.left, *node.comparators]
        operators = {
            ast.Eq: "==" if self.target == "c" else ".eq.",
            ast.NotEq: "!=" if self.target == "c" else ".ne.",
            ast.Lt: "<" if self.target == "c" else ".lt.",
            ast.LtE: "<=" if self.target == "c" else ".le.",
            ast.Gt: ">" if self.target == "c" else ".gt.",
            ast.GtE: ">=" if self.target == "c" else ".ge.",
        }
        comparisons = [
            f"(({self.render(left)}) {operators[type(operator)]} ({self.render(right)}))"
            for left, operator, right in zip(operands[:-1], node.ops, operands[1:], strict=True)
        ]
        joiner = " .and. " if self.target == "fortran" else " && "
        return "(" + joiner.join(comparisons) + ")"

    def _render_IfExp(self, node: ast.IfExp) -> str:
        """Render Python conditional syntax as C ternary or Fortran ``merge``."""
        condition = self.render(node.test)
        body = self.render(node.body)
        otherwise = self.render(node.orelse)
        if self.target == "fortran":
            return f"merge(({body}), ({otherwise}), ({condition}))"
        return f"(({condition}) ? ({body}) : ({otherwise}))"

    def _render_Call(self, node: ast.Call) -> str:
        """Render one policy-approved pure integer helper call."""
        name = node.func.id
        arguments = [self.render(argument) for argument in node.args]
        if name not in _SUPPORTED_CALLS:
            target = self.substitutions.get(name, name)
            return f"{target}({', '.join(arguments)})"
        if name == "int":
            if self.target == "c":
                return f"((npy_intp)({arguments[0]}))"
            return f"int({arguments[0]})"
        if name == "abs":
            value = arguments[0]
            if self.target == "fortran":
                return f"abs({value})"
            return f"(({value}) < 0 ? -({value}) : ({value}))"
        if self.target == "fortran":
            return f"{name}({', '.join(arguments)})"
        comparison = ">" if name == "max" else "<"
        result = arguments[0]
        for argument in arguments[1:]:
            result = f"(({result}) {comparison} ({argument}) ? ({result}) : ({argument}))"
        return result


# ============================================================================
# Public backend-rendering entrypoint
# ============================================================================


def render_declaration_extent(
    expression: str,
    substitutions: Mapping[str, str],
    *,
    target: str,
) -> str:
    """Render a completed role-token expression for ``c`` or ``fortran``.

    Use this after :func:`resolve_declaration_extent` and completed policy have
    supplied backend-local substitutions. Runtime dimension markers are returned
    unchanged for the caller's assumed-shape or rank-specific handling.

    Args:
        expression: A public expression containing only validated role tokens.
        substitutions: Maps completed policy tokens to backend-local values.
        target: Either ``"c"`` or ``"fortran"``.

    Returns:
        The expression rendered in the requested backend dialect.

    Raises:
        ValueError: If ``target`` is unsupported or ``expression`` is not in
            the completed renderable grammar.
    """
    if target not in {"c", "fortran"}:
        raise ValueError(f"unsupported declaration-expression target: {target!r}")
    if expression in _RUNTIME_DIMENSIONS:
        return expression
    try:
        node = ast.parse(expression, mode="eval").body
    except SyntaxError as exc:
        raise ValueError(f"invalid completed declaration expression: {expression!r}") from exc
    return _ExtentRenderer(substitutions, target).render(node)


if __name__ == "__main__":
    # A declared lower bound of zero makes the source-to-public translation
    # visibly different from the original Fortran inquiry spelling.
    fortran_expression = "ubound(source, 1) - lbound(source, 1) + 1"
    source_arrays = {"source": ArrayExpressionSource(rank=2, lower_bounds=("0", "1"))}
    public_expression = canonicalize_declaration_extent(fortran_extent_to_python(fortran_expression, source_arrays))
    resolved = resolve_declaration_extent(
        public_expression,
        scalar_roles={},
        array_roles={"source": ("source", ("source_extent_0", "source_extent_1"))},
    )
    rendered = render_declaration_extent(
        resolved.expression,
        {"__prik_extent_source_0": "native_source_extent_0"},
        target="fortran",
    )

    print(f"Fortran extent: {fortran_expression}")
    print(f"Public expression: {public_expression}")
    print(f"Role-bound expression: {resolved.expression}")
    print(f"Fortran rendering: {rendered}")
    print(f"Compile-time product: {evaluate_integer_expression('product((/ 2, 3 /))')}")
