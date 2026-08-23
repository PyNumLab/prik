"""Convert parsed C declarations into language-neutral semantic IR.

The public helpers at the end of this module consume C parser models and
produce :class:`~prik.semantics.models.SemanticModule` objects.  They preserve
C type, declaration, target-fact, and source-provenance information for later
semantic policy completion; they do not choose wrapper implementation policy.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
import re
from pathlib import Path
from typing import Any

from prik.contracts import NATIVE_C_SCALAR_CASTS
from prik.semantics.metadata import EXPLICIT_C_EXPORT_METADATA, NATIVE_C_SCALAR_CAST_METADATA
from prik.semantics.scalar_types import BOOLEAN_STORAGE_BITS

from prik.parsers.c.models import (
    CArray,
    CBool,
    CChar,
    CComposedType,
    CConst,
    CDouble,
    CDoubleComplex,
    CEnum,
    CFile,
    CFloat,
    CFloatComplex,
    CFunction,
    CFunctionType,
    CMacro,
    CLong,
    CLongDouble,
    CLongDoubleComplex,
    CLongLong,
    CParameter,
    CPointer,
    CProject,
    CQualifier,
    CRestrict,
    CShort,
    CSignedChar,
    CStruct,
    CType,
    CTypedef,
    CUnion,
    CUnknownType,
    CUnsignedChar,
    CUnsignedInt,
    CUnsignedLong,
    CUnsignedLongLong,
    CUnsignedShort,
    CVariable,
    CVoid,
    CInt,
)
from prik.utilities.visitor import ClassVisitor

from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    ProjectionMapping,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticField,
    SemanticFunction,
    SemanticModule,
    SemanticOrigin,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
    _module_semantic_types,
)


_IDENTIFIER_RE = re.compile(r"[^0-9A-Za-z_]+")
_C_IDENTIFIER_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_C_EXPORT_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_C_INTEGER_LITERAL_SUFFIX_RE = re.compile(r"(?<![0-9A-Za-z_.])((?:0[xX][0-9A-Fa-f]+|\d+))[uUlL]+(?![0-9A-Za-z_.])")
_C_OCTAL_LITERAL_RE = re.compile(r"(?<![0-9A-Za-z_.])0([0-7]+)(?![0-9A-Za-z_.])")
_INTEGER_EXPRESSION_CHARS_RE = re.compile(r"[0-9A-Za-z_+\-*/%<>&|^~()\s]+")
_INTEGER_LITERAL_RE = re.compile(r"[-+]?(?:0[xX][0-9A-Fa-f]+|\d+)(?:[uUlL]*)\Z")
_FLOAT_LITERAL_RE = re.compile(
    r"[-+]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+[eE][-+]?\d+)|(?:\d+\.\d*[eE][-+]?\d+))(?:[fFlL]*)\Z"
)
_INTEGER_EXPRESSION_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.LShift,
    ast.RShift,
    ast.BitOr,
    ast.BitAnd,
    ast.BitXor,
    ast.Invert,
    ast.UAdd,
    ast.USub,
)
_SIGNED_WIDTH_TYPES = {8: "Int8", 16: "Int16", 32: "Int32", 64: "Int64"}
_UNSIGNED_WIDTH_TYPES = {8: "UInt8", 16: "UInt16", 32: "UInt32", 64: "UInt64"}
_REAL_WIDTH_TYPES = {32: "Float32", 64: "Float64", 80: "Float128", 96: "Float128", 128: "Float128"}
_COMPLEX_WIDTH_TYPES = {64: "Complex64", 128: "Complex128", 160: "Complex256", 192: "Complex256", 256: "Complex256"}
_PRIMITIVE_TYPE_MAP: dict[type[CType], str | None] = {
    CVoid: None,
    CBool: "Bool",
    CChar: "Int8",
    CSignedChar: "Int8",
    CUnsignedChar: "UInt8",
    CShort: "Int16",
    CUnsignedShort: "UInt16",
    CInt: "Int",
    CUnsignedInt: "UInt32",
    CLong: "Int64",
    CUnsignedLong: "UInt64",
    CLongLong: "Int64",
    CUnsignedLongLong: "UInt64",
    CFloat: "Float32",
    CDouble: "Float64",
    CLongDouble: "Float128",
    CFloatComplex: "Complex64",
    CDoubleComplex: "Complex128",
    CLongDoubleComplex: "Complex256",
}

_PRIMITIVE_TYPE_FACT_NAMES: dict[type[CType], str] = {
    CBool: "_Bool",
    CChar: "char",
    CSignedChar: "signed char",
    CUnsignedChar: "unsigned char",
    CShort: "short",
    CUnsignedShort: "unsigned short",
    CInt: "int",
    CUnsignedInt: "unsigned int",
    CLong: "long",
    CUnsignedLong: "unsigned long",
    CLongLong: "long long",
    CUnsignedLongLong: "unsigned long long",
    CFloat: "float",
    CDouble: "double",
    CLongDouble: "long double",
    CFloatComplex: "float _Complex",
    CDoubleComplex: "double _Complex",
    CLongDoubleComplex: "long double _Complex",
}

_PRIMITIVE_NATIVE_CAST_NAMES = {
    primitive: next(name for name, spelling in NATIVE_C_SCALAR_CASTS.items() if spelling == c_spelling)
    for primitive, c_spelling in _PRIMITIVE_TYPE_FACT_NAMES.items()
}

_CANONICAL_C_TYPE_FACT_NAMES = {
    "Bool": "_Bool",
    "Bool8": "_Bool",
    "Bool16": "_Bool",
    "Bool32": "_Bool",
    "Bool64": "_Bool",
    "Int8": "int8_t",
    "Int16": "int16_t",
    "Int32": "int32_t",
    "Int64": "int64_t",
    "UInt8": "uint8_t",
    "UInt16": "uint16_t",
    "UInt32": "uint32_t",
    "UInt64": "uint64_t",
    "Float32": "float",
    "Float64": "double",
    "Float128": "long double",
    "Complex64": "float _Complex",
    "Complex128": "double _Complex",
    "Complex256": "long double _Complex",
}

_STANDARD_TYPE_FALLBACKS = {
    "bool": "Bool",
    "size_t": "SizeT",
    "uint8_t": "UInt8",
    "uint16_t": "UInt16",
    "uint32_t": "UInt32",
    "uint64_t": "UInt64",
    "int8_t": "Int8",
    "int16_t": "Int16",
    "int32_t": "Int32",
    "int64_t": "Int64",
}

_C_INT_FALLBACK_FACT = {
    "available": True,
    "kind": "integer",
    "signed": True,
    "bits": 32,
    "underlying_c_type": "int",
}


class CToIRConverter(ClassVisitor):
    """Convert parsed C models into the shared semantic IR.

    The converter intentionally keeps C parser facts as provenance instead of
    teaching the parser wrapper policy. The produced semantic IR is then
    completed and, when a backend exists, planned by the shared wrapper path.
    """

    def __init__(
        self,
        *,
        standard_type_report: Any | None = None,
        primitive_type_map: dict[type[CType], str | None] | None = None,
    ):
        """Configure conversion with optional compiler facts and primitive overrides.

        ``standard_type_report`` supplies target-measured C type facts, while
        ``primitive_type_map`` replaces selected parser primitive mappings.
        Mutable symbol registries are initialized for the current file or
        project visitor and are restored after scoped conversion.
        """
        self.primitive_type_map = dict(_PRIMITIVE_TYPE_MAP)
        if primitive_type_map:
            self.primitive_type_map.update(primitive_type_map)
        self.standard_type_facts = self._standard_type_facts(standard_type_report)
        self.typedefs: dict[str, CTypedef] = {}
        self.structs: dict[str, CStruct] = {}
        self.unions: dict[str, CUnion] = {}
        self.enums: dict[str, CEnum] = {}
        self.opaque_standard_types: set[str] = set()

    def visit(self, node, **context):
        """Convert one supported C parser model through the shared class visitor.

        Use this for a specific model when a public convenience helper does not
        match the input shape.  The returned semantic type follows ``node``;
        unsupported parser models raise :class:`TypeError`.
        """
        return self._visit(node, **context)

    @staticmethod
    def _visit_not_supported(node):
        """Reject parser models without a semantic conversion visitor."""
        raise TypeError(f"Unsupported C parse object: {type(node)!r}")

    # Project and translation-unit visitors

    def _visit_CProject(self, project: CProject) -> list[SemanticModule]:
        """Convert each project file in stable filename order with global type context.

        Project symbol registries let each file resolve cross-file declarations.
        After conversion, the existing external-type classifier links consumers
        to the module that owns each public aggregate type.
        """
        self.typedefs = dict(project.typedefs)
        self.structs = dict(project.structs)
        self.unions = dict(project.unions)
        self.enums = dict(project.enums)
        modules = [
            self.visit(
                c_file,
                typedefs=self.typedefs,
                structs=self.structs,
                unions=self.unions,
                enums=self.enums,
            )
            for _filename, c_file in sorted(project.files.items())
        ]
        self._classify_project_external_types(modules, project)
        return modules

    def project_to_semantic_module(
        self,
        project: CProject,
        *,
        name: str = "c_project",
    ) -> SemanticModule:
        """Merge a project registry into one synthetic semantic module.

        This compatibility entrypoint converts project-level registries without
        file-module exposure processing.  It restores every converter registry
        in ``finally`` so a reused converter has no project-state leakage.
        """
        previous = self.typedefs, self.structs, self.unions, self.enums, self.opaque_standard_types
        self.typedefs = dict(project.typedefs)
        self.structs = dict(project.structs)
        self.unions = dict(project.unions)
        self.enums = dict(project.enums)
        self.opaque_standard_types = set()
        try:
            semantic_functions = [self.visit(function) for function in project.functions.values()]
            semantic_variables = [
                *[
                    enumerator
                    for enum in self._project_enum_declarations(project)
                    for enumerator in self._enum_constants_for_enum(enum)
                ],
                *self._macro_constants_from_macros(list(project.macros.values())),
                *[self.visit(variable) for variable in project.variables.values()],
            ]
            semantic_classes = [
                *[self.visit(struct) for struct in project.structs.values()],
                *[self.visit(union) for union in project.unions.values()],
                *self._opaque_standard_type_classes(),
            ]
            return SemanticModule(
                name=self._identifier(name),
                functions=semantic_functions,
                classes=semantic_classes,
                variables=semantic_variables,
                metadata=self._project_metadata(project),
                origin=SemanticOrigin(
                    source_language="c",
                    native_name=name,
                    native_scope=name,
                    source_kind="project",
                    metadata={"files": sorted(project.files)},
                ),
            )
        finally:
            self.typedefs, self.structs, self.unions, self.enums, self.opaque_standard_types = previous

    def _visit_CFile(
        self,
        c_file: CFile,
        *,
        typedefs: dict[str, CTypedef] | None = None,
        structs: dict[str, CStruct] | None = None,
        unions: dict[str, CUnion] | None = None,
        enums: dict[str, CEnum] | None = None,
    ) -> SemanticModule:
        """Convert one translation unit while temporarily installing its type registries.

        The visitor converts functions, constants, variables, and aggregates in
        parser order, then applies include exposure and private-class handling.
        Registry state is restored even if conversion raises an existing error.
        """
        previous = self.typedefs, self.structs, self.unions, self.enums
        self.typedefs = typedefs or {typedef.name: typedef for typedef in c_file.typedefs}
        self.structs = structs or {struct.name: struct for struct in c_file.structs if struct.name}
        self.unions = unions or {union.name: union for union in c_file.unions if union.name}
        self.enums = enums or {enum.name: enum for enum in c_file.enums if enum.name}
        try:
            self.opaque_standard_types = set()
            semantic_functions = [self.visit(function) for function in c_file.functions]
            semantic_variables = [
                *[enumerator for enum in c_file.enums for enumerator in self._enum_constants_for_enum(enum)],
                *self._macro_constants(c_file),
                *[self.visit(variable) for variable in c_file.variables],
            ]
            semantic_classes = [
                *[self.visit(struct) for struct in c_file.structs],
                *[self.visit(union) for union in c_file.unions],
                *self._opaque_standard_type_classes(),
            ]
            module = SemanticModule(
                name=self._module_name(c_file),
                functions=semantic_functions,
                classes=semantic_classes,
                variables=semantic_variables,
                metadata=self._file_metadata(c_file),
                origin=SemanticOrigin(
                    source_language="c",
                    native_name=c_file.filename,
                    native_scope=c_file.filename,
                    source_kind="translation_unit",
                    metadata={
                        "preprocessing": c_file.preprocessing,
                    },
                ),
            )
            self._apply_include_exposure(module, c_file)
            self._externalize_private_classes(module)
            return module
        finally:
            self.typedefs, self.structs, self.unions, self.enums = previous

    # Declaration visitors

    def _visit_CFunction(self, function: CFunction) -> SemanticFunction:
        """Convert a C function declaration into arguments, result, and projection facts.

        Parameter order is retained for both native and Python projection
        positions.  Storage specifiers only determine the existing visibility
        fact here; wrapper policy remains a later semantic stage.
        """
        arguments = [
            self.visit(parameter, position=index, owner=function.name)
            for index, parameter in enumerate(function.parameters)
        ]
        metadata: dict[str, Any] = {
            "storage": list(function.storage),
            "specifiers": list(function.specifiers),
            "prototype_style": function.prototype_style,
            "is_definition": function.is_definition,
            # This is source provenance, not a wrapper decision.  Policy
            # consumes it later to choose an exact direct C declaration or a
            # documented blocker before planning starts.
            "c_abi": {
                "calling_convention": "c",
                "variadic": function.is_variadic,
                "result": self._c_abi_type_facts(function.result_type),
                "parameters": [
                    self._c_abi_type_facts(parameter.declared_type or parameter.type, name=parameter.name)
                    for parameter in function.parameters
                ],
            },
        }
        return SemanticFunction(
            name=function.name,
            native_name=function.name,
            arguments=arguments,
            return_type=self._return_type(function.result_type, owner=f"{function.name}.return"),
            projection=[
                ProjectionMapping(
                    python_name=argument.name,
                    native_name=parameter.name or argument.name,
                    native_position=index,
                    python_position=index,
                    native_cast=argument.semantic_type.metadata.get(NATIVE_C_SCALAR_CAST_METADATA),
                )
                for index, (parameter, argument) in enumerate(zip(function.parameters, arguments, strict=False))
            ],
            metadata=metadata,
            visibility="private" if "static" in function.storage else "public",
            origin=SemanticOrigin(
                source_language="c",
                native_name=function.name,
                source_kind="function",
                source_type=self._type_text(function.type),
                source_location=self._location_dict(function.source_location),
            ),
        )

    def _visit_CParameter(
        self,
        parameter: CParameter,
        *,
        position: int = 0,
        owner: str | None = None,
    ) -> SemanticArgument:
        """Convert one parameter and retain native position and declaration provenance.

        Anonymous parameters receive the stable ``arg<position>`` name.  A
        parser-detected function pointer is represented by the existing callback
        placeholder rather than inferred wrapper policy.
        """
        name = parameter.name or f"arg{position}"
        source_type = parameter.declared_type or parameter.type
        semantic_type = self.visit(source_type, owner=f"{owner or '<function>'}.{name}", as_type=True)
        metadata: dict[str, Any] = {"native_position": position}
        if parameter.callback_candidate:
            semantic_type = self._callback_placeholder(source_type)

        return SemanticArgument(
            name=name,
            semantic_type=semantic_type,
            metadata=metadata,
            origin=SemanticOrigin(
                source_language="c",
                native_name=parameter.name,
                native_scope=owner,
                source_kind="parameter",
                source_type=self._type_text(source_type),
                source_location=self._location_dict(parameter.source_location),
            ),
        )

    def _visit_CVariable(
        self,
        variable: CVariable,
        *,
        binding_cls: type[SemanticVariable] = SemanticVariable,
        source_kind: str = "variable",
    ) -> SemanticVariable:
        """Convert a global variable or aggregate field into the requested binding subtype.

        The result retains static visibility, initializer text, bit width, and
        source origin.  Callback candidates use the existing function-pointer
        placeholder before the semantic binding is constructed.
        """
        name = variable.name or "<anonymous>"
        semantic_type = self.visit(variable.type, owner=name, as_type=True)
        if variable.callback_candidate:
            semantic_type = self._callback_placeholder(variable.type)
        return binding_cls(
            name=name,
            semantic_type=semantic_type,
            visibility="private" if "static" in variable.storage else "public",
            default_value=variable.initializer.source_text if variable.initializer is not None else None,
            origin=SemanticOrigin(
                source_language="c",
                native_name=variable.name,
                source_kind=source_kind,
                source_type=self._type_text(variable.type),
                source_location=self._location_dict(variable.source_location),
                metadata={"storage": list(variable.storage), "bit_width": variable.bit_width},
            ),
        )

    def _visit_CStruct(
        self, struct: CStruct, *, as_type: bool = False, owner: str | None = None
    ) -> SemanticClass | SemanticType:
        """Convert a C struct as a semantic class or, in type mode, a named reference.

        Class conversion retains C kind, incompleteness, anonymous status, and
        nested aggregate fields.  ``as_type`` delegates to existing registry
        resolution for declarations that only refer to the struct.
        """
        if as_type:
            return self._struct_type(struct, owner=owner)
        name = self._struct_name(struct)
        metadata: dict[str, Any] = {"c_kind": "struct", "incomplete": struct.is_incomplete}
        if struct.name is None:
            metadata["c_anonymous"] = True
        fields, nested_classes = self._aggregate_fields(struct.members)
        return SemanticClass(
            name=name,
            native_name=struct.reference_name,
            fields=fields,
            classes=nested_classes,
            base_classes=self._aggregate_base_classes(
                "struct", anonymous=struct.name is None, opaque=struct.is_incomplete
            ),
            metadata=metadata,
            origin=SemanticOrigin(
                source_language="c",
                native_name=struct.reference_name,
                source_kind="struct",
                source_type=struct.reference_name,
                source_location=self._location_dict(struct.source_location),
            ),
        )

    def _visit_CUnion(
        self, union: CUnion, *, as_type: bool = False, owner: str | None = None
    ) -> SemanticClass | SemanticType:
        """Convert a C union as a semantic class or, in type mode, a named reference.

        The class path preserves union-specific metadata and nested aggregates;
        the type path uses the existing union registry resolution without
        changing the parser declaration's incomplete-state semantics.
        """
        if as_type:
            return self._union_type(union, owner=owner)
        metadata: dict[str, Any] = {"c_kind": "union", "incomplete": union.is_incomplete}
        if union.name is None:
            metadata["c_anonymous"] = True
        fields, nested_classes = self._aggregate_fields(union.members)
        return SemanticClass(
            name=self._union_name(union),
            native_name=union.reference_name,
            fields=fields,
            classes=nested_classes,
            base_classes=self._aggregate_base_classes(
                "union", anonymous=union.name is None, opaque=union.is_incomplete
            ),
            metadata=metadata,
            origin=SemanticOrigin(
                source_language="c",
                native_name=union.reference_name,
                source_kind="union",
                source_type=union.reference_name,
                source_location=self._location_dict(union.source_location),
            ),
        )

    def _aggregate_fields(
        self,
        members: list[CVariable],
    ) -> tuple[list[SemanticField], list[SemanticClass]]:
        """Convert aggregate members into fields and separately owned anonymous classes.

        Unnamed nested structs and unions receive deterministic private names so
        their field can reference the nested class.  Nameless ordinary members
        remain omitted, matching the established semantic surface.
        """
        fields: list[SemanticField] = []
        nested_classes: list[SemanticClass] = []
        anonymous_member_counts: dict[str, int] = {"struct": 0, "union": 0}
        used_nested_names: set[str] = set()

        for member in members:
            if isinstance(member.type, CStruct | CUnion) and member.type.name is None:
                kind = "struct" if isinstance(member.type, CStruct) else "union"
                field_name = member.name
                anonymous_member = field_name is None
                if field_name is None:
                    index = anonymous_member_counts[kind]
                    anonymous_member_counts[kind] += 1
                    field_name = f"_anonymous_{kind}_{index}"
                nested_name = self._nested_aggregate_name(field_name, used_nested_names)
                used_nested_names.add(nested_name)
                nested_classes.append(self._nested_aggregate_class(member.type, name=nested_name))
                fields.append(
                    self._aggregate_member_argument(
                        member,
                        name=field_name,
                        semantic_type=self._aggregate_reference_type(member.type, name=nested_name),
                        anonymous_member=anonymous_member,
                    )
                )
                continue

            if member.name is None:
                continue
            fields.append(self.visit(member, binding_cls=SemanticField, source_kind="field"))

        return fields, nested_classes

    def _nested_aggregate_class(self, aggregate: CStruct | CUnion, *, name: str) -> SemanticClass:
        """Build a semantic class for one anonymous nested struct or union.

        ``name`` is supplied by the parent-field naming pass.  Nested members
        are recursively converted, and the output records anonymous and opaque
        facts without registering a new top-level parser symbol.
        """
        if isinstance(aggregate, CStruct):
            fields, nested_classes = self._aggregate_fields(aggregate.members)
            return SemanticClass(
                name=name,
                native_name=aggregate.reference_name,
                fields=fields,
                classes=nested_classes,
                base_classes=self._aggregate_base_classes(
                    "struct",
                    anonymous=True,
                    opaque=aggregate.is_incomplete,
                ),
                metadata={
                    "c_kind": "struct",
                    "incomplete": aggregate.is_incomplete,
                    "c_anonymous": True,
                },
                origin=SemanticOrigin(
                    source_language="c",
                    native_name=aggregate.reference_name,
                    source_kind="struct",
                    source_type=aggregate.reference_name,
                    source_location=self._location_dict(aggregate.source_location),
                ),
            )

        fields, nested_classes = self._aggregate_fields(aggregate.members)
        return SemanticClass(
            name=name,
            native_name=aggregate.reference_name,
            fields=fields,
            classes=nested_classes,
            base_classes=self._aggregate_base_classes(
                "union",
                anonymous=True,
                opaque=aggregate.is_incomplete,
            ),
            metadata={
                "c_kind": "union",
                "incomplete": aggregate.is_incomplete,
                "c_anonymous": True,
            },
            origin=SemanticOrigin(
                source_language="c",
                native_name=aggregate.reference_name,
                source_kind="union",
                source_type=aggregate.reference_name,
                source_location=self._location_dict(aggregate.source_location),
            ),
        )

    @staticmethod
    def _aggregate_base_classes(kind: str, *, anonymous: bool, opaque: bool) -> list[str]:
        """Return semantic marker bases for a struct/union and its declaration facts."""
        base_classes = ["CStruct" if kind == "struct" else "CUnion"]
        if anonymous:
            base_classes.append("CAnonymous")
        if opaque:
            base_classes.append("Opaque")
        return base_classes

    def _aggregate_reference_type(self, aggregate: CStruct | CUnion, *, name: str) -> SemanticType:
        """Create the type reference used by a field that owns an anonymous aggregate."""
        kind = "struct" if isinstance(aggregate, CStruct) else "union"
        return SemanticType(
            name=name,
            dtype=name,
            metadata={
                "c_kind": kind,
                "incomplete": getattr(aggregate, "is_incomplete", False),
                "c_anonymous": True,
            },
            origin=self._type_origin(aggregate, native_name=aggregate.reference_name),
        )

    def _aggregate_member_argument(
        self,
        member: CVariable,
        *,
        name: str,
        semantic_type: SemanticType,
        anonymous_member: bool,
    ) -> SemanticField:
        """Create an aggregate field, marking anonymous member access when required.

        The supplied ``semantic_type`` is mutated only to append the
        ``CAnonymousMember`` constraint for a field with no native name.
        """
        if anonymous_member:
            semantic_type.constraints.append(SemanticConstraint("CAnonymousMember"))
        return SemanticField(
            name=name,
            semantic_type=semantic_type,
            visibility="private" if "static" in member.storage else "public",
            default_value=member.initializer.source_text if member.initializer is not None else None,
            origin=SemanticOrigin(
                source_language="c",
                native_name=member.name,
                source_kind="field",
                source_type=self._type_text(member.type),
                source_location=self._location_dict(member.source_location),
                metadata={"storage": list(member.storage), "bit_width": member.bit_width},
            ),
        )

    # Type visitors and conversion helpers

    def _visit_CType(
        self,
        type_: CType,
        *,
        owner: str | None = None,
        as_type: bool = False,
    ) -> SemanticType:
        """Convert arithmetic primitives through the explicit ABI type table."""
        return self._primitive_type(type_, owner=owner)

    def _visit_CComposedType(self, type_: CComposedType, *, owner: str | None = None, **_context) -> SemanticType:
        """Convert a composed declarator type."""
        return self._composed_type(type_, owner=owner)

    def _visit_CTypedef(self, type_: CTypedef, *, owner: str | None = None, **_context) -> SemanticType:
        """Resolve and convert a typedef reference."""
        return self._typedef_type(type_, owner=owner)

    def _visit_CEnum(self, type_: CEnum, **_context) -> SemanticType:
        """Convert an enum to its semantic integer representation."""
        return self._enum_type(type_)

    def _visit_CFunctionType(self, type_: CFunctionType, **_context) -> SemanticType:
        """Convert a function type to a callback contract placeholder."""
        return self._callback_placeholder(type_)

    def _visit_CUnknownType(self, type_: CUnknownType, *, owner: str | None = None, **_context) -> SemanticType:
        """Resolve a probed standard typedef or preserve an unknown C spelling."""
        standard = self._standard_semantic_type(type_.spelling)
        if standard is not None:
            return standard
        return self._unresolved_type(type_.spelling, owner=owner, source_type=self._type_text(type_))

    def _visit_CVoid(self, type_: CVoid, **_context) -> SemanticType:
        """Represent void when it is used as a pointer pointee."""
        return SemanticType(
            name="Any",
            dtype="Any",
            metadata={"c_void_pointer_pointee": True},
            origin=self._type_origin(type_),
        )

    def _primitive_type(self, type_: CType, *, owner: str | None) -> SemanticType:
        """Convert one modeled C arithmetic primitive using target ABI facts."""
        semantic_name = self.primitive_type_map.get(type(type_))
        if semantic_name is None:
            return self._unsupported_type(
                "c_unsupported_type",
                "This C type is not supported by the semantic converter.",
                owner=owner,
                source_type=self._type_text(type_),
            )

        origin = self._type_origin(type_)
        metadata: dict[str, Any] = {}
        if isinstance(type_, CChar):
            metadata["c_char_policy"] = "implementation-defined signed 8-bit code unit"
        dtype = semantic_name
        primitive_name = _PRIMITIVE_TYPE_FACT_NAMES.get(type(type_))
        fact = self.standard_type_facts.get(primitive_name) if primitive_name is not None else None
        if fact is not None and fact.get("available", True):
            probed_name = self._semantic_type_from_standard_fact(fact)
            if probed_name is None:
                unsupported = self._unsupported_type(
                    "c_unsupported_primitive_abi",
                    "The selected C target uses a primitive ABI that has no semantic dtype mapping.",
                    owner=owner,
                    source_type=self._type_text(type_),
                )
                unsupported.metadata.update(
                    {
                        "c_primitive": primitive_name,
                        "c_type_fact": dict(fact),
                        "c_type_fact_source": "compiler_probe",
                    }
                )
                return unsupported
            semantic_name = "Int" if isinstance(type_, CInt) and semantic_name == "Int" else probed_name
            dtype = probed_name
            metadata["c_primitive"] = primitive_name
            metadata["c_type_fact"] = dict(fact)
            metadata["c_type_fact_source"] = "compiler_probe"
            if isinstance(type_, CChar):
                signedness = "signed" if fact.get("signed") else "unsigned"
                metadata["c_char_policy"] = f"compiler-probed {signedness} {fact.get('bits')}-bit code unit"
        elif isinstance(type_, CInt) and semantic_name == "Int":
            fact, fact_source = self._c_int_fact()
            dtype = self._semantic_type_from_standard_fact(fact) or "Int"
            metadata["c_primitive"] = "int"
            metadata["c_type_fact"] = fact
            metadata["c_type_fact_source"] = fact_source
        native_cast = self._required_native_scalar_cast(type_, dtype)
        if native_cast is not None:
            metadata[NATIVE_C_SCALAR_CAST_METADATA] = native_cast
        return SemanticType(
            name=semantic_name,
            dtype=dtype,
            metadata=metadata,
            origin=origin,
        )

    def _required_native_scalar_cast(self, type_: CType, semantic_name: str) -> str | None:
        """Return the exact C primitive marker when canonical storage is a distinct C type."""
        if not self.standard_type_facts:
            return None
        primitive_name = _PRIMITIVE_TYPE_FACT_NAMES.get(type(type_))
        native_cast = _PRIMITIVE_NATIVE_CAST_NAMES.get(type(type_))
        canonical_name = _CANONICAL_C_TYPE_FACT_NAMES.get(semantic_name)
        if primitive_name is None or native_cast is None or canonical_name is None:
            return None
        source_fact = self.standard_type_facts.get(primitive_name)
        canonical_fact = self.standard_type_facts.get(canonical_name)
        if not isinstance(source_fact, dict) or not isinstance(canonical_fact, dict):
            return None
        source_spelling = self._underlying_c_type(primitive_name)
        canonical_spelling = self._underlying_c_type(canonical_name)
        return None if self._compatible_c_scalar_spelling(source_spelling, canonical_spelling) else native_cast

    def _underlying_c_type(self, name: str) -> str:
        fact = self.standard_type_facts.get(name)
        if isinstance(fact, dict):
            underlying = fact.get("underlying_c_type")
            if isinstance(underlying, str) and underlying:
                return underlying
        return name

    @staticmethod
    def _compatible_c_scalar_spelling(left: str, right: str) -> bool:
        """Compare equivalent builtin spellings without collapsing distinct integer types."""
        aliases = {
            "bool": "_Bool",
            "signed": "int",
            "signed int": "int",
            "unsigned": "unsigned int",
            "float complex": "float _Complex",
            "double complex": "double _Complex",
            "long double complex": "long double _Complex",
        }
        return aliases.get(left, left) == aliases.get(right, right)

    def _return_type(self, type_: CType, *, owner: str) -> SemanticType | None:
        """Convert a function result, using ``None`` for by-value C ``void``."""
        if isinstance(type_, CVoid):
            return None
        return self.visit(type_, owner=owner, as_type=True)

    def _composed_type(self, type_: CComposedType, *, owner: str | None) -> SemanticType:
        """Convert declarator composition through array, pointer, and callback stages.

        Leading arrays and pointers are handled before the remaining base type.
        Unsupported mixtures return the existing explicit unsupported semantic
        type rather than selecting a wrapper policy; source text is retained in
        every resulting diagnostic type.
        """
        components = list(type_.components)
        if not components:
            return self._unsupported_type(
                "c_empty_composed_type",
                "C composed type is missing a base type.",
                owner=owner,
                source_type=self._type_text(type_),
            )
        if self._contains_function_type(type_):
            return self._callback_placeholder(type_)

        leading_arrays = self._leading_components(components, CArray)
        if leading_arrays:
            remaining = components[len(leading_arrays) :]
            if self._has_component(remaining[:-1], CPointer):
                return self._unsupported_type(
                    "c_array_of_pointer_unsupported",
                    "C arrays of pointers need explicit semantic policy.",
                    owner=owner,
                    source_type=self._type_text(type_),
                )
            if not remaining:
                return self._unsupported_type(
                    "c_array_missing_element_type",
                    "C array type is missing an element type.",
                    owner=owner,
                    source_type=self._type_text(type_),
                )
            element = self.visit(remaining[-1], owner=owner, as_type=True)
            return self._array_type(element, leading_arrays, source_type=type_, owner=owner)

        leading_pointers = self._leading_components(components, CPointer)
        if leading_pointers:
            remaining = components[len(leading_pointers) :]
            if not remaining:
                return self._unsupported_type(
                    "c_pointer_missing_pointee",
                    "C pointer type is missing a pointee type.",
                    owner=owner,
                    source_type=self._type_text(type_),
                )
            if self._has_component(remaining[:-1], CArray):
                element = self.visit(remaining[-1], owner=owner, as_type=True)
                arrays = [component for component in remaining[:-1] if isinstance(component, CArray)]
                semantic_type = self._array_type(element, arrays, source_type=type_, owner=owner)
                semantic_type.storage = semantic_type.storage or SemanticStorageContract(kind="array")
                semantic_type.storage.pointer_depth = len(leading_pointers)
                semantic_type.storage.metadata["c_pointer_to_array"] = True
                return semantic_type
            if len(remaining) != 1:
                return self._unsupported_type(
                    "c_unsupported_composed_type",
                    "This C pointer composition needs explicit semantic policy.",
                    owner=owner,
                    source_type=self._type_text(type_),
                )
            pointee = self.visit(remaining[0], owner=owner, as_type=True)
            return self._pointer_type(pointee, leading_pointers, pointee_type=remaining[0], source_type=type_)

        if len(components) == 1:
            return self.visit(components[0], owner=owner, as_type=True)
        return self._unsupported_type(
            "c_unsupported_composed_type",
            "This C declarator composition needs explicit semantic policy.",
            owner=owner,
            source_type=self._type_text(type_),
        )

    def _typedef_type(self, typedef: CTypedef, *, owner: str | None) -> SemanticType:
        """Resolve a typedef chain, standard name, or unresolved reference into semantic IR.

        Resolved declarations append their spelling to ``c_typedefs`` metadata.
        Names without a concrete declaration retain the existing unresolved-type
        representation instead of being guessed from the typedef name.
        """
        resolved = self._resolve_typedef(typedef)
        if resolved is not None and resolved is not typedef:
            semantic_type = self.visit(resolved.type or resolved, owner=owner, as_type=True)
            semantic_type.metadata.setdefault("c_typedefs", []).append(typedef.name)
            return semantic_type
        if typedef.type is not None:
            semantic_type = self.visit(typedef.type, owner=owner, as_type=True)
            semantic_type.metadata.setdefault("c_typedefs", []).append(typedef.name)
            return semantic_type

        standard_type = self._standard_semantic_type(typedef.name)
        if standard_type is not None:
            standard_type.metadata.setdefault("c_typedefs", []).append(typedef.name)
            return standard_type

        return self._unresolved_type(
            typedef.name,
            owner=owner,
            source_type=typedef.name,
            code="c_unresolved_typedef",
            message="C typedef references must resolve to a concrete semantic type before wrapping.",
        )

    def _struct_type(self, struct: CStruct, *, owner: str | None) -> SemanticType:
        """Return a named semantic struct reference after consulting the file/project registry."""
        if struct.name and struct.name in self.structs:
            struct = self.structs[struct.name]
        name = self._struct_name(struct)
        return SemanticType(
            name=name,
            dtype=name,
            metadata={"c_kind": "struct", "incomplete": struct.is_incomplete},
            origin=self._type_origin(struct, native_name=struct.reference_name),
        )

    def _union_type(self, union: CUnion, *, owner: str | None) -> SemanticType:
        """Return a named semantic union reference after consulting the file/project registry."""
        if union.name and union.name in self.unions:
            union = self.unions[union.name]
        name = self._union_name(union)
        return SemanticType(
            name=name,
            dtype=name,
            metadata={"c_kind": "union", "incomplete": union.is_incomplete},
            origin=self._type_origin(union, native_name=union.reference_name),
        )

    def _enum_type(self, enum: CEnum) -> SemanticType:
        """Lower an enum reference to its underlying integer type with enum provenance."""
        enum = self._resolved_enum(enum)
        underlying_type = self._enum_underlying_type(enum)
        underlying_type.metadata.update(
            {
                "c_kind": "enum",
                "c_enum": enum.reference_name,
                "c_enum_name": self._enum_name(enum),
                "c_underlying_type": underlying_type.name,
                "c_underlying_dtype": underlying_type.dtype,
            }
        )
        underlying_type.origin = self._type_origin(enum, native_name=enum.reference_name)
        return underlying_type

    def _enum_underlying_type(self, enum: CEnum) -> SemanticType:
        """Return compiler-probed enum storage or the documented C ``int`` assumption."""
        fact = self.standard_type_facts.get(enum.reference_name)
        if fact is not None and fact.get("available", True):
            dtype = self._semantic_type_from_standard_fact(fact) or "Int"
            name = "Int" if fact.get("underlying_c_type") == "int" else dtype
            return SemanticType(
                name=name,
                dtype=dtype,
                metadata={
                    "c_enum": enum.reference_name,
                    "c_enum_type_fact": dict(fact),
                    "c_enum_type_fact_source": "compiler_probe",
                },
            )
        underlying_type = self.visit(CInt(), as_type=True)
        underlying_type.metadata["c_enum"] = enum.reference_name
        underlying_type.metadata["c_enum_underlying_assumption"] = "int"
        return underlying_type

    def _pointer_type(
        self,
        pointee: SemanticType,
        pointer_components: list[CPointer],
        *,
        pointee_type: CType,
        source_type: CType,
    ) -> SemanticType:
        """Apply C pointer depth, qualifiers, and aliasing facts to a pointee type in place.

        The returned object is ``pointee`` with borrowed reference/pointer
        storage.  Pointee ``const`` controls mutability and ``restrict`` controls
        aliasing; no ownership-transfer policy is inferred.
        """
        pointer_depth = len(pointer_components)
        read_only = self._has_qualifier(pointee_type, CConst)
        pointer_qualifiers = [
            [qualifier.spelling for qualifier in pointer.qualifiers] for pointer in pointer_components
        ]
        restrict = any(self._has_qualifier(pointer, CRestrict) for pointer in pointer_components)
        pointee.storage = SemanticStorageContract(
            kind="reference" if pointer_depth == 1 else "pointer",
            read_only=read_only,
            mutable=not read_only,
            pointer_depth=pointer_depth,
            ownership="borrowed",
            metadata={
                "c_pointer_qualifiers": pointer_qualifiers,
                "restrict": restrict,
                "source_type": self._type_text(source_type),
            },
        )
        pointee.ownership.mutable = not read_only
        pointee.ownership.aliasing = not restrict
        return pointee

    def _array_type(
        self,
        element: SemanticType,
        array_components: list[CArray],
        *,
        source_type: CType,
        owner: str | None,
    ) -> SemanticType:
        """Apply C array shape, C-order storage, and element constness to ``element``.

        The supplied element type is mutated with rank, shape, and borrowed
        array storage.  Array-component metadata preserves static, variable,
        and flexible bound facts for later semantic consumers.
        """
        shape = [self._array_bound(component) for component in array_components]
        rank = len(array_components)
        read_only = self._has_qualifier(self._array_element_type(source_type), CConst)
        element.rank = rank
        element.shape = list(shape)
        element.storage = SemanticStorageContract(
            kind="array",
            read_only=read_only,
            mutable=not read_only,
            pointer_depth=1,
            ownership="borrowed",
            array=SemanticArrayContract(
                rank=rank,
                shape=list(shape),
                source_shape=[component.bound or ":" for component in array_components],
                category="c_array",
                order="ORDER_C" if rank > 1 else None,
                axes=["dense" for _component in array_components],
                contiguous=True,
                metadata={
                    "c_static_minimum": [component.is_static_minimum for component in array_components],
                    "c_variable_length": [component.is_variable_length for component in array_components],
                    "c_flexible": [component.is_flexible for component in array_components],
                },
            ),
            metadata={"source_type": self._type_text(source_type)},
        )
        return element

    # Constant and module metadata helpers

    def _enum_constants_for_enum(self, enum: CEnum) -> list[SemanticVariable]:
        """Convert enum members into ordered constant semantic variables.

        Implicit values continue from a parseable integer predecessor.  Native
        expressions are always preserved, while a Python initializer is stored
        only when the expression is valid and representable in a ``.pyi`` file.
        """
        variables: list[SemanticVariable] = []
        enum = self._resolved_enum(enum)
        next_value: int | None = 0
        for enumerator in enum.constants:
            value = enumerator.value
            if value is None and next_value is not None:
                value = str(next_value)
            literal = self._integer_literal_value(value)
            next_value = literal + 1 if literal is not None else None
            semantic_type = self._enum_type(enum)
            semantic_type.constraints.append(SemanticConstraint("Constant"))
            semantic_type.metadata["enum_name"] = self._enum_name(enum)
            semantic_type.origin = SemanticOrigin(
                source_language="c",
                native_name=enumerator.name,
                native_scope=enum.reference_name,
                source_kind="enum_constant",
                source_type="enum",
                source_location=self._location_dict(enumerator.source_location),
            )
            metadata: dict[str, Any] = {}
            if value is not None:
                metadata["c_value_expression"] = value
            pyi_value = self._pyi_integer_expression(value)
            if pyi_value is not None:
                metadata["pyi_default_value"] = pyi_value
            variables.append(
                SemanticVariable(
                    name=enumerator.name,
                    semantic_type=semantic_type,
                    default_value=value,
                    metadata=metadata,
                    origin=SemanticOrigin(
                        source_language="c",
                        native_name=enumerator.name,
                        native_scope=enum.reference_name,
                        source_kind="enum_constant",
                        source_location=self._location_dict(enumerator.source_location),
                    ),
                )
            )
        return variables

    def _macro_constants(self, c_file: CFile) -> list[SemanticVariable]:
        """Convert eligible object-like macros declared by one translation unit."""
        return self._macro_constants_from_macros(c_file.macros)

    def _macro_constants_from_macros(self, macros: list[CMacro]) -> list[SemanticVariable]:
        """Resolve numeric object-like macros into ordered constant semantic variables.

        The first pass iterates to a fixed point so macros can refer to earlier
        or later resolvable macro names.  Function-like and nonnumeric macros
        are intentionally excluded from the semantic module.
        """
        macro_types: dict[str, str] = {}
        pending = [macro for macro in macros if not macro.function_like and macro.value is not None]
        changed = True
        while changed:
            changed = False
            for macro in pending:
                if macro.name in macro_types or macro.value is None:
                    continue
                value = macro.value.strip()
                if _INTEGER_LITERAL_RE.fullmatch(value):
                    macro_types[macro.name] = "Int32"
                    changed = True
                elif _FLOAT_LITERAL_RE.fullmatch(value):
                    macro_types[macro.name] = "Float64"
                    changed = True
                elif self._integer_macro_expression(value, macro_types):
                    macro_types[macro.name] = "Int32"
                    changed = True

        variables: list[SemanticVariable] = []
        for macro in macros:
            semantic_name = macro_types.get(macro.name)
            if semantic_name is None or macro.value is None:
                continue
            value = macro.value.strip()
            variables.append(
                SemanticVariable(
                    name=macro.name,
                    semantic_type=SemanticType(
                        name=semantic_name,
                        dtype=semantic_name,
                        constraints=[SemanticConstraint("Constant")],
                    ),
                    default_value=value,
                    origin=SemanticOrigin(
                        source_language="c",
                        native_name=macro.name,
                        source_kind="macro",
                        source_location=self._location_dict(macro.source_location),
                    ),
                )
            )
        return variables

    @staticmethod
    def _integer_macro_expression(value: str, macro_types: dict[str, str]) -> bool:
        """Return whether a macro expression is limited to known integer syntax and names."""
        if not _INTEGER_EXPRESSION_CHARS_RE.fullmatch(value):
            return False
        identifiers = set(_C_IDENTIFIER_TOKEN_RE.findall(value))
        if any(macro_types.get(identifier) != "Int32" for identifier in identifiers):
            return False
        normalized = _C_INTEGER_LITERAL_SUFFIX_RE.sub(r"\1", value)
        normalized = _C_IDENTIFIER_TOKEN_RE.sub("1", normalized)
        try:
            expression = ast.parse(normalized, mode="eval")
        except SyntaxError:
            return False
        return all(
            isinstance(node, _INTEGER_EXPRESSION_AST_NODES)
            and not (isinstance(node, ast.Constant) and not isinstance(node.value, int))
            for node in ast.walk(expression)
        )

    @staticmethod
    def _pyi_integer_expression(value: str | None) -> str | None:
        """Return a Python-valid integer expression for a native macro value, if safe."""
        if value is None or not _INTEGER_EXPRESSION_CHARS_RE.fullmatch(value):
            return None
        normalized = _C_INTEGER_LITERAL_SUFFIX_RE.sub(r"\1", value)
        normalized = _C_OCTAL_LITERAL_RE.sub(r"0o\1", normalized)
        try:
            expression = ast.parse(normalized, mode="eval")
        except SyntaxError:
            return None
        if not all(
            isinstance(node, (*_INTEGER_EXPRESSION_AST_NODES, ast.Name, ast.Load))
            and not (isinstance(node, ast.Constant) and not isinstance(node.value, int))
            for node in ast.walk(expression)
        ):
            return None
        return ast.unparse(expression.body)

    def _file_metadata(self, c_file: CFile) -> dict[str, Any]:
        """Return the stable summary metadata attached to one semantic C module."""
        metadata: dict[str, Any] = {
            "source_language": "c",
            "counts": {
                "functions": len(c_file.functions),
                "structs": len(c_file.structs),
                "unions": len(c_file.unions),
                "enums": len(c_file.enums),
                "typedefs": len(c_file.typedefs),
                "macros": len(c_file.macros),
                "includes": len(c_file.includes),
                "diagnostics": len(c_file.diagnostics),
            },
            "preprocessing": c_file.preprocessing,
        }
        return metadata

    @staticmethod
    def _private_recipe_paths(c_file: CFile) -> set[str]:
        """Extract preprocessing-recipe include paths marked private to the source unit."""
        recipe = c_file.preprocessing_recipe or {}
        private_paths: set[str] = set()
        for item in recipe.get("included_files") or []:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if isinstance(path, str) and item.get("exposure") == "private":
                private_paths.add(path)
        return private_paths

    @staticmethod
    def _source_filename(location: dict[str, Any] | None) -> str | None:
        """Read a string filename from serialized source-location metadata."""
        if not isinstance(location, dict):
            return None
        filename = location.get("filename")
        return filename if isinstance(filename, str) else None

    # Include exposure and cross-module aggregate identity

    def _apply_include_exposure(self, module: SemanticModule, c_file: CFile) -> None:
        """Apply private-include visibility to module declarations in place.

        Functions and variables from private included files become private.
        Private classes become opaque with their fields removed, preserving an
        addressable dependency identity without exposing private layout.
        """
        private_paths = self._private_recipe_paths(c_file)
        if not private_paths:
            return

        def is_private_origin(origin: SemanticOrigin) -> bool:
            """Return whether an origin filename appears in this file's private include set."""
            filename = self._source_filename(origin.source_location)
            return filename in private_paths

        for function in module.functions:
            if is_private_origin(function.origin):
                function.visibility = "private"
        for variable in module.variables:
            if is_private_origin(variable.origin):
                variable.visibility = "private"
        for cls in module.classes:
            if not isinstance(cls, SemanticClass):
                continue
            if is_private_origin(cls.origin):
                cls.visibility = "private"
                cls.fields = []
                if "Opaque" not in cls.base_classes:
                    cls.base_classes.append("Opaque")

    def _externalize_private_classes(self, module: SemanticModule) -> None:
        """Mark references to foreign private opaque classes as external in place.

        Only opaque private classes whose source filename maps to another module
        are tracked.  The existing type walk then gives consumers an external
        reference instead of retaining a local duplicate definition.
        """
        external_classes: dict[str, str] = {}
        for cls in module.classes:
            if not isinstance(cls, SemanticClass):
                continue
            if cls.visibility != "private" or "Opaque" not in cls.base_classes:
                continue
            filename = self._source_filename(cls.origin.source_location)
            if filename is None:
                continue
            origin_module = self._module_name_for_filename(filename)
            if origin_module != module.name:
                external_classes[cls.name] = origin_module
        if not external_classes:
            return

        for semantic_type in _module_semantic_types(module):
            origin_module = external_classes.get(semantic_type.name)
            if origin_module is None:
                continue
            self._set_external_type_ref(
                semantic_type,
                origin_module=origin_module,
                wrapped=False,
            )
        module.classes = [cls for cls in module.classes if cls.name not in external_classes]

    def _classify_project_external_types(
        self,
        modules: list[SemanticModule],
        project: CProject,
    ) -> None:
        """Attach owner-module metadata to aggregate references outside their defining file.

        Struct ownership is derived from source locations in the project
        registry.  The method mutates consumer type metadata and removes their
        duplicate class declarations while leaving each owner module unchanged.
        """
        modules_by_filename = {
            module.origin.native_name: module for module in modules if module.origin.native_name is not None
        }
        owners: dict[str, tuple[str, bool]] = {}
        for struct in project.structs.values():
            if struct.name is None or struct.source_location is None:
                continue
            owner = modules_by_filename.get(struct.source_location.filename)
            if owner is None:
                continue
            owners[self._identifier(struct.name)] = (owner.name, not struct.is_incomplete)
        for module in modules:
            external_names = {
                name for name, (origin_module, _wrapped) in owners.items() if origin_module != module.name
            }
            if not external_names:
                continue
            for semantic_type in _module_semantic_types(module):
                owner = owners.get(semantic_type.name)
                if owner is None or owner[0] == module.name:
                    continue
                self._set_external_type_ref(
                    semantic_type,
                    origin_module=owner[0],
                    wrapped=owner[1],
                )
            module.classes = [cls for cls in module.classes if cls.name not in external_names]

    @staticmethod
    def _set_external_type_ref(
        semantic_type: SemanticType,
        *,
        origin_module: str,
        wrapped: bool,
    ) -> None:
        """Store the canonical wrapped/opaque external-type reference metadata in place."""
        semantic_type.metadata[EXTERNAL_TYPE_REF_METADATA] = {
            "name": semantic_type.name,
            "local_name": semantic_type.name,
            "origin_module": origin_module,
            "wrapped": wrapped,
            "representation": "wrapped" if wrapped else "opaque",
        }

    def _project_metadata(self, project: CProject) -> dict[str, Any]:
        """Return stable language and aggregate-count metadata for a merged project module."""
        metadata: dict[str, Any] = {
            "source_language": "c",
            "counts": {
                "files": len(project.files),
                "functions": len(project.functions),
                "structs": len(project.structs),
                "unions": len(project.unions),
                "enums": len(self._project_enum_declarations(project)),
                "typedefs": len(project.typedefs),
                "macros": len(project.macros),
                "includes": len(project.includes),
                "diagnostics": len(project.diagnostics),
            },
        }
        return metadata

    # Type lookup, target facts, and naming helpers

    def _resolve_typedef(self, typedef: CTypedef, stack: tuple[str, ...] = ()) -> CTypedef | None:
        """Resolve typedef aliases through the current registry without following cycles.

        ``stack`` records names already visited.  A cycle, missing entry, or
        non-typedef target returns ``None`` so callers preserve the existing
        unresolved-type semantic representation.
        """
        if typedef.type is not None:
            return typedef
        target = self.typedefs.get(typedef.name)
        if target is None or target.name in stack:
            return None
        if target.type is None:
            return self._resolve_typedef(target, (*stack, target.name))
        return target

    def _standard_semantic_type(self, name: str) -> SemanticType | None:
        """Return a probe-aware semantic type for a recognized standard C typedef name.

        Referenced opaque handles are recorded so the enclosing module can emit
        a matching opaque class; unknown names return ``None`` for the typedef
        caller's ordinary unresolved-type path.
        """
        fact = self.standard_type_facts.get(name)
        if fact is not None:
            if fact.get("available", True) and fact.get("kind") == "opaque_handle":
                semantic_name = self._identifier(name)
                self.opaque_standard_types.add(semantic_name)
                return SemanticType(
                    name=semantic_name,
                    dtype=semantic_name,
                    metadata={"c_standard_type": name, "c_standard_type_fact": dict(fact), "c_opaque_handle": True},
                )
            semantic_name = self._semantic_type_from_standard_fact(fact)
            if semantic_name is not None:
                return SemanticType(
                    name=semantic_name,
                    dtype=semantic_name,
                    metadata={"c_standard_type": name, "c_standard_type_fact": dict(fact)},
                )
        fallback = _STANDARD_TYPE_FALLBACKS.get(name)
        if fallback is None:
            return None
        return SemanticType(
            name=fallback,
            dtype=fallback,
            metadata={"c_standard_type": name, "c_standard_type_fallback": True},
        )

    def _c_int_fact(self) -> tuple[dict[str, Any], str]:
        """Return the configured C ``int`` fact or the historical fallback and provenance."""
        fact = self.standard_type_facts.get("int")
        if fact is not None and fact.get("available", True):
            return dict(fact), "compiler_probe"
        return dict(_C_INT_FALLBACK_FACT), "fallback"

    def _opaque_standard_type_classes(self) -> list[SemanticClass]:
        """Create deterministic opaque classes for referenced standard handle types."""
        return [
            SemanticClass(
                name=name,
                native_name=name,
                base_classes=["Opaque"],
                metadata={"c_kind": "opaque_standard_type"},
                origin=SemanticOrigin(
                    source_language="c",
                    native_name=name,
                    source_kind="standard_type",
                    source_type=name,
                ),
            )
            for name in sorted(self.opaque_standard_types)
        ]

    @staticmethod
    def _semantic_type_from_standard_fact(fact: dict[str, Any]) -> str | None:
        """Map one available compiler-reported standard type fact to a known semantic dtype."""
        if not fact.get("available", True):
            return None
        if fact.get("kind") == "opaque_handle":
            return None
        bits = int(fact.get("bits") or 0)
        if fact.get("kind") == "integer":
            if fact.get("signed") is False:
                return _UNSIGNED_WIDTH_TYPES.get(bits)
            if fact.get("signed") is True:
                return _SIGNED_WIDTH_TYPES.get(bits)
        if fact.get("kind") == "bool":
            return next(
                (
                    name
                    for name, storage_bits in BOOLEAN_STORAGE_BITS.items()
                    if name != "Bool" and storage_bits == bits
                ),
                None,
            )
        if fact.get("kind") == "real":
            return _REAL_WIDTH_TYPES.get(bits)
        if fact.get("kind") == "complex":
            return _COMPLEX_WIDTH_TYPES.get(bits)
        return None

    @staticmethod
    def _standard_type_facts(report: Any | None) -> dict[str, dict[str, Any]]:
        """Normalize a probe report or mapping into copied per-standard-type facts.

        Missing or malformed reports produce an empty lookup.  Fact dictionaries
        are copied so caller-owned reports cannot be mutated during conversion.
        """
        if report is None:
            return {}
        if hasattr(report, "types"):
            types = report.types
        elif isinstance(report, dict) and isinstance(report.get("types"), dict):
            types = report["types"]
        elif isinstance(report, dict):
            types = report
        else:
            return {}
        return {str(name): dict(fact) for name, fact in types.items() if isinstance(fact, dict)}

    def _unresolved_type(
        self,
        name: str,
        *,
        owner: str | None,
        source_type: str,
        code: str = "c_unresolved_type",
        message: str = "C type references must resolve before wrapping.",
    ) -> SemanticType:
        """Represent an unresolved C spelling without fabricating a semantic mapping.

        ``code``, ``message``, and ``owner`` are accepted for callers' stable
        diagnostics but intentionally do not alter this historical IR shape.
        """
        return SemanticType(
            name=name,
            dtype=name,
            metadata={},
            origin=SemanticOrigin(source_language="c", source_kind="type", source_type=source_type),
        )

    def _unsupported_type(
        self,
        code: str,
        message: str,
        *,
        owner: str | None,
        source_type: str,
    ) -> SemanticType:
        """Return the existing explicit placeholder for unsupported C composition.

        Diagnostic context parameters are deliberately not serialized here; the
        resulting origin retains the native source spelling for later reporting.
        """
        return SemanticType(
            name="CUnsupported",
            dtype="CUnsupported",
            metadata={},
            origin=SemanticOrigin(source_language="c", source_kind="unsupported_type", source_type=source_type),
        )

    def _callback_placeholder(self, type_: CType) -> SemanticType:
        """Return the function-pointer semantic placeholder with source-type provenance."""
        return SemanticType(
            name="CFunctionPointer",
            dtype="CFunctionPointer",
            metadata={"source_type": self._type_text(type_)},
            origin=SemanticOrigin(
                source_language="c",
                source_kind="function_pointer",
                source_type=self._type_text(type_),
            ),
        )

    @staticmethod
    def _module_name(c_file: CFile) -> str:
        """Derive the stable semantic module name for a translation unit or unnamed fallback."""
        if c_file.filename:
            return CToIRConverter._module_name_for_filename(c_file.filename)
        stem = "c_module"
        return CToIRConverter._identifier(stem or "c_module")

    @staticmethod
    def _module_name_for_filename(filename: str) -> str:
        """Normalize a source filename stem into a valid semantic module identifier."""
        return CToIRConverter._identifier(Path(filename).stem or "c_module")

    @staticmethod
    def _identifier(name: str) -> str:
        """Convert arbitrary native text into the stable nonempty semantic identifier form."""
        text = _IDENTIFIER_RE.sub("_", str(name)).strip("_")
        if not text:
            text = "anonymous"
        if text[:1].isdigit():
            text = f"_{text}"
        return text

    def _struct_name(self, struct: CStruct) -> str:
        """Choose a struct's explicit name, typedef alias, or anonymous fallback spelling."""
        if struct.name:
            return self._identifier(struct.name)
        alias = self._typedef_alias_for_type(struct)
        return self._identifier(alias or struct.anonymous_id or "anonymous_struct")

    def _union_name(self, union: CUnion) -> str:
        """Choose a union's explicit name, typedef alias, or anonymous fallback spelling."""
        if union.name:
            return self._identifier(union.name)
        alias = self._typedef_alias_for_type(union)
        return self._identifier(alias or union.anonymous_id or "anonymous_union")

    def _enum_name(self, enum: CEnum) -> str:
        """Choose an enum's explicit name, typedef alias, or anonymous fallback spelling."""
        if enum.name:
            return self._identifier(enum.name)
        alias = self._typedef_alias_for_type(enum)
        return self._identifier(alias or enum.anonymous_id or "anonymous_enum")

    def _nested_aggregate_name(self, field_name: str, used_names: set[str]) -> str:
        """Return a deterministic unused semantic class name for one nested aggregate field."""
        base = self._identifier(field_name)
        candidate = self._identifier(f"{base}_type")
        index = 1
        while candidate in used_names:
            candidate = self._identifier(f"{base}_type_{index}")
            index += 1
        return candidate

    def _resolved_enum(self, enum: CEnum) -> CEnum:
        """Return the registry definition for a named enum when one is available."""
        if enum.name and enum.name in self.enums:
            return self.enums[enum.name]
        return enum

    @staticmethod
    def _project_enum_declarations(project: CProject) -> list[CEnum]:
        """Return project enums once, including anonymous declarations stored only on files."""
        declarations = list(project.enums.values())
        anonymous_ids: set[str | int] = {enum.anonymous_id or id(enum) for enum in declarations if enum.name is None}
        for c_file in project.files.values():
            for enum in c_file.enums:
                if enum.name is not None:
                    continue
                identity: str | int = enum.anonymous_id or id(enum)
                if identity in anonymous_ids:
                    continue
                anonymous_ids.add(identity)
                declarations.append(enum)
        return declarations

    def _typedef_alias_for_type(self, target: CType) -> str | None:
        """Find the first registry typedef whose target is the same parser type object."""
        for typedef in self.typedefs.values():
            if typedef.type is target:
                return typedef.name
        return None

    @staticmethod
    def _leading_components(components: list[CType], cls: type) -> list:
        """Return the consecutive leading declarator components of ``cls`` from ``components``."""
        out = []
        for component in components:
            if not isinstance(component, cls):
                break
            out.append(component)
        return out

    @staticmethod
    def _has_component(components: list[CType], cls: type) -> bool:
        """Return whether any declarator component is an instance of ``cls``."""
        return any(isinstance(component, cls) for component in components)

    @staticmethod
    def _contains_function_type(type_: CComposedType) -> bool:
        """Return whether a composed declarator contains a C function type component."""
        return any(isinstance(component, CFunctionType) for component in type_.components)

    @staticmethod
    def _array_bound(array: CArray) -> str:
        """Return an array bound or the established ``:`` marker for an omitted bound."""
        if array.bound:
            return array.bound
        return ":"

    @staticmethod
    def _array_element_type(source_type: CType) -> CType:
        """Return the innermost parser type used to determine array element qualifiers."""
        if isinstance(source_type, CComposedType) and source_type.components:
            return source_type.components[-1]
        return source_type

    @staticmethod
    def _has_qualifier(type_: CType, qualifier_type: type[CQualifier]) -> bool:
        """Return whether a parsed type directly declares ``qualifier_type``."""
        return any(isinstance(qualifier, qualifier_type) for qualifier in getattr(type_, "qualifiers", []))

    @staticmethod
    def _integer_literal_value(value: str | None) -> int | None:
        """Parse one C integer literal with suffixes, returning ``None`` for expressions."""
        if value is None:
            return None
        cleaned = re.sub(r"[uUlL]+\Z", "", value.strip())
        try:
            return int(cleaned, 0)
        except ValueError:
            return None

    @staticmethod
    def _type_text(type_: CType) -> str:
        """Return preserved source spelling when available, otherwise a stable model spelling."""
        source_text = getattr(type_, "source_text", "")
        if source_text:
            return source_text
        if isinstance(type_, CStruct | CUnion | CEnum | CTypedef):
            return type_.reference_name
        return type(type_).__name__

    @classmethod
    def _c_abi_type_facts(cls, type_: CType, *, name: str | None = None) -> dict[str, object]:
        """Return the exact source facts needed by direct-C policy.

        A declaration name is removed only from the final declarator position;
        the preserved spelling retains all qualifiers, pointer levels, and C
        complex/typedef spelling.  Arrays and function pointers stay marked as
        source facts so policy can reject them without lowering a partial ABI.
        """
        source_spelling = cls._type_text(type_)
        if name:
            source_spelling = re.sub(
                rf"\b{re.escape(name)}\b(?=\s*(?:\[[^]]*\]\s*)*$)",
                "",
                source_spelling,
            ).strip()
        components = list(type_.components) if isinstance(type_, CComposedType) else [type_]
        pointer_components = [component for component in components if isinstance(component, CPointer)]
        qualifiers = tuple(
            qualifier.spelling for component in components for qualifier in getattr(component, "qualifiers", ())
        )
        return {
            "source_spelling": source_spelling,
            "pointer_depth": len(pointer_components),
            "qualifiers": qualifiers,
            "const": "const" in qualifiers,
            "has_array_declarator": any(isinstance(component, CArray) for component in components),
            "has_function_pointer": any(isinstance(component, CFunctionType) for component in components),
        }

    @staticmethod
    def _type_metadata(type_: CType) -> dict[str, Any]:
        """Return parser model kind and direct qualifier facts for a semantic type origin."""
        qualifiers = [qualifier.spelling for qualifier in getattr(type_, "qualifiers", [])]
        metadata: dict[str, Any] = {"c_type": type(type_).__name__}
        if qualifiers:
            metadata["qualifiers"] = qualifiers
        return metadata

    @staticmethod
    def _type_origin(type_: CType, *, native_name: str | None = None) -> SemanticOrigin:
        """Build C type provenance with an optional native declaration name."""
        return SemanticOrigin(
            source_language="c",
            native_name=native_name,
            source_kind="type",
            source_type=CToIRConverter._type_text(type_),
            metadata=CToIRConverter._type_metadata(type_),
        )

    @staticmethod
    def _location_dict(location) -> dict[str, Any]:
        """Serialize the populated fields of a parser source location, or return an empty mapping."""
        if location is None:
            return {}
        return {
            key: value
            for key, value in {
                "filename": location.filename,
                "line": location.line,
                "column": location.column,
                "source_line": location.source_line,
            }.items()
            if value is not None
        }


