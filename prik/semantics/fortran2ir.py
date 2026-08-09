"""Convert parsed Fortran facts into language-neutral semantic IR.

The public helpers at the end of this module accept parsed Fortran module,
file, or project models and return :class:`~prik.semantics.models.SemanticModule`
objects.  They normalize types, storage, visibility, imported derived types,
and procedure projections.  Ownership and wrapper-generation policy are
deliberately completed by later semantic stages.
"""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
import re
from pathlib import Path

from prik.parsers.fortran.models import (
    FortranArgument,
    FortranBlockData,
    FortranDerivedType,
    FortranEnum,
    FortranEnumerator,
    FortranFile,
    FortranModule,
    FortranProject,
    FortranProgram,
    FortranProcedureSignature,
    FortranSubmodule,
    FortranUseMapping,
    FortranVariable,
)
from prik.utilities.declaration_expressions import (
    ArrayExpressionSource,
    canonicalize_declaration_extent,
    declaration_expression_calls,
    fortran_extent_to_python,
    is_declaration_expression_helper,
    split_dimension_bounds,
    split_top_level_expression,
)
from prik.semantics.ownership import set_ownership_metadata
from prik.semantics.metadata import BIND_TARGET_METADATA, PROJECTED_OUTPUT_METADATA, SCALAR_STORAGE_CATEGORY
from prik.types.numpy import BOOLEAN_STORAGE_BITS, SEMANTIC_SCALAR_TYPE_NAMES, is_boolean_semantic_type_name
from prik.utilities.visitor import ClassVisitor

from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    FORTRAN_GENERIC_NAME_METADATA,
    OVERLOAD_KIND_METADATA,
    OVERLOAD_TARGET_METADATA,
    NATIVE_BY_VALUE_METADATA,
    PYTHON_BOUND_POSITION_METADATA,
    PYTHON_METHOD_NAME_METADATA,
    PYTHON_STATIC_METADATA,
    PROTOTYPE_INTENT_METADATA,
    PROTOTYPE_REF_METADATA,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticExpressionCallable,
    SemanticField,
    SemanticFunction,
    SemanticImport,
    SemanticImportItem,
    SemanticMethod,
    SemanticModule,
    SemanticOrigin,
    SemanticPrototype,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
    ProjectionMapping,
    ProcedureOverloadSet,
)


_BINARY_OPERATOR_METHODS = {
    "+": ("__add__", "__radd__"),
    "-": ("__sub__", "__rsub__"),
    "*": ("__mul__", "__rmul__"),
    "/": ("__truediv__", "__rtruediv__"),
    "**": ("__pow__", "__rpow__"),
    ".and.": ("__and__", "__rand__"),
    ".or.": ("__or__", "__ror__"),
}
_UNARY_OPERATOR_METHODS = {
    "+": "__pos__",
    "-": "__neg__",
    ".not.": "__invert__",
}
_COMPARISON_OPERATOR_METHODS = {
    "==": ("__eq__", "__eq__"),
    "/=": ("__ne__", "__ne__"),
    "<": ("__lt__", "__gt__"),
    "<=": ("__le__", "__ge__"),
    ">": ("__gt__", "__lt__"),
    ">=": ("__ge__", "__le__"),
    ".eqv.": ("__eq__", "__eq__"),
    ".neqv.": ("__ne__", "__ne__"),
}


FORTRAN_TYPE_MAP = {
    ("integer", None): "Int32",
    ("integer", "1"): "Int8",
    ("integer", "2"): "Int16",
    ("integer", "4"): "Int32",
    ("integer", "8"): "Int64",
    ("integer", "int8"): "Int8",
    ("integer", "int16"): "Int16",
    ("integer", "int32"): "Int32",
    ("integer", "int64"): "Int64",
    ("integer", "c_signed_char"): "Int8",
    ("integer", "c_short"): "Int16",
    ("integer", "c_int"): "Int32",
    ("integer", "c_long_long"): "Int64",
    ("integer", "c_int8_t"): "Int8",
    ("integer", "c_int16_t"): "Int16",
    ("integer", "c_int32_t"): "Int32",
    ("integer", "c_int64_t"): "Int64",
    ("real", None): "Float32",
    ("real", "4"): "Float32",
    ("real", "8"): "Float64",
    ("real", "real32"): "Float32",
    ("real", "real64"): "Float64",
    ("real", "c_float"): "Float32",
    ("real", "c_double"): "Float64",
    ("complex", None): "Complex64",
    ("complex", "4"): "Complex64",
    ("complex", "8"): "Complex128",
    ("complex", "real32"): "Complex64",
    ("complex", "real64"): "Complex128",
    ("complex", "c_float_complex"): "Complex64",
    ("complex", "c_double_complex"): "Complex128",
    ("logical", None): "Bool",
    ("logical", "c_bool"): "Bool",
    ("character", None): "String",
    ("character", "1"): "String",
    ("character", "c_char"): "String",
}

_FORTRAN_INTRINSIC_TYPES = frozenset({"integer", "real", "complex", "logical", "character"})
_FORTRAN_STORAGE_PROBE_TYPES = frozenset({"integer", "real", "complex", "logical"})
_FORTRAN_STORAGE_TYPE_MAP = {
    "logical": {bits: name for name, bits in BOOLEAN_STORAGE_BITS.items() if name != "Bool"},
    "integer": {8: "Int8", 16: "Int16", 32: "Int32", 64: "Int64"},
    "real": {32: "Float32", 64: "Float64", 80: "Float128", 96: "Float128", 128: "Float128"},
    "complex": {64: "Complex64", 128: "Complex128", 160: "Complex256", 192: "Complex256", 256: "Complex256"},
}


# Internal conversion context


@dataclass(frozen=True)
class _DerivedTypeContext:
    """Keep lexical derived-type lookup facts while one parser node is converted.

    The context records the owning module, imported names, procedure-local
    imports, and locally declared type names.  It is immutable so nested
    visitors can safely derive narrower contexts without mutating their parent.
    """

    module: str | None = None
    uses: dict[str, list[FortranUseMapping]] | None = None
    procedure_uses: dict[str, list[FortranUseMapping]] | None = None
    local_types: frozenset[str] = frozenset()


@dataclass(frozen=True)
class _ResolvedDerivedTypeOrigin:
    """Describe the module and spelling selected for an imported derived type.

    ``import_scope`` records when a procedure-local ``use`` made the selected
    name visible, which determines whether the public semantic name is scoped.
    """

    module: str | None
    name: str
    import_scope: str | None = None


@dataclass(frozen=True)
class _DeclarationCallableContext:
    """Hold lexical procedure names and imports for expression-call resolution."""

    module: str | None
    local_procedures: dict[str, SemanticFunction]
    local_interfaces: dict[str, SemanticPrototype]
    uses: dict[str, list[FortranUseMapping]]


def _normalize_compile_time_values(
    compile_time_values: dict[str, int | str] | None,
) -> dict[str, str]:
    """Normalize user-supplied compile-time values for text substitution.

    The semantic layer accepts values keyed either by a symbol name
    (``{"rk": 8}``) or by the exact unresolved expression kept by the parser
    (``{"selected_real_kind(12)": 8}``). Internally both keys and values are
    strings so that kind and shape expressions can be rewritten uniformly.

    Example:
        >>> _normalize_compile_time_values({"rk": 8})["rk"]
        '8'
    """
    return {
        str(key).strip().lower(): str(value) for key, value in (compile_time_values or {}).items() if str(key).strip()
    }


def _resolve_compile_time_text(text: str, compile_time_values: dict[str, str]) -> str:
    """Resolve known compile-time symbols inside one kind or shape expression.

    Exact expression keys win before identifier replacement, so compiler or
    implementation-specific calls can be supplied directly. Symbol keys are
    then substituted token by token.

    Example:
        >>> values = _normalize_compile_time_values({"selected_real_kind(12)": 8, "n": 32})
        >>> _resolve_compile_time_text("selected_real_kind(12)", values)
        '8'
        >>> _resolve_compile_time_text("1:n", values)
        '1:32'
    """
    raw = str(text)
    stripped = raw.strip()
    if not stripped or not compile_time_values:
        return raw

    exact = compile_time_values.get(stripped.lower())
    if exact is not None:
        return exact

    def replace_symbol(match: re.Match[str]) -> str:
        """Replace one identifier only when the supplied values define it."""
        token = match.group(0)
        return compile_time_values.get(token.lower(), token)

    return re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", replace_symbol, raw)


