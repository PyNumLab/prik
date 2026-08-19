"""Render lowered Fortran backend nodes into compilable source text.

This module is the final text-rendering boundary for generated wrapper source.
It consumes only backend syntax nodes; semantic policy and wrapper planning are
completed by earlier stages.
"""

from __future__ import annotations

import re

import textwrap

from prik.codegen.nodes import (
    FortranAllocate,
    FortranAssignment,
    FortranCall,
    FortranDeallocate,
    FortranDeclaration,
    FortranFunction,
    FortranIf,
    FortranInterface,
    FortranInterfaceProcedure,
    FortranModule,
    FortranNullify,
    FortranParameter,
    FortranPointerAssignment,
    FortranSelectCase,
    FortranTypeDefinition,
    FortranUse,
)
from prik.utilities.stage_values import StageRecord
from prik.codegen.visitor import ClassVisitor


class FortranSourcePrinter(ClassVisitor):
    """Render lowered Fortran backend nodes into free-form source text.

    Use this printer after bridge lowering has produced Fortran syntax nodes.
    It freezes stage records before rendering, wraps generated free-form lines
    at safe boundaries, and rejects source that exceeds the compiler-safe line
    limit after wrapping.
    """

    _LINE_LIMIT = 112
    _MAX_LINE_LENGTH = 132

    def doprint(self, node: object) -> str:
        """Render one Fortran backend node into validated free-form source.

        This is the public entrypoint for modules, procedures, and individual
        statements. StageRecord inputs are frozen before dispatch. A ValueError
        is raised only when an overlong generated line has no safe continuation.
        """
        if isinstance(node, StageRecord):
            node.freeze()
        rendered = self.visit(node)
        formatted = self._format_line_lengths(rendered)
        self._validate_line_lengths(formatted)
        return formatted

    def _format_line_lengths(self, source: str) -> str:
        """Wrap every overlong rendered line and return the recombined source."""
        lines = []
        for line in source.splitlines():
            lines.extend(self._wrap_rendered_line(line))
        return "\n".join(lines)

    def _wrap_rendered_line(self, line: str) -> tuple[str, ...]:
        """Split one overlong line at safe syntax or literal boundaries.

        The input is one already-rendered Fortran line. The returned tuple
        preserves indentation and literal value; an unsplittable token remains
        intact so final validation can report the original compiler limit.
        """
        if len(line) <= self._MAX_LINE_LENGTH:
            return (line,)
        indentation = line[: len(line) - len(line.lstrip())]
        continuation_prefix = f"{indentation}  & "
        prefix = indentation
        remaining = line[len(indentation) :]
        continued_quote = None
        wrapped = []
        # Each continuation consumes the remaining source from left to right.
        while len(prefix) + len(remaining) > self._MAX_LINE_LENGTH:
            budget = self._MAX_LINE_LENGTH - len(prefix) - len(" &")
            split = self._safe_fortran_break(remaining, budget, initial_quote=continued_quote)
            if split is None:
                return (*wrapped, f"{prefix}{remaining}")
            position, continued_quote = split
            if continued_quote is None:
                piece = remaining[:position].rstrip()
                remaining = remaining[position:].lstrip()
            else:
                piece = remaining[:position]
                remaining = remaining[position:]
            if not piece or not remaining:
                return (*wrapped, f"{prefix}{piece}{remaining}")
            trailing = "&" if continued_quote is not None else " &"
            wrapped.append(f"{prefix}{piece}{trailing}")
            prefix = f"{indentation}&" if continued_quote is not None else continuation_prefix
        wrapped.append(f"{prefix}{remaining}")
        return tuple(wrapped)

    @staticmethod
    def _safe_fortran_break(
        text: str,
        budget: int,
        *,
        initial_quote: str | None = None,
    ) -> tuple[int, str | None] | None:
        """Choose the rightmost safe break at or below the available width.

        The helper consumes text after existing indentation and returns a source
        offset plus an active quote when a literal continuation is required.
        It never splits comments or doubled quote escapes.
        """
        literal_quotes = FortranSourcePrinter._fortran_literal_quotes(text, initial_quote=initial_quote)
        literal_positions = set(literal_quotes)
        window = text[: budget + 1]
        if FortranSourcePrinter._has_fortran_comment(text, literal_positions):
            return None
        candidates = FortranSourcePrinter._fortran_break_candidates(window, literal_positions)
        position = max((candidate for candidate in candidates if 0 < candidate <= budget), default=None)
        if position is not None:
            return position, None
        return FortranSourcePrinter._fortran_literal_break(text, budget, literal_quotes)

    @staticmethod
    def _fortran_literal_quotes(text: str, *, initial_quote: str | None = None) -> dict[int, str]:
        """Map literal-character offsets in text to their active quote marker.

        An optional initial quote continues a literal begun on a prior line.
        Doubled quotes remain protected so callers cannot split an escape pair.
        """
        positions = {}
        quote = initial_quote
        index = 0
        while index < len(text):
            character = text[index]
            if quote is None:
                if character in {"'", '"'}:
                    quote = character
                    positions[index] = quote
                index += 1
                continue
            positions[index] = quote
            if character == quote and index + 1 < len(text) and text[index + 1] == quote:
                positions[index + 1] = quote
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
        return positions

    @staticmethod
    def _fortran_literal_break(
        text: str,
        budget: int,
        literal_quotes: dict[int, str],
    ) -> tuple[int, str] | None:
        """Choose a literal-internal break that preserves the character value.

        The literal map comes from _fortran_literal_quotes. The returned offset
        and quote identify a valid continuation, or None when no split fits.
        """
        candidates = []
        for position in range(1, min(len(text), budget + 1)):
            quote = literal_quotes.get(position)
            if quote is None or literal_quotes.get(position - 1) != quote:
                continue
            if text[position - 1 : position + 1] == quote * 2:
                continue
            candidates.append(position)
        if not candidates:
            return None
        position = max(candidates)
        return position, literal_quotes[position]

    @staticmethod
    def _has_fortran_comment(text: str, literal_positions: set[int]) -> bool:
        """Report whether text has a comment marker outside protected literals."""
        return any(character == "!" and index not in literal_positions for index, character in enumerate(text))

    @staticmethod
    def _fortran_break_candidates(text: str, literal_positions: set[int]) -> tuple[int, ...]:
        """Collect comma and whitespace boundaries outside Fortran literals."""
        candidates = []
        for index, character in enumerate(text):
            if index in literal_positions:
                continue
            if character == ",":
                candidates.append(index + 1)
            elif character.isspace():
                candidates.append(index)
        return tuple(candidates)

    def _validate_line_lengths(self, source: str) -> None:
        """Reject source whose rendered free-form lines still exceed the limit.

        Source has already passed through the wrapper. The raised ValueError
        includes the original line number and text for an actionable diagnostic.
        """
        for line_number, line in enumerate(source.splitlines(), start=1):
            if len(line) > self._MAX_LINE_LENGTH:
                raise ValueError(
                    f"Generated Fortran line {line_number} has {len(line)} columns; "
                    f"the free-form limit is {self._MAX_LINE_LENGTH}: {line}"
                )

    # Fortran backend-node visitors

    def _visit_FortranModule(self, node: FortranModule) -> str:
        """Render one Fortran module in specification-part and body order.

        The node supplies uses, types, interfaces, declarations, and procedures.
        Abstract interfaces are emitted before declarations, concrete interfaces
        after them, and standalone procedures after the enclosing module.
        """
        lines = [f"module {node.name}"]
        lines.extend(self._indented(self.visit(use)) for use in node.uses)
        lines.append("  implicit none")
        lines.extend(self._indented(self.visit(definition)) for definition in node.type_definitions)
        lines.extend(self._indented(self.visit(interface)) for interface in node.interfaces if interface.abstract)
        lines.extend(self._indented(self.visit(declaration)) for declaration in node.declarations)
        lines.extend(self._indented(self.visit(interface)) for interface in node.interfaces if not interface.abstract)
        lines.append("contains")
        for procedure in node.procedures:
            # One blank line before each procedure keeps a long generated module
            # scannable; without it every procedure abuts the previous `end`.
            lines.append("")
            lines.append(self._indented(self.visit(procedure)))
        lines.append(f"end module {node.name}")
        for procedure in node.standalone_procedures:
            lines.append("")
            lines.append(self.visit(procedure))
        return "\n".join(lines)

    @staticmethod
    def _doc_comment_lines(doc: tuple[str, ...]) -> list[str]:
        """Render one procedure's explanatory prose as wrapped Fortran line comments.

        Free-form Fortran caps a line at 132 columns, and a generated procedure
        is indented inside its module, so prose is wrapped well short of that
        rather than emitted as one long line.
        """
        lines: list[str] = []
        for entry in doc:
            if not entry:
                lines.append("!")
                continue
            lines.extend(f"! {chunk}" for chunk in textwrap.wrap(entry, width=96) or [""])
        return lines

    def _visit_FortranUse(self, node: FortranUse) -> str:
        """Render one Fortran use statement and wrap a long ONLY list."""
        if node.only:
            rendered = f"use {node.module}, only: {', '.join(node.only)}"
            if len(rendered) <= 100:
                return rendered
            lines = [f"use {node.module}, only: &"]
            for index, name in enumerate(node.only):
                continuation = ", &" if index < len(node.only) - 1 else ""
                lines.append(f"  {name}{continuation}")
            return "\n".join(lines)
        return f"use {node.module}"

    def _visit_FortranFunction(self, node: FortranFunction) -> str:
        """Render one Fortran function or subroutine from its backend node.

        The returned text contains its signature, specification part, body, and
        optional internal procedures in Fortran's required source order.
        """
        signature = self._function_signature(node)
        lines = [*self._doc_comment_lines(node.doc), signature, *self._fortran_function_specification(node)]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        if node.internal_procedures:
            lines.append("contains")
            lines.extend(self._indented(self.visit(procedure)) for procedure in node.internal_procedures)
        lines.append(f"end {'subroutine' if node.is_subroutine else 'function'} {node.name}")
        return "\n".join(lines)

    def _fortran_function_specification(self, node: FortranFunction) -> list[str]:
        """Render the ordered specification part for one procedure node.

        Uses, implicit-none, parameter/result declarations, local declarations,
        and interfaces are returned as complete lines before the executable body.
        """
        lines = []
        lines.extend(self._indented(self.visit(use)) for use in node.uses)
        if node.implicit_none:
            lines.append("  implicit none")
        lines.extend(self._indented(self.visit(parameter)) for parameter in node.parameters)
        if node.result_name is not None and node.result_type is not None:
            lines.append(self._indented(f"{node.result_type} :: {node.result_name}"))
        lines.extend(self._indented(self.visit(declaration)) for declaration in node.declarations)
        lines.extend(self._indented(self.visit(interface)) for interface in node.interfaces)
        return lines

    def _visit_FortranParameter(self, node: FortranParameter) -> str:
        """Render one procedure parameter and preserve assumed-size syntax.

        Assumed-size dimensions must follow the parameter name rather than remain
        an attribute; all other attributes keep their original order.
        """
        assumed_size = next(
            (attribute for attribute in node.attributes if attribute.startswith("dimension(") and "*" in attribute),
            None,
        )
        if assumed_size is not None:
            dimensions = assumed_size.removeprefix("dimension(").removesuffix(")")
            attributes = tuple(attribute for attribute in node.attributes if attribute != assumed_size)
            return self._declaration(node.type_name, f"{node.name}({dimensions})", attributes)
        return self._declaration(node.type_name, node.name, node.attributes)

    def _visit_FortranDeclaration(self, node: FortranDeclaration) -> str:
        """Render one non-parameter declaration from its type and attributes."""
        return self._declaration(node.type_name, node.name, node.attributes)

    def _visit_FortranTypeDefinition(self, node: FortranTypeDefinition) -> str:
        """Render one derived-type definition and preserve component order."""
        lines = [f"type :: {node.name}"]
        lines.extend(self._indented(self.visit(component)) for component in node.components)
        lines.append(f"end type {node.name}")
        return "\n".join(lines)

    def _visit_FortranAssignment(self, node: FortranAssignment) -> str:
        """Render one Fortran assignment, using expression continuations if needed."""
        return self._continued_assignment(node.target, "=", node.expression.text)

    def _visit_FortranPointerAssignment(self, node: FortranPointerAssignment) -> str:
        """Render one Fortran pointer association with the shared wrapper."""
        return self._continued_assignment(node.target, "=>", node.expression.text)

    def _continued_assignment(self, target: str, operator: str, expression: str) -> str:
        """Render an assignment and wrap only a suitable parenthesized expression.

        Target, operator, and expression are already rendered backend values.
        Short or opaque expressions retain their exact text; only a recognized
        parenthesized argument list is delegated to continuation rendering.
        """
        rendered = f"{target} {operator} {expression}"
        if len(rendered) <= self._LINE_LIMIT:
            return rendered
        call = self._parenthesized_items(expression, minimum_items=1)
        if call is None:
            return rendered
        function_name, arguments = call
        return self._continued_call(f"{target} {operator} {function_name}(", arguments)

    def _visit_FortranNullify(self, node: FortranNullify) -> str:
        """Render one Fortran pointer-nullification statement."""
        return f"nullify({node.target})"

    def _visit_FortranAllocate(self, node: FortranAllocate) -> str:
        """Render one allocation with optional extents and status destination."""
        shape = f"({', '.join(item.text for item in node.extents)})" if node.extents else ""
        status = f", stat={node.status}" if node.status is not None else ""
        return f"allocate({node.target}{shape}{status})"

    def _visit_FortranDeallocate(self, node: FortranDeallocate) -> str:
        """Render one explicit deallocation for the node target."""
        return f"deallocate({node.target})"

    def _visit_FortranCall(self, node: FortranCall) -> str:
        """Render one Fortran call and wrap its already-rendered arguments."""
        return self._continued_call(
            f"call {node.function_name}(",
            tuple(argument.text for argument in node.arguments),
        )

    def _visit_FortranIf(self, node: FortranIf) -> str:
        """Render one Fortran conditional with optional else body in node order."""
        lines = [self._continued_condition(node.condition.text)]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        if node.else_body:
            lines.append("else")
            lines.extend(self._indented(self.visit(statement)) for statement in node.else_body)
        lines.append("end if")
        return "\n".join(lines)

    def _continued_condition(self, condition: str) -> str:
        """Render a condition and wrap it only at explicit logical operators.

        The condition is an already-rendered expression. Conditions without
        recognized .and. or .or. boundaries remain intact for final validation.
        """
        rendered = f"if ({condition}) then"
        if len(rendered) <= self._LINE_LIMIT:
            return rendered
        tokens = re.split(r"\s+(\.(?:and|or)\.)\s+", condition, flags=re.IGNORECASE)
        terms = tokens[::2]
        operators = tokens[1::2]
        if len(terms) == 1:
            return rendered
        lines = ["if (&"]
        for term, operator in zip(terms[:-1], operators, strict=True):
            lines.append(f"  & {term.strip()} {operator} &")
        lines.append(f"  & {terms[-1].strip()}) then")
        return "\n".join(lines)

    def _visit_FortranSelectCase(self, node: FortranSelectCase) -> str:
        """Render one select-case statement and preserve case/body ordering."""
        lines = [f"select case ({node.expression.text})"]
        for case in node.cases:
            selector = "default" if case.value is None else f"({case.value})"
            lines.append(f"case {selector}")
            lines.extend(self._indented(self.visit(statement)) for statement in case.body)
        lines.append("end select")
        return "\n".join(lines)

    def _visit_FortranInterface(self, node: FortranInterface) -> str:
        """Render one abstract or concrete interface block from procedure nodes."""
        lines = ["abstract interface" if node.abstract else "interface"]
        lines.extend(self._indented(self.visit(procedure)) for procedure in node.procedures)
        lines.append("end interface")
        return "\n".join(lines)

    def _visit_FortranInterfaceProcedure(self, node: FortranInterfaceProcedure) -> str:
        """Render one interface procedure with declarations and optional result.

        Parameter declarations take precedence when supplied, otherwise the
        procedure parameters are reused. This mirrors the completed backend node
        rather than inferring any native procedure details.
        """
        kind = "subroutine" if node.is_subroutine else "function"
        lines = [self._interface_procedure_signature(node, kind)]
        lines.extend(self._interface_import_lines(node))
        declarations = node.parameter_declarations or node.parameters
        lines.extend(self._indented(self.visit(parameter)) for parameter in declarations)
        lines.extend(self._interface_result_lines(node))
        lines.append(f"end {kind} {node.name}")
        return "\n".join(lines)

    def _interface_procedure_signature(self, node: FortranInterfaceProcedure, kind: str) -> str:
        """Render one interface signature from its procedure node and kind.

        The returned declaration preserves parameter order, pure mode, result
        naming, and the binding clause selected by the backend node.
        """
        suffix = f" result({node.result_name})" if node.result_name is not None else ""
        binding = self._interface_binding_suffix(node)
        prefix = "pure " if node.pure else ""
        return self._continued_call(
            f"{prefix}{kind} {node.name}(",
            tuple(parameter.name for parameter in node.parameters),
            suffix=f"){binding}{suffix}",
        )

    @staticmethod
    def _interface_binding_suffix(node: FortranInterfaceProcedure) -> str:
        """Return the named, unnamed, or absent C binding suffix for one node."""
        if node.bind_name is not None:
            return f' bind(c, name="{node.bind_name}")'
        return " bind(c)" if node.bind_c else ""

    def _interface_import_lines(self, node: FortranInterfaceProcedure) -> tuple[str, ...]:
        """Return the indented import line for a procedure, or no lines."""
        if not node.imports:
            return ()
        return (self._indented(f"import :: {', '.join(node.imports)}"),)

    def _interface_result_lines(self, node: FortranInterfaceProcedure) -> tuple[str, ...]:
        """Return an indented result declaration only when both fields exist."""
        if node.result_name is None or node.result_type is None:
            return ()
        return (self._indented(f"{node.result_type} :: {node.result_name}"),)

    def _function_signature(self, node: FortranFunction) -> str:
        """Render a function or subroutine signature from the procedure node."""
        suffix = f" result({node.result_name})" if node.result_name is not None else ""
        bind = f' bind(c, name="{node.bind_name}")' if node.bind_name is not None else " bind(c)" if node.bind_c else ""
        kind = "subroutine" if node.is_subroutine else "function"
        return self._continued_call(
            f"{kind} {node.name}(",
            tuple(parameter.name for parameter in node.parameters),
            suffix=f"){suffix}{bind}",
        )

    # Continuation and declaration layout

    def _continued_call(
        self,
        prefix: str,
        arguments: tuple[str, ...],
        *,
        suffix: str = ")",
    ) -> str:
        """Render and, when needed, wrap a comma-separated argument list.

        Prefix and suffix are source fragments from a caller. Arguments retain
        their established order; recognized nested forms are delegated only after
        the one-line representation exceeds the preferred line limit.
        """
        rendered = f"{prefix}{', '.join(arguments)}{suffix}"
        if len(rendered) <= self._LINE_LIMIT:
            return rendered
        if not arguments:
            if suffix.startswith(")"):
                return f"{prefix}) &\n  &{suffix[1:]}"
            return rendered

        lines = [f"{prefix}&"]
        last_argument_index = len(arguments) - 1
        for argument_index, argument in enumerate(arguments):
            lines.extend(
                self._continued_argument_lines(
                    argument,
                    last_argument=argument_index == last_argument_index,
                    suffix=suffix,
                )
            )
        return "\n".join(lines)

    def _continued_argument_lines(
        self,
        argument: str,
        *,
        last_argument: bool,
        suffix: str,
    ) -> tuple[str, ...]:
        """Return continuation lines for one already-rendered outer-call argument.

        Simple constructors and parenthesized values receive structural wrapping;
        all other expressions remain opaque text. This helper performs layout
        only and never interprets wrapper or ownership policy.
        """
        array_items = self._array_constructor_items(argument)
        if array_items is not None:
            return self._continued_array_constructor_lines(array_items, last_argument, suffix)
        parenthesized_items = self._parenthesized_items(argument)
        if parenthesized_items is not None and len(f"  & {argument}") > self._LINE_LIMIT:
            return self._continued_parenthesized_lines(parenthesized_items, last_argument, suffix)
        ending = suffix if last_argument else ", &"
        return (f"  & {argument}{ending}",)

    def _continued_array_constructor_lines(
        self,
        items: tuple[str, ...],
        last_argument: bool,
        suffix: str,
    ) -> tuple[str, ...]:
        """Return continuation lines for a simple array constructor.

        Items arrive in source order. Long multiplicative items may split between
        factors; other item text is retained unchanged on a single continuation.
        """
        lines = []
        last_item_index = len(items) - 1
        for item_index, item in enumerate(items):
            opening = "[" if item_index == 0 else ""
            closing = "]" if item_index == last_item_index else ""
            ending = self._continued_item_ending(item_index == last_item_index, last_argument, suffix)
            rendered = f"  & {opening}{item}{closing}{ending}"
            factors = tuple(factor.strip() for factor in item.split(" * "))
            if len(rendered) <= self._LINE_LIMIT or len(factors) == 1:
                lines.append(rendered)
                continue
            lines.append(f"  & {opening}{factors[0]} * &")
            lines.extend(f"  & {factor} * &" for factor in factors[1:-1])
            lines.append(f"  & {factors[-1]}{closing}{ending}")
        return tuple(lines)

    def _continued_parenthesized_lines(
        self,
        expression: tuple[str, tuple[str, ...]],
        last_argument: bool,
        suffix: str,
    ) -> tuple[str, ...]:
        """Return continuation lines for a parsed parenthesized value.

        The name and items are produced by _parenthesized_items. Each item stays
        ordered, with the final item receiving the caller's outer suffix.
        """
        name, items = expression
        lines = [f"  & {name}(&"]
        last_item_index = len(items) - 1
        for item_index, item in enumerate(items):
            closing = ")" if item_index == last_item_index else ""
            ending = self._continued_item_ending(item_index == last_item_index, last_argument, suffix)
            lines.append(f"  &   {item}{closing}{ending}")
        return tuple(lines)

    def _continued_item_ending(self, last_item: bool, last_argument: bool, suffix: str) -> str:
        """Choose the separator for one nested item from its final-position flags."""
        if not last_item:
            return ", &"
        return suffix if last_argument else ", &"

    def _array_constructor_items(self, expression: str) -> tuple[str, ...] | None:
        """Parse a simple bracketed constructor into item text, or return None.

        This intentionally recognizes only the shallow layout form used by the
        continuation renderer; nested semantic expression parsing belongs earlier.
        """
        if not (expression.startswith("[") and expression.endswith("]")):
            return None
        content = expression[1:-1]
        if not content:
            return None
        return tuple(item.strip() for item in content.split(","))

    def _parenthesized_items(
        self,
        expression: str,
        *,
        minimum_items: int = 2,
    ) -> tuple[str, tuple[str, ...]] | None:
        """Parse one shallow parenthesized value into its name and item texts.

        The optional minimum keeps callers from expanding short forms. Unmatched,
        nameless, or too-short expressions return None and remain opaque source.
        """
        opening = expression.find("(")
        if opening < 1 or not expression.endswith(")"):
            return None
        items = tuple(item.strip() for item in expression[opening + 1 : -1].split(","))
        if len(items) < minimum_items:
            return None
        return expression[:opening], items

    def _declaration(self, type_name: str, name: str, attributes: tuple[str, ...]) -> str:
        """Render a Fortran declaration while preserving attribute order."""
        suffix = f", {', '.join(attributes)}" if attributes else ""
        return f"{type_name}{suffix} :: {name}"

    def _indented(self, text: str) -> str:
        """Indent every rendered Fortran line for its containing source block."""
        return "\n".join(f"  {line}" for line in text.splitlines())


if __name__ == "__main__":
    from prik.codegen.nodes import CodeExpression

    bridge_module = FortranModule(
        name="bind_c_printer_demo_wrapper",
        uses=(
            FortranUse("iso_c_binding", ("c_double",)),
            FortranUse("printer_demo", ("native_double_value => DOUBLE_VALUE",)),
        ),
        procedures=(
            FortranFunction(
                name="bind_c_double_value",
                parameters=(FortranParameter("value", "real(c_double)", ("value",)),),
                result_name="result",
                result_type="real(c_double)",
                bind_name="DOUBLE_VALUE",
                body=(FortranAssignment("result", CodeExpression("native_double_value(value)")),),
            ),
        ),
    )

    print("Rendered Fortran bridge source:")
    print(FortranSourcePrinter().doprint(bridge_module))