def c_type_to_semantic_type(
    type_: CType,
    *,
    standard_type_report: Any | None = None,
) -> SemanticType:
    """Convert one parsed C type into its language-neutral semantic type.

    Use this for type-only inspection or when constructing a semantic binding
    yourself.  Supply a standard-type probe report when target ABI widths must
    replace the documented fallback mapping.

    Example:
        >>> c_type_to_semantic_type(CInt()).name
        'Int'
    """
    return CToIRConverter(standard_type_report=standard_type_report).visit(type_, as_type=True)


def c_parameter_to_semantic_argument(
    parameter: CParameter,
    *,
    position: int = 0,
    standard_type_report: Any | None = None,
) -> SemanticArgument:
    """Convert one parsed C parameter into a semantic argument.

    ``position`` becomes the native argument index and determines the stable
    fallback name for an anonymous parameter.  Target type facts are consumed
    the same way as in function and file conversion.
    """
    return CToIRConverter(standard_type_report=standard_type_report).visit(
        parameter,
        position=position,
    )


def c_function_to_semantic_function(
    function: CFunction,
    *,
    standard_type_report: Any | None = None,
) -> SemanticFunction:
    """Convert one parsed C function declaration into a semantic callable contract.

    The result keeps native parameter order, C storage/specifier facts, return
    type, projection, and source provenance.  Use file conversion when related
    typedefs, aggregates, enums, or macros must also be resolved.
    """
    return CToIRConverter(standard_type_report=standard_type_report).visit(function)