class FortranToIRConverter(ClassVisitor):
    """Convert parsed Fortran models into semantic IR models.

    ``visit`` is the single dispatch entrypoint. Each parsed model class is
    handled by its matching ``_visit_<ClassName>`` method.
    """

    def __init__(
        self,
        type_map: dict[tuple[str, str | None], str] | None = None,
        compile_time_values: dict[str, int | str] | None = None,
        wrapped_derived_types: Iterable[tuple[str, str]] | None = None,
        type_facts: dict[tuple[str, str | None], dict[str, object]] | None = None,
    ):
        """Configure parser-fact conversion without performing any conversion.

        ``type_map`` overrides intrinsic kind-to-semantic-name mapping;
        ``compile_time_values`` resolves parser-preserved expressions;
        ``wrapped_derived_types`` marks imported types with generated wrappers;
        and ``type_facts`` supplies compiler-measured storage facts.  Inputs are
        normalized into lookup-friendly forms and retained for later visitors.
        """
        self.type_map = FORTRAN_TYPE_MAP if type_map is None else type_map
        self.compile_time_values = _normalize_compile_time_values(compile_time_values)
        self.wrapped_derived_types = {
            (str(module).lower(), str(name).lower()) for module, name in (wrapped_derived_types or [])
        }
        self._known_procedures: set[tuple[str, str]] = set()
        self.type_facts = {
            (str(base_type).lower(), None if kind is None else str(kind).lower()): dict(fact)
            for (base_type, kind), fact in (type_facts or {}).items()
        }

    def visit(self, node, **context):
        """Convert one supported parsed model using the shared class visitor.

        Call this for a specific parser model when the convenience module,
        file, or project helpers do not match the desired input shape.  The
        result type follows ``node``; unsupported model classes raise
        :class:`TypeError`.
        """
        return self._visit(node, **context)

    @staticmethod
    def _visit_not_supported(node):
        """Reject parser models without a semantic conversion visitor."""
        raise TypeError(f"Unsupported Fortran parse object: {type(node)!r}")

    def first_module(self, parsed):
        """Select one module from supported single-module conversion inputs.

        A :class:`FortranModule` is returned unchanged, a file contributes its
        first module, and the legacy signature-list form becomes a synthetic
        module.  Empty files and unsupported shapes retain their established
        :class:`ValueError` and :class:`TypeError` failures.
        """
        if isinstance(parsed, FortranModule):
            return parsed
        if isinstance(parsed, FortranFile):
            if not parsed.modules:
                raise ValueError("Expected at least one Fortran module in parsed file")
            return parsed.modules[0]
        if isinstance(parsed, list):
            module_name = next((getattr(sig, "module", None) for sig in parsed if getattr(sig, "module", None)), None)
            procedures = [sig for sig in parsed if not getattr(sig, "in_interface", False)]
            return FortranModule(name=module_name or "", procedures=procedures)
        raise TypeError(f"Unsupported Fortran parse object: {type(parsed)!r}")

    # Container visitors

    def _visit_FortranFile(
        self,
        parsed_file: FortranFile,
        *,
        standalone_module_name: str | None = None,
    ) -> list[SemanticModule]:
        """Convert every module and standalone procedure group in one file.

        The method first expands the wrapped-derived-type lookup from the file,
        then preserves parser module order.  Standalone procedures are emitted
        last as the requested synthetic module when present.
        """
        converter = self._with_additional_wrapped_types(self._wrapped_types_from_file(parsed_file))
        converter = converter._with_additional_known_procedures(self._known_procedures_from_file(parsed_file))
        modules = [converter.visit(module) for module in parsed_file.modules]
        if parsed_file.procedures:
            modules.append(
                converter.procedures_to_semantic_module(
                    parsed_file.procedures,
                    name=standalone_module_name or self._standalone_module_name(parsed_file),
                    callback_interfaces=self._callback_interface_lookup(parsed_file),
                )
            )
        return modules

    def _visit_FortranProject(self, project: FortranProject) -> list[SemanticModule]:
        """Convert project files in order with project-wide type and callback context.

        Each file receives the known project type set plus its own declarations,
        while imported callback interfaces are resolved against the project.
        The returned module ordering matches the input file and parser order.
        """
        converter = self._with_additional_wrapped_types(self._wrapped_types_from_project(project))
        converter = converter._with_additional_known_procedures(self._known_procedures_from_project(project))
        semantic_modules = []
        for parsed_file in project.files:
            file_converter = converter._with_additional_wrapped_types(converter._wrapped_types_from_file(parsed_file))
            semantic_modules.extend(
                file_converter.visit(
                    module,
                    callback_interfaces=self._project_callback_interface_lookup(project, module),
                )
                for module in parsed_file.modules
            )
            if parsed_file.procedures:
                semantic_modules.append(
                    file_converter.procedures_to_semantic_module(
                        parsed_file.procedures,
                        name=self._standalone_module_name(parsed_file),
                        callback_interfaces=self._callback_interface_lookup(parsed_file),
                    )
                )
        return semantic_modules

    # Variable and argument visitors

    def _visit_FortranVariable(
        self,
        var: FortranVariable,
        *,
        derived_type_context: _DerivedTypeContext | None = None,
        declaration_arrays: dict[str, ArrayExpressionSource] | None = None,
        as_type: bool = False,
        as_data_member: bool = False,
        binding_cls: type[SemanticVariable] = SemanticVariable,
        source_kind: str = "variable",
    ) -> SemanticType | SemanticVariable:
        """Convert a parser variable as a type or a semantic data member.

        ``as_type`` returns the normalized :class:`SemanticType`; ``as_data_member``
        produces the requested semantic variable subtype with origin metadata.
        The default preserves the historical type-only conversion path.
        """
        if as_type:
            return self._convert_variable_type(
                var,
                derived_type_context=derived_type_context,
                declaration_arrays=declaration_arrays,
            )
        if as_data_member:
            return self._convert_data_member(
                var,
                derived_type_context=derived_type_context,
                binding_cls=binding_cls,
                source_kind=source_kind,
                declaration_arrays=declaration_arrays,
            )
        return self._convert_variable_type(
            var,
            derived_type_context=derived_type_context,
            declaration_arrays=declaration_arrays,
        )

    def _convert_variable_type(
        self,
        var: FortranVariable,
        *,
        derived_type_context: _DerivedTypeContext | None = None,
        declaration_arrays: dict[str, ArrayExpressionSource] | None = None,
    ) -> SemanticType:
        """Build a semantic datatype, storage contract, and source metadata for ``var``.

        This is the intrinsic/derived-type normalization stage.  It resolves
        known compile-time text, applies measured type facts, and records
        source storage facts without deciding downstream ownership policy.
        """
        semantic_name = self._semantic_type_name(var)
        derived_type_ref = self._derived_type_ref(var, derived_type_context)
        metadata = {}
        type_fact = self._target_type_fact(var)
        if type_fact is not None:
            metadata["fortran_type_fact"] = dict(type_fact)
            metadata["fortran_type_fact_source"] = str(type_fact.get("source") or "compiler_probe")
        if derived_type_ref is not None:
            semantic_name, ref_metadata = derived_type_ref
            metadata[EXTERNAL_TYPE_REF_METADATA] = ref_metadata
        if var.base_type.lower() == "character":
            metadata["fortran_character_length"] = self._character_length(var)
        if var.rank == 0 and getattr(var, "allocatable", False):
            metadata["fortran_allocatable"] = True
        if getattr(var, "polymorphic", False):
            metadata["fortran_polymorphic"] = True
        if getattr(var, "target", False):
            metadata["aliased"] = True
            metadata["fortran_target"] = True
        if getattr(var, "pointer", False):
            metadata["fortran_pointer"] = True
            metadata["fortran_pointer_association"] = "runtime"
        shape = [self._resolve_compile_time_text(dim) for dim in var.shape]
        if var.rank > 0:
            storage = self._array_storage_contract(var, shape, declaration_arrays=declaration_arrays)
        elif getattr(var, "pointer", False):
            storage = SemanticStorageContract(kind="reference", pointer_depth=1)
        else:
            storage = None
        semantic_type = SemanticType(
            name=semantic_name,
            rank=var.rank,
            dtype=semantic_name,
            shape=list(storage.array.shape if storage is not None and storage.array is not None else shape),
            metadata=metadata,
            storage=storage,
            origin=self._variable_origin(var),
        )
        self._add_variable_constraints(semantic_type, var)
        return semantic_type

    def _character_length(self, var: FortranVariable) -> str:
        """Return the resolved character length recorded by a parsed declaration.

        The helper reads the parser's mixed kind/length spelling, preferring an
        explicit ``len=`` fragment and otherwise preserving legacy length syntax;
        declarations with neither continue to use Fortran's length-one default.
        """
        raw = self._resolve_compile_time_text(str(var.kind or "")).strip()
        length_match = re.search(r"(?:^|,)\s*len\s*=\s*([^,]+)", raw, re.IGNORECASE)
        if length_match is not None:
            return length_match.group(1).strip()
        if var.character_length_syntax and raw:
            return raw
        return "1"

    def _visit_FortranArgument(
        self,
        arg: FortranArgument | FortranVariable,
        *,
        derived_type_context: _DerivedTypeContext | None = None,
        callback_interfaces: dict[str, FortranProcedureSignature] | None = None,
        as_data_member: bool = False,
        as_type: bool = False,
        binding_cls: type[SemanticVariable] = SemanticVariable,
        source_kind: str = "variable",
        declaration_arrays: dict[str, ArrayExpressionSource] | None = None,
    ) -> SemanticArgument | SemanticVariable:
        """Convert a dummy argument, including callback and storage facts.

        The visitor returns a type or data member in the explicit modes used by
        related visitors; otherwise it produces a :class:`SemanticArgument`.
        It mutates the freshly built semantic type with access and storage facts
        inferred from the parser declaration before constructing the argument.
        """
        if as_type:
            return self._convert_variable_type(
                arg,
                derived_type_context=derived_type_context,
                declaration_arrays=declaration_arrays,
            )
        if as_data_member:
            return self._convert_data_member(
                arg,
                derived_type_context=derived_type_context,
                binding_cls=binding_cls,
                source_kind=source_kind,
                declaration_arrays=declaration_arrays,
            )
        if arg.base_type.lower() == "procedure":
            semantic_type = self._callback_semantic_type(
                arg,
                callback_interfaces or {},
                derived_type_context=derived_type_context,
            )
        else:
            semantic_type = self._convert_variable_type(
                arg,
                derived_type_context=derived_type_context,
                declaration_arrays=declaration_arrays,
            )
        access = self._argument_access(arg, semantic_type)
        if semantic_type.storage is not None and semantic_type.storage.kind == "callback":
            pass
        elif semantic_type.rank > 0:
            self._apply_array_argument_contract(semantic_type, arg, writes_argument=access[1])
        elif getattr(arg, "optional", False) and access[1] and not access[0]:
            semantic_type.storage = self._scalar_storage_contract(writes_argument=access[1])
        elif not getattr(arg, "pass_by_value", False):
            semantic_type.storage = self._reference_storage_contract(writes_argument=access[1])
            if getattr(arg, "pointer", False):
                semantic_type.storage.pointer_depth = 1
        if getattr(arg, "pointer", False) and not access[1]:
            self._apply_pointer_input_policy(semantic_type)
        self._apply_argument_ownership(semantic_type, writes_argument=access[1])

        metadata = {}
        if getattr(arg, "pass_by_value", False) and str(getattr(arg, "base_type", "")).casefold() == "derived":
            metadata[NATIVE_BY_VALUE_METADATA] = True
        argument = SemanticArgument(
            name=arg.name,
            semantic_type=semantic_type,
            optional=getattr(arg, "optional", False),
            visibility=getattr(arg, "visibility", "public"),
            metadata=metadata,
            origin=self._argument_origin(arg),
        )
        # Source access is an internal optimization fact, not part of the
        # serialized semantic contract.  It lets policy omit a useless copy-in
        # for intent(out) arrays without changing scalar ownership behavior.
        argument._source_reads_argument = access[0]
        return argument

    def _convert_data_member(
        self,
        var: FortranArgument | FortranVariable,
        *,
        derived_type_context: _DerivedTypeContext | None = None,
        binding_cls: type[SemanticVariable] = SemanticVariable,
        source_kind: str = "variable",
        declaration_arrays: dict[str, ArrayExpressionSource] | None = None,
    ) -> SemanticVariable:
        """Create a module variable or derived-type field from a parsed declaration.

        The result carries normalized type, initializer, visibility, and source
        origin facts.  Array storage receives allocation and pointer facts from
        the declaration; no wrapper accessor or ownership policy is chosen here.
        """
        semantic_type = self._convert_variable_type(
            var,
            derived_type_context=derived_type_context,
            declaration_arrays=declaration_arrays,
        )
        if semantic_type.storage is not None and semantic_type.storage.array is not None:
            semantic_type.storage.array.allocatable = getattr(var, "allocatable", False)
            semantic_type.storage.array.pointer = getattr(var, "pointer", False)
        metadata = {}
        if getattr(var, "symbolic_value", None) is not None:
            metadata["fortran_initializer"] = var.symbolic_value
        binding = binding_cls(
            name=var.name,
            semantic_type=semantic_type,
            visibility=getattr(var, "visibility", "public"),
            default_value=getattr(var, "value", None),
            metadata=metadata,
            origin=self._data_origin(var, source_kind=source_kind),
        )
        binding.optional = getattr(var, "optional", False)
        return binding

    @staticmethod
    def _callback_interface_lookup(
        module: FortranModule | FortranFile,
    ) -> dict[str, FortranProcedureSignature]:
        """Index explicit and abstract interface procedures usable by dummy procedures."""
        lookup: dict[str, FortranProcedureSignature] = {}
        for interface in module.interfaces:
            for signature in interface.procedures:
                lookup.setdefault(signature.name.casefold(), signature)
            if interface.name and len(interface.procedures) == 1:
                lookup.setdefault(interface.name.casefold(), interface.procedures[0])
        return lookup

    @classmethod
    def _project_callback_interface_lookup(
        cls,
        project: FortranProject,
        module: FortranModule,
    ) -> dict[str, FortranProcedureSignature]:
        """Resolve abstract interfaces imported from another parsed module."""
        modules = {name.casefold(): item for name, item in project.modules.items()}
        modules.update({item.name.casefold(): item for parsed_file in project.files for item in parsed_file.modules})
        imported: dict[str, FortranProcedureSignature] = {}
        for module_name, mappings in module.uses.items():
            source_module = modules.get(module_name.casefold())
            if source_module is None:
                continue
            source_lookup = cls._callback_interface_lookup(source_module)
            if not mappings:
                imported.update(source_lookup)
                continue
            for mapping in mappings:
                signature = source_lookup.get(mapping.source.casefold())
                if signature is not None:
                    imported[mapping.local_name.casefold()] = signature
        return imported

    def _callback_semantic_type(
        self,
        arg: FortranArgument | FortranVariable,
        callback_interfaces: dict[str, FortranProcedureSignature],
        *,
        derived_type_context: _DerivedTypeContext | None,
    ) -> SemanticType:
        """Build the callback semantic type for a procedure dummy when resolvable.

        A pointer dummy or unknown interface follows ordinary variable
        conversion.  For a known interface, the helper converts its arguments
        and result into prototype metadata and normalizes non-value callback
        dummies to writable references.
        """
        if getattr(arg, "pointer", False):
            return self._convert_variable_type(arg, derived_type_context=derived_type_context)
        interface_name = str(arg.kind or arg.name)
        signature = callback_interfaces.get(interface_name.casefold())
        if signature is None:
            return self._convert_variable_type(arg, derived_type_context=derived_type_context)

        context = self._procedure_derived_type_context(signature, derived_type_context)
        projected_arguments = list(signature.arguments)
        callback_arguments = [self.visit(item, derived_type_context=context) for item in projected_arguments]
        for source_argument, callback_argument in zip(projected_arguments, callback_arguments, strict=True):
            self._normalize_callback_reference_storage(callback_argument, source_argument)
            self._record_prototype_argument_intent(callback_argument, source_argument)
        callback_return = (
            self.visit(signature.result, derived_type_context=context, as_type=True)
            if signature.result
            else SemanticType("None", dtype="None")
        )
        prototype_module = str(signature.module or "")
        return SemanticType(
            interface_name,
            dtype="Prototype",
            metadata={
                "arguments": [item.semantic_type for item in callback_arguments],
                "callback_arguments": callback_arguments,
                "return": callback_return,
                PROTOTYPE_REF_METADATA: {
                    "name": interface_name,
                    "local_name": interface_name,
                    "origin_module": prototype_module,
                },
                "native_callback_kind": signature.kind,
                "callback_lifetime": "call",
                "callback_thread": "entering_thread",
                "callback_exception": "print_traceback_and_abort",
                "prototype_metadata": self._procedure_metadata(signature),
            },
            storage=SemanticStorageContract(
                kind="callback",
                ownership="borrowed",
                calling_convention="fortran_dummy_procedure",
            ),
            origin=SemanticOrigin(
                source_language="fortran",
                native_name=arg.name,
                native_scope=getattr(arg, "procedure", None),
                source_kind="dummy_procedure",
                source_type=self._fortran_source_type(arg),
                metadata={"prototype": interface_name},
            ),
        )

    @staticmethod
    def _normalize_callback_reference_storage(
        callback_argument: SemanticArgument,
        source_argument: FortranArgument | FortranVariable,
    ) -> None:
        """Make every non-value callback dummy a permissive reference contract."""
        if getattr(source_argument, "pass_by_value", False):
            return
        semantic_type = callback_argument.semantic_type
        if semantic_type.name == "String" and semantic_type.rank == 0:
            semantic_type.storage = SemanticStorageContract(
                kind="array",
                read_only=False,
                mutable=True,
                array=SemanticArrayContract(
                    rank=0,
                    shape=[],
                    category=SCALAR_STORAGE_CATEGORY,
                ),
            )
        elif semantic_type.storage is None:
            semantic_type.storage = SemanticStorageContract(
                kind="reference",
                read_only=False,
                mutable=True,
                pointer_depth=1,
            )
        else:
            semantic_type.storage.read_only = False
            semantic_type.storage.mutable = True
        semantic_type.ownership.mutable = True

    @staticmethod
    def _record_prototype_argument_intent(
        argument: SemanticArgument,
        source_argument: FortranArgument | FortranVariable,
    ) -> None:
        """Retain exact dummy direction only inside an interface prototype."""
        intent = getattr(source_argument, "intent", None)
        if intent is not None:
            argument.origin.metadata[PROTOTYPE_INTENT_METADATA] = intent

    def _module_prototypes(
        self,
        module: FortranModule,
        context: _DerivedTypeContext,
        referenced: set[str],
        called: set[str],
    ) -> list[SemanticPrototype]:
        """Convert every referenced interface into one exact prototype signature."""
        prototypes: list[SemanticPrototype] = []
        seen: set[str] = set()
        for interface in module.interfaces:
            for signature in interface.procedures:
                name = interface.name if interface.name and len(interface.procedures) == 1 else signature.name
                if not (interface.abstract or name.casefold() in referenced or name.casefold() in called):
                    continue
                if name in seen:
                    continue
                seen.add(name)
                arguments = [self.visit(item, derived_type_context=context) for item in signature.arguments]
                for source_argument, argument in zip(signature.arguments, arguments, strict=True):
                    self._normalize_callback_reference_storage(argument, source_argument)
                    self._record_prototype_argument_intent(argument, source_argument)
                return_type = (
                    self.visit(signature.result, derived_type_context=context, as_type=True)
                    if signature.result is not None
                    else SemanticType("None", dtype="None")
                )
                prototypes.append(
                    SemanticPrototype(
                        name=name,
                        native_name=name,
                        arguments=arguments,
                        return_type=return_type,
                        metadata=self._procedure_metadata(signature),
                        visibility=self._symbol_visibility(module, name),
                        origin=SemanticOrigin(
                            source_language="fortran",
                            native_name=name,
                            native_scope=module.name,
                            source_kind="prototype",
                            metadata={"fortran_interface_kind": "abstract" if interface.abstract else "explicit"},
                        ),
                        pure=any(attribute.casefold() == "pure" for attribute in signature.attributes),
                    )
                )
        return prototypes

    @staticmethod
    def _module_declaration_call_names(module: FortranModule) -> set[str]:
        """Collect bare call names appearing in module-owned declaration shapes."""
        variables = [
            *getattr(module, "variables", ()),
            *(field for derived in module.derived_types for field in derived.fields),
            *(
                variable
                for procedure in module.procedures
                for variable in (*procedure.arguments, procedure.result)
                if variable is not None
            ),
        ]
        return {
            call.casefold()
            for variable in variables
            for dimension in getattr(variable, "shape", ())
            for call in declaration_expression_calls(str(dimension))
            if call != "<invalid>" and "." not in call
        }

    @staticmethod
    def _visit_FortranEnumerator(enumerator: FortranEnumerator, *, enum: FortranEnum) -> SemanticVariable:
        """Convert one enum member into a constant integer semantic variable.

        The output preserves the parser value, visibility, enum identity, and
        ``bind(C)`` provenance so printers and later stages can consume it.
        """
        semantic_type = SemanticType(
            "Int32",
            dtype="Int32",
            constraints=[SemanticConstraint("Constant")],
            metadata={
                "enum_name": enum.name,
                "fortran_enum": True,
                "fortran_bind_c": enum.bind_c,
                "c_underlying_type": "Int32",
            },
        )
        metadata = {"fortran_enum": True}
        if enumerator.symbolic_value is not None:
            metadata["fortran_initializer"] = enumerator.symbolic_value
        return SemanticVariable(
            name=enumerator.name,
            semantic_type=semantic_type,
            visibility=enumerator.visibility,
            default_value=enumerator.value,
            metadata=metadata,
            origin=SemanticOrigin(
                source_language="fortran",
                native_name=enumerator.name,
                native_scope=enum.module,
                source_kind="enum_constant",
                source_type="enum, bind(C)" if enum.bind_c else "enum",
                metadata={"fortran_enum": True, "fortran_bind_c": enum.bind_c},
            ),
        )

    def _visit_FortranProcedureSignature(
        self,
        proc: FortranProcedureSignature,
        visibility: str = "public",
        *,
        derived_type_context: _DerivedTypeContext | None = None,
        callback_interfaces: dict[str, FortranProcedureSignature] | None = None,
    ) -> SemanticFunction:
        """Convert a parsed procedure signature into its callable semantic contract.

        Arguments are reordered only through the existing optional-argument
        projection rule, receive derived-type and callback context, and then
        drive the returned function's projection.  Pointer results retain their
        established result-policy metadata.
        """
        context = self._procedure_derived_type_context(proc, derived_type_context)
        declaration_arrays = self._array_expression_sources((*proc.arguments, proc.result))
        arguments = [
            self.visit(
                arg,
                derived_type_context=context,
                callback_interfaces=callback_interfaces,
                declaration_arrays=declaration_arrays,
            )
            for arg in self._projected_procedure_arguments(proc)
        ]
        metadata = self._procedure_metadata(proc)
        return_type = (
            self.visit(
                proc.result,
                derived_type_context=context,
                declaration_arrays=declaration_arrays,
                as_type=True,
            )
            if proc.result
            else None
        )
        if return_type is not None and getattr(proc.result, "pointer", False):
            self._apply_pointer_result_policy(return_type)
        return SemanticFunction(
            name=proc.name,
            native_name=proc.name,
            arguments=arguments,
            return_type=return_type,
            projection=self._procedure_projection(proc, arguments),
            metadata=metadata,
            visibility=visibility,
            origin=SemanticOrigin(
                source_language="fortran",
                native_name=proc.name,
                native_scope=proc.module,
                source_kind=proc.kind,
                metadata=dict(metadata),
            ),
        )

    def _visit_FortranDerivedType(
        self,
        dtype: FortranDerivedType,
        procedure_lookup: dict[str, SemanticFunction] | None = None,
        *,
        derived_type_context: _DerivedTypeContext | None = None,
    ) -> SemanticClass:
        """Convert a Fortran derived type into fields, bound methods, and overload sets.

        The returned class preserves component ordering and type attributes,
        derives method bindings from already converted procedures, and records
        declaration facts for later semantic and printing stages.
        """
        lookup = procedure_lookup or {}
        context = derived_type_context or _DerivedTypeContext(
            module=dtype.module,
            local_types=frozenset({dtype.name.lower()}),
        )
        methods = self._bound_methods(dtype, lookup)
        overload_sets = self._bound_overload_sets(dtype, methods)
        type_attributes = list(dict.fromkeys(str(attr).casefold() for attr in dtype.attributes))
        metadata = {
            "fortran_type_attributes": type_attributes,
            "fortran_component_order": [field.name for field in dtype.fields],
            "fortran_component_facts": [self._derived_type_component_fact(field) for field in dtype.fields],
            "fortran_layout_policy": "accessors",
            "fortran_direct_layout": False,
        }
        if "bind(c)" in type_attributes:
            metadata["fortran_bind_c"] = True
        if "sequence" in type_attributes:
            metadata["fortran_sequence"] = True
        deferred_bindings = [
            str(binding.get("name") or "<anonymous>")
            for binding in getattr(dtype, "procedure_bindings", ()) or ()
            if "deferred" in {str(attr).casefold() for attr in binding.get("attrs", ())}
        ]
        if deferred_bindings:
            metadata["fortran_deferred_bindings"] = deferred_bindings
        final_procedures = list(getattr(dtype, "final_procedures", []))
        if final_procedures:
            metadata["fortran_final_procedures"] = final_procedures
        declaration_arrays = self._array_expression_sources(dtype.fields)
        return SemanticClass(
            name=dtype.name,
            native_name=dtype.name,
            fields=[
                self.visit(
                    field,
                    as_data_member=True,
                    derived_type_context=context,
                    binding_cls=SemanticField,
                    source_kind="field",
                    declaration_arrays=declaration_arrays,
                )
                for field in dtype.fields
            ],
            methods=methods,
            overload_sets=overload_sets,
            base_classes=self._base_classes(dtype),
            metadata=metadata,
            visibility=getattr(dtype, "visibility", "public"),
            origin=SemanticOrigin(
                source_language="fortran",
                native_name=dtype.name,
                native_scope=dtype.module,
                source_kind="derived_type",
            ),
        )

    @staticmethod
    def _derived_type_component_fact(field: FortranArgument) -> dict[str, object]:
        """Return the declaration facts retained for one derived-type component."""
        return {
            "name": field.name,
            "source_type": FortranToIRConverter._fortran_source_type(field),
            "kind": field.kind,
            "rank": field.rank,
            "shape": list(field.shape),
            "allocatable": field.allocatable,
            "pointer": field.pointer,
            "target": field.target,
        }

    def _visit_FortranModule(
        self,
        module: FortranModule,
        *,
        callback_interfaces: dict[str, FortranProcedureSignature] | None = None,
    ) -> SemanticModule:
        """Assemble the semantic contents of one parsed Fortran module.

        The method establishes derived-type and callback context, converts
        procedures before classes, then assembles interfaces, variables, enum
        constants, imports, and visibility.  It deliberately records facts only;
        later policy completion owns wrapper behavior decisions.
        """
        context = self._module_derived_type_context(module)
        callback_interfaces = {
            **(callback_interfaces or {}),
            **self._callback_interface_lookup(module),
        }
        source_procedures = [
            *module.procedures,
            *self._module_explicit_interface_procedures(module),
        ]
        semantic_functions = [
            self.visit(
                proc,
                visibility=self._symbol_visibility(module, proc.name),
                derived_type_context=context,
                callback_interfaces=callback_interfaces,
            )
            for proc in source_procedures
        ]
        callback_prototypes = {
            argument.semantic_type.name.casefold()
            for function in semantic_functions
            for argument in function.arguments
            if argument.semantic_type.storage is not None and argument.semantic_type.storage.kind == "callback"
        }
        prototypes = self._module_prototypes(
            module,
            context,
            callback_prototypes,
            self._module_declaration_call_names(module),
        )
        procedure_lookup = {func.name.casefold(): func for func in semantic_functions}
        for procedure, function in zip(source_procedures, semantic_functions, strict=True):
            callable_context = self._declaration_callable_context(
                module,
                functions=semantic_functions,
                prototypes=prototypes,
                uses={**module.uses, **procedure.uses},
            )
            self._record_function_declaration_callables(function, callable_context)

        semantic_classes = [
            self.visit(
                dtype,
                procedure_lookup=procedure_lookup,
                derived_type_context=context,
            )
            for dtype in module.derived_types
        ]
        for semantic_cls in semantic_classes:
            semantic_cls.visibility = self._symbol_visibility(module, semantic_cls.name)
            self._record_class_declaration_callables(
                semantic_cls,
                self._declaration_callable_context(
                    module,
                    functions=semantic_functions,
                    prototypes=prototypes,
                ),
            )

        overload_sets = self._module_overload_sets(
            module,
            procedure_lookup,
            context,
            semantic_classes,
        )
        metadata = {}
        common_variables = {name.casefold() for name in module.common_variables}
        enum_constants = [
            self.visit(enumerator, enum=enum)
            for enum in getattr(module, "enums", [])
            for enumerator in enum.enumerators
        ]
        representable_variables = [
            var for var in getattr(module, "variables", []) if var.name.casefold() not in common_variables
        ]
        declaration_arrays = self._array_expression_sources(getattr(module, "variables", []))
        module_variables = [
            self.visit(
                var,
                as_data_member=True,
                derived_type_context=context,
                declaration_arrays=declaration_arrays,
            )
            for var in representable_variables
        ]
        for variable in module_variables:
            if variable.origin.native_scope is None:
                variable.origin.native_scope = module.name
            self._record_declaration_callables(
                variable.semantic_type,
                self._declaration_callable_context(
                    module,
                    functions=semantic_functions,
                    prototypes=prototypes,
                ),
            )
        return SemanticModule(
            name=module.name,
            functions=semantic_functions,
            prototypes=prototypes,
            overload_sets=overload_sets,
            classes=semantic_classes,
            variables=module_variables + enum_constants,
            imports=self._module_imports(module),
            metadata=metadata,
            origin=SemanticOrigin(
                source_language="fortran",
                native_name=module.name,
                native_scope=module.name,
                source_kind="module",
            ),
        )

    def _record_function_declaration_callables(
        self,
        function: SemanticFunction,
        context: _DeclarationCallableContext,
    ) -> None:
        """Record expression-call provenance for one function's arrays in place."""
        for argument in function.arguments:
            self._record_declaration_callables(argument.semantic_type, context)
        self._record_declaration_callables(function.return_type, context)
        for variable in function.locals:
            self._record_declaration_callables(variable.semantic_type, context)

    def _record_class_declaration_callables(
        self,
        semantic_class: SemanticClass,
        context: _DeclarationCallableContext,
    ) -> None:
        """Record native calls for fields and recursively nested class members."""
        for field in semantic_class.fields:
            self._record_declaration_callables(field.semantic_type, context)
        for method in semantic_class.methods:
            self._record_function_declaration_callables(method, context)
        for nested in semantic_class.classes:
            self._record_class_declaration_callables(nested, context)

    @staticmethod
    def _array_expression_sources(
        variables: Iterable[FortranVariable | None],
    ) -> dict[str, ArrayExpressionSource]:
        """Index declared arrays for inquiry translation within one source scope.

        The helper consumes parser variables, ignores absent/scalar entries,
        and returns case-preserving names with rank and source lower bounds.
        It does not resolve or mutate declaration expressions.
        """
        return {
            variable.name: ArrayExpressionSource(
                rank=variable.rank,
                lower_bounds=tuple(getattr(variable, "lbound", ()) or ()),
            )
            for variable in variables
            if variable is not None and int(variable.rank or 0) > 0
        }

    def procedures_to_semantic_module(
        self,
        procedures: list[FortranProcedureSignature],
        *,
        name: str,
        callback_interfaces: dict[str, FortranProcedureSignature] | None = None,
    ) -> SemanticModule:
        """Package standalone procedures as the synthetic semantic module ``name``.

        This is used by file and project conversion after parser module handling.
        Procedure order and optional callback lookup are passed unchanged to the
        existing procedure visitor.
        """
        semantic_functions = [self.visit(proc, callback_interfaces=callback_interfaces) for proc in procedures]
        function_lookup = {function.name.casefold(): function for function in semantic_functions}
        for procedure, function in zip(procedures, semantic_functions, strict=True):
            self._record_function_declaration_callables(
                function,
                _DeclarationCallableContext(
                    module=None,
                    local_procedures=function_lookup,
                    local_interfaces={},
                    uses=dict(procedure.uses),
                ),
            )
        return SemanticModule(
            name=name,
            functions=semantic_functions,
            origin=SemanticOrigin(
                source_language="fortran",
                source_kind="external_root",
            ),
        )

    @staticmethod
    def _module_imports(module: FortranModule) -> list[str | SemanticImport]:
        """Translate parser ``use`` mappings while preserving parser declaration order."""
        imports: list[str | SemanticImport] = []
        for module_name, mappings in module.uses.items():
            if not mappings:
                imports.append(module_name)
            else:
                imports.append(
                    SemanticImport(
                        module=module_name,
                        items=[SemanticImportItem(source=item.source, target=item.target) for item in mappings],
                    )
                )
        return imports

    def _declaration_callable_context(
        self,
        module: FortranModule,
        functions: Iterable[SemanticFunction] = (),
        prototypes: Iterable[SemanticPrototype] = (),
        *,
        uses: dict[str, list[FortranUseMapping]] | None = None,
    ) -> _DeclarationCallableContext:
        """Build lexical procedure facts for one module-owned declaration."""
        return _DeclarationCallableContext(
            module=module.name,
            local_procedures={function.name.casefold(): function for function in functions},
            local_interfaces={prototype.name.casefold(): prototype for prototype in prototypes},
            uses=dict(module.uses if uses is None else uses),
        )

    def _record_declaration_callables(
        self,
        semantic_type: SemanticType | None,
        context: _DeclarationCallableContext,
    ) -> None:
        """Attach native identities for calls in every axis of one array type.

        The helper consumes an already translated semantic shape and mutates
        only its array provenance. Public helper calls are omitted unless
        normal Fortran name resolution finds a native procedure that shadows
        the helper name; unresolved user calls remain explicit references.
        """
        storage = semantic_type.storage if semantic_type is not None else None
        array = storage.array if storage is not None else None
        if array is None:
            return
        array.expression_callables = [
            self._expression_callable_references(expression, context) for expression in array.shape
        ]

    def _expression_callable_references(
        self,
        expression: str,
        context: _DeclarationCallableContext,
    ) -> list[SemanticExpressionCallable]:
        """Resolve calls in one axis expression without evaluating their bodies."""
        references: list[SemanticExpressionCallable] = []
        for name in declaration_expression_calls(expression):
            reference = self._resolve_declaration_callable(name, context)
            if reference is not None:
                references.append(reference)
            elif name != "<invalid>" and not is_declaration_expression_helper(name):
                references.append(
                    SemanticExpressionCallable(
                        name=name,
                        native_name=name.rsplit(".", 1)[-1],
                        source_language="fortran",
                    )
                )
        return references

    def _resolve_declaration_callable(
        self,
        name: str,
        context: _DeclarationCallableContext,
    ) -> SemanticExpressionCallable | None:
        """Resolve one bare call through local declarations and ``USE`` maps."""
        if "." in name:
            return None
        key = name.casefold()
        interface = context.local_interfaces.get(key)
        if interface is not None:
            is_abstract_source = interface.origin.metadata.get("fortran_interface_kind") == "abstract"
            return SemanticExpressionCallable(
                name=name,
                native_name=interface.native_name or interface.name,
                native_scope=context.module if is_abstract_source else None,
                source_language="fortran",
                placement="abstract" if is_abstract_source else "standalone",
                declaration=interface,
            )

        local = context.local_procedures.get(key)
        if local is not None:
            return SemanticExpressionCallable(
                name=name,
                native_name=local.native_name or local.name,
                native_scope=context.module,
                source_language="fortran",
                placement="module" if context.module is not None else "standalone",
                declaration=local,
            )

        explicit = [
            (module_name, mapping.source)
            for module_name, mappings in context.uses.items()
            for mapping in mappings
            if mapping.local_name.casefold() == key
        ]
        if len(explicit) == 1:
            return SemanticExpressionCallable(
                name=name,
                native_name=explicit[0][1],
                native_scope=explicit[0][0],
                source_language="fortran",
                placement="module",
            )
        if explicit:
            return None

        wildcard_modules = [module_name for module_name, mappings in context.uses.items() if not mappings]
        known_origins = [
            module_name for module_name in wildcard_modules if (module_name.casefold(), key) in self._known_procedures
        ]
        if len(known_origins) != 1:
            return None
        return SemanticExpressionCallable(
            name=name,
            native_name=name,
            native_scope=known_origins[0],
            source_language="fortran",
            placement="module",
        )

    def _with_additional_wrapped_types(
        self,
        wrapped_types: Iterable[tuple[str, str]],
    ) -> FortranToIRConverter:
        """Return this converter or a clone that also recognizes ``wrapped_types``.

        The existing converter is reused when the normalized set is unchanged;
        otherwise the clone preserves every other conversion configuration.
        """
        merged = self.wrapped_derived_types | {
            (str(module).lower(), str(name).lower()) for module, name in wrapped_types
        }
        if merged == self.wrapped_derived_types:
            return self
        converter = FortranToIRConverter(
            type_map=self.type_map,
            compile_time_values=self.compile_time_values,
            wrapped_derived_types=merged,
            type_facts=self.type_facts,
        )
        converter._known_procedures = set(self._known_procedures)
        return converter

    def _with_additional_known_procedures(
        self,
        procedures: Iterable[tuple[str, str]],
    ) -> FortranToIRConverter:
        """Return this converter or a clone with more module-procedure identities."""
        merged = self._known_procedures | {
            (str(module).casefold(), str(name).casefold()) for module, name in procedures
        }
        if merged == self._known_procedures:
            return self
        converter = FortranToIRConverter(
            type_map=self.type_map,
            compile_time_values=self.compile_time_values,
            wrapped_derived_types=self.wrapped_derived_types,
            type_facts=self.type_facts,
        )
        converter._known_procedures = merged
        return converter

    @staticmethod
    def _wrapped_types_from_file(parsed_file: FortranFile) -> set[tuple[str, str]]:
        """Collect module-qualified derived types declared by one parsed file."""
        return {
            (dtype.module.lower(), dtype.name.lower())
            for module in parsed_file.modules
            for dtype in module.derived_types
            if dtype.module
        }

    @staticmethod
    def _known_procedures_from_file(parsed_file: FortranFile) -> set[tuple[str, str]]:
        """Collect module-qualified procedures declared by one parsed file."""
        return {(module.name, procedure.name) for module in parsed_file.modules for procedure in module.procedures}

    @staticmethod
    def _known_procedures_from_project(project: FortranProject) -> set[tuple[str, str]]:
        """Collect module-qualified procedures known to one parsed project."""
        return {(module.name, procedure.name) for module in project.modules.values() for procedure in module.procedures}

    @staticmethod
    def _module_explicit_interface_procedures(
        module: FortranModule,
    ) -> list[FortranProcedureSignature]:
        """Return explicitly public procedures declared by unnamed interfaces.

        An explicit public list makes the module declaration the authoritative
        wrapper contract. Other unnamed interface declarations remain
        interface-only facts even when a matching implementation is parsed.
        """
        public_names = {name.casefold() for name in module.public_symbols}
        declared_names = {procedure.name.casefold() for procedure in module.procedures}
        procedures: list[FortranProcedureSignature] = []
        for interface in module.interfaces:
            if interface.name is not None or interface.abstract:
                continue
            for procedure in interface.procedures:
                name = procedure.name.casefold()
                if name in declared_names:
                    continue
                if name not in public_names:
                    continue
                declared_names.add(name)
                procedures.append(procedure)
        return procedures

    @staticmethod
    def _wrapped_types_from_project(project: FortranProject) -> set[tuple[str, str]]:
        """Collect project-known module-qualified derived types for import resolution."""
        return {(dtype.module.lower(), dtype.name.lower()) for dtype in project.derived_types.values() if dtype.module}

    @staticmethod
    def _module_derived_type_context(module: FortranModule) -> _DerivedTypeContext:
        """Create the lexical type lookup context owned by ``module``."""
        return _DerivedTypeContext(
            module=module.name,
            uses=module.uses,
            local_types=frozenset(dtype.name.lower() for dtype in module.derived_types),
        )

    @staticmethod
    def _procedure_derived_type_context(
        proc: FortranProcedureSignature,
        parent: _DerivedTypeContext | None,
    ) -> _DerivedTypeContext:
        """Extend a parent type context with one procedure's imports and scope.

        The new context keeps enclosing local types while separating procedure-
        local imports, which later controls imported type qualification.
        """
        uses = dict(parent.uses or {}) if parent is not None else {}
        uses.update(proc.uses)
        return _DerivedTypeContext(
            module=proc.module or (parent.module if parent is not None else None),
            uses=uses,
            procedure_uses=FortranToIRConverter._procedure_local_uses(proc, parent),
            local_types=parent.local_types if parent is not None else frozenset(),
        )

    @staticmethod
    def _procedure_local_uses(
        proc: FortranProcedureSignature,
        parent: _DerivedTypeContext | None,
    ) -> dict[str, list[FortranUseMapping]]:
        """Return imports introduced locally by ``proc`` relative to its parent.

        A parser-preserved ``_local_uses`` mapping takes precedence; otherwise
        only imports differing from the parent context are returned.
        """
        local_uses = getattr(proc, "_local_uses", None)
        if isinstance(local_uses, dict):
            return dict(local_uses)
        if parent is None or parent.uses is None:
            return dict(proc.uses)
        return {module: mappings for module, mappings in proc.uses.items() if parent.uses.get(module) != mappings}

    def _derived_type_ref(
        self,
        var: FortranVariable,
        context: _DerivedTypeContext | None,
    ) -> tuple[str, dict[str, object]] | None:
        """Return an imported derived type's public name and reference metadata.

        Local, unresolved, and non-derived declarations produce ``None``.  A
        procedure-local import is deliberately qualified to avoid colliding with
        module-level names; the returned metadata records wrapper availability.
        """
        if var.base_type.lower() != "derived":
            return None
        local_name = str(var.kind)
        if not local_name:
            return None

        origin = self._resolve_derived_type_origin(local_name, context)
        local_type = bool(context is not None and context.module and local_name.lower() in context.local_types)
        if local_type or origin.module is None:
            return None
        wrapped = bool((origin.module.lower(), origin.name.lower()) in self.wrapped_derived_types)
        public_name = local_name
        if origin.import_scope == "procedure":
            public_name = f"{origin.module}.{origin.name}"
        metadata: dict[str, object] = {
            "name": origin.name,
            "local_name": public_name,
            "origin_module": origin.module,
            "wrapped": wrapped,
            "representation": "wrapped" if wrapped else "opaque",
        }
        if origin.import_scope is not None:
            metadata["import_scope"] = origin.import_scope
        return public_name, metadata

    def _resolve_derived_type_origin(
        self,
        local_name: str,
        context: _DerivedTypeContext | None,
    ) -> _ResolvedDerivedTypeOrigin:
        """Resolve ``local_name`` against local declarations and lexical imports.

        Unambiguous local declarations win.  When a module import and a
        procedure-local import identify the same type, the result records the
        procedure scope so callers can preserve its qualified semantic spelling.
        """
        lname = local_name.lower()
        if context is None:
            return _ResolvedDerivedTypeOrigin(None, local_name)
        if lname in context.local_types:
            return _ResolvedDerivedTypeOrigin(context.module, local_name)

        resolved = self._resolve_derived_type_origin_from_uses(local_name, context.uses)
        if resolved.module is None:
            return resolved
        procedure_resolved = self._resolve_derived_type_origin_from_uses(local_name, context.procedure_uses)
        if (procedure_resolved.module, procedure_resolved.name) == (resolved.module, resolved.name):
            return _ResolvedDerivedTypeOrigin(resolved.module, resolved.name, import_scope="procedure")
        return resolved

    def _resolve_derived_type_origin_from_uses(
        self,
        local_name: str,
        uses: dict[str, list[FortranUseMapping]] | None,
    ) -> _ResolvedDerivedTypeOrigin:
        """Resolve one derived-type spelling from explicit or wildcard ``use`` maps.

        Only an unambiguous match is returned.  Ambiguous explicit or wildcard
        imports intentionally remain unresolved so this conversion stage does
        not invent a native identity.
        """
        lname = local_name.lower()
        explicit: list[tuple[str, str]] = []
        wildcard_modules: list[str] = []
        for module_name, mappings in (uses or {}).items():
            if not mappings:
                wildcard_modules.append(module_name)
                continue
            for mapping in mappings:
                if mapping.local_name.lower() == lname:
                    explicit.append((module_name, mapping.source))

        if len(explicit) == 1:
            return _ResolvedDerivedTypeOrigin(explicit[0][0], explicit[0][1])
        if len(explicit) > 1:
            return _ResolvedDerivedTypeOrigin(None, local_name)

        wrapped_wildcards = [
            module_name
            for module_name in wildcard_modules
            if (module_name.lower(), lname) in self.wrapped_derived_types
        ]
        if len(wrapped_wildcards) == 1:
            return _ResolvedDerivedTypeOrigin(wrapped_wildcards[0], local_name)
        if len(wildcard_modules) == 1:
            return _ResolvedDerivedTypeOrigin(wildcard_modules[0], local_name)
        return _ResolvedDerivedTypeOrigin(None, local_name)

    def _semantic_type_name(self, var: FortranVariable) -> str:
        """Map a parsed intrinsic, derived, or procedure declaration to its dtype name.

        Compiler storage facts take precedence over the configured kind map.
        Unsupported or incomplete parser facts retain their established
        :class:`ValueError` diagnostics rather than being silently approximated.
        """
        base_type = var.base_type.lower()
        if base_type == "unknown":
            raise ValueError(f"Unknown Fortran datatype for variable '{var.name}'")

        if base_type == "derived":
            if not var.kind:
                raise ValueError(f"Derived type variable '{var.name}' is missing concrete type name")
            return str(var.kind)
        if base_type == "procedure":
            return "Procedure"

        fact = self._target_type_fact(var)
        if fact is not None:
            semantic_type = self._semantic_type_from_target_fact(fact)
            if semantic_type is None:
                bits = int(fact.get("bits") or 0)
                raise ValueError(
                    f"Unsupported Fortran target storage for variable '{var.name}': {base_type} uses {bits}-bit storage"
                )
            return semantic_type

        kind = self._semantic_kind_key(var)
        semantic_type = self.type_map.get((base_type, kind))
        if semantic_type is None:
            type_text = base_type if kind is None else f"{base_type}(kind={kind})"
            raise ValueError(f"Unsupported Fortran semantic type for variable '{var.name}': {type_text}")
        return semantic_type

    def _semantic_kind_key(self, var: FortranVariable) -> str | None:
        """Normalize the declaration's kind text for semantic type-map lookup."""
        raw_kind = var.target_kind_expression or var.kind
        if not raw_kind:
            return None

        base_type = var.base_type.lower()
        kind = self._resolve_compile_time_text(str(raw_kind)).strip().lower()
        if base_type == "character":
            return FortranToIRConverter._character_kind_key(kind, character_length_syntax=var.character_length_syntax)
        if base_type == "logical":
            return "c_bool" if kind == "c_bool" else kind
        literal_kind = FortranToIRConverter._literal_kind_key(kind)
        if literal_kind is not None:
            return literal_kind
        return kind

    def _target_type_key(self, var: FortranVariable) -> tuple[str, str | None]:
        """Return the normalized lookup key used for compiler storage facts.

        Character length syntax intentionally maps to the default character
        storage key, while explicit character kind clauses retain their kind.
        """
        base_type = var.base_type.lower()
        raw_kind = var.target_kind_expression or var.kind
        if not raw_kind:
            return base_type, None

        kind = self._resolve_compile_time_text(str(raw_kind)).strip().lower()
        if base_type == "character":
            if var.character_length_syntax:
                return base_type, None
            kind_match = re.search(r"(?:^|,)\s*kind\s*=\s*([^,]+)", kind)
            if kind_match is not None:
                kind = kind_match.group(1).strip()
            elif kind.startswith("len="):
                return base_type, None
        return base_type, kind

    @staticmethod
    def _character_kind_key(kind: str, *, character_length_syntax: bool = False) -> str | None:
        """Extract a character-kind key while ignoring length-only spellings."""
        if character_length_syntax:
            return None
        kind_match = re.search(r"(?:^|,)\s*kind\s*=\s*([^,]+)", kind)
        if kind_match is not None:
            kind = kind_match.group(1).strip()
        elif re.match(r"^len\s*=", kind):
            return None
        return kind or None

    def _target_type_fact(self, var: FortranVariable) -> dict[str, object] | None:
        """Return legacy fixed-width or configured compiler facts for ``var``."""
        if var.declared_storage_bits is not None:
            return {
                "base_type": var.base_type.lower(),
                "kind": var.kind or None,
                "bits": var.declared_storage_bits,
                "source": "legacy_star_storage",
            }
        return self.type_facts.get(self._target_type_key(var))

    @staticmethod
    def _semantic_type_from_target_fact(fact: dict[str, object]) -> str | None:
        """Map one measured intrinsic storage fact to its semantic dtype, if known."""
        base_type = str(fact.get("base_type") or "").lower()
        bits = int(fact.get("bits") or 0)
        if base_type == "character":
            return "String"
        return _FORTRAN_STORAGE_TYPE_MAP.get(base_type, {}).get(bits)

    @staticmethod
    def _literal_kind_key(kind: str) -> str | None:
        """Map a literal ``kind(...)`` real expression to its conventional width key."""
        match = re.fullmatch(r"kind\(\s*[-+]?\d+(?:\.\d*)?([edq])[-+]?\d*\s*\)", kind)
        if match is None:
            return None
        exponent_marker = match.group(1)
        if exponent_marker == "e":
            return "4"
        if exponent_marker == "d":
            return "8"
        if exponent_marker == "q":
            return "16"
        return None

    def _resolve_compile_time_text(self, text: str) -> str:
        """Resolve this converter's known compile-time values in ``text``."""
        return _resolve_compile_time_text(text, self.compile_time_values)

    @staticmethod
    def _variable_origin(var: FortranVariable) -> SemanticOrigin:
        """Create source identity metadata for a non-argument declaration."""
        return SemanticOrigin(
            source_language="fortran",
            native_name=var.name,
            source_kind="variable",
            source_type=FortranToIRConverter._fortran_source_type(var),
            metadata=FortranToIRConverter._fortran_variable_metadata(var),
        )

    @staticmethod
    def _argument_origin(arg: FortranArgument | FortranVariable) -> SemanticOrigin:
        """Create source identity metadata for a dummy argument or variable."""
        return SemanticOrigin(
            source_language="fortran",
            native_name=arg.name,
            native_scope=getattr(arg, "procedure", None),
            source_kind="argument" if isinstance(arg, FortranArgument) else "variable",
            source_type=FortranToIRConverter._fortran_source_type(arg),
            metadata=FortranToIRConverter._fortran_variable_metadata(arg),
        )

    @staticmethod
    def _data_origin(var: FortranArgument | FortranVariable, *, source_kind: str) -> SemanticOrigin:
        """Create source identity metadata for a module variable or type field."""
        return SemanticOrigin(
            source_language="fortran",
            native_name=var.name,
            native_scope=getattr(var, "module", None),
            source_kind=source_kind,
            source_type=FortranToIRConverter._fortran_source_type(var),
            metadata=FortranToIRConverter._fortran_variable_metadata(var),
        )

    @staticmethod
    def _fortran_source_type(var: FortranVariable) -> str:
        """Render the parser declaration's native Fortran type spelling for metadata."""
        if var.base_type == "derived":
            specifier = "class" if getattr(var, "polymorphic", False) else "type"
            dtype = str(var.kind or "*")
            return f"{specifier}({dtype})"
        if var.kind:
            return f"{var.base_type}(kind={var.kind})"
        return var.base_type

    @staticmethod
    def _fortran_variable_metadata(var: FortranVariable) -> dict[str, object]:
        """Return parser storage and declaration facts that semantic IR must retain."""
        metadata: dict[str, object] = {
            "rank": var.rank,
            "shape": list(var.shape),
            "lower_bounds": list(getattr(var, "lbound", []) or []),
            "upper_bounds": list(getattr(var, "ubound", []) or []),
            "allocatable": bool(getattr(var, "allocatable", False)),
            "pointer": bool(getattr(var, "pointer", False)),
            "target": bool(getattr(var, "target", False)),
            "contiguous": bool(getattr(var, "contiguous", False)),
        }
        if isinstance(var, FortranArgument):
            metadata.update(
                {
                    "optional": var.optional,
                    "value": var.pass_by_value,
                }
            )
        if getattr(var, "pointer", False):
            metadata["association"] = "runtime"
        if getattr(var, "polymorphic", False):
            metadata["polymorphic"] = True
        if getattr(var, "is_parameter", False):
            metadata["constant"] = True
        if var.declared_storage_bits is not None:
            metadata["declared_storage_bits"] = var.declared_storage_bits
        return metadata

    @staticmethod
    def _procedure_metadata(proc: FortranProcedureSignature) -> dict[str, object]:
        """Return native procedure attributes and optional bind name for semantic IR."""
        metadata: dict[str, object] = {}
        if proc.attributes:
            metadata["fortran_attributes"] = list(proc.attributes)
        if "bind(c)" in proc.attributes:
            metadata["fortran_bind_c"] = True
            if proc.bind_name:
                metadata["fortran_bind_c_name"] = proc.bind_name
        return metadata

    # Storage and argument-contract helpers

    def _array_storage_contract(
        self,
        var: FortranVariable,
        shape: list[str],
        *,
        declaration_arrays: dict[str, ArrayExpressionSource] | None = None,
    ) -> SemanticStorageContract:
        """Construct the semantic array storage contract for a parsed declaration.

        The helper derives category, axes, bounds, order, contiguity, allocation,
        and pointer facts from ``var`` and already resolved ``shape`` text.
        """
        category = self._array_category(var, shape)
        axes = self._array_axes(
            shape,
            category,
            contiguous=getattr(var, "contiguous", False),
            declaration_arrays=declaration_arrays,
        )
        rank = var.rank
        order = self._array_order(rank, category, contiguous=getattr(var, "contiguous", False))
        lower_bounds, upper_bounds = self._array_bound_metadata(shape)
        array = SemanticArrayContract(
            rank=rank,
            shape=list(axes),
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
            source_shape=list(shape),
            category=category,
            order=order,
            axes=["strided" if self._is_strided_axis(axis) else "dense" for axis in axes],
            contiguous=self._array_contiguous(category, contiguous=getattr(var, "contiguous", False)),
            allocatable=getattr(var, "allocatable", False),
            pointer=getattr(var, "pointer", False),
        )
        return SemanticStorageContract(
            kind="array",
            mutable=False,
            array=array,
        )

    def _resolve_optional_compile_time_text(self, text: str | None) -> str | None:
        """Resolve optional bound text while preserving an absent bound as ``None``."""
        if text is None:
            return None
        return self._resolve_compile_time_text(text)

    def _array_bound_metadata(self, shape: list[str]) -> tuple[list[str | None], list[str | None]]:
        """Split Fortran dimension tokens into optional lower and upper bounds.

        Default lower bound ``1`` is omitted, assumed-size ``*`` is retained as
        an upper marker, and fully absent bound lists stay empty for compatibility.
        """
        lower_bounds: list[str | None] = []
        upper_bounds: list[str | None] = []
        for dim in shape:
            token = dim.strip()
            if ":" not in token:
                lower_bounds.append(None)
                upper_bounds.append("*" if token == "*" else None)
                continue
            lower, upper = self._dimension_bounds(token)
            lower_bounds.append(None if lower in {None, "1"} else self._resolve_compile_time_text(lower))
            upper_bounds.append(self._resolve_optional_compile_time_text(upper))
        if all(value is None for value in lower_bounds):
            lower_bounds = []
        if all(value is None for value in upper_bounds):
            upper_bounds = []
        return lower_bounds, upper_bounds

    @staticmethod
    def _array_category(var: FortranVariable, shape: list[str]) -> str:
        """Classify parsed array dimensions for semantic storage metadata."""
        cleaned = [dim.strip() for dim in shape]
        if cleaned == [".."]:
            return "assumed_rank"
        if cleaned and cleaned[-1] == "*":
            return "assumed_size"
        if any(dim.endswith(":*") for dim in cleaned):
            return "assumed_size"
        if isinstance(var, FortranArgument) and (getattr(var, "allocatable", False) or getattr(var, "pointer", False)):
            return (
                "deferred_shape"
                if any(FortranToIRConverter._has_omitted_upper_bound(dim) for dim in cleaned)
                else "explicit_shape"
            )
        if any(FortranToIRConverter._has_omitted_upper_bound(dim) for dim in cleaned):
            return "assumed_shape"
        return "explicit_shape"

    @classmethod
    def _array_axes(
        cls,
        shape: list[str],
        category: str,
        *,
        contiguous: bool,
        declaration_arrays: dict[str, ArrayExpressionSource] | None = None,
    ) -> list[str]:
        """Convert native bounds into Python-form public extent expressions.

        The source ``shape`` remains unchanged elsewhere in the array contract.
        Explicit bounds are converted to extents first, then the shared
        expression layer translates Fortran inquiries and operators.
        """
        if category == "assumed_rank":
            return ["..."]
        if category == "assumed_shape" and not contiguous:
            return ["::Strided" for _dim in shape]

        axes: list[str] = []
        for dim in shape:
            token = dim.strip()
            if token == "*":
                axes.append(":")
                continue
            if token.endswith(":*"):
                axes.append(":")
                continue
            lower, upper = cls._dimension_bounds(token)
            if lower in {None, "1"} and upper:
                extent = upper
            elif lower is not None and upper is not None:
                extent = f"({upper}) - ({lower}) + 1"
            elif ":" in token:
                axes.append(":")
                continue
            else:
                extent = token
            public_extent = fortran_extent_to_python(extent, declaration_arrays)
            axes.append(canonicalize_declaration_extent(public_extent))
        return axes

    @staticmethod
    def _dimension_bounds(token: str) -> tuple[str | None, str | None]:
        """Return the lower and upper parts of one Fortran dimension token."""
        return split_dimension_bounds(token)

    @staticmethod
    def _has_omitted_upper_bound(token: str) -> bool:
        """Return whether a dimension's colon form has no explicit upper bound."""
        bounds = split_top_level_expression(token, ":")
        return len(bounds) > 1 and not ":".join(bounds[1:]).strip()

    @staticmethod
    def _array_order(rank: int, category: str, *, contiguous: bool) -> str | None:
        """Return Fortran order for multidimensional arrays and ``None`` otherwise."""
        if rank <= 1:
            return None
        return "ORDER_F"

    @staticmethod
    def _array_contiguous(category: str, *, contiguous: bool) -> bool | None:
        """Derive contiguity certainty from parser category and explicit attribute."""
        if contiguous:
            return True
        if category in {"explicit_shape", "assumed_size", "deferred_shape"}:
            return True
        if category == "assumed_shape":
            return False
        return None

    @staticmethod
    def _is_strided_axis(axis: str) -> bool:
        """Return whether an encoded public axis carries the strided marker."""
        return "Strided" in axis

    @staticmethod
    def _reference_storage_contract(*, writes_argument: bool) -> SemanticStorageContract:
        """Create the scalar by-reference contract implied by argument access."""
        read_only = not writes_argument
        return SemanticStorageContract(
            kind="reference",
            read_only=read_only,
            mutable=not read_only,
            pointer_depth=1,
        )

    @staticmethod
    def _scalar_storage_contract(*, writes_argument: bool) -> SemanticStorageContract:
        """Create the rank-zero descriptor contract used for writable optional scalars."""
        read_only = not writes_argument
        return SemanticStorageContract(
            kind="array",
            read_only=read_only,
            mutable=not read_only,
            array=SemanticArrayContract(
                rank=0,
                shape=[],
                category=SCALAR_STORAGE_CATEGORY,
            ),
        )

    @staticmethod
    def _apply_array_argument_contract(
        semantic_type: SemanticType,
        arg: FortranArgument | FortranVariable,
        *,
        writes_argument: bool,
    ) -> None:
        """Apply argument mutability and array declaration facts in place.

        ``semantic_type`` must already carry an array storage contract.  Missing
        storage is intentionally ignored, preserving callers that cannot form
        an array contract for unsupported declarations.
        """
        if semantic_type.storage is None:
            return
        read_only = not writes_argument
        semantic_type.storage.read_only = read_only
        semantic_type.storage.mutable = not read_only
        if semantic_type.storage.array is not None:
            semantic_type.storage.array.allocatable = getattr(arg, "allocatable", False)
            semantic_type.storage.array.pointer = getattr(arg, "pointer", False)
            if getattr(arg, "contiguous", False):
                semantic_type.storage.array.contiguous = True

    @staticmethod
    def _add_variable_constraints(semantic_type: SemanticType, var: FortranVariable) -> None:
        """Append declaration-implied constraints to ``semantic_type`` in place."""
        if getattr(var, "is_parameter", False):
            semantic_type.constraints.append(SemanticConstraint("Constant"))

    @staticmethod
    def _apply_argument_ownership(semantic_type: SemanticType, *, writes_argument: bool) -> None:
        """Record argument mutability on the already constructed ownership metadata."""
        semantic_type.ownership.mutable = writes_argument

    @staticmethod
    def _apply_pointer_input_policy(semantic_type: SemanticType) -> None:
        """Record the existing caller-owned policy for a non-writing pointer input."""
        set_ownership_metadata(
            semantic_type.metadata,
            owner="caller",
            transfer="call_local",
            destruction="none" if semantic_type.rank > 0 else "call_local",
        )

    @staticmethod
    def _apply_pointer_result_policy(semantic_type: SemanticType) -> None:
        """Record the existing Python snapshot policy for a scalar pointer result."""
        if semantic_type.rank > 0:
            return
        set_ownership_metadata(
            semantic_type.metadata,
            owner="python",
            transfer="snapshot_copy",
            destruction="python_refcount",
        )

    @staticmethod
    def _argument_access(
        arg: FortranArgument | FortranVariable,
        semantic_type: SemanticType,
    ) -> tuple[bool, bool]:
        """Return parser-provided read/write facts or the established conservative default."""
        reads = getattr(arg, "reads_argument", None)
        writes = getattr(arg, "writes_argument", None)
        if reads is None or writes is None:
            if semantic_type.name == "String" and semantic_type.rank == 0:
                return True, False
            return True, True
        return bool(reads), bool(writes)

    @staticmethod
    def _argument_has_writable_storage(argument: SemanticArgument) -> bool:
        """Return whether semantic ownership or storage marks an argument writable."""
        storage = argument.semantic_type.storage
        return bool(
            argument.semantic_type.ownership.mutable
            or (storage is not None and (storage.mutable or not storage.read_only))
        )

    # Derived-type binding and generic-interface helpers

    def _bound_methods(
        self,
        dtype: FortranDerivedType,
        procedure_lookup: dict[str, SemanticFunction],
    ) -> list[SemanticMethod]:
        """Project resolved type-bound procedure bindings into semantic methods.

        Procedures missing from ``procedure_lookup`` are ignored as before.
        For matched bindings, this marks the original procedure as type-bound,
        then copies the relevant signature and binding-only metadata into a
        method without leaking temporary mutation into the method metadata.
        """
        methods: list[SemanticMethod] = []
        bindings = getattr(dtype, "procedure_bindings", ()) or [
            {"name": method_name, "attrs": []} for method_name in dtype.methods
        ]
        for binding in bindings:
            binding_name, target_name = self._procedure_binding_names(binding["name"])
            proc = procedure_lookup.get(target_name.casefold())
            if proc is None:
                continue
            binding_attributes = tuple(binding.get("attrs", ()))
            attrs = set(binding_attributes)
            visibility = proc.visibility
            if "private" in attrs:
                visibility = "private"
            elif "public" in attrs:
                visibility = "public"
            is_static = "nopass" in attrs
            passed_object_name, passed_object_position = self._passed_object_argument(proc, binding_attributes)
            proc.metadata["fortran_type_bound_target"] = True
            proc.metadata["fortran_passed_object_name"] = passed_object_name
            proc.metadata["fortran_passed_object_position"] = passed_object_position
            method_metadata = dict(proc.metadata)
            method_metadata.pop("fortran_type_bound_target", None)
            method_metadata.pop("fortran_passed_object_name", None)
            method_metadata.pop("fortran_passed_object_position", None)
            methods.append(
                SemanticMethod(
                    name=binding_name,
                    native_name=proc.native_name,
                    arguments=proc.arguments,
                    return_type=proc.return_type,
                    contracts=proc.contracts,
                    projection=proc.projection,
                    metadata=method_metadata,
                    visibility=visibility,
                    is_static=is_static,
                    passed_object_name=passed_object_name,
                    passed_object_position=passed_object_position,
                    binding_attributes=binding_attributes,
                    origin=proc.origin,
                )
            )
        return methods

    def _module_overload_sets(
        self,
        module: FortranModule,
        procedure_lookup: dict[str, SemanticFunction],
        context: _DerivedTypeContext,
        semantic_classes: list[SemanticClass],
    ) -> list[ProcedureOverloadSet]:
        """Convert module generic interfaces into function or class overload sets.

        Normal procedure generics remain module overloads.  Defined operators
        and assignment are attached to their derived classes, while unsupported
        constructors preserve the existing descriptive conversion failure.
        """
        overload_sets: list[ProcedureOverloadSet] = []
        class_map = {semantic_class.name.casefold(): semantic_class for semantic_class in semantic_classes}
        for interface in module.interfaces:
            if not interface.name or interface.abstract:
                continue
            inline_lookup = {
                signature.name.casefold(): self.visit(
                    signature,
                    visibility=self._symbol_visibility(module, signature.name),
                    derived_type_context=context,
                )
                for signature in interface.procedures
            }
            target_names = interface.specific_procedures or [signature.name for signature in interface.procedures]
            procedures, missing = self._resolve_overload_targets(
                target_names,
                procedure_lookup | inline_lookup,
                visibility=self._symbol_visibility(module, interface.name),
            )
            if missing or not procedures:
                if self._is_procedure_generic_name(interface.name):
                    overload_sets.append(ProcedureOverloadSet(interface.name))
                continue
            if self._is_procedure_generic_name(interface.name):
                if interface.name.casefold() in class_map:
                    raise ValueError(
                        f"Fortran semantic conversion cannot represent generic constructor "
                        f"{module.name}.{interface.name!s}; constructor projection is not implemented"
                    )
                overload_set = self._normal_overload_set(interface.name, procedures)
                target_lookup = procedure_lookup | inline_lookup
                for target_name, candidate in zip(target_names, overload_set.procedures, strict=True):
                    if target_lookup[target_name.casefold()].visibility == "private":
                        candidate.native_name = interface.name
                        candidate.metadata[BIND_TARGET_METADATA] = interface.name
                overload_sets.append(overload_set)
                continue
            defined_sets = self._defined_overload_sets(
                interface.name,
                procedures,
                class_map,
            )
            self._apply_assignment_projection_to_originals(interface.name, procedures, procedure_lookup, class_map)
            for semantic_class, class_sets in defined_sets:
                self._merge_overload_sets(semantic_class.overload_sets, class_sets)
        return overload_sets

    def _bound_overload_sets(
        self,
        dtype: FortranDerivedType,
        methods: list[SemanticMethod],
    ) -> list[ProcedureOverloadSet]:
        """Convert a derived type's generic bindings into method overload sets.

        Resolved method targets keep binding visibility; malformed or missing
        generic targets preserve the previous empty-placeholder behavior for
        ordinary procedure names and are otherwise omitted.
        """
        lookup = {method.name.casefold(): method for method in methods}
        overload_sets: list[ProcedureOverloadSet] = []
        for binding in dtype.generic_bindings:
            name = str(binding["name"])
            attrs = {str(attr).casefold() for attr in binding.get("attrs", ())}
            visibility = "private" if "private" in attrs else "public" if "public" in attrs else None
            procedures, missing = self._resolve_overload_targets(
                list(binding.get("targets", ())),
                lookup,
                visibility=visibility,
            )
            if missing or not procedures:
                if self._is_procedure_generic_name(name):
                    overload_sets.append(ProcedureOverloadSet(name))
                continue
            if self._is_procedure_generic_name(name):
                overload_set = self._normal_overload_set(name, procedures)
                for target_name, candidate in zip(binding.get("targets", ()), overload_set.procedures, strict=True):
                    if lookup[target_name.casefold()].visibility == "private":
                        candidate.native_name = name
                        candidate.metadata[BIND_TARGET_METADATA] = name
                overload_sets.append(overload_set)
                continue
            placeholder = SemanticClass(dtype.name)
            defined_sets = self._defined_overload_sets(
                name,
                procedures,
                {dtype.name.casefold(): placeholder},
            )
            self._apply_assignment_projection_to_originals(
                name,
                procedures,
                lookup,
                {dtype.name.casefold(): placeholder},
            )
            self._merge_overload_sets(overload_sets, defined_sets[0][1] if defined_sets else ())
        return overload_sets

    def _apply_assignment_projection_to_originals(
        self,
        generic_name: str,
        procedures: list[SemanticFunction],
        lookup: dict[str, SemanticFunction],
        classes: dict[str, SemanticClass],
    ) -> None:
        """Replace valid defined-assignment projections on their original procedures.

        The generic candidates are only a view; this mutates the matching
        original lookup entry so later consumers see the same bound-object
        result projection as the defined-assignment overload.
        """
        kind, token = self._defined_generic_identity(generic_name)
        if kind != "assignment":
            return
        for procedure in procedures:
            if self._defined_procedure_error(kind, token, procedure, classes) is not None:
                continue
            original = lookup.get((procedure.native_name or procedure.name).casefold())
            if original is not None:
                original.projection = self._assignment_projection(original, 0)

    @staticmethod
    def _merge_overload_sets(
        overload_sets: list[ProcedureOverloadSet],
        incoming: list[ProcedureOverloadSet],
    ) -> None:
        """Append incoming overload candidates to matching named sets in place."""
        for overload_set in incoming:
            existing = next((item for item in overload_sets if item.name == overload_set.name), None)
            if existing is None:
                overload_sets.append(overload_set)
            else:
                existing.procedures.extend(overload_set.procedures)

    @staticmethod
    def _normal_overload_set(name: str, procedures: list[SemanticFunction]) -> ProcedureOverloadSet:
        """Copy regular generic candidates and attach generic dispatch metadata.

        Type-bound methods are projected back to ordinary functions while
        retaining their bound-object position or static flag in metadata.
        """
        candidates = []
        for procedure in procedures:
            candidate = deepcopy(procedure)
            if isinstance(candidate, SemanticMethod):
                bound_position = candidate.passed_object_position
                is_static = candidate.is_static
                candidate = SemanticFunction(
                    name=candidate.native_name or candidate.name,
                    native_name=candidate.native_name,
                    arguments=candidate.arguments,
                    return_type=candidate.return_type,
                    locals=candidate.locals,
                    contracts=candidate.contracts,
                    projection=candidate.projection,
                    metadata=candidate.metadata,
                    visibility=candidate.visibility,
                    origin=candidate.origin,
                )
                if bound_position is not None:
                    candidate.metadata[PYTHON_BOUND_POSITION_METADATA] = bound_position
                if is_static:
                    candidate.metadata[PYTHON_STATIC_METADATA] = True
            candidate.metadata[FORTRAN_GENERIC_NAME_METADATA] = name
            candidate.metadata[OVERLOAD_KIND_METADATA] = "generic"
            candidate.metadata[OVERLOAD_TARGET_METADATA] = candidate.native_name or candidate.name
            candidates.append(candidate)
        return ProcedureOverloadSet(name, candidates)

    def _defined_overload_sets(
        self,
        generic_name: str,
        procedures: list[SemanticFunction],
        classes: dict[str, SemanticClass],
    ) -> list[tuple[SemanticClass, list[ProcedureOverloadSet]]]:
        """Map valid defined operators or assignments onto affected semantic classes.

        Candidates failing the existing representation checks are skipped.  For
        valid assignment interfaces the candidate projection is changed to
        return the passed object before its class-local overload set is built.
        """
        grouped: dict[str, tuple[SemanticClass, dict[str, ProcedureOverloadSet]]] = {}
        kind, token = self._defined_generic_identity(generic_name)
        if kind is None:
            return []

        for procedure in procedures:
            error = self._defined_procedure_error(kind, token, procedure, classes)
            if error is not None:
                continue
            python_bindings = self._defined_python_bindings(
                kind,
                token,
                procedure,
                classes,
            )
            if kind == "assignment" and python_bindings:
                procedure.projection = self._assignment_projection(procedure, python_bindings[0][3])
            for semantic_class, set_name, method_name, bound_position in python_bindings:
                _, class_sets = grouped.setdefault(semantic_class.name.casefold(), (semantic_class, {}))
                overload_set = class_sets.setdefault(set_name, ProcedureOverloadSet(set_name))
                candidate = self._defined_overload_candidate(
                    procedure,
                    generic_name=generic_name,
                    kind=kind,
                    method_name=method_name,
                    bound_position=bound_position,
                )
                overload_set.procedures.append(candidate)
        return [(semantic_class, list(items.values())) for semantic_class, items in grouped.values()]

    @staticmethod
    def _defined_generic_identity(name: str) -> tuple[str | None, str]:
        """Classify a Fortran defined generic spelling and return its normalized token."""
        compact = re.sub(r"\s+", "", name).casefold()
        if compact == "assignment(=)":
            return "assignment", "="
        match = re.fullmatch(r"operator\((.+)\)", compact)
        if match is None:
            return None, ""
        token = match.group(1)
        intrinsic_aliases = {
            ".eq.": "==",
            ".ne.": "/=",
            ".lt.": "<",
            ".le.": "<=",
            ".gt.": ">",
            ".ge.": ">=",
        }
        token = intrinsic_aliases.get(token, token)
        if (
            token.startswith(".")
            and token.endswith(".")
            and token
            not in {
                ".and.",
                ".or.",
                ".not.",
                ".eqv.",
                ".neqv.",
            }
        ):
            return "named_operator", token[1:-1]
        if token in {*_BINARY_OPERATOR_METHODS, *_UNARY_OPERATOR_METHODS, *_COMPARISON_OPERATOR_METHODS}:
            return "operator", token
        return None, token

    @staticmethod
    def _defined_procedure_error(
        kind: str,
        token: str,
        procedure: SemanticFunction,
        classes: dict[str, SemanticClass],
    ) -> str | None:
        """Return the representation error for a defined generic, or ``None`` when valid."""
        arguments = procedure.arguments
        if kind == "assignment":
            if len(arguments) != 2 or procedure.return_type is not None:
                return "defined assignment must be a subroutine with exactly two dummy arguments"
            lhs = arguments[0]
            if lhs.semantic_type.name.casefold() not in classes:
                return "defined assignment left-hand side must be a wrapped derived type"
            if not FortranToIRConverter._argument_has_writable_storage(lhs):
                return "defined assignment left-hand side must be writable"
            if FortranToIRConverter._argument_has_writable_storage(arguments[1]):
                return "defined assignment right-hand side must be read-only"
            return None

        expected_arities = (
            {1, 2} if token in {"+", "-"} or kind == "named_operator" else {1} if token == ".not." else {2}
        )
        if len(arguments) not in expected_arities or procedure.return_type is None:
            return f"defined operator {token!r} must be a function with {sorted(expected_arities)} operand count"
        if not any(argument.semantic_type.name.casefold() in classes for argument in arguments):
            return "defined operator must have at least one wrapped derived-type operand"
        if token in _COMPARISON_OPERATOR_METHODS and not is_boolean_semantic_type_name(procedure.return_type.dtype):
            return "defined relational operator must return Bool"
        return None

    def _defined_python_bindings(
        self,
        kind: str,
        token: str,
        procedure: SemanticFunction,
        classes: dict[str, SemanticClass],
    ) -> list[tuple[SemanticClass, str, str, int]]:
        """Return class, overload-set, method, and bound-position projections for a generic.

        Assignment maps to ``assign`` on its left-hand derived type.  Operators
        are emitted for each distinct derived-type operand, preserving reflected
        and comparison method naming rules.
        """
        if kind == "assignment":
            semantic_class = classes[procedure.arguments[0].semantic_type.name.casefold()]
            return [(semantic_class, "assign", "assign", 0)]

        bindings: list[tuple[SemanticClass, str, str, int]] = []
        class_positions = [
            (position, classes[argument.semantic_type.name.casefold()])
            for position, argument in enumerate(procedure.arguments)
            if argument.semantic_type.name.casefold() in classes
        ]
        seen_classes: set[str] = set()
        for position, semantic_class in class_positions:
            class_key = semantic_class.name.casefold()
            if class_key in seen_classes:
                continue
            seen_classes.add(class_key)
            if len(procedure.arguments) == 1:
                method_name = f"operator_{token}" if kind == "named_operator" else _UNARY_OPERATOR_METHODS[token]
                bindings.append((semantic_class, method_name, method_name, position))
                continue
            if kind == "named_operator":
                method_name = f"{'r_' if position == 1 else ''}operator_{token}"
                bindings.append((semantic_class, method_name, method_name, position))
                continue
            if token in _COMPARISON_OPERATOR_METHODS:
                method_name = _COMPARISON_OPERATOR_METHODS[token][position]
                bindings.append((semantic_class, method_name, method_name, position))
                continue
            direct_name, reflected_name = _BINARY_OPERATOR_METHODS[token]
            method_name = direct_name if position == 0 else reflected_name
            bindings.append((semantic_class, direct_name, method_name, position))
        return bindings

    @staticmethod
    def _defined_overload_candidate(
        procedure: SemanticFunction,
        *,
        generic_name: str,
        kind: str,
        method_name: str,
        bound_position: int,
    ) -> SemanticFunction:
        """Copy a generic candidate and attach its overload and binding metadata."""
        candidate = deepcopy(procedure)
        candidate.metadata[FORTRAN_GENERIC_NAME_METADATA] = generic_name
        candidate.metadata[OVERLOAD_KIND_METADATA] = (
            "comparison"
            if method_name
            in {
                "__eq__",
                "__ne__",
                "__lt__",
                "__le__",
                "__gt__",
                "__ge__",
            }
            else kind
        )
        candidate.metadata[OVERLOAD_TARGET_METADATA] = candidate.native_name or candidate.name
        candidate.metadata[PYTHON_METHOD_NAME_METADATA] = method_name
        candidate.metadata[PYTHON_BOUND_POSITION_METADATA] = bound_position
        if kind == "assignment":
            candidate.projection = FortranToIRConverter._assignment_projection(candidate, bound_position)

        return FortranToIRConverter._as_semantic_function(candidate)

    @staticmethod
    def _assignment_projection(procedure: SemanticFunction, bound_position: int) -> list[ProjectionMapping]:
        """Return ``procedure`` projection with its assigned object as result zero.

        Native order is preserved; visible Python argument positions are
        recomputed around hidden outputs, and copied mapping values prevent
        mutation of the original projection.
        """
        projection = []
        python_position = 0
        for mapping in sorted(procedure.projection, key=lambda item: item.native_position or 0):
            native_position = mapping.native_position
            if native_position == bound_position:
                projection.append(
                    ProjectionMapping(
                        python_name=mapping.python_name,
                        native_name=mapping.native_name,
                        native_position=native_position,
                        python_position=python_position,
                        result_position=0,
                        value_kind=mapping.value_kind,
                        value=deepcopy(mapping.value),
                    )
                )
                python_position += 1
                continue
            is_hidden = native_position is not None and mapping.python_position is None
            projection.append(
                ProjectionMapping(
                    python_name=mapping.python_name,
                    native_name=mapping.native_name,
                    native_position=native_position,
                    python_position=None if is_hidden else python_position,
                    result_position=mapping.result_position,
                    value_kind=mapping.value_kind,
                    value=deepcopy(mapping.value),
                )
            )
            if not is_hidden:
                python_position += 1
        return projection

    @staticmethod
    def _as_semantic_function(procedure: SemanticFunction) -> SemanticFunction:
        """Copy a procedure-like candidate into the plain function representation used by overloads."""
        return SemanticFunction(
            name=procedure.native_name or procedure.name,
            native_name=procedure.native_name,
            arguments=procedure.arguments,
            return_type=procedure.return_type,
            locals=procedure.locals,
            contracts=procedure.contracts,
            projection=procedure.projection,
            metadata=procedure.metadata,
            visibility=procedure.visibility,
            origin=procedure.origin,
        )

    @staticmethod
    def _is_procedure_generic_name(name: str) -> bool:
        """Return whether a generic spelling is an ordinary callable identifier."""
        return re.fullmatch(r"[a-z_]\w*", name, re.IGNORECASE) is not None

    @staticmethod
    def _resolve_overload_targets(
        target_names: list[str],
        procedure_lookup: dict[str, SemanticFunction],
        *,
        visibility: str | None,
    ) -> tuple[list[SemanticFunction], list[str]]:
        """Copy resolved generic targets and list target names absent from ``procedure_lookup``."""
        procedures: list[SemanticFunction] = []
        missing: list[str] = []
        for target_name in target_names:
            procedure = procedure_lookup.get(target_name.casefold())
            if procedure is None:
                missing.append(target_name)
                continue
            candidate = deepcopy(procedure)
            if visibility is not None:
                candidate.visibility = visibility
            procedures.append(candidate)
        return procedures, missing

    @staticmethod
    def _passed_object_argument(
        proc: SemanticFunction,
        binding_attributes: tuple[str, ...],
    ) -> tuple[str | None, int | None]:
        """Identify a type-bound procedure's passed-object argument and position.

        ``nopass`` returns no object.  An omitted ``pass`` attribute defaults to
        the first argument; explicit missing names keep the established
        :class:`ValueError` diagnostics.
        """
        if "nopass" in binding_attributes:
            return None, None

        pass_name = None
        for attribute in binding_attributes:
            match = re.fullmatch(r"pass(?:\(\s*([a-z_]\w*)\s*\))?", attribute, re.IGNORECASE)
            if match:
                pass_name = match.group(1)
                break

        if pass_name is None:
            if not proc.arguments:
                raise ValueError(f"Type-bound procedure {proc.name!r} has no passed-object dummy argument")
            return proc.arguments[0].name, 0

        for position, argument in enumerate(proc.arguments):
            if argument.name.casefold() == pass_name.casefold():
                return argument.name, position
        raise ValueError(
            f"Type-bound procedure {proc.name!r} declares pass({pass_name}), but that dummy argument is not present"
        )

    @staticmethod
    def _procedure_binding_names(name: str) -> tuple[str, str]:
        """Split a Fortran binding ``local => target`` spelling into both names."""
        if "=>" not in name:
            return name.strip(), name.strip()
        binding_name, target_name = name.split("=>", 1)
        return binding_name.strip(), target_name.strip()

    @staticmethod
    def _projected_procedure_arguments(proc: FortranProcedureSignature) -> list[FortranArgument]:
        """Return procedure dummies with required arguments preceding optional ones."""
        args = list(proc.arguments)
        return [
            *[arg for arg in args if not getattr(arg, "optional", False)],
            *[arg for arg in args if getattr(arg, "optional", False)],
        ]

    @staticmethod
    def _is_returned_output_argument(
        *,
        is_output: bool,
        semantic_type: SemanticType | None,
        is_primitive_scalar_replacement: bool,
        is_allocatable_replacement: bool,
        is_character_replacement: bool,
        is_descriptor_replacement: bool,
    ) -> bool:
        """Return whether an output/replacement must be exposed as a Python result."""
        if (
            is_primitive_scalar_replacement
            or is_allocatable_replacement
            or is_character_replacement
            or is_descriptor_replacement
        ):
            return True
        if not is_output or semantic_type is None:
            return False
        return FortranToIRConverter._is_python_value_scalar_output(
            semantic_type
        ) or FortranToIRConverter._is_native_descriptor_output(semantic_type)

    @staticmethod
    def _is_hidden_output_argument(
        native_arg: FortranArgument,
        *,
        is_output: bool,
        semantic_type: SemanticType | None,
    ) -> bool:
        """Return whether a nonoptional pure-output dummy is hidden from Python input."""
        if not is_output or getattr(native_arg, "optional", False):
            return False
        return (
            FortranToIRConverter._is_python_value_scalar_output(semantic_type)
            or FortranToIRConverter._is_native_descriptor_output(semantic_type)
            or FortranToIRConverter._is_scalar_descriptor(semantic_type)
        )

    @staticmethod
    def _procedure_projection(
        proc: FortranProcedureSignature,
        arguments: list[SemanticArgument],
    ) -> list[ProjectionMapping]:
        """Build native-to-Python argument and result mappings for one procedure.

        The existing flow classifies each dummy's access and storage form, marks
        returned outputs, assigns stable Python/result positions, and records
        descriptor or by-value projection details consumed by later stages.
        """
        by_name = {arg.name: arg for arg in arguments}

        projection: list[ProjectionMapping] = []
        python_position = 0
        result_position = 1 if proc.result is not None else 0
        for native_position, native_arg in enumerate(proc.arguments):
            arg = by_name[native_arg.name]
            reads_argument, writes_argument = FortranToIRConverter._argument_access(native_arg, arg.semantic_type)
            is_output = writes_argument and not reads_argument
            is_replacement = reads_argument and writes_argument
            is_allocatable_replacement = is_replacement and FortranToIRConverter._is_allocatable_array(
                arg.semantic_type
            )
            is_character_replacement = is_replacement and FortranToIRConverter._is_scalar_character(arg.semantic_type)
            is_descriptor_replacement = is_replacement and FortranToIRConverter._is_scalar_descriptor(arg.semantic_type)
            is_primitive_scalar_replacement = is_replacement and FortranToIRConverter._is_primitive_scalar_replacement(
                arg.semantic_type
            )
            is_returned_output = FortranToIRConverter._is_returned_output_argument(
                is_output=is_output,
                semantic_type=arg.semantic_type,
                is_primitive_scalar_replacement=is_primitive_scalar_replacement,
                is_allocatable_replacement=is_allocatable_replacement,
                is_character_replacement=is_character_replacement,
                is_descriptor_replacement=is_descriptor_replacement,
            )
            is_hidden_output = FortranToIRConverter._is_hidden_output_argument(
                native_arg,
                is_output=is_output,
                semantic_type=arg.semantic_type,
            )
            mapping_python_position = None if is_hidden_output else python_position
            mapping_result_position = result_position if is_returned_output else None
            descriptor_kind = FortranToIRConverter._scalar_descriptor_kind(arg.semantic_type)
            descriptor_value = FortranToIRConverter._scalar_descriptor_projection_value(
                arg.name,
                descriptor_kind=descriptor_kind,
                python_position=mapping_python_position,
                result_position=mapping_result_position,
            )
            if is_returned_output:
                arg.metadata[PROJECTED_OUTPUT_METADATA] = True
            projection.append(
                ProjectionMapping(
                    python_name=arg.name,
                    native_name=native_arg.name,
                    native_position=native_position,
                    python_position=mapping_python_position,
                    result_position=mapping_result_position,
                    value_kind=("value" if arg.metadata.get(NATIVE_BY_VALUE_METADATA) else descriptor_kind or ""),
                    value=(
                        {"kind": "arg", "position": mapping_python_position}
                        if arg.metadata.get(NATIVE_BY_VALUE_METADATA)
                        else descriptor_value
                    ),
                )
            )
            if is_returned_output:
                result_position += 1
            if not is_hidden_output:
                python_position += 1
        return projection

    @staticmethod
    def _is_allocatable_array(semantic_type: SemanticType | None) -> bool:
        """Return whether a semantic type has allocatable array storage."""
        return bool(
            semantic_type is not None
            and semantic_type.storage is not None
            and semantic_type.storage.array is not None
            and semantic_type.storage.array.allocatable
        )

    @staticmethod
    def _is_native_descriptor_output(semantic_type: SemanticType | None) -> bool:
        """Return whether output storage uses an allocatable, pointer, or scalar descriptor."""
        if semantic_type is None:
            return False
        if FortranToIRConverter._is_scalar_descriptor(semantic_type):
            return True
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        return bool(array is not None and (array.allocatable or array.pointer))

    @staticmethod
    def _is_scalar_descriptor(semantic_type: SemanticType | None) -> bool:
        """Return whether a rank-zero type is represented by an allocatable or pointer descriptor."""
        return bool(
            semantic_type is not None
            and semantic_type.rank == 0
            and (semantic_type.metadata.get("fortran_allocatable") or semantic_type.metadata.get("fortran_pointer"))
        )

    @staticmethod
    def _is_primitive_scalar_replacement(semantic_type: SemanticType | None) -> bool:
        """Return whether a mutable rank-zero primitive is returned as a replacement value."""
        return bool(
            semantic_type is not None
            and semantic_type.rank == 0
            and semantic_type.name != "String"
            and semantic_type.name in SEMANTIC_SCALAR_TYPE_NAMES
            and not FortranToIRConverter._is_scalar_descriptor(semantic_type)
        )

    @staticmethod
    def _scalar_descriptor_kind(semantic_type: SemanticType | None) -> str | None:
        """Return the ABI-relevant descriptor kind for one rank-zero value."""
        if semantic_type is None or semantic_type.rank != 0:
            return None
        allocatable = bool(semantic_type.metadata.get("fortran_allocatable"))
        pointer = bool(semantic_type.metadata.get("fortran_pointer"))
        if allocatable and pointer:
            return None
        if allocatable:
            return "allocatable"
        if pointer:
            return "pointer"
        return None

    @staticmethod
    def _scalar_descriptor_projection_value(
        name: str,
        *,
        descriptor_kind: str | None,
        python_position: int | None,
        result_position: int | None,
    ) -> dict[str, int | str] | None:
        """Record the explicit argument/return reference wrapped by a descriptor helper."""
        if descriptor_kind is None:
            return None
        if python_position is not None:
            return {"kind": "arg", "position": python_position}
        if result_position is not None:
            return {"kind": "return", "name": name, "position": result_position}
        raise ValueError(f"Scalar descriptor {name!r} has no Python argument or result projection")

    @staticmethod
    def _is_python_value_scalar_output(semantic_type: SemanticType | None) -> bool:
        """Return whether a rank-zero non-descriptor maps directly to a Python value."""
        return bool(
            semantic_type is not None
            and semantic_type.rank == 0
            and not FortranToIRConverter._is_scalar_descriptor(semantic_type)
            and (semantic_type.name == "String" or semantic_type.name in SEMANTIC_SCALAR_TYPE_NAMES)
        )

    @staticmethod
    def _is_scalar_character(semantic_type: SemanticType | None) -> bool:
        """Return whether ``semantic_type`` is a rank-zero semantic string."""
        return bool(semantic_type is not None and semantic_type.rank == 0 and semantic_type.name == "String")

    @staticmethod
    def _base_classes(dtype: FortranDerivedType) -> list[str]:
        """Return the optional Fortran extension parent as semantic class names."""
        if not dtype.extends:
            return []
        if isinstance(dtype.extends, str):
            return [dtype.extends]
        return [dtype.extends.name]

    @staticmethod
    def _standalone_module_name(parsed_file: FortranFile) -> str:
        """Choose the stable synthetic module name for file-level procedures."""
        if parsed_file.filename:
            return Path(parsed_file.filename).stem
        return "standalone"

    @staticmethod
    def _symbol_visibility(module: FortranModule, symbol_name: str) -> str:
        """Resolve explicit private/public lists before the module default visibility."""
        lname = symbol_name.lower()
        public_set = {s.lower() for s in getattr(module, "public_symbols", [])}
        private_set = {s.lower() for s in getattr(module, "private_symbols", [])}
        if lname in private_set:
            return "private"
        if lname in public_set:
            return "public"
        return getattr(module, "default_visibility", "public")


