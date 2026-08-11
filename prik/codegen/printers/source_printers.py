"""Render lowered C and Fortran backend nodes into compilable source text.

This module is the final text-rendering boundary for generated wrapper source.
It consumes only backend syntax nodes; semantic policy and wrapper planning are
completed by earlier stages.
"""

from __future__ import annotations

import re

from prik.codegen.nodes import (
    CAllowThreadsBegin,
    CAllowThreadsEnd,
    CComment,
    CDeclaration,
    CExpressionStatement,
    CFor,
    CBreak,
    CCase,
    CFunction,
    CFunctionPointerType,
    CFunctionPrototype,
    CHeader,
    CIf,
    CInclude,
    CMacroDefinition,
    CMethodDefEntry,
    CMethodDefTable,
    CModuleDef,
    CModule,
    CModulePropertyEntry,
    CModulePropertySupport,
    CParameter,
    CReturn,
    CStructDefinition,
    CSwitch,
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
from prik.stage_values import StageRecord
from prik.codegen.visitor import ClassVisitor


# C source rendering


class CSourcePrinter(ClassVisitor):
    """Render lowered C backend nodes into source or header text.

    Use this printer after the binding generator has produced C syntax nodes.
    It accepts individual nodes, C translation units, and headers, then returns
    their source representation. Rendering a stage record freezes that record,
    matching the immutable handoff used by the rest of code generation.
    """

    def doprint(self, node: object) -> str:
        """Render one C backend node and return its source text.

        Use this public entrypoint for C headers, translation units, and their
        constituent nodes. A StageRecord is frozen before visitor dispatch;
        unsupported node types retain the visitor's existing exception.
        """
        if isinstance(node, StageRecord):
            node.freeze()
        return self.visit(node)

    def _visit_CModule(self, node: CModule) -> str:
        """Render one C translation unit in compiler-required source order."""
        # Definitions must precede includes, declarations, and function bodies.
        parts = [self.visit(define) for define in node.defines]
        parts.extend(self.visit(include) for include in node.includes)
        parts.extend(self.visit(declaration) for declaration in node.declarations)
        parts.extend(self.visit(function) for function in node.functions)
        return "\n\n".join(part for part in parts if part)

    def _visit_CHeader(self, node: CHeader) -> str:
        """Render one guarded C header from its includes and prototypes."""
        lines = [f"#ifndef {node.guard}", f"#define {node.guard}"]
        lines.extend(self.visit(include) for include in node.includes)
        lines.extend(self.visit(prototype) for prototype in node.prototypes)
        lines.append(f"#endif /* {node.guard} */")
        return "\n".join(lines)

    def _visit_CInclude(self, node: CInclude) -> str:
        """Render one C include directive, preserving the system-header mode."""
        if node.system:
            return f"#include <{node.header}>"
        return f'#include "{node.header}"'

    def _visit_CMacroDefinition(self, node: CMacroDefinition) -> str:
        """Render one C macro, omitting its value when the node has none."""
        if node.value is None:
            return f"#define {node.name}"
        return f"#define {node.name} {node.value}"

    def _visit_CComment(self, node: CComment) -> str:
        """Render one generated C line comment from the node text."""
        return f"// {node.text}"

    def _visit_CFunction(self, node: CFunction) -> str:
        """Render one C function definition with each body statement indented."""
        prefix = f"{node.storage} " if node.storage else ""
        body = "\n".join(self._indented(self.visit(statement)) for statement in node.body)
        return f"{prefix}{self._signature(node.return_type, node.name, node.parameters)} {{\n{body}\n}}"

    def _visit_CFunctionPrototype(self, node: CFunctionPrototype) -> str:
        """Render one C prototype using the shared signature renderer."""
        prefix = f"{node.storage} " if node.storage else ""
        return f"{prefix}{self._signature(node.return_type, node.name, node.parameters)};"

    def _visit_CFunctionPointerType(self, node: CFunctionPointerType) -> str:
        """Render one typed function-pointer alias with explicit void parameters."""
        parameters = ", ".join(node.parameter_types) or "void"
        return f"typedef {node.return_type} (*{node.name})({parameters});"

    def _visit_CStructDefinition(self, node: CStructDefinition) -> str:
        """Render one C struct definition and preserve field declaration order."""
        lines = [f"typedef struct {node.name} {{"]
        lines.extend(f"    {self.visit(field)};" for field in node.fields)
        lines.append(f"}} {node.name};")
        return "\n".join(lines)

    def _visit_CMethodDefTable(self, node: CMethodDefTable) -> str:
        """Render one CPython method table and append its required sentinel."""
        lines = [f"static PyMethodDef {node.name}[] = {{"]
        lines.extend(f"    {self.visit(entry)}," for entry in node.entries)
        lines.extend(("    {NULL, NULL, 0, NULL}", "};"))
        return "\n".join(lines)

    def _visit_CMethodDefEntry(self, node: CMethodDefEntry) -> str:
        """Render one CPython method-table entry with safely quoted strings."""
        return (
            f"{{{self._c_string_literal(node.python_name)}, "
            f"(PyCFunction){node.wrapper_name}, {node.flags}, {self._c_string_literal(node.docstring)}}}"
        )

    def _visit_CModuleDef(self, node: CModuleDef) -> str:
        """Render one CPython module-definition initializer from its node fields."""
        return "\n".join(
            (
                f"static struct PyModuleDef {node.name} = {{",
                "    PyModuleDef_HEAD_INIT,",
                f"    {self._c_string_literal(node.module_name)},",
                f"    {self._c_string_literal(node.docstring)},",
                f"    {node.state_size},",
                f"    {node.methods_name},",
                "};",
            )
        )

    def _visit_CModulePropertySupport(self, node: CModulePropertySupport) -> str:
        """Render all generated module-property routing support in stable order.

        The node supplies getter and setter entries plus the heap subtype name.
        This method returns the three dependent C definitions: attribute getter,
        attribute setter, and module-type installer.
        """
        return "\n\n".join(
            (
                self._module_getattro_source(node),
                self._module_setattro_source(node),
                self._module_property_type_source(node),
            )
        )

    def _module_getattro_source(self, node: CModulePropertySupport) -> str:
        """Build the module attribute getter for every declared property entry.

        The returned function compares only Unicode attribute names, delegates
        matching names to generated getters, and preserves the base module
        fallback for all other attributes.
        """
        lines = [f"static PyObject *{node.name}_getattro(PyObject *self, PyObject *name)", "{"]
        lines.append("    if (PyUnicode_Check(name)) {")
        for entry in node.entries:
            lines.extend(self._module_getter_entry_source(entry))
        lines.extend(("    }", "    return PyModule_Type.tp_getattro(self, name);", "}"))
        return "\n".join(lines)

    def _module_getter_entry_source(self, node: CModulePropertyEntry) -> tuple[str, ...]:
        """Build one getter dispatch branch from a property entry.

        The tuple is inserted into the enclosing Unicode-name guard. It returns
        NULL on comparison failure and calls exactly the getter named by the
        supplied entry when its Python name matches.
        """
        name = self._c_string_literal(node.python_name)
        return (
            "        {",
            f"            int comparison = PyUnicode_CompareWithASCIIString(name, {name});",
            "            if (comparison == -1 && PyErr_Occurred()) return NULL;",
            f"            if (comparison == 0) return {node.getter_name}();",
            "        }",
        )

    def _module_setattro_source(self, node: CModulePropertySupport) -> str:
        """Build the module attribute setter for every declared property entry.

        The returned function dispatches writable properties to their generated
        setters and keeps the base module setter as the nonmatching fallback.
        """
        lines = [f"static int {node.name}_setattro(PyObject *self, PyObject *name, PyObject *value)", "{"]
        lines.append("    if (PyUnicode_Check(name)) {")
        for entry in node.entries:
            lines.extend(self._module_setter_entry_source(entry))
        lines.extend(("    }", "    return PyModule_Type.tp_setattro(self, name, value);", "}"))
        return "\n".join(lines)

    def _module_setter_entry_source(self, node: CModulePropertyEntry) -> tuple[str, ...]:
        """Build one setter dispatch branch and its node-selected error path.

        The tuple rejects replacement for read-only entries. Writable entries
        reject deletion before calling their generated setter with the supplied
        value; those rules are already encoded by the backend node.
        """
        name = self._c_string_literal(node.python_name)
        lines = [
            "        {",
            f"            int comparison = PyUnicode_CompareWithASCIIString(name, {name});",
            "            if (comparison == -1 && PyErr_Occurred()) return -1;",
            "            if (comparison == 0) {",
        ]
        if node.reject_replacement:
            lines.extend(
                (
                    f'                PyErr_SetString(PyExc_AttributeError, "module variable {node.python_name} is read-only");',
                    "                return -1;",
                )
            )
        else:
            lines.extend(
                (
                    "                if (value == NULL) {",
                    f'                    PyErr_SetString(PyExc_AttributeError, "module variable {node.python_name} cannot be deleted");',
                    "                    return -1;",
                    "                }",
                    f"                return {node.setter_name}(value);",
                )
            )
        lines.extend(("            }", "        }"))
        return tuple(lines)

    def _module_property_type_source(self, node: CModulePropertySupport) -> str:
        """Build C slots, type spec, and installer for module property support.

        The returned definitions are ordered so the installer can reference the
        generated slots and type spec without forward declarations. The node's
        name is reused consistently for all emitted symbols.
        """
        return "\n".join(
            (
                f"static PyType_Slot {node.name}_slots[] = {{",
                f"    {{Py_tp_getattro, (void *){node.name}_getattro}},",
                f"    {{Py_tp_setattro, (void *){node.name}_setattro}},",
                "    {0, NULL}",
                "};",
                f"static PyType_Spec {node.name}_spec = {{",
                f"    {self._c_string_literal(f'{node.module_name}.__prik_module_type')},",
                "    0,",
                "    0,",
                "    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,",
                f"    {node.name}_slots",
                "};",
                f"static int {node.name}(PyObject *module)",
                "{",
                "    PyObject *bases = PyTuple_Pack(1, (PyObject *)&PyModule_Type);",
                "    if (bases == NULL) return -1;",
                f"    PyObject *module_type = PyType_FromSpecWithBases(&{node.name}_spec, bases);",
                "    Py_DECREF(bases);",
                "    if (module_type == NULL) return -1;",
                '    int status = PyObject_SetAttrString(module, "__class__", module_type);',
                "    Py_DECREF(module_type);",
                "    return status;",
                "}",
            )
        )

    def _visit_CParameter(self, node: CParameter) -> str:
        """Render one C parameter, including typed callback parameters."""
        if node.function_parameters is not None:
            parameters = ", ".join(node.function_parameters) or "void"
            return f"{node.type_name} (*{node.name})({parameters})"
        return f"{node.type_name} {node.name}"

    def _visit_CDeclaration(self, node: CDeclaration) -> str:
        """Render one C declaration and optional initializer expression."""
        if node.initializer is None:
            return f"{node.type_name} {node.name};"
        return f"{node.type_name} {node.name} = {node.initializer.text};"

    def _visit_CExpressionStatement(self, node: CExpressionStatement) -> str:
        """Render one C expression statement and add its terminating semicolon."""
        return f"{node.expression.text};"

    def _visit_CAllowThreadsBegin(self, _node: CAllowThreadsBegin) -> str:
        """Render the opening CPython thread-release macro without a semicolon."""
        return "Py_BEGIN_ALLOW_THREADS"

    def _visit_CAllowThreadsEnd(self, _node: CAllowThreadsEnd) -> str:
        """Render the closing CPython thread-release macro without a semicolon."""
        return "Py_END_ALLOW_THREADS"

    def _visit_CIf(self, node: CIf) -> str:
        """Render one C conditional and preserve optional else-body ordering."""
        lines = [f"if ({node.condition.text}) {{"]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        if node.else_body:
            lines.append("} else {")
            lines.extend(self._indented(self.visit(statement)) for statement in node.else_body)
        lines.append("}")
        return "\n".join(lines)

    def _visit_CFor(self, node: CFor) -> str:
        """Render one C for-loop with each generated statement indented."""
        lines = [f"for ({node.initializer}; {node.condition.text}; {node.increment.text}) {{"]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        lines.append("}")
        return "\n".join(lines)

    def _visit_CBreak(self, _node: CBreak) -> str:
        """Render one C loop-break statement."""
        return "break;"

    def _visit_CCase(self, node: CCase) -> str:
        """Render one switch case with an explicit terminating branch body."""
        label = "default: {" if node.value is None else f"case {node.value.text}: {{"
        lines = [label]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        lines.append("}")
        return "\n".join(lines)

    def _visit_CSwitch(self, node: CSwitch) -> str:
        """Render one integer-key switch and its ordered cases."""
        lines = [f"switch ({node.expression.text}) {{"]
        lines.extend(self._indented(self.visit(case)) for case in node.cases)
        lines.append("}")
        return "\n".join(lines)

    def _visit_CReturn(self, node: CReturn) -> str:
        """Render one C return with or without the node expression."""
        if node.expression is None:
            return "return;"
        return f"return {node.expression.text};"

    def _signature(self, return_type: str, name: str, parameters: tuple[CParameter, ...]) -> str:
        """Render a C signature from its return type, name, and parameters.

        Empty parameter tuples become void so both function declarations and
        definitions retain C's explicit no-argument form.
        """
        rendered = ", ".join(self.visit(parameter) for parameter in parameters) or "void"
        return f"{return_type} {name}({rendered})"

    def _c_string_literal(self, value: str) -> str:
        """Escape one Python string into the C literal used by generated tables."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'

    def _indented(self, text: str) -> str:
        """Indent every line of rendered C text for a containing block."""
        return "\n".join(f"    {line}" for line in text.splitlines())


# Fortran source rendering


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
        lines.extend(self._indented(self.visit(procedure)) for procedure in node.procedures)
        lines.append(f"end module {node.name}")
        lines.extend(self.visit(procedure) for procedure in node.standalone_procedures)
        return "\n".join(lines)

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
        lines = [signature, *self._fortran_function_specification(node)]
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