def c_struct_to_semantic_class(
    struct: CStruct,
    *,
    standard_type_report: Any | None = None,
) -> SemanticClass:
    """Convert one parsed C struct into a semantic class with fields and nested aggregates.

    Use this for a self-contained struct model.  File/project conversion is
    preferable when a named struct reference must resolve through shared parser
    registries or be classified as externally owned.
    """
    return CToIRConverter(standard_type_report=standard_type_report).visit(struct)


def c_file_to_semantic_module(
    parsed_file: CFile,
    *,
    standard_type_report: Any | None = None,
) -> SemanticModule:
    """Convert one parsed C translation unit into its semantic module.

    Use this normal C source-to-IR entrypoint after parsing.  It converts
    declarations and constants, resolves local parser registries, and applies
    preprocessing include exposure; it does not run probes or policy completion.

    Example:
        >>> parsed = CFile(filename="math.h", functions=[CFunction(name="add", result_type=CInt())])
        >>> c_file_to_semantic_module(parsed).name
        'math'
    """
    return CToIRConverter(standard_type_report=standard_type_report).visit(parsed_file)


def c_file_to_semantic_modules(
    parsed_file: CFile,
    *,
    standard_type_report: Any | None = None,
) -> list[SemanticModule]:
    """Return the one semantic module produced by a single parsed C file.

    This list-returning compatibility helper is useful to generic source
    pipelines that always consume module lists.  It preserves the same result
    and target-fact behavior as :func:`c_file_to_semantic_module`.
    """
    return [c_file_to_semantic_module(parsed_file, standard_type_report=standard_type_report)]