# Compile-time requirement collection and specialization


def _requirement_unit_name(
    *,
    module: str | None = None,
    unit_name: str | None = None,
) -> str:
    """Return a diagnostic unit label from optional module and local-unit names."""
    if module and unit_name:
        return f"{module}.{unit_name}"
    return unit_name or module or "<source>"


def _iter_fortran_variable_contexts(
    node,
    *,
    module_name: str | None = None,
    unit_kind: str = "file",
    unit_name: str | None = None,
):
    """Yield parser variables with enough unit context for diagnostics.

    Example:
        ``list(_iter_fortran_variable_contexts(parsed_file))`` returns module
        parameters, procedure arguments/results/locals, and type fields with
        the unit that owns each symbol.
    """
    yield from _FortranVariableContextVisitor()._visit(
        node,
        module_name=module_name,
        unit_kind=unit_kind,
        unit_name=unit_name,
    )


class _FortranVariableContextVisitor(ClassVisitor):
    """Traverse parsed Fortran models through the shared class visitor protocol."""

    def _visit_FortranProject(self, node: FortranProject, **_context):
        """Yield variable contexts from every project file."""
        for parsed_file in node.files:
            yield from self._visit(parsed_file)

    def _visit_FortranFile(self, node: FortranFile, **_context):
        """Yield file, module, and standalone variable contexts."""
        file_unit = node.filename or "<source>"
        for variable in getattr(node, "variables", []):
            yield _variable_context(variable, unit_kind="file", unit=file_unit, module=None, role="variable")
        collections = (
            node.modules,
            node.submodules,
            node.programs,
            node.block_data_units,
            node.procedures,
            node.derived_types,
        )
        for collection in collections:
            for child in collection:
                yield from self._visit(child)

    def _visit_FortranModule(self, node: FortranModule, **_context):
        """Yield module-owned variable contexts."""
        yield from self._module_variable_contexts(node, unit_kind="module")

    def _visit_FortranSubmodule(self, node: FortranSubmodule, **_context):
        """Yield submodule-owned variable contexts."""
        yield from self._module_variable_contexts(node, unit_kind="submodule")

    def _visit_FortranProgram(self, node: FortranProgram, **_context):
        """Yield program-owned variable contexts."""
        owner = node.name or "<program>"
        for variable in node.variables:
            yield _variable_context(variable, unit_kind="program", unit=owner, module=None, role="variable")
        for procedure in node.procedures:
            yield from self._visit(procedure, unit_kind="program", unit_name=owner)

    @staticmethod
    def _visit_FortranBlockData(node: FortranBlockData, **_context):
        """Yield block-data variable contexts."""
        owner = node.name or "<block_data>"
        for variable in node.variables:
            yield _variable_context(variable, unit_kind="block_data", unit=owner, module=None, role="variable")

    @staticmethod
    def _visit_FortranProcedureSignature(
        node: FortranProcedureSignature,
        *,
        module_name: str | None = None,
        **_context,
    ):
        """Yield procedure argument, result, and local contexts."""
        procedure_module = module_name or node.module
        owner = _requirement_unit_name(module=procedure_module, unit_name=node.name)
        context = {
            "unit_kind": "procedure",
            "unit": owner,
            "module": procedure_module,
            "procedure": node.name,
        }
        for argument in node.arguments:
            yield _variable_context(argument, **context, role="argument")
        if node.result is not None:
            yield _variable_context(node.result, **context, role="result")
        for variable in node.variables.values():
            yield _variable_context(variable, **context, role="variable")

    @staticmethod
    def _visit_FortranDerivedType(
        node: FortranDerivedType,
        *,
        module_name: str | None = None,
        **_context,
    ):
        """Yield derived-type field contexts."""
        owner_module = module_name or node.module
        owner = _requirement_unit_name(module=owner_module, unit_name=node.name)
        for field in node.fields:
            yield _variable_context(
                field,
                unit_kind="derived_type",
                unit=owner,
                module=owner_module,
                type_owner=node.name,
                role="field",
            )

    def _module_variable_contexts(
        self,
        node: FortranModule | FortranSubmodule,
        *,
        unit_kind: str,
    ):
        """Yield variable, procedure, and type contexts owned by a module-like node."""
        owner = node.name
        for variable in node.variables:
            yield _variable_context(variable, unit_kind=unit_kind, unit=owner, module=owner, role="variable")
        for procedure in node.procedures:
            yield from self._visit(procedure, module_name=owner)
        for derived_type in node.derived_types:
            yield from self._visit(derived_type, module_name=owner)


