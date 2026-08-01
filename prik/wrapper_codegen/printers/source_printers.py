"""Source printers for direct wrapper-plan backend nodes."""

from __future__ import annotations

import re

from prik.wrapper_codegen.nodes import (
    CAllowThreadsBegin,
    CAllowThreadsEnd,
    CComment,
    CDeclaration,
    CExpressionStatement,
    CFor,
    CBreak,
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
from prik.wrapper_codegen.visitor import ClassVisitor


class CSourcePrinter(ClassVisitor):
    """Print isolated C source and header nodes."""

    def doprint(self, node: object) -> str:
        """Render one isolated C backend node."""
        if isinstance(node, StageRecord):
            node.freeze()
        return self.visit(node)

    def _visit_CModule(self, node: CModule) -> str:
        """Render a complete C source module."""
        parts = [self.visit(define) for define in node.defines]
        parts.extend(self.visit(include) for include in node.includes)
        parts.extend(self.visit(declaration) for declaration in node.declarations)
        parts.extend(self.visit(function) for function in node.functions)
        return "\n\n".join(part for part in parts if part)

    def _visit_CHeader(self, node: CHeader) -> str:
        """Render a complete C header module."""
        lines = [f"#ifndef {node.guard}", f"#define {node.guard}"]
        lines.extend(self.visit(include) for include in node.includes)
        lines.extend(self.visit(prototype) for prototype in node.prototypes)
        lines.append(f"#endif /* {node.guard} */")
        return "\n".join(lines)

    def _visit_CInclude(self, node: CInclude) -> str:
        """Render one C include directive."""
        if node.system:
            return f"#include <{node.header}>"
        return f'#include "{node.header}"'

    def _visit_CMacroDefinition(self, node: CMacroDefinition) -> str:
        """Render one C preprocessor macro definition."""
        if node.value is None:
            return f"#define {node.name}"
        return f"#define {node.name} {node.value}"

    def _visit_CComment(self, node: CComment) -> str:
        """Render one generated C line comment."""
        return f"// {node.text}"

    def _visit_CFunction(self, node: CFunction) -> str:
        """Render one C function definition."""
        prefix = f"{node.storage} " if node.storage else ""
        body = "\n".join(self._indented(self.visit(statement)) for statement in node.body)
        return f"{prefix}{self._signature(node.return_type, node.name, node.parameters)} {{\n{body}\n}}"

    def _visit_CFunctionPrototype(self, node: CFunctionPrototype) -> str:
        """Render one C function prototype."""
        prefix = f"{node.storage} " if node.storage else ""
        return f"{prefix}{self._signature(node.return_type, node.name, node.parameters)};"

    def _visit_CFunctionPointerType(self, node: CFunctionPointerType) -> str:
        """Render one named typed function pointer without an object-pointer cast."""
        parameters = ", ".join(node.parameter_types) or "void"
        return f"typedef {node.return_type} (*{node.name})({parameters});"

    def _visit_CStructDefinition(self, node: CStructDefinition) -> str:
        """Render one typed runtime operation table definition."""
        lines = [f"typedef struct {node.name} {{"]
        lines.extend(f"    {self.visit(field)};" for field in node.fields)
        lines.append(f"}} {node.name};")
        return "\n".join(lines)

    def _visit_CMethodDefTable(self, node: CMethodDefTable) -> str:
        """Render one CPython method table."""
        lines = [f"static PyMethodDef {node.name}[] = {{"]
        lines.extend(f"    {self.visit(entry)}," for entry in node.entries)
        lines.extend(("    {NULL, NULL, 0, NULL}", "};"))
        return "\n".join(lines)

    def _visit_CMethodDefEntry(self, node: CMethodDefEntry) -> str:
        """Render one CPython method table entry."""
        return (
            f"{{{self._c_string_literal(node.python_name)}, "
            f"(PyCFunction){node.wrapper_name}, {node.flags}, {self._c_string_literal(node.docstring)}}}"
        )

    def _visit_CModuleDef(self, node: CModuleDef) -> str:
        """Render one CPython module definition."""
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
        """Render module get/set routing through a generated heap subtype."""
        return "\n\n".join(
            (
                self._module_getattro_source(node),
                self._module_setattro_source(node),
                self._module_property_type_source(node),
            )
        )

    def _module_getattro_source(self, node: CModulePropertySupport) -> str:
        lines = [f"static PyObject *{node.name}_getattro(PyObject *self, PyObject *name)", "{"]
        lines.append("    if (PyUnicode_Check(name)) {")
        for entry in node.entries:
            lines.extend(self._module_getter_entry_source(entry))
        lines.extend(("    }", "    return PyModule_Type.tp_getattro(self, name);", "}"))
        return "\n".join(lines)

    def _module_getter_entry_source(self, node: CModulePropertyEntry) -> tuple[str, ...]:
        name = self._c_string_literal(node.python_name)
        return (
            "        {",
            f"            int comparison = PyUnicode_CompareWithASCIIString(name, {name});",
            "            if (comparison == -1 && PyErr_Occurred()) return NULL;",
            f"            if (comparison == 0) return {node.getter_name}();",
            "        }",
        )

    def _module_setattro_source(self, node: CModulePropertySupport) -> str:
        lines = [f"static int {node.name}_setattro(PyObject *self, PyObject *name, PyObject *value)", "{"]
        lines.append("    if (PyUnicode_Check(name)) {")
        for entry in node.entries:
            lines.extend(self._module_setter_entry_source(entry))
        lines.extend(("    }", "    return PyModule_Type.tp_setattro(self, name, value);", "}"))
        return "\n".join(lines)

    def _module_setter_entry_source(self, node: CModulePropertyEntry) -> tuple[str, ...]:
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
        """Render one C parameter."""
        if node.function_parameters is not None:
            parameters = ", ".join(node.function_parameters) or "void"
            return f"{node.type_name} (*{node.name})({parameters})"
        return f"{node.type_name} {node.name}"

    def _visit_CDeclaration(self, node: CDeclaration) -> str:
        """Render one C declaration."""
        if node.initializer is None:
            return f"{node.type_name} {node.name};"
        return f"{node.type_name} {node.name} = {node.initializer.text};"

    def _visit_CExpressionStatement(self, node: CExpressionStatement) -> str:
        """Render one C expression statement."""
        return f"{node.expression.text};"

    def _visit_CAllowThreadsBegin(self, _node: CAllowThreadsBegin) -> str:
        """Render the opening CPython thread-release macro without a semicolon."""
        return "Py_BEGIN_ALLOW_THREADS"

    def _visit_CAllowThreadsEnd(self, _node: CAllowThreadsEnd) -> str:
        """Render the closing CPython thread-release macro without a semicolon."""
        return "Py_END_ALLOW_THREADS"

    def _visit_CIf(self, node: CIf) -> str:
        """Render one C conditional statement."""
        lines = [f"if ({node.condition.text}) {{"]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        if node.else_body:
            lines.append("} else {")
            lines.extend(self._indented(self.visit(statement)) for statement in node.else_body)
        lines.append("}")
        return "\n".join(lines)

    def _visit_CFor(self, node: CFor) -> str:
        """Render one compact table-dispatch loop."""
        lines = [f"for ({node.initializer}; {node.condition.text}; {node.increment.text}) {{"]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        lines.append("}")
        return "\n".join(lines)

    def _visit_CBreak(self, _node: CBreak) -> str:
        """Render one loop break."""
        return "break;"

    def _visit_CReturn(self, node: CReturn) -> str:
        """Render one C return statement."""
        if node.expression is None:
            return "return;"
        return f"return {node.expression.text};"

    def _signature(self, return_type: str, name: str, parameters: tuple[CParameter, ...]) -> str:
        """Render a C function signature."""
        rendered = ", ".join(self.visit(parameter) for parameter in parameters) or "void"
        return f"{return_type} {name}({rendered})"

    def _c_string_literal(self, value: str) -> str:
        """Render a minimal escaped C string literal."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'

    def _indented(self, text: str) -> str:
        return "\n".join(f"    {line}" for line in text.splitlines())


class FortranSourcePrinter(ClassVisitor):
    """Print isolated Fortran source nodes."""

    _LINE_LIMIT = 112
    _MAX_LINE_LENGTH = 132

    def doprint(self, node: object) -> str:
        """Render one isolated Fortran backend node."""
        if isinstance(node, StageRecord):
            node.freeze()
        source = self._format_line_lengths(self.visit(node))
        self._validate_line_lengths(source)
        return source

    def _format_line_lengths(self, source: str) -> str:
        """Wrap overlong free-form lines at syntax-safe token boundaries."""
        lines = []
        for line in source.splitlines():
            lines.extend(self._wrap_rendered_line(line))
        return "\n".join(lines)

    def _wrap_rendered_line(self, line: str) -> tuple[str, ...]:
        """Add free-form continuations without splitting tokens or literals."""
        if len(line) <= self._MAX_LINE_LENGTH:
            return (line,)
        indentation = line[: len(line) - len(line.lstrip())]
        continuation_prefix = f"{indentation}  & "
        prefix = indentation
        remaining = line[len(indentation) :]
        continued_quote = None
        wrapped = []
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
        """Find the preferred safe code or character-literal continuation."""
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
        """Map character offsets protected by Fortran literals to their quote."""
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
        """Find a character-literal continuation that preserves its exact value."""
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
        """Identify a comment marker that is not protected by a literal."""
        return any(character == "!" and index not in literal_positions for index, character in enumerate(text))

    @staticmethod
    def _fortran_break_candidates(text: str, literal_positions: set[int]) -> tuple[int, ...]:
        """Collect token boundaries that preserve free-form statement syntax."""
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
        """Reject generated free-form source that a standard compiler truncates."""
        for line_number, line in enumerate(source.splitlines(), start=1):
            if len(line) > self._MAX_LINE_LENGTH:
                raise ValueError(
                    f"Generated Fortran line {line_number} has {len(line)} columns; "
                    f"the free-form limit is {self._MAX_LINE_LENGTH}: {line}"
                )

    def _visit_FortranModule(self, node: FortranModule) -> str:
        """Render a complete Fortran module."""
        lines = [f"module {node.name}"]
        lines.extend(self._indented(self.visit(use)) for use in node.uses)
        lines.append("  implicit none")
        lines.extend(self._indented(self.visit(definition)) for definition in node.type_definitions)
        lines.extend(self._indented(self.visit(interface)) for interface in node.interfaces)
        lines.append("contains")
        lines.extend(self._indented(self.visit(procedure)) for procedure in node.procedures)
        lines.append(f"end module {node.name}")
        lines.extend(self.visit(procedure) for procedure in node.external_procedures)
        return "\n".join(lines)

    def _visit_FortranUse(self, node: FortranUse) -> str:
        """Render one Fortran use statement."""
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
        """Render one Fortran function."""
        signature = self._function_signature(node)
        lines = [signature, *self._fortran_function_specification(node)]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        if node.internal_procedures:
            lines.append("contains")
            lines.extend(self._indented(self.visit(procedure)) for procedure in node.internal_procedures)
        lines.append(f"end {'subroutine' if node.is_subroutine else 'function'} {node.name}")
        return "\n".join(lines)

    def _fortran_function_specification(self, node: FortranFunction) -> list[str]:
        """Render use, declaration, and local-interface specification lines."""
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
        """Render one Fortran parameter declaration."""
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
        """Render one Fortran declaration."""
        return self._declaration(node.type_name, node.name, node.attributes)

    def _visit_FortranTypeDefinition(self, node: FortranTypeDefinition) -> str:
        """Render one typed holder shared by producers and consumers."""
        lines = [f"type :: {node.name}"]
        lines.extend(self._indented(self.visit(component)) for component in node.components)
        lines.append(f"end type {node.name}")
        return "\n".join(lines)

    def _visit_FortranAssignment(self, node: FortranAssignment) -> str:
        """Render one Fortran assignment."""
        return self._continued_assignment(node.target, "=", node.expression.text)

    def _visit_FortranPointerAssignment(self, node: FortranPointerAssignment) -> str:
        """Render one Fortran pointer association."""
        return self._continued_assignment(node.target, "=>", node.expression.text)

    def _continued_assignment(self, target: str, operator: str, expression: str) -> str:
        """Wrap a long assignment whose expression has parenthesized items."""
        rendered = f"{target} {operator} {expression}"
        if len(rendered) <= self._LINE_LIMIT:
            return rendered
        call = self._parenthesized_items(expression, minimum_items=1)
        if call is None:
            return rendered
        function_name, arguments = call
        return self._continued_call(f"{target} {operator} {function_name}(", arguments)

    def _visit_FortranNullify(self, node: FortranNullify) -> str:
        """Render one pointer nullification statement."""
        return f"nullify({node.target})"

    def _visit_FortranAllocate(self, node: FortranAllocate) -> str:
        """Render one explicit allocation statement."""
        shape = f"({', '.join(item.text for item in node.extents)})" if node.extents else ""
        status = f", stat={node.status}" if node.status is not None else ""
        return f"allocate({node.target}{shape}{status})"

    def _visit_FortranDeallocate(self, node: FortranDeallocate) -> str:
        """Render one explicit deallocation statement."""
        return f"deallocate({node.target})"

    def _visit_FortranCall(self, node: FortranCall) -> str:
        """Render one Fortran call statement."""
        return self._continued_call(
            f"call {node.function_name}(",
            tuple(argument.text for argument in node.arguments),
        )

    def _visit_FortranIf(self, node: FortranIf) -> str:
        """Render one Fortran conditional statement."""
        lines = [self._continued_condition(node.condition.text)]
        lines.extend(self._indented(self.visit(statement)) for statement in node.body)
        if node.else_body:
            lines.append("else")
            lines.extend(self._indented(self.visit(statement)) for statement in node.else_body)
        lines.append("end if")
        return "\n".join(lines)

    def _continued_condition(self, condition: str) -> str:
        """Wrap a long logical condition at explicit Fortran operators."""
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
        """Render runtime-rank dispatch without hiding branch structure."""
        lines = [f"select case ({node.expression.text})"]
        for case in node.cases:
            selector = "default" if case.value is None else f"({case.value})"
            lines.append(f"case {selector}")
            lines.extend(self._indented(self.visit(statement)) for statement in case.body)
        lines.append("end select")
        return "\n".join(lines)

    def _visit_FortranInterface(self, node: FortranInterface) -> str:
        """Render one explicit interface block."""
        lines = ["abstract interface" if node.abstract else "interface"]
        lines.extend(self._indented(self.visit(procedure)) for procedure in node.procedures)
        lines.append("end interface")
        return "\n".join(lines)

    def _visit_FortranInterfaceProcedure(self, node: FortranInterfaceProcedure) -> str:
        """Render one native procedure declaration inside an interface."""
        kind = "subroutine" if node.is_subroutine else "function"
        lines = [self._interface_procedure_signature(node, kind)]
        lines.extend(self._interface_import_lines(node))
        declarations = node.parameter_declarations or node.parameters
        lines.extend(self._indented(self.visit(parameter)) for parameter in declarations)
        lines.extend(self._interface_result_lines(node))
        lines.append(f"end {kind} {node.name}")
        return "\n".join(lines)

    def _interface_procedure_signature(self, node: FortranInterfaceProcedure, kind: str) -> str:
        """Render the ordered parameter list and optional native binding."""
        suffix = f" result({node.result_name})" if node.result_name is not None else ""
        binding = self._interface_binding_suffix(node)
        return self._continued_call(
            f"{kind} {node.name}(",
            tuple(parameter.name for parameter in node.parameters),
            suffix=f"){binding}{suffix}",
        )

    @staticmethod
    def _interface_binding_suffix(node: FortranInterfaceProcedure) -> str:
        """Spell one named, unnamed, or absent C binding clause."""
        if node.bind_name is not None:
            return f' bind(c, name="{node.bind_name}")'
        return " bind(c)" if node.bind_c else ""

    def _interface_import_lines(self, node: FortranInterfaceProcedure) -> tuple[str, ...]:
        """Render the optional interface import declaration."""
        if not node.imports:
            return ()
        return (self._indented(f"import :: {', '.join(node.imports)}"),)

    def _interface_result_lines(self, node: FortranInterfaceProcedure) -> tuple[str, ...]:
        """Render a complete function result declaration when present."""
        if node.result_name is None or node.result_type is None:
            return ()
        return (self._indented(f"{node.result_type} :: {node.result_name}"),)

    def _function_signature(self, node: FortranFunction) -> str:
        """Render a Fortran function signature."""
        suffix = f" result({node.result_name})" if node.result_name is not None else ""
        bind = f' bind(c, name="{node.bind_name}")' if node.bind_name is not None else " bind(c)" if node.bind_c else ""
        kind = "subroutine" if node.is_subroutine else "function"
        return self._continued_call(
            f"{kind} {node.name}(",
            tuple(parameter.name for parameter in node.parameters),
            suffix=f"){suffix}{bind}",
        )

    def _continued_call(
        self,
        prefix: str,
        arguments: tuple[str, ...],
        *,
        suffix: str = ")",
    ) -> str:
        """Wrap one comma-separated Fortran argument list with continuations."""
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
        """Wrap one outer-call argument without interpreting semantic policy."""
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
        """Wrap one simple Fortran array constructor item by item."""
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
        """Wrap one nested array section or other simple parenthesized value."""
        name, items = expression
        lines = [f"  & {name}(&"]
        last_item_index = len(items) - 1
        for item_index, item in enumerate(items):
            closing = ")" if item_index == last_item_index else ""
            ending = self._continued_item_ending(item_index == last_item_index, last_argument, suffix)
            lines.append(f"  &   {item}{closing}{ending}")
        return tuple(lines)

    def _continued_item_ending(self, last_item: bool, last_argument: bool, suffix: str) -> str:
        """Return the continuation or outer-call ending for one nested item."""
        if not last_item:
            return ", &"
        return suffix if last_argument else ", &"

    def _array_constructor_items(self, expression: str) -> tuple[str, ...] | None:
        """Return simple array-constructor items that need their own lines."""
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
        """Return simple parenthesized items that need continuation lines."""
        opening = expression.find("(")
        if opening < 1 or not expression.endswith(")"):
            return None
        items = tuple(item.strip() for item in expression[opening + 1 : -1].split(","))
        if len(items) < minimum_items:
            return None
        return expression[:opening], items

    def _declaration(self, type_name: str, name: str, attributes: tuple[str, ...]) -> str:
        """Render a Fortran declaration."""
        suffix = f", {', '.join(attributes)}" if attributes else ""
        return f"{type_name}{suffix} :: {name}"

    def _indented(self, text: str) -> str:
        """Indent a rendered procedure inside a module body."""
        return "\n".join(f"  {line}" for line in text.splitlines())