def c_project_to_semantic_modules(
    project: CProject,
    *,
    standard_type_report: Any | None = None,
) -> list[SemanticModule]:
    """Convert every parsed C project file into an ordered semantic module list.

    Use this for multi-header input, where type ownership must be assigned to
    defining modules and consumer modules retain external references.  Project
    files are emitted in stable filename order.

    Example:
        >>> project = CProject(files={"math.h": CFile(filename="math.h")})
        >>> [module.name for module in c_project_to_semantic_modules(project)]
        ['math']
    """
    return CToIRConverter(standard_type_report=standard_type_report).visit(project)


def select_c_export_functions(
    modules: Iterable[SemanticModule],
    symbols: Iterable[str],
) -> list[SemanticModule]:
    """Restrict C semantic IR to an exact, fail-closed function allowlist.

    The selection happens after ordinary include exposure has recorded source
    provenance and before policy completion. Selected functions receive one
    explicit-export marker so a declaration from an included system header is
    intentionally treated as part of the wrapped translation unit. Every
    other declaration category is removed from the selected semantic surface.
    """
    selected_modules = list(modules)
    requested = _validated_c_export_symbols(symbols)
    functions_by_symbol, non_function_symbols = _c_export_candidates(selected_modules)
    _validate_c_export_resolution(requested, functions_by_symbol, non_function_symbols)
    selected = set(requested)
    for module in selected_modules:
        _apply_c_export_selection(module, selected)
    return selected_modules