def _variable_context(variable, *, unit_kind, unit, module, role, **extra):
    """Pair one parser variable with the stable diagnostic context used by collectors."""
    return variable, {
        "unit_kind": unit_kind,
        "unit": unit,
        "module": module,
        **extra,
        "symbol": variable.name,
        "role": role,
    }


def _compile_time_requirement_message(code: str, symbol: str, expression: str) -> str:
    """Build the existing user-facing message for one unresolved-value requirement."""
    if code == "parameter_value":
        return f"Parameter '{symbol}' needs a compile-time value for expression '{expression}'."
    if code == "unsupported_kind":
        return f"Kind expression for '{symbol}' needs a supported compile-time value."
    return f"Compile-time value required for '{symbol}'."


def fortran_type_storage_expression(base_type: str, kind: str | None = None) -> str:
    """Return the Fortran ``storage_size`` expression for one intrinsic type.

    Use this when executing a requirement returned by
    :func:`collect_fortran_type_storage_requirements` with a target compiler.
    ``base_type`` must be an integer, real, complex, or logical intrinsic;
    unsupported probe types raise :class:`ValueError`.

    Example:
        >>> fortran_type_storage_expression("real", "8")
        'storage_size(real(0.0,kind=8))'
    """
    constructors = {
        "integer": "int(0)",
        "real": "real(0.0)",
        "complex": "cmplx(0.0)",
        "logical": "logical(.false.)",
    }
    base = str(base_type).lower()
    constructor = constructors.get(base)
    if constructor is None:
        raise ValueError(f"Unsupported Fortran storage probe type: {base_type}")
    if kind is not None:
        constructor = constructor[:-1] + f",kind={kind})"
    return f"storage_size({constructor})"


