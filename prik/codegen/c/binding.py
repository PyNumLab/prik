"""Lower validated wrapper plans into CPython C binding syntax nodes.

Use :class:`CBindingGenerator` after post-IR policy completion and wrapper
planning.  Its visitor entrypoint consumes a validated `ModulePlan` and
returns a `CModule` plus `CHeader` for the source printers.  This stage
only projects completed binding actions: it does not infer ownership,
conversion, or lifecycle policy from datatypes or local state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import math
import re

from prik.utilities.declaration_expressions import declaration_extent_uses_power, render_declaration_extent
from prik.policy.ownership import (
    CodegenAction,
    ObjectKind,
    PythonBarrierAction,
    SetterAction,
)
from prik.policy.models import (
    ArgumentHandoffMode,
    CallbackABIKind,
    CallbackResultAction,
    CallbackTransferAction,
    ClassConstructorKind,
    DerivedDummyCategory,
    DerivedFieldAccessMechanism,
    DerivedObjectStorage,
    DerivedOwnerRetention,
    DerivedWriteback,
    DirectResultABI,
    ModuleObjectAccessMechanism,
    ModuleGetterAction,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorInterop,
    NativeArrayDefaultConstruction,
    NativeArrayOperation,
    NativeDescriptorHandoffABI,
    EntrypointProjectionAction,
    EntrypointPassingConvention,
    OptionalMode,
    OverloadMatchKind,
    PythonExceptionKind,
    TransformationAction,
    WritebackPhase,
)
from prik.codegen.c.naming import CBindingNames
from prik.codegen.c.python_surface import PythonSurfaceContext, PythonSurfaceEmitter
from prik.semantics.scalar_types import is_boolean_semantic_type_name
from prik.codegen.nodes import (
    CAllowThreadsBegin,
    CAllowThreadsEnd,
    CBreak,
    CCase,
    CComment,
    CDeclaration,
    CExpressionStatement,
    CFor,
    CFunction,
    CFunctionPointerType,
    CFunctionPrototype,
    CHeader,
    CIf,
    CInclude,
    CMacroDefinition,
    CMethodDefEntry,
    CMethodDefTable,
    CModule,
    CModuleDef,
    CModulePropertyEntry,
    CModulePropertySupport,
    CParameter,
    CReturn,
    CStructDefinition,
    CSwitch,
    CodeExpression,
)
from prik.codegen.overloads import OverloadPlanQueries
from prik.naming.native_symbols import COLLISION_ADAPTER_STORAGE
from prik.planning.models import (
    ArrayHandoffPlan,
    ArgumentTransferPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    ClassSurfacePlan,
    DatatypeFamily,
    DerivedFieldPlan,
    DerivedHandoffPlan,
    DerivedMemberPathPlan,
    DerivedTypePlan,
    DirectCABITypePlan,
    FunctionPlan,
    LifecycleActionPlan,
    ModulePlan,
    ModuleVariablePlan,
    NamespacePlan,
    NativeArrayActualPlan,
    NativeArrayHandlePlan,
    NativeEntrypointABIValueKind,
    NativeEntrypointABIValuePlan,
    GeneratedSupportProcedureImplementationOwner,
    GeneratedSupportProcedureEntrypointPlan,
    NativeEntrypointParameterPlan,
    NativeEntrypointProjectedSlotPlan,
    NativeEntrypointResultPlan,
    OverloadArgumentMatchPlan,
    OverloadPlan,
    ResultPlan,
)
from prik.codegen.primitive_scalar_types import NativeCArrayStorageRegistry, PrimitiveScalarTypeRegistry
from prik.codegen.visitor import ClassVisitor


@dataclass
class _CArgumentNames:
    """Binding-private C local names for one planned Python argument.

    The context builder creates this immutable record once per argument so all
    extraction, conversion, call, and writeback helpers use identical names.
    """

    object_name: str
    value_name: str
    length_name: str
    nullable_name: str
    present_name: str
    extent_names: tuple[str, ...]
    upper_bound_names: tuple[str, ...]
    stride_names: tuple[str, ...]
    dense_actual_name: str
    runtime_rank_name: str
    itemsize_name: str
    polymorphic_name: str


@dataclass
class _CFunctionContext:
    """Per-function names and role substitutions shared across C lowering.

    The record is derived from a completed function plan and is read-only while
    declarations, conversion nodes, entrypoint calls, and result assembly are
    emitted.
    """

    arguments: dict[str, _CArgumentNames]
    native_outputs: dict[str, str]
    result_name: str | None
    python_result_name: str | None
    python_results: dict[str, str]
    role_values: dict[str, str]


@dataclass(frozen=True)
class _COverloadDispatch:
    """Describe one namespace-installed C overload dispatcher."""

    overload: OverloadPlan
    receiver: bool
    public: bool


_BINDING_GETTER_SUMMARIES = {
    ModuleGetterAction.CONSTANT_VALUE: "The value is a constant placed in the module dictionary at import.",
    ModuleGetterAction.NATIVE_CONSTANT_VALUE: "Builds a Python object from the compiler-evaluated constant.",
    ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE: "Copies the parameter array into one read-only NumPy array.",
    ModuleGetterAction.DIRECT_VALUE: "Builds a Python scalar from the current native value.",
    ModuleGetterAction.CHARACTER_VALUE: "Decodes the fixed-width native characters into a Python str.",
    ModuleGetterAction.NULLABLE_SNAPSHOT: "Returns a detached copy, or None when the native value holds nothing.",
    ModuleGetterAction.BORROWED_ARRAY_VIEW: "Wraps the native storage in a live NumPy array without copying.",
    ModuleGetterAction.DERIVED_OBJECT: "Returns the generated wrapper object for the native value.",
}

_BINDING_SETTER_SUMMARIES = {
    SetterAction.WRITE_THROUGH: "Validates the incoming object and writes it into native storage.",
    SetterAction.REJECT_REPLACEMENT: "Replacement is rejected; the attribute is read-only.",
    SetterAction.OMIT: "No setter is exposed.",
}


class CBindingGenerator(ClassVisitor):
    """Build the CPython C half of a wrapper from validated binding-plan views.

    Use :meth:`require_supported` followed by :meth:`visit` for a single
    C module/header pair, or :meth:`binding_modules` when a plan qualifies
    for independent wrapper shards.  The returned nodes are normally consumed
    by the C source printer.  Completed semantic policy remains outside this
    class; unsupported plan actions fail instead of being reinterpreted here.
    """

    _SHARD_MIN_FUNCTIONS = 128
    _SHARD_TARGET_FUNCTIONS = 32

    def require_supported(self, plan: ModulePlan) -> None:
        """Preflight primitive spellings needed by an already-validated plan.

        Call this before direct binding lowering.  It checks only capability
        of the C scalar registry; cross-view consistency and policy selection
        are completed and validated before this backend stage.
        """
        for derived in self._derived_types(plan):
            self._require_derived_type_supported(derived)
        for function in self._functions(plan):
            self._require_function_supported(function)
        for variable in self._variables(plan):
            self._require_variable_supported(variable)

    def _require_variable_supported(self, variable: ModuleVariablePlan) -> None:
        """Preflight only the primitive registry needed by C emission."""
        self._require_backend_type_supported(variable.semantic_type_name, variable.datatype_family)

    # Derived-type definition and field support checks.
    def _require_derived_type_supported(self, derived: DerivedTypePlan) -> None:
        """Preflight primitive field types after shared plan validation."""
        for field in derived.fields:
            if field.semantic_type_name != "String" and field.derived is None:
                PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)

    @staticmethod
    def _require_backend_type_supported(
        semantic_type_name: str | None,
        datatype_family: DatatypeFamily | None,
    ) -> None:
        """Resolve primitive types; shared validation owns every plan decision."""
        if semantic_type_name is None or datatype_family in {DatatypeFamily.STRING, DatatypeFamily.DERIVED}:
            return
        PrimitiveScalarTypeRegistry.type_for(semantic_type_name)

    def _require_function_supported(self, function: FunctionPlan) -> None:
        """Preflight primitive types after shared plan validation."""
        for argument in function.arguments:
            self._require_argument_supported(argument)
        self._require_function_results_supported(function)
        for action in function.writeback_actions:
            self._require_backend_type_supported(action.semantic_type_name, action.datatype_family)

    def _require_function_results_supported(self, function: FunctionPlan) -> None:
        """Preflight primitive binding-visible result types."""
        for result in function.results:
            self._require_backend_type_supported(result.semantic_type_name, result.datatype_family)

    def _require_argument_supported(self, argument: ArgumentTransferPlan) -> None:
        """Preflight primitive argument and callback transfer types."""
        if argument.callback is not None:
            transfers = (
                *argument.callback.arguments,
                *((argument.callback.result.transfer,) if argument.callback.result.transfer is not None else ()),
            )
            for transfer in transfers:
                if transfer.semantic_type_name != "String" and transfer.derived_type_identity is None:
                    PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name)
            return
        self._require_backend_type_supported(argument.semantic_type_name, argument.datatype_family)

    def _visit_ModulePlan(self, plan: ModulePlan) -> tuple[CModule, CHeader]:
        """Build the matching C implementation module and public header.

        Both artifacts project the same validated plan.  They are returned as
        nodes so the next printer stage can render them independently.
        """
        return self.binding_module(plan), self.binding_header(plan)

    def binding_module(self, plan: ModulePlan) -> CModule:
        """Build one complete C implementation module from a validated plan.

        This records class Python names for later property-source generation,
        then assembles module support, runtime helpers, wrappers, and module
        initialization in emitted dependency order.
        """
        # Stage 1: index planner-owned cross-language operations before any lowering.
        self._generated_support_procedure_entrypoints = {
            (procedure.owner_path, procedure.role): procedure for procedure in plan.entrypoint.support_procedures
        }
        self._derived_owner_paths = {
            derived.backend_symbol: derived.owner_path for derived in self._derived_types(plan)
        }
        self._binding_owned_derived_owner_paths = frozenset(plan.binding.owned_derived_type_owner_paths)
        self._binding_allocatable_holder_owner_paths = frozenset(plan.binding.allocatable_holder_type_owner_paths)
        self._binding_pointer_holder_owner_paths = frozenset(plan.binding.pointer_holder_type_owner_paths)
        # Stage 2: complete the immutable name index consumed by Python-surface emission.
        class_python_names = {
            surface.type_identity: surface.python_names[0]
            for namespace in plan.namespaces
            for surface in namespace.classes
            if surface.python_names
        }
        # Stage 3: select support and assemble generated functions in dependency order.
        functions = tuple(function for namespace in plan.namespaces for function in self.visit(namespace))
        needs_native_support = self.requires_native_support(plan)
        needs_free = self._module_needs_allocator(plan)
        return CModule(
            name=f"{plan.binding.owner_path}_wrapper",
            defines=self._module_defines(plan, needs_native_support),
            includes=self._module_includes(plan, needs_native_support, needs_free),
            declarations=self._module_declarations(plan),
            functions=(
                *self._module_allocator_functions(needs_free),
                *self._extent_expression_support_functions(plan),
                *self._callback_runtime_functions(plan),
                *self._derived_call_runtime_functions(plan),
                *self._derived_origin_functions(plan),
                *self._derived_capsule_destructor_functions(plan),
                *self._class_constructor_functions(plan),
                *self._derived_field_functions(plan),
                *self._derived_handle_operation_functions(plan),
                *self._native_array_operation_functions(plan),
                *functions,
                *self._overload_dispatch_functions(plan, class_python_names),
                self._module_init(plan, needs_native_support),
            ),
        )

    def _generated_support_procedure_entrypoint(
        self, owner_path: str, role: str
    ) -> GeneratedSupportProcedureEntrypointPlan:
        """Return one required planner-owned operation without a naming fallback."""
        try:
            return self._generated_support_procedure_entrypoints[(owner_path, role)]
        except (AttributeError, KeyError):
            raise ValueError(f"Missing generated support procedure entrypoint {owner_path!r} role {role!r}") from None

    def _generated_support_procedure_entrypoints_for(
        self,
        owner_path: str,
        role_prefix: str,
    ) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        """Return planner-ordered operations for one owner and role family."""
        return tuple(
            operation
            for operation in self._generated_support_procedure_entrypoints.values()
            if operation.owner_path == owner_path and operation.role.startswith(role_prefix)
        )

    def _has_generated_support_procedure_entrypoint(self, owner_path: str, role: str) -> bool:
        """Return whether planning registered one generated support procedure."""
        return (owner_path, role) in self._generated_support_procedure_entrypoints

    def _generated_support_procedure_entrypoint_prototype(
        self,
        operation: GeneratedSupportProcedureEntrypointPlan,
    ) -> CFunctionPrototype:
        """Lower one complete planner-owned C ABI into a declaration."""
        if operation.implementation_owner is not GeneratedSupportProcedureImplementationOwner.FORTRAN:
            raise ValueError(f"C cannot declare binding-owned operation {operation.key!r} as an external bridge")
        return CFunctionPrototype(
            operation.symbol_name,
            self._support_procedure_c_type(operation.signature.result),
            tuple(self._support_procedure_c_parameter(parameter) for parameter in operation.signature.parameters),
        )

    def _support_procedure_c_parameter(self, value: NativeEntrypointABIValuePlan) -> CParameter:
        """Lower one ordered generated-support C-ABI parameter."""
        if value.kind is NativeEntrypointABIValueKind.CALLBACK and value.callback_signature is not None:
            if value.c_type_name is not None:
                return CParameter(value.c_name, value.c_type_name)
            return CParameter(
                value.c_name,
                self._support_procedure_c_type(value.callback_signature.result),
                tuple(self._support_procedure_c_type(item) for item in value.callback_signature.parameters),
            )
        return CParameter(value.c_name, self._support_procedure_c_type(value))

    @staticmethod
    def _support_procedure_c_type(value: NativeEntrypointABIValuePlan) -> str:
        """Spell one structured generated-support ABI value for C."""
        base_types = {
            NativeEntrypointABIValueKind.VOID: "void",
            NativeEntrypointABIValueKind.BOOL: "bool",
            NativeEntrypointABIValueKind.INT: "int",
            NativeEntrypointABIValueKind.INT8: "int8_t",
            NativeEntrypointABIValueKind.INT64: "int64_t",
            NativeEntrypointABIValueKind.OPAQUE: "void",
            NativeEntrypointABIValueKind.CHARACTER: "char",
            NativeEntrypointABIValueKind.DESCRIPTOR: "CFI_cdesc_t",
        }
        if value.kind is NativeEntrypointABIValueKind.SEMANTIC_SCALAR:
            if value.semantic_type_name is None:
                raise ValueError(f"Generated-support ABI value {value.role!r} has no semantic scalar type")
            base = PrimitiveScalarTypeRegistry.type_for(value.semantic_type_name).c_spelling
        elif value.kind is NativeEntrypointABIValueKind.CALLBACK:
            if value.c_type_name is None:
                raise ValueError(f"Generated-support ABI callback {value.role!r} has no C typedef")
            base = value.c_type_name
        else:
            try:
                base = base_types[value.kind]
            except KeyError:
                raise ValueError(f"Unsupported generated-support C ABI kind {value.kind.value!r}") from None
        prefix = "const " if value.const else ""
        return f"{prefix}{base}{' *' * value.pointer_depth}"

    def binding_modules(self, plan: ModulePlan) -> tuple[CModule, ...]:
        """Build one implementation module or independently compilable wrapper shards.

        Use this public entrypoint when compilation can benefit from sharding.
        Plans with coupled runtime support intentionally return one module so
        helper state and declarations remain shared.
        """
        module = self.binding_module(plan)
        function_groups = self._binding_function_shards(plan)
        modules = (module,) if not function_groups else self._sharded_binding_modules(plan, module, function_groups)
        adapters = self._collision_adapter_module(plan)
        return (*modules, adapters) if adapters is not None else modules

    def _collision_adapter_module(self, plan: ModulePlan) -> CModule | None:
        """Build the translation unit that forwards collision-adapted symbols.

        The unit deliberately includes no Python header, so its declaration of
        each native symbol is the only one in scope and cannot conflict with a
        declaration ``Python.h`` would otherwise have brought in.
        """
        adapted = self._collision_adapted_functions(plan)
        if not adapted:
            return None
        return CModule(
            name=f"{plan.binding.owner_path}_adapters",
            includes=(
                CInclude("stdint.h"),
                CInclude("stdbool.h"),
                CInclude("complex.h"),
                CInclude("stddef.h"),
            ),
            declarations=tuple(self._collision_adapter_native_prototype(function) for function in adapted),
            functions=tuple(self._collision_adapter_function(function) for function in adapted),
        )

    def _collision_adapted_functions(self, plan: ModulePlan) -> tuple[FunctionPlan, ...]:
        """Return one function per adapted symbol, in stable emission order.

        Several Python callables may name the same native symbol, so the
        forwarder is defined once per symbol rather than once per callable.
        """
        adapted: dict[str, FunctionPlan] = {}
        for function in self._functions(plan):
            symbol = function.entrypoint.collision_adapter_symbol
            if symbol is not None:
                adapted.setdefault(symbol, function)
        return tuple(adapted.values())

    def _collision_adapter_native_prototype(self, plan: FunctionPlan) -> CFunctionPrototype:
        """Declare the native symbol under its own name inside the adapter unit."""
        return replace(self._entrypoint_prototype(plan), name=plan.entrypoint.symbol_name)

    def _collision_adapter_function(self, plan: FunctionPlan) -> CFunction:
        """Define the forwarder the binding calls in place of the native symbol."""
        prototype = self._entrypoint_prototype(plan)
        call = CodeExpression(
            f"({plan.entrypoint.symbol_name})({', '.join(parameter.name for parameter in prototype.parameters)})"
        )
        body = (CExpressionStatement(call),) if prototype.return_type == "void" else (CReturn(call),)
        return CFunction(
            name=prototype.name,
            return_type=prototype.return_type,
            parameters=prototype.parameters,
            body=body,
            # A hidden forwarder is not part of the extension's exported ABI, so
            # link-time optimization may inline it and drop the definition. An
            # exported one is interposable and must survive the link.
            storage=COLLISION_ADAPTER_STORAGE,
        )

    def _sharded_binding_modules(
        self,
        plan: ModulePlan,
        module: CModule,
        function_groups: tuple[tuple[FunctionPlan, ...], ...],
    ) -> tuple[CModule, ...]:
        """Move independently planned wrappers into balanced worker units."""
        wrapper_names = {self._binding_function_name(function) for function in self._functions(plan)}
        wrappers = self._external_binding_wrappers(module, wrapper_names)
        main_module = replace(
            module,
            functions=tuple(function for function in module.functions if function.name not in wrapper_names),
        )
        worker_defines = tuple(
            definition for definition in module.defines if definition.name != "PRIK_BINDING_IMPORT_ARRAY"
        )
        workers = self._binding_worker_modules(module, function_groups, wrappers, worker_defines)
        return (main_module, *workers)

    @staticmethod
    def _external_binding_wrappers(module: CModule, wrapper_names: set[str]) -> dict[str, CFunction]:
        """Return externally linked copies of the selected wrapper functions."""
        return {
            function.name: replace(function, storage=None)
            for function in module.functions
            if function.name in wrapper_names
        }

    def _binding_worker_modules(
        self,
        module: CModule,
        function_groups: tuple[tuple[FunctionPlan, ...], ...],
        wrappers: dict[str, CFunction],
        worker_defines: tuple[CMacroDefinition, ...],
    ) -> tuple[CModule, ...]:
        """Assemble the independently compilable wrapper worker units."""
        return tuple(
            CModule(
                name=f"{module.name}_{index:03d}",
                defines=worker_defines,
                includes=module.includes,
                declarations=tuple(self._entrypoint_prototype(function) for function in group),
                functions=tuple(wrappers[self._binding_function_name(function)] for function in group),
            )
            for index, group in enumerate(function_groups, start=1)
        )

    def _binding_function_shards(self, plan: ModulePlan) -> tuple[tuple[FunctionPlan, ...], ...]:
        """Return balanced groups when wrappers are safe to compile independently."""
        functions = self._functions(plan)
        if not self._can_shard_binding_functions(plan, functions):
            return ()
        shard_count = max(2, math.ceil(len(functions) / self._SHARD_TARGET_FUNCTIONS))
        base_size, larger_groups = divmod(len(functions), shard_count)
        groups = []
        offset = 0
        for index in range(shard_count):
            size = base_size + (index < larger_groups)
            groups.append(functions[offset : offset + size])
            offset += size
        return tuple(groups)

    def _can_shard_binding_functions(
        self,
        plan: ModulePlan,
        functions: tuple[FunctionPlan, ...],
    ) -> bool:
        """Keep runtime-coupled surfaces in one binding translation unit."""
        if len(functions) < self._SHARD_MIN_FUNCTIONS:
            return False
        if not self._has_shardable_namespace(plan):
            return False
        if self._module_has_shard_runtime_state(plan):
            return False
        return not self._functions_use_native_array_handles(functions)

    @staticmethod
    def _has_shardable_namespace(plan: ModulePlan) -> bool:
        """Return whether one root procedure namespace owns the module."""
        if len(plan.namespaces) != 1:
            return False
        namespace = plan.namespaces[0]
        runtime_surfaces = (
            namespace.python_path,
            namespace.variables,
            namespace.classes,
            namespace.derived_types,
            namespace.overloads,
        )
        return not any(runtime_surfaces)

    def _module_has_shard_runtime_state(self, plan: ModulePlan) -> bool:
        """Return whether wrappers call helpers that must share one unit."""
        return any(
            (
                self._module_needs_allocator(plan),
                self._module_uses_callbacks(plan),
                self._module_uses_derived_calls(plan),
                self._module_uses_extent_power(plan),
            )
        )

    def _extent_expression_support_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Emit the integer-power helper only when a completed extent uses it."""
        if not self._module_uses_extent_power(plan):
            return ()
        return (
            CFunction(
                "prik_extent_power",
                "npy_intp",
                parameters=(CParameter("base", "npy_intp"), CParameter("exponent", "npy_intp")),
                storage="static",
                body=(
                    CIf(
                        CodeExpression("exponent < 0"),
                        body=(
                            CIf(CodeExpression("base == 1"), body=(CReturn(CodeExpression("1")),)),
                            CIf(
                                CodeExpression("base == -1"),
                                body=(CReturn(CodeExpression("(exponent % 2) ? -1 : 1")),),
                            ),
                            CReturn(CodeExpression("0")),
                        ),
                    ),
                    CDeclaration("value", "npy_intp", CodeExpression("1")),
                    CFor(
                        "",
                        CodeExpression("exponent > 0"),
                        CodeExpression("exponent /= 2"),
                        body=(
                            CIf(
                                CodeExpression("exponent % 2 != 0"),
                                body=(CExpressionStatement(CodeExpression("value *= base")),),
                            ),
                            CIf(
                                CodeExpression("exponent > 1"),
                                body=(CExpressionStatement(CodeExpression("base *= base")),),
                            ),
                        ),
                    ),
                    CReturn(CodeExpression("value")),
                ),
            ),
        )

    def _module_uses_extent_power(self, plan: ModulePlan) -> bool:
        """Return whether any executable plan-owned array extent uses ``**``."""
        return (
            any(self._array_uses_extent_power(variable.array) for variable in self._variables(plan))
            or any(
                self._array_uses_extent_power(field.array)
                for derived in self._derived_types(plan)
                for field in derived.fields
            )
            or any(self._function_uses_extent_power(function) for function in self._functions(plan))
        )

    def _function_uses_extent_power(self, function: FunctionPlan) -> bool:
        """Scan one function's direct and callback transfer arrays for ``**``."""
        direct_owners = (*function.arguments, *function.results)
        if any(self._array_uses_extent_power(owner.array) for owner in direct_owners):
            return True
        callbacks = (argument.callback for argument in function.arguments if argument.callback is not None)
        return any(
            self._array_uses_extent_power(transfer.array)
            for callback in callbacks
            for transfer in (
                *callback.arguments,
                *((callback.result.transfer,) if callback.result.transfer is not None else ()),
            )
        )

    @staticmethod
    def _array_uses_extent_power(array: ArrayHandoffPlan | None) -> bool:
        """Return whether one optional completed array shape contains power."""
        return bool(array) and any(declaration_extent_uses_power(expression) for expression in array.shape)

    @staticmethod
    def _functions_use_native_array_handles(functions: tuple[FunctionPlan, ...]) -> bool:
        """Return whether persistent descriptor helpers couple the wrappers."""
        arguments_use_handles = any(
            argument.native_array_handle is not None for function in functions for argument in function.arguments
        )
        results_use_handles = any(
            result.native_array_handle is not None for function in functions for result in function.results
        )
        return any((arguments_use_handles, results_use_handles))

    def binding_header(self, plan: ModulePlan) -> CHeader:
        """Build the C header that declares wrappers from the validated plan.

        The header mirrors whether wrapper functions are externally linked for
        sharding.  It is paired with :meth:`binding_module` or
        :meth:`binding_modules` output.
        """
        external_wrappers = bool(self._binding_function_shards(plan))
        return CHeader(
            guard=f"{plan.binding.owner_path.upper()}_WRAPPER_H",
            includes=(CInclude("Python.h"),),
            prototypes=tuple(
                self._binding_prototype(function, external=external_wrappers) for function in self._functions(plan)
            ),
        )

    @staticmethod
    def _scalar_numpy_type(scalar) -> str:
        """Return the completed NumPy type selected for one scalar boundary."""
        if scalar.numpy_type_macro is None:
            raise ValueError(f"Scalar type {scalar.semantic_name!r} has no NumPy type")
        return scalar.numpy_type_macro

    def _scalar_helper_suffix(self, scalar) -> str:
        """Return the typed native-support suffix selected by scalar policy."""
        numpy_type = self._scalar_numpy_type(scalar)
        if not numpy_type.startswith("NPY_"):
            raise ValueError(f"Unsupported NumPy scalar type macro {numpy_type!r}")
        return numpy_type.removeprefix("NPY_").casefold()

    def _scalar_unpack_expression(self, scalar, object_name: str, value_name: str) -> str:
        """Return one typed coercive Python-to-native scalar conversion."""
        suffix = self._scalar_helper_suffix(scalar)
        return f"prik_{suffix}_unpack({object_name}, &{value_name})"

    def _scalar_exact_unpack_expression(self, scalar, object_name: str, value_name: str) -> str:
        """Return one fused exact-type validation and scalar conversion."""
        suffix = self._scalar_helper_suffix(scalar)
        return f"prik_{suffix}_unpack_exact({object_name}, &{value_name})"

    def _scalar_exact_unpack_statement(
        self,
        scalar,
        object_name: str,
        value_name: str,
        mismatch_error: str,
        failure_return: str,
    ) -> CExpressionStatement:
        """Return one exact scalar transfer with its boundary-specific error."""
        unpack = self._scalar_exact_unpack_expression(scalar, object_name, value_name)
        return CExpressionStatement(
            CodeExpression(
                f"if ({unpack} < 0) {{ if (!PyErr_Occurred()) {{ {mismatch_error}; }} return {failure_return}; }}"
            )
        )

    def _scalar_result_expression(self, scalar, value_pointer: str, *, module: bool = False) -> str:
        """Return one native scalar conversion selected by completed result policy."""
        result_kind = scalar.python_module_result_kind if module else scalar.python_result_kind
        if result_kind not in {"python", "numpy"}:
            raise ValueError(f"Unsupported Python result kind for {scalar.semantic_name!r}: {result_kind!r}") from None
        suffix = self._scalar_helper_suffix(scalar)
        return f"prik_{suffix}_to_{result_kind}({value_pointer})"

    def _visit_NamespacePlan(self, plan: NamespacePlan) -> tuple[CFunction, ...]:
        """Return binding functions directly owned by one Python namespace."""
        return (
            *(self.visit(function) for function in plan.functions),
            *(function for variable in plan.variables for function in self.visit(variable)),
        )

    def requires_native_support(self, plan: ModulePlan) -> bool:
        """Return whether module lowering consumes bundled native helpers."""
        return (
            bool(tuple(self._variables(plan)))
            or any(function.arguments or function.results for function in self._functions(plan))
            # Every published component converts through the bundled helpers, so a
            # type whose module exposes only `bind(C)` procedures still needs them.
            or any(derived.fields for derived in self._derived_types(plan))
        )

    def _module_needs_allocator(self, plan: ModulePlan) -> bool:
        """Return whether emitted value/result copies need the shared allocator."""
        return any(
            variable.binding.getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT for variable in self._variables(plan)
        ) or any(self._function_needs_allocator(function) for function in self._functions(plan))

    def _function_needs_allocator(self, function: FunctionPlan) -> bool:
        """Return whether one wrapper function requires allocated string storage."""
        return any(
            result.scalar_descriptor is not None or result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY}
            for result in function.entrypoint.results
        ) or any(
            argument.object_kind is ObjectKind.STRING and argument.binding.codegen_action is CodegenAction.COPY_IN_OUT
            for argument in function.arguments
        )

    def _module_defines(self, plan: ModulePlan, needs_native_support: bool) -> tuple[CMacroDefinition, ...]:
        """Select native-support sections required by the completed module plan."""
        if not needs_native_support:
            return ()
        definitions = [CMacroDefinition("PRIK_BINDING_IMPORT_ARRAY", "1")]
        if any(
            argument.native_array_actual is not None
            for function in self._functions(plan)
            for argument in function.arguments
        ):
            definitions.append(CMacroDefinition("PRIK_BINDING_NATIVE_ARRAY_ACTUAL", "1"))
        return tuple(definitions)

    def _module_includes(
        self,
        plan: ModulePlan,
        needs_native_support: bool,
        needs_free: bool,
    ) -> tuple[CInclude, ...]:
        """Return dependency-closed includes for one assembled C module."""
        return (
            CInclude("Python.h"),
            CInclude("stdint.h"),
            CInclude("stdbool.h"),
            CInclude("complex.h"),
            # A preserved direct-C declaration may spell a standard typedef such
            # as ``size_t`` or ``ptrdiff_t``, so the entrypoint prototype needs
            # its defining header rather than whatever ``Python.h`` happens to
            # pull in on one platform.
            *((CInclude("stddef.h"),) if self._module_declares_direct_c_entrypoints(plan) else ()),
            *((CInclude("stdatomic.h"),) if self._module_uses_derived_origin_ops(plan) else ()),
            *((CInclude("string.h"),) if self._module_uses_memory_copy(plan) else ()),
            *(
                (CInclude("stdlib.h"),)
                if needs_free or self._module_uses_derived_calls(plan) or self._module_uses_callbacks(plan)
                else ()
            ),
            *(CInclude(header) for header in plan.required_headers),
            *self._module_native_support_includes(needs_native_support),
            CInclude(f"{plan.binding.owner_path}_wrapper.h", system=False),
        )

    @staticmethod
    def _module_declares_direct_c_entrypoints(plan: ModulePlan) -> bool:
        """Return whether any planned entrypoint carries preserved C declarations."""
        return any(
            function.entrypoint.direct_c_abi is not None
            for namespace in plan.namespaces
            for function in namespace.functions
        )

    def _module_uses_string_values(self, plan: ModulePlan) -> bool:
        """Return whether binding conversion needs C string helpers."""
        return any(
            argument.binding.python_action is PythonBarrierAction.STRING_VALUE
            for function in self._functions(plan)
            for argument in function.arguments
        )

    def _module_uses_callbacks(self, plan: ModulePlan) -> bool:
        """Return whether one binding owns immediate callback trampolines."""
        return any(
            argument.callback is not None for function in self._functions(plan) for argument in function.arguments
        )

    def _module_uses_memory_copy(self, plan: ModulePlan) -> bool:
        """Return whether binding conversion emits string or array byte copies."""
        return (
            self._module_uses_string_values(plan)
            or self._module_uses_array_result_copy(plan)
            or any(
                variable.binding.getter_action is ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE
                for namespace in plan.namespaces
                for variable in namespace.variables
            )
            or self._module_uses_derived_string_copy(plan)
            or self._module_uses_non_direct_derived_calls(plan)
        )

    def _module_uses_array_result_copy(self, plan: ModulePlan) -> bool:
        """Return module uses array result copy from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return any(
            result.object_kind is ObjectKind.NUMPY_ARRAY
            for function in self._functions(plan)
            for result in function.results
        )

    def _module_uses_derived_string_copy(self, plan: ModulePlan) -> bool:
        """Return module uses derived string copy from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return any(
            field.access is DerivedFieldAccessMechanism.FIXED_STRING_COPY
            for derived in self._derived_types(plan)
            for field in derived.fields
        )

    def _module_uses_non_direct_derived_calls(self, plan: ModulePlan) -> bool:
        """Return module uses non direct derived calls from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return any(
            any(case.actual_storage is not DerivedObjectStorage.DIRECT for case in argument.derived_call.cases)
            for function in self._functions(plan)
            for argument in function.arguments
            if argument.derived_call is not None
        )

    def _module_uses_derived_calls(self, plan: ModulePlan) -> bool:
        """Return whether one binding needs scalar-derived origin dispatch."""
        return any(
            argument.derived_call is not None for function in self._functions(plan) for argument in function.arguments
        )

    def _module_uses_derived_alias_validation(self, plan: ModulePlan) -> bool:
        """Return module uses derived alias validation from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return any(
            sum(argument.derived_call is not None for argument in function.arguments) >= 2
            for function in self._functions(plan)
        )

    def _module_uses_derived_origin_ops(self, plan: ModulePlan) -> bool:
        """Return whether runtime-selected module origins need typed operations."""
        return any(variable.derived is not None for variable in self._variables(plan))

    def _module_native_support_includes(self, required: bool) -> tuple[CInclude, ...]:
        """Return bundled native-support includes consumed by generated nodes."""
        if not required:
            return ()
        return (CInclude("binding_support/prik_binding.h", system=False),)

    # Immediate callback runtime.
    def _callback_sites(self, plan: ModulePlan) -> tuple[CallbackHandoffPlan, ...]:
        """Return call-scoped callback sites in stable function argument order."""
        return tuple(
            argument.callback
            for function in self._functions(plan)
            for argument in sorted(function.arguments, key=lambda item: item.native_position)
            if argument.callback is not None
        )

    def _callback_runtime_declarations(self, plan: ModulePlan) -> tuple:
        """Declare one independent thread-local stack for each callback site."""
        declarations = []
        for callback in self._callback_sites(plan):
            declarations.extend(
                (
                    CStructDefinition(
                        callback.binding.context_type_symbol,
                        (
                            CParameter("callable", "PyObject *"),
                            CParameter("module", "PyObject *"),
                            CParameter("thread_id", "unsigned long"),
                            CParameter(
                                "previous",
                                f"struct {callback.binding.context_type_symbol} *",
                            ),
                            CParameter("last_result", "PyObject *"),
                        ),
                    ),
                    CDeclaration(
                        callback.binding.context_current_symbol,
                        f"static _Thread_local {callback.binding.context_type_symbol} *",
                        CodeExpression("NULL"),
                    ),
                )
            )
        return tuple(declarations)

    def _callback_runtime_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Emit one fatal helper and one typed trampoline per callback site."""
        return tuple(
            function
            for callback in self._callback_sites(plan)
            for function in (
                self._callback_abort_function(callback),
                self._callback_trampoline_function(callback),
            )
        )

    @staticmethod
    def _callback_abort_function(callback: CallbackHandoffPlan) -> CFunction:
        """Emit the single non-returning traceback boundary for one site."""
        return CFunction(
            callback.binding.abort_symbol,
            "void",
            parameters=(CParameter("message", "const char *"),),
            storage="static",
            body=(
                CIf(
                    CodeExpression("!PyErr_Occurred()"),
                    body=(CExpressionStatement(CodeExpression("PyErr_SetString(PyExc_RuntimeError, message)")),),
                ),
                CExpressionStatement(CodeExpression("PyErr_PrintEx(0)")),
                CExpressionStatement(CodeExpression("abort()")),
            ),
        )

    def _callback_trampoline_function(self, callback: CallbackHandoffPlan) -> CFunction:
        """Convert one typed native callback invocation into a Python call."""
        context = "callback_context"
        gil = "callback_gil"
        nodes = [
            CDeclaration(
                context,
                f"{callback.binding.context_type_symbol} *",
                CodeExpression(callback.binding.context_current_symbol),
            ),
            CIf(
                CodeExpression(f"{context} == NULL || {context}->thread_id != PyThread_get_thread_ident()"),
                body=(
                    CExpressionStatement(CodeExpression("PyGILState_Ensure()")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_RuntimeError, "callback invoked outside its entering Python thread")'
                        )
                    ),
                    CExpressionStatement(
                        CodeExpression(f'{callback.binding.abort_symbol}("callback thread violation")')
                    ),
                ),
            ),
            CDeclaration(gil, "PyGILState_STATE", CodeExpression("PyGILState_Ensure()")),
            CDeclaration(
                "callback_args",
                "PyObject *",
                CodeExpression(f"PyTuple_New({len(callback.arguments)})"),
            ),
            self._callback_abort_if_null(callback, "callback_args", "failed to allocate callback arguments"),
        ]
        for position, transfer in enumerate(callback.arguments):
            argument_name = f"callback_arg_{position}"
            nodes.extend(self._callback_python_argument_nodes(callback, transfer, position, argument_name))
            nodes.append(
                CExpressionStatement(CodeExpression(f"PyTuple_SET_ITEM(callback_args, {position}, {argument_name})"))
            )
        nodes.extend(
            (
                CDeclaration(
                    "callback_result",
                    "PyObject *",
                    CodeExpression(f"PyObject_CallObject({context}->callable, callback_args)"),
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(callback_args)")),
                self._callback_abort_if_null(
                    callback,
                    "callback_result",
                    "Python callback raised an exception",
                ),
                *self._callback_result_nodes(callback, context, gil),
            )
        )
        operation = callback.entrypoint.support_procedure
        return CFunction(
            operation.symbol_name,
            self._support_procedure_c_type(operation.signature.result),
            parameters=tuple(
                self._support_procedure_c_parameter(parameter) for parameter in operation.signature.parameters
            ),
            body=tuple(nodes),
        )

    @staticmethod
    def _callback_abort_if_null(
        callback: CallbackHandoffPlan,
        name: str,
        message: str,
    ) -> CIf:
        """Build callback abort if null from the supplied local lowering values; emitted nodes only project completed binding actions."""
        return CIf(
            CodeExpression(f"{name} == NULL"),
            body=(CExpressionStatement(CodeExpression(f'{callback.binding.abort_symbol}("{message}")')),),
        )

    def _callback_python_argument_nodes(
        self,
        callback: CallbackHandoffPlan,
        transfer: CallbackTransferPlan,
        position: int,
        target: str,
    ) -> tuple:
        """Dispatch one completed Python projection into a small conversion leaf."""
        match transfer.python_action:
            case PythonBarrierAction.SCALAR_VALUE:
                nodes = self._callback_scalar_value_nodes(transfer, target)
            case PythonBarrierAction.ARRAY_STORAGE:
                nodes = self._callback_array_nodes(transfer, position, target)
            case PythonBarrierAction.STRING_STORAGE:
                nodes = self._callback_string_nodes(transfer, target)
            case PythonBarrierAction.WRAPPER_INSTANCE:
                nodes = self._callback_derived_nodes(transfer, position, target)
            case _:
                raise ValueError(
                    f"Unsupported C callback Python projection for {transfer.owner_path!r}: "
                    f"{transfer.python_action.value}"
                )
        return (
            *nodes,
            self._callback_abort_if_null(callback, target, "failed to convert callback argument"),
        )

    def _callback_scalar_value_nodes(
        self,
        transfer: CallbackTransferPlan,
        target: str,
    ) -> tuple[CDeclaration, ...]:
        """Materialize one completed scalar-value projection as a NumPy scalar."""
        scalar = PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name)
        parameter = self._callback_parameter_base_name(transfer)
        value_pointer = {
            CallbackABIKind.VALUE: f"&{parameter}",
            CallbackABIKind.REFERENCE: f"{parameter}_data",
        }.get(transfer.abi)
        if value_pointer is None:
            raise ValueError(f"Unsupported scalar callback ABI for {transfer.owner_path!r}: {transfer.abi.value}")
        return (
            CDeclaration(
                target,
                "PyObject *",
                CodeExpression(f"prik_{self._scalar_helper_suffix(scalar)}_to_numpy({value_pointer})"),
            ),
        )

    def _callback_array_nodes(
        self,
        transfer: CallbackTransferPlan,
        position: int,
        target: str,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Build callback array nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        scalar = PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name)
        rank = transfer.rank
        dimensions = f"callback_dims_{position}"
        strides = f"callback_strides_{position}"
        base = self._callback_parameter_base_name(transfer)
        flags = "NPY_ARRAY_F_CONTIGUOUS | NPY_ARRAY_ALIGNED"
        if transfer.adapter_action in {
            CallbackTransferAction.COPY_OUT,
            CallbackTransferAction.COPY_IN_OUT,
            CallbackTransferAction.BORROW_WRITABLE,
        }:
            flags += " | NPY_ARRAY_WRITEABLE"
        nodes: list[CDeclaration | CExpressionStatement] = [
            CDeclaration(
                f"{dimensions}[{rank}]",
                "npy_intp",
                CodeExpression("{" + ", ".join(f"(npy_intp){base}_extent_{axis}" for axis in range(rank)) + "}"),
            ),
            CDeclaration(f"{strides}[{rank}]", "npy_intp"),
            CExpressionStatement(CodeExpression(f"{strides}[0] = (npy_intp)sizeof({scalar.c_spelling})")),
        ]
        nodes.extend(
            CExpressionStatement(
                CodeExpression(f"{strides}[{axis}] = {strides}[{axis - 1}] * {dimensions}[{axis - 1}]")
            )
            for axis in range(1, rank)
        )
        nodes.append(
            CDeclaration(
                target,
                "PyObject *",
                CodeExpression(
                    f"PyArray_New(&PyArray_Type, {rank}, {dimensions}, {scalar.numpy_type_macro}, "
                    f"{strides}, {base}_data, 0, {flags}, NULL)"
                ),
            )
        )
        return tuple(nodes)

    def _callback_string_nodes(
        self,
        transfer: CallbackTransferPlan,
        target: str,
    ) -> tuple[CDeclaration, ...]:
        """Build callback string nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        base = self._callback_parameter_base_name(transfer)
        if transfer.adapter_action is CallbackTransferAction.COPY_IN:
            expression = f"PyUnicode_FromStringAndSize((const char *){base}_data, (Py_ssize_t){base}_length)"
        else:
            expression = (
                f"PyArray_New(&PyArray_Type, 0, NULL, NPY_STRING, NULL, {base}_data, "
                f"(int){base}_length, NPY_ARRAY_ALIGNED | NPY_ARRAY_WRITEABLE, NULL)"
            )
        return (CDeclaration(target, "PyObject *", CodeExpression(expression)),)

    def _callback_derived_nodes(
        self,
        transfer: CallbackTransferPlan,
        position: int,
        target: str,
    ) -> tuple:
        """Build callback derived nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        symbol = transfer.derived_backend_symbol
        if symbol is None:
            raise ValueError(f"Callback derived argument {transfer.owner_path!r} has no backend symbol")
        base = self._callback_parameter_base_name(transfer)
        capsule = f"callback_capsule_{position}"
        helper = f"callback_helper_{position}"
        return (
            CDeclaration(
                capsule,
                "PyObject *",
                CodeExpression(f'PyCapsule_New({base}_data, "{self._derived_capsule_name(symbol)}", NULL)'),
            ),
            CDeclaration(
                helper,
                "PyObject *",
                CodeExpression(
                    f'PyObject_GetAttrString(callback_context->module, "_prik_wrap_{transfer.semantic_type_name}")'
                ),
            ),
            CDeclaration(
                target,
                "PyObject *",
                CodeExpression(
                    f"({capsule} != NULL && {helper} != NULL) ? "
                    f"PyObject_CallFunctionObjArgs({helper}, {capsule}, NULL) : NULL"
                ),
            ),
            CExpressionStatement(CodeExpression(f"Py_XDECREF({helper})")),
            CExpressionStatement(CodeExpression(f"Py_XDECREF({capsule})")),
        )

    def _callback_result_nodes(
        self,
        callback: CallbackHandoffPlan,
        context: str,
        gil: str,
    ) -> tuple:
        """Dispatch one completed callback result action without trial conversion."""
        action = callback.result.action
        if action is CallbackResultAction.RETURN_VOID:
            return self._callback_void_result_nodes(callback, gil)
        transfer = callback.result.transfer
        if transfer is None:
            raise ValueError(f"Callback result {callback.owner_path!r} has no transfer plan")
        if action is CallbackResultAction.RETURN_SCALAR:
            return self._callback_scalar_result_nodes(callback, transfer, gil)
        if action is CallbackResultAction.RETURN_ARRAY_ADDRESS:
            return self._callback_array_result_nodes(callback, transfer, context, gil)
        if action is CallbackResultAction.RETURN_DERIVED_ADDRESS:
            return self._callback_derived_result_nodes(callback, transfer, context, gil)
        raise ValueError(f"Unsupported C callback result action: {action.value}")

    @staticmethod
    def _callback_void_result_nodes(callback: CallbackHandoffPlan, gil: str) -> tuple:
        """Build callback void result nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        return (
            CIf(
                CodeExpression("callback_result != Py_None"),
                body=(
                    CExpressionStatement(
                        CodeExpression('PyErr_SetString(PyExc_TypeError, "callback subroutine must return None")')
                    ),
                    CExpressionStatement(
                        CodeExpression(f'{callback.binding.abort_symbol}("invalid callback return value")')
                    ),
                ),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(callback_result)")),
            CExpressionStatement(CodeExpression(f"PyGILState_Release({gil})")),
            CReturn(),
        )

    def _callback_scalar_result_nodes(
        self,
        callback: CallbackHandoffPlan,
        transfer: CallbackTransferPlan,
        gil: str,
    ) -> tuple:
        """Build callback scalar result nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        scalar = PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name)
        return (
            CDeclaration(
                "callback_value",
                scalar.c_spelling,
            ),
            CIf(
                CodeExpression(self._scalar_unpack_expression(scalar, "callback_result", "callback_value") + " < 0"),
                body=(
                    CExpressionStatement(
                        CodeExpression(f'{callback.binding.abort_symbol}("invalid callback return value")')
                    ),
                ),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(callback_result)")),
            CExpressionStatement(CodeExpression(f"PyGILState_Release({gil})")),
            CReturn(CodeExpression("callback_value")),
        )

    def _callback_array_result_nodes(
        self,
        callback: CallbackHandoffPlan,
        transfer: CallbackTransferPlan,
        context: str,
        gil: str,
    ) -> tuple:
        """Build callback array result nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        scalar = PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name)
        shape = transfer.array.shape if transfer.array is not None else ()
        invalid = [
            "!PyArray_Check(callback_result)",
            f"PyArray_TYPE((PyArrayObject *)callback_result) != {scalar.numpy_type_macro}",
            f"PyArray_NDIM((PyArrayObject *)callback_result) != {transfer.rank}",
            "!PyArray_IS_F_CONTIGUOUS((PyArrayObject *)callback_result)",
        ]
        invalid.extend(
            "PyArray_DIM((PyArrayObject *)callback_result, "
            f"{axis}) != (npy_intp)({self._callback_extent_value_expression(callback, extent)})"
            for axis, extent in enumerate(shape)
        )
        return (
            CIf(
                CodeExpression(" || ".join(invalid)),
                body=(
                    CExpressionStatement(
                        CodeExpression('PyErr_SetString(PyExc_TypeError, "invalid callback array result")')
                    ),
                    CExpressionStatement(
                        CodeExpression(f'{callback.binding.abort_symbol}("invalid callback return value")')
                    ),
                ),
            ),
            CExpressionStatement(CodeExpression(f"Py_XDECREF({context}->last_result)")),
            CExpressionStatement(CodeExpression(f"{context}->last_result = callback_result")),
            CDeclaration(
                "callback_value",
                "void *",
                CodeExpression("PyArray_DATA((PyArrayObject *)callback_result)"),
            ),
            CExpressionStatement(CodeExpression(f"PyGILState_Release({gil})")),
            CReturn(CodeExpression("callback_value")),
        )

    def _callback_extent_value_expression(
        self,
        callback: CallbackHandoffPlan,
        extent: str,
    ) -> str:
        """Spell one completed callback extent source in the flattened C ABI."""
        substitutions = {}
        for source in callback.arguments:
            base = self._callback_parameter_base_name(source)
            if source.abi is CallbackABIKind.VALUE:
                substitutions[source.name] = base
            elif source.abi is CallbackABIKind.REFERENCE:
                scalar = PrimitiveScalarTypeRegistry.type_for(source.semantic_type_name)
                substitutions[source.name] = f"*(({scalar.c_spelling} *){base}_data)"
        return render_declaration_extent(extent, substitutions, target="c")

    def _callback_derived_result_nodes(
        self,
        callback: CallbackHandoffPlan,
        transfer: CallbackTransferPlan,
        context: str,
        gil: str,
    ) -> tuple:
        """Build callback derived result nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        symbol = transfer.derived_backend_symbol
        if symbol is None:
            raise ValueError(f"Callback derived result {transfer.owner_path!r} has no backend symbol")
        return (
            CDeclaration(
                "callback_expected_type",
                "PyObject *",
                CodeExpression(f'PyObject_GetAttrString({context}->module, "{transfer.semantic_type_name}")'),
            ),
            self._callback_abort_if_null(
                callback,
                "callback_expected_type",
                "failed to resolve callback result type",
            ),
            CIf(
                CodeExpression("Py_TYPE(callback_result) != (PyTypeObject *)callback_expected_type"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_TypeError, "callback must return {transfer.semantic_type_name}")'
                        )
                    ),
                    CExpressionStatement(
                        CodeExpression(f'{callback.binding.abort_symbol}("invalid callback return value")')
                    ),
                ),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(callback_expected_type)")),
            CDeclaration(
                "callback_capsule",
                "PyObject *",
                CodeExpression('PyObject_GetAttrString(callback_result, "_prik_capsule")'),
            ),
            self._callback_abort_if_null(
                callback,
                "callback_capsule",
                "callback result has no native capsule",
            ),
            CDeclaration(
                "callback_value",
                "void *",
                CodeExpression(f'PyCapsule_GetPointer(callback_capsule, "{self._derived_capsule_name(symbol)}")'),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(callback_capsule)")),
            self._callback_abort_if_null(
                callback,
                "callback_value",
                "callback result capsule is invalid",
            ),
            CExpressionStatement(CodeExpression(f"Py_XDECREF({context}->last_result)")),
            CExpressionStatement(CodeExpression(f"{context}->last_result = callback_result")),
            CExpressionStatement(CodeExpression(f"PyGILState_Release({gil})")),
            CReturn(CodeExpression("callback_value")),
        )

    @staticmethod
    def _callback_parameter_base_name(transfer: CallbackTransferPlan) -> str:
        """Return the binding-local callback parameter base name derived from the supplied local lowering values; this helper preserves completed policy."""
        return re.sub(r"\W", "_", transfer.name).casefold()

    # Shared scalar-derived runtime dispatch.
    def _derived_call_runtime_declarations(self, plan: ModulePlan) -> tuple:
        """Declare the one table-driven origin ABI shared by every derived type."""
        if not (self._module_uses_derived_calls(plan) or self._module_uses_derived_origin_ops(plan)):
            return ()
        return (
            CFunctionPointerType("prik_derived_consumer_fn", "int", ("void *", "void *")),
            CFunctionPointerType(
                "prik_derived_scoped_fn",
                "int",
                ("prik_derived_consumer_fn", "void *"),
            ),
            CFunctionPointerType("prik_derived_checkout_fn", "int", ("void **",)),
            CFunctionPointerType("prik_derived_restore_fn", "int", ("void *",)),
            CFunctionPointerType("prik_derived_present_fn", "int"),
            CFunctionPointerType("prik_derived_address_fn", "void *"),
            CStructDefinition(
                "prik_derived_origin_ops",
                (
                    CParameter("type_symbol", "const char *"),
                    CParameter("present", "prik_derived_present_fn"),
                    CParameter("address", "prik_derived_address_fn"),
                    CParameter("scoped", "prik_derived_scoped_fn"),
                    CParameter("checkout", "prik_derived_checkout_fn"),
                    CParameter("restore", "prik_derived_restore_fn"),
                ),
            ),
            CStructDefinition(
                "prik_derived_call_case",
                (
                    CParameter("origin", "const char *"),
                    CParameter("access", "int"),
                    CParameter("capsule_name", "const char *"),
                    CParameter("uses_ops", "int"),
                    CParameter("requires_present", "int"),
                    CParameter("failure_kind", "const char *"),
                    CParameter("failure_message", "const char *"),
                ),
            ),
            *(
                (
                    CStructDefinition(
                        "prik_derived_alias_entry",
                        (
                            CParameter("identity", "void *"),
                            CParameter("writable", "int"),
                            CParameter("argument_name", "const char *"),
                        ),
                    ),
                )
                if self._module_uses_derived_alias_validation(plan)
                else ()
            ),
            *(
                self._derived_call_case_declaration(argument)
                for function in self._functions(plan)
                for argument in function.arguments
                if argument.derived_call is not None
            ),
        )

    def _derived_call_case_declaration(self, argument: ArgumentTransferPlan) -> CDeclaration:
        """Materialize one completed exhaustive matrix as immutable runtime data."""
        rows = ", ".join(self._derived_call_case_initializer(argument, case) for case in argument.derived_call.cases)
        return CDeclaration(
            f"{self._derived_call_case_table_name(argument)}[]",
            "static const prik_derived_call_case",
            CodeExpression("{" + rows + "}"),
        )

    def _derived_call_case_initializer(self, argument: ArgumentTransferPlan, case) -> str:
        """Return derived call case initializer from the supplied completed binding records; this helper preserves the selected binding behavior."""
        uses_ops = case.actual_storage in {
            DerivedObjectStorage.MODULE_PROXY,
            DerivedObjectStorage.MODULE_ALLOCATABLE,
            DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
            DerivedObjectStorage.MODULE_POINTER,
        }
        capsule_name = self._derived_case_capsule_name(argument, case.actual_storage)
        fields = (
            self._c_string_literal(case.actual_storage.value),
            str(case.abi_code),
            self._c_string_literal(capsule_name) if capsule_name is not None else "NULL",
            "1" if uses_ops else "0",
            "1" if case.requires_present else "0",
            self._c_string_literal(case.failure_kind) if case.failure_kind is not None else "NULL",
            self._c_string_literal(case.failure_message) if case.failure_message is not None else "NULL",
        )
        return "{" + ", ".join(fields) + "}"

    def _derived_case_capsule_name(
        self,
        argument: ArgumentTransferPlan,
        storage: DerivedObjectStorage,
    ) -> str | None:
        """Return the binding-local derived case capsule name derived from the supplied completed binding records; this helper preserves completed policy."""
        if argument.derived is None:
            raise ValueError(f"Derived argument {argument.owner_path!r} has no handoff")
        if storage in {DerivedObjectStorage.DIRECT, DerivedObjectStorage.MODULE_TARGET}:
            return self._derived_capsule_name(argument.derived.backend_symbol)
        if storage is DerivedObjectStorage.ALLOCATABLE_HOLDER:
            return self._allocatable_holder_capsule_name(argument.derived.backend_symbol)
        if storage is DerivedObjectStorage.POINTER_HOLDER:
            return self._pointer_holder_capsule_name(argument.derived.backend_symbol)
        return None

    @staticmethod
    def _derived_call_case_table_name(argument: ArgumentTransferPlan) -> str:
        """Return the binding-local derived call case table name derived from the supplied completed binding records; this helper preserves completed policy."""
        symbol = re.sub(r"\W", "_", argument.owner_path).casefold()
        return f"prik_derived_cases_{symbol}"

    def _derived_call_runtime_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Emit one generic extractor; per-type differences live only in table data."""
        if not self._module_uses_derived_calls(plan):
            return ()
        return (
            self._derived_argument_extractor_function(),
            *((self._derived_alias_validator_function(),) if self._module_uses_derived_alias_validation(plan) else ()),
        )

    def _derived_alias_validator_function(self) -> CFunction:
        """Reject repeated writable origins before any native transaction starts."""
        return CFunction(
            "prik_validate_derived_aliases",
            "int",
            parameters=(
                CParameter("entries", "const prik_derived_alias_entry *"),
                CParameter("count", "size_t"),
            ),
            storage="static",
            body=(
                CFor(
                    "size_t left = 0",
                    CodeExpression("left < count"),
                    CodeExpression("++left"),
                    body=(
                        CIf(
                            CodeExpression("entries[left].identity != NULL"),
                            body=(
                                CFor(
                                    "size_t right = left + 1",
                                    CodeExpression("right < count"),
                                    CodeExpression("++right"),
                                    body=(
                                        CIf(
                                            CodeExpression(
                                                "entries[left].identity == entries[right].identity && "
                                                "(entries[left].writable || entries[right].writable)"
                                            ),
                                            body=(
                                                CExpressionStatement(
                                                    CodeExpression(
                                                        'PyErr_Format(PyExc_TypeError, "derived origin is repeated in '
                                                        'writable arguments %s and %s", entries[left].argument_name, '
                                                        "entries[right].argument_name)"
                                                    )
                                                ),
                                                CReturn(CodeExpression("-1")),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                CReturn(CodeExpression("0")),
            ),
        )

    def _derived_argument_extractor_function(self) -> CFunction:
        """Build derived argument extractor function from the supplied local lowering values; emitted nodes only project completed binding actions."""
        return CFunction(
            "prik_extract_derived_argument",
            "int",
            parameters=(
                CParameter("object", "PyObject *"),
                CParameter("type_name", "const char *"),
                CParameter("type_symbol", "const char *"),
                CParameter("direct_capsule_name", "const char *"),
                CParameter("argument_name", "const char *"),
                CParameter("cases", "const prik_derived_call_case *"),
                CParameter("case_count", "size_t"),
                CParameter("carrier", "void **"),
                CParameter("access", "int *"),
                CParameter("ops", "prik_derived_origin_ops **"),
            ),
            storage="static",
            body=(
                CExpressionStatement(CodeExpression("*carrier = NULL")),
                CExpressionStatement(CodeExpression("*access = 0")),
                CExpressionStatement(CodeExpression("*ops = NULL")),
                CDeclaration(
                    "origin_object",
                    "PyObject *",
                    CodeExpression('PyObject_GetAttrString(object, "_prik_origin")'),
                ),
                CIf(
                    CodeExpression("origin_object == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("PyErr_Clear()")),
                        CExpressionStatement(
                            CodeExpression(
                                'PyErr_Format(PyExc_TypeError, "Expected exact wrapper type %s for argument %s", '
                                "type_name, argument_name)"
                            )
                        ),
                        CReturn(CodeExpression("-1")),
                    ),
                ),
                CDeclaration("origin", "const char *", CodeExpression("PyUnicode_AsUTF8(origin_object)")),
                CIf(
                    CodeExpression("origin == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                        CReturn(CodeExpression("-1")),
                    ),
                ),
                CDeclaration(
                    "selected",
                    "const prik_derived_call_case *",
                    CodeExpression("NULL"),
                ),
                CFor(
                    "size_t index = 0",
                    CodeExpression("index < case_count"),
                    CodeExpression("++index"),
                    body=(
                        CIf(
                            CodeExpression("strcmp(origin, cases[index].origin) == 0"),
                            body=(
                                CExpressionStatement(CodeExpression("selected = &cases[index]")),
                                CBreak(),
                            ),
                        ),
                    ),
                ),
                CIf(
                    CodeExpression("selected == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                        CExpressionStatement(
                            CodeExpression(
                                'PyErr_Format(PyExc_TypeError, "Unknown native origin %s for argument %s", '
                                "origin, argument_name)"
                            )
                        ),
                        CReturn(CodeExpression("-1")),
                    ),
                ),
                CIf(
                    CodeExpression("selected->access == 0"),
                    body=(
                        CExpressionStatement(
                            CodeExpression(
                                'PyErr_Format(PyExc_TypeError, "%s: %s", selected->failure_kind, '
                                "selected->failure_message)"
                            )
                        ),
                        CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                        CReturn(CodeExpression("-1")),
                    ),
                ),
                *self._derived_argument_origin_extraction_nodes(),
                CExpressionStatement(CodeExpression("*access = selected->access")),
                CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                CReturn(CodeExpression("0")),
            ),
        )

    def _derived_argument_origin_extraction_nodes(self) -> tuple[CIf, ...]:
        """Dispatch carrier extraction solely from the selected completed row."""
        return (
            CIf(
                CodeExpression("selected->uses_ops"),
                body=self._derived_argument_ops_extraction_nodes(),
                else_body=self._derived_argument_capsule_extraction_nodes(),
            ),
            CIf(
                CodeExpression(
                    "*ops != NULL && ((*ops)->type_symbol == NULL || strcmp((*ops)->type_symbol, type_symbol) != 0)"
                ),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_Format(PyExc_TypeError, "Expected exact wrapper type %s for argument %s", '
                            "type_name, argument_name)"
                        )
                    ),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CIf(
                CodeExpression(
                    "selected->requires_present && *ops != NULL && (*ops)->present != NULL && !(*ops)->present()"
                ),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", '
                            "argument_name)"
                        )
                    ),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CIf(
                CodeExpression("selected->requires_present && selected->access == 1 && *carrier == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", '
                            "argument_name)"
                        )
                    ),
                    CReturn(CodeExpression("-1")),
                ),
            ),
        )

    def _derived_argument_ops_extraction_nodes(self) -> tuple:
        """Build derived argument ops extraction nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        return (
            CDeclaration(
                "operation_map",
                "PyObject *",
                CodeExpression('PyObject_GetAttrString(object, "_prik_ops")'),
            ),
            CIf(
                CodeExpression("operation_map == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CDeclaration(
                "ops_capsule",
                "PyObject *",
                CodeExpression('PyDict_GetItemString(operation_map, "_native_ops")'),
            ),
            CIf(
                CodeExpression("ops_capsule == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(operation_map)")),
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_Format(PyExc_TypeError, "module origin for argument %s has no native operations", '
                            "argument_name)"
                        )
                    ),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CExpressionStatement(
                CodeExpression(
                    '*ops = (prik_derived_origin_ops *)PyCapsule_GetPointer(ops_capsule, "prik.derived_origin_ops")'
                )
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(operation_map)")),
            CIf(
                CodeExpression("*ops == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CIf(
                CodeExpression("selected->access == 1"),
                body=(
                    CIf(
                        CodeExpression("(*ops)->address == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                            CExpressionStatement(
                                CodeExpression(
                                    'PyErr_Format(PyExc_RuntimeError, "module origin for argument %s has no address operation", '
                                    "argument_name)"
                                )
                            ),
                            CReturn(CodeExpression("-1")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression("*carrier = (*ops)->address()")),
                ),
            ),
        )

    def _derived_argument_capsule_extraction_nodes(self) -> tuple:
        """Build derived argument capsule extraction nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        return (
            CDeclaration(
                "capsule_name",
                "const char *",
                CodeExpression("selected->access == 1 ? direct_capsule_name : selected->capsule_name"),
            ),
            CDeclaration(
                "carrier_capsule",
                "PyObject *",
                CodeExpression('PyObject_GetAttrString(object, "_prik_capsule")'),
            ),
            CIf(
                CodeExpression("carrier_capsule == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CIf(
                CodeExpression("!PyCapsule_IsValid(carrier_capsule, capsule_name)"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(carrier_capsule)")),
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_Format(PyExc_TypeError, "Expected exact wrapper type %s for argument %s", '
                            "type_name, argument_name)"
                        )
                    ),
                    CReturn(CodeExpression("-1")),
                ),
            ),
            CExpressionStatement(CodeExpression("*carrier = PyCapsule_GetPointer(carrier_capsule, capsule_name)")),
            CExpressionStatement(CodeExpression("Py_DECREF(carrier_capsule)")),
            CIf(
                CodeExpression("*carrier == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("Py_DECREF(origin_object)")),
                    CReturn(CodeExpression("-1")),
                ),
            ),
        )

    # Typed module-origin operation tables.
    def _derived_origin_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return derived origin variables from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return tuple(variable for variable in self._variables(plan) if variable.derived is not None)

    def _derived_origin_declarations(self, plan: ModulePlan) -> tuple:
        """Declare raw Fortran operations and one typed table per module origin."""
        declarations = []
        for variable in self._derived_origin_variables(plan):
            declarations.extend(self._derived_origin_bridge_prototypes(variable))
            declarations.extend(self._derived_origin_wrapper_prototypes(variable))
            declarations.append(
                CFunctionPrototype(
                    self._derived_origin_capsule_method_name(variable),
                    "PyObject *",
                    (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                    storage="static",
                )
            )
            if self._derived_origin_needs_guard(variable):
                declarations.extend(
                    (
                        CDeclaration(
                            self._derived_origin_active_name(variable),
                            "static atomic_bool",
                            CodeExpression("false"),
                        ),
                        CDeclaration(
                            self._derived_origin_poisoned_name(variable),
                            "static atomic_bool",
                            CodeExpression("false"),
                        ),
                    )
                )
            operations = ", ".join(
                self._derived_origin_wrapper_name(variable, operation)
                if self._derived_origin_supports(variable, operation)
                else "NULL"
                for operation in ("present", "address", "scoped", "checkout", "restore")
            )
            type_symbol = self._c_string_literal(variable.derived.handoff.backend_symbol)
            declarations.append(
                CDeclaration(
                    self._derived_origin_table_name(variable),
                    "static prik_derived_origin_ops",
                    CodeExpression("{" + type_symbol + ", " + operations + "}"),
                )
            )
        return tuple(declarations)

    def _derived_origin_bridge_prototypes(self, variable: ModuleVariablePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare planner-owned derived-origin bridge operations."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for operation in self._generated_support_procedure_entrypoints_for(variable.owner_path, "derived_origin:")
        )

    def _derived_origin_wrapper_prototypes(self, variable: ModuleVariablePlan) -> tuple[CFunctionPrototype, ...]:
        """Return the binding-local derived origin wrapper prototypes derived from the supplied completed binding records; this helper preserves completed policy."""
        return tuple(
            CFunctionPrototype(
                self._derived_origin_wrapper_name(variable, operation),
                "void *" if operation == "address" else "int",
                self._derived_origin_operation_parameters(operation),
                storage="static",
            )
            for operation in ("present", "address", "scoped", "checkout", "restore")
            if self._derived_origin_supports(variable, operation)
        )

    @staticmethod
    def _derived_origin_operation_parameters(operation: str) -> tuple[CParameter, ...]:
        """Build derived origin operation parameters from the supplied local lowering values; emitted nodes only project completed binding actions."""
        if operation == "scoped":
            return (
                CParameter("consumer", "prik_derived_consumer_fn"),
                CParameter("context", "void *"),
            )
        if operation == "checkout":
            return (CParameter("holder", "void **"),)
        if operation == "restore":
            return (CParameter("holder", "void *"),)
        return ()

    def _derived_origin_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Build derived origin functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return tuple(
            function
            for variable in self._derived_origin_variables(plan)
            for function in (
                *(
                    self._derived_origin_operation_function(variable, operation)
                    for operation in ("present", "address", "scoped", "checkout", "restore")
                    if self._derived_origin_supports(variable, operation)
                ),
                self._derived_origin_capsule_method(variable),
            )
        )

    def _derived_origin_operation_function(self, variable: ModuleVariablePlan, operation: str) -> CFunction:
        """Build derived origin operation function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        builders = {
            "present": self._derived_origin_present_function,
            "address": self._derived_origin_address_function,
            "scoped": self._derived_origin_scoped_function,
            "checkout": self._derived_origin_checkout_function,
            "restore": self._derived_origin_restore_function,
        }
        return builders[operation](variable)

    def _derived_origin_present_function(self, variable: ModuleVariablePlan) -> CFunction:
        """Build derived origin present function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return CFunction(
            self._derived_origin_wrapper_name(variable, "present"),
            "int",
            storage="static",
            body=(CReturn(CodeExpression(f"{self._derived_origin_bridge_name(variable, 'present')}() ? 1 : 0")),),
        )

    def _derived_origin_address_function(self, variable: ModuleVariablePlan) -> CFunction:
        """Build derived origin address function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return CFunction(
            self._derived_origin_wrapper_name(variable, "address"),
            "void *",
            storage="static",
            body=(CReturn(CodeExpression(f"{self._derived_origin_bridge_name(variable, 'address')}()")),),
        )

    def _derived_origin_scoped_function(self, variable: ModuleVariablePlan) -> CFunction:
        """Build derived origin scoped function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        active = self._derived_origin_active_name(variable)
        poisoned = self._derived_origin_poisoned_name(variable)
        fault = "prik_derived_fault"
        return CFunction(
            self._derived_origin_wrapper_name(variable, "scoped"),
            "int",
            parameters=self._derived_origin_operation_parameters("scoped"),
            storage="static",
            body=(
                self._derived_origin_fault_declaration(fault),
                self._derived_origin_fault_return(variable, "scoped", "before", fault),
                CIf(CodeExpression(f"atomic_load(&{poisoned})"), body=(CReturn(CodeExpression("3")),)),
                CDeclaration("expected", "bool", CodeExpression("false")),
                CIf(
                    CodeExpression(f"!atomic_compare_exchange_strong(&{active}, &expected, true)"),
                    body=(CReturn(CodeExpression("2")),),
                ),
                CDeclaration(
                    "status",
                    "int",
                    CodeExpression(f"{self._derived_origin_bridge_name(variable, 'scoped')}(consumer, context)"),
                ),
                self._derived_origin_fault_status(variable, "scoped", "after", fault),
                CExpressionStatement(CodeExpression(f"atomic_store(&{active}, false)")),
                CReturn(CodeExpression("status")),
            ),
        )

    def _derived_origin_checkout_function(self, variable: ModuleVariablePlan) -> CFunction:
        """Build derived origin checkout function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        active = self._derived_origin_active_name(variable)
        poisoned = self._derived_origin_poisoned_name(variable)
        fault = "prik_derived_fault"
        return CFunction(
            self._derived_origin_wrapper_name(variable, "checkout"),
            "int",
            parameters=self._derived_origin_operation_parameters("checkout"),
            storage="static",
            body=(
                self._derived_origin_fault_declaration(fault),
                self._derived_origin_fault_return(variable, "checkout", "before", fault),
                CIf(CodeExpression(f"atomic_load(&{poisoned})"), body=(CReturn(CodeExpression("3")),)),
                CDeclaration("expected", "bool", CodeExpression("false")),
                CIf(
                    CodeExpression(f"!atomic_compare_exchange_strong(&{active}, &expected, true)"),
                    body=(CReturn(CodeExpression("2")),),
                ),
                CDeclaration(
                    "status",
                    "int",
                    CodeExpression(f"{self._derived_origin_bridge_name(variable, 'checkout')}(holder)"),
                ),
                CIf(
                    CodeExpression("status != 0"),
                    body=(CExpressionStatement(CodeExpression(f"atomic_store(&{active}, false)")),),
                ),
                CReturn(CodeExpression("status")),
            ),
        )

    def _derived_origin_restore_function(self, variable: ModuleVariablePlan) -> CFunction:
        """Build derived origin restore function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        active = self._derived_origin_active_name(variable)
        poisoned = self._derived_origin_poisoned_name(variable)
        fault = "prik_derived_fault"
        return CFunction(
            self._derived_origin_wrapper_name(variable, "restore"),
            "int",
            parameters=self._derived_origin_operation_parameters("restore"),
            storage="static",
            body=(
                self._derived_origin_fault_declaration(fault),
                CIf(CodeExpression(f"!atomic_load(&{active})"), body=(CReturn(CodeExpression("6")),)),
                CDeclaration(
                    "status",
                    "int",
                    CodeExpression(f"{self._derived_origin_bridge_name(variable, 'restore')}(holder)"),
                ),
                self._derived_origin_fault_status(variable, "restore", "after", fault),
                CIf(
                    CodeExpression("status != 0"),
                    body=(CExpressionStatement(CodeExpression(f"atomic_store(&{poisoned}, true)")),),
                ),
                CExpressionStatement(CodeExpression(f"atomic_store(&{active}, false)")),
                CReturn(CodeExpression("status")),
            ),
        )

    @staticmethod
    def _derived_origin_fault_declaration(name: str) -> CDeclaration:
        """Read the opt-in failure selector used by transaction fault tests."""
        return CDeclaration(
            name,
            "const char *",
            CodeExpression('getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN")'),
        )

    def _derived_origin_fault_return(
        self,
        variable: ModuleVariablePlan,
        operation: str,
        phase: str,
        name: str,
    ) -> CIf:
        """Return derived origin fault return from the supplied completed binding records; this helper preserves the selected binding behavior."""
        selector = self._c_string_literal(f"{operation}:{phase}:{variable.symbol_name}")
        return CIf(
            CodeExpression(f"{name} != NULL && strcmp({name}, {selector}) == 0"),
            body=(CReturn(CodeExpression("7")),),
        )

    def _derived_origin_fault_status(
        self,
        variable: ModuleVariablePlan,
        operation: str,
        phase: str,
        name: str,
    ) -> CIf:
        """Return the binding-local derived origin fault status derived from the supplied completed binding records; this helper preserves completed policy."""
        selector = self._c_string_literal(f"{operation}:{phase}:{variable.symbol_name}")
        return CIf(
            CodeExpression(f"status == 0 && {name} != NULL && strcmp({name}, {selector}) == 0"),
            body=(CExpressionStatement(CodeExpression("status = 7")),),
        )

    def _derived_origin_capsule_method(self, variable: ModuleVariablePlan) -> CFunction:
        """Return derived origin capsule method from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return CFunction(
            self._derived_origin_capsule_method_name(variable),
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=(
                CReturn(
                    CodeExpression(
                        f"PyCapsule_New((void *)&{self._derived_origin_table_name(variable)}, "
                        '"prik.derived_origin_ops", NULL)'
                    )
                ),
            ),
        )

    def _derived_origin_supports(self, variable: ModuleVariablePlan, operation: str) -> bool:
        """Return whether planning registered one derived-origin operation."""
        return (variable.owner_path, f"derived_origin:{operation}") in self._generated_support_procedure_entrypoints

    def _derived_origin_needs_guard(self, variable: ModuleVariablePlan) -> bool:
        """Return derived origin needs guard from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return any(self._derived_origin_supports(variable, operation) for operation in ("scoped", "checkout"))

    @staticmethod
    def _derived_origin_symbol(variable: ModuleVariablePlan) -> str:
        """Return the binding-local derived origin symbol derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.derived_origin_symbol(variable)

    def _derived_origin_bridge_name(self, variable: ModuleVariablePlan, operation: str) -> str:
        """Return one planner-owned derived-origin entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(
            variable.owner_path, f"derived_origin:{operation}"
        ).symbol_name

    def _derived_origin_wrapper_name(self, variable: ModuleVariablePlan, operation: str) -> str:
        """Return the binding-local derived origin wrapper name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_origin_{self._derived_origin_symbol(variable)}_{operation}"

    def _derived_origin_table_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local derived origin table name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_origin_{self._derived_origin_symbol(variable)}_ops"

    def _derived_origin_active_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local derived origin active name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_origin_{self._derived_origin_symbol(variable)}_active"

    def _derived_origin_poisoned_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local derived origin poisoned name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_origin_{self._derived_origin_symbol(variable)}_poisoned"

    def _derived_origin_capsule_method_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local derived origin capsule method name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.derived_origin_capsule_method(variable)

    def _module_declarations(
        self,
        plan: ModulePlan,
    ) -> tuple[
        CComment | CDeclaration | CFunctionPrototype | CMethodDefTable | CModuleDef | CModulePropertySupport,
        ...,
    ]:
        """Return ordered bridge, helper, table, and module declarations."""
        return (
            *self._callback_runtime_declarations(plan),
            *self._derived_call_runtime_declarations(plan),
            *self._derived_origin_declarations(plan),
            *(self._entrypoint_prototype(function) for function in self._functions(plan)),
            *self._class_constructor_prototypes(plan),
            *(
                self._derived_destroy_entrypoint_prototype(derived)
                for derived in self._binding_owned_derived_types(plan)
            ),
            *(
                self._allocatable_holder_destroy_entrypoint_prototype(derived)
                for derived in self._binding_allocatable_holder_types(plan)
            ),
            *(
                self._pointer_holder_destroy_entrypoint_prototype(derived)
                for derived in self._binding_pointer_holder_types(plan)
            ),
            *(
                self._generated_support_procedure_entrypoint_prototype(
                    self._generated_support_procedure_entrypoint(derived.owner_path, "holder:allocatable:present")
                )
                for derived in self._binding_allocatable_holder_types(plan)
            ),
            *(
                self._generated_support_procedure_entrypoint_prototype(
                    self._generated_support_procedure_entrypoint(derived.owner_path, "holder:pointer:present")
                )
                for derived in self._binding_pointer_holder_types(plan)
            ),
            *self._owned_native_array_bridge_prototypes(plan),
            *self._default_native_array_bridge_prototypes(plan),
            *self._derived_field_bridge_prototypes(plan),
            *self._derived_private_method_prototypes(plan),
            *self._overload_dispatch_prototypes(plan),
            *self._derived_handle_operation_declarations(plan),
            *self._derived_module_owner_declarations(plan),
            *self._module_variable_declarations(plan),
            *self._native_array_operation_declarations(plan),
            *self._namespace_declarations(plan),
        )

    def _overload_dispatch_prototypes(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare namespace dispatchers before generated method tables use them."""
        return tuple(
            CFunctionPrototype(
                CBindingNames.overload_dispatch_function(dispatch.overload),
                "PyObject *",
                self._binding_parameters(),
                "static",
            )
            for namespace in plan.namespaces
            for dispatch in self._namespace_overload_dispatches(namespace)
        )

    def _module_variable_declarations(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Return bridge and binding helper declarations for module state."""
        variables = self._variables(plan)
        return (
            *(prototype for variable in variables for prototype in self._module_variable_bridge_prototypes(variable)),
            *(prototype for variable in variables for prototype in self._module_variable_helper_prototypes(variable)),
        )

    def _namespace_declarations(
        self,
        plan: ModulePlan,
    ) -> tuple[CMethodDefTable | CModuleDef | CModulePropertySupport, ...]:
        """Return method, module, and optional property declarations."""
        property_support = tuple(
            support
            for namespace in plan.namespaces
            if (support := self._module_property_support(plan, namespace)) is not None
        )
        return (
            *(self._method_table(plan, namespace) for namespace in plan.namespaces),
            *(self._module_def(plan, namespace) for namespace in plan.namespaces),
            *property_support,
        )

    def _derived_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return namespace-owned opaque types in stable plan order."""
        return tuple(derived for namespace in plan.namespaces for derived in namespace.derived_types)

    def _binding_derived_types(
        self,
        plan: ModulePlan,
        owner_paths: frozenset[str],
    ) -> tuple[DerivedTypePlan, ...]:
        """Join planner-owned binding support membership to derived records."""
        return tuple(derived for derived in self._derived_types(plan) if derived.owner_path in owner_paths)

    def _binding_owned_derived_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return planned direct-capsule owners in stable derived-type order."""
        return self._binding_derived_types(plan, self._binding_owned_derived_owner_paths)

    def _binding_allocatable_holder_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return planned allocatable-holder Python support owners."""
        return self._binding_derived_types(plan, self._binding_allocatable_holder_owner_paths)

    def _binding_pointer_holder_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return planned pointer-holder Python support owners."""
        return self._binding_derived_types(plan, self._binding_pointer_holder_owner_paths)

    def _derived_destroy_entrypoint_prototype(self, derived: DerivedTypePlan) -> CFunctionPrototype:
        """Declare the native-aware destroy helper for one opaque type."""
        return self._generated_support_procedure_entrypoint_prototype(
            self._generated_support_procedure_entrypoint(derived.owner_path, "derived:destroy")
        )

    def _allocatable_holder_destroy_entrypoint_prototype(self, derived: DerivedTypePlan) -> CFunctionPrototype:
        """Declare one typed holder destructor bridge."""
        return self._generated_support_procedure_entrypoint_prototype(
            self._generated_support_procedure_entrypoint(derived.owner_path, "holder:allocatable:destroy")
        )

    def _pointer_holder_destroy_entrypoint_prototype(self, derived: DerivedTypePlan) -> CFunctionPrototype:
        """Return the binding-local pointer holder destroy bridge prototype derived from the supplied local lowering values; this helper preserves completed policy."""
        return self._generated_support_procedure_entrypoint_prototype(
            self._generated_support_procedure_entrypoint(derived.owner_path, "holder:pointer:destroy")
        )

    def _derived_capsule_destructor_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Emit one capsule destructor that delegates to the native bridge."""
        direct = tuple(self._derived_capsule_destructor(derived) for derived in self._binding_owned_derived_types(plan))
        holders = tuple(
            self._allocatable_holder_capsule_destructor(derived)
            for derived in self._binding_allocatable_holder_types(plan)
        )
        pointers = tuple(
            self._pointer_holder_capsule_destructor(derived) for derived in self._binding_pointer_holder_types(plan)
        )
        return (*direct, *holders, *pointers)

    # Class construction reuses the Phase 8 direct derived owner path.
    def _class_constructor_prototypes(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare native allocators and their private Python entrypoints."""
        return tuple(
            prototype
            for namespace in plan.namespaces
            for surface in namespace.classes
            if self._has_generated_support_procedure_entrypoint(surface.owner_path, "class:create")
            for prototype in (
                self._generated_support_procedure_entrypoint_prototype(
                    self._generated_support_procedure_entrypoint(surface.owner_path, "class:create")
                ),
                CFunctionPrototype(
                    CBindingNames.class_create_method(surface),
                    "PyObject *",
                    (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                    "static",
                ),
            )
        )

    def _class_constructor_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Lower each completed class allocation into one compact C leaf."""
        derived_by_identity = {derived.type_identity: derived for derived in self._derived_types(plan)}
        return tuple(
            self._class_constructor_function(surface, derived_by_identity[surface.type_identity])
            for namespace in plan.namespaces
            for surface in namespace.classes
            if self._has_generated_support_procedure_entrypoint(surface.owner_path, "class:create")
        )

    def _class_constructor_function(
        self,
        surface: ClassSurfacePlan,
        derived: DerivedTypePlan,
    ) -> CFunction:
        """Allocate, capsule-own, and wrap one persistent native instance."""
        address = "address"
        capsule = "capsule"
        helper = "wrapper_helper"
        result = "result"
        destroy = self._generated_support_procedure_entrypoint(derived.owner_path, "derived:destroy").symbol_name
        create = self._generated_support_procedure_entrypoint(surface.owner_path, "class:create").symbol_name
        return CFunction(
            CBindingNames.class_create_method(surface),
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=(
                CIf(
                    CodeExpression('!PyArg_ParseTuple(args, "")'),
                    body=(CReturn(CodeExpression("NULL")),),
                ),
                CDeclaration(address, "void *", CodeExpression(f"{create}()")),
                CIf(
                    CodeExpression(f"{address} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CDeclaration(
                    capsule,
                    "PyObject *",
                    CodeExpression(
                        f'PyCapsule_New({address}, "{self._derived_capsule_name(derived.backend_symbol)}", '
                        f"{self._derived_capsule_destructor_name(derived.backend_symbol)})"
                    ),
                ),
                CIf(
                    CodeExpression(f"{capsule} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"{destroy}({address})")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CDeclaration(
                    helper,
                    "PyObject *",
                    CodeExpression(f'PyObject_GetAttrString(self, "{CBindingNames.class_wrap_helper(surface)}")'),
                ),
                CIf(
                    CodeExpression(f"{helper} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CDeclaration(
                    result,
                    "PyObject *",
                    CodeExpression(f"PyObject_CallFunctionObjArgs({helper}, {capsule}, NULL)"),
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({helper})")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                CReturn(CodeExpression(result)),
            ),
        )

    def _pointer_holder_capsule_destructor(self, derived: DerivedTypePlan) -> CFunction:
        """Return pointer holder capsule destructor from the supplied local lowering values; this helper preserves the selected binding behavior."""
        type_symbol = derived.backend_symbol
        return CFunction(
            self._pointer_holder_capsule_destructor_name(type_symbol),
            "void",
            parameters=(CParameter("capsule", "PyObject *"),),
            storage="static",
            body=(
                CDeclaration(
                    "address",
                    "void *",
                    CodeExpression(
                        f'PyCapsule_GetPointer(capsule, "{self._pointer_holder_capsule_name(type_symbol)}")'
                    ),
                ),
                CIf(
                    CodeExpression("address != NULL"),
                    body=(
                        CExpressionStatement(
                            CodeExpression(f"{self._pointer_holder_destroy_bridge_name(type_symbol)}(address)")
                        ),
                    ),
                    else_body=(CExpressionStatement(CodeExpression("PyErr_Clear()")),),
                ),
            ),
        )

    def _allocatable_holder_capsule_destructor(self, derived: DerivedTypePlan) -> CFunction:
        """Delegate holder cleanup to its typed Fortran destructor."""
        type_symbol = derived.backend_symbol
        return CFunction(
            self._allocatable_holder_capsule_destructor_name(type_symbol),
            "void",
            parameters=(CParameter("capsule", "PyObject *"),),
            storage="static",
            body=(
                CDeclaration(
                    "address",
                    "void *",
                    CodeExpression(
                        f'PyCapsule_GetPointer(capsule, "{self._allocatable_holder_capsule_name(type_symbol)}")'
                    ),
                ),
                CIf(
                    CodeExpression("address != NULL"),
                    body=(
                        CExpressionStatement(
                            CodeExpression(f"{self._allocatable_holder_destroy_bridge_name(type_symbol)}(address)")
                        ),
                    ),
                    else_body=(CExpressionStatement(CodeExpression("PyErr_Clear()")),),
                ),
            ),
        )

    def _derived_capsule_destructor(self, derived: DerivedTypePlan) -> CFunction:
        """Lower exactly-once wrapper-owned native destruction."""
        pointer = "address"
        return CFunction(
            self._derived_capsule_destructor_name(derived.backend_symbol),
            "void",
            parameters=(CParameter("capsule", "PyObject *"),),
            storage="static",
            body=(
                CDeclaration(
                    pointer,
                    "void *",
                    CodeExpression(
                        f'PyCapsule_GetPointer(capsule, "{self._derived_capsule_name(derived.backend_symbol)}")'
                    ),
                ),
                CIf(
                    CodeExpression(f"{pointer} != NULL"),
                    body=(
                        CExpressionStatement(
                            CodeExpression(f"{self._derived_destroy_bridge_name(derived.backend_symbol)}({pointer})")
                        ),
                    ),
                    else_body=(CExpressionStatement(CodeExpression("PyErr_Clear()")),),
                ),
            ),
        )

    # Derived-type fields and module-member operations.
    def _derived_field_bridge_prototypes(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare typed field operations selected by derived field plans."""
        return (
            *self._direct_field_bridge_prototype_entries(plan),
            *self._module_member_bridge_prototype_entries(plan),
            *self._allocatable_holder_field_bridge_prototype_entries(plan),
            *self._pointer_holder_field_bridge_prototype_entries(plan),
        )

    def _direct_field_bridge_prototype_entries(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare planner-owned direct-field bridge operations."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for derived in self._derived_types(plan)
            if not derived.abstract
            for field in derived.fields
            for operation in self._generated_support_procedure_entrypoints_for(
                f"{derived.owner_path}.{field.name}", "field:direct:"
            )
        )

    def _module_member_bridge_prototype_entries(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare planner-owned module-member bridge operations."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            for operation in self._generated_support_procedure_entrypoints_for(
                ".".join((variable.owner_path, *member.path)), "field:module:"
            )
        )

    def _allocatable_holder_field_bridge_prototype_entries(
        self,
        plan: ModulePlan,
    ) -> tuple[CFunctionPrototype, ...]:
        """Declare planner-owned allocatable-holder field bridge operations."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for derived in self._binding_allocatable_holder_types(plan)
            for field in derived.fields
            for operation in self._generated_support_procedure_entrypoints_for(
                f"{derived.owner_path}.{field.name}", "field:allocatable:"
            )
        )

    def _pointer_holder_field_bridge_prototype_entries(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare planner-owned pointer-holder field bridge operations."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for derived in self._binding_pointer_holder_types(plan)
            for field in derived.fields
            for operation in self._generated_support_procedure_entrypoints_for(
                f"{derived.owner_path}.{field.name}", "field:pointer:"
            )
        )

    def _derived_private_method_prototypes(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare private property callables before namespace method tables."""
        return tuple(
            CFunctionPrototype(
                function.name,
                function.return_type,
                function.parameters,
                storage=function.storage,
            )
            for function in self._derived_field_functions(plan)
        )

    def _derived_field_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Lower address-backed and plain-module field methods."""
        return (
            *self._direct_field_functions_for_plan(plan),
            *self._module_member_functions_for_plan(plan),
            *self._allocatable_holder_functions_for_plan(plan),
            *self._pointer_holder_functions_for_plan(plan),
            *self._module_proxy_guard_functions_for_plan(plan),
        )

    def _direct_field_functions_for_plan(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Build direct field functions for plan from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return tuple(
            function
            for derived in self._derived_types(plan)
            if not derived.abstract
            for field in derived.fields
            for function in self._direct_field_functions(derived, field)
        )

    def _module_member_functions_for_plan(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Build module member functions for plan from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return tuple(
            function
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            for function in self._module_member_functions(variable, member)
        )

    def _allocatable_holder_functions_for_plan(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Build allocatable holder functions for plan from the supplied completed binding records; emitted nodes only project completed binding actions."""
        derived_types = self._binding_allocatable_holder_types(plan)
        fields = tuple(
            function
            for derived in derived_types
            for field in derived.fields
            for function in self._allocatable_holder_field_functions(derived, field)
        )
        presence = tuple(self._allocatable_holder_presence_method(derived) for derived in derived_types)
        return (*presence, *fields)

    def _pointer_holder_functions_for_plan(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Build pointer holder functions for plan from the supplied completed binding records; emitted nodes only project completed binding actions."""
        derived_types = self._binding_pointer_holder_types(plan)
        fields = tuple(
            function
            for derived in derived_types
            for field in derived.fields
            for function in self._pointer_holder_field_functions(derived, field)
        )
        presence = tuple(self._pointer_holder_presence_method(derived) for derived in derived_types)
        return (*presence, *fields)

    def _module_proxy_guard_functions_for_plan(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Build module proxy guard functions for plan from the supplied completed binding records; emitted nodes only project completed binding actions."""
        variables = self._derived_member_proxy_variables(plan)
        return tuple(
            self._module_derived_presence_method(variable)
            for variable in variables
            if self._nullable_derived_module_proxy(variable)
        )

    def _allocatable_holder_presence_method(self, derived: DerivedTypePlan) -> CFunction:
        """Reject field access while one persistent holder component is unallocated."""
        return self._derived_private_method(
            self._allocatable_holder_presence_method_name(derived.backend_symbol),
            (
                *self._allocatable_holder_owner_nodes(derived.backend_symbol, setter=False),
                CIf(
                    CodeExpression(
                        f"!{self._allocatable_holder_presence_bridge_name(derived.backend_symbol)}(owner_address)"
                    ),
                    body=(
                        CExpressionStatement(
                            CodeExpression(
                                'PyErr_SetString(PyExc_ReferenceError, "allocatable derived object is unallocated")'
                            )
                        ),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            ),
        )

    def _allocatable_holder_field_functions(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[CFunction, ...]:
        """Expose scalar holder fields through holder-checked private methods."""
        if field.access is not DerivedFieldAccessMechanism.SCALAR_VALUE:
            raise ValueError(f"Unsupported allocatable-holder field for {field.owner_path!r}: {field.access.value}")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        owner_nodes = self._allocatable_holder_owner_nodes(derived.backend_symbol, setter=False)
        getter = self._derived_private_method(
            self._allocatable_holder_field_method_name(derived, field, "get"),
            (
                *owner_nodes,
                CDeclaration(
                    "value",
                    scalar.c_spelling,
                    CodeExpression(
                        self._allocatable_holder_field_bridge_name(derived, field, "get") + "(owner_address)"
                    ),
                ),
                CReturn(CodeExpression(self._scalar_result_expression(scalar, "&value"))),
            ),
        )
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return (getter,)
        setter = self._derived_private_method(
            self._allocatable_holder_field_method_name(derived, field, "set"),
            (
                *self._allocatable_holder_owner_nodes(derived.backend_symbol, setter=True),
                CDeclaration("value", scalar.c_spelling),
                self._scalar_field_unpack_statement(field, scalar, "value_obj", "value"),
                CExpressionStatement(
                    CodeExpression(
                        f"{self._allocatable_holder_field_bridge_name(derived, field, 'set')}(owner_address, value)"
                    )
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            ),
        )
        return getter, setter

    def _allocatable_holder_owner_nodes(self, type_name: str, *, setter: bool) -> tuple:
        """Parse property arguments and extract one exact typed-holder capsule."""
        declarations: tuple = (CDeclaration("owner_obj", "PyObject *"),)
        if setter:
            declarations = (*declarations, CDeclaration("value_obj", "PyObject *"))
            parse = 'if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL'
        else:
            parse = 'if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL'
        return (
            *declarations,
            CExpressionStatement(CodeExpression(parse)),
            CDeclaration(
                "owner_capsule",
                "PyObject *",
                CodeExpression('PyObject_GetAttrString(owner_obj, "_prik_capsule")'),
            ),
            CIf(CodeExpression("owner_capsule == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CDeclaration(
                "owner_address",
                "void *",
                CodeExpression(
                    f'PyCapsule_GetPointer(owner_capsule, "{self._allocatable_holder_capsule_name(type_name)}")'
                ),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(owner_capsule)")),
            CIf(CodeExpression("owner_address == NULL"), body=(CReturn(CodeExpression("NULL")),)),
        )

    def _pointer_holder_presence_method(self, derived: DerivedTypePlan) -> CFunction:
        """Return pointer holder presence method from the supplied local lowering values; this helper preserves the selected binding behavior."""
        return self._derived_private_method(
            self._pointer_holder_presence_method_name(derived.backend_symbol),
            (
                *self._pointer_holder_owner_nodes(derived.backend_symbol, setter=False),
                CIf(
                    CodeExpression(
                        f"!{self._pointer_holder_presence_bridge_name(derived.backend_symbol)}(owner_address)"
                    ),
                    body=(
                        CExpressionStatement(
                            CodeExpression(
                                'PyErr_SetString(PyExc_ReferenceError, "pointer derived object is disassociated")'
                            )
                        ),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            ),
        )

    def _pointer_holder_field_functions(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[CFunction, ...]:
        """Build pointer holder field functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        if field.access is not DerivedFieldAccessMechanism.SCALAR_VALUE:
            raise ValueError(f"Unsupported pointer-holder field for {field.owner_path!r}: {field.access.value}")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        getter = self._derived_private_method(
            self._pointer_holder_field_method_name(derived, field, "get"),
            (
                *self._pointer_holder_owner_nodes(derived.backend_symbol, setter=False),
                CDeclaration(
                    "value",
                    scalar.c_spelling,
                    CodeExpression(self._pointer_holder_field_bridge_name(derived, field, "get") + "(owner_address)"),
                ),
                CReturn(CodeExpression(self._scalar_result_expression(scalar, "&value"))),
            ),
        )
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return (getter,)
        setter = self._derived_private_method(
            self._pointer_holder_field_method_name(derived, field, "set"),
            (
                *self._pointer_holder_owner_nodes(derived.backend_symbol, setter=True),
                CDeclaration("value", scalar.c_spelling),
                self._scalar_field_unpack_statement(field, scalar, "value_obj", "value"),
                CExpressionStatement(
                    CodeExpression(
                        f"{self._pointer_holder_field_bridge_name(derived, field, 'set')}(owner_address, value)"
                    )
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            ),
        )
        return getter, setter

    def _pointer_holder_owner_nodes(self, type_name: str, *, setter: bool) -> tuple:
        """Build pointer holder owner nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        declarations: tuple = (CDeclaration("owner_obj", "PyObject *"),)
        if setter:
            declarations = (*declarations, CDeclaration("value_obj", "PyObject *"))
            parse = 'if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL'
        else:
            parse = 'if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL'
        return (
            *declarations,
            CExpressionStatement(CodeExpression(parse)),
            CDeclaration(
                "owner_capsule",
                "PyObject *",
                CodeExpression('PyObject_GetAttrString(owner_obj, "_prik_capsule")'),
            ),
            CIf(CodeExpression("owner_capsule == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CDeclaration(
                "owner_address",
                "void *",
                CodeExpression(
                    f'PyCapsule_GetPointer(owner_capsule, "{self._pointer_holder_capsule_name(type_name)}")'
                ),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(owner_capsule)")),
            CIf(CodeExpression("owner_address == NULL"), body=(CReturn(CodeExpression("NULL")),)),
        )

    def _module_derived_presence_method(self, variable: ModuleVariablePlan) -> CFunction:
        """Reject stale field access after native deallocation or nullification."""
        name = self._module_derived_presence_method_name(variable)
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            CIf(
                CodeExpression(f"!{self._module_derived_presence_bridge_name(variable)}()"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_ReferenceError, "module object {variable.symbol_name} '
                            'is not currently present")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(name, body)

    def _direct_field_functions(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[CFunction, ...]:
        """Dispatch one address-backed field by its completed object kind."""
        builders = {
            DerivedFieldAccessMechanism.FIXED_STRING_COPY: self._direct_string_field_functions,
            DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE: self._direct_handle_field_functions,
            DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR: self._direct_array_field_functions,
            DerivedFieldAccessMechanism.SCALAR_VALUE: self._direct_scalar_field_functions,
            DerivedFieldAccessMechanism.NESTED_OBJECT: self._direct_nested_field_functions,
        }
        try:
            return builders[field.access](derived, field)
        except KeyError as exc:
            raise ValueError(f"Unsupported direct field lowering for {field.owner_path!r}") from exc

    def _module_member_functions(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> tuple[CFunction, ...]:
        """Dispatch one plain-module member by its completed object kind."""
        builders = {
            DerivedFieldAccessMechanism.FIXED_STRING_COPY: self._module_string_member_functions,
            DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE: self._module_handle_member_functions,
            DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR: self._module_array_member_functions,
            DerivedFieldAccessMechanism.SCALAR_VALUE: self._module_scalar_member_functions,
            DerivedFieldAccessMechanism.NESTED_OBJECT: self._module_nested_member_functions,
        }
        try:
            return builders[member.field.access](variable, member)
        except KeyError as exc:
            raise ValueError(f"Unsupported module member lowering for {member.field.owner_path!r}") from exc

    def _direct_string_field_functions(self, derived, field) -> tuple[CFunction, ...]:
        """Build direct string field functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return self._optional_field_functions(
            self._direct_string_field_getter(derived, field),
            self._direct_string_field_setter(derived, field),
        )

    def _direct_handle_field_functions(self, derived, field) -> tuple[CFunction, ...]:
        """Build direct handle field functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return (self._direct_native_handle_field_getter(derived, field),)

    def _direct_array_field_functions(self, derived, field) -> tuple[CFunction, ...]:
        """Build direct array field functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        callback = self._ordinary_array_field_descriptor_callback(
            field,
            self._derived_field_descriptor_callback_name(derived, field),
        )
        return (
            callback,
            self._direct_ordinary_array_field_getter(derived, field),
            *self._present_field_function(self._direct_ordinary_array_field_setter(derived, field)),
        )

    def _direct_scalar_field_functions(self, derived, field) -> tuple[CFunction, ...]:
        """Build direct scalar field functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return self._optional_field_functions(
            self._direct_scalar_field_getter(derived, field),
            self._direct_scalar_field_setter(derived, field),
        )

    def _direct_nested_field_functions(self, derived, field) -> tuple[CFunction, ...]:
        """Build direct nested field functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return self._optional_field_functions(
            self._direct_nested_field_getter(derived, field),
            self._direct_nested_field_setter(derived, field),
        )

    def _module_string_member_functions(self, variable, member) -> tuple[CFunction, ...]:
        """Build module string member functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return self._optional_field_functions(
            self._module_string_member_getter(variable, member),
            self._module_string_member_setter(variable, member),
        )

    def _module_handle_member_functions(self, variable, member) -> tuple[CFunction, ...]:
        """Build module handle member functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return (self._module_native_handle_member_getter(variable, member),)

    def _module_array_member_functions(self, variable, member) -> tuple[CFunction, ...]:
        """Build module array member functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        callback = self._ordinary_array_field_descriptor_callback(
            member.field,
            self._module_member_descriptor_callback_name(variable, member),
        )
        return (
            callback,
            self._module_ordinary_array_member_getter(variable, member),
            *self._present_field_function(self._module_ordinary_array_member_setter(variable, member)),
        )

    def _module_scalar_member_functions(self, variable, member) -> tuple[CFunction, ...]:
        """Build module scalar member functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return self._optional_field_functions(
            self._module_scalar_member_getter(variable, member),
            self._module_scalar_member_setter(variable, member),
        )

    def _module_nested_member_functions(self, variable, member) -> tuple[CFunction, ...]:
        """Build module nested member functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return self._optional_field_functions(
            self._module_nested_member_getter(variable, member),
            self._module_nested_member_setter(variable, member),
        )

    @staticmethod
    def _optional_field_functions(getter: CFunction, setter: CFunction | None) -> tuple[CFunction, ...]:
        """Build optional field functions from the supplied local lowering values; emitted nodes only project completed binding actions."""
        return (getter, *CBindingGenerator._present_field_function(setter))

    @staticmethod
    def _present_field_function(function: CFunction | None) -> tuple[CFunction, ...]:
        """Build present field function from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return () if function is None else (function,)

    def _direct_ordinary_array_field_getter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction:
        """Create a live NumPy view over one fixed address-backed field."""
        body = (
            *self._derived_owner_address_nodes(derived),
            CDeclaration("field_view", "PyObject *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"{self._derived_field_bridge_name(derived, field, 'get')}(owner_address, "
                    f"{self._derived_field_descriptor_callback_name(derived, field)}, &field_view)"
                )
            ),
            *self._ordinary_array_field_owner_nodes("field_view", "owner_obj"),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "get"), body)

    def _direct_native_handle_field_getter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction:
        """Create one parent-retaining Phase 7 handle for an address-backed field."""
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            *self._field_handle_factory_nodes(derived, field, "owner_obj"),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "get"), body)

    def _direct_string_field_getter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction:
        """Copy one fixed native string field into an independent Python string."""
        length = self._fixed_string_field_length(field)
        body = (
            *self._derived_owner_address_nodes(derived),
            CDeclaration(f"value[{length + 1}]", "char"),
            CExpressionStatement(
                CodeExpression(f"{self._derived_field_bridge_name(derived, field, 'get')}(owner_address, value)")
            ),
            CExpressionStatement(CodeExpression(f"value[{length}] = '\\0'")),
            CReturn(CodeExpression(f'PyUnicode_DecodeUTF8(value, {length}, "strict")')),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "get"), body)

    def _direct_string_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction | None:
        """Validate and copy one exact-width Python string into native storage."""
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        body = (
            *self._derived_owner_and_value_nodes(derived),
            *self._fixed_string_field_input_nodes(field, "value_obj"),
            CExpressionStatement(
                CodeExpression(f"{self._derived_field_bridge_name(derived, field, 'set')}(owner_address, value)")
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "set"), body)

    def _direct_ordinary_array_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction | None:
        """Copy one exact NumPy array into a writable fixed native field."""
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        body = (
            *self._derived_owner_and_value_nodes(derived),
            *self._ordinary_array_field_input_nodes(field, "value_obj", "value_array"),
            CExpressionStatement(
                CodeExpression(
                    f"{self._derived_field_bridge_name(derived, field, 'set')}("
                    "owner_address, PyArray_DATA(value_array))"
                )
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "set"), body)

    def _module_ordinary_array_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction:
        """Create a live NumPy view over one plain-module fixed array member."""
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            CDeclaration("field_view", "PyObject *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_member_bridge_name(variable, member, 'get')}("
                    f"{self._module_member_descriptor_callback_name(variable, member)}, &field_view)"
                )
            ),
            *self._ordinary_array_field_owner_nodes("field_view", "owner_obj"),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "get"), body)

    def _module_native_handle_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction:
        """Create one parent-retaining handle for a plain-module field path."""
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            *self._field_handle_factory_nodes((variable, member), member.field, "owner_obj"),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "get"), body)

    def _module_string_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction:
        """Copy one fixed plain-module string member into Python storage."""
        length = self._fixed_string_field_length(member.field)
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            CDeclaration(f"value[{length + 1}]", "char"),
            CExpressionStatement(CodeExpression(f"{self._module_member_bridge_name(variable, member, 'get')}(value)")),
            CExpressionStatement(CodeExpression(f"value[{length}] = '\\0'")),
            CReturn(CodeExpression(f'PyUnicode_DecodeUTF8(value, {length}, "strict")')),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "get"), body)

    def _module_string_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction | None:
        """Validate and copy one exact-width string into a plain module member."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CDeclaration("value_obj", "PyObject *"),
            CExpressionStatement(
                CodeExpression('if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL')
            ),
            *self._fixed_string_field_input_nodes(field, "value_obj"),
            CExpressionStatement(CodeExpression(f"{self._module_member_bridge_name(variable, member, 'set')}(value)")),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "set"), body)

    @staticmethod
    def _fixed_string_field_length(field: DerivedFieldPlan) -> int:
        """Return the binding-local fixed string field length derived from the supplied completed binding records; this helper preserves completed policy."""
        length = field.character_length
        if length is None or length <= 0:
            raise ValueError(f"Fixed string field {field.owner_path!r} has no positive length")
        return length

    def _fixed_string_field_input_nodes(self, field: DerivedFieldPlan, object_name: str) -> tuple:
        """Require exact UTF-8 byte width and reject embedded NULs."""
        length = self._fixed_string_field_length(field)
        return (
            CIf(
                CodeExpression(f"!PyUnicode_Check({object_name})"),
                body=(
                    CExpressionStatement(
                        CodeExpression(f'PyErr_SetString(PyExc_TypeError, "Expected str for field {field.name}")')
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration("value_length", "Py_ssize_t", CodeExpression("0")),
            CDeclaration(
                "value",
                "const char *",
                CodeExpression(f"PyUnicode_AsUTF8AndSize({object_name}, &value_length)"),
            ),
            CIf(CodeExpression("value == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CIf(
                CodeExpression(f"value_length != {length} || (Py_ssize_t)strlen(value) != value_length"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_TypeError, "Field {field.name} must encode to exactly '
                            f'{length} bytes without embedded NUL")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        )

    def _field_handle_factory_nodes(self, owner, field: DerivedFieldPlan, owner_name: str) -> tuple:
        """Build a fresh borrowed handle whose operations are bound to its parent."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no factory plan")
        prefix = re.sub(r"\W", "_", field.owner_path).casefold()
        ops = f"{prefix}_ops"
        operation_object = f"{prefix}_operation"
        runtime = f"{prefix}_runtime"
        helper = f"{prefix}_helper"
        result = f"{prefix}_handle"
        nodes = [
            CDeclaration(ops, "PyObject *", CodeExpression("PyDict_New()")),
            CDeclaration(operation_object, "PyObject *", CodeExpression("NULL")),
            CDeclaration(runtime, "PyObject *", CodeExpression("NULL")),
            CDeclaration(helper, "PyObject *", CodeExpression("NULL")),
            CDeclaration(result, "PyObject *", CodeExpression("NULL")),
            CIf(CodeExpression(f"{ops} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
        ]
        for operation in handle.operations:
            name = self._field_handle_operation_name(owner, field, operation)
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"{operation_object} = PyCFunction_NewEx(&{name}_def, {owner_name}, NULL)")
                    ),
                    CIf(
                        CodeExpression(f"{operation_object} == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({ops})")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CIf(
                        CodeExpression(f'PyDict_SetItemString({ops}, "{operation.value}", {operation_object}) < 0'),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({operation_object})")),
                            CExpressionStatement(CodeExpression(f"Py_DECREF({ops})")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({operation_object})")),
                )
            )
        family = DatatypeFamily.STRING if field.string_element else DatatypeFamily.REAL
        nodes.extend(
            (
                CExpressionStatement(CodeExpression(f'{runtime} = PyImport_ImportModule("prik.runtime.handles")')),
                CIf(
                    CodeExpression(f"{runtime} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({ops})")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        f'{helper} = PyObject_GetAttrString({runtime}, "_native_array_handle_from_generated_ops")'
                    )
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({runtime})")),
                CIf(
                    CodeExpression(f"{helper} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({ops})")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        self._native_array_handle_factory_call(
                            helper=helper,
                            target=result,
                            descriptor_kind=handle.descriptor_kind.value,
                            semantic_type_name=field.semantic_type_name,
                            datatype_family=family,
                            rank=handle.array.rank,
                            ops=ops,
                            owner=owner_name,
                            descriptor_ownership="borrowed",
                            extraction_action=handle.extraction_action.value,
                        )
                    )
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({helper})")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({ops})")),
                CReturn(CodeExpression(result)),
            )
        )
        return tuple(nodes)

    def _field_handle_operation_name(
        self,
        owner,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the binding-local field handle operation name derived from the supplied completed binding records; this helper preserves completed policy."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_operation_name(owner, field, operation)
        variable, member = owner
        return self._module_member_handle_operation_name(variable, member, operation)

    def _module_ordinary_array_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction | None:
        """Copy one exact NumPy array into a writable plain-module member."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CDeclaration("value_obj", "PyObject *"),
            CExpressionStatement(
                CodeExpression('if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL')
            ),
            *self._ordinary_array_field_input_nodes(field, "value_obj", "value_array"),
            CExpressionStatement(
                CodeExpression(f"{self._module_member_bridge_name(variable, member, 'set')}(PyArray_DATA(value_array))")
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "set"), body)

    def _ordinary_array_field_descriptor_callback(
        self,
        field: DerivedFieldPlan,
        callback_name: str,
    ) -> CFunction:
        """Construct a NumPy view from one standard field descriptor."""
        array = field.array
        if array is None or array.rank is None or not array.shape:
            raise ValueError(f"Ordinary array field {field.owner_path!r} has no fixed shape")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        dims = ", ".join(f"(npy_intp)descriptor->dim[{axis}].extent" for axis in range(array.rank))
        strides = ", ".join(f"(npy_intp)descriptor->dim[{axis}].sm" for axis in range(array.rank))
        return CFunction(
            callback_name,
            "void",
            parameters=(CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
            storage="static",
            body=(
                CExpressionStatement(CodeExpression("*(PyObject **)context = NULL")),
                CIf(
                    CodeExpression("descriptor == NULL || descriptor->base_addr == NULL"),
                    body=(
                        CExpressionStatement(
                            CodeExpression(
                                'PyErr_SetString(PyExc_ReferenceError, "array field descriptor is unavailable")'
                            )
                        ),
                        CReturn(),
                    ),
                ),
                CDeclaration(
                    f"field_dims[{array.rank}]",
                    "npy_intp",
                    CodeExpression("{" + dims + "}"),
                ),
                CDeclaration(
                    f"field_strides[{array.rank}]",
                    "npy_intp",
                    CodeExpression("{" + strides + "}"),
                ),
                CExpressionStatement(
                    CodeExpression(
                        f"*(PyObject **)context = PyArray_New(&PyArray_Type, {array.rank}, field_dims, "
                        f"{scalar.numpy_type_macro}, field_strides, descriptor->base_addr, 0, "
                        "NPY_ARRAY_F_CONTIGUOUS | NPY_ARRAY_ALIGNED | NPY_ARRAY_WRITEABLE, NULL)"
                    )
                ),
            ),
        )

    @staticmethod
    def _ordinary_array_field_owner_nodes(field_view: str, owner_name: str) -> tuple:
        """Retain the live parent as the NumPy view base after descriptor use."""
        return (
            CIf(CodeExpression(f"{field_view} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CExpressionStatement(CodeExpression(f"Py_INCREF({owner_name})")),
            CIf(
                CodeExpression(f"PyArray_SetBaseObject((PyArrayObject *){field_view}, {owner_name}) < 0"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({field_view})")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CReturn(CodeExpression(field_view)),
        )

    def _ordinary_array_field_input_nodes(
        self,
        field: DerivedFieldPlan,
        object_name: str,
        array_name: str,
    ) -> tuple:
        """Validate one exact primitive NumPy field replacement."""
        array = field.array
        if array is None or array.rank is None:
            raise ValueError(f"Ordinary array field {field.owner_path!r} has no fixed rank")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        conditions = [
            f"!PyArray_CheckExact({object_name})",
            f"PyArray_TYPE((PyArrayObject *){object_name}) != {scalar.numpy_type_macro}",
            f"PyArray_NDIM((PyArrayObject *){object_name}) != {array.rank}",
            f"!PyArray_ISALIGNED((PyArrayObject *){object_name})",
            f"!PyArray_IS_F_CONTIGUOUS((PyArrayObject *){object_name})",
        ]
        conditions.extend(
            f"PyArray_DIM((PyArrayObject *){object_name}, {axis}) != "
            f"(npy_intp)({render_declaration_extent(extent, {}, target='c')})"
            for axis, extent in enumerate(array.shape)
        )
        return (
            CIf(
                CodeExpression(" || ".join(conditions)),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_TypeError, "Expected an exact Fortran-contiguous '
                            f'{field.semantic_type_name} array for field {field.name}")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(array_name, "PyArrayObject *", CodeExpression(f"(PyArrayObject *){object_name}")),
        )

    def _direct_scalar_field_getter(self, derived: DerivedTypePlan, field: DerivedFieldPlan) -> CFunction:
        """Return direct scalar field getter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        body = (
            *self._derived_owner_address_nodes(derived),
            CDeclaration(
                "value",
                scalar.c_spelling,
                CodeExpression(f"{self._derived_field_bridge_name(derived, field, 'get')}(owner_address)"),
            ),
            CReturn(CodeExpression(self._scalar_result_expression(scalar, "&value", module=True))),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "get"), body)

    def _direct_scalar_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction | None:
        """Return direct scalar field setter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        body = (
            *self._derived_owner_and_value_nodes(derived),
            CDeclaration("value", scalar.c_spelling),
            self._scalar_field_unpack_statement(field, scalar, "value_obj", "value"),
            CExpressionStatement(
                CodeExpression(f"{self._derived_field_bridge_name(derived, field, 'set')}(owner_address, value)")
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "set"), body)

    def _module_scalar_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction:
        """Return module scalar member getter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        scalar = PrimitiveScalarTypeRegistry.type_for(member.field.semantic_type_name)
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            CDeclaration(
                "value",
                scalar.c_spelling,
                CodeExpression(f"{self._module_member_bridge_name(variable, member, 'get')}()"),
            ),
            CReturn(CodeExpression(self._scalar_result_expression(scalar, "&value", module=True))),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "get"), body)

    def _module_scalar_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction | None:
        """Return module scalar member setter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CDeclaration("value_obj", "PyObject *"),
            CExpressionStatement(
                CodeExpression('if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL')
            ),
            CDeclaration("value", scalar.c_spelling),
            self._scalar_field_unpack_statement(field, scalar, "value_obj", "value"),
            CExpressionStatement(CodeExpression(f"{self._module_member_bridge_name(variable, member, 'set')}(value)")),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "set"), body)

    def _direct_nested_field_getter(self, derived: DerivedTypePlan, field: DerivedFieldPlan) -> CFunction:
        """Return direct nested field getter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        if field.derived is None:
            raise ValueError(f"Nested field {field.owner_path!r} has no derived handoff")
        child_type = field.derived.type_name
        child_symbol = field.derived.backend_symbol
        body = (
            *self._derived_owner_address_nodes(derived),
            CDeclaration(
                "child_address",
                "void *",
                CodeExpression(f"{self._derived_field_bridge_name(derived, field, 'get')}(owner_address)"),
            ),
            CIf(
                CodeExpression("child_address == NULL"),
                body=(
                    CExpressionStatement(
                        CodeExpression('PyErr_SetString(PyExc_ReferenceError, "derived field address is unavailable")')
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                "child_capsule",
                "PyObject *",
                CodeExpression(f'PyCapsule_New(child_address, "{self._derived_capsule_name(child_symbol)}", NULL)'),
            ),
            CIf(CodeExpression("child_capsule == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            *self._borrowed_derived_wrapper_nodes(child_type, "child_capsule", "owner_obj", None),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "get"), body)

    def _direct_nested_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> CFunction | None:
        """Return direct nested field setter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        if field.setter_action is not SetterAction.WRITE_THROUGH or field.derived is None:
            return None
        body = (
            *self._derived_owner_and_value_nodes(derived),
            *self._exact_derived_type_check_nodes(field.derived.type_name, "value_obj", field.name),
            *self._derived_address_from_object_nodes(field.derived.backend_symbol, "value_obj", "value"),
            CExpressionStatement(
                CodeExpression(
                    f"{self._derived_field_bridge_name(derived, field, 'set')}(owner_address, value_address)"
                )
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._derived_field_method_name(derived, field, "set"), body)

    def _module_nested_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction:
        """Return module nested member getter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        field = member.field
        if field.derived is None:
            raise ValueError(f"Nested module member {field.owner_path!r} has no derived handoff")
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            *self._borrowed_derived_wrapper_nodes(
                field.derived.type_name,
                "Py_None",
                "owner_obj",
                self._module_member_ops_name(variable, member.path),
                borrowed_capsule=False,
            ),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "get"), body)

    def _module_nested_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> CFunction | None:
        """Return module nested member setter from the supplied completed binding records; this helper preserves the selected binding behavior."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH or field.derived is None:
            return None
        body = (
            CDeclaration("owner_obj", "PyObject *"),
            CDeclaration("value_obj", "PyObject *"),
            CExpressionStatement(
                CodeExpression('if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL')
            ),
            *self._exact_derived_type_check_nodes(field.derived.type_name, "value_obj", field.name),
            *self._derived_address_from_object_nodes(field.derived.backend_symbol, "value_obj", "value"),
            CExpressionStatement(
                CodeExpression(f"{self._module_member_bridge_name(variable, member, 'set')}(value_address)")
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )
        return self._derived_private_method(self._module_member_method_name(variable, member, "set"), body)

    def _borrowed_derived_wrapper_nodes(
        self,
        type_name: str,
        capsule_name: str,
        owner_name: str,
        ops_name: str | None,
        *,
        borrowed_capsule: bool = True,
    ) -> tuple:
        """Construct one borrowed child/proxy while retaining its Python owner."""
        nodes = [
            CDeclaration(
                "child_helper",
                "PyObject *",
                CodeExpression(f'PyObject_GetAttrString(self, "_prik_wrap_{type_name}")'),
            ),
            CIf(
                CodeExpression("child_helper == NULL"),
                body=(
                    *(
                        (CExpressionStatement(CodeExpression(f"Py_DECREF({capsule_name})")),)
                        if borrowed_capsule
                        else ()
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        ]
        call_arguments = f"child_helper, {capsule_name}, {owner_name}"
        if ops_name is not None:
            nodes.extend(
                (
                    CDeclaration(
                        "child_ops",
                        "PyObject *",
                        CodeExpression(f'PyObject_GetAttrString(self, "{ops_name}")'),
                    ),
                    CIf(
                        CodeExpression("child_ops == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(child_helper)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                )
            )
            call_arguments += ", child_ops"
        nodes.extend(
            (
                CDeclaration(
                    "child_result",
                    "PyObject *",
                    CodeExpression(f"PyObject_CallFunctionObjArgs({call_arguments}, NULL)"),
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(child_helper)")),
                *((CExpressionStatement(CodeExpression("Py_DECREF(child_ops)")),) if ops_name is not None else ()),
                *((CExpressionStatement(CodeExpression(f"Py_DECREF({capsule_name})")),) if borrowed_capsule else ()),
                CReturn(CodeExpression("child_result")),
            )
        )
        return tuple(nodes)

    def _derived_private_method(self, name: str, body: tuple) -> CFunction:
        """Return one private module callable used by generated properties."""
        return CFunction(
            name,
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=body,
        )

    def _derived_owner_address_nodes(self, derived: DerivedTypePlan) -> tuple:
        """Extract one checked opaque parent address from a live wrapper."""
        return (
            CDeclaration("owner_obj", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL')),
            *self._derived_address_from_object_nodes(derived.backend_symbol, "owner_obj", "owner"),
        )

    def _derived_owner_and_value_nodes(self, derived: DerivedTypePlan) -> tuple:
        """Extract one checked parent address and Python setter value."""
        return (
            CDeclaration("owner_obj", "PyObject *"),
            CDeclaration("value_obj", "PyObject *"),
            CExpressionStatement(
                CodeExpression('if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL')
            ),
            *self._derived_address_from_object_nodes(derived.backend_symbol, "owner_obj", "owner"),
        )

    def _derived_address_from_object_nodes(self, type_symbol: str, object_name: str, prefix: str) -> tuple:
        """Extract a capsule address with the plan's exact native type identity."""
        capsule = f"{prefix}_capsule"
        address = f"{prefix}_address"
        return (
            CDeclaration(
                capsule, "PyObject *", CodeExpression(f'PyObject_GetAttrString({object_name}, "_prik_capsule")')
            ),
            CIf(CodeExpression(f"{capsule} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CIf(
                CodeExpression(f"{capsule} == Py_None"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                address,
                "void *",
                CodeExpression(f'PyCapsule_GetPointer({capsule}, "{self._derived_capsule_name(type_symbol)}")'),
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
            CIf(CodeExpression(f"{address} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
        )

    @staticmethod
    def _exact_derived_type_check_nodes(type_name: str, object_name: str, label: str) -> tuple:
        """Require the exact exported opaque class before a concrete field copy."""
        expected = f"{label}_expected_type"
        return (
            CDeclaration(expected, "PyObject *", CodeExpression(f'PyObject_GetAttrString(self, "{type_name}")')),
            CIf(CodeExpression(f"{expected} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CIf(
                CodeExpression(f"Py_TYPE({object_name}) != (PyTypeObject *){expected}"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({expected})")),
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_TypeError, "Expected exact wrapper type {type_name} '
                            f'for field {label}")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({expected})")),
        )

    def _scalar_field_unpack_statement(
        self,
        field: DerivedFieldPlan,
        scalar,
        object_name: str,
        value_name: str,
    ) -> CExpressionStatement:
        """Validate and unpack one exact scalar field replacement."""
        return self._scalar_exact_unpack_statement(
            scalar,
            object_name,
            value_name,
            (
                f'PyErr_Format(PyExc_TypeError, "Expected {scalar.python_type_name} for field {field.name}. '
                f"Received <class '%s'>\", Py_TYPE({object_name})->tp_name)"
            ),
            "NULL",
        )

    def _derived_field_c_type(self, field: DerivedFieldPlan) -> str:
        """Return the binding-local derived field c type derived from the supplied completed binding records; this helper preserves completed policy."""
        if field.object_kind is ObjectKind.DERIVED_TYPE:
            return "void *"
        return PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name).c_spelling

    # Derived native-array-handle fields reuse the Phase 7 runtime protocol.
    def _derived_handle_operation_declarations(
        self,
        plan: ModulePlan,
    ) -> tuple[CFunctionPrototype | CDeclaration, ...]:
        """Declare every parent-bound field-handle callable and method record."""
        declarations = []
        for _owner, field, operation_name, callback_names in self._derived_handle_targets(plan):
            descriptor_callback, actual_callback = callback_names
            declarations.extend(
                (
                    CFunctionPrototype(
                        descriptor_callback,
                        "void",
                        (CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
                        storage="static",
                    ),
                    CFunctionPrototype(
                        actual_callback,
                        "void",
                        (CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
                        storage="static",
                    ),
                )
            )
            handle = field.native_array_handle
            if handle is None:
                continue
            for operation in handle.operations:
                name = operation_name(operation)
                declarations.extend(
                    (
                        CFunctionPrototype(
                            name,
                            "PyObject *",
                            (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                            storage="static",
                        ),
                        CDeclaration(
                            f"{name}_def",
                            "static PyMethodDef",
                            CodeExpression(f'{{"{name}", (PyCFunction){name}, METH_VARARGS, ""}}'),
                        ),
                    )
                )
        return tuple(declarations)

    def _derived_handle_operation_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Lower descriptor callbacks and parent-bound runtime operations."""
        functions = []
        for owner, field, operation_name, callback_names in self._derived_handle_targets(plan):
            descriptor_callback, actual_callback = callback_names
            functions.extend(self._field_handle_descriptor_callbacks(field, descriptor_callback, actual_callback))
            handle = field.native_array_handle
            if handle is None:
                continue
            functions.extend(
                self._field_handle_operation_function(owner, field, operation, operation_name(operation))
                for operation in handle.operations
            )
        return tuple(functions)

    def _derived_handle_targets(self, plan: ModulePlan) -> tuple[tuple, ...]:
        """Return direct-parent and plain-module handle targets in stable order."""
        targets = [
            (
                derived,
                field,
                lambda operation, derived=derived, field=field: self._derived_handle_operation_name(
                    derived, field, operation
                ),
                (
                    self._derived_handle_descriptor_callback_name(derived, field),
                    self._derived_handle_actual_callback_name(derived, field),
                ),
            )
            for derived in self._derived_types(plan)
            for field in derived.fields
            if field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE
        ]
        targets.extend(
            (
                (variable, member),
                member.field,
                lambda operation, variable=variable, member=member: self._module_member_handle_operation_name(
                    variable, member, operation
                ),
                (
                    self._module_member_handle_descriptor_callback_name(variable, member),
                    self._module_member_handle_actual_callback_name(variable, member),
                ),
            )
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            if member.field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE
        )
        return tuple(targets)

    def _field_handle_descriptor_callbacks(
        self,
        field: DerivedFieldPlan,
        descriptor_name: str,
        actual_name: str,
    ) -> tuple[CFunction, CFunction]:
        """Decode one current field descriptor without copying its payload."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no descriptor rank")
        descriptor = CFunction(
            descriptor_name,
            "void",
            parameters=(CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
            storage="static",
            body=(
                CExpressionStatement(CodeExpression("*(PyObject **)context = NULL")),
                *self._native_array_descriptor_record_nodes(
                    handle.array.rank,
                    "descriptor",
                    return_target="*(PyObject **)context",
                ),
            ),
        )
        actual = CFunction(
            actual_name,
            "void",
            parameters=(CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
            storage="static",
            body=(
                CExpressionStatement(CodeExpression("*(void **)context = descriptor->base_addr")),
                CReturn(),
            ),
        )
        return descriptor, actual

    def _field_handle_operation_function(
        self,
        owner,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
        name: str,
    ) -> CFunction:
        """Lower one live field-handle operation selected by completed policy."""
        return CFunction(
            name,
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=self._field_handle_operation_body(owner, field, operation),
        )

    def _field_handle_operation_body(self, owner, field: DerivedFieldPlan, operation: NativeArrayOperation) -> tuple:
        """Dispatch one operation without inferring descriptor ownership."""
        if operation in {
            NativeArrayOperation.NATIVE_BYTE_ORDER,
            NativeArrayOperation.ALIGNED,
            NativeArrayOperation.WRITEABLE,
            NativeArrayOperation.LAYOUT,
        }:
            return self._module_native_array_metadata_body(operation)
        prefix = self._field_handle_owner_nodes(owner)
        owner_args = self._field_handle_owner_arguments(owner)
        if operation in {NativeArrayOperation.DESCRIPTOR, NativeArrayOperation.TO_NUMPY}:
            callback = self._field_handle_descriptor_callback(owner, field)
            descriptor_bridge = self._field_handle_bridge_name(
                owner,
                field,
                NativeArrayOperation.DESCRIPTOR,
            )
            return (*prefix, *self._field_handle_descriptor_nodes(descriptor_bridge, owner_args, callback))
        if operation is NativeArrayOperation.ARRAY_ACTUAL:
            callback = self._field_handle_actual_callback(owner, field)
            descriptor_bridge = self._field_handle_bridge_name(
                owner,
                field,
                NativeArrayOperation.DESCRIPTOR,
            )
            return (*prefix, *self._field_handle_actual_nodes(descriptor_bridge, owner_args, callback))
        bridge = self._field_handle_bridge_name(owner, field, operation)
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            return (*prefix, CReturn(CodeExpression(f"PyBool_FromLong({bridge}({owner_args}))")))
        if operation is NativeArrayOperation.ELEMENT_LENGTH:
            return (*prefix, CReturn(CodeExpression(f"PyLong_FromLongLong((long long){bridge}({owner_args}))")))
        if operation is NativeArrayOperation.SHAPE:
            return (*prefix, *self._field_handle_shape_nodes(field, bridge, owner_args))
        if operation is NativeArrayOperation.ASSOCIATE:
            return self._field_handle_associate_body(field, prefix, bridge, owner_args)
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            return (*prefix, *self._field_handle_shape_mutation_nodes(field, bridge, owner_args))
        if operation in {NativeArrayOperation.DEALLOCATE, NativeArrayOperation.NULLIFY}:
            arguments = owner_args
            return (
                *prefix,
                CExpressionStatement(CodeExpression(f"{bridge}({arguments})")),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            )
        raise ValueError(f"Unsupported field handle operation for {field.owner_path!r}: {operation!r}")

    def _field_handle_associate_body(
        self,
        field: DerivedFieldPlan,
        prefix: tuple,
        bridge: str,
        owner_args: str,
    ) -> tuple:
        """Associate one field pointer through its selected bridge operation."""
        arguments = f"{owner_args}, source_descriptor" if owner_args else "source_descriptor"
        return (
            *prefix,
            CDeclaration("source_packed", "PyObject *"),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &source_packed)) return NULL')),
            *self._pointer_association_source_nodes(field),
            CExpressionStatement(CodeExpression(f"{bridge}({arguments})")),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )

    def _field_handle_owner_nodes(self, owner) -> tuple:
        """Extract an address only for a completed direct-parent target."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_address_from_object_nodes(owner.backend_symbol, "self", "owner")
        return ()

    @staticmethod
    def _field_handle_owner_arguments(owner) -> str:
        """Return field handle owner arguments from the supplied local lowering values; this helper preserves the selected binding behavior."""
        return "owner_address" if isinstance(owner, DerivedTypePlan) else ""

    def _field_handle_bridge_name(
        self,
        owner,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the binding-local field handle bridge name derived from the supplied completed binding records; this helper preserves completed policy."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_bridge_name(owner, field, operation)
        variable, member = owner
        return self._module_member_handle_bridge_name(variable, member, operation)

    def _field_handle_descriptor_callback(self, owner, field: DerivedFieldPlan) -> str:
        """Build field handle descriptor callback from the supplied completed binding records; emitted nodes only project completed binding actions."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_descriptor_callback_name(owner, field)
        variable, member = owner
        return self._module_member_handle_descriptor_callback_name(variable, member)

    def _field_handle_actual_callback(self, owner, field: DerivedFieldPlan) -> str:
        """Build field handle actual callback from the supplied completed binding records; emitted nodes only project completed binding actions."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_actual_callback_name(owner, field)
        variable, member = owner
        return self._module_member_handle_actual_callback_name(variable, member)

    def _field_handle_shape_nodes(self, field: DerivedFieldPlan, bridge: str, owner_args: str) -> tuple:
        """Build field handle shape nodes from the supplied completed binding records; emitted nodes only project completed binding actions."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no shape rank")
        extents = tuple(f"extent_{axis}" for axis in range(handle.array.rank))
        call_args = ", ".join((*((owner_args,) if owner_args else ()), *(f"&{item}" for item in extents)))
        return (
            *(CDeclaration(item, "int64_t", CodeExpression("0")) for item in extents),
            CExpressionStatement(CodeExpression(f"{bridge}({call_args})")),
            CDeclaration("shape", "PyObject *", CodeExpression(f"PyTuple_New({handle.array.rank})")),
            CIf(CodeExpression("shape == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            *(
                CExpressionStatement(
                    CodeExpression(f"PyTuple_SET_ITEM(shape, {axis}, PyLong_FromLongLong((long long){extent}))")
                )
                for axis, extent in enumerate(extents)
            ),
            CIf(
                CodeExpression("PyErr_Occurred()"),
                body=(CExpressionStatement(CodeExpression("Py_DECREF(shape)")), CReturn(CodeExpression("NULL"))),
            ),
            CReturn(CodeExpression("shape")),
        )

    @staticmethod
    def _field_handle_descriptor_nodes(bridge: str, owner_args: str, callback: str) -> tuple:
        """Build field handle descriptor nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        arguments = ", ".join((*((owner_args,) if owner_args else ()), callback, "&descriptor_record"))
        return (
            CDeclaration("descriptor_record", "PyObject *", CodeExpression("NULL")),
            CExpressionStatement(CodeExpression(f"{bridge}({arguments})")),
            CReturn(CodeExpression("descriptor_record")),
        )

    @staticmethod
    def _field_handle_actual_nodes(bridge: str, owner_args: str, callback: str) -> tuple:
        """Build field handle actual nodes from the supplied local lowering values; emitted nodes only project completed binding actions."""
        arguments = ", ".join((*((owner_args,) if owner_args else ()), callback, "&base_addr"))
        return (
            CDeclaration("base_addr", "void *", CodeExpression("NULL")),
            CExpressionStatement(CodeExpression(f"{bridge}({arguments})")),
            CReturn(CodeExpression("PyLong_FromVoidPtr(base_addr)")),
        )

    def _field_handle_shape_mutation_nodes(self, field: DerivedFieldPlan, bridge: str, owner_args: str) -> tuple:
        """Build field handle shape mutation nodes from the supplied completed binding records; emitted nodes only project completed binding actions."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no mutation rank")
        objects = tuple(f"extent_{axis}_obj" for axis in range(handle.array.rank))
        extents = tuple(f"extent_{axis}" for axis in range(handle.array.rank))
        call_args = ", ".join((*((owner_args,) if owner_args else ()), *extents))
        return (
            *(CDeclaration(item, "PyObject *") for item in objects),
            *(CDeclaration(item, "int64_t", CodeExpression("0")) for item in extents),
            CExpressionStatement(
                CodeExpression(
                    f'if (!PyArg_ParseTuple(args, "{"O" * handle.array.rank}", '
                    f"{', '.join(f'&{item}' for item in objects)})) return NULL"
                )
            ),
            *(
                CExpressionStatement(
                    CodeExpression(f"{extent} = (int64_t)PyLong_AsLongLong({obj}); if (PyErr_Occurred()) return NULL")
                )
                for extent, obj in zip(extents, objects, strict=True)
            ),
            CExpressionStatement(CodeExpression(f"{bridge}({call_args})")),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )

    def _module_allocator_functions(self, required: bool) -> tuple[CFunction, ...]:
        """Return the copy allocator exported to the Fortran bridge."""
        if not required:
            return ()
        return (
            CFunction(
                "prik_malloc",
                "void *",
                parameters=(CParameter("size", "size_t"),),
                body=(
                    CDeclaration(
                        "fail_alloc",
                        "const char *",
                        CodeExpression('getenv("PRIK_WRAPPER_FAIL_ALLOC")'),
                    ),
                    CIf(
                        CodeExpression("fail_alloc != NULL && fail_alloc[0] != '\\0' && fail_alloc[0] != '0'"),
                        body=(CReturn(CodeExpression("NULL")),),
                    ),
                    CReturn(CodeExpression("malloc(size == 0 ? 1 : size)")),
                ),
            ),
        )

    # Owned native-array-handle operation tables.
    def _native_array_operation_declarations(
        self,
        plan: ModulePlan,
    ) -> tuple[CFunctionPrototype | CDeclaration, ...]:
        """Declare private operation wrappers and their callable definitions."""
        declarations = []
        for variable in self._module_array_owner_variables(plan):
            if variable.binding.getter_action is ModuleGetterAction.NATIVE_ARRAY_HANDLE:
                declarations.append(
                    CDeclaration(
                        self._module_native_array_cache_name(variable),
                        "static PyObject *",
                        CodeExpression("NULL"),
                    )
                )
            declarations.append(
                CDeclaration(
                    self._module_native_array_owner_name(variable),
                    "static PyObject *",
                    CodeExpression("NULL"),
                )
            )
            if variable.native_array_handle is None:
                continue
            for operation in variable.native_array_handle.operations:
                name = self._module_native_array_operation_name(variable, operation)
                declarations.extend(
                    (
                        CFunctionPrototype(
                            name,
                            "PyObject *",
                            (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                            storage="static",
                        ),
                        CDeclaration(
                            self._module_native_array_operation_def_name(variable, operation),
                            "static PyMethodDef",
                            CodeExpression(f'{{"{name}", (PyCFunction){name}, METH_VARARGS, ""}}'),
                        ),
                    )
                )
        for function, result in self._owned_native_array_results(plan):
            for operation in result.native_array_handle.operations:
                name = self._owned_native_array_operation_name(function, result, operation)
                declarations.extend(
                    (
                        CFunctionPrototype(
                            name,
                            "PyObject *",
                            (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                            storage="static",
                        ),
                        CDeclaration(
                            self._owned_native_array_operation_def_name(function, result, operation),
                            "static PyMethodDef",
                            CodeExpression(f'{{"{name}", (PyCFunction){name}, METH_VARARGS, ""}}'),
                        ),
                    )
                )
        for function, argument in self._default_native_array_arguments(plan):
            binder_name = self._default_native_array_binder_name(argument)
            declarations.extend(
                (
                    CFunctionPrototype(
                        binder_name,
                        "PyObject *",
                        (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                        storage="static",
                    ),
                    CDeclaration(
                        self._default_native_array_binder_def_name(argument),
                        "static PyMethodDef",
                        CodeExpression(f'{{"{binder_name}", (PyCFunction){binder_name}, METH_VARARGS, ""}}'),
                    ),
                )
            )
            for operation in argument.native_array_handle.default_handle.operations:
                name = self._owned_native_array_operation_name(function, argument, operation)
                declarations.extend(
                    (
                        CFunctionPrototype(
                            name,
                            "PyObject *",
                            (CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
                            storage="static",
                        ),
                        CDeclaration(
                            self._owned_native_array_operation_def_name(function, argument, operation),
                            "static PyMethodDef",
                            CodeExpression(f'{{"{name}", (PyCFunction){name}, METH_VARARGS, ""}}'),
                        ),
                    )
                )
        return tuple(declarations)

    def _native_array_operation_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Lower every planned owned-descriptor operation into a named C method."""
        return (
            *(
                self._native_array_capsule_release_function(result)
                for _function, result in self._owned_native_array_results(plan)
            ),
            *(
                self._native_array_capsule_release_function(argument)
                for _function, argument in self._default_native_array_arguments(plan)
            ),
            *(
                callback
                for variable in self._module_native_array_variables(plan)
                for callback in self._module_allocatable_descriptor_callbacks(variable)
            ),
            *(
                self._module_native_array_operation_function(variable, operation)
                for variable in self._module_native_array_variables(plan)
                if variable.native_array_handle is not None
                for operation in variable.native_array_handle.operations
            ),
            *(
                self._owned_native_array_operation_function(function, result, operation)
                for function, result in self._owned_native_array_results(plan)
                for operation in result.native_array_handle.operations
            ),
            *self._default_native_array_operation_functions(plan),
        )

    def _native_array_capsule_release_function(
        self,
        plan: ArgumentTransferPlan | ResultPlan,
    ) -> CFunction:
        """Release descriptor payload through the module that created its record."""
        descriptor = "owner_descriptor"
        body: tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...] = (
            CDeclaration(descriptor, "CFI_cdesc_t *", CodeExpression("(CFI_cdesc_t *)storage")),
            CIf(CodeExpression(f"{descriptor} == NULL"), body=(CReturn(),)),
        )
        handle = plan.native_array_handle
        if handle is None:
            raise ValueError(f"Native array handle {plan.owner_path!r} has no release policy")
        if plan.datatype_family is DatatypeFamily.STRING:
            if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE:
                body = (
                    *body,
                    CIf(
                        CodeExpression(f"{descriptor}->base_addr != NULL"),
                        body=(CExpressionStatement(CodeExpression(f"(void)CFI_deallocate({descriptor})")),),
                    ),
                )
        else:
            body = (
                *body,
                CExpressionStatement(
                    CodeExpression(
                        f"{self._owned_native_array_bridge_operation_name(plan, NativeArrayOperation.DESTROY)}"
                        f"({descriptor})"
                    )
                ),
            )
        return CFunction(
            self._native_array_capsule_release_name(plan),
            "void",
            parameters=(CParameter("storage", "void *"),),
            storage="static",
            body=body,
        )

    def _default_native_array_operation_functions(self, plan: ModulePlan) -> tuple[CFunction, ...]:
        """Lower lazy caller-handle binders and their owned operation methods."""
        arguments = self._default_native_array_arguments(plan)
        operations = tuple(
            self._owned_native_array_operation_function(function, argument, operation)
            for function, argument in arguments
            for operation in argument.native_array_handle.default_handle.operations
        )
        binders = tuple(
            self._default_native_array_binder_function(function, argument) for function, argument in arguments
        )
        return (*operations, *binders)

    def _module_native_array_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return borrowed module-handle plans in stable namespace order."""
        return tuple(
            variable
            for variable in self._variables(plan)
            if variable.binding.getter_action is ModuleGetterAction.NATIVE_ARRAY_HANDLE
        )

    def _module_array_owner_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return module arrays whose Python values retain the native module."""
        return tuple(
            variable
            for variable in self._variables(plan)
            if variable.binding.getter_action
            in {ModuleGetterAction.BORROWED_ARRAY_VIEW, ModuleGetterAction.NATIVE_ARRAY_HANDLE}
        )

    # Borrowed module native-array-handle operations.
    def _module_native_array_operation_function(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> CFunction:
        """Lower one planned borrowed-module operation into a private callable."""
        return CFunction(
            self._module_native_array_operation_name(variable, operation),
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=self._module_native_array_operation_body(variable, operation),
        )

    def _module_native_array_operation_body(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Dispatch one module operation without rediscovering semantic policy."""
        if operation in {
            NativeArrayOperation.NATIVE_BYTE_ORDER,
            NativeArrayOperation.ALIGNED,
            NativeArrayOperation.WRITEABLE,
            NativeArrayOperation.LAYOUT,
        }:
            return self._module_native_array_metadata_body(operation)
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
            NativeArrayOperation.ELEMENT_LENGTH,
            NativeArrayOperation.ARRAY_ACTUAL,
        }:
            return self._module_native_array_query_body(variable, operation)
        return self._module_native_array_data_operation_body(variable, operation)

    @staticmethod
    def _module_native_array_metadata_body(
        operation: NativeArrayOperation,
    ) -> tuple[CReturn, ...]:
        """Return binding-known metadata that requires no bridge call."""
        if operation is NativeArrayOperation.LAYOUT:
            return (CReturn(CodeExpression('PyUnicode_FromString("F")')),)
        return (CReturn(CodeExpression("PyBool_FromLong(1)")),)

    def _module_native_array_query_body(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> tuple[CReturn, ...]:
        """Return one scalar fact queried from the native bridge."""
        if operation is NativeArrayOperation.ARRAY_ACTUAL and self._uses_module_allocatable_descriptor(variable):
            return self._module_allocatable_array_actual_body(variable)
        call = f"{self._module_native_array_bridge_operation_name(variable, operation)}()"
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            expression = f"PyBool_FromLong({call})"
        elif operation is NativeArrayOperation.ELEMENT_LENGTH:
            expression = f"PyLong_FromLongLong((long long){call})"
        else:
            expression = f"PyLong_FromVoidPtr({call})"
        return (CReturn(CodeExpression(expression)),)

    def _module_native_array_data_operation_body(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Lower shape, extraction, descriptor, and mutation operations."""
        if operation is NativeArrayOperation.SHAPE:
            return self._module_native_array_shape_body(variable)
        if operation is NativeArrayOperation.TO_NUMPY:
            return self._module_native_array_descriptor_body(variable)
        if operation is NativeArrayOperation.DESCRIPTOR:
            return self._module_native_array_descriptor_body(variable)
        if operation is NativeArrayOperation.ASSOCIATE:
            return (
                CDeclaration("source_packed", "PyObject *"),
                CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &source_packed)) return NULL')),
                *self._pointer_association_source_nodes(variable),
                CExpressionStatement(
                    CodeExpression(
                        f"{self._module_native_array_bridge_operation_name(variable, operation)}(source_descriptor)"
                    )
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            )
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            return self._module_native_array_shape_mutation_body(variable, operation)
        if operation in {
            NativeArrayOperation.DEALLOCATE,
            NativeArrayOperation.NULLIFY,
        }:
            return (
                CExpressionStatement(
                    CodeExpression(f"{self._module_native_array_bridge_operation_name(variable, operation)}()")
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            )
        raise ValueError(f"Unsupported module native array operation for {variable.owner_path!r}: {operation!r}")

    def _module_native_array_shape_body(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Return current module-array extents as one Python tuple."""
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {variable.owner_path!r} has no rank")
        rank = handle.array.rank
        extents = tuple(f"extent_{axis}" for axis in range(rank))
        return (
            *(CDeclaration(name, "int64_t", CodeExpression("0")) for name in extents),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.SHAPE)}("
                    f"{', '.join(f'&{name}' for name in extents)})"
                )
            ),
            CDeclaration("shape", "PyObject *", CodeExpression(f"PyTuple_New({rank})")),
            CIf(CodeExpression("shape == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            *(
                CExpressionStatement(
                    CodeExpression(f"PyTuple_SET_ITEM(shape, {axis}, PyLong_FromLongLong((long long){name}))")
                )
                for axis, name in enumerate(extents)
            ),
            CExpressionStatement(CodeExpression("if (PyErr_Occurred()) { Py_DECREF(shape); return NULL; }")),
            CReturn(CodeExpression("shape")),
        )

    def _module_native_array_descriptor_body(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Return standard descriptor facts for module extraction and handoff."""
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {variable.owner_path!r} has no descriptor rank")
        if self._uses_module_allocatable_descriptor(variable):
            return self._module_allocatable_descriptor_body(variable)
        if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
            return self._module_pointer_descriptor_body(variable)
        return self._module_contiguous_descriptor_body(variable)

    @staticmethod
    def _uses_module_allocatable_descriptor(variable: ModuleVariablePlan) -> bool:
        """Return whether completed policy selected callback-based descriptor access."""
        handle = variable.native_array_handle
        return bool(
            handle is not None
            and handle.descriptor_interop is NativeArrayDescriptorInterop.MODULE_ALLOCATABLE_C_DESCRIPTOR
        )

    def _module_allocatable_descriptor_body(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CReturn, ...]:
        """Request the current standard descriptor and return its decoded facts."""
        return (
            CDeclaration("descriptor_record", "PyObject *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.DESCRIPTOR)}("
                    f"{self._module_descriptor_callback_name(variable)}, &descriptor_record)"
                )
            ),
            CReturn(CodeExpression("descriptor_record")),
        )

    def _module_allocatable_array_actual_body(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CReturn, ...]:
        """Request the current standard descriptor and expose only its data address."""
        return (
            CDeclaration("base_addr", "void *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.ARRAY_ACTUAL)}("
                    f"{self._module_array_actual_callback_name(variable)}, &base_addr)"
                )
            ),
            CReturn(CodeExpression("PyLong_FromVoidPtr(base_addr)")),
        )

    def _module_allocatable_descriptor_callbacks(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CFunction, ...]:
        """Return C consumers for descriptor-record and data-address operations."""
        if not self._uses_module_allocatable_descriptor(variable):
            return ()
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {variable.owner_path!r} has no descriptor rank")
        descriptor_callback = CFunction(
            self._module_descriptor_callback_name(variable),
            "void",
            parameters=(CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
            storage="static",
            body=(
                CExpressionStatement(CodeExpression("*(PyObject **)context = NULL")),
                *self._native_array_descriptor_record_nodes(
                    handle.array.rank,
                    "descriptor",
                    return_target="*(PyObject **)context",
                ),
            ),
        )
        array_actual_callback = CFunction(
            self._module_array_actual_callback_name(variable),
            "void",
            parameters=(CParameter("descriptor", "CFI_cdesc_t *"), CParameter("context", "void *")),
            storage="static",
            body=(
                CExpressionStatement(CodeExpression("*(void **)context = descriptor->base_addr")),
                CReturn(),
            ),
        )
        return descriptor_callback, array_actual_callback

    def _module_descriptor_callback_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local module descriptor callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        owner = re.sub(r"\W", "_", variable.owner_path).casefold()
        return f"prik_module_{owner}_descriptor_callback"

    def _module_array_actual_callback_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local module array actual callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        owner = re.sub(r"\W", "_", variable.owner_path).casefold()
        return f"prik_module_{owner}_array_actual_callback"

    def _module_contiguous_descriptor_body(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Build allocatable descriptor facts from native data and extents."""
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {variable.owner_path!r} has no descriptor rank")
        rank = handle.array.rank
        scalar_type = (
            None
            if variable.datatype_family is DatatypeFamily.STRING
            else PrimitiveScalarTypeRegistry.type_for(variable.semantic_type_name)
        )
        extents = tuple(f"extent_{axis}" for axis in range(rank))
        elem_len = (
            f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.ELEMENT_LENGTH)}()"
            if variable.datatype_family is DatatypeFamily.STRING
            else f"sizeof({scalar_type.c_spelling})"
        )
        nodes: list[CDeclaration | CExpressionStatement | CIf | CReturn] = [
            CDeclaration(
                "base_addr",
                "void *",
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.ARRAY_ACTUAL)}()"
                ),
            ),
            *(CDeclaration(name, "int64_t", CodeExpression("0")) for name in extents),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.SHAPE)}("
                    f"{', '.join(f'&{name}' for name in extents)})"
                )
            ),
            CDeclaration("dimensions", "PyObject *", CodeExpression(f"PyList_New({rank})")),
            CIf(CodeExpression("dimensions == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CDeclaration("stride", "int64_t", CodeExpression(elem_len)),
        ]
        for axis, extent in enumerate(extents):
            nodes.extend(
                (
                    CDeclaration(
                        f"dimension_{axis}",
                        "PyObject *",
                        CodeExpression(
                            f'Py_BuildValue("{{sL,sL,sL}}", "lower_bound", (long long)0, '
                            f'"extent", (long long){extent}, "sm", (long long)stride)'
                        ),
                    ),
                    CIf(
                        CodeExpression(f"dimension_{axis} == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(dimensions)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"PyList_SET_ITEM(dimensions, {axis}, dimension_{axis})")),
                    CExpressionStatement(CodeExpression(f"stride *= ({extent} > 0 ? {extent} : 1)")),
                )
            )
        nodes.extend(self._descriptor_record_return_nodes("base_addr", elem_len, rank))
        return tuple(nodes)

    def _module_pointer_descriptor_body(
        self,
        variable: ModuleVariablePlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Decode a call-local standard pointer descriptor without copying data."""
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Pointer module handle {variable.owner_path!r} has no descriptor rank")
        cfi_type = self._module_native_array_cfi_type(variable)
        if cfi_type is None:
            raise ValueError(f"Pointer module handle {variable.owner_path!r} has no CFI type")
        rank = handle.array.rank
        elem_len = self._module_native_array_elem_size(variable)
        return (
            CDeclaration("descriptor_storage", f"CFI_CDESC_T({rank})"),
            CDeclaration("descriptor", "CFI_cdesc_t *", CodeExpression("(CFI_cdesc_t *)&descriptor_storage")),
            CDeclaration("status", "int", CodeExpression("CFI_SUCCESS")),
            CExpressionStatement(
                CodeExpression(
                    f"status = CFI_establish(descriptor, NULL, CFI_attribute_pointer, "
                    f"{cfi_type}, {elem_len}, {rank}, NULL)"
                )
            ),
            CIf(
                CodeExpression("status != CFI_SUCCESS"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_RuntimeError, "failed to establish pointer descriptor reader")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, NativeArrayOperation.DESCRIPTOR)}"
                    "(descriptor)"
                )
            ),
            *self._native_array_descriptor_record_nodes(rank, "descriptor"),
        )

    def _descriptor_record_return_nodes(
        self,
        base_addr: str,
        elem_len: str,
        rank: int,
    ) -> tuple[CDeclaration | CExpressionStatement | CReturn, ...]:
        """Finish one standard descriptor mapping from existing dimensions."""
        return (
            CDeclaration(
                "descriptor_record",
                "PyObject *",
                CodeExpression(
                    f'Py_BuildValue("{{sK,sK,si,sO}}", "base_addr", '
                    f'(unsigned long long)(uintptr_t){base_addr}, "elem_len", '
                    f'(unsigned long long)({elem_len}), "rank", {rank}, "dim", dimensions)'
                ),
            ),
            CExpressionStatement(CodeExpression("Py_DECREF(dimensions)")),
            CReturn(CodeExpression("descriptor_record")),
        )

    def _module_native_array_shape_mutation_body(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> tuple[CDeclaration | CExpressionStatement | CReturn, ...]:
        """Parse and forward one planned module allocation/resize shape."""
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {variable.owner_path!r} has no mutation rank")
        rank = handle.array.rank
        objects = tuple(f"extent_{axis}_obj" for axis in range(rank))
        extents = tuple(f"extent_{axis}" for axis in range(rank))
        return (
            *(CDeclaration(name, "PyObject *") for name in objects),
            *(CDeclaration(name, "int64_t", CodeExpression("0")) for name in extents),
            CExpressionStatement(
                CodeExpression(
                    f'if (!PyArg_ParseTuple(args, "{"O" * rank}", '
                    f"{', '.join(f'&{name}' for name in objects)})) return NULL"
                )
            ),
            *(
                CExpressionStatement(
                    CodeExpression(f"{extent} = (int64_t)PyLong_AsLongLong({obj}); if (PyErr_Occurred()) return NULL")
                )
                for extent, obj in zip(extents, objects, strict=True)
            ),
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_native_array_bridge_operation_name(variable, operation)}({', '.join(extents)})"
                )
            ),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )

    def _module_native_array_operation_name(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the binding-local module native array operation name derived from the supplied completed binding records; this helper preserves completed policy."""
        owner = re.sub(r"\W", "_", variable.owner_path).casefold()
        return f"prik_module_{owner}_{operation.value}"

    def _module_native_array_operation_def_name(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the binding-local module native array operation def name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"{self._module_native_array_operation_name(variable, operation)}_def"

    def _module_native_array_bridge_operation_name(
        self,
        variable: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return one planner-owned module native-array entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(
            variable.owner_path, f"module:native_array:{operation.value}"
        ).symbol_name

    def _module_native_array_cache_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local module native array cache name derived from the supplied completed binding records; this helper preserves completed policy."""
        owner = re.sub(r"\W", "_", variable.owner_path).casefold()
        return f"prik_module_{owner}_handle"

    def _module_native_array_owner_name(self, variable: ModuleVariablePlan) -> str:
        """Return the binding-local module native array owner name derived from the supplied completed binding records; this helper preserves completed policy."""
        owner = re.sub(r"\W", "_", variable.owner_path).casefold()
        return f"prik_module_{owner}_owner"

    def _owned_native_array_results(self, plan: ModulePlan) -> tuple[tuple[FunctionPlan, ResultPlan], ...]:
        """Return wrapper-owned descriptor result plans in stable generation order."""
        return tuple(
            (function, result)
            for function in self._functions(plan)
            for result in function.results
            if result.native_array_handle is not None
            and result.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
        )

    def _default_native_array_arguments(
        self,
        plan: ModulePlan,
    ) -> tuple[tuple[FunctionPlan, ArgumentTransferPlan], ...]:
        """Return arguments that can attach storage to caller-created handles."""
        return tuple(
            (function, argument)
            for function in self._functions(plan)
            for argument in function.arguments
            if argument.native_array_handle is not None
            and argument.native_array_handle.default_handle.construction
            is NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR
        )

    def _owned_native_array_operation_function(
        self,
        function: FunctionPlan,
        result: ResultPlan,
        operation: NativeArrayOperation,
    ) -> CFunction:
        """Dispatch one planned owned-descriptor runtime operation."""
        name = self._owned_native_array_operation_name(function, result, operation)
        body = self._owned_native_array_operation_body(result, operation)
        return CFunction(
            name,
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=body,
        )

    def _default_native_array_binder_function(
        self,
        function: FunctionPlan,
        argument: ArgumentTransferPlan,
    ) -> CFunction:
        """Attach one compiler-compatible owned descriptor to a fresh handle."""
        handle = argument.native_array_handle
        default = handle.default_handle
        dtype = self._native_array_dtype_for_semantic_type(
            argument.semantic_type_name,
            argument.datatype_family,
        )
        cfi_type = self._native_array_cfi_type(argument)
        elem_len = f"sizeof({PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name).c_spelling})"
        nodes: list[CDeclaration | CExpressionStatement | CIf | CReturn] = [
            CDeclaration("handle_obj", "PyObject *"),
            CDeclaration("owner_descriptor", "CFI_cdesc_t *", CodeExpression("NULL")),
            CDeclaration("owner_status", "int", CodeExpression("CFI_SUCCESS")),
            CDeclaration("ops", "PyObject *", CodeExpression("NULL")),
            CDeclaration("operation", "PyObject *", CodeExpression("NULL")),
            CDeclaration("owner_obj", "PyObject *", CodeExpression("NULL")),
            CDeclaration("runtime", "PyObject *", CodeExpression("NULL")),
            CDeclaration("helper", "PyObject *", CodeExpression("NULL")),
            CDeclaration("result", "PyObject *", CodeExpression("NULL")),
            CExpressionStatement(CodeExpression('if (!PyArg_ParseTuple(args, "O", &handle_obj)) return NULL')),
            CExpressionStatement(
                CodeExpression(f"owner_descriptor = {self._zeroed_descriptor_allocation(handle.array.rank)}")
            ),
            CIf(
                CodeExpression("owner_descriptor == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(
                CodeExpression(
                    f"owner_status = CFI_establish(owner_descriptor, NULL, "
                    f"{self._owned_native_array_cfi_attribute(handle)}, {cfi_type}, {elem_len}, "
                    f"{handle.array.rank}, NULL)"
                )
            ),
            CIf(
                CodeExpression("owner_status != CFI_SUCCESS"),
                body=(
                    CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_RuntimeError, "failed to establish caller-created native '
                            'array descriptor storage")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(CodeExpression("ops = PyDict_New()")),
            CIf(
                CodeExpression("ops == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        ]
        for operation in default.operations:
            definition = self._owned_native_array_operation_def_name(function, argument, operation)
            nodes.extend(
                (
                    CExpressionStatement(CodeExpression(f"operation = PyCFunction_NewEx(&{definition}, NULL, NULL)")),
                    CIf(
                        CodeExpression("operation == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(ops)")),
                            CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CIf(
                        CodeExpression(f'PyDict_SetItemString(ops, "{operation.value}", operation) < 0'),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(operation)")),
                            CExpressionStatement(CodeExpression("Py_DECREF(ops)")),
                            CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression("Py_DECREF(operation)")),
                )
            )
        nodes.extend(
            (
                CExpressionStatement(
                    CodeExpression(
                        f"owner_obj = {self._native_array_capsule_new_expression(argument, 'owner_descriptor')}"
                    )
                ),
                CIf(
                    CodeExpression("owner_obj == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(ops)")),
                        CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(CodeExpression("owner_descriptor = NULL")),
                CExpressionStatement(CodeExpression('runtime = PyImport_ImportModule("prik.runtime.handles")')),
                CIf(
                    CodeExpression("runtime == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(owner_obj)")),
                        CExpressionStatement(CodeExpression("Py_DECREF(ops)")),
                        CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression('helper = PyObject_GetAttrString(runtime, "_bind_contract_native_array_handle")')
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(runtime)")),
                CIf(
                    CodeExpression("helper == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(owner_obj)")),
                        CExpressionStatement(CodeExpression("Py_DECREF(ops)")),
                        CExpressionStatement(CodeExpression("free(owner_descriptor)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        f'result = PyObject_CallFunction(helper, "OssiOOssO", handle_obj, '
                        f'"{handle.descriptor_kind.value}", "{dtype}", {handle.array.rank}, ops, owner_obj, '
                        f'"{default.descriptor_ownership.value}", "{handle.extraction_action.value}", Py_None)'
                    )
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(helper)")),
                CExpressionStatement(CodeExpression("Py_DECREF(owner_obj)")),
                CExpressionStatement(CodeExpression("Py_DECREF(ops)")),
                CReturn(CodeExpression("result")),
            )
        )
        return CFunction(
            self._default_native_array_binder_name(argument),
            "PyObject *",
            parameters=(CParameter("self", "PyObject *"), CParameter("args", "PyObject *")),
            storage="static",
            body=tuple(nodes),
        )

    def _owned_native_array_operation_body(
        self,
        result: ResultPlan,
        operation: NativeArrayOperation,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Return one operation body over persistent CFI owner storage."""
        if operation is NativeArrayOperation.ASSOCIATE:
            return self._owned_native_array_associate_body(result)
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            return self._owned_native_array_shape_mutation_body(
                result,
                release_existing=operation is NativeArrayOperation.RESIZE,
            )
        handler = self._owned_native_array_operation_handler(operation)
        materialize_descriptor = operation not in {
            NativeArrayOperation.NATIVE_BYTE_ORDER,
            NativeArrayOperation.ALIGNED,
            NativeArrayOperation.WRITEABLE,
            NativeArrayOperation.LAYOUT,
            NativeArrayOperation.DESCRIPTOR,
            NativeArrayOperation.DESTROY,
        }
        return (
            *self._owned_native_array_owner_nodes(
                result,
                "owner",
                materialize_descriptor=materialize_descriptor,
            ),
            *handler(result),
        )

    def _owned_native_array_operation_handler(self, operation: NativeArrayOperation):
        """Return one directly named operation lowerer."""
        handlers = {
            NativeArrayOperation.SHAPE: self._owned_native_array_shape_body,
            NativeArrayOperation.TO_NUMPY: self._owned_native_array_descriptor_record_body,
            NativeArrayOperation.ELEMENT_LENGTH: self._owned_native_array_element_length_body,
            NativeArrayOperation.ARRAY_ACTUAL: self._owned_native_array_actual_body,
            NativeArrayOperation.DESCRIPTOR: self._owned_native_array_descriptor_body,
            NativeArrayOperation.ALLOCATED: self._owned_native_array_allocated_body,
            NativeArrayOperation.ASSOCIATED: self._owned_native_array_associated_body,
            NativeArrayOperation.NATIVE_BYTE_ORDER: self._owned_native_array_true_body,
            NativeArrayOperation.ALIGNED: self._owned_native_array_true_body,
            NativeArrayOperation.WRITEABLE: self._owned_native_array_true_body,
            NativeArrayOperation.LAYOUT: self._owned_native_array_layout_body,
            NativeArrayOperation.CONTIGUOUS: self._owned_native_array_contiguous_body,
            NativeArrayOperation.DEALLOCATE: self._owned_native_array_deallocate_body,
            NativeArrayOperation.NULLIFY: self._owned_native_array_nullify_body,
            NativeArrayOperation.DESTROY: self._owned_native_array_destroy_body,
        }
        try:
            return handlers[operation]
        except KeyError:
            raise ValueError(f"Unsupported owned native array operation {operation.value!r}") from None

    def _owned_native_array_associate_body(
        self,
        result: ArgumentTransferPlan | ResultPlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Apply pointer assignment to one persistent owned descriptor."""
        bridge = self._owned_native_array_bridge_operation_name(result, NativeArrayOperation.ASSOCIATE)
        return (
            *self._owned_native_array_owner_nodes(
                result,
                "owner",
                trailing_objects=("source_packed",),
            ),
            *self._pointer_association_source_nodes(result),
            CExpressionStatement(CodeExpression(f"{bridge}(owner_descriptor, source_descriptor)")),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )

    def _owned_native_array_descriptor_record_body(
        self,
        result: ResultPlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Expose one owned descriptor record for shape or NumPy extraction."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor rank")
        return self._native_array_descriptor_record_nodes(handle.array.rank, "owner_descriptor")

    def _owned_native_array_shape_body(
        self,
        result: ResultPlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Expose extents using the typed compiler descriptor inquiry."""
        if self._is_owned_deferred_character_result(result):
            return self._owned_native_array_descriptor_record_body(result)
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no shape rank")
        dimensions = tuple(f"extent_{axis}" for axis in range(handle.array.rank))
        return (
            *(CDeclaration(name, "int64_t", CodeExpression("0")) for name in dimensions),
            CExpressionStatement(
                CodeExpression(
                    f"{self._owned_native_array_bridge_operation_name(result, NativeArrayOperation.SHAPE)}"
                    f"(owner_descriptor, {', '.join(f'&{name}' for name in dimensions)})"
                )
            ),
            CReturn(CodeExpression(f'Py_BuildValue("({",".join("L" for _ in dimensions)})", {", ".join(dimensions)})')),
        )

    def _owned_native_array_actual_body(self, _result: ResultPlan) -> tuple[CReturn, ...]:
        """Expose the current owned allocation data address."""
        return (CReturn(CodeExpression("PyLong_FromVoidPtr(owner_descriptor->base_addr)")),)

    def _owned_native_array_element_length_body(self, _result: ResultPlan) -> tuple[CReturn, ...]:
        """Expose the current deferred character element width."""
        return (CReturn(CodeExpression("PyLong_FromSize_t(owner_descriptor->elem_len)")),)

    def _owned_native_array_descriptor_body(
        self,
        _result: ResultPlan,
    ) -> tuple[CExpressionStatement | CReturn, ...]:
        """Expose the versioned owner capsule for cross-extension handoff."""
        return (
            CExpressionStatement(CodeExpression("Py_INCREF(owner_obj)")),
            CReturn(CodeExpression("owner_obj")),
        )

    def _owned_native_array_allocated_body(self, _result: ResultPlan) -> tuple[CReturn, ...]:
        """Report the current allocation state."""
        if self._is_owned_deferred_character_result(_result):
            return (CReturn(CodeExpression("PyBool_FromLong(owner_descriptor->base_addr != NULL)")),)
        return (
            CReturn(
                CodeExpression(
                    f"PyBool_FromLong({self._owned_native_array_bridge_operation_name(_result, NativeArrayOperation.ALLOCATED)}"
                    "(owner_descriptor))"
                )
            ),
        )

    def _owned_native_array_associated_body(self, result: ResultPlan) -> tuple[CReturn, ...]:
        """Report the current pointer association state."""
        return self._owned_native_array_bridge_state_body(result, NativeArrayOperation.ASSOCIATED)

    def _owned_native_array_contiguous_body(self, result: ResultPlan) -> tuple[CReturn, ...]:
        """Report whether the current pointer target is contiguous."""
        return self._owned_native_array_bridge_state_body(result, NativeArrayOperation.CONTIGUOUS)

    def _owned_native_array_bridge_state_body(
        self,
        result: ResultPlan,
        operation: NativeArrayOperation,
    ) -> tuple[CReturn, ...]:
        """Call one typed compiler descriptor inquiry."""
        return (
            CReturn(
                CodeExpression(
                    f"PyBool_FromLong({self._owned_native_array_bridge_operation_name(result, operation)}"
                    "(owner_descriptor))"
                )
            ),
        )

    def _owned_native_array_true_body(self, _result: ResultPlan) -> tuple[CReturn, ...]:
        """Return one invariant true array capability."""
        return (CReturn(CodeExpression("PyBool_FromLong(1)")),)

    def _owned_native_array_layout_body(self, _result: ResultPlan) -> tuple[CReturn, ...]:
        """Return the planned Fortran layout marker."""
        return (CReturn(CodeExpression('PyUnicode_FromString("F")')),)

    def _owned_native_array_deallocate_body(
        self,
        result: ResultPlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Deallocate payload while retaining owner storage."""
        return self._owned_native_array_deallocate_nodes(result, NativeArrayOperation.DEALLOCATE, free_owner=False)

    def _owned_native_array_nullify_body(
        self,
        result: ResultPlan,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Clear pointer association while retaining owner storage."""
        return self._owned_native_array_deallocate_nodes(result, NativeArrayOperation.NULLIFY, free_owner=False)

    def _owned_native_array_destroy_body(
        self,
        _result: ResultPlan,
    ) -> tuple[CExpressionStatement, ...]:
        """Destroy payload and persistent owner storage."""
        return (
            CExpressionStatement(CodeExpression("prik_native_array_handle_release(owner_handle)")),
            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
        )

    def _owned_native_array_owner_nodes(
        self,
        plan: ArgumentTransferPlan | ResultPlan,
        prefix: str,
        *,
        trailing_objects: tuple[str, ...] = (),
        materialize_descriptor: bool = True,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Decode a versioned descriptor owner capsule from a validated plan."""
        handle = plan.native_array_handle
        cfi_type = self._native_array_cfi_type(plan)
        return (
            CDeclaration(f"{prefix}_obj", "PyObject *"),
            *(CDeclaration(name, "PyObject *") for name in trailing_objects),
            CDeclaration(f"{prefix}_handle", "prik_native_array_handle *", CodeExpression("NULL")),
            *(
                (CDeclaration(f"{prefix}_descriptor", "CFI_cdesc_t *", CodeExpression("NULL")),)
                if materialize_descriptor
                else ()
            ),
            CExpressionStatement(
                CodeExpression(
                    f'if (!PyArg_ParseTuple(args, "{"O" * (1 + len(trailing_objects))}", '
                    f"&{prefix}_obj{', ' if trailing_objects else ''}"
                    f"{', '.join(f'&{name}' for name in trailing_objects)})) return NULL"
                )
            ),
            CExpressionStatement(
                CodeExpression(
                    f"{prefix}_handle = prik_native_array_handle_from_capsule({prefix}_obj, "
                    f"{self._native_array_handle_kind_constant(handle)}, {handle.array.rank}, {cfi_type}, "
                    f"{self._native_array_expected_element_size(plan)}, "
                    f"sizeof(CFI_CDESC_T({handle.array.rank})))"
                )
            ),
            CExpressionStatement(CodeExpression(f"if ({prefix}_handle == NULL) return NULL")),
            *(
                (
                    CExpressionStatement(
                        CodeExpression(f"{prefix}_descriptor = (CFI_cdesc_t *){prefix}_handle->descriptor")
                    ),
                )
                if materialize_descriptor
                else ()
            ),
        )

    def _pointer_association_source_nodes(
        self,
        plan: ArgumentTransferPlan | ResultPlan | ModuleVariablePlan | DerivedFieldPlan,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Establish one call-local pointer descriptor from validated source facts."""
        handle = plan.native_array_handle
        rank = handle.array.rank
        cfi_type = self._pointer_association_cfi_type(plan)
        expected_fields = 3 + 3 * rank
        nodes: list[CDeclaration | CExpressionStatement] = [
            CDeclaration("source_item", "PyObject *", CodeExpression("NULL")),
            CDeclaration("source_storage", f"CFI_CDESC_T({rank})"),
            CDeclaration("source_descriptor", "CFI_cdesc_t *", CodeExpression("NULL")),
            CDeclaration("source_base_addr", "void *", CodeExpression("NULL")),
            CDeclaration("source_elem_len", "size_t", CodeExpression("0")),
            CDeclaration("source_descriptor_rank", "CFI_rank_t", CodeExpression("0")),
            CDeclaration(f"source_extents[{rank}]", "CFI_index_t"),
            *(
                CDeclaration(f"source_{label}_{axis}", "CFI_index_t", CodeExpression("0"))
                for axis in range(rank)
                for label in ("lower_bound", "extent", "stride_multiplier")
            ),
            CDeclaration("source_establish_status", "int", CodeExpression("CFI_SUCCESS")),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyTuple_Check(source_packed) || PyTuple_GET_SIZE(source_packed) != {expected_fields}) {{ "
                    f'PyErr_SetString(PyExc_TypeError, "pointer association requires {expected_fields} '
                    'descriptor facts"); return NULL; }'
                )
            ),
            *self._pointer_association_fact_nodes("source_base_addr", 0, pointer=True),
            *self._pointer_association_fact_nodes("source_elem_len", 1, unsigned=True),
            *self._pointer_association_fact_nodes("source_descriptor_rank", 2),
        ]
        for axis in range(rank):
            offset = 3 + 3 * axis
            nodes.extend(
                (
                    *self._pointer_association_fact_nodes(f"source_lower_bound_{axis}", offset),
                    *self._pointer_association_fact_nodes(f"source_extent_{axis}", offset + 1),
                    *self._pointer_association_fact_nodes(f"source_stride_multiplier_{axis}", offset + 2),
                    CExpressionStatement(CodeExpression(f"source_extents[{axis}] = source_extent_{axis}")),
                )
            )
        nodes.extend(
            (
                CExpressionStatement(
                    CodeExpression(
                        f"if (source_descriptor_rank != {rank}) {{ PyErr_Format(PyExc_ValueError, "
                        f'"pointer association source rank %d does not match destination rank {rank}", '
                        "(int)source_descriptor_rank); return NULL; }"
                    )
                ),
                CExpressionStatement(
                    CodeExpression(
                        "source_establish_status = CFI_establish((CFI_cdesc_t *)&source_storage, "
                        f"source_base_addr, CFI_attribute_pointer, {cfi_type}, source_elem_len, "
                        f"{rank}, source_extents)"
                    )
                ),
                CExpressionStatement(
                    CodeExpression(
                        "if (source_establish_status != CFI_SUCCESS) { "
                        'PyErr_SetString(PyExc_RuntimeError, "failed to establish pointer association source"); '
                        "return NULL; }"
                    )
                ),
            )
        )
        for axis in range(rank):
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(
                            f"((CFI_cdesc_t *)&source_storage)->dim[{axis}].lower_bound = source_lower_bound_{axis}"
                        )
                    ),
                    CExpressionStatement(
                        CodeExpression(f"((CFI_cdesc_t *)&source_storage)->dim[{axis}].extent = source_extent_{axis}")
                    ),
                    CExpressionStatement(
                        CodeExpression(
                            f"((CFI_cdesc_t *)&source_storage)->dim[{axis}].sm = source_stride_multiplier_{axis}"
                        )
                    ),
                )
            )
        nodes.append(CExpressionStatement(CodeExpression("source_descriptor = (CFI_cdesc_t *)&source_storage")))
        return tuple(nodes)

    @staticmethod
    def _pointer_association_fact_nodes(
        target: str,
        index: int,
        *,
        pointer: bool = False,
        unsigned: bool = False,
    ) -> tuple[CExpressionStatement, ...]:
        """Decode one pointer-association descriptor fact."""
        if pointer:
            conversion = "(void *)PyLong_AsVoidPtr(source_item)"
            error = f"{target} == NULL && PyErr_Occurred()"
        elif unsigned:
            conversion = "(size_t)PyLong_AsUnsignedLongLong(source_item)"
            error = "PyErr_Occurred()"
        else:
            conversion = "PyLong_AsLongLong(source_item)"
            error = "PyErr_Occurred()"
        return (
            CExpressionStatement(CodeExpression(f"source_item = PyTuple_GET_ITEM(source_packed, {index})")),
            CExpressionStatement(CodeExpression(f"{target} = {conversion}")),
            CExpressionStatement(CodeExpression(f"if ({error}) return NULL")),
        )

    @staticmethod
    def _pointer_association_cfi_type(
        plan: ArgumentTransferPlan | ResultPlan | ModuleVariablePlan | DerivedFieldPlan,
    ) -> str:
        """Return the completed standard-descriptor type for pointer assignment."""
        if isinstance(plan, DerivedFieldPlan):
            if plan.string_element:
                return "CFI_type_char"
        elif plan.datatype_family is DatatypeFamily.STRING:
            return "CFI_type_char"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).cfi_type_spelling

    def _native_array_descriptor_record_nodes(
        self,
        rank: int,
        descriptor_name: str,
        *,
        return_target: str | None = None,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Decode a standard C descriptor into the runtime's mapping protocol."""
        failure_return = CReturn() if return_target is not None else CReturn(CodeExpression("NULL"))
        nodes: list[CDeclaration | CExpressionStatement | CIf | CReturn] = [
            CDeclaration("dimensions", "PyObject *", CodeExpression(f"PyList_New({rank})")),
            CIf(CodeExpression("dimensions == NULL"), body=(failure_return,)),
        ]
        for axis in range(rank):
            item = f"dimension_{axis}"
            nodes.extend(
                (
                    CDeclaration(
                        item,
                        "PyObject *",
                        CodeExpression(
                            f'Py_BuildValue("{{sL,sL,sL}}", "lower_bound", '
                            f'(long long){descriptor_name}->dim[{axis}].lower_bound, "extent", '
                            f'(long long){descriptor_name}->dim[{axis}].extent, "sm", '
                            f"(long long){descriptor_name}->dim[{axis}].sm)"
                        ),
                    ),
                    CIf(
                        CodeExpression(f"{item} == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(dimensions)")),
                            failure_return,
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"PyList_SET_ITEM(dimensions, {axis}, {item})")),
                )
            )
        nodes.extend(
            (
                CDeclaration(
                    "descriptor_record",
                    "PyObject *",
                    CodeExpression(
                        f'Py_BuildValue("{{sK,sK,si,sO}}", "base_addr", '
                        f'(unsigned long long)(uintptr_t){descriptor_name}->base_addr, "elem_len", '
                        f'(unsigned long long){descriptor_name}->elem_len, "rank", '
                        f'(int){descriptor_name}->rank, "dim", dimensions)'
                    ),
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(dimensions)")),
                (
                    CExpressionStatement(CodeExpression(f"{return_target} = descriptor_record"))
                    if return_target is not None
                    else CReturn(CodeExpression("descriptor_record"))
                ),
                *((CReturn(),) if return_target is not None else ()),
            )
        )
        return tuple(nodes)

    def _owned_native_array_deallocate_nodes(
        self,
        result: ResultPlan,
        operation: NativeArrayOperation,
        *,
        free_owner: bool,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Release payload and optionally persistent descriptor storage."""
        if not self._is_owned_deferred_character_result(result):
            nodes: list[CExpressionStatement | CReturn] = [
                CExpressionStatement(
                    CodeExpression(
                        f"{self._owned_native_array_bridge_operation_name(result, operation)}(owner_descriptor)"
                    )
                ),
            ]
            if free_owner:
                nodes.append(CExpressionStatement(CodeExpression("free(owner_descriptor)")))
            nodes.append(CExpressionStatement(CodeExpression("Py_RETURN_NONE")))
            return tuple(nodes)
        nodes: list[CDeclaration | CExpressionStatement | CIf | CReturn] = [
            CDeclaration("status", "int", CodeExpression("CFI_SUCCESS")),
            CIf(
                CodeExpression("owner_descriptor->base_addr != NULL"),
                body=(
                    CExpressionStatement(CodeExpression("status = CFI_deallocate(owner_descriptor)")),
                    CIf(
                        CodeExpression("status != CFI_SUCCESS"),
                        body=(
                            *((CExpressionStatement(CodeExpression("free(owner_descriptor)")),) if free_owner else ()),
                            CExpressionStatement(
                                CodeExpression(
                                    'PyErr_SetString(PyExc_RuntimeError, "failed to deallocate owned native array")'
                                )
                            ),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                ),
            ),
        ]
        if free_owner:
            nodes.append(CExpressionStatement(CodeExpression("free(owner_descriptor)")))
        nodes.append(CExpressionStatement(CodeExpression("Py_RETURN_NONE")))
        return tuple(nodes)

    def _owned_native_array_shape_mutation_body(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        *,
        release_existing: bool,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Allocate or replace descriptor payload with one validated shape."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no resize rank")
        rank = handle.array.rank
        cfi_type = self._native_array_cfi_type(result)
        if cfi_type is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no CFI element type")
        extent_objects = tuple(f"extent_{axis}_obj" for axis in range(rank))
        targets = ", ".join(f"&{name}" for name in ("owner_obj", *extent_objects))
        nodes: list[CDeclaration | CExpressionStatement | CIf | CReturn] = [
            CDeclaration("owner_obj", "PyObject *"),
            *(CDeclaration(name, "PyObject *") for name in extent_objects),
            CDeclaration("owner_handle", "prik_native_array_handle *", CodeExpression("NULL")),
            CDeclaration("owner_descriptor", "CFI_cdesc_t *", CodeExpression("NULL")),
            CDeclaration(f"lower_bounds[{rank}]", "CFI_index_t"),
            CDeclaration(f"upper_bounds[{rank}]", "CFI_index_t"),
            CDeclaration("status", "int", CodeExpression("CFI_SUCCESS")),
            CExpressionStatement(
                CodeExpression(f'if (!PyArg_ParseTuple(args, "{"O" * (rank + 1)}", {targets})) return NULL')
            ),
            CExpressionStatement(
                CodeExpression(
                    "owner_handle = prik_native_array_handle_from_capsule(owner_obj, "
                    f"{self._native_array_handle_kind_constant(handle)}, {rank}, {cfi_type}, "
                    f"{self._native_array_expected_element_size(result)}, sizeof(CFI_CDESC_T({rank})))"
                )
            ),
            CExpressionStatement(CodeExpression("if (owner_handle == NULL) return NULL")),
            CExpressionStatement(CodeExpression("owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor")),
        ]
        for axis, item in enumerate(extent_objects):
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"upper_bounds[{axis}] = (CFI_index_t)PyLong_AsLongLong({item}) - 1")
                    ),
                    CExpressionStatement(CodeExpression("if (PyErr_Occurred()) return NULL")),
                    CExpressionStatement(CodeExpression(f"lower_bounds[{axis}] = 0")),
                )
            )
        release_nodes = self._owned_native_array_resize_release_nodes(result) if release_existing else ()
        action = "resize" if release_existing else "allocate"
        nodes.extend(
            (
                *release_nodes,
                CExpressionStatement(
                    CodeExpression(
                        "status = CFI_allocate(owner_descriptor, lower_bounds, upper_bounds, "
                        "owner_descriptor->elem_len)"
                    )
                ),
                CExpressionStatement(
                    CodeExpression(
                        "if (status != CFI_SUCCESS) { PyErr_SetString(PyExc_RuntimeError, "
                        f'"failed to {action} owned native array"); return NULL; }}'
                    )
                ),
                CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
            )
        )
        return tuple(nodes)

    def _owned_native_array_resize_release_nodes(
        self,
        result: ResultPlan,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Release existing owned payload before resize through the selected descriptor path."""
        if not self._is_owned_deferred_character_result(result):
            return (
                CExpressionStatement(
                    CodeExpression(
                        f"{self._owned_native_array_bridge_operation_name(result, NativeArrayOperation.DEALLOCATE)}"
                        "(owner_descriptor)"
                    )
                ),
            )
        return (
            CIf(
                CodeExpression("owner_descriptor->base_addr != NULL"),
                body=(
                    CExpressionStatement(CodeExpression("status = CFI_deallocate(owner_descriptor)")),
                    CExpressionStatement(
                        CodeExpression(
                            "if (status != CFI_SUCCESS) { PyErr_SetString(PyExc_RuntimeError, "
                            '"failed to release owned native array before resize"); return NULL; }'
                        )
                    ),
                ),
            ),
        )

    def _owned_native_array_operation_name(
        self,
        _function: FunctionPlan | None,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return one stable private operation symbol."""
        owner = re.sub(r"\W", "_", result.owner_path).casefold()
        return f"prik_owned_{owner}_{operation.value}"

    def _owned_native_array_bridge_operation_name(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return one planner-owned descriptor operation symbol."""
        return self._generated_support_procedure_entrypoint(
            result.owner_path, f"native_array:owned:{operation.value}"
        ).symbol_name

    def _owned_native_array_operation_def_name(
        self,
        function: FunctionPlan | None,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the private PyMethodDef symbol for one operation."""
        return f"{self._owned_native_array_operation_name(function, result, operation)}_def"

    def _default_native_array_binder_name(self, argument: ArgumentTransferPlan) -> str:
        """Return one private lazy descriptor-attachment callable name."""
        owner = re.sub(r"\W", "_", argument.owner_path).casefold()
        return f"prik_bind_default_{owner}"

    def _default_native_array_binder_def_name(self, argument: ArgumentTransferPlan) -> str:
        """Return the binding-local default native array binder def name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"{self._default_native_array_binder_name(argument)}_def"

    @staticmethod
    def _native_array_capsule_release_name(plan: ArgumentTransferPlan | ResultPlan) -> str:
        """Return one stable descriptor-payload release callback symbol."""
        owner = re.sub(r"\W", "_", plan.owner_path).casefold()
        return f"prik_release_native_handle_{owner}"

    @staticmethod
    def _documented(functions: tuple[CFunction, ...], *doc: str) -> tuple[CFunction, ...]:
        """Attach explanatory prose to generated functions that carry none."""
        return tuple(function if function.doc else replace(function, doc=doc) for function in functions)

    def _visit_ModuleVariablePlan(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Lower binding-owned getter and setter actions into C functions."""
        # The binding facet names the Python attribute and the C symbols it
        # calls; the native Fortran variable belongs to the bridge facet and is
        # deliberately not read here.
        name = plan.binding.python_names[0]
        return (
            *self._documented(
                self._lower_module_getter(plan),
                f"Read module attribute '{name}'.",
                _BINDING_GETTER_SUMMARIES.get(plan.binding.getter_action, ""),
            ),
            *self._documented(
                self._lower_module_setter(plan),
                f"Assign module attribute '{name}'.",
                _BINDING_SETTER_SUMMARIES.get(plan.binding.setter_action, ""),
            ),
        )

    def _lower_module_getter(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Dispatch one completed Python getter action explicitly."""
        action = plan.binding.getter_action
        match action:
            case ModuleGetterAction.CONSTANT_VALUE:
                return self._lower_module_getter_constant_value(plan)
            case ModuleGetterAction.NATIVE_CONSTANT_VALUE:
                return self._lower_module_getter_native_constant_value(plan)
            case ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE:
                return self._lower_module_getter_constant_value(plan)
            case ModuleGetterAction.DIRECT_VALUE:
                return self._lower_module_getter_direct_value(plan)
            case ModuleGetterAction.CHARACTER_VALUE:
                return self._lower_module_getter_character_value(plan)
            case ModuleGetterAction.NULLABLE_SNAPSHOT:
                return self._lower_module_getter_nullable_snapshot(plan)
            case ModuleGetterAction.BORROWED_ARRAY_VIEW:
                return self._lower_module_getter_borrowed_array_view(plan)
            case ModuleGetterAction.NATIVE_ARRAY_HANDLE:
                return self._lower_module_getter_native_array_handle(plan)
            case ModuleGetterAction.DERIVED_OBJECT:
                return self._lower_module_getter_derived_object(plan)
        raise ValueError(f"Unsupported C module getter action for {plan.owner_path!r}: {action!r}")

    def _lower_module_getter_constant_value(self, _plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Constants are materialized in the module dictionary at initialization."""
        return ()

    def _lower_module_getter_native_constant_value(self, _plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Compiler-evaluated constants are materialized from their bridge getter."""
        return ()

    def _lower_module_getter_direct_value(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Return a copied Python scalar from one native getter call."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=(
                    CDeclaration(
                        "value",
                        scalar_type.c_spelling,
                        CodeExpression(f"{self._module_bridge_getter_name(plan)}()"),
                    ),
                    CDeclaration(
                        "result",
                        "PyObject *",
                        CodeExpression(self._scalar_result_expression(scalar_type, "&value", module=True)),
                    ),
                    CReturn(CodeExpression("result")),
                ),
            ),
        )

    def _module_character_length(self, plan: ModuleVariablePlan) -> int:
        """Return the declared width one character module accessor copies."""
        length = plan.character_length
        if length is None or length <= 0:
            raise ValueError(f"Character module variable {plan.owner_path!r} has no declared length")
        return length

    def _lower_module_getter_character_value(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Copy one fixed native character module variable into an independent Python string."""
        length = self._module_character_length(plan)
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=(
                    CDeclaration(f"value[{length + 1}]", "char"),
                    CExpressionStatement(CodeExpression(f"{self._module_bridge_getter_name(plan)}(value)")),
                    CExpressionStatement(CodeExpression(f"value[{length}] = '\\0'")),
                    CReturn(CodeExpression(f'PyUnicode_DecodeUTF8(value, {length}, "strict")')),
                ),
            ),
        )

    def _lower_module_setter_character_value(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Validate and copy one exact-width Python string into native module storage.

        The setter reports failure with ``-1`` rather than ``NULL``: a module
        attribute assignment is an ``int`` slot, not a returned object.
        """
        length = self._module_character_length(plan)
        name = plan.binding.python_names[0]
        return (
            CFunction(
                self._module_setter_name(plan),
                "int",
                parameters=(CParameter("value_obj", "PyObject *"),),
                storage="static",
                body=(
                    CIf(
                        CodeExpression("!PyUnicode_Check(value_obj)"),
                        body=(
                            CExpressionStatement(
                                CodeExpression(
                                    f'PyErr_SetString(PyExc_TypeError, "Expected str for module variable {name}")'
                                )
                            ),
                            CReturn(CodeExpression("-1")),
                        ),
                    ),
                    CDeclaration("value_length", "Py_ssize_t", CodeExpression("0")),
                    CDeclaration(
                        "value",
                        "const char *",
                        CodeExpression("PyUnicode_AsUTF8AndSize(value_obj, &value_length)"),
                    ),
                    CIf(CodeExpression("value == NULL"), body=(CReturn(CodeExpression("-1")),)),
                    CIf(
                        CodeExpression(f"value_length != {length} || (Py_ssize_t)strlen(value) != value_length"),
                        body=(
                            CExpressionStatement(
                                CodeExpression(
                                    f'PyErr_SetString(PyExc_TypeError, "Module variable {name} must encode to '
                                    f'exactly {length} bytes without embedded NUL")'
                                )
                            ),
                            CReturn(CodeExpression("-1")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"{self._module_bridge_setter_name(plan)}(value)")),
                    CReturn(CodeExpression("0")),
                ),
            ),
        )

    def _lower_module_getter_nullable_snapshot(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Return None or a detached Python copy from a nullable native snapshot."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return self._lower_module_getter_nullable_character_snapshot(plan)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=(
                    CDeclaration(
                        "data",
                        "void *",
                        CodeExpression(f"{self._module_bridge_getter_name(plan)}()"),
                    ),
                    CIf(
                        CodeExpression("data == NULL"),
                        body=(CExpressionStatement(CodeExpression("Py_RETURN_NONE")),),
                    ),
                    CDeclaration(
                        "value",
                        scalar_type.c_spelling,
                        CodeExpression(f"*({scalar_type.c_spelling} *)data"),
                    ),
                    CDeclaration(
                        "result",
                        "PyObject *",
                        CodeExpression(self._scalar_result_expression(scalar_type, "&value", module=True)),
                    ),
                    CExpressionStatement(CodeExpression("free(data)")),
                    CReturn(CodeExpression("result")),
                ),
            ),
        )

    def _lower_module_getter_nullable_character_snapshot(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[CFunction, ...]:
        """Decode one nullable detached character snapshot, or report absence.

        An unallocated descriptor and a failed allocation are different
        outcomes: the first is ``None``, the second is a ``MemoryError``, and
        only the reported width separates them.
        """
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=(
                    CDeclaration("length", "int64_t", CodeExpression("0")),
                    CDeclaration(
                        "data",
                        "void *",
                        CodeExpression(f"{self._module_bridge_getter_name(plan)}(&length)"),
                    ),
                    CIf(
                        CodeExpression("data == NULL"),
                        body=(
                            CIf(
                                CodeExpression("length > 0"),
                                body=(CReturn(CodeExpression("PyErr_NoMemory()")),),
                            ),
                            CExpressionStatement(CodeExpression("Py_RETURN_NONE")),
                        ),
                    ),
                    CDeclaration(
                        "result",
                        "PyObject *",
                        CodeExpression('PyUnicode_DecodeUTF8((const char *)data, (Py_ssize_t)length, "strict")'),
                    ),
                    CExpressionStatement(CodeExpression("free(data)")),
                    CReturn(CodeExpression("result")),
                ),
            ),
        )

    def _lower_module_getter_borrowed_array_view(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Create one live Fortran-ordered NumPy alias over fixed module storage."""
        array = plan.array
        if array is None or array.rank is None:
            raise ValueError(f"Module array view {plan.owner_path!r} has no fixed rank")
        # A character element is a fixed-width bytes dtype whose width the
        # Fortran variable reports, so it carries an itemsize instead of naming
        # a NumPy scalar type macro.
        character = plan.datatype_family is DatatypeFamily.STRING
        if character:
            element_size = "itemsize"
            numpy_type = "NPY_STRING"
            numpy_itemsize = "(int)itemsize"
        else:
            scalar = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
            element_size = f"sizeof({scalar.c_spelling})"
            numpy_type = str(scalar.numpy_type_macro)
            numpy_itemsize = "0"
        owner = self._module_native_array_owner_name(plan)
        width = ("itemsize",) if character else ()
        extents = tuple(f"extent_{axis}" for axis in range(array.rank))
        strides = "strides"
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=(
                    *(CDeclaration(name, "int64_t", CodeExpression("0")) for name in (*width, *extents)),
                    CDeclaration(
                        "data",
                        "void *",
                        CodeExpression(
                            f"{self._module_bridge_getter_name(plan)}"
                            f"({', '.join(f'&{name}' for name in (*width, *extents))})"
                        ),
                    ),
                    CDeclaration(
                        f"dimensions[{array.rank}]",
                        "npy_intp",
                        CodeExpression("{" + ", ".join(extents) + "}"),
                    ),
                    CDeclaration(f"{strides}[{array.rank}]", "npy_intp"),
                    CExpressionStatement(CodeExpression(f"{strides}[0] = (npy_intp){element_size}")),
                    *(
                        CExpressionStatement(
                            CodeExpression(f"{strides}[{axis}] = {strides}[{axis - 1}] * dimensions[{axis - 1}]")
                        )
                        for axis in range(1, array.rank)
                    ),
                    CDeclaration(
                        "result",
                        "PyObject *",
                        CodeExpression(
                            f"PyArray_New(&PyArray_Type, {array.rank}, dimensions, {numpy_type}, "
                            f"{strides}, data, {numpy_itemsize}, NPY_ARRAY_F_CONTIGUOUS | NPY_ARRAY_ALIGNED | "
                            "NPY_ARRAY_WRITEABLE, NULL)"
                        ),
                    ),
                    *self._ordinary_array_field_owner_nodes("result", owner),
                ),
            ),
        )

    def _lower_module_getter_native_array_handle(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Create one stable borrowed runtime handle from planned module operations."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module native array handle {plan.owner_path!r} is incomplete")
        cache = self._module_native_array_cache_name(plan)
        owner = self._module_native_array_owner_name(plan)
        prefix = f"{cache}_build"
        nodes: list[CDeclaration | CExpressionStatement | CIf | CReturn] = [
            CIf(
                CodeExpression(f"{cache} != NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_INCREF({cache})")),
                    CReturn(CodeExpression(cache)),
                ),
            ),
            CDeclaration(f"{prefix}_ops", "PyObject *", CodeExpression("PyDict_New()")),
            CDeclaration(f"{prefix}_operation", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_runtime", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_helper", "PyObject *", CodeExpression("NULL")),
            CIf(CodeExpression(f"{prefix}_ops == NULL"), body=(CReturn(CodeExpression("NULL")),)),
        ]
        for operation in handle.operations:
            definition = self._module_native_array_operation_def_name(plan, operation)
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"{prefix}_operation = PyCFunction_NewEx(&{definition}, NULL, NULL)")
                    ),
                    CIf(
                        CodeExpression(f"{prefix}_operation == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CIf(
                        CodeExpression(
                            f'PyDict_SetItemString({prefix}_ops, "{operation.value}", {prefix}_operation) < 0'
                        ),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_operation)")),
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_operation)")),
                )
            )
        nodes.extend(
            (
                CExpressionStatement(
                    CodeExpression(f'{prefix}_runtime = PyImport_ImportModule("prik.runtime.handles")')
                ),
                CIf(
                    CodeExpression(f"{prefix}_runtime == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        f"{prefix}_helper = PyObject_GetAttrString({prefix}_runtime, "
                        '"_native_array_handle_from_generated_ops")'
                    )
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_runtime)")),
                CIf(
                    CodeExpression(f"{prefix}_helper == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        self._native_array_handle_factory_call(
                            helper=f"{prefix}_helper",
                            target=cache,
                            descriptor_kind=handle.descriptor_kind.value,
                            semantic_type_name=plan.semantic_type_name,
                            datatype_family=plan.datatype_family,
                            rank=handle.array.rank,
                            ops=f"{prefix}_ops",
                            owner=f"{owner} != NULL ? {owner} : Py_None",
                            descriptor_ownership="borrowed",
                            extraction_action=handle.extraction_action.value,
                        )
                    )
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_helper)")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                CIf(CodeExpression(f"{cache} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
                CExpressionStatement(CodeExpression(f"Py_INCREF({cache})")),
                CReturn(CodeExpression(cache)),
            )
        )
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=tuple(nodes),
            ),
        )

    def _lower_module_getter_derived_object(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Construct one live direct-address wrapper or typed member proxy."""
        derived = plan.derived
        if derived is None:
            raise ValueError(f"Derived module object {plan.owner_path!r} has no access plan")
        if derived.access is ModuleObjectAccessMechanism.VALUE_COPY:
            return self._lower_module_getter_derived_value_copy(plan)
        owner = self._derived_module_owner_name(plan)
        capsule_expression = (
            CodeExpression(
                f"PyCapsule_New({self._module_bridge_getter_name(plan)}(), "
                f'"{self._derived_capsule_name(derived.handoff.backend_symbol)}", NULL)'
            )
            if derived.access is ModuleObjectAccessMechanism.DIRECT_ADDRESS
            else CodeExpression("Py_None")
        )
        ops_name = self._module_member_ops_name(plan, ())
        body: list = [CDeclaration("capsule", "PyObject *", capsule_expression)]
        if derived.access is ModuleObjectAccessMechanism.DIRECT_ADDRESS:
            body.append(CIf(CodeExpression("capsule == NULL"), body=(CReturn(CodeExpression("NULL")),)))
        body.extend(self._module_derived_wrapper_nodes(plan, owner, ops_name))
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=tuple(body),
            ),
        )

    def _lower_module_getter_derived_value_copy(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Wrap one fresh native copy of an explicit derived constant."""
        derived = plan.derived
        if derived is None:
            raise ValueError(f"Derived module constant {plan.owner_path!r} has no handoff")
        type_name = derived.handoff.type_name
        type_symbol = derived.handoff.backend_symbol
        owner = self._derived_module_owner_name(plan)
        address = "address"
        capsule = "capsule"
        helper = "helper"
        return (
            CFunction(
                self._module_getter_name(plan),
                "PyObject *",
                storage="static",
                body=(
                    CDeclaration(address, "void *", CodeExpression(f"{self._module_bridge_getter_name(plan)}()")),
                    CIf(
                        CodeExpression(f"{address} == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CDeclaration(
                        capsule,
                        "PyObject *",
                        CodeExpression(
                            f'PyCapsule_New({address}, "{self._derived_capsule_name(type_symbol)}", '
                            f"{self._derived_capsule_destructor_name(type_symbol)})"
                        ),
                    ),
                    CIf(
                        CodeExpression(f"{capsule} == NULL"),
                        body=(
                            CExpressionStatement(
                                CodeExpression(f"{self._derived_destroy_bridge_name(type_symbol)}({address})")
                            ),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CDeclaration(
                        helper,
                        "PyObject *",
                        CodeExpression(f'PyObject_GetAttrString({owner}, "_prik_wrap_{type_name}")'),
                    ),
                    CIf(
                        CodeExpression(f"{helper} == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CDeclaration(
                        "result",
                        "PyObject *",
                        CodeExpression(f"PyObject_CallFunctionObjArgs({helper}, {capsule}, NULL)"),
                    ),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({helper})")),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                    CReturn(CodeExpression("result")),
                ),
            ),
        )

    def _module_derived_wrapper_nodes(
        self,
        plan: ModuleVariablePlan,
        owner: str,
        ops_name: str | None,
    ) -> tuple:
        """Call the namespace's internal wrapper helper with explicit owner/ops."""
        if plan.derived is None:
            return ()
        type_name = plan.derived.handoff.type_name
        nodes = [
            CDeclaration(
                "helper",
                "PyObject *",
                CodeExpression(f'PyObject_GetAttrString({owner}, "_prik_wrap_{type_name}")'),
            ),
            CIf(
                CodeExpression("helper == NULL"),
                body=(
                    *(
                        (CExpressionStatement(CodeExpression("Py_DECREF(capsule)")),)
                        if plan.derived.access is ModuleObjectAccessMechanism.DIRECT_ADDRESS
                        else ()
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        ]
        ops_argument = "Py_None"
        if ops_name is not None:
            nodes.extend(
                (
                    CDeclaration(
                        "ops",
                        "PyObject *",
                        CodeExpression(f'PyObject_GetAttrString({owner}, "{ops_name}")'),
                    ),
                    CIf(
                        CodeExpression("ops == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("Py_DECREF(helper)")),
                            *(
                                (CExpressionStatement(CodeExpression("Py_DECREF(capsule)")),)
                                if plan.derived.access is ModuleObjectAccessMechanism.DIRECT_ADDRESS
                                else ()
                            ),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                )
            )
            ops_argument = "ops"
        origin = plan.derived.handoff.storage.value
        nodes.extend(
            (
                CDeclaration(
                    "result",
                    "PyObject *",
                    CodeExpression(
                        f'PyObject_CallFunction(helper, "OOOs", capsule, {owner}, {ops_argument}, "{origin}")'
                    ),
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(helper)")),
                *((CExpressionStatement(CodeExpression("Py_DECREF(ops)")),) if ops_name is not None else ()),
                *(
                    (CExpressionStatement(CodeExpression("Py_DECREF(capsule)")),)
                    if plan.derived.access is ModuleObjectAccessMechanism.DIRECT_ADDRESS
                    else ()
                ),
                CReturn(CodeExpression("result")),
            )
        )
        return tuple(nodes)

    def _lower_module_setter(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Dispatch one completed Python setter action explicitly."""
        action = plan.binding.setter_action
        match action:
            case SetterAction.WRITE_THROUGH:
                return self._lower_module_setter_write_through(plan)
            case SetterAction.REJECT_REPLACEMENT:
                return self._lower_module_setter_reject_replacement(plan)
            case SetterAction.OMIT:
                return self._lower_module_setter_omit(plan)
        raise ValueError(f"Unsupported C module setter action for {plan.owner_path!r}: {action!r}")

    def _lower_module_setter_write_through(self, plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Return a Python-to-native scalar write-through helper."""
        if plan.binding.setter_converts_characters:
            return self._lower_module_setter_character_value(plan)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        return (
            CFunction(
                self._module_setter_name(plan),
                "int",
                parameters=(CParameter("value_obj", "PyObject *"),),
                storage="static",
                body=(
                    CDeclaration(
                        "value",
                        scalar_type.c_spelling,
                    ),
                    self._module_setter_unpack_statement(plan, scalar_type),
                    CExpressionStatement(CodeExpression(f"{self._module_bridge_setter_name(plan)}(value)")),
                    CReturn(CodeExpression("0")),
                ),
            ),
        )

    def _lower_module_setter_reject_replacement(self, _plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Read-only descriptor rejection is emitted by module attribute routing."""
        return ()

    def _lower_module_setter_omit(self, _plan: ModuleVariablePlan) -> tuple[CFunction, ...]:
        """Constants use ordinary Python module-dictionary rebinding."""
        return ()

    def _module_setter_unpack_statement(self, plan, scalar_type) -> CExpressionStatement:
        """Validate and unpack one exact scalar module-variable replacement."""
        return self._scalar_exact_unpack_statement(
            scalar_type,
            "value_obj",
            "value",
            (
                f'PyErr_Format(PyExc_TypeError, "Expected an argument of type '
                f"{scalar_type.python_type_name} for module variable {plan.binding.python_names[0]}. "
                "Received <class '%s'>\", Py_TYPE(value_obj)->tp_name)"
            ),
            "-1",
        )

    def _visit_FunctionPlan(self, plan: FunctionPlan) -> CFunction:
        """Build one CPython wrapper through context, conversion, and call stages.

        The returned function preserves the completed conversion order and
        lifecycle actions; this orchestration does not select those policies.
        """
        # Stage 1: allocate stable local names and separate declarations from executable nodes.
        context = self._function_context(plan)
        argument_declarations, argument_body = self._declarations_first(self._function_argument_nodes(plan, context))
        alias_declarations, alias_body = self._declarations_first(self._derived_alias_preflight_nodes(plan, context))
        # Stage 2: assemble the entrypoint call, completed output projection, and cleanup.
        output_nodes = self._output_nodes(plan, context)
        return CFunction(
            name=self._binding_function_name(plan),
            doc=self._binding_function_doc(plan),
            return_type="PyObject *",
            parameters=self._binding_parameters(plan),
            storage="static",
            body=(
                *self._keyword_declarations(plan),
                *argument_declarations,
                *alias_declarations,
                *self._callback_context_declarations(plan),
                *self._declaration_extent_result_declarations(plan),
                *self._direct_result_declaration(plan, context),
                *self._native_output_declarations(plan, context),
                self._parse_statement(plan, context),
                *argument_body,
                *alias_body,
                *self._native_call_setup_nodes(plan, context),
                *output_nodes,
            ),
        )

    def _function_argument_nodes(self, plan: FunctionPlan, context: _CFunctionContext) -> tuple:
        """Build function argument nodes from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return tuple(
            node for argument in self._binding_conversion_order(plan) for node in self.visit(argument, context=context)
        )

    @staticmethod
    def _declarations_first(nodes: tuple) -> tuple[tuple, tuple]:
        """Build declarations first from the supplied local lowering values; emitted nodes only project completed binding actions."""
        declarations = tuple(node for node in nodes if isinstance(node, CDeclaration))
        body = tuple(node for node in nodes if not isinstance(node, CDeclaration))
        return declarations, body

    def _derived_alias_preflight_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Validate completed writeback authority before entering the bridge."""
        arguments = tuple(argument for argument in plan.arguments if argument.derived_call is not None)
        if len(arguments) < 2:
            return ()
        array = "prik_derived_aliases"
        assignments = []
        for index, argument in enumerate(arguments):
            names = context.arguments[argument.owner_path]
            writable = argument.derived_call.writeback is not DerivedWriteback.NONE
            assignments.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"{array}[{index}].identity = {self._derived_identity_name(names)}")
                    ),
                    CExpressionStatement(CodeExpression(f"{array}[{index}].writable = {1 if writable else 0}")),
                    CExpressionStatement(
                        CodeExpression(
                            f"{array}[{index}].argument_name = {self._c_string_literal(argument.binding.python_name)}"
                        )
                    ),
                )
            )
        return (
            CDeclaration(f"{array}[{len(arguments)}]", "prik_derived_alias_entry"),
            *assignments,
            CIf(
                CodeExpression(f"prik_validate_derived_aliases({array}, {len(arguments)}) < 0"),
                body=(CReturn(CodeExpression("NULL")),),
            ),
        )

    def _binding_conversion_order(self, plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Apply the dependency-safe argument conversion schedule from the plan."""
        arguments = {argument.owner_path: argument for argument in plan.arguments}
        try:
            return tuple(arguments[owner_path] for owner_path in plan.binding.argument_conversion_order)
        except KeyError as error:
            raise ValueError(f"Unknown binding argument conversion owner {error.args[0]!r}") from None

    def _binding_function_doc(self, plan: FunctionPlan) -> tuple[str, ...]:
        """Describe one CPython wrapper: its Python name and the symbol it calls.

        A reader opening the generated binding sees the Python entry point and
        the native symbol it reaches without cross-referencing the plan.
        """
        lines = [
            f"Python callable '{plan.binding.python_name}'.",
            f"Calls the native entrypoint '{plan.entrypoint.symbol_name}'.",
        ]
        if plan.binding.release_gil:
            lines.append("Releases the GIL around the native call.")
        return tuple(lines)

    def _visit_ArgumentTransferPlan(
        self,
        plan: ArgumentTransferPlan,
        *,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Lower one input through its completed optional mode."""
        return self._lower_argument(plan, context)

    def _lower_argument(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Dispatch one completed binding optional mode explicitly."""
        if plan.callback is not None:
            return self._lower_argument_callback(plan, context)
        if plan.native_array_handle is not None:
            return self._lower_argument_native_array_handle(plan, context)
        derived_nodes = self._lower_planned_derived_call_argument(plan, context)
        if derived_nodes is not None:
            return derived_nodes
        mode = plan.binding.optional_mode
        match mode:
            case OptionalMode.REQUIRED:
                return self._lower_argument_required(plan, context)
            case OptionalMode.REQUIRED_DESCRIPTOR:
                return self._lower_argument_required_descriptor(plan, context)
            case OptionalMode.NULLABLE_VALUE:
                return self._lower_argument_nullable_value(plan, context)
            case OptionalMode.DESCRIPTOR:
                return self._lower_argument_descriptor(plan, context)
        raise ValueError(f"Unsupported C argument optional mode for {plan.owner_path!r}: {mode!r}")

    def _lower_argument_callback(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CIf, ...]:
        """Validate an immediate Python callable before any context is retained."""
        names = context.arguments[plan.owner_path]
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CIf(
                CodeExpression(f"!PyCallable_Check({names.object_name})"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_TypeError, "argument {plan.binding.python_name} must be callable")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        )

    def _callback_context_declarations(
        self,
        plan: FunctionPlan,
    ) -> tuple[CDeclaration, ...]:
        """Declare stack storage for each call-scoped callback context."""
        return tuple(
            CDeclaration(
                self._callback_context_name(argument),
                argument.callback.binding.context_type_symbol,
            )
            for argument in plan.arguments
            if argument.callback is not None
        )

    def _callback_context_push_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement, ...]:
        """Retain callables and publish each stack context immediately before entry."""
        return tuple(
            node
            for argument in plan.arguments
            if argument.callback is not None
            for node in (
                CExpressionStatement(
                    CodeExpression(
                        f"{self._callback_context_name(argument)}.callable = "
                        f"{context.arguments[argument.owner_path].object_name}"
                    )
                ),
                CExpressionStatement(CodeExpression(f"{self._callback_context_name(argument)}.module = self")),
                CExpressionStatement(
                    CodeExpression(f"{self._callback_context_name(argument)}.thread_id = PyThread_get_thread_ident()")
                ),
                CExpressionStatement(
                    CodeExpression(
                        f"{self._callback_context_name(argument)}.previous = "
                        f"{argument.callback.binding.context_current_symbol}"
                    )
                ),
                CExpressionStatement(CodeExpression(f"{self._callback_context_name(argument)}.last_result = NULL")),
                CExpressionStatement(
                    CodeExpression(f"Py_INCREF({context.arguments[argument.owner_path].object_name})")
                ),
                CExpressionStatement(CodeExpression("Py_INCREF(self)")),
                CExpressionStatement(
                    CodeExpression(
                        f"{argument.callback.binding.context_current_symbol} = &{self._callback_context_name(argument)}"
                    )
                ),
            )
        )

    def _callback_context_pop_nodes(
        self,
        plan: FunctionPlan,
    ) -> tuple[CExpressionStatement, ...]:
        """Restore nested stacks and release retained objects in reverse order."""
        arguments = tuple(argument for argument in plan.arguments if argument.callback is not None)
        return tuple(
            node
            for argument in reversed(arguments)
            for node in (
                CExpressionStatement(
                    CodeExpression(
                        f"{argument.callback.binding.context_current_symbol} = "
                        f"{self._callback_context_name(argument)}.previous"
                    )
                ),
                CExpressionStatement(
                    CodeExpression(f"Py_XDECREF({self._callback_context_name(argument)}.last_result)")
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({self._callback_context_name(argument)}.module)")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({self._callback_context_name(argument)}.callable)")),
            )
        )

    @staticmethod
    def _callback_context_name(argument: ArgumentTransferPlan) -> str:
        """Return the binding-local callback context name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"{argument.binding.python_name.casefold()}_callback_context"

    def _lower_planned_derived_call_argument(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...] | None:
        """Dispatch only the completed scalar-derived runtime call action."""
        if plan.object_kind is not ObjectKind.DERIVED_TYPE or plan.derived_call is None:
            return None
        if not plan.derived_call.cases:
            raise ValueError(f"Derived argument {plan.owner_path!r} has no completed call matrix")
        return self._derived_argument_nodes(plan, context)

    def _lower_argument_required_descriptor(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CIf, ...]:
        """Require the Python argument while allowing an empty native descriptor state."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        names = context.arguments[plan.owner_path]
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, scalar_type.c_spelling),
            CDeclaration(names.nullable_name, "void *", CodeExpression("NULL")),
            *(
                (
                    CDeclaration(
                        self._descriptor_output_present_name(names),
                        "int",
                        CodeExpression("0"),
                    ),
                )
                if plan.entrypoint.descriptor_output_role is not None
                else ()
            ),
            CIf(
                CodeExpression(f"{names.object_name} != Py_None"),
                body=(
                    self._argument_scalar_unpack_statement(plan, names, scalar_type),
                    CExpressionStatement(CodeExpression(f"{names.nullable_name} = &{names.value_name}")),
                ),
            ),
        )

    def _lower_argument_required(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Dispatch one required argument from its completed Python action."""
        action = plan.binding.python_action
        match action:
            case PythonBarrierAction.SCALAR_VALUE:
                return self._lower_argument_required_scalar_value(plan, context)
            case PythonBarrierAction.SCALAR_STORAGE:
                return self._lower_argument_required_scalar_storage(plan, context)
            case PythonBarrierAction.STRING_STORAGE:
                return self._lower_argument_required_string_storage(plan, context)
            case PythonBarrierAction.STRING_VALUE:
                return self._lower_argument_required_string_value(plan, context)
            case PythonBarrierAction.RAW_ADDRESS:
                return self._lower_argument_required_raw_address(plan, context)
            case PythonBarrierAction.ARRAY_STORAGE:
                return self._lower_argument_required_array_storage(plan, context)
            case PythonBarrierAction.WRAPPER_INSTANCE:
                return self._lower_argument_required_derived(plan, context)
        raise ValueError(f"Unsupported required C argument action for {plan.owner_path!r}: {action!r}")

    # Scalar-derived argument lowering.
    def _lower_argument_required_derived(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Lower through the completed scalar-derived origin table."""
        return self._derived_argument_nodes(plan, context)

    def _derived_argument_nodes(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Extract one runtime carrier without recreating the semantic matrix."""
        if plan.derived is None:
            raise ValueError(f"Derived argument {plan.owner_path!r} has no handoff plan")
        names = context.arguments[plan.owner_path]
        access = self._derived_access_name(names)
        ops = self._derived_ops_name(names)
        identity = self._derived_identity_name(names)
        status = self._derived_status_name(names)
        table = self._derived_call_case_table_name(plan)
        polymorphic_declarations, polymorphic_selection = self._polymorphic_argument_nodes(plan, names)
        type_name = (
            self._polymorphic_type_name_name(names)
            if plan.polymorphic is not None
            else self._c_string_literal(plan.derived.type_name)
        )
        type_symbol = (
            self._polymorphic_type_symbol_name(names)
            if plan.polymorphic is not None
            else self._c_string_literal(plan.derived.backend_symbol)
        )
        capsule_name = (
            self._polymorphic_capsule_name_name(names)
            if plan.polymorphic is not None
            else self._c_string_literal(self._derived_capsule_name(plan.derived.backend_symbol))
        )
        extraction = (
            *polymorphic_selection,
            CDeclaration(
                f"{names.value_name}_extract_status",
                "int",
                CodeExpression(
                    f"prik_extract_derived_argument({names.object_name}, "
                    f"{type_name}, {type_symbol}, {capsule_name}, "
                    f"{self._c_string_literal(plan.binding.python_name)}, {table}, "
                    f"sizeof({table}) / sizeof({table}[0]), &{names.value_name}, &{access}, &{ops})"
                ),
            ),
            CIf(
                CodeExpression(f"{names.value_name}_extract_status < 0"),
                body=(CReturn(CodeExpression("NULL")),),
            ),
        )
        none_body = self._derived_none_argument_nodes(plan, access)
        return (
            CDeclaration(
                names.object_name,
                "PyObject *",
                CodeExpression("Py_None")
                if plan.binding.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
                else None,
            ),
            CDeclaration(names.value_name, "void *", CodeExpression("NULL")),
            CDeclaration(access, "int", CodeExpression("0")),
            CDeclaration(ops, "prik_derived_origin_ops *", CodeExpression("NULL")),
            CDeclaration(identity, "void *", CodeExpression("NULL")),
            CDeclaration(status, "int", CodeExpression("0")),
            *polymorphic_declarations,
            *(
                (
                    CDeclaration(
                        self._descriptor_output_present_name(names),
                        "int",
                        CodeExpression("0"),
                    ),
                )
                if plan.entrypoint.descriptor_output_role is not None
                else ()
            ),
            CIf(CodeExpression(f"{names.object_name} != Py_None"), body=extraction, else_body=none_body),
            CExpressionStatement(CodeExpression(f"{identity} = {ops} != NULL ? (void *){ops} : {names.value_name}")),
        )

    def _polymorphic_argument_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[tuple[CDeclaration, ...], tuple[CExpressionStatement | CIf, ...]]:
        """Select one exact enumerated Python class before capsule extraction."""
        dispatch = plan.polymorphic
        if dispatch is None:
            return (), ()
        code = names.polymorphic_name
        type_name = self._polymorphic_type_name_name(names)
        type_symbol = self._polymorphic_type_symbol_name(names)
        capsule_name = self._polymorphic_capsule_name_name(names)
        expected = f"{code}_expected"
        declarations = (
            CDeclaration(code, "int", CodeExpression("0")),
            CDeclaration(type_name, "const char *", CodeExpression("NULL")),
            CDeclaration(type_symbol, "const char *", CodeExpression("NULL")),
            CDeclaration(capsule_name, "const char *", CodeExpression("NULL")),
            CDeclaration(expected, "PyObject *", CodeExpression("NULL")),
        )
        nodes: list[CExpressionStatement | CIf] = []
        for variant in dispatch.variants:
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f'{expected} = PyObject_GetAttrString(self, "{variant.python_name}")')
                    ),
                    CIf(CodeExpression(f"{expected} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
                    CIf(
                        CodeExpression(f"Py_TYPE({names.object_name}) == (PyTypeObject *){expected}"),
                        body=(
                            CExpressionStatement(CodeExpression(f"{code} = {variant.abi_code}")),
                            CExpressionStatement(
                                CodeExpression(f"{type_name} = {self._c_string_literal(variant.python_name)}")
                            ),
                            CExpressionStatement(
                                CodeExpression(f"{type_symbol} = {self._c_string_literal(variant.backend_symbol)}")
                            ),
                            CExpressionStatement(
                                CodeExpression(
                                    f"{capsule_name} = "
                                    f"{self._c_string_literal(self._derived_capsule_name(variant.backend_symbol))}"
                                )
                            ),
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({expected})")),
                )
            )
        accepted = ", ".join(variant.python_name for variant in dispatch.variants)
        nodes.append(
            CIf(
                CodeExpression(f"{code} == 0"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_Format(PyExc_TypeError, "argument {plan.binding.python_name} requires exact '
                            f'polymorphic wrapper type: {accepted}")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            )
        )
        return declarations, tuple(nodes)

    @staticmethod
    def _polymorphic_type_name_name(names: _CArgumentNames) -> str:
        """Return the binding-local polymorphic type name name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.polymorphic_name}_type_name"

    @staticmethod
    def _polymorphic_type_symbol_name(names: _CArgumentNames) -> str:
        """Return the binding-local polymorphic type symbol name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.polymorphic_name}_type_symbol"

    @staticmethod
    def _polymorphic_capsule_name_name(names: _CArgumentNames) -> str:
        """Return the binding-local polymorphic capsule name name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.polymorphic_name}_capsule_name"

    def _derived_none_argument_nodes(self, plan: ArgumentTransferPlan, access_name: str) -> tuple:
        """Map Python absence without fabricating an incompatible native actual."""
        if plan.binding.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}:
            return ()
        if plan.binding.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR:
            access = {
                DerivedDummyCategory.ALLOCATABLE: 3,
                DerivedDummyCategory.ALLOCATABLE_TARGET: 3,
                DerivedDummyCategory.POINTER: 4,
            }.get(plan.derived_call.dummy_category)
            if access is None:
                raise ValueError(f"Derived descriptor {plan.owner_path!r} has no empty-holder access")
            return (CExpressionStatement(CodeExpression(f"{access_name} = {access}")),)
        return (
            CExpressionStatement(
                CodeExpression(
                    f'PyErr_Format(PyExc_TypeError, "argument {plan.binding.python_name} requires a derived wrapper")'
                )
            ),
            CReturn(CodeExpression("NULL")),
        )

    @staticmethod
    def _derived_access_name(names: _CArgumentNames) -> str:
        """Return the binding-local derived access name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.value_name}_derived_access"

    @staticmethod
    def _derived_ops_name(names: _CArgumentNames) -> str:
        """Return the binding-local derived ops name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.value_name}_derived_ops"

    @staticmethod
    def _derived_identity_name(names: _CArgumentNames) -> str:
        """Return the binding-local derived identity name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.value_name}_derived_identity"

    @staticmethod
    def _derived_status_name(names: _CArgumentNames) -> str:
        """Return the binding-local derived status name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.value_name}_derived_status"

    # Scalar argument lowering.
    def _lower_argument_required_scalar_value(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Return declarations and conversion statements for one scalar value."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        if scalar_type.numpy_type_macro is None:
            raise ValueError(f"Unsupported scalar input type {plan.semantic_type_name!r}")
        names = context.arguments[plan.owner_path]
        storage_type = plan.native_storage_c_type or scalar_type.c_spelling
        if storage_type != scalar_type.c_spelling:
            converted_name = f"{names.value_name}_converted"
            return (
                CDeclaration(names.object_name, "PyObject *"),
                CDeclaration(converted_name, scalar_type.c_spelling),
                CDeclaration(names.value_name, storage_type),
                self._scalar_exact_unpack_statement(
                    scalar_type,
                    names.object_name,
                    converted_name,
                    (
                        f'PyErr_Format(PyExc_TypeError, "Expected an argument of type '
                        f"{scalar_type.python_type_name} for argument {plan.binding.python_name}. "
                        f"Received <class '%s'>\", Py_TYPE({names.object_name})->tp_name)"
                    ),
                    "NULL",
                ),
                CExpressionStatement(CodeExpression(f"{names.value_name} = ({storage_type}){converted_name}")),
            )
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, scalar_type.c_spelling),
            self._scalar_exact_unpack_statement(
                scalar_type,
                names.object_name,
                names.value_name,
                (
                    f'PyErr_Format(PyExc_TypeError, "Expected an argument of type '
                    f"{scalar_type.python_type_name} for argument {plan.binding.python_name}. "
                    f"Received <class '%s'>\", Py_TYPE({names.object_name})->tp_name)"
                ),
                "NULL",
            ),
        )

    # String argument lowering.
    def _lower_argument_required_string_value(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Dispatch one completed string input-storage action."""
        action = plan.binding.codegen_action
        if action is CodegenAction.CALL_LOCAL_INPUT:
            return self._lower_argument_required_string_input(plan, context)
        if action is CodegenAction.COPY_IN_OUT:
            return self._lower_argument_required_string_replacement(plan, context)
        raise ValueError(f"Unsupported required C string action for {plan.owner_path!r}: {action!r}")

    def _lower_argument_required_string_input(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Validate and borrow one read-only UTF-8 payload for the call."""
        names = context.arguments[plan.owner_path]
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, "const char *", CodeExpression("NULL")),
            CDeclaration(names.length_name, "Py_ssize_t", CodeExpression("0")),
            *self._required_string_validation_nodes(plan, names, names.value_name),
        )

    def _lower_argument_required_string_replacement(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Allocate and populate one mutable string call buffer."""
        names = context.arguments[plan.owner_path]
        source_name = f"{names.value_name}_source"
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(source_name, "const char *", CodeExpression("NULL")),
            CDeclaration(names.value_name, "char *", CodeExpression("NULL")),
            CDeclaration(names.length_name, "Py_ssize_t", CodeExpression("0")),
            *self._required_string_validation_nodes(plan, names, source_name),
            *self._string_replacement_allocation_nodes(plan, names, source_name),
        )

    def _string_replacement_allocation_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        source_name: str,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Allocate and copy one validated mutable string payload."""
        return (
            CExpressionStatement(
                CodeExpression(f"{names.value_name} = (char *)prik_malloc((size_t){names.length_name} + 1)")
            ),
            CIf(
                CodeExpression(f"{names.value_name} == NULL"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_SetString(PyExc_MemoryError, "Unable to allocate mutable string buffer '
                            f'for argument {plan.binding.python_name}.")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(
                CodeExpression(f"memcpy({names.value_name}, {source_name}, (size_t){names.length_name})")
            ),
            CExpressionStatement(CodeExpression(f"{names.value_name}[{names.length_name}] = '\\0'")),
        )

    def _required_string_validation_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        payload_name: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Return shared required-string type, UTF-8, NUL, and length checks."""
        nodes = [
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyUnicode_Check({names.object_name})) {{ "
                    f'PyErr_Format(PyExc_TypeError, "Expected an argument of type str for argument '
                    f"{plan.binding.python_name}. Received <class '%s'>\", "
                    f"Py_TYPE({names.object_name})->tp_name); return NULL; }}"
                )
            ),
            CExpressionStatement(
                CodeExpression(f"{payload_name} = PyUnicode_AsUTF8AndSize({names.object_name}, &{names.length_name})")
            ),
            CExpressionStatement(CodeExpression(f"if ({payload_name} == NULL) return NULL")),
            *(
                ()
                if plan.character_allows_embedded_nul
                else (
                    CExpressionStatement(
                        CodeExpression(
                            f"if ((Py_ssize_t)strlen({payload_name}) != {names.length_name}) {{ "
                            f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} cannot contain '
                            'embedded NUL"); return NULL; }'
                        )
                    ),
                )
            ),
        ]
        fixed_length = plan.character_length
        if fixed_length is not None:
            nodes.append(
                CExpressionStatement(
                    CodeExpression(
                        f"if ({names.length_name} != {fixed_length}) {{ "
                        f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must encode to '
                        f'exactly {fixed_length} bytes"); return NULL; }}'
                    )
                )
            )
        return tuple(nodes)

    # Ordinary-array argument lowering.
    def _lower_argument_required_array_storage(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CFor, ...]:
        """Validate and borrow one completed ordinary NumPy array buffer."""
        if plan.native_array_actual is not None:
            return self._lower_argument_required_array_actual(plan, context)
        array_plan = plan.array
        if array_plan is None:
            raise ValueError(f"Array argument {plan.owner_path!r} is missing its handoff")
        names = context.arguments[plan.owner_path]
        array = f"(PyArrayObject *){names.object_name}"
        nodes = [
            *self._ordinary_array_argument_declarations(plan, names),
            self._array_validation_statement(plan, names),
            *self._array_shape_checks(plan, context, array),
        ]
        nodes.extend(self._array_extraction_nodes(plan, names, array))
        return tuple(nodes)

    def _ordinary_array_argument_declarations(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CDeclaration, ...]:
        """Declare backend-local storage named by one ordinary-array handoff."""
        array = plan.array
        if array is None:
            raise ValueError(f"Array argument {plan.owner_path!r} is missing its handoff")
        declarations = [
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, "void *", CodeExpression("NULL")),
        ]
        if plan.transformations:
            declarations.append(
                CDeclaration(
                    self._array_transformation_temp_name(names),
                    "PyObject *",
                    CodeExpression("NULL"),
                )
            )
        declarations.extend(CDeclaration(name, "int64_t", CodeExpression("0")) for name in names.extent_names)
        if array.upper_bound_roles:
            declarations.extend(CDeclaration(name, "int64_t", CodeExpression("0")) for name in names.upper_bound_names)
        if array.stride_roles:
            declarations.extend(CDeclaration(name, "int64_t", CodeExpression("1")) for name in names.stride_names)
        declarations.extend(self._array_dense_actual_declarations(array, names))
        if array.runtime_rank_role is not None:
            declarations.append(CDeclaration(names.runtime_rank_name, "int64_t", CodeExpression("0")))
        if array.itemsize_role is not None:
            declarations.append(CDeclaration(names.itemsize_name, "int64_t", CodeExpression("0")))
        return tuple(declarations)

    @staticmethod
    def _array_dense_actual_declarations(
        array: ArrayHandoffPlan,
        names: _CArgumentNames,
    ) -> tuple[CDeclaration, ...]:
        """Declare the planned dense-actual selector when its role exists."""
        if array.dense_actual_role is None:
            return ()
        return (CDeclaration(names.dense_actual_name, "int", CodeExpression("0")),)

    # Native-handle actuals reuse the ordinary array-buffer ABI.
    def _lower_argument_required_array_actual(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Validate ndarrays directly and reserve runtime packing for native handles."""
        actual = plan.native_array_actual
        array = plan.array
        if actual is None or array is None:
            raise ValueError(f"Array actual {plan.owner_path!r} is missing its completed policy")
        names = context.arguments[plan.owner_path]
        prefix = names.value_name
        array_object = f"(PyArrayObject *){names.object_name}"
        direct_nodes = (
            self._array_validation_statement(plan, names),
            *self._array_shape_checks(plan, context, array_object),
            *self._array_extraction_nodes(plan, names, array_object),
        )
        handle_nodes = (
            CDeclaration(f"{prefix}_shape", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_actual", "prik_array_actual"),
            *self._native_array_actual_call_nodes(plan, context, names),
            *self._native_array_actual_unpack_nodes(plan, names),
        )
        return (
            *self._ordinary_array_argument_declarations(plan, names),
            CIf(
                CodeExpression(f"PyArray_Check({names.object_name})"),
                body=direct_nodes,
                else_body=handle_nodes,
            ),
        )

    def _native_array_actual_call_nodes(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Call the shared normal-array native-handle slow path."""
        actual = plan.native_array_actual
        if actual is None:
            return ()
        prefix = names.value_name
        layout = "NULL" if actual.order is None else f'"{actual.order}"'
        nodes = [
            *self._native_array_actual_shape_object_nodes(plan, names),
            *self._native_array_actual_shape_nodes(plan, context, names),
            CExpressionStatement(
                CodeExpression(
                    f'if (prik_array_actual_unpack({names.object_name}, "{actual.dtype}", '
                    f"{self._native_array_actual_expected_rank(actual)}, {prefix}_shape, {layout}, "
                    f"{int(actual.writable)}, {int(actual.require_native_byte_order)}, {int(actual.require_aligned)}, "
                    f"{int(plan.array.runtime_rank_role is not None)}, "
                    f"{int(plan.array.itemsize_role is not None)}, {int(bool(plan.array.stride_roles))}, "
                    f"{int(actual.require_contiguous)}, {int(actual.flatten_storage)}, "
                    f"{self._native_array_actual_flat_axis(actual)}, &{prefix}_actual) < 0) {{ "
                    f"Py_DECREF({prefix}_shape); return NULL; }}"
                )
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_shape)")),
        ]
        return tuple(nodes)

    def _native_array_actual_shape_object_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Create the expected-shape object consumed by the runtime helper."""
        actual = plan.native_array_actual
        if actual is None:
            return ()
        prefix = names.value_name
        return (
            CExpressionStatement(CodeExpression(f"{prefix}_shape = PyTuple_New({actual.rank})")),
            CExpressionStatement(CodeExpression(f"if ({prefix}_shape == NULL) return NULL")),
        )

    @staticmethod
    def _native_array_actual_expected_rank(actual: NativeArrayActualPlan) -> int:
        """Return the runtime-helper rank selector selected by completed policy."""
        return actual.rank

    @staticmethod
    def _native_array_actual_flat_axis(actual: NativeArrayActualPlan) -> int:
        """Return the flattened contract axis marker consumed by the runtime helper."""
        return -1 if actual.flat_axis is None else actual.flat_axis

    def _native_array_actual_shape_nodes(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Build the planned expected-shape tuple for runtime validation."""
        actual = plan.native_array_actual
        array = plan.array
        if actual is None or array is None:
            return ()
        prefix = names.value_name
        nodes = []
        for axis, expression in enumerate(actual.shape):
            if (
                expression in {":", "::Strided", "Flat"}
                or (actual.flatten_storage and axis == actual.flat_axis)
                or array.extent_evaluation[axis] == "bridge"
            ):
                nodes.append(CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")))
                item = "Py_None"
            else:
                expected = self._array_extent_expression(array, axis, expression, context)
                item = f"PyLong_FromLongLong((long long)({expected}))"
            nodes.append(CExpressionStatement(CodeExpression(f"PyTuple_SET_ITEM({prefix}_shape, {axis}, {item})")))
            nodes.append(
                CExpressionStatement(
                    CodeExpression(
                        f"if (PyTuple_GET_ITEM({prefix}_shape, {axis}) == NULL) {{ "
                        f"Py_DECREF({prefix}_shape); return NULL; }}"
                    )
                )
            )
        return tuple(nodes)

    def _native_array_actual_unpack_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Assign planned ABI roles from the shared native-handle result."""
        prefix = names.value_name
        nodes = [
            CExpressionStatement(CodeExpression(f"{names.value_name} = {prefix}_actual.data")),
        ]
        array = plan.array
        if array is None:
            raise ValueError(f"Array actual {plan.owner_path!r} is missing its handoff")
        if array.runtime_rank_role is not None:
            nodes.append(CExpressionStatement(CodeExpression(f"{names.runtime_rank_name} = {prefix}_actual.rank")))
        if array.itemsize_role is not None:
            nodes.append(CExpressionStatement(CodeExpression(f"{names.itemsize_name} = {prefix}_actual.itemsize")))
        nodes.extend(
            CExpressionStatement(CodeExpression(f"{field_name} = {prefix}_actual.extents[{axis}]"))
            for axis, field_name in enumerate(names.extent_names)
        )
        nodes.extend(
            CExpressionStatement(CodeExpression(f"{field_name} = {prefix}_actual.upper_bounds[{axis}]"))
            for axis, field_name in enumerate(names.upper_bound_names[: len(array.upper_bound_roles)])
        )
        nodes.extend(
            CExpressionStatement(CodeExpression(f"{field_name} = {prefix}_actual.strides[{axis}]"))
            for axis, field_name in enumerate(names.stride_names[: len(array.stride_roles)])
        )
        return tuple(nodes)

    def _array_validation_statement(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> CExpressionStatement:
        """Call compact validation with selectors from the completed plan."""
        handoff = plan.array
        if handoff is None:
            raise ValueError(f"Array argument {plan.owner_path!r} is missing its handoff")
        numpy_type, python_type = self._array_dtype_selectors(plan, handoff)
        minimum_rank, maximum_rank = self._array_rank_bounds(handoff)
        layout = self._array_layout_selector(handoff)
        return CExpressionStatement(
            CodeExpression(
                f"if (prik_array_validate({names.object_name}, {numpy_type}, {minimum_rank}, {maximum_rank}, "
                f'{layout}, {int(handoff.contiguous is True)}, {int(plan.binding.writable)}, "{python_type}", '
                f'"{plan.binding.python_name}") < 0) return NULL'
            )
        )

    @staticmethod
    def _array_dtype_selectors(
        plan: ArgumentTransferPlan,
        handoff: ArrayHandoffPlan,
    ) -> tuple[str, str]:
        """Return compact helper dtype selectors from completed array facts."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "NPY_STRING", f"numpy.bytes_[{handoff.itemsize}]"
        return CBindingGenerator._numeric_array_dtype_selectors(plan)

    @staticmethod
    def _numeric_array_dtype_selectors(plan: ArgumentTransferPlan) -> tuple[str, str]:
        """Return canonical or policy-selected exact native NumPy storage."""
        if plan.binding.native_array_element_c_type is not None:
            native = NativeCArrayStorageRegistry.type_for(
                plan.binding.native_array_element_c_type,
                plan.semantic_type_name,
            )
            return native.numpy_type_macro, native.python_type_name
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        if scalar_type.numpy_type_macro is None or scalar_type.python_type_name is None:
            raise ValueError(f"Unsupported array element type {plan.semantic_type_name!r}")
        return scalar_type.numpy_type_macro, scalar_type.python_type_name

    @staticmethod
    def _array_rank_bounds(handoff: ArrayHandoffPlan) -> tuple[int, int]:
        """Return inclusive runtime-rank bounds selected by array policy."""
        if handoff.rank is None:
            return 1, 15
        if handoff.flatten_python_storage:
            return handoff.rank, 15
        return handoff.rank, handoff.rank

    @staticmethod
    def _array_layout_selector(handoff: ArrayHandoffPlan) -> str:
        """Return the compact helper layout selector chosen by the plan."""
        if handoff.contiguous is False:
            return "PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F"
        if handoff.order == "ORDER_C":
            return "PRIK_ARRAY_LAYOUT_C_CONTIGUOUS"
        if handoff.order == "ORDER_F" or (handoff.rank is not None and handoff.rank > 1):
            return "PRIK_ARRAY_LAYOUT_F_CONTIGUOUS"
        return "PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS"

    def _array_shape_checks(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
        array: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Validate every concrete declared extent against completed scalar roles."""
        handoff = plan.array
        if handoff is None or handoff.rank is None:
            return ()
        checks = []
        runtime_markers = {":", "::Strided", "Flat"}
        for axis, expression in enumerate(handoff.shape):
            if expression in runtime_markers:
                continue
            if handoff.extent_evaluation[axis] == "bridge":
                continue
            expected = self._array_extent_expression(handoff, axis, expression, context)
            actual_axis = self._array_actual_axis_expression(handoff, array, axis)
            checks.append(
                CExpressionStatement(
                    CodeExpression(
                        f"if (PyArray_DIM({array}, {actual_axis}) != (npy_intp)({expected})) {{ "
                        f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} has incompatible '
                        f'shape at axis {axis}"); return NULL; }}'
                    )
                )
            )
        return tuple(checks)

    @staticmethod
    def _array_actual_axis_expression(handoff, array: str, axis: int) -> str:
        """Map one contract axis to the runtime ndarray axis selected by the plan."""
        if not handoff.flatten_python_storage or handoff.flat_axis is None:
            return str(axis)
        if handoff.flat_axis == 0 and axis > 0:
            suffix_count = handoff.rank - 1
            suffix_offset = axis - 1
            return f"(PyArray_NDIM({array}) - {suffix_count} + {suffix_offset})"
        return str(axis)

    def _array_extent_expression(
        self,
        handoff,
        axis: int,
        expression: str,
        context: _CFunctionContext,
    ) -> str:
        """Lower one validated extent expression through its planned role references."""
        substitutions = {}
        references = zip(
            handoff.extent_reference_tokens[axis],
            handoff.extent_reference_roles[axis],
            strict=True,
        )
        for token, role in references:
            try:
                value_name = context.role_values[role]
            except KeyError:
                raise ValueError(f"Array extent role {role!r} has no binding value") from None
            substitutions[token] = value_name
        return render_declaration_extent(expression, substitutions, target="c")

    def _array_extraction_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement | CIf | CFor, ...]:
        """Extract only the ABI fields named by the editable handoff plan."""
        handoff = plan.array
        if handoff is None:
            return ()
        nodes = [CExpressionStatement(CodeExpression(f"{names.value_name} = PyArray_DATA({array})"))]
        if handoff.runtime_rank_role is not None:
            nodes.append(
                CExpressionStatement(CodeExpression(f"{names.runtime_rank_name} = (int64_t)PyArray_NDIM({array})"))
            )
        if handoff.itemsize_role is not None:
            nodes.append(
                CExpressionStatement(CodeExpression(f"{names.itemsize_name} = (int64_t)PyArray_ITEMSIZE({array})"))
            )
            # An assumed width accepts whatever the caller's array declares; only
            # a stated width is checked against it.
            if handoff.itemsize is not None:
                nodes.append(
                    CExpressionStatement(
                        CodeExpression(
                            f"if ({names.itemsize_name} != {handoff.itemsize}) {{ PyErr_SetString(PyExc_TypeError, "
                            f'"Argument {plan.binding.python_name} must have NumPy bytes dtype itemsize '
                            f'{handoff.itemsize}"); return NULL; }}'
                        )
                    )
                )
        if handoff.flatten_python_storage:
            nodes.extend(self._flat_array_extraction_nodes(handoff, names, array))
            return tuple(nodes)
        nodes.extend(self._array_dense_actual_extraction_nodes(handoff, names, array))
        active_rank = 15 if handoff.rank is None else handoff.rank
        for axis in range(active_rank):
            guard = f"if (PyArray_NDIM({array}) > {axis}) " if handoff.rank is None else ""
            nodes.append(
                CExpressionStatement(
                    CodeExpression(f"{guard}{names.extent_names[axis]} = (int64_t)PyArray_DIM({array}, {axis})")
                )
            )
        nodes.extend(self._array_strided_extraction_dispatch_nodes(handoff, names, array))
        return tuple(nodes)

    @staticmethod
    def _array_dense_actual_extraction_nodes(
        handoff: ArrayHandoffPlan,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Extract the runtime dense-actual selector named by the plan."""
        if handoff.dense_actual_role is None:
            return ()
        return (CExpressionStatement(CodeExpression(f"{names.dense_actual_name} = PyArray_IS_F_CONTIGUOUS({array})")),)

    def _array_strided_extraction_dispatch_nodes(
        self,
        handoff: ArrayHandoffPlan,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Dispatch general stride extraction only when the selected actual needs it."""
        if handoff.contiguous is not False:
            return ()
        strided_nodes = self._strided_array_extraction_nodes(handoff.rank, names, array)
        if handoff.dense_actual_role is None:
            return strided_nodes
        return (CIf(CodeExpression(f"!{names.dense_actual_name}"), body=strided_nodes),)

    def _flat_array_extraction_nodes(
        self,
        handoff,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement | CFor, ...]:
        """Compute native extents for a contiguous Python array with one flat edge."""
        if handoff.rank is None or handoff.flat_axis is None:
            raise ValueError("Flat array extraction requires a completed concrete flat axis")
        if handoff.flat_axis == 0:
            return self._leading_flat_array_extraction_nodes(handoff, names, array)
        return self._final_flat_array_extraction_nodes(handoff, names, array)

    def _final_flat_array_extraction_nodes(
        self,
        handoff,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement | CFor, ...]:
        """Keep prefix extents and flatten all runtime axes at the final flat edge."""
        flat_axis = handoff.flat_axis
        nodes: list[CExpressionStatement | CFor] = [
            *(
                CExpressionStatement(
                    CodeExpression(f"{names.extent_names[axis]} = (int64_t)PyArray_DIM({array}, {axis})")
                )
                for axis in range(flat_axis)
            ),
            CExpressionStatement(CodeExpression(f"{names.extent_names[flat_axis]} = 1")),
            CFor(
                f"int axis = {flat_axis}",
                CodeExpression(f"axis < PyArray_NDIM({array})"),
                CodeExpression("++axis"),
                body=(
                    CExpressionStatement(
                        CodeExpression(f"{names.extent_names[flat_axis]} *= (int64_t)PyArray_DIM({array}, axis)")
                    ),
                ),
            ),
        ]
        return tuple(nodes)

    def _leading_flat_array_extraction_nodes(
        self,
        handoff,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement | CFor, ...]:
        """Flatten leading runtime axes and keep suffix extents at the Python edge."""
        suffix_count = handoff.rank - 1
        nodes: list[CExpressionStatement | CFor] = [
            CExpressionStatement(CodeExpression(f"{names.extent_names[0]} = 1")),
            CFor(
                "int axis = 0",
                CodeExpression(f"axis < PyArray_NDIM({array}) - {suffix_count}"),
                CodeExpression("++axis"),
                body=(
                    CExpressionStatement(
                        CodeExpression(f"{names.extent_names[0]} *= (int64_t)PyArray_DIM({array}, axis)")
                    ),
                ),
            ),
        ]
        nodes.extend(
            CExpressionStatement(
                CodeExpression(
                    f"{names.extent_names[axis]} = (int64_t)PyArray_DIM({array}, "
                    f"PyArray_NDIM({array}) - {suffix_count} + {axis - 1})"
                )
            )
            for axis in range(1, handoff.rank)
        )
        return tuple(nodes)

    def _strided_array_extraction_nodes(
        self,
        rank: int | None,
        names: _CArgumentNames,
        array: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Compute bridge base extents, slice bounds, and relative strides."""
        if rank is None:
            raise ValueError("Assumed-rank strided arrays require a separate completed lane")
        nodes = []
        base_product = "1"
        for axis in range(rank):
            absolute_stride = f"(PyArray_STRIDE({array}, {axis}) / PyArray_ITEMSIZE({array}))"
            nodes.append(
                CExpressionStatement(
                    CodeExpression(
                        f"{names.stride_names[axis]} = PyArray_SIZE({array}) == 0 ? 1 : "
                        f"{absolute_stride} / ({base_product})"
                    )
                )
            )
            nodes.append(
                CExpressionStatement(
                    CodeExpression(
                        f"{names.upper_bound_names[axis]} = {names.extent_names[axis]} == 0 ? -1 : "
                        f"({names.extent_names[axis]} - 1) * {names.stride_names[axis]}"
                    )
                )
            )
            if axis + 1 < rank:
                next_stride = f"(PyArray_STRIDE({array}, {axis + 1}) / PyArray_ITEMSIZE({array}))"
                nodes.append(
                    CExpressionStatement(
                        CodeExpression(
                            f"{names.extent_names[axis]} = {next_stride} / ({base_product}); "
                            f"if ({names.extent_names[axis]} < 1) {names.extent_names[axis]} = 1"
                        )
                    )
                )
                base_product = f"({base_product}) * {names.extent_names[axis]}"
            else:
                nodes.append(
                    CExpressionStatement(
                        CodeExpression(f"{names.extent_names[axis]} = {names.upper_bound_names[axis]} + 1")
                    )
                )
        return tuple(nodes)

    # Scalar storage and address lowering.
    def _lower_argument_required_scalar_storage(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Validate and borrow one rank-zero NumPy scalar data address."""
        numpy_type, expected = self._numeric_array_dtype_selectors(plan)
        names = context.arguments[plan.owner_path]
        array = f"(PyArrayObject *){names.object_name}"
        nodes = [
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, "void *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_Check({names.object_name}) || PyArray_TYPE({array}) != "
                    f"{numpy_type} || PyArray_NDIM({array}) != 0) {{ "
                    f'PyErr_Format(PyExc_TypeError, "Expected a rank-zero numpy.ndarray of type '
                    f"{expected} for argument {plan.binding.python_name}. Received <class '%s'>\", "
                    f"Py_TYPE({names.object_name})->tp_name); return NULL; }}"
                )
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_ISNOTSWAPPED({array})) {{ "
                    f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must use native '
                    'byte order"); return NULL; }'
                )
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_ISALIGNED({array})) {{ "
                    f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must be aligned"); '
                    "return NULL; }"
                )
            ),
        ]
        if plan.binding.writable:
            nodes.append(
                CExpressionStatement(
                    CodeExpression(
                        f"if (!PyArray_ISWRITEABLE({array})) {{ "
                        f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must be writeable"); '
                        "return NULL; }"
                    )
                )
            )
        nodes.append(CExpressionStatement(CodeExpression(f"{names.value_name} = PyArray_DATA({array})")))
        return tuple(nodes)

    # String storage lowering.
    def _lower_argument_required_string_storage(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Validate and borrow one rank-zero NumPy bytes buffer.

        A declared capacity is checked against the array's itemsize.  An
        assumed capacity accepts any ``S`` width, because the caller's buffer
        states its own size and the binding passes that storage untouched.
        """
        if plan.character_length is not None and plan.character_length <= 0:
            raise ValueError(f"String storage {plan.owner_path!r} has a non-positive length")
        names = context.arguments[plan.owner_path]
        array = f"(PyArrayObject *){names.object_name}"
        length = plan.character_length
        expected = f"S{length}" if length is not None else "S"
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, "void *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_Check({names.object_name}) || PyArray_TYPE({array}) != NPY_STRING || "
                    f"PyArray_NDIM({array}) != 0) {{ "
                    f'PyErr_Format(PyExc_TypeError, "Expected a rank-zero numpy.ndarray with dtype {expected} '
                    f"for argument {plan.binding.python_name}. Received <class '%s'>\", "
                    f"Py_TYPE({names.object_name})->tp_name); return NULL; }}"
                )
            ),
            *(
                (
                    CExpressionStatement(
                        CodeExpression(
                            f"if (PyArray_ITEMSIZE({array}) != {length}) {{ "
                            f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must use itemsize '
                            f'{length}"); return NULL; }}'
                        )
                    ),
                )
                if length is not None
                else ()
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_ISNOTSWAPPED({array})) {{ "
                    f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must use native '
                    'byte order"); return NULL; }'
                )
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_ISALIGNED({array})) {{ "
                    f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must be aligned"); '
                    "return NULL; }"
                )
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyArray_ISWRITEABLE({array})) {{ "
                    f'PyErr_SetString(PyExc_TypeError, "Argument {plan.binding.python_name} must be writeable"); '
                    "return NULL; }"
                )
            ),
            CExpressionStatement(CodeExpression(f"{names.value_name} = PyArray_DATA({array})")),
        )

    def _lower_argument_required_raw_address(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Convert one Python integer into a caller-owned raw address."""
        names = context.arguments[plan.owner_path]
        return (
            CDeclaration(names.object_name, "PyObject *"),
            CDeclaration(names.value_name, "void *", CodeExpression("NULL")),
            CExpressionStatement(
                CodeExpression(
                    f"if (!PyLong_Check({names.object_name})) {{ "
                    f'PyErr_Format(PyExc_TypeError, "Expected an integer raw address for argument '
                    f"{plan.binding.python_name}. Received <class '%s'>\", "
                    f"Py_TYPE({names.object_name})->tp_name); return NULL; }}"
                )
            ),
            CExpressionStatement(CodeExpression(f"{names.value_name} = PyLong_AsVoidPtr({names.object_name})")),
            CExpressionStatement(CodeExpression(f"if ({names.value_name} == NULL && PyErr_Occurred()) return NULL")),
        )

    # Native-array-handle argument lowering.
    def _lower_argument_native_array_handle(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Dispatch one descriptor handle from its planned standard ABI."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        if handle.handoff.abi is NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL:
            return self._lower_argument_native_array_facts(plan, context)
        if handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR:
            return self._lower_argument_native_array_direct(plan, context)
        raise ValueError(f"Unsupported C native descriptor ABI for {plan.owner_path!r}: {handle.handoff.abi!r}")

    def _lower_argument_native_array_facts(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Establish call-local CFI storage from validated descriptor facts."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native descriptor {plan.owner_path!r} has no concrete rank")
        names = context.arguments[plan.owner_path]
        rank = handle.array.rank
        prefix = names.value_name
        nodes: list[CDeclaration | CExpressionStatement | CIf] = [
            self._native_descriptor_object_declaration(plan, names),
            CDeclaration(f"{prefix}_storage", f"CFI_CDESC_T({rank})"),
            CDeclaration(names.value_name, "CFI_cdesc_t *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_base_addr", "void *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_elem_len", "size_t", CodeExpression("0")),
            CDeclaration(f"{prefix}_descriptor_rank", "CFI_rank_t", CodeExpression("0")),
            CDeclaration(f"{prefix}_cfi_extents[{rank}]", "CFI_index_t"),
            *(
                CDeclaration(f"{prefix}_{label}_{axis}", "CFI_index_t", CodeExpression("0"))
                for axis in range(rank)
                for label in ("lower_bound", "descriptor_extent", "stride_multiplier")
            ),
            CDeclaration(f"{prefix}_establish_status", "int", CodeExpression("CFI_SUCCESS")),
            *self._native_descriptor_helper_declarations(prefix),
            *(self._native_descriptor_presence_declarations(plan, names)),
        ]
        nodes.extend(
            self._native_descriptor_helper_call_nodes(
                plan,
                context,
                names,
                "_native_array_descriptor_argument_for_binding_positional",
            )
        )
        nodes.extend(self._native_descriptor_presence_unpack_nodes(plan, names, 3 + 3 * rank))
        nodes.extend(self._native_descriptor_fact_unpack_nodes(plan, names))
        nodes.append(CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_packed)")))
        return tuple(nodes)

    def _lower_argument_native_array_direct(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Borrow one persistent runtime-owned standard descriptor pointer."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        names = context.arguments[plan.owner_path]
        prefix = names.value_name
        binder_definition = (
            self._default_native_array_binder_def_name(plan)
            if handle.default_handle.construction is NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR
            else None
        )
        nodes: list[CDeclaration | CExpressionStatement | CIf] = [
            self._native_descriptor_object_declaration(plan, names),
            CDeclaration(names.value_name, "CFI_cdesc_t *", CodeExpression("NULL")),
            CDeclaration(
                f"{names.value_name}_native_handle",
                "prik_native_array_handle *",
                CodeExpression("NULL"),
            ),
            *self._native_descriptor_helper_declarations(
                prefix,
                include_default_binder=binder_definition is not None,
            ),
            *(self._native_descriptor_presence_declarations(plan, names)),
        ]
        nodes.extend(
            self._native_descriptor_helper_call_nodes(
                plan,
                context,
                names,
                "_native_array_descriptor_handoff_for_binding_positional",
                default_binder_definition=binder_definition,
            )
        )
        nodes.extend(self._native_descriptor_presence_unpack_nodes(plan, names, 1))
        nodes.extend(self._native_descriptor_pointer_unpack_nodes(plan, names))
        nodes.append(CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_packed)")))
        return tuple(nodes)

    def _native_descriptor_object_declaration(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> CDeclaration:
        """Declare a required object or the optional-absence default."""
        initializer = CodeExpression("Py_None") if plan.binding.optional_mode is OptionalMode.DESCRIPTOR else None
        return CDeclaration(names.object_name, "PyObject *", initializer)

    def _native_descriptor_helper_declarations(
        self,
        prefix: str,
        *,
        include_default_binder: bool = False,
    ) -> tuple[CDeclaration, ...]:
        """Return binding-local Python objects used by one runtime helper call."""
        declarations = tuple(
            CDeclaration(f"{prefix}_{suffix}", "PyObject *", CodeExpression("NULL"))
            for suffix in ("runtime", "helper", "shape", "packed", "item")
        )
        if include_default_binder:
            return (*declarations, CDeclaration(f"{prefix}_default_binder", "PyObject *", CodeExpression("NULL")))
        return declarations

    def _native_descriptor_presence_declarations(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CDeclaration, ...]:
        """Declare a dedicated optional-presence token only when planned."""
        if plan.binding.optional_mode is not OptionalMode.DESCRIPTOR:
            return ()
        return (CDeclaration(names.present_name, "void *", CodeExpression("NULL")),)

    def _native_descriptor_helper_call_nodes(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
        names: _CArgumentNames,
        helper_name: str,
        default_binder_definition: str | None = None,
    ) -> tuple[CExpressionStatement, ...]:
        """Call one planned native-descriptor runtime packer."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            return ()
        prefix = names.value_name
        dtype = self._native_array_dtype(plan)
        dtype_format = "O" if dtype is None else "s"
        dtype_argument = "Py_None" if dtype is None else f'"{dtype}"'
        nodes: list[CExpressionStatement] = [
            CExpressionStatement(CodeExpression(f'{prefix}_runtime = PyImport_ImportModule("prik.runtime.handles")')),
            CExpressionStatement(CodeExpression(f"if ({prefix}_runtime == NULL) return NULL")),
            CExpressionStatement(
                CodeExpression(f'{prefix}_helper = PyObject_GetAttrString({prefix}_runtime, "{helper_name}")')
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_runtime)")),
            CExpressionStatement(CodeExpression(f"if ({prefix}_helper == NULL) return NULL")),
            CExpressionStatement(CodeExpression(f"{prefix}_shape = PyTuple_New({handle.array.rank})")),
            CExpressionStatement(
                CodeExpression(f"if ({prefix}_shape == NULL) {{ Py_DECREF({prefix}_helper); return NULL; }}")
            ),
            *self._native_descriptor_expected_shape_nodes(plan, context, names),
        ]
        binder_argument = ""
        binder_format = ""
        if default_binder_definition is not None:
            binder = f"{prefix}_default_binder"
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"{binder} = PyCFunction_NewEx(&{default_binder_definition}, NULL, NULL)")
                    ),
                    CExpressionStatement(
                        CodeExpression(
                            f"if ({binder} == NULL) {{ Py_DECREF({prefix}_helper); "
                            f"Py_DECREF({prefix}_shape); return NULL; }}"
                        )
                    ),
                )
            )
            binder_format = "O"
            binder_argument = f", {binder}"
        nodes.append(
            CExpressionStatement(
                CodeExpression(
                    f'{prefix}_packed = PyObject_CallFunction({prefix}_helper, "Os{dtype_format}iOi{binder_format}", '
                    f'{names.object_name}, "{handle.descriptor_kind.value}", {dtype_argument}, '
                    f"{handle.array.rank}, {prefix}_shape, {int(handle.optional_absent)}{binder_argument})"
                )
            )
        )
        if default_binder_definition is not None:
            nodes.append(CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_default_binder)")))
        nodes.extend(
            (
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_helper)")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_shape)")),
                CExpressionStatement(CodeExpression(f"if ({prefix}_packed == NULL) return NULL")),
            )
        )
        return tuple(nodes)

    def _native_descriptor_expected_shape_nodes(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Materialize the descriptor's declared shape for runtime validation."""
        handle = plan.native_array_handle
        if handle is None:
            return ()
        prefix = names.value_name
        nodes = []
        for axis, expression in enumerate(handle.array.shape):
            if expression in {":", "::Strided", "Flat"}:
                nodes.append(CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")))
                item = "Py_None"
            else:
                expected = self._array_extent_expression(handle.array, axis, expression, context)
                item = f"PyLong_FromLongLong((long long)({expected}))"
            nodes.extend(
                (
                    CExpressionStatement(CodeExpression(f"PyTuple_SET_ITEM({prefix}_shape, {axis}, {item})")),
                    CExpressionStatement(
                        CodeExpression(
                            f"if (PyTuple_GET_ITEM({prefix}_shape, {axis}) == NULL) {{ "
                            f"Py_DECREF({prefix}_helper); Py_DECREF({prefix}_shape); return NULL; }}"
                        )
                    ),
                )
            )
        return tuple(nodes)

    def _native_descriptor_presence_unpack_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        index: int,
    ) -> tuple[CExpressionStatement, ...]:
        """Decode the separate optional-presence token before descriptor fields."""
        if plan.binding.optional_mode is not OptionalMode.DESCRIPTOR:
            return ()
        prefix = names.value_name
        return (
            CExpressionStatement(CodeExpression(f"{prefix}_item = PyTuple_GetItem({prefix}_packed, {index})")),
            CExpressionStatement(
                CodeExpression(f"if ({prefix}_item == NULL) {{ Py_DECREF({prefix}_packed); return NULL; }}")
            ),
            CExpressionStatement(
                CodeExpression(f"if ({prefix}_item != Py_None) {names.present_name} = PyLong_AsVoidPtr({prefix}_item)")
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if ({names.present_name} == NULL && PyErr_Occurred()) {{ "
                    f"Py_DECREF({prefix}_packed); return NULL; }}"
                )
            ),
        )

    def _native_descriptor_pointer_unpack_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Validate one capsule and decode its plan-validated descriptor."""
        handle = plan.native_array_handle
        cfi_type = self._native_array_cfi_type(plan)
        prefix = names.value_name
        condition = "1" if plan.binding.optional_mode is OptionalMode.REQUIRED else f"{names.present_name} != NULL"
        return (
            CExpressionStatement(CodeExpression(f"{prefix}_item = PyTuple_GetItem({prefix}_packed, 0)")),
            CExpressionStatement(
                CodeExpression(f"if ({prefix}_item == NULL) {{ Py_DECREF({prefix}_packed); return NULL; }}")
            ),
            CIf(
                CodeExpression(condition),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f"{prefix}_native_handle = prik_native_array_handle_from_capsule({prefix}_item, "
                            f"{self._native_array_handle_kind_constant(handle)}, {handle.array.rank}, {cfi_type}, "
                            f"{self._native_array_expected_element_size(plan)}, "
                            f"sizeof(CFI_CDESC_T({handle.array.rank})))"
                        )
                    ),
                    CIf(
                        CodeExpression(f"{prefix}_native_handle == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_packed)")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(
                        CodeExpression(f"{names.value_name} = (CFI_cdesc_t *){prefix}_native_handle->descriptor")
                    ),
                ),
            ),
        )

    def _native_descriptor_fact_unpack_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Decode facts and establish a call-local standard descriptor."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            return ()
        if plan.binding.optional_mode is OptionalMode.REQUIRED:
            return self._native_descriptor_fact_present_nodes(plan, names)
        return (
            CIf(
                CodeExpression(f"{names.present_name} != NULL"),
                body=self._native_descriptor_fact_present_nodes(plan, names),
                else_body=self._native_descriptor_fact_absent_nodes(plan, names),
            ),
        )

    def _native_descriptor_fact_present_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Unpack one present fact tuple and initialize its CFI dimensions."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            return ()
        prefix = names.value_name
        rank = handle.array.rank
        nodes = [
            *self._native_descriptor_integer_field_nodes(prefix, f"{prefix}_base_addr", 0, pointer=True),
            *self._native_descriptor_integer_field_nodes(prefix, f"{prefix}_elem_len", 1),
            *self._native_descriptor_integer_field_nodes(prefix, f"{prefix}_descriptor_rank", 2),
        ]
        for axis in range(rank):
            offset = 3 + 3 * axis
            nodes.extend(self._native_descriptor_integer_field_nodes(prefix, f"{prefix}_lower_bound_{axis}", offset))
            nodes.extend(
                self._native_descriptor_integer_field_nodes(prefix, f"{prefix}_descriptor_extent_{axis}", offset + 1)
            )
            nodes.extend(
                self._native_descriptor_integer_field_nodes(prefix, f"{prefix}_stride_multiplier_{axis}", offset + 2)
            )
        nodes.append(
            CExpressionStatement(
                CodeExpression(
                    f"if ({prefix}_descriptor_rank != {rank}) {{ PyErr_Format(PyExc_ValueError, "
                    f'"native descriptor rank %lld does not match planned rank {rank} for argument '
                    f'{plan.binding.python_name}", (long long){prefix}_descriptor_rank); '
                    f"Py_DECREF({prefix}_packed); return NULL; }}"
                )
            )
        )
        nodes.extend(self._native_descriptor_establish_nodes(plan, names))
        return tuple(nodes)

    def _native_descriptor_fact_absent_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Establish one valid placeholder descriptor for an omitted argument."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            return ()
        prefix = names.value_name
        nodes = [
            CExpressionStatement(
                CodeExpression(f"{prefix}_elem_len = {self._native_descriptor_placeholder_elem_len(plan)}")
            ),
            CExpressionStatement(CodeExpression(f"{prefix}_descriptor_rank = {handle.array.rank}")),
        ]
        for axis in range(handle.array.rank):
            nodes.append(
                CExpressionStatement(
                    CodeExpression(f"{prefix}_stride_multiplier_{axis} = (CFI_index_t){prefix}_elem_len")
                )
            )
        nodes.extend(self._native_descriptor_establish_nodes(plan, names))
        return tuple(nodes)

    def _native_descriptor_establish_nodes(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[CExpressionStatement, ...]:
        """Establish call-local descriptor storage from already completed facts."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            return ()
        prefix = names.value_name
        rank = handle.array.rank
        cfi_type = self._native_array_cfi_type(plan)
        if cfi_type is None:
            raise ValueError(f"Missing CFI type for {plan.owner_path!r}")
        attribute = (
            "CFI_attribute_allocatable"
            if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
            else "CFI_attribute_pointer"
        )
        nodes = [
            *(
                CExpressionStatement(
                    CodeExpression(f"{prefix}_cfi_extents[{axis}] = {prefix}_descriptor_extent_{axis}")
                )
                for axis in range(rank)
            ),
            CExpressionStatement(
                CodeExpression(
                    f"{prefix}_establish_status = CFI_establish((CFI_cdesc_t *)&{prefix}_storage, "
                    f"{prefix}_base_addr, {attribute}, {cfi_type}, "
                    f"{prefix}_elem_len, {rank}, {prefix}_cfi_extents)"
                )
            ),
            CExpressionStatement(
                CodeExpression(
                    f"if ({prefix}_establish_status != CFI_SUCCESS) {{ PyErr_Format(PyExc_RuntimeError, "
                    f'"Unable to establish native descriptor for argument {plan.binding.python_name}: %d", '
                    f"{prefix}_establish_status); Py_DECREF({prefix}_packed); return NULL; }}"
                )
            ),
        ]
        for axis in range(rank):
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(
                            f"((CFI_cdesc_t *)&{prefix}_storage)->dim[{axis}].lower_bound = {prefix}_lower_bound_{axis}"
                        )
                    ),
                    CExpressionStatement(
                        CodeExpression(
                            f"((CFI_cdesc_t *)&{prefix}_storage)->dim[{axis}].extent = "
                            f"{prefix}_descriptor_extent_{axis}"
                        )
                    ),
                    CExpressionStatement(
                        CodeExpression(
                            f"((CFI_cdesc_t *)&{prefix}_storage)->dim[{axis}].sm = {prefix}_stride_multiplier_{axis}"
                        )
                    ),
                )
            )
        nodes.append(CExpressionStatement(CodeExpression(f"{names.value_name} = (CFI_cdesc_t *)&{prefix}_storage")))
        return tuple(nodes)

    @staticmethod
    def _native_descriptor_placeholder_elem_len(plan: ArgumentTransferPlan) -> str:
        """Return a valid element length for one absent call-local descriptor."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "0"
        return f"sizeof({PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).c_spelling})"

    def _native_descriptor_integer_field_nodes(
        self,
        prefix: str,
        target: str,
        index: int,
        *,
        pointer: bool = False,
    ) -> tuple[CExpressionStatement, ...]:
        """Decode one validated tuple integer with local failure cleanup."""
        converter = "PyLong_AsVoidPtr" if pointer else "PyLong_AsLongLong"
        cast = "(void *)" if pointer else ""
        error = f"{target} == NULL && PyErr_Occurred()" if pointer else "PyErr_Occurred()"
        return (
            CExpressionStatement(CodeExpression(f"{prefix}_item = PyTuple_GetItem({prefix}_packed, {index})")),
            CExpressionStatement(
                CodeExpression(f"if ({prefix}_item == NULL) {{ Py_DECREF({prefix}_packed); return NULL; }}")
            ),
            CExpressionStatement(CodeExpression(f"{target} = {cast}{converter}({prefix}_item)")),
            CExpressionStatement(CodeExpression(f"if ({error}) {{ Py_DECREF({prefix}_packed); return NULL; }}")),
        )

    def _native_array_dtype(self, plan: ArgumentTransferPlan) -> str | None:
        """Return the NumPy dtype spelling already selected by primitive type."""
        return self._native_array_dtype_for_semantic_type(plan.semantic_type_name, plan.datatype_family)

    def _native_array_dtype_for_result(self, plan: ResultPlan) -> str | None:
        """Return the NumPy dtype spelling selected for one handle result."""
        return self._native_array_dtype_for_semantic_type(plan.semantic_type_name, plan.datatype_family)

    def _native_array_dtype_for_semantic_type(
        self,
        semantic_type_name: str,
        datatype_family: DatatypeFamily,
    ) -> str | None:
        """Translate one completed array element family to a runtime dtype."""
        if datatype_family is DatatypeFamily.STRING:
            return None
        scalar_type = PrimitiveScalarTypeRegistry.type_for(semantic_type_name)
        return {
            "NPY_BOOL": "bool",
            "NPY_INT8": "int8",
            "NPY_INT16": "int16",
            "NPY_INT32": "int32",
            "NPY_INT64": "int64",
            "NPY_FLOAT32": "float32",
            "NPY_FLOAT64": "float64",
            "NPY_COMPLEX64": "complex64",
            "NPY_COMPLEX128": "complex128",
        }[scalar_type.numpy_type_macro]

    def _native_array_cfi_type(self, plan: ArgumentTransferPlan | ResultPlan) -> str | None:
        """Return the standard-descriptor element type after array-family dispatch."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "CFI_type_char"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).cfi_type_spelling

    def _module_native_array_cfi_type(self, plan: ModuleVariablePlan) -> str | None:
        """Return one module handle's standard-descriptor element type."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "CFI_type_char"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).cfi_type_spelling

    def _module_native_array_elem_size(self, plan: ModuleVariablePlan) -> str:
        """Return the completed numeric size or runtime character element length."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return f"{self._module_native_array_bridge_operation_name(plan, NativeArrayOperation.ELEMENT_LENGTH)}()"
        return f"sizeof({PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).c_spelling})"

    def _native_array_handle_factory_call(
        self,
        *,
        helper: str,
        target: str,
        descriptor_kind: str,
        semantic_type_name: str,
        datatype_family: DatatypeFamily,
        rank: int,
        ops: str,
        owner: str,
        descriptor_ownership: str,
        extraction_action: str,
    ) -> str:
        """Call the runtime factory with a fixed dtype or deferred character dtype."""
        dtype = self._native_array_dtype_for_semantic_type(semantic_type_name, datatype_family)
        if dtype is None:
            return (
                f'{target} = PyObject_CallFunction({helper}, "sOiOOssO", "{descriptor_kind}", Py_None, '
                f'{rank}, {ops}, {owner}, "{descriptor_ownership}", "{extraction_action}", Py_None)'
            )
        return (
            f'{target} = PyObject_CallFunction({helper}, "ssiOOssO", "{descriptor_kind}", "{dtype}", '
            f'{rank}, {ops}, {owner}, "{descriptor_ownership}", "{extraction_action}", Py_None)'
        )

    def _lower_argument_nullable_value(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Return omitted-or-value conversion nodes for an optional value."""
        if plan.binding.python_action is PythonBarrierAction.SCALAR_STORAGE:
            return self._lower_argument_nullable_scalar_storage(plan, context)
        if plan.object_kind is ObjectKind.NUMPY_ARRAY:
            return self._lower_argument_nullable_array_storage(plan, context)
        if plan.object_kind is ObjectKind.STRING:
            return self._lower_argument_nullable_string_value(plan, context)
        if plan.object_kind is ObjectKind.DERIVED_TYPE:
            return self._derived_argument_nodes(plan, context, optional=True)
        if plan.object_kind is not ObjectKind.SCALAR:
            raise ValueError(
                f"Unsupported optional C argument object kind for {plan.owner_path!r}: {plan.object_kind!r}"
            )
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        names = context.arguments[plan.owner_path]
        return (
            CDeclaration(names.object_name, "PyObject *", CodeExpression("Py_None")),
            CDeclaration(names.value_name, scalar_type.c_spelling),
            CDeclaration(names.nullable_name, "void *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"{names.object_name} != Py_None"),
                body=(
                    self._argument_scalar_unpack_statement(plan, names, scalar_type),
                    CExpressionStatement(CodeExpression(f"{names.nullable_name} = &{names.value_name}")),
                ),
            ),
        )

    def _lower_argument_nullable_scalar_storage(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CIf, ...]:
        """Preserve absent rank-zero storage or borrow one present NumPy cell."""
        names = context.arguments[plan.owner_path]
        required = self._lower_argument_required_scalar_storage(plan, context)
        declarations = tuple(node for node in required if isinstance(node, CDeclaration))
        body = tuple(node for node in required if not isinstance(node, CDeclaration))
        return (
            CDeclaration(names.object_name, "PyObject *", CodeExpression("Py_None")),
            *(node for node in declarations if node.name != names.object_name),
            CDeclaration(names.nullable_name, "void *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"{names.object_name} != Py_None"),
                body=(*body, CExpressionStatement(CodeExpression(f"{names.nullable_name} = {names.value_name}"))),
            ),
        )

    # Optional ordinary-array lowering.
    def _lower_argument_nullable_array_storage(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CIf, ...]:
        """Preserve absent optional arrays or validate one present NumPy buffer."""
        names = context.arguments[plan.owner_path]
        required_nodes = self._lower_argument_required_array_storage(plan, context)
        declarations = tuple(node for node in required_nodes if isinstance(node, CDeclaration))
        body = tuple(node for node in required_nodes if not isinstance(node, CDeclaration))
        return (
            CDeclaration(names.object_name, "PyObject *", CodeExpression("Py_None")),
            *(node for node in declarations if node.name != names.object_name),
            CIf(CodeExpression(f"{names.object_name} != Py_None"), body=body),
        )

    # Optional string lowering.
    def _lower_argument_nullable_string_value(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CIf, ...]:
        """Convert a concrete optional string or preserve its absent state."""
        names = context.arguments[plan.owner_path]
        declarations: tuple[CDeclaration, ...] = (
            CDeclaration(names.object_name, "PyObject *", CodeExpression("Py_None")),
            CDeclaration(names.length_name, "Py_ssize_t", CodeExpression("0")),
        )
        action = plan.binding.codegen_action
        if action is CodegenAction.CALL_LOCAL_INPUT:
            return (
                *declarations,
                CDeclaration(names.value_name, "const char *", CodeExpression("NULL")),
                CIf(
                    CodeExpression(f"{names.object_name} != Py_None"),
                    body=self._required_string_validation_nodes(plan, names, names.value_name),
                ),
            )
        if action is CodegenAction.COPY_IN_OUT:
            source_name = f"{names.value_name}_source"
            return (
                *declarations,
                CDeclaration(source_name, "const char *", CodeExpression("NULL")),
                CDeclaration(names.value_name, "char *", CodeExpression("NULL")),
                CIf(
                    CodeExpression(f"{names.object_name} != Py_None"),
                    body=(
                        *self._required_string_validation_nodes(plan, names, source_name),
                        *self._string_replacement_allocation_nodes(plan, names, source_name),
                    ),
                ),
            )
        raise ValueError(f"Unsupported optional C string action for {plan.owner_path!r}: {action!r}")

    def _lower_argument_descriptor(
        self,
        plan: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Return distinct omitted, explicit-none, and concrete descriptor states."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        names = context.arguments[plan.owner_path]
        return (
            CDeclaration(names.object_name, "PyObject *", CodeExpression("NULL")),
            CDeclaration(names.value_name, scalar_type.c_spelling),
            CDeclaration(names.nullable_name, "void *", CodeExpression("NULL")),
            CDeclaration(names.present_name, "void *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"{names.object_name} != NULL"),
                body=(CExpressionStatement(CodeExpression(f"{names.present_name} = &{names.value_name}")),),
            ),
            CIf(
                CodeExpression(f"({names.object_name} != NULL) && ({names.object_name} != Py_None)"),
                body=(
                    self._argument_scalar_unpack_statement(plan, names, scalar_type),
                    CExpressionStatement(CodeExpression(f"{names.nullable_name} = &{names.value_name}")),
                ),
            ),
        )

    def _argument_scalar_unpack_statement(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        scalar_type,
    ) -> CExpressionStatement:
        """Validate and unpack one exact scalar argument with its public error."""
        return self._scalar_exact_unpack_statement(
            scalar_type,
            names.object_name,
            names.value_name,
            (
                f'PyErr_Format(PyExc_TypeError, "Expected an argument of type '
                f"{scalar_type.python_type_name} for argument {plan.binding.python_name}. "
                f"Received <class '%s'>\", Py_TYPE({names.object_name})->tp_name)"
            ),
            "NULL",
        )

    def _visit_ResultPlan(
        self,
        plan: ResultPlan,
        *,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...] = (),
    ) -> tuple[CExpressionStatement | CDeclaration | CIf, ...]:
        """Lower one result through its completed binding action."""
        return self._lower_result(plan, context, failure_cleanup)

    def _lower_result(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CExpressionStatement | CDeclaration | CIf, ...]:
        """Dispatch one completed binding result action explicitly."""
        if plan.scalar_descriptor is not None:
            return self._lower_result_scalar_descriptor(plan, context, failure_cleanup)
        if plan.native_array_handle is not None:
            return self._lower_result_owned_native_array_handle(plan, context, failure_cleanup)
        match plan.object_kind:
            case ObjectKind.NUMPY_ARRAY:
                return self._lower_result_array_copy(plan, context, failure_cleanup)
            case ObjectKind.STRING:
                return self._lower_result_fixed_string(plan, context, failure_cleanup)
            case ObjectKind.SCALAR:
                if plan.binding.codegen_action is CodegenAction.DIRECT_VALUE:
                    return self._lower_result_direct_value(plan, context, failure_cleanup)
                raise ValueError(
                    f"Unsupported C scalar result action for {plan.owner_path!r}: {plan.binding.codegen_action!r}"
                )
            case ObjectKind.DERIVED_TYPE:
                return self._lower_result_derived(plan, context, failure_cleanup)
            case _:
                raise ValueError(f"Unsupported C result object kind for {plan.owner_path!r}: {plan.object_kind!r}")

    # Nullable rank-zero descriptor result lowering.
    def _lower_result_scalar_descriptor(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Copy one nullable descriptor payload into a detached Python value."""
        native_name = self._result_native_name(plan, context)
        python_name = context.python_results.get(plan.owner_path)
        if python_name is None:
            raise ValueError(f"Scalar descriptor result {plan.owner_path!r} has no Python role")
        prior_cleanup = self._decref_names(failure_cleanup)
        if plan.object_kind is ObjectKind.STRING:
            conversion = CodeExpression(
                f'PyUnicode_DecodeUTF8((const char *){native_name}, (Py_ssize_t){native_name}_length, "strict")'
            )
        else:
            scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
            if scalar_type.python_result_kind is None:
                raise ValueError(f"Unsupported scalar descriptor type {plan.semantic_type_name!r}")
            conversion = CodeExpression(
                self._scalar_result_expression(scalar_type, f"({scalar_type.c_spelling} *){native_name}")
            )
        present_body: tuple[CDeclaration | CExpressionStatement | CIf, ...] = (
            CIf(
                CodeExpression(f"{native_name} == NULL"),
                body=(
                    *prior_cleanup,
                    CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(CodeExpression(f"{python_name} = {conversion.text}")),
            CExpressionStatement(CodeExpression(f"free({native_name})")),
            CIf(
                CodeExpression(f"{python_name} == NULL"),
                body=(*prior_cleanup, CReturn(CodeExpression("NULL"))),
            ),
        )
        return (
            CDeclaration(python_name, "PyObject *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"!{native_name}_present"),
                body=(
                    CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")),
                    CExpressionStatement(CodeExpression(f"{python_name} = Py_None")),
                ),
                else_body=present_body,
            ),
        )

    # Owned native-array-handle result lowering.
    def _lower_result_owned_native_array_handle(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Transfer persistent CFI owner storage into one runtime handle."""
        descriptor_name = self._owned_result_descriptor_name(plan, context)
        python_name = context.python_results.get(plan.owner_path)
        handle = plan.native_array_handle
        if python_name is None or handle is None or handle.array.rank is None:
            raise ValueError(f"Owned native array result {plan.owner_path!r} has no binding consumer")
        prefix = f"{descriptor_name}_handle"
        cleanup = self._owned_descriptor_failure_cleanup(plan, descriptor_name)
        nodes: list[CDeclaration | CExpressionStatement | CIf] = [
            CDeclaration(f"{prefix}_runtime", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_helper", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_ops", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_owner", "PyObject *", CodeExpression("NULL")),
            CDeclaration(f"{prefix}_operation", "PyObject *", CodeExpression("NULL")),
            CDeclaration(python_name, "PyObject *", CodeExpression("NULL")),
            *self._owned_pointer_result_normalization_nodes(
                plan,
                descriptor_name,
                cleanup,
                failure_cleanup,
            ),
            CExpressionStatement(CodeExpression(f"{prefix}_ops = PyDict_New()")),
            CIf(
                CodeExpression(f"{prefix}_ops == NULL"),
                body=(*cleanup, *self._decref_names(failure_cleanup), CReturn(CodeExpression("NULL"))),
            ),
        ]
        nodes.extend(self._owned_native_array_ops_dictionary_nodes(plan, prefix, cleanup, failure_cleanup))
        nodes.extend(
            (
                CExpressionStatement(
                    CodeExpression(
                        f"{prefix}_owner = {self._native_array_capsule_new_expression(plan, descriptor_name)}"
                    )
                ),
                CIf(
                    CodeExpression(f"{prefix}_owner == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                        *cleanup,
                        *self._decref_names(failure_cleanup),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(CodeExpression(f"{descriptor_name} = NULL")),
                CExpressionStatement(
                    CodeExpression(f'{prefix}_runtime = PyImport_ImportModule("prik.runtime.handles")')
                ),
                CIf(
                    CodeExpression(f"{prefix}_runtime == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_owner)")),
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                        *cleanup,
                        *self._decref_names(failure_cleanup),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        f"{prefix}_helper = PyObject_GetAttrString({prefix}_runtime, "
                        '"_native_array_handle_from_generated_ops")'
                    )
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_runtime)")),
                CIf(
                    CodeExpression(f"{prefix}_helper == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_owner)")),
                        CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                        *cleanup,
                        *self._decref_names(failure_cleanup),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(
                        self._native_array_handle_factory_call(
                            helper=f"{prefix}_helper",
                            target=python_name,
                            descriptor_kind=handle.descriptor_kind.value,
                            semantic_type_name=plan.semantic_type_name,
                            datatype_family=plan.datatype_family,
                            rank=handle.array.rank,
                            ops=f"{prefix}_ops",
                            owner=f"{prefix}_owner",
                            descriptor_ownership="owned",
                            extraction_action=handle.extraction_action.value,
                        )
                    )
                ),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_helper)")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_owner)")),
                CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                CIf(
                    CodeExpression(f"{python_name} == NULL"),
                    body=(*self._decref_names(failure_cleanup), CReturn(CodeExpression("NULL"))),
                ),
            )
        )
        return tuple(nodes)

    def _owned_pointer_result_normalization_nodes(
        self,
        plan: ResultPlan,
        descriptor_name: str,
        cleanup: tuple[CExpressionStatement, ...],
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CIf, ...]:
        """Re-establish empty numeric pointer storage before publishing it.

        Some Fortran runtimes clear descriptor metadata when assigning an
        unassociated pointer result.  The binding consumes the completed
        descriptor kind, rank, and dtype to restore a valid empty CFI record;
        associated results and runtime-width string descriptors are unchanged.
        """
        handle = plan.native_array_handle
        if (
            handle is None
            or handle.descriptor_kind is not NativeArrayDescriptorKind.POINTER
            or plan.datatype_family is DatatypeFamily.STRING
        ):
            return ()
        cfi_type = self._native_array_cfi_type(plan)
        status_name = f"{descriptor_name}_owner_status"
        return (
            CIf(
                CodeExpression(f"{descriptor_name}->base_addr == NULL"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f"{status_name} = CFI_establish({descriptor_name}, NULL, CFI_attribute_pointer, "
                            f"{cfi_type}, {self._native_array_expected_element_size(plan)}, "
                            f"{handle.array.rank}, NULL)"
                        )
                    ),
                    CIf(
                        CodeExpression(f"{status_name} != CFI_SUCCESS"),
                        body=(
                            *cleanup,
                            *self._decref_names(failure_cleanup),
                            CExpressionStatement(
                                CodeExpression(
                                    'PyErr_SetString(PyExc_RuntimeError, "failed to normalize unassociated pointer '
                                    'result descriptor")'
                                )
                            ),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                ),
            ),
        )

    def _owned_native_array_ops_dictionary_nodes(
        self,
        result: ResultPlan,
        prefix: str,
        cleanup: tuple[CExpressionStatement | CIf, ...],
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Populate a result handle's operation dictionary from planned roles."""
        handle = result.native_array_handle
        if handle is None:
            return ()
        nodes = []
        for operation in handle.operations:
            definition = self._owned_native_array_operation_def_name(None, result, operation)
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"{prefix}_operation = PyCFunction_NewEx(&{definition}, NULL, NULL)")
                    ),
                    CIf(
                        CodeExpression(f"{prefix}_operation == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                            *cleanup,
                            *self._decref_names(failure_cleanup),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CIf(
                        CodeExpression(
                            f'PyDict_SetItemString({prefix}_ops, "{operation.value}", {prefix}_operation) < 0'
                        ),
                        body=(
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_operation)")),
                            CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_ops)")),
                            *cleanup,
                            *self._decref_names(failure_cleanup),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({prefix}_operation)")),
                )
            )
        return tuple(nodes)

    # Ordinary-array result lowering.
    def _lower_result_array_copy(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Transfer one bridge-owned fixed-shape buffer into a NumPy capsule owner."""
        handoff = plan.array
        native_name = self._result_native_name(plan, context)
        python_name = context.python_results.get(plan.owner_path)
        if handoff is None or handoff.rank is None or python_name is None:
            raise ValueError(f"Array result {plan.owner_path!r} has no fixed binding shape")
        dimensions = tuple(
            self._result_extent_expression(plan, handoff, axis, expression, context)
            for axis, expression in enumerate(handoff.shape)
        )
        dimension_declarations: tuple[CDeclaration, ...]
        if handoff.rank == 0:
            dims_name = "NULL"
            dimension_declarations = ()
        else:
            dims_name = f"{python_name}_dims"
            dimension_declarations = (
                CDeclaration(f"{dims_name}[]", "npy_intp", CodeExpression(f"{{{', '.join(dimensions)}}}")),
            )
        fortran_order = 0 if handoff.order == "ORDER_C" or handoff.rank <= 1 else 1
        base_name = f"{python_name}_base"
        decrefs = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in failure_cleanup)
        return (
            CIf(
                CodeExpression(f"{native_name} == NULL"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_MemoryError, "Unable to allocate copy-return output array.")'
                        )
                    ),
                    *decrefs,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            *dimension_declarations,
            CDeclaration(
                python_name,
                "PyObject *",
                self._array_result_creation_expression(
                    plan,
                    handoff.rank,
                    dims_name,
                    fortran_order,
                    native_name,
                ),
            ),
            CIf(
                CodeExpression(f"{python_name} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"free({native_name})")),
                    *decrefs,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            *self._capsule_base_attachment_nodes(
                python_name,
                base_name,
                native_name,
                failure_cleanup=decrefs,
            ),
        )

    def _result_extent_expression(
        self,
        result: ResultPlan,
        handoff: ArrayHandoffPlan,
        axis: int,
        expression: str,
        context: _CFunctionContext,
    ) -> str:
        """Use the entrypoint result for native axes and local roles for all others."""
        if handoff.extent_evaluation[axis] == "bridge":
            return self._declaration_extent_result_name(result, axis)
        return self._array_extent_expression(handoff, axis, expression, context)

    def _array_result_creation_expression(
        self,
        plan: ResultPlan,
        rank: int,
        dims_name: str,
        fortran_order: int,
        native_name: str,
    ) -> CodeExpression:
        """Construct a non-owning NumPy view before attaching its capsule owner."""
        flags = (
            "NPY_ARRAY_F_CONTIGUOUS | NPY_ARRAY_WRITEABLE"
            if fortran_order
            else "NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_WRITEABLE"
        )
        if plan.datatype_family is DatatypeFamily.STRING:
            handoff = plan.array
            if handoff is None or handoff.itemsize is None or handoff.itemsize <= 0:
                raise ValueError(f"Character array result {plan.owner_path!r} has no fixed itemsize")
            return CodeExpression(
                f"(PyObject *)PyArray_New(&PyArray_Type, {rank}, {dims_name}, NPY_STRING, "
                f"NULL, {native_name}, {handoff.itemsize}, {flags}, NULL)"
            )
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        if scalar_type.numpy_type_macro is None:
            raise ValueError(f"Unsupported array result type {plan.semantic_type_name!r}")
        return CodeExpression(
            f"(PyObject *)PyArray_New(&PyArray_Type, {rank}, {dims_name}, {scalar_type.numpy_type_macro}, "
            f"NULL, {native_name}, 0, {flags}, NULL)"
        )

    def _capsule_base_attachment_nodes(
        self,
        array_name: str,
        base_name: str,
        data_name: str,
        *,
        failure_cleanup: tuple[CExpressionStatement, ...] = (),
    ) -> tuple[CDeclaration | CIf, ...]:
        """Transfer one bridge-owned buffer to NumPy without double release."""
        return (
            CDeclaration(
                base_name,
                "PyObject *",
                CodeExpression(f"PyCapsule_New({data_name}, NULL, prik_release_owned_memory)"),
            ),
            CIf(
                CodeExpression(f"{base_name} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({array_name})")),
                    CExpressionStatement(CodeExpression(f"free({data_name})")),
                    *failure_cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CIf(
                CodeExpression(f"PyArray_SetBaseObject((PyArrayObject *){array_name}, {base_name}) < 0"),
                body=(
                    # PyArray_SetBaseObject steals the capsule reference even on failure.
                    CExpressionStatement(CodeExpression(f"Py_DECREF({array_name})")),
                    *failure_cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        )

    # String result lowering.
    def _lower_result_fixed_string(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CExpressionStatement | CDeclaration | CIf, ...]:
        """Consume one bridge-owned NUL-terminated fixed string copy."""
        native_name = self._result_native_name(plan, context)
        python_name = context.python_results.get(plan.owner_path)
        if python_name is None:
            raise ValueError(f"String result {plan.owner_path!r} has no Python result role")
        decrefs = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in failure_cleanup)
        if plan.nullable:
            return (
                CDeclaration(python_name, "PyObject *", CodeExpression("NULL")),
                CIf(
                    CodeExpression(f"{native_name} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression(f"{python_name} = Py_None")),
                        CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")),
                    ),
                    else_body=(
                        CExpressionStatement(
                            CodeExpression(f'{python_name} = Py_BuildValue("s", (const char *){native_name})')
                        ),
                        CExpressionStatement(CodeExpression(f"free({native_name})")),
                    ),
                ),
                CIf(
                    CodeExpression(f"{python_name} == NULL"),
                    body=(*decrefs, CReturn(CodeExpression("NULL"))),
                ),
            )
        return (
            CIf(
                CodeExpression(f"{native_name} == NULL"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_MemoryError, "Unable to allocate copy-return output string.")'
                        )
                    ),
                    *decrefs,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                python_name,
                "PyObject *",
                CodeExpression(f'Py_BuildValue("s", (const char *){native_name})'),
            ),
            CExpressionStatement(CodeExpression(f"free({native_name})")),
            CIf(
                CodeExpression(f"{python_name} == NULL"),
                body=(*decrefs, CReturn(CodeExpression("NULL"))),
            ),
        )

    # Derived-type result lowering.
    def _lower_result_derived(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
        pending_native_cleanup: tuple[CExpressionStatement, ...] = (),
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Wrap persistent native storage in one exactly-once capsule owner."""
        if plan.derived is None:
            raise ValueError(f"Derived result {plan.owner_path!r} has no handoff plan")
        if plan.derived.storage in {
            DerivedObjectStorage.ALLOCATABLE_HOLDER,
            DerivedObjectStorage.POINTER_HOLDER,
        }:
            return self._lower_holder_result(plan, context, failure_cleanup, pending_native_cleanup)
        native_name = self._result_native_name(plan, context)
        python_name = context.python_results[plan.owner_path]
        capsule = f"{python_name}_capsule"
        helper = f"{python_name}_helper"
        prior = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in failure_cleanup)
        return (
            CIf(
                CodeExpression(f"{native_name} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                    *pending_native_cleanup,
                    *prior,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                capsule,
                "PyObject *",
                CodeExpression(
                    f'PyCapsule_New({native_name}, "{self._derived_capsule_name(plan.derived.backend_symbol)}", '
                    f"{self._derived_capsule_destructor_name(plan.derived.backend_symbol)})"
                ),
            ),
            CIf(
                CodeExpression(f"{capsule} == NULL"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f"{self._derived_destroy_bridge_name(plan.derived.backend_symbol)}({native_name})"
                        )
                    ),
                    *pending_native_cleanup,
                    *prior,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                helper,
                "PyObject *",
                CodeExpression(f'PyObject_GetAttrString(self, "_prik_wrap_{plan.derived.type_name}")'),
            ),
            CIf(
                CodeExpression(f"{helper} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                    *pending_native_cleanup,
                    *prior,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                python_name,
                "PyObject *",
                CodeExpression(f"PyObject_CallFunctionObjArgs({helper}, {capsule}, NULL)"),
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({helper})")),
            CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
            CIf(
                CodeExpression(f"{python_name} == NULL"),
                body=(*pending_native_cleanup, *prior, CReturn(CodeExpression("NULL"))),
            ),
        )

    def _lower_holder_result(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
        pending_native_cleanup: tuple[CExpressionStatement, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Wrap one nullable typed holder without exposing its component address."""
        if plan.derived is None:
            raise ValueError(f"Derived result {plan.owner_path!r} has no handoff plan")
        type_name = plan.derived.type_name
        type_symbol = plan.derived.backend_symbol
        storage = plan.derived.storage
        native_name = self._result_native_name(plan, context)
        python_name = context.python_results[plan.owner_path]
        cleanup = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in failure_cleanup)
        return (
            CDeclaration(python_name, "PyObject *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"{native_name} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                    *pending_native_cleanup,
                    *cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
                else_body=self._holder_wrapper_nodes(
                    type_name,
                    type_symbol,
                    storage,
                    self._derived_target_owner(plan.derived),
                    native_name,
                    python_name,
                    (*pending_native_cleanup, *cleanup),
                ),
            ),
        )

    def _holder_wrapper_nodes(
        self,
        type_name: str,
        type_symbol: str,
        storage: DerivedObjectStorage,
        owner: str,
        address: str,
        target: str,
        failure_cleanup: tuple[CExpressionStatement, ...] = (),
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Construct one holder-backed wrapper with a single cleanup path."""
        capsule_name, destructor_name, destroy_name, ops_name, origin = self._holder_wrapper_symbols(
            type_symbol,
            storage,
        )
        capsule = f"{target}_capsule"
        helper = f"{target}_helper"
        ops = f"{target}_ops"
        return (
            CDeclaration(
                capsule,
                "PyObject *",
                CodeExpression(f'PyCapsule_New({address}, "{capsule_name}", {destructor_name})'),
            ),
            CIf(
                CodeExpression(f"{capsule} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"{destroy_name}({address})")),
                    *failure_cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                helper,
                "PyObject *",
                CodeExpression(f'PyObject_GetAttrString(self, "_prik_wrap_{type_name}")'),
            ),
            CIf(
                CodeExpression(f"{helper} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                    *failure_cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration(
                ops,
                "PyObject *",
                CodeExpression(f'PyObject_GetAttrString(self, "{ops_name}")'),
            ),
            CIf(
                CodeExpression(f"{ops} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({helper})")),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
                    *failure_cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(
                CodeExpression(
                    f'{target} = PyObject_CallFunction({helper}, "OOOs", {capsule}, {owner}, {ops}, "{origin}")'
                )
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({ops})")),
            CExpressionStatement(CodeExpression(f"Py_DECREF({helper})")),
            CExpressionStatement(CodeExpression(f"Py_DECREF({capsule})")),
            CIf(
                CodeExpression(f"{target} == NULL"),
                body=(*failure_cleanup, CReturn(CodeExpression("NULL"))),
            ),
        )

    @staticmethod
    def _derived_target_owner(handoff: DerivedHandoffPlan) -> str:
        """Select the retained pointer-target owner from completed policy."""
        if handoff.target_owner_retention is DerivedOwnerRetention.NATIVE_MODULE:
            return "self"
        if handoff.target_owner_retention is DerivedOwnerRetention.NONE:
            return "Py_None"
        raise ValueError(f"Unsupported derived target owner retention: {handoff.target_owner_retention.value}")

    def _holder_wrapper_symbols(
        self,
        type_symbol: str,
        storage: DerivedObjectStorage,
    ) -> tuple[str, str, str, str, str]:
        """Return mechanical symbols for one completed holder storage choice."""
        if storage is DerivedObjectStorage.ALLOCATABLE_HOLDER:
            return (
                self._allocatable_holder_capsule_name(type_symbol),
                self._allocatable_holder_capsule_destructor_name(type_symbol),
                self._allocatable_holder_destroy_bridge_name(type_symbol),
                self._allocatable_holder_ops_name(type_symbol),
                storage.value,
            )
        if storage is DerivedObjectStorage.POINTER_HOLDER:
            return (
                self._pointer_holder_capsule_name(type_symbol),
                self._pointer_holder_capsule_destructor_name(type_symbol),
                self._pointer_holder_destroy_bridge_name(type_symbol),
                self._pointer_holder_ops_name(type_symbol),
                storage.value,
            )
        raise ValueError(f"Unsupported derived holder storage: {storage.value}")

    # Scalar result lowering.
    def _lower_result_direct_value(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CExpressionStatement | CDeclaration | CIf, ...]:
        """Lower result direct value from the supplied completed binding records without inferring semantic policy."""
        return self._lower_result_value(plan, context, failure_cleanup)

    def _lower_result_value(
        self,
        plan: ResultPlan,
        context: _CFunctionContext,
        failure_cleanup: tuple[str, ...],
    ) -> tuple[CExpressionStatement | CDeclaration | CIf, ...]:
        """Convert one native result into its binding-owned Python consumer."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        native_name = self._result_native_name(plan, context)
        python_name = context.python_results.get(plan.owner_path)
        if scalar_type.python_result_kind is None or python_name is None:
            raise ValueError(f"Unsupported scalar result type {plan.semantic_type_name!r}")
        converted_name = native_name
        conversion = ()
        if plan.entrypoint.native_scalar_c_type is not None:
            converted_name = f"{native_name}_contract"
            conversion = (
                CDeclaration(
                    converted_name,
                    scalar_type.c_spelling,
                    CodeExpression(f"({scalar_type.c_spelling}){native_name}"),
                ),
            )
        return (
            *conversion,
            CDeclaration(
                python_name,
                "PyObject *",
                CodeExpression(self._scalar_result_expression(scalar_type, f"&{converted_name}")),
            ),
            CIf(
                CodeExpression(f"{python_name} == NULL"),
                body=(
                    *(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in failure_cleanup),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        )

    def _result_native_name(self, plan: ResultPlan, context: _CFunctionContext) -> str:
        """Return the validated C storage consumed by one result conversion."""
        if plan.source_kind == "direct_return":
            if context.result_name is None:
                raise ValueError(f"Direct result {plan.owner_path!r} has no C storage")
            return context.result_name
        try:
            return context.native_outputs[plan.entrypoint.native_result_role]
        except KeyError:
            raise ValueError(f"Hidden result {plan.owner_path!r} has no C output storage") from None

    def _output_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement | CDeclaration | CReturn, ...]:
        """Return the native envelope, status projection, and Python result."""
        nodes = [
            *self._callback_context_push_nodes(plan, context),
            *self._lower_native_call(plan, self._entrypoint_call_statement(plan, context)),
            *self._callback_context_pop_nodes(plan),
            *self._derived_call_failure_nodes(plan, context),
            *self._derived_after_native_failure_nodes(plan, context),
            *self._derived_result_allocation_failure_nodes(plan, context),
            *self._owned_deferred_character_materialization_nodes(plan, context),
            *self._binding_transformation_post_call_nodes(plan, context),
            *self._lower_status_error(plan, context),
        ]
        if plan.results or plan.writeback_actions:
            nodes.extend(self._combined_output_nodes(plan, context))
        else:
            nodes.append(CExpressionStatement(CodeExpression("Py_RETURN_NONE")))
        return tuple(nodes)

    def _combined_output_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Convert every public output once, then aggregate by completed position."""
        published, ordinary_writebacks, derived_results, scalar_results = self._output_conversion_groups(plan)
        converted: list[str] = []
        nodes = []

        # Published temporaries are converted first so every later failure owns
        # an ordinary Python reference that can be released uniformly.
        for action in published:
            nodes.extend(self._writeback_value_nodes(plan, action, context, tuple(converted)))
            converted.append(context.python_results[action.owner_path])

        for position, result in enumerate(derived_results):
            pending = self._derived_native_storage_cleanup_nodes(derived_results[position + 1 :], context)
            nodes.extend(self._lower_result_derived(result, context, tuple(converted), pending))
            converted.append(context.python_results[result.owner_path])

        for result in scalar_results:
            nodes.extend(self.visit(result, context=context, failure_cleanup=tuple(converted)))
            converted.append(context.python_results[result.owner_path])

        for action in ordinary_writebacks:
            nodes.extend(self._writeback_value_nodes(plan, action, context, tuple(converted)))
            converted.append(context.python_results[action.owner_path])

        # A ``Hidden`` result is lowered exactly like a published one so that
        # every release the ordinary path performs still happens; only the
        # Python object it produced is dropped instead of being aggregated.
        for result in plan.results:
            if not result.python_returned:
                nodes.append(
                    CExpressionStatement(CodeExpression(f"Py_DECREF({context.python_results[result.owner_path]})"))
                )
        hidden_owners = {result.owner_path for result in plan.results if not result.python_returned}
        ordered = tuple(
            context.python_results[owner]
            for owner, _position in self._output_owners(plan)
            if owner not in hidden_owners
        )
        nodes.extend(self._python_result_aggregation_nodes(ordered, context))
        return tuple(nodes)

    def _output_conversion_groups(
        self,
        plan: FunctionPlan,
    ) -> tuple[
        tuple[LifecycleActionPlan, ...],
        tuple[LifecycleActionPlan, ...],
        tuple[ResultPlan, ...],
        tuple[ResultPlan, ...],
    ]:
        """Partition completed outputs into their ordered conversion leaves."""
        writebacks = self._ordered_output_writebacks(plan)
        published = tuple(action for action in writebacks if self._publishes_array_replacement(plan, action))
        ordinary = tuple(action for action in writebacks if action not in published)
        derived = tuple(result for result in plan.results if result.object_kind is ObjectKind.DERIVED_TYPE)
        scalar = tuple(result for result in plan.results if result.object_kind is not ObjectKind.DERIVED_TYPE)
        return published, ordinary, derived, scalar

    def _mixed_string_writeback_nodes(
        self,
        plan: FunctionPlan,
        action: LifecycleActionPlan,
        context: _CFunctionContext,
        converted: tuple[str, ...],
    ) -> tuple:
        """Convert one projected fixed string without terminating aggregation."""
        source = self._argument_for_role(plan, action.source_role)
        if action.binding.datatype_family is not DatatypeFamily.STRING:
            raise ValueError(f"Mixed output {action.owner_path!r} is not a fixed string")
        names = context.arguments[source.owner_path]
        target = context.python_results[action.owner_path]
        cleanup = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in converted)
        conversion = CExpressionStatement(
            CodeExpression(f'{target} = Py_BuildValue("s", (const char *){names.value_name})')
        )
        failure = CIf(CodeExpression(f"{target} == NULL"), body=(*cleanup, CReturn(CodeExpression("NULL"))))
        if source.binding.optional_mode is OptionalMode.REQUIRED:
            return (
                CDeclaration(target, "PyObject *", CodeExpression("NULL")),
                conversion,
                CExpressionStatement(CodeExpression(f"free({names.value_name})")),
                failure,
            )
        if source.binding.optional_mode is OptionalMode.NULLABLE_VALUE:
            return (
                CDeclaration(target, "PyObject *", CodeExpression("NULL")),
                CIf(
                    CodeExpression(f"{names.value_name} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")),
                        CExpressionStatement(CodeExpression(f"{target} = Py_None")),
                    ),
                    else_body=(
                        conversion,
                        CExpressionStatement(CodeExpression(f"free({names.value_name})")),
                        failure,
                    ),
                ),
            )
        raise ValueError(f"Unsupported mixed string presence for {source.owner_path!r}")

    def _derived_after_native_failure_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CIf, ...]:
        """Inject one post-return error after the bridge has restored all origins."""
        if not any(argument.derived_call is not None for argument in plan.arguments):
            return ()
        fault = "prik_derived_after_native_fault"
        derived_results = self._required_derived_results(plan)
        return (
            CDeclaration(
                fault,
                "const char *",
                CodeExpression('getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE")'),
            ),
            CIf(
                CodeExpression(f"{fault} != NULL && {fault}[0] != '\\0' && {fault}[0] != '0'"),
                body=(
                    *self._binding_transformation_cleanup_nodes(plan, context),
                    *self._derived_native_storage_cleanup_nodes(derived_results, context),
                    *self._owned_result_descriptor_failure_nodes(plan, context),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        )

    def _derived_call_failure_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CIf, ...]:
        """Map bridge status codes after every transaction has been restored."""
        arguments = tuple(argument for argument in plan.arguments if argument.derived_call is not None)
        return tuple(
            CIf(
                CodeExpression(f"{self._derived_status_name(context.arguments[argument.owner_path])} != 0"),
                body=(
                    *self._binding_transformation_cleanup_nodes(plan, context),
                    *self._one_derived_call_error_nodes(argument, context),
                    CReturn(CodeExpression("NULL")),
                ),
            )
            for argument in arguments
        )

    def _one_derived_call_error_nodes(
        self,
        argument: ArgumentTransferPlan,
        context: _CFunctionContext,
    ) -> tuple[CIf, ...]:
        """Build one derived call error nodes from the supplied completed binding records; emitted nodes only project completed binding actions."""
        status = self._derived_status_name(context.arguments[argument.owner_path])
        name = self._c_string_literal(argument.binding.python_name)
        return (
            CIf(
                CodeExpression(f"{status} == 1"),
                body=(
                    CExpressionStatement(
                        CodeExpression(
                            f'PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", {name})'
                        )
                    ),
                ),
                else_body=(
                    CIf(
                        CodeExpression(f"{status} == 4"),
                        body=(CExpressionStatement(CodeExpression("PyErr_NoMemory()")),),
                        else_body=(
                            CExpressionStatement(
                                CodeExpression(
                                    f'PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", {name}, {status})'
                                )
                            ),
                        ),
                    ),
                ),
            ),
        )

    # Deferred-character native-array-handle result materialization.
    def _owned_deferred_character_materialization_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Materialize copied runtime-width character outputs into persistent CFI owners."""
        nodes = []
        for result in sorted(plan.results, key=lambda item: item.result_position):
            if not self._is_owned_deferred_character_result(result):
                continue
            native_name = self._result_native_name(result, context)
            nodes.extend(self._one_owned_deferred_character_materialization(result, native_name))
        return tuple(nodes)

    def _one_owned_deferred_character_materialization(
        self,
        result: ResultPlan,
        native_name: str,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Copy one bridge-owned character payload into its handle-owned descriptor."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Deferred character result {result.owner_path!r} has no descriptor rank")
        rank = handle.array.rank
        descriptor = f"{native_name}_owner_descriptor"
        status = f"{native_name}_owner_status"
        itemsize = f"{native_name}_itemsize"
        lower_bounds = f"{native_name}_lower_bounds"
        upper_bounds = f"{native_name}_upper_bounds"
        byte_count = " * ".join((itemsize, *(f"{native_name}_extent_{axis}" for axis in range(rank))))
        return (
            CExpressionStatement(CodeExpression(f"{descriptor} = {self._zeroed_descriptor_allocation(rank)}")),
            CIf(
                CodeExpression(f"{descriptor} == NULL"),
                body=(
                    CExpressionStatement(CodeExpression(f"free({native_name})")),
                    CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(
                CodeExpression(
                    f"{status} = CFI_establish({descriptor}, NULL, CFI_attribute_allocatable, CFI_type_char, "
                    f"({itemsize} > 0 ? (size_t){itemsize} : (size_t)1), {rank}, NULL)"
                )
            ),
            CIf(
                CodeExpression(f"{status} != CFI_SUCCESS"),
                body=(
                    CExpressionStatement(CodeExpression(f"free({descriptor})")),
                    CExpressionStatement(CodeExpression(f"{descriptor} = NULL")),
                    CExpressionStatement(CodeExpression(f"free({native_name})")),
                    CExpressionStatement(
                        CodeExpression(
                            'PyErr_SetString(PyExc_RuntimeError, "failed to establish deferred character owner")'
                        )
                    ),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CIf(
                CodeExpression(f"{native_name} != NULL"),
                body=(
                    CDeclaration(f"{lower_bounds}[{rank}]", "CFI_index_t"),
                    CDeclaration(f"{upper_bounds}[{rank}]", "CFI_index_t"),
                    *(CExpressionStatement(CodeExpression(f"{lower_bounds}[{axis}] = 0")) for axis in range(rank)),
                    *(
                        CExpressionStatement(
                            CodeExpression(f"{upper_bounds}[{axis}] = (CFI_index_t){native_name}_extent_{axis} - 1")
                        )
                        for axis in range(rank)
                    ),
                    CExpressionStatement(
                        CodeExpression(
                            f"{status} = CFI_allocate({descriptor}, {lower_bounds}, {upper_bounds}, (size_t){itemsize})"
                        )
                    ),
                    CIf(
                        CodeExpression(f"{status} != CFI_SUCCESS"),
                        body=(
                            CExpressionStatement(CodeExpression(f"free({descriptor})")),
                            CExpressionStatement(CodeExpression(f"{descriptor} = NULL")),
                            CExpressionStatement(CodeExpression(f"free({native_name})")),
                            CExpressionStatement(
                                CodeExpression(
                                    'PyErr_SetString(PyExc_RuntimeError, "failed to allocate deferred character owner")'
                                )
                            ),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(
                        CodeExpression(f"memcpy({descriptor}->base_addr, {native_name}, (size_t)({byte_count}))")
                    ),
                    CExpressionStatement(CodeExpression(f"free({native_name})")),
                    CExpressionStatement(CodeExpression(f"{native_name} = NULL")),
                ),
            ),
        )

    def _derived_result_allocation_failure_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CIf, ...]:
        """Reject null persistent object storage before reading any other native output."""
        derived = self._required_derived_results(plan)
        if not derived:
            return ()
        native_names = tuple(self._result_native_name(result, context) for result in derived)
        cleanup = [
            *self._derived_native_storage_cleanup_nodes(derived, context),
            *self._owned_result_descriptor_failure_nodes(plan, context),
            *self._binding_transformation_cleanup_nodes(plan, context),
        ]
        return (
            CIf(
                CodeExpression(" || ".join(f"{name} == NULL" for name in native_names)),
                body=(
                    *cleanup,
                    CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
        )

    @staticmethod
    def _required_derived_results(plan: FunctionPlan) -> tuple[ResultPlan, ...]:
        """Return derived results whose bridge must publish non-null owner storage."""
        return tuple(result for result in plan.results if result.object_kind is ObjectKind.DERIVED_TYPE)

    def _owned_result_descriptor_failure_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement, ...]:
        """Release persistent array descriptors when another result allocation fails."""
        return tuple(
            node
            for result in plan.results
            if self._is_owned_native_array_result(result)
            for node in self._owned_descriptor_failure_cleanup(
                result,
                self._owned_result_descriptor_name(result, context),
            )
        )

    def _derived_native_storage_cleanup_nodes(
        self,
        results: tuple[ResultPlan, ...],
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement, ...]:
        """Destroy every unpublished derived result pointer exactly once when non-null."""
        return tuple(
            CExpressionStatement(
                CodeExpression(
                    f"if ({self._result_native_name(result, context)} != NULL) {{ "
                    f"{self._derived_result_destroy_bridge_name(result)}("
                    f"{self._result_native_name(result, context)}); "
                    f"{self._result_native_name(result, context)} = NULL; }}"
                )
            )
            for result in results
            if result.derived is not None
        )

    def _derived_result_destroy_bridge_name(self, result: ResultPlan) -> str:
        """Return the binding-local derived result destroy bridge name derived from the supplied completed binding records; this helper preserves completed policy."""
        if result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER:
            return self._allocatable_holder_destroy_bridge_name(result.derived.backend_symbol)
        if result.derived.storage is DerivedObjectStorage.POINTER_HOLDER:
            return self._pointer_holder_destroy_bridge_name(result.derived.backend_symbol)
        return self._derived_destroy_bridge_name(result.derived.backend_symbol)

    def _python_result_aggregation_nodes(
        self,
        converted: tuple[str, ...],
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Return one object directly or assemble ordered tuple ownership."""
        if not converted:
            # Every output was hidden, so the call publishes nothing. The macro
            # increfs before returning; a bare ``Py_None`` would leak a
            # decrement onto the singleton.
            return (CExpressionStatement(CodeExpression("Py_RETURN_NONE")),)
        if len(converted) == 1:
            return (CReturn(CodeExpression(converted[0])),)
        aggregate = context.python_result_name
        if aggregate is None:
            raise ValueError("Multiple Python results have no aggregate binding role")
        return (
            CDeclaration(aggregate, "PyObject *", CodeExpression(f"PyTuple_New({len(converted)})")),
            CIf(
                CodeExpression(f"{aggregate} == NULL"),
                body=(
                    *(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in converted),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            *(
                CExpressionStatement(CodeExpression(f"PyTuple_SET_ITEM({aggregate}, {position}, {name})"))
                for position, name in enumerate(converted)
            ),
            CReturn(CodeExpression(aggregate)),
        )

    def _entrypoint_call_statement(self, plan: FunctionPlan, context: _CFunctionContext) -> CExpressionStatement:
        """Return the mechanical entrypoint call selected by result storage."""
        call = self._entrypoint_call(plan, context)
        direct_result = self._direct_result(plan)
        if direct_result is None or self._is_owned_native_array_result(direct_result):
            expression = call
        elif direct_result.entrypoint.direct_result_abi is DirectResultABI.LOGICAL_LOW_BIT_INT8:
            expression = f"{context.result_name} = (bool){call}"
        elif (
            direct_result.entrypoint.direct_result_abi is DirectResultABI.NATIVE_SCALAR
            or direct_result.object_kind is not ObjectKind.SCALAR
            or direct_result.scalar_descriptor is not None
        ):
            direct_c_result = plan.entrypoint.direct_c_abi.result if plan.entrypoint.direct_c_abi is not None else None
            if direct_c_result is not None and direct_c_result.converts_to_contract_storage:
                contract_type = PrimitiveScalarTypeRegistry.type_for(direct_result.semantic_type_name)
                call = f"({contract_type.c_spelling}){call}"
            expression = f"{context.result_name} = {call}"
        else:
            raise ValueError(f"Scalar result {direct_result.owner_path!r} has no completed direct-result ABI")
        return CExpressionStatement(CodeExpression(expression))

    def _lower_native_call(
        self,
        plan: FunctionPlan,
        call: CExpressionStatement,
    ) -> tuple[CAllowThreadsBegin | CAllowThreadsEnd | CExpressionStatement, ...]:
        """Dispatch the completed GIL envelope to directly named methods."""
        if plan.binding.release_gil:
            return self._lower_native_call_released(call)
        return self._lower_native_call_held(call)

    def _lower_native_call_held(self, call: CExpressionStatement) -> tuple[CExpressionStatement, ...]:
        """Emit one native entrypoint call while retaining the GIL."""
        return (call,)

    def _lower_native_call_released(
        self,
        call: CExpressionStatement,
    ) -> tuple[CAllowThreadsBegin | CExpressionStatement | CAllowThreadsEnd, ...]:
        """Release the GIL only for the native entrypoint call."""
        return (CAllowThreadsBegin(), call, CAllowThreadsEnd())

    def _lower_status_error(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Dispatch one completed post-call Python exception action."""
        policy = plan.binding.status_error
        if policy is None:
            return ()
        if policy.exception_kind is PythonExceptionKind.RUNTIME_ERROR:
            return self._lower_status_error_runtime_error(plan, context)
        raise ValueError(f"Unsupported C status exception for {plan.owner_path!r}: {policy.exception_kind!r}")

    def _lower_status_error_runtime_error(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf | CReturn, ...]:
        """Raise RuntimeError from completed status/message roles with the GIL held."""
        policy = plan.binding.status_error
        status_name = context.native_outputs[policy.status_role]
        condition = CodeExpression(f"{status_name} != {policy.success}")
        derived_cleanup = self._derived_native_storage_cleanup_nodes(
            tuple(result for result in plan.results if result.object_kind is ObjectKind.DERIVED_TYPE),
            context,
        )
        transformation_cleanup = self._binding_transformation_cleanup_nodes(plan, context)
        if policy.message_role is None and policy.message_argument is None:
            return (
                CIf(
                    condition,
                    body=(
                        CExpressionStatement(
                            CodeExpression(
                                f'PyErr_Format(PyExc_RuntimeError, "native call failed with status %d != {policy.success}", '
                                f"(int){status_name})"
                            )
                        ),
                        *transformation_cleanup,
                        *derived_cleanup,
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
            )
        message_capacity: str | None = None
        if policy.message_argument is not None:
            # The caller supplied the buffer, so the binding neither owns nor
            # frees it; it only reads what the native call left behind. The read
            # is bounded by the caller's own capacity because a native writer is
            # not obliged to terminate: Fortran blank-pads fixed-length
            # character storage and never writes a NUL.
            names = context.arguments[policy.message_argument]
            message_name = names.value_name
            message_plan = next(
                argument for argument in plan.arguments if argument.owner_path == policy.message_argument
            )
            message_capacity = (
                f"PyArray_ITEMSIZE((PyArrayObject *){names.object_name})"
                if message_plan.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
                else names.length_name
            )
            binding_owned = True
        else:
            message_name = context.native_outputs[policy.message_role]
            # A binding-owned buffer is never NULL and is never freed here; only
            # the adapter's owned-allocation protocol hands back memory the
            # binding owns.
            binding_owned = any(
                result.character_capacity is not None and result.native_result_role == policy.message_role
                for result in plan.entrypoint.results
            )
            # A hidden message occupies fixed-length native character storage,
            # which Fortran blank-pads to the declared width. Bounding the read
            # by that width drops the padding instead of reporting it.
            if policy.message_character_length is not None:
                message_capacity = str(policy.message_character_length)
        # A visible argument already owns ``<name>_obj`` for its Python object,
        # so the exception string needs a distinct local there.
        message_object = f"{message_name}_status_text" if policy.message_argument is not None else f"{message_name}_obj"
        if binding_owned:
            # Nothing needs freeing, so the Python string is built only on the
            # failure path instead of on every successful call.
            message_value = (
                f"PyUnicode_FromString((const char *){message_name})"
                if message_capacity is None
                else (f"prik_status_message_text((const char *){message_name}, (Py_ssize_t)({message_capacity}))")
            )
            return (
                CIf(
                    condition,
                    body=(
                        CDeclaration(
                            message_object,
                            "PyObject *",
                            CodeExpression(message_value),
                        ),
                        CIf(
                            CodeExpression(f"{message_object} == NULL"),
                            body=(*transformation_cleanup, *derived_cleanup, CReturn(CodeExpression("NULL"))),
                        ),
                        CExpressionStatement(CodeExpression(f"PyErr_SetObject(PyExc_RuntimeError, {message_object})")),
                        CExpressionStatement(CodeExpression(f"Py_DECREF({message_object})")),
                        *transformation_cleanup,
                        *derived_cleanup,
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
            )
        return (
            *(
                ()
                if binding_owned
                else (
                    CIf(
                        CodeExpression(f"{message_name} == NULL"),
                        body=(
                            CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                            *transformation_cleanup,
                            *derived_cleanup,
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                )
            ),
            CDeclaration(
                message_object,
                "PyObject *",
                CodeExpression(
                    f"PyUnicode_FromString((const char *){message_name})"
                    if message_capacity is None
                    else f"prik_status_message_text((const char *){message_name}, (Py_ssize_t)({message_capacity}))"
                ),
            ),
            *(() if binding_owned else (CExpressionStatement(CodeExpression(f"free({message_name})")),)),
            CIf(
                CodeExpression(f"{message_object} == NULL"),
                body=(*transformation_cleanup, *derived_cleanup, CReturn(CodeExpression("NULL"))),
            ),
            CIf(
                condition,
                body=(
                    CExpressionStatement(CodeExpression(f"PyErr_SetObject(PyExc_RuntimeError, {message_object})")),
                    CExpressionStatement(CodeExpression(f"Py_DECREF({message_object})")),
                    *transformation_cleanup,
                    *derived_cleanup,
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CExpressionStatement(CodeExpression(f"Py_DECREF({message_object})")),
        )

    def _writeback_value_nodes(
        self,
        plan: FunctionPlan,
        action: LifecycleActionPlan,
        context: _CFunctionContext,
        converted: tuple[str, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Convert one planned writeback without terminating output aggregation."""
        if action.binding is None:
            raise ValueError(f"Writeback {action.owner_path!r} has no binding policy")
        source = self._argument_for_role(plan, action.source_role)
        if self._publishes_array_replacement(plan, action):
            return self._array_replacement_writeback_nodes(source, action, context)
        if action.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT:
            return self._identity_writeback_value_nodes(source, action, context, converted)
        if action.binding.codegen_action is CodegenAction.COPY_IN_OUT:
            if action.binding.datatype_family is DatatypeFamily.STRING:
                return self._mixed_string_writeback_nodes(plan, action, context, converted)
            return self._scalar_writeback_value_nodes(source, action, context, converted)
        raise ValueError(f"Unsupported C writeback action for {action.owner_path!r}: {action.binding.codegen_action!r}")

    def _identity_writeback_value_nodes(
        self,
        source: ArgumentTransferPlan,
        action: LifecycleActionPlan,
        context: _CFunctionContext,
        converted: tuple[str, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Retain the exact mutable Python object selected by completed policy."""
        target = context.python_results[action.owner_path]
        if source.derived_call is not None and source.derived_call.writeback in {
            DerivedWriteback.ALLOCATION_STATE,
            DerivedWriteback.POINTER_ASSOCIATION,
        }:
            return self._holder_writeback_value_nodes(source, target, converted, context)
        source_object = context.arguments[source.owner_path].object_name
        return (
            CDeclaration(target, "PyObject *", CodeExpression(source_object)),
            CExpressionStatement(CodeExpression(f"Py_INCREF({target})")),
        )

    def _array_replacement_writeback_nodes(
        self,
        source: ArgumentTransferPlan,
        action: LifecycleActionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Transfer one binding-owned mutable NumPy replacement to Python."""
        names = context.arguments[source.owner_path]
        temporary = self._array_transformation_temp_name(names)
        target = context.python_results[action.owner_path]
        return (
            CDeclaration(target, "PyObject *", CodeExpression(temporary)),
            CExpressionStatement(CodeExpression(f"{temporary} = NULL")),
        )

    def _scalar_writeback_value_nodes(
        self,
        source: ArgumentTransferPlan,
        action: LifecycleActionPlan,
        context: _CFunctionContext,
        converted: tuple[str, ...],
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Convert one mutated scalar storage value for combined aggregation."""
        names = context.arguments[source.owner_path]
        scalar_type = PrimitiveScalarTypeRegistry.type_for(action.binding.semantic_type_name)
        target = context.python_results[action.owner_path]
        cleanup = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in converted)
        conversion = CExpressionStatement(
            CodeExpression(f"{target} = {self._scalar_result_expression(scalar_type, f'&{names.value_name}')}")
        )
        failure = CIf(CodeExpression(f"{target} == NULL"), body=(*cleanup, CReturn(CodeExpression("NULL"))))
        if source.entrypoint.descriptor_output_presence_role is None:
            return (CDeclaration(target, "PyObject *", CodeExpression("NULL")), conversion, failure)
        return (
            CDeclaration(target, "PyObject *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"!{self._descriptor_output_present_name(names)}"),
                body=(
                    CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")),
                    CExpressionStatement(CodeExpression(f"{target} = Py_None")),
                ),
                else_body=(conversion, failure),
            ),
        )

    def _publishes_array_replacement(
        self,
        plan: FunctionPlan,
        action: LifecycleActionPlan,
    ) -> bool:
        """Return whether completed COPY_OUT policy transfers a NumPy temporary."""
        source = self._argument_for_role(plan, action.source_role)
        return any(
            transformation.phase is WritebackPhase.COPY_OUT
            and transformation.action is TransformationAction.PUBLISH_ARRAY_REPLACEMENT
            for transformation in source.transformations
        )

    def _holder_writeback_value_nodes(
        self,
        source: ArgumentTransferPlan,
        result: str,
        converted: tuple[str, ...],
        context: _CFunctionContext,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Preserve an existing holder or publish one created from Python None."""
        if source.derived is None or source.derived_call is None:
            raise ValueError(f"Derived holder writeback {source.owner_path!r} is incomplete")
        names = context.arguments[source.owner_path]
        storage = (
            DerivedObjectStorage.ALLOCATABLE_HOLDER
            if source.derived_call.writeback is DerivedWriteback.ALLOCATION_STATE
            else DerivedObjectStorage.POINTER_HOLDER
        )
        _, _, destroy_name, _, _ = self._holder_wrapper_symbols(source.derived.backend_symbol, storage)
        cleanup = tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in converted)
        return (
            CDeclaration(result, "PyObject *", CodeExpression("NULL")),
            CIf(
                CodeExpression(f"{names.object_name} != Py_None"),
                body=(
                    CExpressionStatement(CodeExpression(f"Py_INCREF({names.object_name})")),
                    CExpressionStatement(CodeExpression(f"{result} = {names.object_name}")),
                ),
                else_body=(
                    CIf(
                        CodeExpression(f"!{self._descriptor_output_present_name(names)}"),
                        body=(
                            CIf(
                                CodeExpression(f"{names.value_name} != NULL"),
                                body=(CExpressionStatement(CodeExpression(f"{destroy_name}({names.value_name})")),),
                            ),
                            CExpressionStatement(CodeExpression("Py_INCREF(Py_None)")),
                            CExpressionStatement(CodeExpression(f"{result} = Py_None")),
                        ),
                        else_body=self._holder_wrapper_nodes(
                            source.derived.type_name,
                            source.derived.backend_symbol,
                            storage,
                            self._derived_target_owner(source.derived),
                            names.value_name,
                            result,
                            cleanup,
                        ),
                    ),
                ),
            ),
        )

    @staticmethod
    def _descriptor_output_present_name(names: _CArgumentNames) -> str:
        """Name the binding-local final descriptor-state flag."""
        return f"{names.value_name}_descriptor_output_present"

    @staticmethod
    def _holder_allocation_status_name(names: _CArgumentNames) -> str:
        """Return the binding-local holder allocation status name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"{names.value_name}_holder_allocation_status"

    def _argument_for_role(self, plan: FunctionPlan, role: str) -> ArgumentTransferPlan:
        """Return the argument that produced one validated lifecycle role."""
        for argument in plan.arguments:
            if argument.entrypoint.handoff_role == role:
                return argument
        raise ValueError(f"{plan.owner_path!r} has no argument for lifecycle role {role!r}")

    def _function_context(self, plan: FunctionPlan) -> _CFunctionContext:
        """Build function context from the supplied completed binding records; emitted nodes only project completed binding actions."""
        arguments = self._argument_contexts(plan)
        native_outputs = self._native_output_names(plan)
        output_owners = self._output_owners(plan)
        python_results = self._python_result_names(output_owners)
        python_result = self._python_result_name(plan)
        native_result = self._native_result_name(plan)
        role_values = self._argument_role_values(plan, arguments)
        return _CFunctionContext(
            arguments,
            native_outputs,
            native_result,
            python_result,
            python_results,
            role_values,
        )

    def _argument_contexts(self, plan: FunctionPlan) -> dict[str, _CArgumentNames]:
        """Name the binding locals for every Python argument."""
        return {argument.owner_path: self._argument_context_names(argument) for argument in plan.arguments}

    def _native_output_names(self, plan: FunctionPlan) -> dict[str, str]:
        """Name native hidden-output locals by their completed symbolic roles."""
        return {
            result.native_result_role: result.parameter_name
            for result in plan.entrypoint.results
            if result.source_kind == "hidden_output" and result.parameter_name is not None
        }

    def _output_owners(self, plan: FunctionPlan) -> tuple[tuple[str, int], ...]:
        """Return every result and writeback owner in public result order."""
        results = tuple(sorted(plan.results, key=lambda item: item.result_position))
        writebacks = self._ordered_output_writebacks(plan)
        return tuple(
            sorted(
                (
                    *((result.owner_path, result.result_position) for result in results),
                    *((action.owner_path, action.binding.result_position) for action in writebacks),
                ),
                key=lambda item: item[1],
            )
        )

    def _ordered_output_writebacks(self, plan: FunctionPlan) -> tuple[LifecycleActionPlan, ...]:
        """Return copy-out writebacks ordered by their completed result positions."""
        actions = (
            action
            for action in plan.writeback_actions
            if action.phase is WritebackPhase.COPY_OUT and action.binding is not None
        )
        return tuple(sorted(actions, key=lambda action: action.binding.result_position))

    def _python_result_names(self, output_owners: tuple[tuple[str, int], ...]) -> dict[str, str]:
        """Name one Python result local per ordered output owner."""
        single_output = len(output_owners) == 1
        return {
            owner_path: ("result_obj" if single_output else f"result_{position}_obj")
            for owner_path, position in output_owners
        }

    def _python_result_name(self, plan: FunctionPlan) -> str | None:
        """Return the aggregate Python result local only when output exists."""
        return "result_obj" if plan.results or plan.writeback_actions else None

    def _native_result_name(self, plan: FunctionPlan) -> str | None:
        """Return the direct native result local only for native functions."""
        return "result" if self._direct_result(plan) is not None else None

    def _argument_role_values(
        self,
        plan: FunctionPlan,
        arguments: dict[str, _CArgumentNames],
    ) -> dict[str, str]:
        """Map completed handoff roles to their binding value locals."""
        values = {
            argument.entrypoint.handoff_role: self._argument_role_value(
                argument,
                arguments[argument.owner_path].value_name,
            )
            for argument in plan.arguments
        }
        values.update(
            {
                role: arguments[argument.owner_path].extent_names[axis]
                for argument in plan.arguments
                if argument.array is not None
                for axis, role in enumerate(argument.array.extent_roles)
            }
        )
        return values

    @staticmethod
    def _argument_role_value(argument: ArgumentTransferPlan, value_name: str) -> str:
        """Expose scalar-storage roles as values in dependent shape expressions."""
        if argument.binding.python_action is not PythonBarrierAction.SCALAR_STORAGE:
            return value_name
        scalar_type = PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name)
        return f"(*(({scalar_type.c_spelling} *){value_name}))"

    def _argument_context_names(self, argument: ArgumentTransferPlan) -> _CArgumentNames:
        """Name one argument's binding locals in the binding-private namespace."""
        name = argument.binding.python_name.lower()
        local = f"bound_{name}"
        rank = (
            15
            if argument.array is not None and argument.array.rank is None
            else (argument.array.rank if argument.array is not None else 0)
        )
        return _CArgumentNames(
            f"{local}_obj",
            local,
            f"{local}_length",
            f"{local}_nullable",
            f"{local}_present",
            tuple(f"{local}_extent_{axis}" for axis in range(rank)),
            tuple(f"{local}_upper_bound_{axis}" for axis in range(rank)),
            tuple(f"{local}_stride_{axis}" for axis in range(rank)),
            f"{local}_dense_actual",
            f"{local}_rank",
            f"{local}_itemsize",
            f"{local}_polymorphic",
        )

    def _keyword_declarations(self, plan: FunctionPlan) -> tuple[CDeclaration, ...]:
        """Return the keyword table one wrapper needs, or nothing when it takes none."""
        if not plan.binding.accepts_keyword_arguments:
            return ()
        return (self._keyword_declaration(plan),)

    def _keyword_declaration(self, plan: FunctionPlan) -> CDeclaration:
        """Build keyword declaration from the supplied completed binding records; emitted nodes only project completed binding actions."""
        keywords = ", ".join(
            f'"{argument.binding.python_name}"'
            for argument in sorted(plan.arguments, key=lambda item: item.python_position)
        )
        entries = f"{keywords}, NULL" if keywords else "NULL"
        return CDeclaration("kwlist[]", "static char *", CodeExpression(f"{{{entries}}}"))

    def _parse_statement(self, plan: FunctionPlan, context: _CFunctionContext) -> CExpressionStatement:
        """Return parse statement from the supplied completed binding records; this helper preserves the selected binding behavior."""
        arguments = sorted(plan.arguments, key=lambda item: item.python_position)
        required_modes = {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR}
        required = [item for item in arguments if item.binding.optional_mode in required_modes]
        optional = [item for item in arguments if item.binding.optional_mode not in required_modes]
        units = "O" * len(required) + ("|" if optional else "") + "O" * len(optional)
        targets = ", ".join(f"&{context.arguments[item.owner_path].object_name}" for item in arguments)
        suffix = f", {targets}" if targets else ""
        if not plan.binding.accepts_keyword_arguments:
            return CExpressionStatement(CodeExpression(f'if (!PyArg_ParseTuple(args, "{units}"{suffix})) return NULL'))
        return CExpressionStatement(
            CodeExpression(f'if (!PyArg_ParseTupleAndKeywords(args, kwargs, "{units}", kwlist{suffix})) return NULL')
        )

    def _direct_result_declaration(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration, ...]:
        """Build direct result declaration from the supplied completed binding records; emitted nodes only project completed binding actions."""
        result = self._direct_result(plan)
        if result is None or context.result_name is None:
            return ()
        if result.scalar_descriptor is not None:
            declarations = [
                CDeclaration(context.result_name, "void *", CodeExpression("NULL")),
                CDeclaration(f"{context.result_name}_present", "int", CodeExpression("0")),
            ]
            if result.scalar_descriptor.runtime_length:
                declarations.append(CDeclaration(f"{context.result_name}_length", "int64_t", CodeExpression("0")))
            return tuple(declarations)
        if self._is_owned_native_array_result(result):
            if self._is_owned_deferred_character_result(result):
                rank = result.native_array_handle.array.rank
                return (
                    CDeclaration(context.result_name, "void *", CodeExpression("NULL")),
                    CDeclaration(f"{context.result_name}_itemsize", "int64_t", CodeExpression("0")),
                    *(
                        CDeclaration(f"{context.result_name}_extent_{axis}", "int64_t", CodeExpression("0"))
                        for axis in range(rank)
                    ),
                    CDeclaration(
                        f"{context.result_name}_owner_descriptor",
                        "CFI_cdesc_t *",
                        CodeExpression("NULL"),
                    ),
                    CDeclaration(
                        f"{context.result_name}_owner_status",
                        "int",
                        CodeExpression("CFI_SUCCESS"),
                    ),
                )
            return (
                CDeclaration(context.result_name, "CFI_cdesc_t *", CodeExpression("NULL")),
                CDeclaration(f"{context.result_name}_owner_status", "int", CodeExpression("CFI_SUCCESS")),
            )
        if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return (CDeclaration(context.result_name, "void *", CodeExpression("NULL")),)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name)
        return (CDeclaration(context.result_name, scalar_type.c_spelling),)

    def _declaration_extent_result_declarations(self, plan: FunctionPlan) -> tuple[CDeclaration, ...]:
        """Declare storage populated by native-dependent main-bridge extent outputs."""
        return tuple(
            CDeclaration(
                self._declaration_extent_result_name(result, axis),
                "int64_t",
                CodeExpression("0"),
            )
            for result in plan.results
            if result.array is not None
            for axis, evaluation in enumerate(result.array.extent_evaluation)
            if evaluation == "bridge"
        )

    def _native_output_declarations(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CDeclaration, ...]:
        """Declare C storage for every hidden entrypoint result."""
        declarations = []
        for result in self._entrypoint_hidden_results(plan):
            name = context.native_outputs[result.native_result_role]
            if result.scalar_descriptor is not None:
                declarations.append(CDeclaration(name, "void *", CodeExpression("NULL")))
                declarations.append(CDeclaration(f"{name}_present", "int", CodeExpression("0")))
                if result.scalar_descriptor.runtime_length:
                    declarations.append(CDeclaration(f"{name}_length", "int64_t", CodeExpression("0")))
                continue
            if self._is_owned_native_array_result(result):
                if self._is_owned_deferred_character_result(result):
                    rank = result.native_array_handle.array.rank
                    declarations.extend(
                        (
                            CDeclaration(name, "void *", CodeExpression("NULL")),
                            CDeclaration(f"{name}_itemsize", "int64_t", CodeExpression("0")),
                            *(
                                CDeclaration(f"{name}_extent_{axis}", "int64_t", CodeExpression("0"))
                                for axis in range(rank)
                            ),
                            CDeclaration(
                                f"{name}_owner_descriptor",
                                "CFI_cdesc_t *",
                                CodeExpression("NULL"),
                            ),
                            CDeclaration(f"{name}_owner_status", "int", CodeExpression("CFI_SUCCESS")),
                        )
                    )
                    continue
                declarations.extend(
                    (
                        CDeclaration(name, "CFI_cdesc_t *", CodeExpression("NULL")),
                        CDeclaration(f"{name}_owner_status", "int", CodeExpression("CFI_SUCCESS")),
                    )
                )
                continue
            if result.character_capacity is not None:
                # One extra byte so a callee that terminates its own output
                # cannot write past the buffer the contract asked for.
                declarations.append(
                    CDeclaration(f"{name}[{result.character_capacity + 1}]", "char", CodeExpression("{0}"))
                )
                continue
            if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
                declarations.append(CDeclaration(name, "void *", CodeExpression("NULL")))
                continue
            scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name)
            declarations.append(CDeclaration(name, result.native_scalar_c_type or scalar_type.c_spelling))
        return tuple(declarations)

    def _native_call_setup_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Allocate persistent standard-descriptor storage selected by result plans."""
        nodes = list(self._binding_transformation_setup_nodes(plan, context))
        initialized = []
        transformation_cleanup = self._binding_transformation_cleanup_nodes(plan, context)
        for result in sorted(plan.results, key=lambda item: item.result_position):
            if not self._is_owned_native_array_result(result):
                continue
            if self._is_owned_deferred_character_result(result):
                continue
            descriptor = self._result_native_name(result, context)
            handle = result.native_array_handle
            if handle is None or handle.array.rank is None:
                raise ValueError(f"Owned result {result.owner_path!r} is missing descriptor facts")
            cfi_type = self._native_array_cfi_type(result)
            if cfi_type is None:
                raise ValueError(f"Owned result {result.owner_path!r} is missing a CFI element type")
            elem_len = f"sizeof({PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name).c_spelling})"
            cleanup = tuple(
                node
                for previous_result, previous_descriptor in reversed(initialized)
                for node in self._owned_descriptor_failure_cleanup(previous_result, previous_descriptor)
            )
            nodes.extend(
                (
                    CExpressionStatement(
                        CodeExpression(f"{descriptor} = {self._zeroed_descriptor_allocation(handle.array.rank)}")
                    ),
                    CIf(
                        CodeExpression(f"{descriptor} == NULL"),
                        body=(
                            *transformation_cleanup,
                            *cleanup,
                            CExpressionStatement(CodeExpression("PyErr_NoMemory()")),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                    CExpressionStatement(
                        CodeExpression(
                            f"{descriptor}_owner_status = CFI_establish({descriptor}, NULL, "
                            f"{self._owned_native_array_cfi_attribute(handle)}, {cfi_type}, {elem_len}, "
                            f"{handle.array.rank}, NULL)"
                        )
                    ),
                    CIf(
                        CodeExpression(f"{descriptor}_owner_status != CFI_SUCCESS"),
                        body=(
                            CExpressionStatement(CodeExpression(f"free({descriptor})")),
                            CExpressionStatement(CodeExpression(f"{descriptor} = NULL")),
                            *transformation_cleanup,
                            *cleanup,
                            CExpressionStatement(
                                CodeExpression(
                                    'PyErr_SetString(PyExc_RuntimeError, "failed to establish owned native array '
                                    'descriptor storage")'
                                )
                            ),
                            CReturn(CodeExpression("NULL")),
                        ),
                    ),
                )
            )
            initialized.append((result, descriptor))
        return tuple(nodes)

    @staticmethod
    def _owned_native_array_cfi_attribute(handle: NativeArrayHandlePlan) -> str:
        """Return the CFI descriptor attribute selected by completed policy."""
        if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
            return "CFI_attribute_pointer"
        return "CFI_attribute_allocatable"

    @staticmethod
    def _zeroed_descriptor_allocation(rank: int) -> str:
        """Allocate initialized CFI storage so native runtimes never inspect padding."""
        return f"(CFI_cdesc_t *)calloc(1, sizeof(CFI_CDESC_T({rank})))"

    @staticmethod
    def _native_array_handle_kind_constant(handle: NativeArrayHandlePlan) -> str:
        """Return the common-header descriptor-kind constant."""
        if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
            return "PRIK_NATIVE_ARRAY_KIND_POINTER"
        return "PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE"

    @staticmethod
    def _native_array_expected_element_size(plan: ArgumentTransferPlan | ResultPlan) -> str:
        """Return a fixed element-size check or zero for runtime-width strings."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "0"
        return f"sizeof({PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).c_spelling})"

    def _native_array_capsule_new_expression(
        self,
        plan: ArgumentTransferPlan | ResultPlan,
        descriptor: str,
    ) -> str:
        """Create one versioned capsule around established descriptor storage."""
        handle = plan.native_array_handle
        cfi_type = self._native_array_cfi_type(plan)
        element_size = (
            f"{descriptor}->elem_len"
            if plan.datatype_family is DatatypeFamily.STRING
            else self._native_array_expected_element_size(plan)
        )
        return (
            "prik_native_array_handle_capsule_new("
            f"{self._native_array_handle_kind_constant(handle)}, {handle.array.rank}, {cfi_type}, "
            f"{element_size}, sizeof(CFI_CDESC_T({handle.array.rank})), {descriptor}, "
            f"{self._native_array_capsule_release_name(plan)})"
        )

    # Binding-owned representation transformations.
    def _binding_transformation_setup_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Create planned NumPy temporaries after every source argument is validated."""
        nodes = []
        initialized: list[str] = []
        for argument in plan.arguments:
            if not argument.transformations:
                continue
            names = context.arguments[argument.owner_path]
            temporary = self._array_transformation_temp_name(names)
            source = f"(PyArrayObject *){names.object_name}"
            copy_in = self._has_transformation_phase(argument, WritebackPhase.COPY_IN)
            expression = (
                f"PyArray_NewCopy({source}, NPY_FORTRANORDER)"
                if copy_in
                else f"PyArray_EMPTY(PyArray_NDIM({source}), PyArray_DIMS({source}), PyArray_TYPE({source}), 1)"
            )
            prior_cleanup = tuple(
                CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in reversed(initialized)
            )
            nodes.extend(
                (
                    CExpressionStatement(CodeExpression(f"{temporary} = {expression}")),
                    CIf(
                        CodeExpression(f"{temporary} == NULL"),
                        body=(*prior_cleanup, CReturn(CodeExpression("NULL"))),
                    ),
                    CExpressionStatement(
                        CodeExpression(f"{names.value_name} = PyArray_DATA((PyArrayObject *){temporary})")
                    ),
                )
            )
            initialized.append(temporary)
        return tuple(nodes)

    def _binding_transformation_post_call_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement | CIf, ...]:
        """Copy back ordinary temporaries and retain published replacements."""
        nodes = []
        cleanup = self._binding_transformation_cleanup_nodes(plan, context)
        for argument in plan.arguments:
            action = self._transformation_action(argument, WritebackPhase.COPY_OUT)
            if action is not TransformationAction.COPY_ARRAY_REPRESENTATION:
                continue
            names = context.arguments[argument.owner_path]
            temporary = self._array_transformation_temp_name(names)
            nodes.append(
                CIf(
                    CodeExpression(
                        f"PyArray_CopyInto((PyArrayObject *){names.object_name}, (PyArrayObject *){temporary}) < 0"
                    ),
                    body=(*cleanup, CReturn(CodeExpression("NULL"))),
                )
            )
        nodes.extend(self._binding_transformation_success_cleanup_nodes(plan, context))
        return tuple(nodes)

    def _binding_transformation_success_cleanup_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement, ...]:
        """Release temporaries whose successful path does not publish ownership."""
        return tuple(
            CExpressionStatement(
                CodeExpression(
                    f"Py_XDECREF({self._array_transformation_temp_name(context.arguments[item.owner_path])})"
                )
            )
            for item in reversed(plan.arguments)
            if self._has_transformation_phase(item, WritebackPhase.CLEANUP)
            and self._transformation_action(item, WritebackPhase.COPY_OUT)
            is not TransformationAction.PUBLISH_ARRAY_REPLACEMENT
        )

    def _binding_transformation_cleanup_nodes(
        self,
        plan: FunctionPlan,
        context: _CFunctionContext,
    ) -> tuple[CExpressionStatement, ...]:
        """Release every planned binding temporary exactly once."""
        return tuple(
            CExpressionStatement(
                CodeExpression(
                    f"Py_XDECREF({self._array_transformation_temp_name(context.arguments[item.owner_path])})"
                )
            )
            for item in reversed(plan.arguments)
            if self._has_transformation_phase(item, WritebackPhase.CLEANUP)
        )

    @staticmethod
    def _has_transformation_phase(argument: ArgumentTransferPlan, phase: WritebackPhase) -> bool:
        """Return whether one completed transfer owns an action in a lifecycle phase."""
        return any(transformation.phase is phase for transformation in argument.transformations)

    @staticmethod
    def _transformation_action(
        argument: ArgumentTransferPlan,
        phase: WritebackPhase,
    ) -> TransformationAction | None:
        """Return the sole completed transformation action for one lifecycle phase."""
        actions = tuple(
            transformation.action for transformation in argument.transformations if transformation.phase is phase
        )
        if len(actions) > 1:
            raise ValueError(f"Argument {argument.owner_path!r} has repeated {phase.value} transformations")
        return actions[0] if actions else None

    @staticmethod
    def _array_transformation_temp_name(names: _CArgumentNames) -> str:
        """Name the binding-owned NumPy representation temporary."""
        return f"{names.value_name}_representation"

    def _owned_descriptor_failure_cleanup(
        self,
        result: ResultPlan,
        descriptor_name: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Release unpublished descriptor storage without releasing pointer targets."""
        handle = result.native_array_handle
        payload_release = ""
        if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE:
            payload_release = f"if ({descriptor_name}->base_addr != NULL) (void)CFI_deallocate({descriptor_name}); "
        return (
            CExpressionStatement(
                CodeExpression(
                    f"if ({descriptor_name} != NULL) {{ {payload_release}free({descriptor_name}); "
                    f"{descriptor_name} = NULL; }}"
                )
            ),
        )

    @staticmethod
    def _decref_names(names: tuple[str, ...]) -> tuple[CExpressionStatement, ...]:
        """Release already-created Python result objects on a later failure."""
        return tuple(CExpressionStatement(CodeExpression(f"Py_DECREF({name})")) for name in names)

    @staticmethod
    def _is_owned_native_array_result(result: ResultPlan | NativeEntrypointResultPlan) -> bool:
        """Return whether one result owns persistent standard-descriptor storage."""
        handle = result.native_array_handle
        return handle is not None and handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE

    @classmethod
    def _is_owned_deferred_character_result(cls, result: ResultPlan | NativeEntrypointResultPlan) -> bool:
        """Return whether owner storage needs runtime character-width materialization."""
        return cls._is_owned_native_array_result(result) and result.datatype_family is DatatypeFamily.STRING

    def _owned_result_descriptor_name(self, result: ResultPlan, context: _CFunctionContext) -> str:
        """Return persistent owner storage after any deferred-character materialization."""
        native_name = self._result_native_name(result, context)
        if self._is_owned_deferred_character_result(result):
            return f"{native_name}_owner_descriptor"
        return native_name

    def _entrypoint_call(self, plan: FunctionPlan, context: _CFunctionContext) -> str:
        """Return the call assembled in planned entrypoint-parameter order."""
        arguments = [
            value
            for parameter in sorted(plan.entrypoint.parameters, key=lambda item: item.position)
            for value in self._entrypoint_parameter_values(plan, parameter, context)
        ]
        return f"{self._entrypoint_function_name(plan)}({', '.join(arguments)})"

    def _entrypoint_parameter_values(
        self,
        plan: FunctionPlan,
        parameter: NativeEntrypointParameterPlan,
        context: _CFunctionContext,
    ) -> tuple[str, ...]:
        """Lower one planned C-ABI parameter group to binding call actuals."""
        if parameter.source_kind == "argument":
            argument = self._argument_by_owner(plan, parameter.owner_path)
            names = context.arguments[argument.owner_path]
            slot = self._projected_slot_for_parameter(plan, parameter)
            values = list(
                self._entrypoint_argument_values(
                    argument,
                    names,
                    passing=slot.passing,
                )
            )
            if argument.entrypoint.pass_descriptor_presence:
                values.append(names.present_name)
            if argument.entrypoint.descriptor_output_role is not None:
                values.extend((f"&{names.value_name}", f"&{self._descriptor_output_present_name(names)}"))
            if slot.native_scalar_c_type is not None and slot.passing is EntrypointPassingConvention.C_VALUE:
                values[0] = f"({slot.native_scalar_c_type}){values[0]}"
            return tuple(values)
        if parameter.source_kind == "projected_slot":
            return self._projected_slot_values(
                plan,
                self._projected_slot_for_parameter(plan, parameter),
                context,
            )
        result = self._entrypoint_result_by_owner(plan, parameter.owner_path)
        if parameter.source_kind == "hidden_result":
            name = context.native_outputs[result.native_result_role]
            return self._entrypoint_hidden_result_values(result, name)
        if parameter.source_kind == "direct_result":
            return self._entrypoint_direct_result_values(result, context)
        if parameter.source_kind == "declaration_extent":
            return self._declaration_extent_result_values_for_result(result)
        raise ValueError(f"Unsupported entrypoint parameter group {parameter.source_kind!r}")

    @staticmethod
    def _argument_by_owner(plan: FunctionPlan, owner_path: str) -> ArgumentTransferPlan:
        """Return the argument referenced by one entrypoint parameter group."""
        return next(argument for argument in plan.arguments if argument.owner_path == owner_path)

    @staticmethod
    def _entrypoint_result_by_owner(plan: FunctionPlan, owner_path: str) -> NativeEntrypointResultPlan:
        """Return the C-ABI result referenced by one parameter group."""
        return next(result for result in plan.entrypoint.results if result.owner_path == owner_path)

    @staticmethod
    def _projected_slot_for_parameter(
        plan: FunctionPlan,
        parameter: NativeEntrypointParameterPlan,
    ) -> NativeEntrypointProjectedSlotPlan:
        """Return the authoritative projected slot referenced by one C ABI group."""
        return next(
            slot for slot in plan.entrypoint.projected_slots if slot.native_position == parameter.native_position
        )

    def _projected_slot_values(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
        context: _CFunctionContext,
    ) -> tuple[str, ...]:
        """Materialize one non-argument projected actual in the C binding."""
        if slot.projection_action is EntrypointProjectionAction.TYPED_LITERAL:
            return (self._projected_literal_expression(slot),)
        if slot.python_position is None:
            raise ValueError(f"Projected slot {slot.owner_path!r} has no binding source")
        argument = next(item for item in plan.arguments if item.python_position == slot.python_position)
        names = context.arguments[argument.owner_path]
        if slot.projection_action is EntrypointProjectionAction.COMPUTED_LENGTH:
            return (f"(size_t){names.length_name}",)
        if slot.projection_action is EntrypointProjectionAction.COMPUTED_PRESENCE:
            return (f"({names.nullable_name} != NULL)",)
        if not isinstance(slot.literal_value, Mapping):
            raise ValueError(f"Projected array fact {slot.owner_path!r} has no axis metadata")
        axis = slot.literal_value.get("dim")
        if not isinstance(axis, int):
            raise ValueError(f"Projected array fact {slot.owner_path!r} has no integer axis")
        if slot.projection_action is EntrypointProjectionAction.COMPUTED_SHAPE:
            return (f"(size_t)PyArray_DIM((PyArrayObject *){names.object_name}, {axis})",)
        if slot.projection_action is EntrypointProjectionAction.COMPUTED_STRIDE:
            return (f"(size_t)PyArray_STRIDE((PyArrayObject *){names.object_name}, {axis})",)
        raise ValueError(f"Unsupported projected C actual {slot.projection_action.value!r}")

    @staticmethod
    def _projected_slot_parameters(
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[CParameter, ...]:
        """Declare one binding-materialized projected C ABI value."""
        if slot.semantic_type_name is None:
            raise ValueError(f"Projected slot {slot.owner_path!r} has no semantic type")
        scalar_type = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name).c_spelling
        if slot.passing in {
            EntrypointPassingConvention.POINTER_REFERENCE,
            EntrypointPassingConvention.NULLABLE_POINTER,
        }:
            scalar_type = f"{scalar_type} *"
        elif slot.passing is not EntrypointPassingConvention.C_VALUE:
            raise ValueError(f"Unsupported projected C parameter passing {slot.passing.value!r}")
        return (CParameter(slot.native_name.casefold(), scalar_type),)

    @staticmethod
    def _projected_literal_expression(slot: NativeEntrypointProjectedSlotPlan) -> str:
        """Render one typed literal as a C call-site value."""
        value = slot.literal_value
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, complex):
            return f"({value.real!r} + {value.imag!r} * I)"
        if isinstance(value, (int, float)):
            return repr(value)
        raise ValueError(f"Unsupported projected C literal {value!r}")

    def _entrypoint_hidden_results(self, plan: FunctionPlan) -> tuple[NativeEntrypointResultPlan, ...]:
        """Return hidden results in planned C-ABI parameter-group order."""
        return tuple(
            self._entrypoint_result_by_owner(plan, parameter.owner_path)
            for parameter in sorted(plan.entrypoint.parameters, key=lambda item: item.position)
            if parameter.source_kind == "hidden_result"
        )

    def _declaration_extent_result_values_for_result(
        self,
        result: NativeEntrypointResultPlan,
    ) -> tuple[str, ...]:
        """Return extent output actuals for one planned result group."""
        if result.array is None:
            return ()
        return tuple(
            f"&{self._declaration_extent_result_name(result, axis)}"
            for axis, evaluation in enumerate(result.array.extent_evaluation)
            if evaluation == "bridge"
        )

    def _entrypoint_hidden_result_values(
        self,
        result: NativeEntrypointResultPlan,
        name: str,
    ) -> tuple[str, ...]:
        """Return ABI pointers for one hidden output slot."""
        if self._is_owned_deferred_character_result(result):
            rank = result.native_array_handle.array.rank
            return (
                f"&{name}",
                f"&{name}_itemsize",
                *(f"&{name}_extent_{axis}" for axis in range(rank)),
            )
        if result.character_capacity is not None:
            return (name,)
        values = [name if self._is_owned_native_array_result(result) else f"&{name}"]
        if result.scalar_descriptor is not None:
            values.append(f"&{name}_present")
            if result.scalar_descriptor.runtime_length:
                values.append(f"&{name}_length")
        return tuple(values)

    def _entrypoint_direct_result_values(
        self,
        result: NativeEntrypointResultPlan,
        context: _CFunctionContext,
    ) -> tuple[str, ...]:
        """Return helper ABI actuals for one planned direct-result group."""
        if self._is_owned_native_array_result(result):
            if context.result_name is None:
                raise ValueError(f"Owned direct result {result.owner_path!r} has no C storage")
            if self._is_owned_deferred_character_result(result):
                rank = result.native_array_handle.array.rank
                return (
                    f"&{context.result_name}",
                    f"&{context.result_name}_itemsize",
                    *(f"&{context.result_name}_extent_{axis}" for axis in range(rank)),
                )
            return (context.result_name,)
        if result.scalar_descriptor is None:
            return ()
        values = [f"&{context.result_name}_present"]
        if result.scalar_descriptor.runtime_length:
            values.append(f"&{context.result_name}_length")
        return tuple(values)

    def _entrypoint_argument_values(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        *,
        passing: EntrypointPassingConvention,
    ) -> tuple[str, ...]:
        """Return one binding-to-entrypoint C handoff, including helper ABI fields."""
        if plan.callback is not None:
            if not plan.entrypoint.pass_callback_parameter:
                return ()
            return (plan.callback.entrypoint.support_procedure.symbol_name,)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER:
            return self._string_entrypoint_argument_values(plan, names, passing=passing)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._array_entrypoint_argument_values(plan, names)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return (names.value_name,)
        return self._scalar_entrypoint_argument_values(plan, names, passing=passing)

    # Scalar entrypoint call arguments.
    def _scalar_entrypoint_argument_values(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        *,
        passing: EntrypointPassingConvention,
    ) -> tuple[str, ...]:
        """Return one scalar value, storage, address, or optional handoff."""
        if plan.derived_call is not None:
            if not plan.entrypoint.pass_derived_transaction:
                return (names.value_name,)
            ops = self._derived_ops_name(names)
            return (
                names.value_name,
                self._derived_access_name(names),
                self._derived_identity_name(names),
                *((names.polymorphic_name,) if plan.polymorphic is not None else ()),
                f"{ops} != NULL ? {ops}->scoped : NULL",
                f"{ops} != NULL ? {ops}->checkout : NULL",
                f"{ops} != NULL ? {ops}->restore : NULL",
                f"&{self._derived_status_name(names)}",
            )
        if plan.entrypoint.optional_mode is not OptionalMode.REQUIRED:
            return (names.nullable_name,)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            if plan.entrypoint.pass_character_length:
                # Assumed-capacity storage reports the caller's own itemsize.
                return (
                    names.value_name,
                    f"(int64_t)PyArray_ITEMSIZE((PyArrayObject *){names.object_name})",
                )
            return (names.value_name,)
        if passing is EntrypointPassingConvention.C_VALUE:
            return (names.value_name,)
        if passing is EntrypointPassingConvention.POINTER_REFERENCE:
            return (f"&{names.value_name}",)
        if passing is not plan.entrypoint.passing:
            raise ValueError(f"Unsupported projected scalar passing convention {passing.value!r}")
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            return (names.value_name,)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.TYPED_REFERENCE:
            return (f"&{names.value_name}",)
        return (names.value_name,)

    # String entrypoint call arguments.
    def _string_entrypoint_argument_values(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
        *,
        passing: EntrypointPassingConvention,
    ) -> tuple[str, ...]:
        """Return one scalar string pointer-and-length handoff."""
        values = [
            f"*{names.value_name}"
            if not plan.entrypoint.pass_character_length and passing is EntrypointPassingConvention.C_VALUE
            else names.value_name
        ]
        if plan.entrypoint.pass_character_length:
            values.append(f"(int64_t){names.length_name}")
        return tuple(values)

    # Ordinary-array entrypoint call arguments.
    def _array_entrypoint_argument_values(
        self,
        plan: ArgumentTransferPlan,
        names: _CArgumentNames,
    ) -> tuple[str, ...]:
        """Return one completed ordinary-array C ABI field sequence."""
        handoff = plan.array
        if handoff is None:
            raise ValueError(f"Array argument {plan.owner_path!r} has no handoff spec")
        arguments = [names.value_name]
        if not plan.entrypoint.pass_array_metadata:
            return tuple(arguments)
        if handoff.runtime_rank_role is not None:
            arguments.append(names.runtime_rank_name)
        if handoff.itemsize_role is not None:
            arguments.append(names.itemsize_name)
        if handoff.dense_actual_role is not None:
            arguments.append(names.dense_actual_name)
        arguments.extend(names.extent_names)
        arguments.extend(self._selected_array_axis_names(names.upper_bound_names, handoff.upper_bound_roles))
        arguments.extend(self._selected_array_axis_names(names.stride_names, handoff.stride_roles))
        return tuple(arguments)

    def _selected_array_axis_names(self, names: tuple[str, ...], roles: tuple[str, ...]) -> tuple[str, ...]:
        """Return array ABI local names only when the plan carries their roles."""
        return names if roles else ()

    def _entrypoint_prototype(self, plan: FunctionPlan) -> CFunctionPrototype:
        """Return the shared C prototype in planned parameter-group order."""
        parameters = tuple(
            parameter
            for group in sorted(plan.entrypoint.parameters, key=lambda item: item.position)
            for parameter in self._entrypoint_parameter_declarations(plan, group)
        )
        direct_c_abi = plan.entrypoint.direct_c_abi
        if direct_c_abi is not None:
            if len(parameters) != len(direct_c_abi.parameters):
                raise ValueError(
                    f"Direct C entrypoint {plan.owner_path!r} has {len(parameters)} planned parameters "
                    f"but {len(direct_c_abi.parameters)} preserved C declarations"
                )
            parameters = tuple(
                CParameter(parameter.name, self._direct_c_abi_declaration_type(abi_type))
                for parameter, abi_type in zip(parameters, direct_c_abi.parameters, strict=True)
            )
        return CFunctionPrototype(
            self._entrypoint_function_name(plan),
            self._entrypoint_return_type(plan),
            parameters,
        )

    def _entrypoint_parameter_declarations(
        self,
        plan: FunctionPlan,
        parameter: NativeEntrypointParameterPlan,
    ) -> tuple[CParameter, ...]:
        """Lower one planned entrypoint parameter group into a C prototype."""
        if parameter.source_kind == "argument":
            slot = self._projected_slot_for_parameter(plan, parameter)
            return self._entrypoint_argument_parameters(
                self._argument_by_owner(plan, parameter.owner_path),
                passing=slot.passing,
            )
        if parameter.source_kind == "projected_slot":
            return self._projected_slot_parameters(self._projected_slot_for_parameter(plan, parameter))
        result = self._entrypoint_result_by_owner(plan, parameter.owner_path)
        if parameter.source_kind == "hidden_result":
            return self._entrypoint_result_parameters(result)
        if parameter.source_kind == "direct_result":
            return self._direct_entrypoint_result_parameters(result)
        if parameter.source_kind == "declaration_extent":
            return self._declaration_extent_result_parameters_for_result(result)
        raise ValueError(f"Unsupported entrypoint parameter group {parameter.source_kind!r}")

    def _declaration_extent_result_parameters_for_result(
        self,
        result: NativeEntrypointResultPlan,
    ) -> tuple[CParameter, ...]:
        """Declare native-dependent extent outputs for one result group."""
        if result.array is None:
            return ()
        return tuple(
            CParameter(self._declaration_extent_result_name(result, axis), "int64_t *")
            for axis, evaluation in enumerate(result.array.extent_evaluation)
            if evaluation == "bridge"
        )

    @staticmethod
    def _declaration_extent_result_name(result: ResultPlan | NativeEntrypointResultPlan, axis: int) -> str:
        """Return the shared entrypoint ABI name for one evaluated result axis."""
        return f"prik_decl_extent_{result.result_position}_{axis}"

    def _owned_native_array_bridge_prototypes(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare typed Fortran operations over binding-owned result descriptors."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for _function, result in self._owned_native_array_results(plan)
            if not self._is_owned_deferred_character_result(result)
            for operation in self._generated_support_procedure_entrypoints_for(result.owner_path, "native_array:owned:")
        )

    def _default_native_array_bridge_prototypes(self, plan: ModulePlan) -> tuple[CFunctionPrototype, ...]:
        """Declare typed operations over lazily attached caller descriptors."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for _function, argument in self._default_native_array_arguments(plan)
            for operation in self._generated_support_procedure_entrypoints_for(
                argument.owner_path, "native_array:owned:"
            )
        )

    @staticmethod
    def _direct_c_abi_declaration_type(abi_type: DirectCABITypePlan) -> str:
        """Render one planned direct-C declaration type.

        A preserved source spelling is emitted verbatim so the generated
        prototype stays compatible with the user's declaration.  A source-free
        contract preserves none, so the backend composes the canonical spelling
        from the completed scalar identity and pointer depth.
        """
        if abi_type.source_spelling:
            return abi_type.source_spelling
        canonical = PrimitiveScalarTypeRegistry.type_for(abi_type.scalar_type_name).c_spelling
        return f"{canonical} {'*' * abi_type.pointer_depth}" if abi_type.pointer_depth else canonical

    def _entrypoint_return_type(self, plan: FunctionPlan) -> str:
        """Return the direct entrypoint result type, or void for subroutines."""
        direct_c_abi = plan.entrypoint.direct_c_abi
        if direct_c_abi is not None:
            if direct_c_abi.result is None:
                return "void"
            return self._direct_c_abi_declaration_type(direct_c_abi.result)
        result = self._direct_result(plan)
        if result is None:
            return "void"
        if self._is_owned_native_array_result(result):
            return "void"
        if result.scalar_descriptor is not None:
            return "void *"
        if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return "void *"
        if result.entrypoint.direct_result_abi is DirectResultABI.LOGICAL_LOW_BIT_INT8:
            return "int8_t"
        if result.entrypoint.direct_result_abi is DirectResultABI.NATIVE_SCALAR:
            return PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name).c_spelling
        raise ValueError(f"Scalar result {result.owner_path!r} has no completed direct-result ABI")

    def _direct_entrypoint_result_parameters(self, result: NativeEntrypointResultPlan) -> tuple[CParameter, ...]:
        """Return helper ABI parameters associated with one direct result."""
        if self._is_owned_native_array_result(result):
            if self._is_owned_deferred_character_result(result):
                rank = result.native_array_handle.array.rank
                return (
                    CParameter("result", "void **"),
                    CParameter("result_itemsize", "int64_t *"),
                    *(CParameter(f"result_extent_{axis}", "int64_t *") for axis in range(rank)),
                )
            return (CParameter("result", "CFI_cdesc_t *"),)
        if result.scalar_descriptor is not None:
            parameters = [CParameter("result_present", "int *")]
            if result.scalar_descriptor.runtime_length:
                parameters.append(CParameter("result_length", "int64_t *"))
            return tuple(parameters)
        return ()

    def _direct_result(self, plan: FunctionPlan) -> ResultPlan | None:
        """Return the sole direct native function result, when present."""
        return next((result for result in plan.results if result.source_kind == "direct_return"), None)

    def _entrypoint_argument_parameters(
        self,
        argument: ArgumentTransferPlan,
        *,
        passing: EntrypointPassingConvention,
    ) -> tuple[CParameter, ...]:
        """Return the entrypoint ABI parameters for one Python argument."""
        name = argument.entrypoint.parameter_name
        if argument.callback is not None:
            if not argument.entrypoint.pass_callback_parameter:
                return ()
            signature = argument.callback.entrypoint.support_procedure.signature
            return (
                CParameter(
                    name,
                    self._support_procedure_c_type(signature.result),
                    tuple(self._support_procedure_c_type(item) for item in signature.parameters),
                ),
            )
        if argument.derived_call is not None:
            return self._derived_entrypoint_argument_parameters(argument, name)
        return self._ordinary_entrypoint_argument_parameters(argument, name, passing=passing)

    @staticmethod
    def _derived_entrypoint_argument_parameters(
        argument: ArgumentTransferPlan,
        name: str,
    ) -> tuple[CParameter, ...]:
        """Declare the shared scalar-derived origin transaction ABI."""
        if not argument.entrypoint.pass_derived_transaction:
            return (CParameter(name, "void *"),)
        descriptor_output = (
            CParameter(f"{name}_output", "void **"),
            CParameter(f"{name}_output_present", "int *"),
        )
        return (
            CParameter(name, "void *"),
            CParameter(f"{name}_access", "int"),
            CParameter(f"{name}_identity", "void *"),
            *((CParameter(f"{name}_polymorphic", "int"),) if argument.polymorphic is not None else ()),
            CParameter(f"{name}_scoped", "prik_derived_scoped_fn"),
            CParameter(f"{name}_checkout", "prik_derived_checkout_fn"),
            CParameter(f"{name}_restore", "prik_derived_restore_fn"),
            CParameter(f"{name}_status", "int *"),
            *(descriptor_output if argument.entrypoint.descriptor_output_role is not None else ()),
        )

    def _ordinary_entrypoint_argument_parameters(
        self,
        argument: ArgumentTransferPlan,
        name: str,
        *,
        passing: EntrypointPassingConvention,
    ) -> tuple[CParameter, ...]:
        """Dispatch ordinary entrypoint parameters by completed handoff mode."""
        if argument.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER:
            return self._string_entrypoint_argument_parameters(argument, name, passing=passing)
        if argument.entrypoint.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._array_entrypoint_argument_parameters(argument, name)
        if argument.entrypoint.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            parameters = [CParameter(name, "CFI_cdesc_t *")]
            if argument.entrypoint.pass_descriptor_presence:
                parameters.append(CParameter(f"{name}_present", "void *"))
            return tuple(parameters)
        if argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            if argument.entrypoint.pass_character_length:
                return (CParameter(name, "void *"), CParameter(f"{name}_length", "int64_t"))
            return (CParameter(name, "void *"),)
        scalar_type = self._scalar_entrypoint_argument_type(argument, passing=passing)
        if argument.entrypoint.pass_descriptor_presence:
            return (CParameter(name, scalar_type), CParameter(f"{name}_present", "void *"))
        if argument.entrypoint.descriptor_output_role is not None:
            return (
                CParameter(name, scalar_type),
                CParameter(f"{name}_output", "void *"),
                CParameter(f"{name}_output_present", "int *"),
            )
        return (CParameter(name, scalar_type),)

    # Scalar entrypoint ABI parameters.
    def _scalar_entrypoint_argument_type(
        self,
        argument: ArgumentTransferPlan,
        *,
        passing: EntrypointPassingConvention,
    ) -> str:
        """Return the C ABI type for one scalar entrypoint input."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name).c_spelling
        if passing is EntrypointPassingConvention.C_VALUE:
            return scalar_type
        if passing in {
            EntrypointPassingConvention.POINTER_REFERENCE,
            EntrypointPassingConvention.NULLABLE_POINTER,
        }:
            return f"{scalar_type} *"
        if argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            return "void *"
        raise ValueError(f"Unsupported projected scalar passing convention {passing.value!r}")

    # String entrypoint ABI parameters.
    def _string_entrypoint_argument_parameters(
        self,
        argument: ArgumentTransferPlan,
        name: str,
        *,
        passing: EntrypointPassingConvention,
    ) -> tuple[CParameter, ...]:
        """Return one scalar string pointer-and-length ABI pair."""
        if not argument.entrypoint.pass_character_length and passing is EntrypointPassingConvention.C_VALUE:
            return (CParameter(name, "char"),)
        pointer_type = "char *" if argument.binding.codegen_action is CodegenAction.COPY_IN_OUT else "const char *"
        parameters = [CParameter(name, pointer_type)]
        if argument.entrypoint.pass_character_length:
            parameters.append(CParameter(f"{name}_length", "int64_t"))
        return tuple(parameters)

    # Ordinary-array entrypoint ABI parameters.
    def _array_entrypoint_argument_parameters(
        self,
        argument: ArgumentTransferPlan,
        name: str,
    ) -> tuple[CParameter, ...]:
        """Return the completed ordinary-array entrypoint ABI parameters."""
        handoff = argument.array
        if handoff is None:
            raise ValueError(f"Array argument {argument.owner_path!r} has no handoff spec")
        pointer_type = "void *"
        if not argument.entrypoint.pass_array_metadata:
            scalar_type = (
                "char"
                if argument.datatype_family is DatatypeFamily.STRING
                else PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name).c_spelling
            )
            pointer_type = f"{scalar_type} *"
        parameters = [CParameter(name, pointer_type)]
        if not argument.entrypoint.pass_array_metadata:
            return tuple(parameters)
        if handoff.runtime_rank_role is not None:
            parameters.append(CParameter(f"{name}_rank", "int64_t"))
        if handoff.itemsize_role is not None:
            parameters.append(CParameter(f"{name}_itemsize", "int64_t"))
        if handoff.dense_actual_role is not None:
            parameters.append(CParameter(f"{name}_dense_actual", "int"))
        parameters.extend(self._array_entrypoint_axis_parameters(name, "extent", len(handoff.extent_roles)))
        parameters.extend(self._array_entrypoint_axis_parameters(name, "upper_bound", len(handoff.upper_bound_roles)))
        parameters.extend(self._array_entrypoint_axis_parameters(name, "stride", len(handoff.stride_roles)))
        return tuple(parameters)

    def _array_entrypoint_axis_parameters(self, name: str, label: str, count: int) -> tuple[CParameter, ...]:
        """Return one named int64 entrypoint parameter per ordinary-array axis."""
        return tuple(CParameter(f"{name}_{label}_{axis}", "int64_t") for axis in range(count))

    def _entrypoint_result_parameters(self, result: NativeEntrypointResultPlan) -> tuple[CParameter, ...]:
        """Return the C ABI parameter for one native result slot."""
        if result.source_kind != "hidden_output":
            return ()
        name = result.parameter_name
        if name is None:
            raise ValueError(f"Hidden result {result.owner_path!r} has no entrypoint parameter name")
        if result.scalar_descriptor is not None:
            parameters = [
                CParameter(name, "void **"),
                CParameter(f"{name}_present", "int *"),
            ]
            if result.scalar_descriptor.runtime_length:
                parameters.append(CParameter(f"{name}_length", "int64_t *"))
            return tuple(parameters)
        if self._is_owned_native_array_result(result):
            if self._is_owned_deferred_character_result(result):
                rank = result.native_array_handle.array.rank
                return (
                    CParameter(name, "void **"),
                    CParameter(f"{name}_itemsize", "int64_t *"),
                    *(CParameter(f"{name}_extent_{axis}", "int64_t *") for axis in range(rank)),
                )
            return (CParameter(name, "CFI_cdesc_t *"),)
        if result.character_capacity is not None:
            # Direct C: the binding owns the buffer, so the callee receives a
            # plain ``char *`` rather than the adapter's owned-allocation slot.
            return (CParameter(name, "char *"),)
        if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return (CParameter(name, "void **"),)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name).c_spelling
        return (CParameter(name, f"{scalar_type} *"),)

    def _module_variable_bridge_prototypes(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[CFunctionPrototype, ...]:
        """Return getter/setter ABI declarations selected by the variable plan."""
        return tuple(
            self._generated_support_procedure_entrypoint_prototype(operation)
            for operation in self._generated_support_procedure_entrypoints_for(plan.owner_path, "module:")
        )

    def _module_variable_helper_prototypes(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[CFunctionPrototype, ...]:
        """Declare C helpers before the generated module-type routing code."""
        if plan.binding.getter_action in {
            ModuleGetterAction.CONSTANT_VALUE,
            ModuleGetterAction.NATIVE_CONSTANT_VALUE,
            ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
        }:
            return ()
        prototypes = [CFunctionPrototype(self._module_getter_name(plan), "PyObject *", storage="static")]
        if plan.binding.setter_action is SetterAction.WRITE_THROUGH:
            prototypes.append(
                CFunctionPrototype(
                    self._module_setter_name(plan),
                    "int",
                    (CParameter("value_obj", "PyObject *"),),
                    "static",
                )
            )
        return tuple(prototypes)

    def _module_property_support(
        self,
        module: ModulePlan,
        namespace: NamespacePlan,
    ) -> CModulePropertySupport | None:
        """Return dynamic module-attribute routing for non-constant variables."""
        entries = tuple(
            CModulePropertyEntry(
                python_name=python_name,
                getter_name=self._module_getter_name(variable),
                setter_name=(
                    self._module_setter_name(variable)
                    if variable.binding.setter_action is SetterAction.WRITE_THROUGH
                    else None
                ),
                reject_replacement=(variable.binding.setter_action is SetterAction.REJECT_REPLACEMENT),
            )
            for variable in namespace.variables
            if variable.binding.getter_action
            not in {
                ModuleGetterAction.CONSTANT_VALUE,
                ModuleGetterAction.NATIVE_CONSTANT_VALUE,
                ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
            }
            for python_name in variable.binding.python_names
        )
        if not entries:
            return None
        namespace_symbol = self._namespace_symbol(namespace)
        return CModulePropertySupport(
            name=f"{module.binding.owner_path}_{namespace_symbol}_module_property_setup",
            module_name=self._namespace_module_name(module, namespace),
            entries=entries,
        )

    def _binding_prototype(self, plan: FunctionPlan, *, external: bool = False) -> CFunctionPrototype:
        """Return the binding-local binding prototype derived from the supplied completed binding records; this helper preserves completed policy."""
        return CFunctionPrototype(
            self._binding_function_name(plan),
            "PyObject *",
            self._binding_parameters(plan),
            None if external else "static",
        )

    @staticmethod
    def _derived_capsule_name(type_name: str) -> str:
        """Return the checked capsule identity for one native type."""
        return f"prik.derived.{type_name}"

    @staticmethod
    def _derived_capsule_destructor_name(type_name: str) -> str:
        """Return one binding-owned capsule cleanup symbol."""
        return f"prik_destroy_{type_name.casefold()}_capsule"

    def _derived_destroy_bridge_name(self, type_name: str) -> str:
        """Return the planner-owned native-aware destroy symbol."""
        return self._generated_support_procedure_entrypoint(
            self._derived_owner_paths[type_name], "derived:destroy"
        ).symbol_name

    @staticmethod
    def _allocatable_holder_capsule_name(type_name: str) -> str:
        """Return the binding-local allocatable holder capsule name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"prik.derived.{type_name}.allocatable_holder"

    @staticmethod
    def _pointer_holder_capsule_name(type_name: str) -> str:
        """Return the binding-local pointer holder capsule name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"prik.derived.{type_name}.pointer_holder"

    @staticmethod
    def _pointer_holder_capsule_destructor_name(type_name: str) -> str:
        """Return the binding-local pointer holder capsule destructor name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"prik_destroy_{type_name.casefold()}_pointer_holder_capsule"

    def _pointer_holder_destroy_bridge_name(self, type_name: str) -> str:
        """Return the planner-owned pointer-holder destroy symbol."""
        return self._generated_support_procedure_entrypoint(
            self._derived_owner_paths[type_name], "holder:pointer:destroy"
        ).symbol_name

    def _pointer_holder_presence_bridge_name(self, type_name: str) -> str:
        """Return the planner-owned pointer-holder presence symbol."""
        return self._generated_support_procedure_entrypoint(
            self._derived_owner_paths[type_name], "holder:pointer:present"
        ).symbol_name

    @staticmethod
    def _allocatable_holder_capsule_destructor_name(type_name: str) -> str:
        """Return the binding-local allocatable holder capsule destructor name derived from the supplied local lowering values; this helper preserves completed policy."""
        return f"prik_destroy_{type_name.casefold()}_allocatable_holder_capsule"

    def _allocatable_holder_destroy_bridge_name(self, type_name: str) -> str:
        """Return the planner-owned allocatable-holder destroy symbol."""
        return self._generated_support_procedure_entrypoint(
            self._derived_owner_paths[type_name], "holder:allocatable:destroy"
        ).symbol_name

    def _allocatable_holder_presence_bridge_name(self, type_name: str) -> str:
        """Return the planner-owned allocatable-holder presence symbol."""
        return self._generated_support_procedure_entrypoint(
            self._derived_owner_paths[type_name], "holder:allocatable:present"
        ).symbol_name

    @staticmethod
    def _allocatable_holder_presence_method_name(type_name: str) -> str:
        """Return the binding-local allocatable holder presence method name derived from the supplied local lowering values; this helper preserves completed policy."""
        return CBindingNames.allocatable_holder_presence_method(type_name)

    @staticmethod
    def _pointer_holder_presence_method_name(type_name: str) -> str:
        """Return the binding-local pointer holder presence method name derived from the supplied local lowering values; this helper preserves completed policy."""
        return CBindingNames.pointer_holder_presence_method(type_name)

    @staticmethod
    def _derived_field_symbol(derived: DerivedTypePlan, field: DerivedFieldPlan) -> str:
        """Return the binding-local derived field symbol derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.derived_field_symbol(derived, field)

    def _derived_field_method_name(self, derived: DerivedTypePlan, field: DerivedFieldPlan, action: str) -> str:
        """Return the binding-local derived field method name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.derived_field_method(derived, field, action)

    def _derived_field_bridge_name(self, derived: DerivedTypePlan, field: DerivedFieldPlan, action: str) -> str:
        """Return the planner-owned direct-field entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(
            f"{derived.owner_path}.{field.name}", f"field:direct:{action}"
        ).symbol_name

    def _allocatable_holder_field_bridge_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        """Return the planner-owned allocatable-holder field symbol."""
        return self._generated_support_procedure_entrypoint(
            f"{derived.owner_path}.{field.name}", f"field:allocatable:{action}"
        ).symbol_name

    def _allocatable_holder_field_method_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        """Return the binding-local allocatable holder field method name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.allocatable_holder_field_method(derived, field, action)

    def _pointer_holder_field_bridge_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        """Return the planner-owned pointer-holder field symbol."""
        return self._generated_support_procedure_entrypoint(
            f"{derived.owner_path}.{field.name}", f"field:pointer:{action}"
        ).symbol_name

    def _pointer_holder_field_method_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        """Return the binding-local pointer holder field method name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.pointer_holder_field_method(derived, field, action)

    @staticmethod
    def _allocatable_holder_ops_name(type_name: str) -> str:
        """Return the binding-local allocatable holder ops name derived from the supplied local lowering values; this helper preserves completed policy."""
        return CBindingNames.allocatable_holder_ops(type_name)

    @staticmethod
    def _pointer_holder_ops_name(type_name: str) -> str:
        """Return the binding-local pointer holder ops name derived from the supplied local lowering values; this helper preserves completed policy."""
        return CBindingNames.pointer_holder_ops(type_name)

    def _derived_field_descriptor_callback_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        """Return the binding-local derived field descriptor callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_field_{self._derived_field_symbol(derived, field)}_descriptor"

    def _derived_handle_operation_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the binding-local derived handle operation name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_field_handle_{self._derived_field_symbol(derived, field)}_{operation.value}"

    def _derived_handle_bridge_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the planner-owned direct-field handle symbol."""
        return self._generated_support_procedure_entrypoint(
            f"{derived.owner_path}.{field.name}",
            f"field:direct:handle:{operation.value}",
        ).symbol_name

    def _derived_handle_descriptor_callback_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        """Return the binding-local derived handle descriptor callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_field_handle_{self._derived_field_symbol(derived, field)}_descriptor_callback"

    def _derived_handle_actual_callback_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        """Return the binding-local derived handle actual callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_field_handle_{self._derived_field_symbol(derived, field)}_actual_callback"

    @staticmethod
    def _module_member_symbol(variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        """Return the binding-local module member symbol derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.module_member_symbol(variable, member)

    def _module_member_method_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        action: str,
    ) -> str:
        """Return the binding-local module member method name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.module_member_method(variable, member, action)

    def _module_member_bridge_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        action: str,
    ) -> str:
        """Return the planner-owned module-member entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(
            ".".join((variable.owner_path, *member.path)), f"field:module:{action}"
        ).symbol_name

    def _module_member_descriptor_callback_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        """Return the binding-local module member descriptor callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_module_field_{self._module_member_symbol(variable, member)}_descriptor"

    def _module_member_handle_operation_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the binding-local module member handle operation name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_module_field_handle_{self._module_member_symbol(variable, member)}_{operation.value}"

    def _module_member_handle_bridge_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return the planner-owned module-member handle symbol."""
        return self._generated_support_procedure_entrypoint(
            ".".join((variable.owner_path, *member.path)),
            f"field:module:handle:{operation.value}",
        ).symbol_name

    def _module_member_handle_descriptor_callback_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        """Return the binding-local module member handle descriptor callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_module_field_handle_{self._module_member_symbol(variable, member)}_descriptor_callback"

    def _module_member_handle_actual_callback_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        """Return the binding-local module member handle actual callback name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"prik_module_field_handle_{self._module_member_symbol(variable, member)}_actual_callback"

    @staticmethod
    def _module_member_ops_name(variable: ModuleVariablePlan, prefix: tuple[str, ...]) -> str:
        """Return the binding-local module member ops name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.module_member_ops(variable, prefix)

    def _derived_member_proxy_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return plain derived module objects with typed member operations."""
        return tuple(
            variable
            for variable in self._variables(plan)
            if variable.derived is not None and variable.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY
        )

    def _derived_module_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return every live native-owned derived module object."""
        return tuple(variable for variable in self._variables(plan) if variable.derived is not None)

    def _derived_module_owner_declarations(self, plan: ModulePlan) -> tuple[CDeclaration, ...]:
        """Retain the Python module owner for borrowed derived objects."""
        return tuple(
            CDeclaration(
                self._derived_module_owner_name(variable),
                "static PyObject *",
                CodeExpression("NULL"),
            )
            for variable in self._derived_module_variables(plan)
        )

    @staticmethod
    def _derived_module_owner_name(variable: ModuleVariablePlan) -> str:
        """Return the binding-local derived module owner name derived from the supplied completed binding records; this helper preserves completed policy."""
        owner = re.sub(r"\W", "_", variable.owner_path).casefold()
        return f"prik_module_{owner}_derived_owner"

    def _method_table(self, module: ModulePlan, namespace: NamespacePlan) -> CMethodDefTable:
        """Build method table from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return CMethodDefTable(
            f"{module.binding.owner_path}_{self._namespace_symbol(namespace)}_methods",
            (
                *(
                    CMethodDefEntry(
                        function.binding.python_name,
                        self._binding_function_name(function),
                        self._binding_method_flags(function),
                        function.binding.docstring,
                    )
                    for function in namespace.functions
                ),
                *self._overload_method_entries(namespace),
                *(
                    CMethodDefEntry(
                        CBindingNames.class_create_method(surface),
                        CBindingNames.class_create_method(surface),
                        "METH_VARARGS",
                        "",
                    )
                    for surface in namespace.classes
                    if surface.constructor.kind is not ClassConstructorKind.ABSENT
                ),
                *self._derived_private_method_entries(namespace),
            ),
        )

    @staticmethod
    def _binding_method_flags(plan: FunctionPlan) -> str:
        """Return the CPython call convention selected for one wrapper."""
        if plan.binding.accepts_keyword_arguments:
            return "METH_VARARGS | METH_KEYWORDS"
        return "METH_VARARGS"

    def _overload_method_entries(self, namespace: NamespacePlan) -> tuple[CMethodDefEntry, ...]:
        """Install public module dispatchers and private class dispatchers."""
        return tuple(
            CMethodDefEntry(
                dispatch.overload.python_name
                if dispatch.public
                else CBindingNames.overload_dispatch_method(dispatch.overload),
                CBindingNames.overload_dispatch_function(dispatch.overload),
                "METH_VARARGS | METH_KEYWORDS",
                dispatch.overload.docstring if dispatch.public else "",
            )
            for dispatch in self._namespace_overload_dispatches(namespace)
        )

    @staticmethod
    def _namespace_overload_dispatches(namespace: NamespacePlan) -> tuple[_COverloadDispatch, ...]:
        """Return every distinct overload surface installed in one namespace."""
        dispatches = [_COverloadDispatch(overload, receiver=False, public=True) for overload in namespace.overloads]
        seen = {id(overload) for overload in namespace.overloads}
        for surface in namespace.classes:
            constructor = surface.constructor.overload
            if constructor is not None and id(constructor) not in seen:
                # A constructor overload whose candidates are type-bound takes the
                # receiver; one whose candidates are functions returning the type
                # -- a Fortran `interface <typename>` -- does not.
                constructor_receiver = bool(
                    constructor.candidate_passed_objects and constructor.candidate_passed_objects[0]
                )
                dispatches.append(_COverloadDispatch(constructor, receiver=constructor_receiver, public=False))
                seen.add(id(constructor))
            for overload in surface.overloads:
                if id(overload) in seen:
                    continue
                receiver = bool(overload.candidate_passed_objects and overload.candidate_passed_objects[0])
                dispatches.append(_COverloadDispatch(overload, receiver=receiver, public=False))
                seen.add(id(overload))
        return tuple(dispatches)

    def _overload_dispatch_functions(
        self,
        plan: ModulePlan,
        class_python_names: dict[tuple[str, str], str],
    ) -> tuple[CFunction, ...]:
        """Lower every completed overload surface into one C dispatcher."""
        return tuple(
            self._overload_dispatch_function(dispatch, class_python_names)
            for namespace in plan.namespaces
            for dispatch in self._namespace_overload_dispatches(namespace)
        )

    def _overload_dispatch_function(
        self,
        dispatch: _COverloadDispatch,
        class_python_names: dict[tuple[str, str], str],
    ) -> CFunction:
        """Classify one call, assign a candidate ID, and switch to its wrapper."""
        overload = dispatch.overload
        positional_offset = 1 if dispatch.receiver else 0
        body = [
            CDeclaration("nargs", "Py_ssize_t", CodeExpression("PyTuple_GET_SIZE(args)")),
        ]
        if dispatch.receiver:
            body.extend(self._overload_receiver_nodes(overload))
        else:
            body.append(CDeclaration("user_nargs", "Py_ssize_t", CodeExpression("nargs")))
        body.append(CDeclaration("candidate_id", "int", CodeExpression("-1")))
        body.extend(self._overload_special_case_nodes(overload, dispatch.receiver))
        body.extend(
            CIf(
                CodeExpression(
                    "candidate_id < 0 && ("
                    + self._overload_candidate_condition(
                        matches,
                        positional_offset=positional_offset,
                        class_python_names=class_python_names,
                    )
                    + ")"
                ),
                body=(CExpressionStatement(CodeExpression(f"candidate_id = {candidate_id}")),),
            )
            for candidate_id, matches in zip(
                overload.candidate_ids,
                overload.candidate_matches,
                strict=True,
            )
        )
        cases = tuple(
            self._overload_candidate_case(
                dispatch,
                candidate_id,
                candidate,
                matches,
                positional_offset=positional_offset,
            )
            for candidate_id, candidate, matches in zip(
                overload.candidate_ids,
                overload.candidates,
                overload.candidate_matches,
                strict=True,
            )
        )
        body.append(
            CSwitch(
                CodeExpression("candidate_id"),
                cases=(*cases, self._overload_default_case(overload)),
            )
        )
        return CFunction(
            CBindingNames.overload_dispatch_function(overload),
            "PyObject *",
            parameters=self._binding_parameters(),
            body=tuple(body),
            storage="static",
        )

    def _overload_receiver_nodes(self, overload: OverloadPlan) -> tuple[CIf | CDeclaration, ...]:
        """Extract the class receiver inserted by the generated Python method."""
        message = self._c_string_literal(f"no matching overload for {overload.python_name}")
        return (
            CIf(
                CodeExpression("nargs < 1"),
                body=(
                    CExpressionStatement(CodeExpression(f"PyErr_SetString(PyExc_TypeError, {message})")),
                    CReturn(CodeExpression("NULL")),
                ),
            ),
            CDeclaration("receiver", "PyObject *", CodeExpression("PyTuple_GET_ITEM(args, 0)")),
            CDeclaration("user_nargs", "Py_ssize_t", CodeExpression("nargs - 1")),
        )

    def _overload_special_case_nodes(
        self,
        overload: OverloadPlan,
        has_receiver: bool,
    ) -> tuple[CIf, ...]:
        """Preserve planned early errors and reflected identity behavior."""
        nodes = []
        if overload.unsupported_extra_argument_message is not None:
            message = self._c_string_literal(overload.unsupported_extra_argument_message)
            nodes.append(
                CIf(
                    CodeExpression("user_nargs > 1"),
                    body=(
                        CExpressionStatement(CodeExpression(f"PyErr_SetString(PyExc_TypeError, {message})")),
                        CReturn(CodeExpression("NULL")),
                    ),
                )
            )
        if overload.identity_receiver_shortcut and has_receiver:
            nodes.append(
                CIf(
                    CodeExpression(
                        "user_nargs == 1 && (kwargs == NULL || PyDict_Size(kwargs) == 0) "
                        "&& PyTuple_GET_ITEM(args, 1) == receiver"
                    ),
                    body=(
                        CExpressionStatement(CodeExpression("Py_INCREF(receiver)")),
                        CReturn(CodeExpression("receiver")),
                    ),
                )
            )
        return tuple(nodes)

    def _overload_candidate_condition(
        self,
        matches: tuple[OverloadArgumentMatchPlan, ...],
        *,
        positional_offset: int,
        class_python_names: dict[tuple[str, str], str],
    ) -> str:
        """Return one ordered candidate predicate over borrowed call arguments."""
        shape = self._overload_call_shape_condition(matches)
        predicates = tuple(
            self._overload_argument_condition(
                match,
                self._overload_argument_value_expression(match, index, positional_offset),
                class_python_names,
            )
            for index, match in enumerate(matches)
        )
        return " && ".join((shape, *predicates))

    def _overload_call_shape_condition(self, matches: tuple[OverloadArgumentMatchPlan, ...]) -> str:
        """Validate keyword membership and positional-keyword exclusivity."""
        keyword_hits = (
            " + ".join(
                f"(PyDict_GetItemString(kwargs, {self._c_string_literal(match.python_name)}) != NULL)"
                for match in matches
            )
            or "0"
        )
        duplicates = (
            " && ".join(
                "(user_nargs <= "
                f"{index} || PyDict_GetItemString(kwargs, {self._c_string_literal(match.python_name)}) == NULL)"
                for index, match in enumerate(matches)
            )
            or "1"
        )
        keyword_shape = f"PyDict_Size(kwargs) == ({keyword_hits}) && {duplicates}"
        return f"user_nargs <= {len(matches)} && (kwargs == NULL || ({keyword_shape}))"

    def _overload_argument_value_expression(
        self,
        match: OverloadArgumentMatchPlan,
        index: int,
        positional_offset: int,
    ) -> str:
        """Return a borrowed value from its candidate-specific canonical position."""
        name = self._c_string_literal(match.python_name)
        return (
            f"(user_nargs > {index} ? PyTuple_GET_ITEM(args, {index + positional_offset}) "
            f": (kwargs != NULL ? PyDict_GetItemString(kwargs, {name}) : NULL))"
        )

    def _overload_argument_condition(
        self,
        match: OverloadArgumentMatchPlan,
        value: str,
        class_python_names: dict[tuple[str, str], str],
    ) -> str:
        """Wrap one exact C predicate with its required or optional presence rule."""
        predicate = self._overload_required_argument_condition(match, value, class_python_names)
        if match.optional:
            return f"({value} == NULL || ({predicate}))"
        return f"({value} != NULL && ({predicate}))"

    def _overload_required_argument_condition(
        self,
        match: OverloadArgumentMatchPlan,
        value: str,
        class_python_names: dict[tuple[str, str], str],
    ) -> str:
        """Return the C-API predicate for one completed overload match kind."""
        if match.kind is OverloadMatchKind.DERIVED:
            if match.derived_type_identity is None:
                raise ValueError(f"Derived overload argument {match.python_name!r} has no type identity")
            class_name = self._c_string_literal(class_python_names[match.derived_type_identity])
            expected = f"PyDict_GetItemString(PyModule_GetDict(self), {class_name})"
            return f"{expected} != NULL && (PyObject *)Py_TYPE({value}) == {expected}"
        if match.kind is OverloadMatchKind.NUMPY_ARRAY:
            numpy_type = PrimitiveScalarTypeRegistry.type_for(match.semantic_type_name).numpy_type_macro
            return (
                f"PyArray_Check({value}) && PyArray_NDIM((PyArrayObject *){value}) == {match.rank} "
                f"&& PyArray_TYPE((PyArrayObject *){value}) == {numpy_type}"
            )
        if match.kind is OverloadMatchKind.STRING:
            return f"PyUnicode_Check({value})"
        if match.kind is OverloadMatchKind.NUMPY_SCALAR:
            predicate = f"PyArray_IsScalar({value}, {self._overload_numpy_scalar_kind(match.semantic_type_name)})"
            if match.builtin_scalar_family is not None:
                predicate = f"({predicate} || {self._overload_builtin_scalar_condition(match, value)})"
            return predicate
        raise ValueError(f"Unsupported overload match kind: {match.kind.value}")

    @staticmethod
    def _overload_numpy_scalar_kind(semantic_type_name: str) -> str:
        """Return the NumPy scalar macro suffix used by exact C dispatch."""
        if is_boolean_semantic_type_name(semantic_type_name):
            return "Bool"
        kinds = {
            "Int8": "Int8",
            "Int16": "Int16",
            "Int32": "Int",
            "Int64": "Int64",
            "Float32": "Float",
            "Float64": "Double",
            "Complex64": "CFloat",
            "Complex128": "CDouble",
        }
        try:
            return kinds[semantic_type_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported NumPy overload scalar {semantic_type_name!r}") from exc

    @staticmethod
    def _overload_builtin_scalar_condition(match: OverloadArgumentMatchPlan, value: str) -> str:
        """Return the exact builtin predicate allowed for reflected dispatch."""
        if match.builtin_scalar_family == "bool":
            return f"PyBool_Check({value})"
        if match.builtin_scalar_family == "int":
            return f"PyLong_CheckExact({value})"
        if match.builtin_scalar_family == "float":
            return f"PyFloat_CheckExact({value})"
        if match.builtin_scalar_family == "complex":
            return f"PyComplex_CheckExact({value})"
        raise ValueError(f"Unsupported reflected overload scalar family {match.builtin_scalar_family!r}")

    def _overload_candidate_case(
        self,
        dispatch: _COverloadDispatch,
        candidate_id: int,
        candidate: FunctionPlan,
        matches: tuple[OverloadArgumentMatchPlan, ...],
        *,
        positional_offset: int,
    ) -> CCase:
        """Build one switch leaf that calls the selected existing C wrapper."""
        body = [
            CDeclaration("candidate_kwargs", "PyObject *", CodeExpression("PyDict_New()")),
            CIf(CodeExpression("candidate_kwargs == NULL"), body=(CReturn(CodeExpression("NULL")),)),
        ]
        for index, match in enumerate(matches):
            body.extend(
                self._overload_candidate_keyword_nodes(
                    match,
                    index,
                    positional_offset=positional_offset,
                )
            )
        if dispatch.receiver:
            receiver_name = OverloadPlanQueries.receiver_name(candidate)
            body.extend(self._overload_set_keyword_nodes(receiver_name, "receiver"))
        body.extend(
            (
                CDeclaration("candidate_args", "PyObject *", CodeExpression("PyTuple_New(0)")),
                CIf(
                    CodeExpression("candidate_args == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(candidate_kwargs)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CDeclaration(
                    "candidate_result",
                    "PyObject *",
                    CodeExpression(f"{self._binding_function_name(candidate)}(self, candidate_args, candidate_kwargs)"),
                ),
                CExpressionStatement(CodeExpression("Py_DECREF(candidate_args)")),
                CExpressionStatement(CodeExpression("Py_DECREF(candidate_kwargs)")),
                CReturn(CodeExpression("candidate_result")),
            )
        )
        return CCase(CodeExpression(str(candidate_id)), body=tuple(body))

    def _overload_candidate_keyword_nodes(
        self,
        match: OverloadArgumentMatchPlan,
        index: int,
        *,
        positional_offset: int,
    ) -> tuple[CDeclaration | CIf | CExpressionStatement, ...]:
        """Copy one matched borrowed argument into the selected candidate call."""
        value_name = f"candidate_value_{index}"
        nodes = [
            CDeclaration(
                value_name,
                "PyObject *",
                CodeExpression(self._overload_argument_value_expression(match, index, positional_offset)),
            )
        ]
        coerced_name = None
        if match.builtin_scalar_family is not None:
            coerced_name = f"candidate_coerced_{index}"
            nodes.append(CDeclaration(coerced_name, "PyObject *", CodeExpression("NULL")))
            nodes.append(self._overload_builtin_coercion_node(match, value_name, coerced_name))
        set_nodes = self._overload_set_keyword_nodes(match.python_name, value_name, coerced_name=coerced_name)
        if match.optional:
            nodes.append(CIf(CodeExpression(f"{value_name} != NULL"), body=set_nodes))
        else:
            nodes.extend(set_nodes)
        return tuple(nodes)

    def _overload_builtin_coercion_node(
        self,
        match: OverloadArgumentMatchPlan,
        value_name: str,
        coerced_name: str,
    ) -> CIf:
        """Convert one accepted builtin to the exact NumPy scalar expected downstream."""
        builtin = self._overload_builtin_scalar_condition(match, value_name)
        numpy_type = PrimitiveScalarTypeRegistry.type_for(match.semantic_type_name).numpy_type_macro
        type_name = f"candidate_scalar_type_{coerced_name.rsplit('_', 1)[-1]}"
        return CIf(
            CodeExpression(f"{value_name} != NULL && {builtin}"),
            body=(
                CDeclaration(
                    type_name,
                    "PyObject *",
                    CodeExpression(f"(PyObject *)PyArray_TypeObjectFromType({numpy_type})"),
                ),
                CIf(
                    CodeExpression(f"{type_name} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(candidate_kwargs)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(
                    CodeExpression(f"{coerced_name} = PyObject_CallOneArg({type_name}, {value_name})")
                ),
                CIf(
                    CodeExpression(f"{coerced_name} == NULL"),
                    body=(
                        CExpressionStatement(CodeExpression("Py_DECREF(candidate_kwargs)")),
                        CReturn(CodeExpression("NULL")),
                    ),
                ),
                CExpressionStatement(CodeExpression(f"{value_name} = {coerced_name}")),
            ),
        )

    def _overload_set_keyword_nodes(
        self,
        name: str,
        value_name: str,
        *,
        coerced_name: str | None = None,
    ) -> tuple[CIf | CExpressionStatement, ...]:
        """Set one candidate keyword and release any temporary scalar conversion."""
        cleanup = (
            *((CExpressionStatement(CodeExpression(f"Py_XDECREF({coerced_name})")),) if coerced_name else ()),
            CExpressionStatement(CodeExpression("Py_DECREF(candidate_kwargs)")),
            CReturn(CodeExpression("NULL")),
        )
        nodes = [
            CIf(
                CodeExpression(
                    f"PyDict_SetItemString(candidate_kwargs, {self._c_string_literal(name)}, {value_name}) < 0"
                ),
                body=cleanup,
            )
        ]
        if coerced_name is not None:
            nodes.append(CExpressionStatement(CodeExpression(f"Py_XDECREF({coerced_name})")))
        return tuple(nodes)

    def _overload_default_case(self, overload: OverloadPlan) -> CCase:
        """Raise the stable public error when no planned candidate matches."""
        message = self._c_string_literal(f"no matching overload for {overload.python_name}")
        return CCase(
            None,
            body=(
                CExpressionStatement(CodeExpression(f"PyErr_SetString(PyExc_TypeError, {message})")),
                CReturn(CodeExpression("NULL")),
            ),
        )

    def _derived_private_method_entries(self, namespace: NamespacePlan) -> tuple[CMethodDefEntry, ...]:
        """Expose private field callables used by generated Python properties."""
        names = (
            *self._direct_field_method_names(namespace),
            *self._module_member_method_names(namespace),
            *self._allocatable_holder_method_names(namespace),
            *self._pointer_holder_method_names(namespace),
            *self._module_proxy_guard_method_names(namespace),
        )
        return tuple(CMethodDefEntry(name, name, "METH_VARARGS", "") for name in names)

    def _direct_field_method_names(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Return the binding-local direct field method names derived from the supplied completed binding records; this helper preserves completed policy."""
        return tuple(
            self._derived_field_method_name(derived, field, action)
            for derived in namespace.derived_types
            if not derived.abstract
            for field in derived.fields
            for action in self._field_method_actions(field)
        )

    def _module_member_method_names(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Return the binding-local module member method names derived from the supplied completed binding records; this helper preserves completed policy."""
        return tuple(
            self._module_member_method_name(variable, member, action)
            for variable in namespace.variables
            if variable.derived is not None and variable.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY
            for member in variable.derived.member_paths
            for action in self._field_method_actions(member.field)
        )

    @staticmethod
    def _namespace_binding_holder_types(
        namespace: NamespacePlan,
        owner_paths: frozenset[str],
    ) -> tuple[DerivedTypePlan, ...]:
        """Join one namespace to its planner-owned binding holder inventory."""
        return tuple(derived for derived in namespace.derived_types if derived.owner_path in owner_paths)

    def _allocatable_holder_method_names(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Return methods for the namespace's planned allocatable holders."""
        holders = self._namespace_binding_holder_types(
            namespace,
            self._binding_allocatable_holder_owner_paths,
        )
        fields = tuple(
            self._allocatable_holder_field_method_name(derived, field, action)
            for derived in holders
            for field in derived.fields
            for action in self._field_method_actions(field)
        )
        guards = tuple(self._allocatable_holder_presence_method_name(derived.backend_symbol) for derived in holders)
        return (*fields, *guards)

    def _pointer_holder_method_names(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Return methods for the namespace's planned pointer holders."""
        holders = self._namespace_binding_holder_types(
            namespace,
            self._binding_pointer_holder_owner_paths,
        )
        fields = tuple(
            self._pointer_holder_field_method_name(derived, field, action)
            for derived in holders
            for field in derived.fields
            for action in self._field_method_actions(field)
        )
        guards = tuple(self._pointer_holder_presence_method_name(derived.backend_symbol) for derived in holders)
        return (*fields, *guards)

    def _module_proxy_guard_method_names(self, namespace: NamespacePlan) -> tuple[str, ...]:
        """Return the binding-local module proxy guard method names derived from the supplied completed binding records; this helper preserves completed policy."""
        presence = tuple(
            self._module_derived_presence_method_name(variable)
            for variable in namespace.variables
            if self._nullable_derived_module_proxy(variable)
        )
        native_ops = tuple(
            self._derived_origin_capsule_method_name(variable)
            for variable in namespace.variables
            if variable.derived is not None
        )
        return (*presence, *native_ops)

    @staticmethod
    def _field_method_actions(field: DerivedFieldPlan) -> tuple[str, ...]:
        """Return field method actions from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return ("get", *(("set",) if field.setter_action is SetterAction.WRITE_THROUGH else ()))

    def _module_def(self, module: ModulePlan, namespace: NamespacePlan) -> CModuleDef:
        """Return module def from the supplied completed binding records; this helper preserves the selected binding behavior."""
        owner = module.binding.owner_path
        symbol = self._namespace_symbol(namespace)
        python_name = self._namespace_module_name(module, namespace)
        return CModuleDef(
            f"{owner}_{symbol}_module",
            python_name,
            namespace.docstring,
            f"{owner}_{symbol}_methods",
        )

    def _module_init(
        self,
        plan: ModulePlan,
        needs_native_support: bool,
    ) -> CFunction:
        """Return module init from the supplied completed binding records; this helper preserves the selected binding behavior."""
        module_name = plan.binding.owner_path
        root_namespace = self._namespace(plan, ())
        child_namespaces = self._ordered_child_namespaces(plan)
        return CFunction(
            f"PyInit_{module_name}",
            "PyMODINIT_FUNC",
            body=(
                *((CExpressionStatement(CodeExpression("import_array()")),) if needs_native_support else ()),
                CDeclaration(
                    "mod",
                    "PyObject *",
                    CodeExpression(f"PyModule_Create(&{module_name}_{self._namespace_symbol(root_namespace)}_module)"),
                ),
                CExpressionStatement(CodeExpression("if (mod == NULL) return NULL")),
                *self._namespace_configuration_nodes(
                    plan,
                    root_namespace,
                    "mod",
                ),
                *(node for namespace in child_namespaces for node in self._child_namespace_nodes(plan, namespace)),
                *(
                    node
                    for namespace in child_namespaces
                    for node in self._child_namespace_import_registration_nodes(plan, namespace)
                ),
                CReturn(CodeExpression("mod")),
            ),
        )

    def _ordered_child_namespaces(self, plan: ModulePlan) -> tuple[NamespacePlan, ...]:
        """Return parents before descendants regardless of editable tuple order."""
        return tuple(
            sorted(
                (namespace for namespace in plan.namespaces if namespace.python_path),
                key=lambda namespace: (len(namespace.python_path), namespace.python_path),
            )
        )

    def _child_namespace_nodes(
        self,
        module: ModulePlan,
        namespace: NamespacePlan,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Create, attach, and configure one child Python module."""
        object_name = self._namespace_object_name(namespace)
        parent = self._namespace_object_name(self._namespace(module, namespace.python_path[:-1]))
        definition = f"{module.binding.owner_path}_{self._namespace_symbol(namespace)}_module"
        local_name = namespace.python_path[-1]
        return (
            CDeclaration(object_name, "PyObject *", CodeExpression(f"PyModule_Create(&{definition})")),
            CExpressionStatement(CodeExpression(f"if ({object_name} == NULL) {{ Py_DECREF(mod); return NULL; }}")),
            CExpressionStatement(
                CodeExpression(
                    f'if (PyModule_AddObject({parent}, "{local_name}", {object_name}) < 0) '
                    f"{{ Py_DECREF({object_name}); Py_DECREF(mod); return NULL; }}"
                )
            ),
            *self._namespace_configuration_nodes(
                module,
                namespace,
                object_name,
            ),
        )

    def _child_namespace_import_registration_nodes(
        self,
        module: ModulePlan,
        namespace: NamespacePlan,
    ) -> tuple[CExpressionStatement, ...]:
        """Register one generated child module under its qualified import name."""
        module_name = self._c_string_literal(self._namespace_module_name(module, namespace))
        object_name = self._namespace_object_name(namespace)
        return (
            CExpressionStatement(
                CodeExpression(
                    f"if (PyDict_SetItemString(PyImport_GetModuleDict(), {module_name}, {object_name}) < 0) "
                    f"{{ Py_DECREF(mod); return NULL; }}"
                )
            ),
        )

    def _namespace_configuration_nodes(
        self,
        module: ModulePlan,
        namespace: NamespacePlan,
        object_name: str,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Initialize properties, native state, and constants in one namespace."""
        property_support = self._module_property_support(module, namespace)
        property_nodes = (
            (
                CExpressionStatement(
                    CodeExpression(
                        f"if ({property_support.name}({object_name}) < 0) {{ Py_DECREF(mod); return NULL; }}"
                    )
                ),
            )
            if property_support is not None
            else ()
        )
        return (
            *property_nodes,
            *self._namespace_python_initializer_nodes(
                namespace,
                object_name,
            ),
            *self._module_native_array_owner_nodes(namespace, object_name),
            *self._derived_module_owner_nodes(namespace, object_name),
            *self._module_initializer_nodes(namespace),
            *self._module_constant_nodes(namespace, object_name),
        )

    def _namespace_python_initializer_nodes(
        self,
        namespace: NamespacePlan,
        module_object: str,
    ) -> tuple[CDeclaration | CExpressionStatement | CIf, ...]:
        """Install exact overload dispatch plus generated opaque wrapper types."""
        has_proxy = any(variable.derived is not None for variable in namespace.variables)
        if not namespace.derived_types and not has_proxy:
            return ()
        allocatable_holders = self._namespace_binding_holder_types(
            namespace,
            self._binding_allocatable_holder_owner_paths,
        )
        pointer_holders = self._namespace_binding_holder_types(
            namespace,
            self._binding_pointer_holder_owner_paths,
        )
        context = PythonSurfaceContext(
            allocatable_holder_identities=frozenset(derived.type_identity for derived in allocatable_holders),
            pointer_holder_identities=frozenset(derived.type_identity for derived in pointer_holders),
            nullable_module_proxy_owner_paths=frozenset(
                variable.owner_path for variable in namespace.variables if self._nullable_derived_module_proxy(variable)
            ),
        )
        source = PythonSurfaceEmitter(context).emit(namespace)
        literal = self._c_string_literal(source)
        result_name = f"{self._namespace_symbol(namespace)}_python_setup"
        dictionary = f"{self._namespace_symbol(namespace)}_python_dict"
        return (
            CDeclaration(dictionary, "PyObject *", CodeExpression(f"PyModule_GetDict({module_object})")),
            CIf(CodeExpression(f"{dictionary} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CDeclaration(
                result_name,
                "PyObject *",
                CodeExpression(f"PyRun_String({literal}, Py_file_input, {dictionary}, {dictionary})"),
            ),
            CIf(CodeExpression(f"{result_name} == NULL"), body=(CReturn(CodeExpression("NULL")),)),
            CExpressionStatement(CodeExpression(f"Py_DECREF({result_name})")),
        )

    @staticmethod
    def _c_string_literal(value: str) -> str:
        """Escape generated Python helper source as one C string literal."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'

    def _module_native_array_owner_nodes(
        self,
        namespace: NamespacePlan,
        _module_object: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Retain the root extension package for every borrowed native array."""
        nodes = []
        for variable in namespace.variables:
            if variable.binding.getter_action not in {
                ModuleGetterAction.BORROWED_ARRAY_VIEW,
                ModuleGetterAction.NATIVE_ARRAY_HANDLE,
            }:
                continue
            owner = self._module_native_array_owner_name(variable)
            nodes.extend(
                (
                    CExpressionStatement(CodeExpression("Py_INCREF(mod)")),
                    CExpressionStatement(CodeExpression(f"{owner} = mod")),
                )
            )
        return tuple(nodes)

    def _derived_module_owner_nodes(
        self,
        namespace: NamespacePlan,
        module_object: str,
    ) -> tuple[CExpressionStatement, ...]:
        """Retain one module reference for each live borrowed derived object."""
        nodes = []
        for variable in namespace.variables:
            if variable.derived is None:
                continue
            owner = self._derived_module_owner_name(variable)
            nodes.extend(
                (
                    CExpressionStatement(CodeExpression(f"Py_INCREF({module_object})")),
                    CExpressionStatement(CodeExpression(f"{owner} = {module_object}")),
                )
            )
        return tuple(nodes)

    def _module_initializer_nodes(self, namespace: NamespacePlan) -> tuple[CExpressionStatement, ...]:
        """Return import-time native assignments selected by completed policy."""
        return tuple(
            CExpressionStatement(
                CodeExpression(
                    f"{self._module_bridge_setter_name(variable)}("
                    f"{self._module_literal(variable, variable.binding.initializer)})"
                )
            )
            for variable in namespace.variables
            if variable.binding.initializer is not None
        )

    def _module_constant_nodes(
        self,
        namespace: NamespacePlan,
        module_object: str,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Materialize scalar constants in the ordinary module dictionary."""
        nodes = []
        index = 0
        for variable in namespace.variables:
            if variable.binding.getter_action not in {
                ModuleGetterAction.CONSTANT_VALUE,
                ModuleGetterAction.NATIVE_CONSTANT_VALUE,
                ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
            }:
                continue
            for python_name in variable.binding.python_names:
                value_name = f"constant_{variable.symbol_name}_value_{index}"
                object_name = f"constant_{variable.symbol_name}_object_{index}"
                nodes.extend(
                    (
                        *self._module_constant_declarations(variable, value_name, object_name),
                        CExpressionStatement(
                            CodeExpression(f"if ({object_name} == NULL) {{ Py_DECREF(mod); return NULL; }}")
                        ),
                        CExpressionStatement(
                            CodeExpression(
                                f'if (PyModule_AddObject({module_object}, "{python_name}", {object_name}) < 0) '
                                f"{{ Py_DECREF({object_name}); Py_DECREF(mod); return NULL; }}"
                            )
                        ),
                    )
                )
                index += 1
        return tuple(nodes)

    def _module_constant_declarations(
        self,
        variable: ModuleVariablePlan,
        value_name: str,
        object_name: str,
    ) -> tuple[CDeclaration | CExpressionStatement, ...]:
        """Materialize one planned binding or native constant value."""
        if variable.binding.getter_action is ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE:
            return self._module_constant_array_declarations(variable, value_name, object_name)
        if variable.datatype_family is DatatypeFamily.STRING:
            literal = self._c_string_literal(str(variable.binding.constant_value))
            return (
                CDeclaration(
                    object_name,
                    "PyObject *",
                    CodeExpression(f"PyUnicode_FromString({literal})"),
                ),
            )
        scalar_type = PrimitiveScalarTypeRegistry.type_for(variable.semantic_type_name)
        value_expression = (
            f"{self._module_bridge_getter_name(variable)}()"
            if variable.binding.getter_action is ModuleGetterAction.NATIVE_CONSTANT_VALUE
            else self._module_literal(variable, variable.binding.constant_value)
        )
        return (
            CDeclaration(value_name, scalar_type.c_spelling, CodeExpression(value_expression)),
            CDeclaration(
                object_name,
                "PyObject *",
                CodeExpression(self._scalar_result_expression(scalar_type, f"&{value_name}", module=True)),
            ),
        )

    def _module_constant_array_declarations(
        self,
        variable: ModuleVariablePlan,
        value_name: str,
        object_name: str,
    ) -> tuple[CDeclaration | CExpressionStatement]:
        """Materialize one compiler-evaluated parameter array as a read-only NumPy snapshot."""
        array = variable.array
        if array is None or array.rank is None or array.rank <= 0:
            raise ValueError(f"Module parameter array {variable.owner_path!r} has no fixed array plan")
        # A character element is a fixed-width bytes dtype whose width is the
        # Fortran element length. The parameter reports that length itself, so
        # a `len=*` declaration works the same as a declared one.
        character = variable.datatype_family is DatatypeFamily.STRING
        itemsize_name = f"{value_name}_itemsize"
        if character:
            allocation = (
                f"(PyObject *)PyArray_New(&PyArray_Type, {array.rank}, {{dimensions}}, NPY_STRING, "
                f"NULL, NULL, (int){itemsize_name}, NPY_ARRAY_F_CONTIGUOUS | NPY_ARRAY_WRITEABLE, NULL)"
            )
        else:
            scalar_type = PrimitiveScalarTypeRegistry.type_for(variable.semantic_type_name)
            allocation = f"(PyObject *)PyArray_EMPTY({array.rank}, {{dimensions}}, {scalar_type.numpy_type_macro}, 1)"
        width_names = (itemsize_name,) if character else ()
        extent_names = tuple(f"{value_name}_extent_{axis}" for axis in range(array.rank))
        dimensions = f"{value_name}_dimensions"
        reported = (*width_names, *extent_names)
        return (
            *(CDeclaration(name, "int64_t", CodeExpression("0")) for name in reported),
            CDeclaration(
                value_name,
                "void *",
                CodeExpression(
                    f"{self._module_bridge_getter_name(variable)}({', '.join(f'&{name}' for name in reported)})"
                ),
            ),
            CExpressionStatement(
                CodeExpression(f"if ({value_name} == NULL) {{ PyErr_NoMemory(); Py_DECREF(mod); return NULL; }}")
            ),
            CDeclaration(
                f"{dimensions}[{array.rank}]",
                "npy_intp",
                CodeExpression("{" + ", ".join(f"(npy_intp){extent}" for extent in extent_names) + "}"),
            ),
            CDeclaration(
                object_name,
                "PyObject *",
                CodeExpression(allocation.format(dimensions=dimensions)),
            ),
            CExpressionStatement(CodeExpression(f"if ({object_name} == NULL) {{ Py_DECREF(mod); return NULL; }}")),
            CExpressionStatement(
                CodeExpression(
                    f"memcpy(PyArray_DATA((PyArrayObject *){object_name}), {value_name}, "
                    f"PyArray_NBYTES((PyArrayObject *){object_name}))"
                )
            ),
            CExpressionStatement(
                CodeExpression(f"PyArray_CLEARFLAGS((PyArrayObject *){object_name}, NPY_ARRAY_WRITEABLE)")
            ),
        )

    def _module_literal(self, plan: ModuleVariablePlan, value: object) -> str:
        """Dispatch one completed datatype family to its C literal spelling."""
        family = plan.datatype_family
        match family:
            case DatatypeFamily.BOOL:
                return self._lower_module_literal_bool(value)
            case DatatypeFamily.INTEGER:
                return self._lower_module_literal_integer(value)
            case DatatypeFamily.REAL:
                return self._lower_module_literal_real(value)
            case DatatypeFamily.COMPLEX:
                return self._lower_module_literal_complex(value)
        raise ValueError(f"Unsupported C module literal family for {plan.owner_path!r}: {family!r}")

    # Scalar module-literal lowering.
    def _lower_module_literal_bool(self, value: object) -> str:
        """Lower module literal bool from the supplied local lowering values without inferring semantic policy."""
        return "true" if value else "false"

    def _lower_module_literal_integer(self, value: object) -> str:
        """Lower module literal integer from the supplied local lowering values without inferring semantic policy."""
        return str(value)

    def _lower_module_literal_real(self, value: object) -> str:
        """Lower module literal real from the supplied local lowering values without inferring semantic policy."""
        return repr(value)

    def _lower_module_literal_complex(self, value: object) -> str:
        """Lower module literal complex from the supplied local lowering values without inferring semantic policy."""
        number = complex(value)
        return f"({number.real!r} + {number.imag!r} * I)"

    def _binding_parameters(self, plan: FunctionPlan | None = None) -> tuple[CParameter, ...]:
        """Build binding parameters from the supplied local lowering values; emitted nodes only project completed binding actions."""
        parameters = (CParameter("self", "PyObject *"), CParameter("args", "PyObject *"))
        if plan is not None and not plan.binding.accepts_keyword_arguments:
            return parameters
        return (*parameters, CParameter("kwargs", "PyObject *"))

    def _binding_function_name(self, plan: FunctionPlan) -> str:
        """Return the binding-local binding function name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"wrap_{plan.symbol_name}"

    def _entrypoint_function_name(self, plan: FunctionPlan) -> str:
        """Return the symbol the binding declares and calls for one entrypoint.

        Planning selects a collision-adapter forwarder when the binding must
        not declare the native symbol itself; the forwarder is defined in the
        separate adapter translation unit built by :meth:`binding_modules`.
        """
        return plan.entrypoint.collision_adapter_symbol or plan.entrypoint.symbol_name

    def _module_getter_name(self, plan: ModuleVariablePlan) -> str:
        """Return the binding-local module getter name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"module_get_{plan.symbol_name}"

    def _module_setter_name(self, plan: ModuleVariablePlan) -> str:
        """Return the binding-local module setter name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"module_set_{plan.symbol_name}"

    def _module_bridge_getter_name(self, plan: ModuleVariablePlan) -> str:
        """Return the shared module-variable getter entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(plan.owner_path, "module:get").symbol_name

    def _module_bridge_setter_name(self, plan: ModuleVariablePlan) -> str:
        """Return the shared module-variable setter entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(plan.owner_path, "module:set").symbol_name

    @staticmethod
    def _nullable_derived_module_proxy(plan: ModuleVariablePlan) -> bool:
        """Return whether the completed module storage has descriptor presence."""
        return bool(
            plan.derived is not None
            and plan.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY
            and plan.derived.handoff.storage
            in {
                DerivedObjectStorage.MODULE_ALLOCATABLE,
                DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
                DerivedObjectStorage.MODULE_POINTER,
            }
        )

    def _module_derived_presence_bridge_name(self, plan: ModuleVariablePlan) -> str:
        """Return the planner-owned nullable module-derived presence symbol."""
        return self._generated_support_procedure_entrypoint(plan.owner_path, "module:derived:present").symbol_name

    @staticmethod
    def _module_derived_presence_method_name(plan: ModuleVariablePlan) -> str:
        """Return the binding-local module derived presence method name derived from the supplied completed binding records; this helper preserves completed policy."""
        return CBindingNames.module_derived_presence_method(plan)

    def _functions(self, plan: ModulePlan) -> tuple[FunctionPlan, ...]:
        """Build functions from the supplied completed binding records; emitted nodes only project completed binding actions."""
        return tuple(function for namespace in plan.namespaces for function in namespace.functions)

    def _variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return variables from the supplied completed binding records; this helper preserves the selected binding behavior."""
        return tuple(variable for namespace in plan.namespaces for variable in namespace.variables)

    def _namespace(self, plan: ModulePlan, python_path: tuple[str, ...]) -> NamespacePlan:
        """Return the binding-local namespace derived from the supplied completed binding records; this helper preserves completed policy."""
        for namespace in plan.namespaces:
            if namespace.python_path == python_path:
                return namespace
        raise ValueError(f"{plan.owner_path!r} has no namespace {python_path!r}")

    def _namespace_symbol(self, plan: NamespacePlan) -> str:
        """Return the binding-local namespace symbol derived from the supplied completed binding records; this helper preserves completed policy."""
        return "_".join(plan.python_path).casefold() if plan.python_path else "root"

    def _namespace_object_name(self, plan: NamespacePlan) -> str:
        """Return the binding-local namespace object name derived from the supplied completed binding records; this helper preserves completed policy."""
        return f"namespace_{self._namespace_symbol(plan)}" if plan.python_path else "mod"

    def _namespace_module_name(self, module: ModulePlan, namespace: NamespacePlan) -> str:
        """Return the binding-local namespace module name derived from the supplied completed binding records; this helper preserves completed policy."""
        return ".".join((module.binding.owner_path, *namespace.python_path))


if __name__ == "__main__":
    from prik.planning.planner import WrapperPlanner
    from prik.policy.completion import complete_semantic_policies
    from prik.printers.c import CSourcePrinter
    from prik.semantics.models import SemanticArgument, SemanticFunction, SemanticModule, SemanticType

    module = SemanticModule(
        name="binding_demo",
        functions=[
            SemanticFunction(
                name="double_value",
                native_name="DOUBLE_VALUE",
                arguments=[SemanticArgument("value", SemanticType("Float64"))],
                return_type=SemanticType("Float64"),
            )
        ],
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    binding = CBindingGenerator()
    binding.require_supported(plan)
    c_module, c_header = binding.visit(plan)
    wrapper = next(function for function in c_module.functions if function.name == "wrap_double_value")

    printer = CSourcePrinter()
    print("Rendered C header:")
    print(printer.doprint(c_header))
    print()
    print("Rendered C binding wrapper:")
    print(printer.doprint(wrapper))