def _validated_c_export_symbols(symbols: Iterable[str]) -> tuple[str, ...]:
    """Return unique C identifiers or raise one request-level diagnostic."""
    requested = tuple(symbols)
    if not requested:
        raise ValueError("C export-symbol selection requires at least one function name")
    invalid = [symbol for symbol in requested if _C_EXPORT_IDENTIFIER_RE.fullmatch(symbol) is None]
    seen: set[str] = set()
    repeated = []
    for symbol in requested:
        if symbol in seen and symbol not in repeated:
            repeated.append(symbol)
        seen.add(symbol)
    problems = tuple(
        problem
        for problem in (
            _c_export_problem("invalid C identifiers", invalid),
            _c_export_problem("repeated names", repeated),
        )
        if problem is not None
    )
    if problems:
        raise ValueError("C export-symbol selection failed: " + "; ".join(problems))
    return requested


def _c_export_problem(label: str, names: Iterable[str]) -> str | None:
    """Format one populated export-selection problem category."""
    values = tuple(names)
    return f"{label}: {', '.join(values)}" if values else None


def _c_export_candidates(
    modules: Iterable[SemanticModule],
) -> tuple[dict[str, list[SemanticFunction]], set[str]]:
    """Index reachable functions and names from all other declaration kinds."""
    functions_by_symbol: dict[str, list[SemanticFunction]] = {}
    non_function_symbols: set[str] = set()
    for module in modules:
        for function in module.functions:
            symbol = _c_function_symbol(function)
            functions_by_symbol.setdefault(symbol, []).append(function)
        for declaration in (*module.variables, *module.classes, *module.prototypes, *module.overload_sets):
            if symbol := _c_non_function_symbol(declaration):
                non_function_symbols.add(symbol)
    return functions_by_symbol, non_function_symbols