def collect_fortran_type_storage_requirements(
    parsed,
    *,
    compile_time_values: dict[str, int | str] | None = None,
) -> list[dict[str, object]]:
    """Collect distinct compiler storage queries required for semantic conversion.

    Pass a parsed Fortran module, file, or project before invoking a target
    probe.  Each result keeps the normalized base type, kind, expression, and
    first parser context that needs it; callers normally feed probe facts back
    to the conversion helpers through ``type_facts``.

    Example:
        >>> parsed = FortranFile(variables=[FortranVariable(name="value", base_type="real", kind="8")])
        >>> collect_fortran_type_storage_requirements(parsed)[0]["expression"]
        'storage_size(real(0.0,kind=8))'
    """
    converter = FortranToIRConverter(compile_time_values=compile_time_values)
    requirements: list[dict[str, object]] = []
    seen: set[tuple[str, str | None]] = set()
    for var, context in _iter_fortran_variable_contexts(parsed):
        base_type = str(var.base_type or "").lower()
        if base_type not in _FORTRAN_STORAGE_PROBE_TYPES:
            continue
        if var.declared_storage_bits is not None:
            continue
        key = converter._target_type_key(var)
        if key in seen:
            continue
        seen.add(key)
        requirements.append(
            {
                "base_type": key[0],
                "kind": key[1],
                "expression": fortran_type_storage_expression(*key),
                "unit": context.get("unit"),
                "symbol": context.get("symbol"),
            }
        )
    return requirements


