"""Render lowered C backend nodes into compilable source text.

This module is the final text-rendering boundary for generated wrapper source.
It consumes only backend syntax nodes; semantic policy and wrapper planning are
completed by earlier stages.
"""

from __future__ import annotations


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
)
from prik.stage_values import StageRecord
from prik.codegen.visitor import ClassVisitor


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