def _c_function_symbol(function: SemanticFunction) -> str:
    """Return the exact native lookup key for one C semantic function."""
    return str(function.origin.native_name or function.native_name or function.name)


def _c_non_function_symbol(declaration: object) -> str | None:
    """Return one non-function declaration name when it has one."""
    name = getattr(declaration, "name", None)
    origin = getattr(declaration, "origin", None)
    native_name = getattr(origin, "native_name", None)
    return str(native_name or name) if native_name or name else None


def _validate_c_export_resolution(
    requested: tuple[str, ...],
    functions_by_symbol: dict[str, list[SemanticFunction]],
    non_function_symbols: set[str],
) -> None:
    """Fail unless every requested name identifies exactly one function."""
    missing = [
        symbol for symbol in requested if symbol not in functions_by_symbol and symbol not in non_function_symbols
    ]
    non_functions = [
        symbol for symbol in requested if symbol not in functions_by_symbol and symbol in non_function_symbols
    ]
    ambiguous = [symbol for symbol in requested if len(functions_by_symbol.get(symbol, ())) > 1]
    problems = tuple(
        problem
        for problem in (
            _c_export_problem("unknown names", missing),
            _c_export_problem("non-function names", non_functions),
            _c_export_problem("ambiguous function names", ambiguous),
        )
        if problem is not None
    )
    if problems:
        raise ValueError("C export-symbol selection failed: " + "; ".join(problems))