def collect_semantic_compile_time_requirements(
    parsed,
    *,
    compile_time_values: dict[str, int | str] | None = None,
    type_map: dict[tuple[str, str | None], str] | None = None,
) -> list[dict[str, str | None]]:
    """Collect parser symbols that block semantic IR conversion or wrapping.

    This is the inspection half of the "unknown compile-time value" workflow:
    parse first, collect unresolved parameter/kind expressions, evaluate them
    externally when needed, then pass the resulting dictionary to
    ``FortranToIRConverter(..., compile_time_values=...)`` or the convenience
    wrappers below.

    Example:
        >>> from prik import parse_fortran_file
        >>> parsed = parse_fortran_file("module m\\ninteger, parameter :: rk = selected_real_kind(12)\\nend module")
        >>> reqs = collect_semantic_compile_time_requirements(parsed)
        >>> reqs[0]["symbol"]
        'rk'
    """
    values = _normalize_compile_time_values(compile_time_values)
    converter = FortranToIRConverter(type_map=type_map, compile_time_values=values)
    requirements: list[dict[str, str | None]] = []
    seen: set[tuple[str | None, ...]] = set()

    def add_requirement(
        code: str, ctx: dict, *, expression: str, base_type: str | None = None, kind: str | None = None
    ) -> None:
        """Append one unique unresolved-value requirement using parser diagnostic context."""
        symbol = str(ctx.get("symbol") or "")
        item = {
            "code": code,
            "unit_kind": ctx.get("unit_kind"),
            "unit": ctx.get("unit"),
            "module": ctx.get("module"),
            "procedure": ctx.get("procedure"),
            "type_owner": ctx.get("type_owner"),
            "role": ctx.get("role"),
            "symbol": symbol,
            "base_type": base_type,
            "kind": kind,
            "expression": expression,
            "message": _compile_time_requirement_message(code, symbol, expression),
        }
        key = tuple(
            str(item.get(field) or "") for field in ("code", "unit", "symbol", "base_type", "kind", "expression")
        )
        if key in seen:
            return
        seen.add(key)
        requirements.append(item)

    for var, ctx in _iter_fortran_variable_contexts(parsed):
        expression = var.symbolic_value if var.symbolic_value is not None else var.value
        parameter_base_type = str(var.base_type or "").lower()
        if var.is_parameter and parameter_base_type == "integer" and var.value is None and expression:
            resolved = _resolve_compile_time_text(expression, values)
            supplied_by_symbol = values.get(var.name.lower())
            if supplied_by_symbol is None and resolved == expression:
                add_requirement("parameter_value", ctx, expression=expression)

        base_type = parameter_base_type
        if base_type not in {"integer", "real", "complex", "logical", "character"} or not var.kind:
            continue
        kind_key = converter._semantic_kind_key(var)
        if converter.type_map.get((base_type, kind_key)) is None:
            expression = _resolve_compile_time_text(str(var.kind), values)
            add_requirement(
                "unsupported_kind",
                ctx,
                expression=expression,
                base_type=base_type,
                kind=kind_key,
            )

    return requirements


def _resolve_semantic_value(value, compile_time_values: dict[str, str]):
    """Recursively resolve compile-time text inside a semantic metadata value."""
    if isinstance(value, str):
        return _resolve_compile_time_text(value, compile_time_values)
    if isinstance(value, list):
        return [_resolve_semantic_value(item, compile_time_values) for item in value]
    if isinstance(value, tuple):
        return tuple(_resolve_semantic_value(item, compile_time_values) for item in value)
    if isinstance(value, dict):
        return {key: _resolve_semantic_value(item, compile_time_values) for key, item in value.items()}
    return value


def _resolve_semantic_type_compile_time_values(
    semantic_type: SemanticType | None,
    compile_time_values: dict[str, str],
) -> None:
    """Resolve shape, constraint, and storage text on one semantic type in place."""
    if semantic_type is None:
        return
    semantic_type.shape = [_resolve_compile_time_text(dim, compile_time_values) for dim in semantic_type.shape]
    for constraint in semantic_type.constraints:
        constraint.arguments = _resolve_semantic_value(constraint.arguments, compile_time_values)
    semantic_type.metadata = _resolve_semantic_value(semantic_type.metadata, compile_time_values)
    if semantic_type.storage is not None:
        semantic_type.storage.metadata = _resolve_semantic_value(
            semantic_type.storage.metadata,
            compile_time_values,
        )
        if semantic_type.storage.array is not None:
            array = semantic_type.storage.array
            array.shape = [_resolve_compile_time_text(dim, compile_time_values) for dim in array.shape]
            array.source_shape = [_resolve_compile_time_text(dim, compile_time_values) for dim in array.source_shape]
            array.lower_bounds = [
                None if dim is None else _resolve_compile_time_text(dim, compile_time_values)
                for dim in array.lower_bounds
            ]
            array.upper_bounds = [
                None if dim is None else _resolve_compile_time_text(dim, compile_time_values)
                for dim in array.upper_bounds
            ]
            array.metadata = _resolve_semantic_value(array.metadata, compile_time_values)