def _apply_c_export_selection(module: SemanticModule, selected: set[str]) -> None:
    """Promote selected functions and clear every other declaration category."""
    module.functions = [function for function in module.functions if _c_function_symbol(function) in selected]
    for function in module.functions:
        function.visibility = "public"
        function.metadata[EXPLICIT_C_EXPORT_METADATA] = True
    module.prototypes = []
    module.overload_sets = []
    module.classes = []
    module.variables = []


def c_project_to_semantic_module(
    project: CProject,
    *,
    name: str = "c_project",
    standard_type_report: Any | None = None,
) -> SemanticModule:
    """Merge project registries into one synthetic semantic module.

    Use this compatibility entrypoint when consumers require one aggregate
    module rather than file-level ownership and external references.  ``name``
    is normalized into a semantic identifier; the project itself is not mutated.
    """
    return CToIRConverter(standard_type_report=standard_type_report).project_to_semantic_module(
        project,
        name=name,
    )


__all__ = (
    "CToIRConverter",
    "c_file_to_semantic_module",
    "c_file_to_semantic_modules",
    "c_function_to_semantic_function",
    "c_parameter_to_semantic_argument",
    "c_project_to_semantic_module",
    "c_project_to_semantic_modules",
    "c_struct_to_semantic_class",
    "c_type_to_semantic_type",
    "select_c_export_functions",
)


if __name__ == "__main__":
    from prik.parsers.c.models import CFile, CFunction, CInt, CParameter

    parsed_file = CFile(
        filename="math.h",
        functions=[
            CFunction(
                name="scale",
                result_type=CInt(),
                parameters=[CParameter(name="value", type=CInt())],
            )
        ],
    )
    semantic_module = c_file_to_semantic_module(parsed_file)
    semantic_function = semantic_module.functions[0]
    semantic_argument = semantic_function.arguments[0]
    print(
        f"{semantic_module.name}.{semantic_function.name}"
        f"({semantic_argument.name}): {semantic_function.return_type.name}"
        f" <- {semantic_argument.semantic_type.name}"
    )