def _resolve_semantic_argument_compile_time_values(
    arg: SemanticArgument | SemanticVariable,
    compile_time_values: dict[str, str],
) -> None:
    """Resolve type, default, and metadata text on one semantic argument in place."""
    _resolve_semantic_type_compile_time_values(arg.semantic_type, compile_time_values)
    arg.default_value = _resolve_semantic_value(arg.default_value, compile_time_values)
    arg.metadata = _resolve_semantic_value(arg.metadata, compile_time_values)


def _resolve_semantic_function_compile_time_values(
    func: SemanticFunction,
    compile_time_values: dict[str, str],
) -> None:
    """Resolve all type-bearing fields and projection values on one function in place."""
    for arg in func.arguments:
        _resolve_semantic_argument_compile_time_values(arg, compile_time_values)
    for local in func.locals:
        _resolve_semantic_argument_compile_time_values(local, compile_time_values)
    _resolve_semantic_type_compile_time_values(func.return_type, compile_time_values)
    for mapping in func.projection:
        mapping.value = _resolve_semantic_value(mapping.value, compile_time_values)
    func.metadata = _resolve_semantic_value(func.metadata, compile_time_values)


def _resolve_semantic_module_compile_time_values(
    module: SemanticModule,
    compile_time_values: dict[str, str],
) -> None:
    """Resolve compile-time text across one module's variables, functions, and classes."""
    for var in module.variables:
        _resolve_semantic_argument_compile_time_values(var, compile_time_values)
    for func in module.functions:
        _resolve_semantic_function_compile_time_values(func, compile_time_values)
    for declaration in module.classes:
        for field in declaration.fields:
            _resolve_semantic_argument_compile_time_values(field, compile_time_values)
        for method in declaration.methods:
            _resolve_semantic_function_compile_time_values(method, compile_time_values)
        declaration.metadata = _resolve_semantic_value(declaration.metadata, compile_time_values)
    module.metadata = _resolve_semantic_value(module.metadata, compile_time_values)


def resolve_semantic_compile_time_values(
    semantic_ir: SemanticModule | list[SemanticModule],
    compile_time_values: dict[str, int | str],
) -> SemanticModule | list[SemanticModule]:
    """Return a copy of semantic IR with known compile-time text resolved.

    Use this after semantic conversion when symbolic shape metadata should be
    specialized without mutating the original IR object.

    Example:
        >>> mod = SemanticModule(name="m", variables=[SemanticVariable("x", SemanticType("Float64", rank=1, shape=["1:n"]))])
        >>> resolve_semantic_compile_time_values(mod, {"n": 4}).variables[0].semantic_type.shape
        ['1:4']
    """
    values = _normalize_compile_time_values(compile_time_values)
    resolved = deepcopy(semantic_ir)
    modules = resolved if isinstance(resolved, list) else [resolved]
    for module in modules:
        _resolve_semantic_module_compile_time_values(module, values)
    return resolved


def _converter_for(
    compile_time_values: dict[str, int | str] | None = None,
    wrapped_derived_types: Iterable[tuple[str, str]] | None = None,
    type_facts: dict[tuple[str, str | None], dict[str, object]] | None = None,
) -> FortranToIRConverter:
    """Return the shared default converter or an isolated configured converter.

    The shared instance is used only for the all-default case.  Supplying any
    conversion input creates a new instance so per-call compile-time values and
    facts never leak into unrelated conversions.
    """
    if compile_time_values is None and wrapped_derived_types is None and type_facts is None:
        return _DEFAULT_CONVERTER
    return FortranToIRConverter(
        compile_time_values=compile_time_values,
        wrapped_derived_types=wrapped_derived_types,
        type_facts=type_facts,
    )


_DEFAULT_CONVERTER = FortranToIRConverter()


def fortran_module_to_semantic_module(
    module,
    *,
    compile_time_values: dict[str, int | str] | None = None,
    wrapped_derived_types: Iterable[tuple[str, str]] | None = None,
    type_facts: dict[tuple[str, str | None], dict[str, object]] | None = None,
) -> SemanticModule:
    """Convert one parsed Fortran module into a :class:`SemanticModule`.

    Use this for a selected :class:`FortranModule`, or for a file whose first
    module is intentionally the target.  Optional compile-time values and
    compiler storage facts complete parser-known datatype conversion; imported
    wrapper identities may be supplied through ``wrapped_derived_types``.
    Unsupported types or an empty file raise the existing conversion errors.

    Example:
        >>> parsed = FortranModule(
        ...     name="math",
        ...     procedures=[FortranProcedureSignature(name="scale", kind="subroutine", arguments=[
        ...         FortranArgument(name="value", base_type="real", kind="8")
        ...     ])],
        ... )
        >>> fortran_module_to_semantic_module(parsed).functions[0].arguments[0].semantic_type.name
        'Float64'
    """
    converter = _converter_for(compile_time_values, wrapped_derived_types, type_facts)
    return converter.visit(converter.first_module(module))


def fortran_file_to_semantic_modules(
    parsed_file: FortranFile,
    *,
    standalone_module_name: str | None = None,
    compile_time_values: dict[str, int | str] | None = None,
    wrapped_derived_types: Iterable[tuple[str, str]] | None = None,
    type_facts: dict[tuple[str, str | None], dict[str, object]] | None = None,
) -> list[SemanticModule]:
    """Convert every module and standalone procedure group in one parsed file.

    Use this rather than the single-module helper when file-level procedures
    matter.  Parser module ordering is retained, and ``standalone_module_name``
    controls the synthetic module used for top-level procedures.

    Example:
        >>> parsed = FortranFile(procedures=[FortranProcedureSignature(name="tick", kind="subroutine")])
        >>> [module.name for module in fortran_file_to_semantic_modules(parsed)]
        ['standalone']
    """
    return _converter_for(compile_time_values, wrapped_derived_types, type_facts).visit(
        parsed_file,
        standalone_module_name=standalone_module_name,
    )


def fortran_project_to_semantic_modules(
    project: FortranProject,
    *,
    compile_time_values: dict[str, int | str] | None = None,
    type_facts: dict[tuple[str, str | None], dict[str, object]] | None = None,
) -> list[SemanticModule]:
    """Convert an ordered parsed Fortran project with project-wide type context.

    Use this for multi-file conversion where imported derived types and callback
    interfaces must resolve across files.  The output preserves project file
    and parser module order; type facts and compile-time values apply to every
    converted module.

    Example:
        >>> project = FortranProject(files=[FortranFile(modules=[FortranModule(name="math")])])
        >>> [module.name for module in fortran_project_to_semantic_modules(project)]
        ['math']
    """
    return _converter_for(compile_time_values, type_facts=type_facts).visit(project)


if __name__ == "__main__":
    from prik.parsers.fortran.models import FortranArgument, FortranModule, FortranProcedureSignature

    parsed_module = FortranModule(
        name="math",
        procedures=[
            FortranProcedureSignature(
                name="scale",
                kind="subroutine",
                module="math",
                arguments=[FortranArgument(name="value", base_type="real", kind="8", procedure="scale")],
            )
        ],
    )
    semantic_module = fortran_module_to_semantic_module(parsed_module)
    semantic_argument = semantic_module.functions[0].arguments[0]
    print(
        f"{semantic_module.name}.{semantic_module.functions[0].name}"
        f"({semantic_argument.name}): {semantic_argument.semantic_type.name}"
        f" via {semantic_argument.semantic_type.storage.kind} storage"
    )
