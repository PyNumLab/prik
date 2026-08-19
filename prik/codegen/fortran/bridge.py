"""Lower validated wrapper plans into Fortran bridge syntax nodes.

Use :class:`FortranBridgeGenerator` after post-IR policy completion and wrapper
planning.  Its :meth:`visit` method consumes a validated `ModulePlan` and
returns a `FortranModule` for the source printer.  This stage does not infer
ownership, argument, or result policy: it dispatches only the completed bridge
actions already projected into the plan.
"""

from __future__ import annotations

from dataclasses import replace
import re

from prik.utilities.declaration_expressions import render_declaration_extent
from prik.policy.ownership import (
    AssignmentMode,
    CodegenAction,
    NativeBarrierAction,
    ObjectKind,
    SetterAction,
)
from prik.semantics.metadata import SCALAR_STORAGE_CATEGORY
from prik.policy.models import (
    ArgumentHandoffMode,
    ArrayLogicalABI,
    ArrayWritebackABI,
    BridgeDataAction,
    CallbackABIKind,
    CallbackResultAction,
    CallbackTransferAction,
    ClassInvocationKind,
    DerivedActualAccess,
    DerivedCallAction,
    DerivedFieldAccessMechanism,
    DerivedNativeHandoff,
    DerivedDummyCategory,
    DerivedObjectStorage,
    DeclarationCallableAction,
    DirectResultABI,
    ExternalDeclarationMode,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    CharacterLocalRelease,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorInterop,
    NativeArrayDefaultConstruction,
    NativeArrayOperation,
    NativeArrayResultAllocation,
    NativeDescriptorHandoffABI,
    NativeInvocationKind,
    EntrypointPassingConvention,
    EntrypointProjectionAction,
    OptionalMode,
    ScalarLogicalABI,
)
from prik.semantics.scalar_types import is_boolean_semantic_type_name
from prik.codegen.nodes import (
    CodeExpression,
    FortranAllocate,
    FortranAssignment,
    FortranCall,
    FortranCase,
    FortranDeclaration,
    FortranDeallocate,
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
from prik.planning.models import (
    ArrayHandoffPlan,
    ArgumentTransferPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    CharacterLocalPlan,
    ClassSurfacePlan,
    DatatypeFamily,
    DeclarationCallablePlan,
    DerivedFieldPlan,
    DerivedMemberPathPlan,
    DerivedTypePlan,
    FunctionPlan,
    ModulePlan,
    ModuleVariablePlan,
    NamespacePlan,
    NativeArrayHandlePlan,
    NativeEntrypointABIValueKind,
    NativeEntrypointABIValuePlan,
    GeneratedSupportProcedureImplementationOwner,
    GeneratedSupportProcedureEntrypointPlan,
    NativeEntrypointParameterPlan,
    NativeEntrypointProjectedSlotPlan,
    NativeEntrypointResultPlan,
    ProcedurePrototypeArgumentPlan,
    ProcedurePrototypePlan,
    ProcedurePrototypeResultPlan,
    ResultPlan,
)
from prik.codegen.primitive_scalar_types import PrimitiveScalarTypeRegistry
from prik.codegen.visitor import ClassVisitor


class FortranBridgeGenerator(ClassVisitor):
    """Build the Fortran half of a wrapper from validated bridge-plan views.

    Instantiate this visitor when direct generation needs backend syntax nodes,
    rather than rendered source.  Call :meth:`require_supported` for the
    backend-local type preflight and then :meth:`visit` with a `ModulePlan`.
    The result is a `FortranModule` consumed by `FortranSourcePrinter`.
    Completed policy stays outside this class; unmatched lowering actions fail
    defensively instead of being reinterpreted here.
    """

    def require_supported(self, plan: ModulePlan) -> None:
        """Preflight primitive spellings required by an already-validated plan.

        Call this before :meth:`visit` when using the bridge generator
        directly.  It resolves only the primitive types the Fortran backend
        must emit; plan consistency and semantic-policy decisions remain owned
        by earlier stages.  Unsupported registry entries propagate their normal
        lookup error.
        """
        for derived in self._derived_types(plan):
            self._require_derived_type_supported(derived)
        for function in self._functions(plan):
            if function.bridge is not None:
                self._require_function_supported(function)
        for variable in self._variables(plan):
            self._require_variable_supported(variable)

    def _require_function_supported(self, function: FunctionPlan) -> None:
        """Preflight primitive types after shared plan validation."""
        for argument in function.arguments:
            self._require_argument_supported(argument)
        for result in function.results:
            self._require_backend_type_supported(result.semantic_type_name, result.datatype_family)
        for slot in self._adapter_slots(function):
            if slot.source_kind == "result":
                self._require_backend_type_supported(slot.semantic_type_name, slot.datatype_family)

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

    def _require_variable_supported(self, variable: ModuleVariablePlan) -> None:
        """Preflight only the primitive registry needed by Fortran emission."""
        self._require_backend_type_supported(variable.semantic_type_name, variable.datatype_family)

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

    @staticmethod
    def _adapter_slots(function: FunctionPlan) -> tuple[NativeEntrypointProjectedSlotPlan, ...]:
        """Return ordered projected slots that carry adapter-local actions."""
        return tuple(
            slot
            for slot in sorted(function.entrypoint.projected_slots, key=lambda item: item.native_position)
            if slot.adapter is not None
        )

    def _visit_ModulePlan(self, plan: ModulePlan) -> FortranModule:
        """Build one complete bridge module from one validated module plan."""
        self._generated_support_procedure_entrypoints = {
            (procedure.owner_path, procedure.role): procedure for procedure in plan.entrypoint.support_procedures
        }
        self._derived_owner_paths = {
            derived.backend_symbol: derived.owner_path for derived in self._derived_types(plan)
        }
        if plan.bridge is None:
            raise ValueError(f"Fortran lowering requires a bridge plan for {plan.owner_path!r}")
        self._bridge_allocatable_holder_owner_paths = frozenset(plan.bridge.allocatable_holder_type_owner_paths)
        self._bridge_pointer_holder_owner_paths = frozenset(plan.bridge.pointer_holder_type_owner_paths)
        self._bridge_allocatable_holder_field_owner_paths = frozenset(
            plan.bridge.allocatable_holder_field_type_owner_paths
        )
        self._bridge_pointer_holder_field_owner_paths = frozenset(plan.bridge.pointer_holder_field_type_owner_paths)
        # Scoped origins are module-wide facts needed by derived-call lowering.
        scoped_origin_type_identities = self._scoped_origin_type_identities(plan)
        procedures = (
            *(
                procedure
                for namespace in plan.namespaces
                for procedure in self.visit(namespace, scoped_origin_type_identities)
            ),
            # Typed derived-field access remains separate from class orchestration.
            *self._derived_field_procedures(plan),
            # Native-aware opaque-owner destruction is Phase 8 substrate, not class orchestration.
            *self._class_constructor_procedures(plan),
            *(
                self._derived_destroy_procedure(derived)
                for derived in self._derived_types(plan)
                if self._has_generated_support_procedure_entrypoint(derived.owner_path, "derived:destroy")
            ),
            *(
                self._allocatable_holder_destroy_procedure(derived)
                for derived in self._derived_types(plan)
                if self._has_generated_support_procedure_entrypoint(derived.owner_path, "holder:allocatable:destroy")
            ),
            *(
                self._allocatable_holder_presence_procedure(derived)
                for derived in self._derived_types(plan)
                if self._has_generated_support_procedure_entrypoint(derived.owner_path, "holder:allocatable:present")
            ),
            *(
                self._pointer_holder_destroy_procedure(derived)
                for derived in self._derived_types(plan)
                if self._has_generated_support_procedure_entrypoint(derived.owner_path, "holder:pointer:destroy")
            ),
            *(
                self._pointer_holder_presence_procedure(derived)
                for derived in self._derived_types(plan)
                if self._has_generated_support_procedure_entrypoint(derived.owner_path, "holder:pointer:present")
            ),
            *(
                procedure
                for variable in self._derived_origin_variables(plan)
                for procedure in self._derived_origin_procedures(variable)
            ),
        )
        # Assemble imports, declarations, and procedures from plan projections.
        return FortranModule(
            name=f"bind_c_{plan.entrypoint.owner_path}_wrapper",
            uses=(
                FortranUse("iso_c_binding", self._iso_c_symbols(plan)),
                *self._native_module_uses(plan),
            ),
            type_definitions=self._derived_holder_definitions(plan),
            interfaces=(
                *self._derived_call_interfaces(plan),
                *self._prototype_interfaces(plan),
                *self._external_interfaces(plan),
                *self._module_descriptor_callback_interfaces(plan),
                *self._derived_array_callback_interfaces(plan),
                *self._allocator_interfaces(plan),
            ),
            declarations=self._prototype_entity_declarations(plan),
            procedures=self._apply_generated_support_procedure_entrypoints(procedures),
            standalone_procedures=self._callback_standalone_adapter_procedures(plan),
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

    def _generated_support_procedure_entrypoint_function(
        self,
        operation: GeneratedSupportProcedureEntrypointPlan,
        function: FortranFunction,
    ) -> FortranFunction:
        """Apply one planner-owned bridge ABI to an adapter-local procedure body."""
        if operation.implementation_owner is not GeneratedSupportProcedureImplementationOwner.FORTRAN:
            raise ValueError(f"Fortran cannot implement binding-owned operation {operation.key!r}")
        result_type = self._support_procedure_fortran_type(operation.signature.result)
        is_subroutine = operation.signature.result.kind is NativeEntrypointABIValueKind.VOID
        return replace(
            function,
            name=operation.symbol_name,
            parameters=tuple(
                self._support_procedure_fortran_parameter(parameter) for parameter in operation.signature.parameters
            ),
            result_name=None if is_subroutine else function.result_name,
            result_type=None if is_subroutine else result_type,
            bind_name=operation.symbol_name,
            is_subroutine=is_subroutine,
        )

    def _apply_generated_support_procedure_entrypoints(
        self,
        procedures: tuple[FortranFunction, ...],
    ) -> tuple[FortranFunction, ...]:
        """Join every adapter-local body to exactly one planner-owned C ABI."""
        operations = {
            operation.symbol_name: operation
            for operation in self._generated_support_procedure_entrypoints.values()
            if operation.implementation_owner is GeneratedSupportProcedureImplementationOwner.FORTRAN
        }
        generated = {procedure.name for procedure in procedures if procedure.name in operations}
        missing = tuple(symbol for symbol in operations if symbol not in generated)
        if missing:
            raise ValueError(f"Fortran lowering did not implement planned support procedures: {missing!r}")
        return tuple(
            self._generated_support_procedure_entrypoint_function(operations[procedure.name], procedure)
            if procedure.name in operations
            else procedure
            for procedure in procedures
        )

    def _support_procedure_fortran_parameter(
        self,
        value: NativeEntrypointABIValuePlan,
    ) -> FortranParameter:
        """Lower one generated-support C-ABI value as a Fortran dummy."""
        type_name = self._support_procedure_fortran_type(value)
        if value.kind is NativeEntrypointABIValueKind.DESCRIPTOR:
            if value.descriptor_kind is None or value.rank is None:
                raise ValueError(f"Generated-support descriptor {value.role!r} is incomplete")
            attributes = (
                value.descriptor_kind.value,
                self._array_dimension_attribute(value.rank),
                *((f"intent({value.intent})",) if value.intent is not None else ()),
            )
        elif value.kind is NativeEntrypointABIValueKind.CHARACTER:
            if value.character_length is None:
                raise ValueError(f"Generated-support character value {value.role!r} has no length")
            attributes = (
                f"dimension({value.character_length})",
                *((f"intent({value.intent})",) if value.intent is not None else ()),
            )
        elif value.intent is not None:
            attributes = (f"intent({value.intent})",)
        elif value.pointer_depth == 0 or value.kind in {
            NativeEntrypointABIValueKind.OPAQUE,
            NativeEntrypointABIValueKind.CALLBACK,
        }:
            attributes = ("value",)
        else:
            attributes = ()
        return FortranParameter(value.fortran_name, type_name, attributes)

    @staticmethod
    def _support_procedure_fortran_type(value: NativeEntrypointABIValuePlan) -> str | None:
        """Spell one structured generated-support ABI value for Fortran."""
        if value.kind is NativeEntrypointABIValueKind.SEMANTIC_SCALAR:
            if value.semantic_type_name is None:
                raise ValueError(f"Generated-support ABI value {value.role!r} has no semantic scalar type")
            return PrimitiveScalarTypeRegistry.type_for(value.semantic_type_name).fortran_spelling
        types = {
            NativeEntrypointABIValueKind.VOID: None,
            NativeEntrypointABIValueKind.BOOL: "logical(c_bool)",
            NativeEntrypointABIValueKind.INT: "integer(c_int)",
            NativeEntrypointABIValueKind.INT8: "integer(c_int8_t)",
            NativeEntrypointABIValueKind.INT64: "integer(c_int64_t)",
            NativeEntrypointABIValueKind.OPAQUE: "type(c_ptr)",
            NativeEntrypointABIValueKind.CHARACTER: "character(kind=c_char)",
            NativeEntrypointABIValueKind.CALLBACK: "type(c_funptr)",
        }
        if value.kind is NativeEntrypointABIValueKind.DESCRIPTOR:
            if value.semantic_type_name is None:
                raise ValueError(f"Generated-support descriptor {value.role!r} has no element type")
            return PrimitiveScalarTypeRegistry.type_for(value.semantic_type_name).fortran_spelling
        try:
            return types[value.kind]
        except KeyError:
            raise ValueError(f"Unsupported generated-support Fortran ABI kind {value.kind.value!r}") from None

    def _callback_standalone_adapter_procedures(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Return separately linked callback adapters in stable site order."""
        return tuple(
            self._callback_standalone_adapter_procedure(callback, plan) for callback in self._callback_sites(plan)
        )

    def _derived_holder_definitions(self, plan: ModulePlan) -> tuple[FortranTypeDefinition, ...]:
        """Define one allocatable and pointer carrier per qualified native type."""
        allocatable = tuple(
            FortranTypeDefinition(
                self._allocatable_holder_type_name(derived.backend_symbol),
                (
                    FortranDeclaration(
                        "value",
                        f"type({self._derived_native_alias(derived.backend_symbol)})",
                        ("allocatable",),
                    ),
                ),
            )
            for derived in self._bridge_support_types(plan, self._bridge_allocatable_holder_owner_paths)
        )
        pointers = tuple(
            FortranTypeDefinition(
                self._pointer_holder_type_name(derived.backend_symbol),
                (
                    FortranDeclaration(
                        "value",
                        f"type({self._derived_native_alias(derived.backend_symbol)})",
                        ("pointer",),
                    ),
                ),
            )
            for derived in self._bridge_support_types(plan, self._bridge_pointer_holder_owner_paths)
        )
        return (*allocatable, *pointers)

    def _visit_NamespacePlan(
        self,
        plan: NamespacePlan,
        scoped_origin_type_identities: frozenset[tuple[str, str]] = frozenset(),
    ) -> tuple[FortranFunction, ...]:
        """Return bridge procedures directly owned by one Python namespace."""
        return (
            *(
                procedure
                for function in plan.functions
                if function.bridge is not None
                for procedure in (
                    self.visit(function, scoped_origin_type_identities),
                    *self._owned_native_array_result_operations(function),
                )
            ),
            *(
                procedure
                for function in plan.functions
                for procedure in self._default_native_array_argument_operations(function)
            ),
            *(procedure for variable in plan.variables for procedure in self.visit(variable)),
        )

    def _visit_FunctionPlan(
        self,
        plan: FunctionPlan,
        scoped_origin_type_identities: frozenset[tuple[str, str]] = frozenset(),
    ) -> FortranFunction:
        """Build one bridge procedure through ABI, call, and cleanup stages.

        All declarations and nodes come from completed function-plan actions;
        this orchestration only preserves their required execution order.
        """
        # Stage 1: determine the entrypoint ABI and result representation.
        result_name, result_type = self._lower_result(plan)
        owned_direct_result = self._owned_direct_result(plan)
        parameters = tuple(
            parameter
            for group in sorted(plan.entrypoint.parameters, key=lambda item: item.position)
            for parameter in self._entrypoint_parameter_declarations(plan, group)
        )
        entrypoint_name = self._entrypoint_function_name(plan)
        is_subroutine = plan.bridge.native_is_subroutine or owned_direct_result is not None
        # Stage 2: assemble the native invocation and its ordered finalizers.
        function_body, optional_procedures = self._function_body(plan, result_name)
        native_body = (
            *self._derived_pointer_call_initializers(plan),
            *function_body,
            *self._logical_scalar_argument_finalizers(plan),
            *self._logical_array_argument_finalizers(plan),
            *self._array_writeback_finalizers(plan),
            *self._derived_pointer_call_finalizers(plan),
            *self._required_descriptor_finalizers(plan),
            *self._string_value_finalizers(plan),
            *self._string_address_finalizers(plan),
            *self._direct_result_finalizers(plan),
            *self._native_output_finalizers(plan),
            *self._character_local_release_finalizers(plan),
        )
        # Stage 3: wrap native execution in derived-result and carrier lifecycles.
        call_body = self._derived_result_execution(plan, result_name, native_body)
        derived_body, internal_procedures = self._derived_call_execution(
            plan,
            call_body,
            scoped_origin_type_identities,
        )
        return FortranFunction(
            name=entrypoint_name,
            parameters=parameters,
            result_name=result_name,
            result_type=result_type,
            bind_name=entrypoint_name,
            declarations=(
                *self._callback_external_declarations(plan),
                *self._native_external_declarations(plan),
                *self._optional_declarations(plan),
                *self._logical_scalar_argument_declarations(plan),
                *self._opaque_address_declarations(plan),
                *self._array_declarations(plan),
                *self._raw_array_address_declarations(plan),
                *self._string_value_declarations(plan),
                *self._string_address_declarations(plan),
                *self._derived_call_declarations(plan),
                *self._direct_result_declarations(plan),
                *self._native_output_declarations(plan),
                *self._derived_result_allocation_declarations(plan),
            ),
            body=(
                *self._character_local_initializers(plan),
                *self._descriptor_initializers(plan),
                *self._required_descriptor_initializers(plan),
                *self._logical_scalar_argument_initializers(plan),
                *self._opaque_address_initializers(plan),
                *self._array_initializers(plan),
                *self._logical_array_argument_initializers(plan),
                *self._raw_array_address_initializers(plan),
                *self._string_value_initializers(plan),
                *self._string_address_initializers(plan),
                *self._declaration_extent_result_assignments(plan),
                *self._direct_array_result_initializers(plan),
                *derived_body,
            ),
            is_subroutine=is_subroutine,
            internal_procedures=(
                *optional_procedures,
                *self._direct_result_internal_procedures(plan),
                *internal_procedures,
            ),
        )

    def _entrypoint_parameter_declarations(
        self,
        plan: FunctionPlan,
        parameter: NativeEntrypointParameterPlan,
    ) -> tuple[FortranParameter, ...]:
        """Lower one shared C-ABI parameter group into a bind(C) declaration."""
        if parameter.source_kind == "argument":
            return self.visit(self._argument_by_owner(plan, parameter.owner_path))
        if parameter.source_kind == "projected_slot":
            return self._projected_slot_parameters(self._projected_slot_for_parameter(plan, parameter))
        result = self._result_by_owner(plan, parameter.owner_path)
        if parameter.source_kind == "hidden_result":
            return self._native_output_parameters_for_result(result)
        if parameter.source_kind == "direct_result":
            return (
                *self._owned_direct_result_parameters(result),
                *self._scalar_descriptor_direct_result_parameters_for_result(result),
            )
        if parameter.source_kind == "declaration_extent":
            return self._declaration_extent_result_parameters_for_result(result)
        raise ValueError(f"Unsupported entrypoint parameter group {parameter.source_kind!r}")

    @staticmethod
    def _argument_by_owner(plan: FunctionPlan, owner_path: str) -> ArgumentTransferPlan:
        """Return the argument referenced by one entrypoint parameter group."""
        return next(argument for argument in plan.arguments if argument.owner_path == owner_path)

    @staticmethod
    def _result_by_owner(plan: FunctionPlan, owner_path: str) -> NativeEntrypointResultPlan:
        """Return the C-ABI result referenced by one entrypoint parameter group."""
        return next(result for result in plan.entrypoint.results if result.owner_path == owner_path)

    @staticmethod
    def _projected_slot_for_parameter(
        plan: FunctionPlan,
        parameter: NativeEntrypointParameterPlan,
    ) -> NativeEntrypointProjectedSlotPlan:
        """Return the shared projected slot referenced by one adapter parameter."""
        return next(
            slot for slot in plan.entrypoint.projected_slots if slot.native_position == parameter.native_position
        )

    @staticmethod
    def _projected_slot_parameters(
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[FortranParameter, ...]:
        """Declare one binding-materialized projection at the shared C ABI."""
        if slot.semantic_type_name is None:
            raise ValueError(f"Projected slot {slot.owner_path!r} has no semantic type")
        type_name = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name).fortran_spelling
        if slot.passing is EntrypointPassingConvention.C_VALUE:
            attributes = ("value",)
        elif slot.passing in {
            EntrypointPassingConvention.POINTER_REFERENCE,
            EntrypointPassingConvention.NULLABLE_POINTER,
        }:
            attributes = ()
        else:
            raise ValueError(f"Unsupported projected Fortran parameter passing {slot.passing.value!r}")
        return (FortranParameter(slot.native_name.casefold(), type_name, attributes),)

    def _declaration_extent_result_parameters_for_result(
        self,
        result: NativeEntrypointResultPlan,
    ) -> tuple[FortranParameter, ...]:
        """Expose bridge-evaluated extents for one entrypoint result group."""
        if result.array is None:
            return ()
        return tuple(
            FortranParameter(
                self._declaration_extent_result_name(result, axis),
                "integer(c_int64_t)",
                ("intent(out)",),
            )
            for axis, evaluation in enumerate(result.array.extent_evaluation)
            if evaluation == "bridge"
        )

    def _declaration_extent_result_assignments(self, plan: FunctionPlan) -> tuple[FortranAssignment, ...]:
        """Evaluate native-dependent result axes inside the Fortran bridge."""
        assignments = []
        for result in plan.results:
            if result.array is None or "bridge" not in result.array.extent_evaluation:
                continue
            shape = self._array_shape_from_roles(result.array, plan)
            assignments.extend(
                FortranAssignment(
                    self._declaration_extent_result_name(result, axis),
                    CodeExpression(f"int({shape[axis]}, c_int64_t)"),
                )
                for axis, evaluation in enumerate(result.array.extent_evaluation)
                if evaluation == "bridge"
            )
        return tuple(assignments)

    @staticmethod
    def _declaration_extent_result_name(result: ResultPlan | NativeEntrypointResultPlan, axis: int) -> str:
        """Return the shared entrypoint ABI name for one evaluated result axis."""
        return f"prik_decl_extent_{result.result_position}_{axis}"

    # Immediate callback adapters.
    def _callback_standalone_adapter_procedure(
        self,
        callback: CallbackHandoffPlan,
        plan: ModulePlan,
    ) -> FortranFunction:
        """Adapt one native callback through a separately declared external procedure."""
        result = callback.result.transfer
        is_subroutine = callback.result.action is CallbackResultAction.RETURN_VOID
        trampoline_name = f"{callback.entrypoint.support_procedure.symbol_name}_call"
        return FortranFunction(
            name=callback.bridge.adapter_symbol,
            parameters=tuple(self._callback_native_parameter(transfer) for transfer in callback.arguments),
            result_name=None if is_subroutine else "callback_result",
            result_type=None if is_subroutine else self._callback_native_result_type(result),
            uses=self._callback_standalone_adapter_uses(callback, plan),
            implicit_none=True,
            interfaces=(
                FortranInterface(
                    (
                        self._callback_c_interface(
                            callback,
                            name=trampoline_name,
                            bind_name=callback.entrypoint.support_procedure.symbol_name,
                        ),
                    )
                ),
            ),
            declarations=(
                *(
                    declaration
                    for transfer in callback.arguments
                    for declaration in self._callback_transfer_declarations(transfer)
                ),
                *self._callback_result_declarations(callback),
            ),
            body=(
                *(
                    statement
                    for transfer in callback.arguments
                    for statement in self._callback_transfer_preparation(transfer)
                ),
                *self._callback_invocation(callback, trampoline_name),
                *(
                    statement
                    for transfer in callback.arguments
                    for statement in self._callback_transfer_writeback(transfer)
                ),
                *self._callback_result_reconstruction(callback),
            ),
            is_subroutine=is_subroutine,
        )

    def _callback_native_parameter(self, transfer: CallbackTransferPlan) -> FortranParameter:
        """Declare the exact native callback dummy represented by one transfer."""
        attributes = []
        if transfer.passed_by_value:
            attributes.append("value")
        if transfer.intent is not None:
            attributes.append(f"intent({transfer.intent})")
        if transfer.abi is not CallbackABIKind.VALUE and transfer.adapter_action in {
            CallbackTransferAction.BORROW_READ_ONLY,
            CallbackTransferAction.BORROW_WRITABLE,
        }:
            attributes.append("target")
        if transfer.rank:
            attributes.append(f"dimension({self._callback_shape(transfer)})")
        return FortranParameter(
            self._callback_parameter_base_name(transfer),
            self._callback_native_type(transfer),
            tuple(attributes),
        )

    def _callback_standalone_adapter_uses(
        self,
        callback: CallbackHandoffPlan,
        plan: ModulePlan,
    ) -> tuple[FortranUse, ...]:
        """Import the native types and C ABI kinds used by one external adapter."""
        native_imports = self._callback_native_imports(callback)
        adapter_imports = (
            *(("c_loc",) if any(transfer.abi is not CallbackABIKind.VALUE for transfer in callback.arguments) else ()),
            *(
                ("c_f_pointer",)
                if callback.result.action
                in {CallbackResultAction.RETURN_ARRAY_ADDRESS, CallbackResultAction.RETURN_DERIVED_ADDRESS}
                else ()
            ),
        )
        iso_imports = tuple(
            symbol for symbol in (*native_imports, *adapter_imports) if not symbol.startswith("prik_type_")
        )
        derived_imports = tuple(symbol for symbol in native_imports if symbol.startswith("prik_type_"))
        return (
            FortranUse(
                "iso_c_binding",
                tuple(dict.fromkeys((*iso_imports, *self._callback_c_imports(callback)))),
            ),
            *(
                (
                    FortranUse(
                        f"bind_c_{plan.entrypoint.owner_path}_wrapper",
                        derived_imports,
                    ),
                )
                if derived_imports
                else ()
            ),
        )

    def _callback_external_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare every external callback adapter from its shared prototype."""
        return tuple(
            FortranDeclaration(
                callback.bridge.adapter_symbol,
                f"procedure({callback.prototype.interface_symbol})",
            )
            for callback in (
                argument.callback
                for argument in sorted(plan.arguments, key=lambda item: item.native_position)
                if argument.callback is not None
            )
        )

    def _callback_transfer_declarations(
        self,
        transfer: CallbackTransferPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare only the address and optional copy storage required by one ABI."""
        if transfer.abi is CallbackABIKind.VALUE:
            return ()
        base = self._callback_parameter_base_name(transfer)
        declarations = [FortranDeclaration(f"{base}_data", "type(c_ptr)")]
        if transfer.adapter_action in {
            CallbackTransferAction.COPY_IN,
            CallbackTransferAction.COPY_OUT,
            CallbackTransferAction.COPY_IN_OUT,
        }:
            attributes = ["target"]
            if transfer.rank:
                attributes.append(f"dimension({self._callback_shape(transfer)})")
            declarations.append(
                FortranDeclaration(
                    self._callback_storage_name(transfer),
                    self._callback_native_type(transfer),
                    tuple(attributes),
                )
            )
        return tuple(declarations)

    def _callback_transfer_preparation(
        self,
        transfer: CallbackTransferPlan,
    ) -> tuple[FortranAssignment, ...]:
        """Copy into call-local storage when selected, then expose its address."""
        if transfer.abi is CallbackABIKind.VALUE:
            return ()
        base = self._callback_parameter_base_name(transfer)
        storage = self._callback_address_source(transfer)
        statements = []
        if transfer.adapter_action in {
            CallbackTransferAction.COPY_IN,
            CallbackTransferAction.COPY_IN_OUT,
        }:
            statements.append(FortranAssignment(storage, CodeExpression(base)))
        statements.append(FortranAssignment(f"{base}_data", CodeExpression(f"c_loc({storage})")))
        return tuple(statements)

    def _callback_transfer_writeback(
        self,
        transfer: CallbackTransferPlan,
    ) -> tuple[FortranAssignment, ...]:
        """Copy writable callback storage back to the native dummy exactly once."""
        if transfer.adapter_action not in {
            CallbackTransferAction.COPY_OUT,
            CallbackTransferAction.COPY_IN_OUT,
        }:
            return ()
        return (
            FortranAssignment(
                self._callback_parameter_base_name(transfer),
                CodeExpression(self._callback_storage_name(transfer)),
            ),
        )

    def _callback_invocation(
        self,
        callback: CallbackHandoffPlan,
        callback_name: str,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Call the C trampoline once using the completed flattened ABI."""
        arguments = tuple(
            argument for transfer in callback.arguments for argument in self._callback_c_argument_expressions(transfer)
        )
        if callback.result.action is CallbackResultAction.RETURN_VOID:
            return (FortranCall(callback_name, arguments),)
        target = (
            "callback_result"
            if callback.result.action is CallbackResultAction.RETURN_SCALAR
            else "callback_result_data"
        )
        return (
            FortranAssignment(
                target,
                CodeExpression(f"{callback_name}({', '.join(argument.text for argument in arguments)})"),
            ),
        )

    def _callback_c_argument_expressions(
        self,
        transfer: CallbackTransferPlan,
    ) -> tuple[CodeExpression, ...]:
        """Flatten one native callback dummy into the matching C ABI arguments."""
        base = self._callback_parameter_base_name(transfer)
        if transfer.abi is CallbackABIKind.VALUE:
            return (CodeExpression(base),)
        if transfer.abi is CallbackABIKind.DATA_AND_SHAPE:
            storage = self._callback_address_source(transfer)
            return (
                CodeExpression(f"{base}_data"),
                *(CodeExpression(f"size({storage}, dim={axis + 1}, kind=c_int64_t)") for axis in range(transfer.rank)),
            )
        if transfer.abi is CallbackABIKind.DATA_AND_LENGTH:
            storage = self._callback_address_source(transfer)
            return (
                CodeExpression(f"{base}_data"),
                CodeExpression(f"int(len({storage}), kind=c_int64_t)"),
            )
        return (CodeExpression(f"{base}_data"),)

    def _callback_result_declarations(
        self,
        callback: CallbackHandoffPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare pointer reconstruction storage only for address results."""
        transfer = callback.result.transfer
        if callback.result.action not in {
            CallbackResultAction.RETURN_ARRAY_ADDRESS,
            CallbackResultAction.RETURN_DERIVED_ADDRESS,
        }:
            return ()
        if transfer is None:
            raise ValueError(f"Callback result {callback.owner_path!r} has no transfer plan")
        attributes = ["pointer"]
        if transfer.rank:
            attributes.append(self._array_dimension_attribute(transfer.rank))
        return (
            FortranDeclaration("callback_result_data", "type(c_ptr)"),
            FortranDeclaration(
                "callback_result_view",
                self._callback_native_type(transfer),
                tuple(attributes),
            ),
        )

    def _callback_result_reconstruction(
        self,
        callback: CallbackHandoffPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Reconstruct an address result and copy it into the native function result."""
        transfer = callback.result.transfer
        if callback.result.action is CallbackResultAction.RETURN_ARRAY_ADDRESS:
            if transfer is None:
                raise ValueError(f"Callback array result {callback.owner_path!r} has no transfer plan")
            return (
                FortranCall(
                    "c_f_pointer",
                    (
                        CodeExpression("callback_result_data"),
                        CodeExpression("callback_result_view"),
                        CodeExpression(f"[{self._callback_shape(transfer)}]"),
                    ),
                ),
                FortranAssignment("callback_result", CodeExpression("callback_result_view")),
            )
        if callback.result.action is CallbackResultAction.RETURN_DERIVED_ADDRESS:
            return (
                FortranCall(
                    "c_f_pointer",
                    (
                        CodeExpression("callback_result_data"),
                        CodeExpression("callback_result_view"),
                    ),
                ),
                FortranAssignment("callback_result", CodeExpression("callback_result_view")),
            )
        return ()

    def _callback_native_result_type(self, transfer: CallbackTransferPlan | None) -> str:
        """Return the native callback result declaration from its completed transfer."""
        if transfer is None:
            raise ValueError("Callback function result is missing its transfer plan")
        result_type = self._callback_native_type(transfer)
        if transfer.rank:
            result_type += f", dimension({self._callback_shape(transfer)})"
        return result_type

    def _callback_native_type(self, transfer: CallbackTransferPlan) -> str:
        """Return one typed native callback value without selecting behavior."""
        if transfer.abi is CallbackABIKind.DERIVED_ADDRESS:
            if transfer.derived_backend_symbol is None:
                raise ValueError(f"Callback derived transfer {transfer.owner_path!r} has no backend symbol")
            return f"type({self._derived_native_alias(transfer.derived_backend_symbol)})"
        if transfer.abi is CallbackABIKind.DATA_AND_LENGTH:
            return f"character(kind=c_char, len={transfer.character_length})"
        return PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name).fortran_spelling

    @staticmethod
    def _callback_parameter_base_name(transfer: CallbackTransferPlan) -> str:
        """Return the base Fortran dummy name reserved for one callback transfer."""
        return re.sub(r"\W", "_", transfer.name).casefold()

    def _callback_shape(self, transfer: CallbackTransferPlan) -> str:
        """Render completed callback extents in native Fortran syntax."""
        if transfer.array is None or transfer.array.rank is None:
            raise ValueError(f"Callback array transfer {transfer.owner_path!r} has no shape plan")
        return ", ".join(
            render_declaration_extent(expression, {}, target="fortran") for expression in transfer.array.shape
        )

    def _callback_address_source(self, transfer: CallbackTransferPlan) -> str:
        """Return the C-address expression that backs one callback transfer."""
        if transfer.adapter_action in {
            CallbackTransferAction.COPY_IN,
            CallbackTransferAction.COPY_OUT,
            CallbackTransferAction.COPY_IN_OUT,
        }:
            return self._callback_storage_name(transfer)
        return self._callback_parameter_base_name(transfer)

    def _callback_storage_name(self, transfer: CallbackTransferPlan) -> str:
        """Return the local storage name used while adapting one callback transfer."""
        return f"{self._callback_parameter_base_name(transfer)}_callback_storage"

    # Scalar-derived carrier preparation, invocation, and restoration.
    def _derived_arguments(self, plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return function arguments that carry completed scalar-derived call actions, preserving native-call order."""
        return tuple(
            sorted(
                (argument for argument in plan.arguments if argument.derived_call is not None),
                key=lambda argument: argument.derived_call.acquisition_order,
            )
        )

    def _derived_call_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare the same generic carrier locals for every derived datatype."""
        arguments = self._derived_arguments(plan)
        if not arguments:
            return ()
        declarations = [FortranDeclaration("prik_derived_ready", "logical")]
        for argument in arguments:
            name = argument.entrypoint.parameter_name
            native_type = f"type({self._derived_native_alias(argument.derived.backend_symbol)})"
            declarations.extend(
                (
                    FortranDeclaration(name, native_type, ("pointer",)),
                    FortranDeclaration(
                        f"{name}_allocatable_holder",
                        f"type({self._allocatable_holder_type_name(argument.derived.backend_symbol)})",
                        ("pointer",),
                    ),
                    FortranDeclaration(
                        f"{name}_pointer_holder",
                        f"type({self._pointer_holder_type_name(argument.derived.backend_symbol)})",
                        ("pointer",),
                    ),
                    FortranDeclaration(f"{name}_call_pointer", native_type, ("pointer",)),
                    FortranDeclaration(f"{name}_transaction_address", "type(c_ptr)"),
                    FortranDeclaration(f"{name}_holder_status", "integer(c_int)"),
                    FortranDeclaration(f"{name}_restore_status", "integer(c_int)"),
                    FortranDeclaration(f"{name}_created", "logical"),
                    FortranDeclaration(f"{name}_acquired", "logical"),
                    FortranDeclaration(f"{name}_scoped_proc", "procedure(prik_derived_scoped)", ("pointer",)),
                    FortranDeclaration(
                        f"{name}_checkout_proc",
                        "procedure(prik_derived_checkout)",
                        ("pointer",),
                    ),
                    FortranDeclaration(
                        f"{name}_restore_proc",
                        "procedure(prik_derived_restore)",
                        ("pointer",),
                    ),
                )
            )
            if argument.polymorphic is not None:
                declarations.extend(
                    FortranDeclaration(
                        self._polymorphic_variant_name(argument, variant.abi_code),
                        f"type({self._derived_native_alias(variant.backend_symbol)})",
                        ("pointer",),
                    )
                    for variant in argument.polymorphic.variants
                )
        return tuple(declarations)

    def _derived_call_execution(
        self,
        plan: FunctionPlan,
        call_body: tuple,
        scoped_origin_type_identities: frozenset[tuple[str, str]],
    ) -> tuple[tuple, tuple[FortranFunction, ...]]:
        """Prepare all carriers, invoke once, then restore in reverse order."""
        arguments = self._derived_arguments(plan)
        if not arguments:
            return call_body, ()
        body = list(self._derived_call_preparation_nodes(arguments, scoped_origin_type_identities))
        scoped = self._scoped_derived_arguments(arguments, scoped_origin_type_identities)
        invocation, internal = self._derived_call_invocation(arguments, scoped, call_body)
        body.append(invocation)
        body.extend(self._derived_transaction_restoration(argument) for argument in reversed(arguments))
        body.extend(node for argument in arguments for node in self._derived_argument_output_and_cleanup(argument))
        return tuple(body), internal

    def _derived_call_preparation_nodes(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
        scoped_origin_type_identities: frozenset[tuple[str, str]],
    ) -> tuple:
        """Build carrier initialization, preparation, and transaction-acquisition nodes for derived arguments. Acquisition remains in argument order."""
        return (
            *(node for argument in arguments for node in self._derived_argument_initializers(argument)),
            FortranAssignment("prik_derived_ready", CodeExpression(".true.")),
            *(self._derived_argument_preparation(argument, scoped_origin_type_identities) for argument in arguments),
            *(self._derived_transaction_acquisition(arguments, index) for index in range(len(arguments))),
        )

    def _scoped_derived_arguments(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
        scoped_origin_type_identities: frozenset[tuple[str, str]],
    ) -> tuple[ArgumentTransferPlan, ...]:
        """Select derived arguments whose scoped-origin producer exists in this module."""
        return tuple(
            argument
            for argument in arguments
            if self._derived_argument_uses_access(argument, DerivedActualAccess.SCOPED_ADDRESS)
            and self._has_scoped_origin_for_argument(argument, scoped_origin_type_identities)
        )

    @staticmethod
    def _derived_argument_uses_access(argument: ArgumentTransferPlan, access: DerivedActualAccess) -> bool:
        """Return whether any compatible derived-call case uses the requested actual-access mechanism."""
        return any(
            case.access is access
            for case in argument.derived_call.cases
            if case.action is not DerivedCallAction.INCOMPATIBLE
        )

    def _derived_call_invocation(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
        scoped: tuple[ArgumentTransferPlan, ...],
        call_body: tuple,
    ) -> tuple[FortranIf, tuple[FortranFunction, ...]]:
        """Build the guarded native invocation, using nested internal procedures only when scoped origins are required."""
        ready = self._derived_ready_condition(arguments)
        if scoped:
            return (
                FortranIf(
                    CodeExpression(ready),
                    body=(FortranCall(self._derived_step_name(0), ()),),
                ),
                self._derived_scoped_internal_procedures(scoped, call_body),
            )
        return FortranIf(CodeExpression(ready), body=call_body), ()

    def _derived_argument_initializers(self, argument: ArgumentTransferPlan) -> tuple:
        """Initialize bridge-local state for one derived carrier before its completed action is dispatched."""
        name = argument.entrypoint.parameter_name
        nodes = [
            FortranAssignment(f"bound_{name}_status", CodeExpression("0_c_int")),
            FortranAssignment(f"{name}_created", CodeExpression(".false.")),
            FortranAssignment(f"{name}_acquired", CodeExpression(".false.")),
            FortranAssignment(f"{name}_transaction_address", CodeExpression("c_null_ptr")),
            FortranNullify(name),
            FortranNullify(f"{name}_call_pointer"),
        ]
        if argument.entrypoint.descriptor_output_role is not None:
            nodes.extend(
                (
                    FortranAssignment(f"bound_{name}_output", CodeExpression("c_null_ptr")),
                    FortranAssignment(f"bound_{name}_output_present", CodeExpression("0_c_int")),
                )
            )
        return tuple(nodes)

    def _derived_argument_preparation(
        self,
        argument: ArgumentTransferPlan,
        scoped_origin_type_identities: frozenset[tuple[str, str]],
    ) -> FortranSelectCase:
        """Dispatch one carrier only by its completed ABI code."""
        compatible = {
            case.abi_code for case in argument.derived_call.cases if case.action is not DerivedCallAction.INCOMPATIBLE
        }
        cases = [FortranCase(0, ())]
        builders = {
            1: self._derived_direct_preparation,
            2: self._derived_scoped_preparation,
            3: self._derived_allocatable_holder_preparation,
            4: self._derived_pointer_holder_preparation,
            5: self._derived_allocatable_transaction_preparation,
            6: self._derived_pointer_transaction_preparation,
        }
        cases.extend(
            FortranCase(code, builders[code](argument))
            for code in sorted(compatible)
            if code in builders
            and (code != 2 or self._has_scoped_origin_for_argument(argument, scoped_origin_type_identities))
        )
        cases.append(
            FortranCase(
                None,
                (FortranAssignment(self._derived_status_parameter(argument), CodeExpression("6_c_int")),),
            )
        )
        return FortranSelectCase(
            CodeExpression(f"bound_{argument.entrypoint.parameter_name}_access"),
            tuple(cases),
        )

    def _derived_direct_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build preparation for the completed direct scalar-derived handoff case."""
        if argument.polymorphic is not None:
            return self._polymorphic_direct_preparation(argument)
        name = argument.entrypoint.parameter_name
        return (
            FortranIf(
                CodeExpression(f"c_associated(bound_{name})"),
                body=(FortranCall("c_f_pointer", (CodeExpression(f"bound_{name}"), CodeExpression(name))),),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
            ),
        )

    def _polymorphic_direct_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Associate one carrier with the concrete type selected by the binding."""
        name = argument.entrypoint.parameter_name
        cases = tuple(
            FortranCase(
                variant.abi_code,
                (
                    FortranIf(
                        CodeExpression(f"c_associated(bound_{name})"),
                        body=(
                            FortranCall(
                                "c_f_pointer",
                                (
                                    CodeExpression(f"bound_{name}"),
                                    CodeExpression(self._polymorphic_variant_name(argument, variant.abi_code)),
                                ),
                            ),
                        ),
                        else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
                    ),
                ),
            )
            for variant in argument.polymorphic.variants
        )
        fallback = FortranCase(
            None,
            (FortranAssignment(f"bound_{name}_status", CodeExpression("6_c_int")),),
        )
        return (
            FortranSelectCase(
                CodeExpression(f"bound_{name}_polymorphic"),
                (*cases, fallback),
            ),
        )

    def _derived_scoped_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build preparation for the completed scoped-address scalar-derived handoff case."""
        name = argument.entrypoint.parameter_name
        return (
            FortranIf(
                CodeExpression(f"c_associated(bound_{name}_scoped)"),
                body=(
                    FortranCall(
                        "c_f_procpointer",
                        (CodeExpression(f"bound_{name}_scoped"), CodeExpression(f"{name}_scoped_proc")),
                    ),
                ),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("6_c_int")),),
            ),
        )

    def _derived_allocatable_holder_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build preparation for a completed allocatable-holder scalar-derived handoff."""
        name = argument.entrypoint.parameter_name
        holder = f"{name}_allocatable_holder"
        return (
            FortranAssignment(f"{name}_holder_status", CodeExpression("0_c_int")),
            FortranIf(
                CodeExpression(f"c_associated(bound_{name})"),
                body=(FortranCall("c_f_pointer", (CodeExpression(f"bound_{name}"), CodeExpression(holder))),),
                else_body=(
                    FortranAllocate(holder, status=f"{name}_holder_status"),
                    FortranAssignment(f"{name}_created", CodeExpression(".true.")),
                ),
            ),
            FortranIf(
                CodeExpression(f"{name}_holder_status /= 0_c_int"),
                body=(FortranAssignment(f"bound_{name}_status", CodeExpression("4_c_int")),),
                else_body=self._derived_allocatable_payload_preparation(argument),
            ),
        )

    def _derived_allocatable_payload_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build preparation for an allocatable-holder payload after its carrier has been acquired."""
        if argument.derived_call.dummy_category in {
            DerivedDummyCategory.ALLOCATABLE,
            DerivedDummyCategory.ALLOCATABLE_TARGET,
        }:
            return ()
        name = argument.entrypoint.parameter_name
        return (
            FortranIf(
                CodeExpression(f"allocated({name}_allocatable_holder%value)"),
                body=(FortranPointerAssignment(name, CodeExpression(f"{name}_allocatable_holder%value")),),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
            ),
        )

    def _derived_pointer_holder_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build preparation for a completed pointer-holder scalar-derived handoff."""
        name = argument.entrypoint.parameter_name
        holder = f"{name}_pointer_holder"
        return (
            FortranAssignment(f"{name}_holder_status", CodeExpression("0_c_int")),
            FortranIf(
                CodeExpression(f"c_associated(bound_{name})"),
                body=(FortranCall("c_f_pointer", (CodeExpression(f"bound_{name}"), CodeExpression(holder))),),
                else_body=(
                    FortranAllocate(holder, status=f"{name}_holder_status"),
                    FortranNullify(f"{holder}%value"),
                    FortranAssignment(f"{name}_created", CodeExpression(".true.")),
                ),
            ),
            FortranIf(
                CodeExpression(f"{name}_holder_status /= 0_c_int"),
                body=(FortranAssignment(f"bound_{name}_status", CodeExpression("4_c_int")),),
                else_body=self._derived_pointer_payload_preparation(argument),
            ),
        )

    def _derived_pointer_payload_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build preparation for a pointer-holder payload after its carrier has been acquired."""
        if argument.derived_call.dummy_category is DerivedDummyCategory.POINTER:
            return ()
        name = argument.entrypoint.parameter_name
        return (
            FortranIf(
                CodeExpression(f"associated({name}_pointer_holder%value)"),
                body=(FortranPointerAssignment(name, CodeExpression(f"{name}_pointer_holder%value")),),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
            ),
        )

    def _derived_allocatable_transaction_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build the transaction setup selected for an allocatable derived carrier."""
        return self._derived_transaction_operation_preparation(argument)

    def _derived_pointer_transaction_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Build the transaction setup selected for a pointer derived carrier."""
        return self._derived_transaction_operation_preparation(argument)

    def _derived_transaction_operation_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Dispatch one derived transaction operation only by its completed action."""
        name = argument.entrypoint.parameter_name
        return (
            FortranIf(
                CodeExpression(f"c_associated(bound_{name}_checkout) .and. c_associated(bound_{name}_restore)"),
                body=(
                    FortranCall(
                        "c_f_procpointer",
                        (CodeExpression(f"bound_{name}_checkout"), CodeExpression(f"{name}_checkout_proc")),
                    ),
                    FortranCall(
                        "c_f_procpointer",
                        (CodeExpression(f"bound_{name}_restore"), CodeExpression(f"{name}_restore_proc")),
                    ),
                ),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("6_c_int")),),
            ),
        )

    def _derived_transaction_acquisition(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
        index: int,
    ) -> FortranIf:
        """Build acquisition nodes for one derived argument at the current native-call position."""
        argument = arguments[index]
        name = argument.entrypoint.parameter_name
        acquisition = FortranSelectCase(
            CodeExpression(f"bound_{name}_access"),
            (
                FortranCase(5, self._one_derived_transaction_acquisition(argument, allocatable=True)),
                FortranCase(6, self._one_derived_transaction_acquisition(argument, allocatable=False)),
                FortranCase(None, ()),
            ),
        )
        return FortranIf(
            CodeExpression("prik_derived_ready"),
            body=(
                FortranIf(
                    CodeExpression(f"bound_{name}_status == 0_c_int"),
                    body=(
                        acquisition,
                        FortranIf(
                            CodeExpression(f"bound_{name}_status /= 0_c_int"),
                            body=(FortranAssignment("prik_derived_ready", CodeExpression(".false.")),),
                        ),
                    ),
                    else_body=(FortranAssignment("prik_derived_ready", CodeExpression(".false.")),),
                ),
            ),
        )

    def _one_derived_transaction_acquisition(
        self,
        argument: ArgumentTransferPlan,
        *,
        allocatable: bool,
    ) -> tuple:
        """Build the guarded acquisition for one derived argument and preserve earlier failure state."""
        name = argument.entrypoint.parameter_name
        holder = f"{name}_{'allocatable' if allocatable else 'pointer'}_holder"
        return (
            FortranAssignment(
                f"bound_{name}_status",
                CodeExpression(f"{name}_checkout_proc({name}_transaction_address)"),
            ),
            FortranIf(
                CodeExpression(f"bound_{name}_status == 0_c_int"),
                body=(
                    FortranCall(
                        "c_f_pointer",
                        (CodeExpression(f"{name}_transaction_address"), CodeExpression(holder)),
                    ),
                    FortranAssignment(f"{name}_acquired", CodeExpression(".true.")),
                ),
            ),
        )

    def _derived_transaction_restoration(self, argument: ArgumentTransferPlan) -> FortranIf:
        """Build the restoration selected for one derived carrier after the native call."""
        name = argument.entrypoint.parameter_name
        return FortranIf(
            CodeExpression(f"{name}_acquired"),
            body=(
                FortranAssignment(
                    f"{name}_restore_status",
                    CodeExpression(f"{name}_restore_proc({name}_transaction_address)"),
                ),
                FortranIf(
                    CodeExpression(f"{name}_restore_status /= 0_c_int"),
                    body=(FortranAssignment(f"bound_{name}_status", CodeExpression(f"{name}_restore_status")),),
                ),
                FortranAssignment(f"{name}_acquired", CodeExpression(".false.")),
            ),
        )

    def _derived_scoped_internal_procedures(
        self,
        scoped: tuple[ArgumentTransferPlan, ...],
        call_body: tuple,
    ) -> tuple[FortranFunction, ...]:
        """Build nested procedures that serialize scoped-origin consumers around the native invocation."""
        procedures = []
        for index, argument in enumerate(scoped):
            name = argument.entrypoint.parameter_name
            next_step = self._derived_step_name(index + 1)
            scoped_body = self._derived_scoped_step_body(argument, scoped[:index], index, next_step)
            procedures.append(
                FortranFunction(
                    name=self._derived_step_name(index),
                    body=(
                        FortranIf(
                            CodeExpression(f"bound_{name}_access == 2_c_int"),
                            body=scoped_body,
                            else_body=(FortranCall(next_step, ()),),
                        ),
                    ),
                    is_subroutine=True,
                )
            )
            procedures.append(
                FortranFunction(
                    name=self._derived_consumer_name(index),
                    parameters=(
                        FortranParameter("address", "type(c_ptr)", ("value",)),
                        FortranParameter("context", "type(c_ptr)", ("value",)),
                    ),
                    result_name="status",
                    result_type="integer(c_int)",
                    bind_c=True,
                    body=(
                        FortranIf(
                            CodeExpression("c_associated(address)"),
                            body=(
                                FortranCall("c_f_pointer", (CodeExpression("address"), CodeExpression(name))),
                                FortranCall(next_step, ()),
                                FortranAssignment("status", CodeExpression("0_c_int")),
                            ),
                            else_body=(FortranAssignment("status", CodeExpression("1_c_int")),),
                        ),
                    ),
                )
            )
        procedures.append(
            FortranFunction(
                name=self._derived_step_name(len(scoped)),
                body=call_body,
                is_subroutine=True,
            )
        )
        return tuple(procedures)

    def _derived_scoped_step_body(
        self,
        argument: ArgumentTransferPlan,
        previous: tuple[ArgumentTransferPlan, ...],
        index: int,
        next_step: str,
    ) -> tuple:
        """Reuse a prior read-only scoped origin or acquire it exactly once."""
        name = argument.entrypoint.parameter_name
        body: tuple = (
            FortranAssignment(
                f"bound_{name}_status",
                CodeExpression(f"{name}_scoped_proc(c_funloc({self._derived_consumer_name(index)}), c_null_ptr)"),
            ),
        )
        same_type = tuple(
            candidate
            for candidate in previous
            if candidate.derived is not None
            and argument.derived is not None
            and candidate.derived.type_identity == argument.derived.type_identity
        )
        for candidate in reversed(same_type):
            prior = candidate.entrypoint.parameter_name
            body = (
                FortranIf(
                    CodeExpression(
                        f"bound_{prior}_access == 2_c_int .and. "
                        f"c_associated(bound_{name}_identity, bound_{prior}_identity)"
                    ),
                    body=(
                        FortranPointerAssignment(name, CodeExpression(prior)),
                        FortranCall(next_step, ()),
                    ),
                    else_body=body,
                ),
            )
        return body

    def _derived_pointer_call_initializers(self, plan: FunctionPlan) -> tuple:
        """Initialize temporary pointer-call associations before invoking the native procedure."""
        return tuple(
            node
            for argument in self._derived_arguments(plan)
            if argument.derived_call.dummy_category is DerivedDummyCategory.POINTER
            for node in self._one_derived_pointer_call_initializer(argument)
        )

    def _one_derived_pointer_call_initializer(self, argument: ArgumentTransferPlan) -> tuple:
        """Build initialization for one derived pointer actual selected by its completed call action."""
        name = argument.entrypoint.parameter_name
        holder = f"{name}_pointer_holder%value"
        associate_holder = FortranIf(
            CodeExpression(f"associated({holder})"),
            body=(FortranPointerAssignment(f"{name}_call_pointer", CodeExpression(holder)),),
            else_body=(FortranNullify(f"{name}_call_pointer"),),
        )
        associate_payload = FortranIf(
            CodeExpression(f"associated({name})"),
            body=(FortranPointerAssignment(f"{name}_call_pointer", CodeExpression(name)),),
            else_body=(FortranNullify(f"{name}_call_pointer"),),
        )
        return (
            FortranIf(
                CodeExpression(f"bound_{name}_access == 4_c_int .or. bound_{name}_access == 6_c_int"),
                body=(associate_holder,),
                else_body=(associate_payload,),
            ),
        )

    def _derived_pointer_call_finalizers(self, plan: FunctionPlan) -> tuple:
        """Build final pointer-call cleanup in native argument order after invocation."""
        return tuple(
            node
            for argument in self._derived_arguments(plan)
            if argument.derived_call.dummy_category is DerivedDummyCategory.POINTER
            for node in self._one_derived_pointer_call_finalizer(argument)
        )

    def _one_derived_pointer_call_finalizer(self, argument: ArgumentTransferPlan) -> tuple:
        """Build finalization for one derived pointer actual selected by its completed call action."""
        name = argument.entrypoint.parameter_name
        return (
            FortranIf(
                CodeExpression(f"bound_{name}_access == 4_c_int .or. bound_{name}_access == 6_c_int"),
                body=(
                    FortranIf(
                        CodeExpression(f"associated({name}_call_pointer)"),
                        body=(
                            FortranPointerAssignment(
                                f"{name}_pointer_holder%value",
                                CodeExpression(f"{name}_call_pointer"),
                            ),
                        ),
                        else_body=(FortranNullify(f"{name}_pointer_holder%value"),),
                    ),
                ),
            ),
        )

    def _derived_argument_output_and_cleanup(self, argument: ArgumentTransferPlan) -> tuple:
        """Build output projection and cleanup for one derived argument after restoration."""
        name = argument.entrypoint.parameter_name
        nodes = []
        if argument.entrypoint.descriptor_output_role is not None:
            nodes.append(self._derived_argument_output_finalizer(argument))
        else:
            nodes.extend(
                (
                    FortranIf(
                        CodeExpression(f"{name}_created .and. bound_{name}_access == 3_c_int"),
                        body=(FortranDeallocate(f"{name}_allocatable_holder"),),
                    ),
                    FortranIf(
                        CodeExpression(f"{name}_created .and. bound_{name}_access == 4_c_int"),
                        body=(FortranDeallocate(f"{name}_pointer_holder"),),
                    ),
                )
            )
        return tuple(nodes)

    def _derived_argument_output_finalizer(self, argument: ArgumentTransferPlan) -> FortranIf:
        """Build the completed output action for one derived carrier."""
        name = argument.entrypoint.parameter_name
        return FortranIf(
            CodeExpression(f"bound_{name}_access == 3_c_int"),
            body=self._derived_holder_output_nodes(name, allocatable=True),
            else_body=(
                FortranIf(
                    CodeExpression(f"bound_{name}_access == 4_c_int"),
                    body=self._derived_holder_output_nodes(name, allocatable=False),
                    else_body=(
                        FortranIf(
                            CodeExpression(f"bound_{name}_access == 5_c_int .or. bound_{name}_access == 6_c_int"),
                            body=(FortranAssignment(f"bound_{name}_output_present", CodeExpression("1_c_int")),),
                        ),
                    ),
                ),
            ),
        )

    @staticmethod
    def _derived_holder_output_nodes(name: str, *, allocatable: bool) -> tuple:
        """Build C-address output nodes for a derived holder that survived the native call."""
        holder = f"{name}_{'allocatable' if allocatable else 'pointer'}_holder"
        inquiry = "allocated" if allocatable else "associated"
        return (
            FortranAssignment(f"bound_{name}_output", CodeExpression(f"c_loc({holder})")),
            FortranIf(
                CodeExpression(f"{inquiry}({holder}%value)"),
                body=(FortranAssignment(f"bound_{name}_output_present", CodeExpression("1_c_int")),),
                else_body=(FortranAssignment(f"bound_{name}_output_present", CodeExpression("0_c_int")),),
            ),
        )

    @staticmethod
    def _derived_ready_condition(arguments: tuple[ArgumentTransferPlan, ...]) -> str:
        """Return the combined success condition that guards the derived native invocation."""
        return "prik_derived_ready" if arguments else ".true."

    @staticmethod
    def _derived_status_parameter(argument: ArgumentTransferPlan) -> str:
        """Return the bridge status parameter shared by derived transaction helpers."""
        return f"bound_{argument.entrypoint.parameter_name}_status"

    @staticmethod
    def _derived_step_name(index: int) -> str:
        """Return a deterministic nested procedure name for one scoped-origin invocation step."""
        return f"prik_derived_step_{index}"

    @staticmethod
    def _derived_consumer_name(index: int) -> str:
        """Return the deterministic consumer-procedure name for one scoped derived argument."""
        return f"prik_derived_consumer_{index}"

    def _lower_result(
        self,
        plan: FunctionPlan,
    ) -> tuple[str | None, str | None]:
        """Dispatch one completed bridge result action explicitly."""
        result = self._direct_result(plan)
        if result is None:
            return self._lower_result_none(plan)
        if result.scalar_descriptor is not None:
            return self._lower_result_scalar_descriptor(plan, result)
        if self._is_owned_native_array_result(result):
            return self._lower_result_none(plan)
        action = result.bridge.codegen_action
        match result.object_kind:
            case ObjectKind.NUMPY_ARRAY if action is CodegenAction.COPY_OUT:
                return self._lower_result_array_copy(plan, result)
            case ObjectKind.STRING if action is CodegenAction.COPY_OUT:
                return self._lower_result_fixed_string(plan, result)
            case ObjectKind.SCALAR if action is CodegenAction.DIRECT_VALUE:
                return self._lower_result_direct_value(plan, result)
            case ObjectKind.DERIVED_TYPE if action is CodegenAction.WRAPPER_INSTANCE:
                return self._lower_result_derived(plan, result)
            case _:
                raise ValueError(
                    f"Unsupported Fortran result selection for {plan.owner_path!r}: {result.object_kind!r}:{action!r}"
                )

    # Nullable rank-zero descriptor result lowering.
    def _lower_result_scalar_descriptor(
        self,
        _plan: FunctionPlan,
        _result: ResultPlan,
    ) -> tuple[str | None, str | None]:
        """Return the detached-copy C-pointer bridge shape."""
        return "result", "type(c_ptr)"

    # String result lowering.
    def _lower_result_fixed_string(
        self,
        _plan: FunctionPlan,
        _result: ResultPlan,
    ) -> tuple[str | None, str | None]:
        """Return the C-pointer bridge shape for one copied fixed string."""
        return "result", "type(c_ptr)"

    # Ordinary-array result lowering.
    def _lower_result_array_copy(
        self,
        _plan: FunctionPlan,
        _result: ResultPlan,
    ) -> tuple[str | None, str | None]:
        """Return the C-pointer bridge shape for one copied ordinary array."""
        return "result", "type(c_ptr)"

    # Derived-type result lowering.
    def _lower_result_derived(
        self,
        _plan: FunctionPlan,
        _result: ResultPlan,
    ) -> tuple[str | None, str | None]:
        """Return the opaque C-pointer bridge shape for persistent object storage."""
        return "result", "type(c_ptr)"

    def _lower_result_none(
        self,
        _plan: FunctionPlan,
    ) -> tuple[str | None, str | None]:
        """Return the procedure shape of a native subroutine with no projection."""
        return None, None

    # Scalar result lowering.
    def _lower_result_direct_value(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[str | None, str | None]:
        """Return the procedure shape of a direct native function result."""
        return "result", self._entrypoint_result_type(plan, result)

    def _owned_direct_result_parameters(
        self,
        result: NativeEntrypointResultPlan | None,
    ) -> tuple[FortranParameter, ...]:
        """Expose persistent binding-owned descriptor storage as one output dummy."""
        if result is None:
            return ()
        handle = result.native_array_handle
        if handle is None:
            return ()
        if handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor rank")
        if self._is_owned_deferred_character_result(result):
            return (
                FortranParameter("result", "type(c_ptr)"),
                FortranParameter("result_itemsize", "integer(c_int64_t)"),
                *(FortranParameter(f"result_extent_{axis}", "integer(c_int64_t)") for axis in range(handle.array.rank)),
            )
        dimension = self._array_dimension_attribute(handle.array.rank)
        return (
            FortranParameter(
                "result",
                self._array_result_element_type(result),
                (self._owned_native_array_descriptor_attribute(handle), dimension, "intent(out)"),
            ),
        )

    def _scalar_descriptor_direct_result_parameters_for_result(
        self,
        result: NativeEntrypointResultPlan,
    ) -> tuple[FortranParameter, ...]:
        """Expose runtime metadata associated with a direct descriptor result."""
        if result.scalar_descriptor is None:
            return ()
        parameters = [FortranParameter("result_present", "integer(c_int)")]
        if result.scalar_descriptor.runtime_length:
            parameters.append(FortranParameter("result_length", "integer(c_int64_t)"))
        return tuple(parameters)

    # Owned native-array result operations.
    def _owned_native_array_result_operations(self, function: FunctionPlan) -> tuple[FortranFunction, ...]:
        """Lower typed operations over binding-owned result descriptors."""
        procedures = []
        for result in function.results:
            if not self._supports_owned_native_array_result_operations(result):
                continue
            for entrypoint in self._generated_support_procedure_entrypoints_for(
                result.owner_path, "native_array:owned:"
            ):
                operation = NativeArrayOperation(entrypoint.role.rsplit(":", 1)[-1])
                procedure = self._owned_native_array_result_operation(result, operation)
                if procedure is not None:
                    procedures.append(procedure)
        return tuple(procedures)

    def _default_native_array_argument_operations(
        self,
        function: FunctionPlan,
    ) -> tuple[FortranFunction, ...]:
        """Lower typed operations used after lazy caller-handle attachment."""
        procedures = []
        for argument in function.arguments:
            handle = argument.native_array_handle
            if (
                handle is None
                or handle.default_handle.construction is not NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR
            ):
                continue
            for entrypoint in self._generated_support_procedure_entrypoints_for(
                argument.owner_path, "native_array:owned:"
            ):
                operation = NativeArrayOperation(entrypoint.role.rsplit(":", 1)[-1])
                procedure = self._owned_native_array_result_operation(argument, operation)
                if procedure is not None:
                    procedures.append(procedure)
        return tuple(procedures)

    def _supports_owned_native_array_result_operations(self, result: ResultPlan) -> bool:
        """Return whether typed helper operations use a Fortran descriptor dummy."""
        return self._is_owned_native_array_result(result) and not self._is_owned_deferred_character_result(result)

    def _owned_native_array_result_operation(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction | None:
        """Dispatch one generated operation selected by completed handle policy."""
        if operation in {NativeArrayOperation.ALLOCATED, NativeArrayOperation.ASSOCIATED}:
            return self._owned_native_array_result_state_operation(result, operation)
        if operation is NativeArrayOperation.CONTIGUOUS:
            return self._owned_native_array_result_contiguous_operation(result)
        if operation is NativeArrayOperation.SHAPE:
            return self._owned_native_array_result_shape_operation(result)
        if operation is NativeArrayOperation.ASSOCIATE:
            return self._owned_native_array_result_associate_operation(result)
        if operation in {NativeArrayOperation.DEALLOCATE, NativeArrayOperation.NULLIFY, NativeArrayOperation.DESTROY}:
            return self._owned_native_array_result_release_operation(result, operation)
        return None

    def _owned_native_array_result_state_operation(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction:
        """Return descriptor presence using its completed compiler inquiry."""
        inquiry = self._owned_native_array_result_presence_inquiry(result)
        name = self._owned_native_array_result_operation_name(result, operation)
        return FortranFunction(
            name=name,
            parameters=(self._owned_native_array_result_parameter(result, intent="in"),),
            result_name="state",
            result_type="logical(c_bool)",
            bind_name=name,
            body=(FortranAssignment("state", CodeExpression(f"{inquiry}(result)")),),
        )

    def _owned_native_array_result_contiguous_operation(
        self,
        result: ArgumentTransferPlan | ResultPlan,
    ) -> FortranFunction:
        """Return target contiguity without querying an absent pointer target."""
        name = self._owned_native_array_result_operation_name(result, NativeArrayOperation.CONTIGUOUS)
        return FortranFunction(
            name=name,
            parameters=(self._owned_native_array_result_parameter(result, intent="in"),),
            result_name="state",
            result_type="logical(c_bool)",
            bind_name=name,
            body=(
                FortranAssignment("state", CodeExpression(".false._c_bool")),
                FortranIf(
                    CodeExpression("associated(result)"),
                    body=(FortranAssignment("state", CodeExpression("is_contiguous(result)")),),
                ),
            ),
        )

    def _owned_native_array_result_shape_operation(
        self,
        result: ArgumentTransferPlan | ResultPlan,
    ) -> FortranFunction:
        """Return shape through Fortran when the owned descriptor is allocated."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no shape rank")
        name = self._owned_native_array_result_operation_name(result, NativeArrayOperation.SHAPE)
        extents = tuple(FortranParameter(f"extent_{axis}", "integer(c_int64_t)") for axis in range(handle.array.rank))
        present = tuple(
            FortranAssignment(
                f"extent_{axis}",
                CodeExpression(f"size(result, {axis + 1}, kind=c_int64_t)"),
            )
            for axis in range(handle.array.rank)
        )
        absent = tuple(
            FortranAssignment(f"extent_{axis}", CodeExpression("0_c_int64_t")) for axis in range(handle.array.rank)
        )
        inquiry = self._owned_native_array_result_presence_inquiry(result)
        return FortranFunction(
            name=name,
            parameters=(self._owned_native_array_result_parameter(result, intent="in"), *extents),
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(f"{inquiry}(result)"),
                    body=present,
                    else_body=absent,
                ),
            ),
            is_subroutine=True,
        )

    def _owned_native_array_result_release_operation(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction:
        """Apply the planned payload or association release operation."""
        name = self._owned_native_array_result_operation_name(result, operation)
        handle = result.native_array_handle
        if handle is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor policy")
        pointer = handle.descriptor_kind is NativeArrayDescriptorKind.POINTER
        nullify_only = pointer and operation in {NativeArrayOperation.NULLIFY, NativeArrayOperation.DESTROY}
        inquiry = self._owned_native_array_result_presence_inquiry(result)
        release = FortranNullify("result") if nullify_only else FortranDeallocate("result")
        return FortranFunction(
            name=name,
            parameters=(self._owned_native_array_result_parameter(result, intent="inout"),),
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(f"{inquiry}(result)"),
                    body=(release,),
                ),
            ),
            is_subroutine=True,
        )

    def _owned_native_array_result_associate_operation(
        self,
        result: ArgumentTransferPlan | ResultPlan,
    ) -> FortranFunction:
        """Make one owned pointer descriptor match another pointer descriptor."""
        name = self._owned_native_array_result_operation_name(result, NativeArrayOperation.ASSOCIATE)
        return FortranFunction(
            name=name,
            parameters=(
                self._owned_native_array_result_parameter(result, intent="inout"),
                self._owned_native_array_result_parameter(result, intent="in", name="source"),
            ),
            bind_name=name,
            body=(FortranPointerAssignment("result", CodeExpression("source")),),
            is_subroutine=True,
        )

    def _owned_native_array_result_parameter(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        *,
        intent: str,
        name: str = "result",
    ) -> FortranParameter:
        """Return the typed descriptor dummy used by owned-result operations."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor rank")
        return FortranParameter(
            name,
            self._array_result_element_type(result),
            (
                self._owned_native_array_descriptor_attribute(handle),
                self._array_dimension_attribute(handle.array.rank),
                f"intent({intent})",
            ),
        )

    @staticmethod
    def _owned_native_array_descriptor_attribute(handle: NativeArrayHandlePlan) -> str:
        """Return the descriptor attribute selected by completed handle policy."""
        return handle.descriptor_kind.value

    @staticmethod
    def _owned_native_array_result_presence_inquiry(result: ArgumentTransferPlan | ResultPlan) -> str:
        """Return the compiler inquiry selected by completed descriptor kind."""
        handle = result.native_array_handle
        if handle is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor policy")
        return "associated" if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER else "allocated"

    def _owned_native_array_result_operation_name(
        self,
        result: ArgumentTransferPlan | ResultPlan,
        operation: NativeArrayOperation,
    ) -> str:
        """Return one planner-owned descriptor operation symbol."""
        return self._generated_support_procedure_entrypoint(
            result.owner_path, f"native_array:owned:{operation.value}"
        ).symbol_name

    def _visit_ModuleVariablePlan(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Lower bridge-owned getter and setter actions into procedures."""
        if plan.bridge.native_getter_action is ModuleGetterAction.NATIVE_ARRAY_HANDLE:
            return self._lower_module_native_array_operations(plan)
        return (
            *self._lower_module_getter(plan),
            *self._lower_module_setter(plan),
        )

    def _lower_module_getter(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Dispatch one completed bridge getter action explicitly."""
        action = plan.bridge.native_getter_action
        match action:
            case ModuleGetterAction.CONSTANT_VALUE:
                return self._lower_module_getter_constant_value(plan)
            case ModuleGetterAction.NATIVE_CONSTANT_VALUE:
                return self._lower_module_getter_direct_value(plan)
            case ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE:
                return self._lower_module_getter_constant_array_value(plan)
            case ModuleGetterAction.DIRECT_VALUE:
                return self._lower_module_getter_direct_value(plan)
            case ModuleGetterAction.CHARACTER_VALUE:
                return self._lower_module_getter_character_value(plan)
            case ModuleGetterAction.NULLABLE_SNAPSHOT:
                return self._lower_module_getter_nullable_snapshot(plan)
            case ModuleGetterAction.BORROWED_ARRAY_VIEW:
                return self._lower_module_getter_borrowed_array_view(plan)
            case ModuleGetterAction.DERIVED_OBJECT:
                return self._lower_module_getter_derived_object(plan)
        raise ValueError(f"Unsupported Fortran module getter action for {plan.owner_path!r}: {action!r}")

    def _lower_module_getter_constant_value(self, _plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Constants are materialized directly by the Python binding."""
        return ()

    def _lower_module_getter_derived_object(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[FortranFunction, ...]:
        """Expose a whole address only for the completed direct-address path."""
        if plan.derived is None:
            raise ValueError(f"Derived module object {plan.owner_path!r} has no access plan")
        if plan.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY:
            return self._lower_module_derived_presence(plan)
        if plan.derived.access is ModuleObjectAccessMechanism.VALUE_COPY:
            return self._lower_module_getter_derived_value_copy(plan)
        name = self._module_bridge_getter_name(plan)
        return (
            FortranFunction(
                name=name,
                result_name="result",
                result_type="type(c_ptr)",
                bind_name=name,
                body=(FortranAssignment("result", CodeExpression(f"c_loc({self._native_variable_name(plan)})")),),
            ),
        )

    def _lower_module_derived_presence(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Expose descriptor state for one nullable typed module proxy."""
        storage = plan.derived.handoff.storage
        inquiry = {
            DerivedObjectStorage.MODULE_ALLOCATABLE: "allocated",
            DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET: "allocated",
            DerivedObjectStorage.MODULE_POINTER: "associated",
        }.get(storage)
        if inquiry is None:
            return ()
        name = self._module_derived_presence_bridge_name(plan)
        return (
            FortranFunction(
                name=name,
                result_name="result",
                result_type="logical(c_bool)",
                bind_name=name,
                body=(
                    FortranAssignment(
                        "result",
                        CodeExpression(f"{inquiry}({self._native_variable_name(plan)})"),
                    ),
                ),
            ),
        )

    # Runtime-selected scalar-derived module origins.
    def _derived_origin_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return module variables that provide a completed scalar-derived origin, preserving module order."""
        return tuple(variable for variable in self._variables(plan) if variable.derived is not None)

    def _scoped_origin_type_identities(self, plan: ModulePlan) -> frozenset[tuple[str, str]]:
        """Return derived identities with at least one scoped module-origin producer."""
        return frozenset(
            variable.derived.handoff.type_identity
            for variable in self._derived_origin_variables(plan)
            if self._derived_origin_supports(variable, "scoped")
        )

    @staticmethod
    def _has_scoped_origin_for_argument(
        argument: ArgumentTransferPlan,
        scoped_origin_type_identities: frozenset[tuple[str, str]],
    ) -> bool:
        """Return whether this bridge module can produce a scoped origin for the argument type."""
        return argument.derived is not None and argument.derived.type_identity in scoped_origin_type_identities

    def _derived_origin_procedures(self, variable: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Emit only the typed leaves supported by one completed module storage."""
        builders = {
            "present": self._derived_origin_presence_procedure,
            "address": self._derived_origin_address_procedure,
            "scoped": self._derived_origin_scoped_procedure,
            "checkout": self._derived_origin_checkout_procedure,
            "restore": self._derived_origin_restore_procedure,
        }
        return tuple(
            builders[operation](variable)
            for operation in ("present", "address", "scoped", "checkout", "restore")
            if self._derived_origin_supports(variable, operation)
        )

    def _derived_origin_presence_procedure(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build the native-presence inquiry for one scalar-derived module origin."""
        storage = variable.derived.handoff.storage
        inquiry = "associated" if storage is DerivedObjectStorage.MODULE_POINTER else "allocated"
        name = self._derived_origin_bridge_name(variable, "present")
        return FortranFunction(
            name=name,
            result_name="result",
            result_type="logical(c_bool)",
            bind_name=name,
            body=(FortranAssignment("result", CodeExpression(f"{inquiry}({self._native_variable_name(variable)})")),),
        )

    def _derived_origin_address_procedure(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build the address-export bridge procedure for one scalar-derived module origin."""
        storage = variable.derived.handoff.storage
        native = self._native_variable_name(variable)
        name = self._derived_origin_bridge_name(variable, "address")
        body = [FortranAssignment("result", CodeExpression("c_null_ptr"))]
        if storage is DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET:
            body.append(
                FortranIf(
                    CodeExpression(f"allocated({native})"),
                    body=(FortranAssignment("result", CodeExpression(f"c_loc({native})")),),
                )
            )
        else:
            body.append(FortranAssignment("result", CodeExpression(f"c_loc({native})")))
        return FortranFunction(
            name=name,
            result_name="result",
            result_type="type(c_ptr)",
            bind_name=name,
            body=tuple(body),
        )

    def _derived_origin_scoped_procedure(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build the callback-based scoped-origin procedure for one scalar-derived module variable."""
        name = self._derived_origin_bridge_name(variable, "scoped")
        native = self._native_variable_name(variable)
        storage = variable.derived.handoff.storage
        presence = (
            f"allocated({native})"
            if storage is DerivedObjectStorage.MODULE_ALLOCATABLE
            else f"associated({native})"
            if storage is DerivedObjectStorage.MODULE_POINTER
            else None
        )
        invoke = CodeExpression(f"prik_invoke_origin({native})")
        body = [
            FortranCall(
                "c_f_procpointer",
                (CodeExpression("consumer"), CodeExpression("consume")),
            ),
            FortranAssignment("status", CodeExpression("1_c_int")),
        ]
        if presence is None:
            body.append(FortranAssignment("status", invoke))
        else:
            body.append(
                FortranIf(
                    CodeExpression(presence),
                    body=(FortranAssignment("status", invoke),),
                )
            )
        native_type = f"type({self._derived_native_alias(variable.derived.handoff.backend_symbol)})"
        internal = FortranFunction(
            name="prik_invoke_origin",
            parameters=(FortranParameter("value", native_type, ("target",)),),
            result_name="inner_status",
            result_type="integer(c_int)",
            body=(
                FortranAssignment(
                    "inner_status",
                    CodeExpression("consume(c_loc(value), context)"),
                ),
            ),
        )
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("consumer", "type(c_funptr)", ("value",)),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            result_name="status",
            result_type="integer(c_int)",
            bind_name=name,
            declarations=(FortranDeclaration("consume", "procedure(prik_derived_consumer)", ("pointer",)),),
            body=tuple(body),
            internal_procedures=(internal,),
        )

    def _derived_origin_checkout_procedure(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Dispatch checkout generation from the origin's completed native storage category."""
        storage = variable.derived.handoff.storage
        return (
            self._derived_origin_allocatable_checkout(variable)
            if storage in {DerivedObjectStorage.MODULE_ALLOCATABLE, DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET}
            else self._derived_origin_pointer_checkout(variable)
        )

    def _derived_origin_allocatable_checkout(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build checkout that moves a module allocatable into a bridge-owned holder."""
        name = self._derived_origin_bridge_name(variable, "checkout")
        holder_type = self._allocatable_holder_type_name(variable.derived.handoff.backend_symbol)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("holder_address", "type(c_ptr)", ("intent(out)",)),),
            result_name="status",
            result_type="integer(c_int)",
            bind_name=name,
            declarations=(
                FortranDeclaration("holder", f"type({holder_type})", ("pointer",)),
                FortranDeclaration("allocation_status", "integer(c_int)"),
            ),
            body=(
                FortranAssignment("holder_address", CodeExpression("c_null_ptr")),
                FortranAllocate("holder", status="allocation_status"),
                FortranIf(
                    CodeExpression("allocation_status == 0_c_int"),
                    body=(
                        FortranCall(
                            "move_alloc",
                            (
                                CodeExpression(self._native_variable_name(variable)),
                                CodeExpression("holder%value"),
                            ),
                        ),
                        FortranAssignment("holder_address", CodeExpression("c_loc(holder)")),
                        FortranAssignment("status", CodeExpression("0_c_int")),
                    ),
                    else_body=(FortranAssignment("status", CodeExpression("4_c_int")),),
                ),
            ),
        )

    def _derived_origin_pointer_checkout(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build checkout that transfers a module pointer association into a bridge-owned holder."""
        name = self._derived_origin_bridge_name(variable, "checkout")
        holder_type = self._pointer_holder_type_name(variable.derived.handoff.backend_symbol)
        native = self._native_variable_name(variable)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("holder_address", "type(c_ptr)", ("intent(out)",)),),
            result_name="status",
            result_type="integer(c_int)",
            bind_name=name,
            declarations=(
                FortranDeclaration("holder", f"type({holder_type})", ("pointer",)),
                FortranDeclaration("allocation_status", "integer(c_int)"),
            ),
            body=(
                FortranAssignment("holder_address", CodeExpression("c_null_ptr")),
                FortranAllocate("holder", status="allocation_status"),
                FortranIf(
                    CodeExpression("allocation_status == 0_c_int"),
                    body=(
                        FortranIf(
                            CodeExpression(f"associated({native})"),
                            body=(FortranPointerAssignment("holder%value", CodeExpression(native)),),
                            else_body=(FortranNullify("holder%value"),),
                        ),
                        FortranNullify(native),
                        FortranAssignment("holder_address", CodeExpression("c_loc(holder)")),
                        FortranAssignment("status", CodeExpression("0_c_int")),
                    ),
                    else_body=(FortranAssignment("status", CodeExpression("4_c_int")),),
                ),
            ),
        )

    def _derived_origin_restore_procedure(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Dispatch restore generation from the origin's completed native storage category."""
        storage = variable.derived.handoff.storage
        return (
            self._derived_origin_allocatable_restore(variable)
            if storage in {DerivedObjectStorage.MODULE_ALLOCATABLE, DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET}
            else self._derived_origin_pointer_restore(variable)
        )

    def _derived_origin_allocatable_restore(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build restore that moves an allocatable holder payload back to its module variable."""
        name = self._derived_origin_bridge_name(variable, "restore")
        holder_type = self._allocatable_holder_type_name(variable.derived.handoff.backend_symbol)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("holder_address", "type(c_ptr)", ("value",)),),
            result_name="status",
            result_type="integer(c_int)",
            bind_name=name,
            declarations=(FortranDeclaration("holder", f"type({holder_type})", ("pointer",)),),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("holder_address"), CodeExpression("holder"))),
                FortranIf(
                    CodeExpression("associated(holder)"),
                    body=(
                        FortranCall(
                            "move_alloc",
                            (
                                CodeExpression("holder%value"),
                                CodeExpression(self._native_variable_name(variable)),
                            ),
                        ),
                        FortranDeallocate("holder"),
                        FortranAssignment("status", CodeExpression("0_c_int")),
                    ),
                    else_body=(FortranAssignment("status", CodeExpression("5_c_int")),),
                ),
            ),
        )

    def _derived_origin_pointer_restore(self, variable: ModuleVariablePlan) -> FortranFunction:
        """Build restore that re-associates a pointer holder payload with its module variable."""
        name = self._derived_origin_bridge_name(variable, "restore")
        holder_type = self._pointer_holder_type_name(variable.derived.handoff.backend_symbol)
        native = self._native_variable_name(variable)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("holder_address", "type(c_ptr)", ("value",)),),
            result_name="status",
            result_type="integer(c_int)",
            bind_name=name,
            declarations=(FortranDeclaration("holder", f"type({holder_type})", ("pointer",)),),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("holder_address"), CodeExpression("holder"))),
                FortranIf(
                    CodeExpression("associated(holder)"),
                    body=(
                        FortranIf(
                            CodeExpression("associated(holder%value)"),
                            body=(FortranPointerAssignment(native, CodeExpression("holder%value")),),
                            else_body=(FortranNullify(native),),
                        ),
                        FortranNullify("holder%value"),
                        FortranDeallocate("holder"),
                        FortranAssignment("status", CodeExpression("0_c_int")),
                    ),
                    else_body=(FortranAssignment("status", CodeExpression("5_c_int")),),
                ),
            ),
        )

    def _derived_origin_supports(self, variable: ModuleVariablePlan, operation: str) -> bool:
        """Return whether planning registered one derived-origin operation."""
        return (variable.owner_path, f"derived_origin:{operation}") in self._generated_support_procedure_entrypoints

    def _derived_origin_bridge_name(self, variable: ModuleVariablePlan, operation: str) -> str:
        """Return one planner-owned derived-origin operation symbol."""
        return self._generated_support_procedure_entrypoint(
            variable.owner_path, f"derived_origin:{operation}"
        ).symbol_name

    def _lower_module_getter_derived_value_copy(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[FortranFunction, ...]:
        """Allocate one persistent typed copy of an explicit native constant."""
        derived = plan.derived
        if derived is None:
            raise ValueError(f"Derived module constant {plan.owner_path!r} has no handoff")
        name = self._module_bridge_getter_name(plan)
        local = "value"
        return (
            FortranFunction(
                name=name,
                result_name="result",
                result_type="type(c_ptr)",
                bind_name=name,
                declarations=(
                    FortranDeclaration(
                        local,
                        f"type({self._derived_native_alias(derived.handoff.backend_symbol)})",
                        ("pointer",),
                    ),
                    FortranDeclaration("prik_allocation_status", "integer(c_int)"),
                ),
                body=(
                    FortranAssignment("result", CodeExpression("c_null_ptr")),
                    FortranAllocate(local, status="prik_allocation_status"),
                    FortranIf(
                        CodeExpression("prik_allocation_status == 0"),
                        body=(
                            FortranAssignment(local, CodeExpression(self._native_variable_name(plan))),
                            FortranAssignment("result", CodeExpression(f"c_loc({local})")),
                        ),
                    ),
                ),
            ),
        )

    # Borrowed module native-array-handle operations.
    def _lower_module_native_array_operations(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[FortranFunction, ...]:
        """Lower every planned module-handle operation into a named bridge procedure."""
        if plan.native_array_handle is None:
            raise ValueError(f"Module handle {plan.owner_path!r} has no operation plan")
        return tuple(
            self._lower_module_native_array_bridge_operation(
                plan,
                NativeArrayOperation(operation.role.rsplit(":", 1)[-1]),
            )
            for operation in self._generated_support_procedure_entrypoints_for(plan.owner_path, "module:native_array:")
        )

    def _lower_module_native_array_bridge_operation(
        self,
        plan: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction:
        """Lower one operation selected to cross the native bridge."""
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            return self._module_native_array_state_operation(plan, operation)
        if operation is NativeArrayOperation.ELEMENT_LENGTH:
            return self._module_native_array_element_length_operation(plan)
        if operation is NativeArrayOperation.ARRAY_ACTUAL:
            return self._module_native_array_actual_operation(plan)
        if operation is NativeArrayOperation.SHAPE:
            return self._module_native_array_shape_operation(plan)
        if operation is NativeArrayOperation.DESCRIPTOR:
            return self._module_native_array_descriptor_operation(plan)
        if operation is NativeArrayOperation.ASSOCIATE:
            return self._module_native_array_associate_operation(plan)
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            return self._module_native_array_shape_mutation_operation(plan, operation)
        if operation is NativeArrayOperation.DEALLOCATE:
            return self._module_native_array_deallocate_operation(plan)
        if operation is NativeArrayOperation.NULLIFY:
            return self._module_native_array_nullify_operation(plan)
        raise ValueError(f"Unsupported module native array operation for {plan.owner_path!r}: {operation!r}")

    def _module_native_array_state_operation(self, plan: ModuleVariablePlan, operation) -> FortranFunction:
        """Return allocated, associated, or contiguous state."""
        native = self._native_variable_name(plan)
        if operation is NativeArrayOperation.ALLOCATED:
            expression = f"allocated({native})"
        elif operation is NativeArrayOperation.ASSOCIATED:
            expression = f"associated({native})"
        else:
            presence = self._module_native_array_presence_expression(plan)
            expression = f".not. ({presence}) .or. is_contiguous({native})"
        name = self._module_native_array_operation_name(plan, operation)
        return FortranFunction(
            name=name,
            result_name="result",
            result_type="logical(c_bool)",
            bind_name=name,
            body=(FortranAssignment("result", CodeExpression(expression)),),
        )

    def _module_native_array_actual_operation(self, plan: ModuleVariablePlan) -> FortranFunction:
        """Return current module-array data storage without changing ownership."""
        if self._uses_module_allocatable_descriptor(plan):
            return self._module_allocatable_descriptor_callback_operation(
                plan,
                NativeArrayOperation.ARRAY_ACTUAL,
            )
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.ARRAY_ACTUAL)
        native = self._native_variable_name(plan)
        return FortranFunction(
            name=name,
            result_name="result",
            result_type="type(c_ptr)",
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(self._module_native_array_presence_expression(plan)),
                    body=(FortranAssignment("result", CodeExpression(f"c_loc({native})")),),
                    else_body=(FortranAssignment("result", CodeExpression("c_null_ptr")),),
                ),
            ),
        )

    def _module_native_array_element_length_operation(self, plan: ModuleVariablePlan) -> FortranFunction:
        """Return the runtime character element width or zero when absent."""
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.ELEMENT_LENGTH)
        native = self._native_variable_name(plan)
        return FortranFunction(
            name=name,
            result_name="result",
            result_type="integer(c_int64_t)",
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(self._module_native_array_presence_expression(plan)),
                    body=(FortranAssignment("result", CodeExpression(f"len({native}, kind=c_int64_t)")),),
                    else_body=(FortranAssignment("result", CodeExpression("0_c_int64_t")),),
                ),
            ),
        )

    def _module_native_array_shape_operation(self, plan: ModuleVariablePlan) -> FortranFunction:
        """Return current extents, preserving absent descriptor state as zeroes."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {plan.owner_path!r} has no shape rank")
        parameters = tuple(
            FortranParameter(f"extent_{axis}", "integer(c_int64_t)") for axis in range(handle.array.rank)
        )
        native = self._native_variable_name(plan)
        present = tuple(
            FortranAssignment(f"extent_{axis}", CodeExpression(f"size({native}, {axis + 1}, kind=c_int64_t)"))
            for axis in range(handle.array.rank)
        )
        absent = tuple(
            FortranAssignment(f"extent_{axis}", CodeExpression("0_c_int64_t")) for axis in range(handle.array.rank)
        )
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.SHAPE)
        return FortranFunction(
            name=name,
            parameters=parameters,
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(self._module_native_array_presence_expression(plan)),
                    body=present,
                    else_body=absent,
                ),
            ),
            is_subroutine=True,
        )

    def _module_native_array_descriptor_operation(self, plan: ModuleVariablePlan) -> FortranFunction | None:
        """Expose current module descriptor state through the selected mechanism."""
        handle = plan.native_array_handle
        if self._uses_module_allocatable_descriptor(plan):
            return self._module_allocatable_descriptor_callback_operation(
                plan,
                NativeArrayOperation.DESCRIPTOR,
            )
        if handle is None or handle.descriptor_kind is not NativeArrayDescriptorKind.POINTER:
            return None
        if handle.array.rank is None:
            raise ValueError(f"Pointer module handle {plan.owner_path!r} has no descriptor rank")
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.DESCRIPTOR)
        native = self._native_variable_name(plan)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter(
                    "descriptor",
                    self._module_native_array_element_type(plan),
                    ("pointer", self._array_dimension_attribute(handle.array.rank), "intent(out)"),
                ),
            ),
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(f"associated({native})"),
                    body=(FortranPointerAssignment("descriptor", CodeExpression(native)),),
                    else_body=(FortranPointerAssignment("descriptor", CodeExpression("null()")),),
                ),
            ),
            is_subroutine=True,
        )

    @staticmethod
    def _uses_module_allocatable_descriptor(plan: ModuleVariablePlan) -> bool:
        """Return whether completed policy selected callback-based descriptor access."""
        handle = plan.native_array_handle
        return bool(
            handle is not None
            and handle.descriptor_interop is NativeArrayDescriptorInterop.MODULE_ALLOCATABLE_C_DESCRIPTOR
        )

    def _module_allocatable_descriptor_callback_operation(
        self,
        plan: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction:
        """Pass the current allocatable descriptor to a C callback without copying."""
        name = self._module_native_array_operation_name(plan, operation)
        interface_name = self._module_descriptor_callback_interface_name(plan)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("callback_address", "type(c_funptr)", ("value",)),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            bind_name=name,
            declarations=(FortranDeclaration("callback", f"procedure({interface_name})", ("pointer",)),),
            body=(
                FortranCall(
                    "c_f_procpointer",
                    (CodeExpression("callback_address"), CodeExpression("callback")),
                ),
                FortranCall(
                    "callback",
                    (CodeExpression(self._native_variable_name(plan)), CodeExpression("context")),
                ),
            ),
            is_subroutine=True,
        )

    def _module_native_array_shape_mutation_operation(self, plan: ModuleVariablePlan, operation) -> FortranFunction:
        """Allocate or resize one module descriptor through completed permissions."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {plan.owner_path!r} has no mutation rank")
        parameters = tuple(
            FortranParameter(f"extent_{axis}", "integer(c_int64_t)", ("value",)) for axis in range(handle.array.rank)
        )
        extents = tuple(CodeExpression(f"extent_{axis}") for axis in range(handle.array.rank))
        native = self._native_variable_name(plan)
        body = (
            FortranIf(
                CodeExpression(self._module_native_array_presence_expression(plan)),
                body=(FortranDeallocate(native),),
            ),
            FortranAllocate(native, extents),
        )
        name = self._module_native_array_operation_name(plan, operation)
        return FortranFunction(
            name=name,
            parameters=parameters,
            bind_name=name,
            body=body,
            is_subroutine=True,
        )

    def _module_native_array_associate_operation(self, plan: ModuleVariablePlan) -> FortranFunction:
        """Make one module pointer association match the source descriptor."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module pointer handle {plan.owner_path!r} has no association rank")
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.ASSOCIATE)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter(
                    "source",
                    self._module_native_array_element_type(plan),
                    ("pointer", self._array_dimension_attribute(handle.array.rank), "intent(in)"),
                ),
            ),
            bind_name=name,
            body=(
                FortranPointerAssignment(
                    self._native_variable_name(plan),
                    CodeExpression("source"),
                ),
            ),
            is_subroutine=True,
        )

    def _module_native_array_deallocate_operation(self, plan: ModuleVariablePlan) -> FortranFunction:
        """Deallocate one policy-authorized module descriptor payload."""
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.DEALLOCATE)
        native = self._native_variable_name(plan)
        return FortranFunction(
            name=name,
            bind_name=name,
            body=(
                FortranIf(
                    CodeExpression(self._module_native_array_presence_expression(plan)),
                    body=(FortranDeallocate(native),),
                ),
            ),
            is_subroutine=True,
        )

    def _module_native_array_nullify_operation(self, plan: ModuleVariablePlan) -> FortranFunction:
        """Nullify one policy-authorized module pointer association."""
        name = self._module_native_array_operation_name(plan, NativeArrayOperation.NULLIFY)
        return FortranFunction(
            name=name,
            bind_name=name,
            body=(FortranPointerAssignment(self._native_variable_name(plan), CodeExpression("null()")),),
            is_subroutine=True,
        )

    def _module_native_array_presence_expression(self, plan: ModuleVariablePlan) -> str:
        """Return the presence inquiry selected by a module native-array handle's descriptor kind."""
        handle = plan.native_array_handle
        if handle is None:
            raise ValueError(f"Module handle {plan.owner_path!r} has no descriptor kind")
        intrinsic = "allocated" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "associated"
        return f"{intrinsic}({self._native_variable_name(plan)})"

    def _module_native_array_element_type(self, plan: ModuleVariablePlan) -> str:
        """Return one numeric or deferred-character module-array element type."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "character(kind=c_char, len=:)"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).fortran_spelling

    def _module_native_array_operation_name(self, plan: ModuleVariablePlan, operation) -> str:
        """Return one planner-owned module native-array operation symbol."""
        return self._generated_support_procedure_entrypoint(
            plan.owner_path, f"module:native_array:{operation.value}"
        ).symbol_name

    def _lower_module_getter_direct_value(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Return one direct scalar module-variable getter."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        name = self._module_bridge_getter_name(plan)
        return (
            FortranFunction(
                name=name,
                result_name="result",
                result_type=scalar_type.fortran_spelling,
                bind_name=name,
                body=(FortranAssignment("result", CodeExpression(self._native_variable_name(plan))),),
            ),
        )

    def _module_character_length(self, plan: ModuleVariablePlan) -> int:
        """Return the declared width one character module accessor copies."""
        length = plan.character_length
        if length is None or length <= 0:
            raise ValueError(f"Character module variable {plan.owner_path!r} has no declared length")
        return length

    def _lower_module_getter_character_value(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Copy one fixed native character module variable into a C byte buffer.

        A character value has no by-value C ABI, so it travels the same
        fixed-width buffer a character field already uses.
        """
        length = self._module_character_length(plan)
        name = self._module_bridge_getter_name(plan)
        return (
            FortranFunction(
                name=name,
                parameters=(
                    FortranParameter("value", "character(kind=c_char)", (f"dimension({length})", "intent(out)")),
                ),
                bind_name=name,
                body=(
                    FortranAssignment("value", CodeExpression(f"transfer({self._native_variable_name(plan)}, value)")),
                ),
                is_subroutine=True,
            ),
        )

    def _lower_module_setter_character_value(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Copy one exact-width C byte buffer into a native character module variable."""
        length = self._module_character_length(plan)
        name = self._module_bridge_setter_name(plan)
        return (
            FortranFunction(
                name=name,
                parameters=(
                    FortranParameter("value", "character(kind=c_char)", (f"dimension({length})", "intent(in)")),
                ),
                bind_name=name,
                body=(
                    FortranAssignment(
                        self._native_variable_name(plan),
                        CodeExpression(f"transfer(value, {self._native_variable_name(plan)})"),
                    ),
                ),
                is_subroutine=True,
            ),
        )

    def _lower_module_getter_constant_array_value(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Copy one compiler-owned parameter array into persistent bridge storage.

        The binding copies this temporary native buffer into its one
        Python-owned read-only NumPy allocation during module initialization.
        A Fortran parameter itself has no addressable storage to expose.
        """
        array = plan.array
        if array is None or array.rank is None or array.rank <= 0:
            raise ValueError(f"Module parameter array {plan.owner_path!r} has no fixed array plan")
        element_type = self._module_array_element_type(plan, array)
        name = self._module_bridge_getter_name(plan)
        native = self._native_variable_name(plan)
        snapshot = "parameter_snapshot"
        extents = tuple(f"extent_{axis}" for axis in range(array.rank))
        return (
            FortranFunction(
                name=name,
                parameters=tuple(
                    FortranParameter(extent, "integer(c_int64_t)", ("intent(out)",)) for extent in extents
                ),
                result_name="result",
                result_type="type(c_ptr)",
                bind_name=name,
                uses=(FortranUse("iso_c_binding", ("c_int", "c_int64_t", "c_loc", "c_null_ptr", "c_ptr")),),
                declarations=(
                    FortranDeclaration(
                        snapshot,
                        element_type,
                        ("allocatable", "target", "save", self._array_dimension_attribute(array.rank)),
                    ),
                    FortranDeclaration("allocation_status", "integer(c_int)"),
                ),
                body=(
                    FortranAssignment("result", CodeExpression("c_null_ptr")),
                    FortranAssignment("allocation_status", CodeExpression("0_c_int")),
                    FortranIf(
                        CodeExpression(f".not. allocated({snapshot})"),
                        body=(
                            FortranAllocate(
                                snapshot,
                                tuple(CodeExpression(f"size({native}, {axis + 1})") for axis in range(array.rank)),
                                status="allocation_status",
                            ),
                        ),
                    ),
                    FortranIf(
                        CodeExpression("allocation_status == 0_c_int"),
                        body=(
                            FortranAssignment(snapshot, CodeExpression(native)),
                            *(
                                FortranAssignment(
                                    extent,
                                    CodeExpression(f"int(size({native}, {axis + 1}), c_int64_t)"),
                                )
                                for axis, extent in enumerate(extents)
                            ),
                            FortranAssignment("result", CodeExpression(f"c_loc({snapshot})")),
                        ),
                    ),
                ),
            ),
        )

    def _module_array_element_type(self, plan: ModuleVariablePlan, array: ArrayHandoffPlan) -> str:
        """Return the Fortran element spelling one module array snapshot declares.

        A character element carries its Fortran length, which the binding reads
        back as the fixed dtype width; every other element names a scalar type.
        """
        if plan.datatype_family is DatatypeFamily.STRING:
            if array.itemsize is None or array.itemsize <= 0:
                raise ValueError(f"Character module array {plan.owner_path!r} has no fixed itemsize")
            return f"character(kind=c_char, len={array.itemsize})"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).fortran_spelling

    def _lower_module_getter_borrowed_array_view(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[FortranFunction, ...]:
        """Expose one addressable fixed module array through pointer and extents."""
        array = plan.array
        if array is None or array.rank is None:
            raise ValueError(f"Module array view {plan.owner_path!r} has no fixed rank")
        name = self._module_bridge_getter_name(plan)
        native = self._native_variable_name(plan)
        return (
            FortranFunction(
                name=name,
                parameters=tuple(
                    FortranParameter(f"extent_{axis}", "integer(c_int64_t)", ("intent(out)",))
                    for axis in range(array.rank)
                ),
                result_name="result",
                result_type="type(c_ptr)",
                bind_name=name,
                body=(
                    *(
                        FortranAssignment(
                            f"extent_{axis}",
                            CodeExpression(f"int(size({native}, {axis + 1}), c_int64_t)"),
                        )
                        for axis in range(array.rank)
                    ),
                    FortranAssignment("result", CodeExpression(f"c_loc({native})")),
                ),
            ),
        )

    def _lower_module_getter_nullable_snapshot(
        self,
        plan: ModuleVariablePlan,
    ) -> tuple[FortranFunction, ...]:
        """Return a nullable detached snapshot through C-owned storage."""
        presence = "allocated" if plan.entrypoint.descriptor_kind == "allocatable" else "associated"
        condition = f"{presence}({self._native_variable_name(plan)})"
        if plan.datatype_family is DatatypeFamily.STRING:
            return self._lower_nullable_character_module_getter(plan, condition)
        return self._lower_nullable_module_getter(plan, condition)

    def _lower_nullable_character_module_getter(
        self,
        plan: ModuleVariablePlan,
        condition: str,
    ) -> tuple[FortranFunction, ...]:
        """Build one nullable detached character snapshot with its runtime width.

        A descriptor character has no width until it is allocated, so the
        length travels beside the copied bytes rather than being known here.
        """
        name = self._module_bridge_getter_name(plan)
        native = self._native_variable_name(plan)
        return (
            FortranFunction(
                name=name,
                parameters=(FortranParameter("length", "integer(c_int64_t)", ("intent(out)",)),),
                result_name="result",
                result_type="type(c_ptr)",
                bind_name=name,
                declarations=(FortranDeclaration("copy", "character(kind=c_char)", ("pointer", "dimension(:)")),),
                body=(
                    FortranAssignment("result", CodeExpression("c_null_ptr")),
                    FortranAssignment("length", CodeExpression("0_c_int64_t")),
                    FortranIf(
                        CodeExpression(condition),
                        body=(
                            FortranAssignment("length", CodeExpression(f"len({native}, kind=c_int64_t)")),
                            FortranAssignment(
                                "result",
                                CodeExpression("c_malloc(max(1_c_size_t, int(length, c_size_t)))"),
                            ),
                            FortranIf(
                                CodeExpression("c_associated(result)"),
                                body=(
                                    FortranCall(
                                        "c_f_pointer",
                                        (
                                            CodeExpression("result"),
                                            CodeExpression("copy"),
                                            CodeExpression("[length]"),
                                        ),
                                    ),
                                    FortranIf(
                                        CodeExpression("length > 0_c_int64_t"),
                                        body=(
                                            FortranAssignment(
                                                "copy(1:length)",
                                                CodeExpression(f"transfer({native}, copy(1:length))"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def _lower_nullable_module_getter(
        self,
        plan: ModuleVariablePlan,
        condition: str,
    ) -> tuple[FortranFunction, ...]:
        """Build the shared detached scalar snapshot bridge procedure."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        name = self._module_bridge_getter_name(plan)
        return (
            FortranFunction(
                name=name,
                result_name="result",
                result_type="type(c_ptr)",
                bind_name=name,
                declarations=(
                    FortranDeclaration("copy", scalar_type.fortran_spelling, ("pointer",)),
                    FortranDeclaration("element", scalar_type.fortran_spelling),
                ),
                body=(
                    FortranIf(
                        CodeExpression(condition),
                        body=(
                            FortranAssignment(
                                "result",
                                CodeExpression("c_malloc(storage_size(element, kind=c_size_t))"),
                            ),
                            FortranIf(
                                CodeExpression("c_associated(result)"),
                                body=(
                                    FortranCall(
                                        "c_f_pointer",
                                        (CodeExpression("result"), CodeExpression("copy")),
                                    ),
                                    FortranAssignment("copy", CodeExpression(self._native_variable_name(plan))),
                                ),
                            ),
                        ),
                        else_body=(FortranAssignment("result", CodeExpression("c_null_ptr")),),
                    ),
                ),
            ),
        )

    def _lower_module_setter(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Dispatch one completed native assignment action explicitly."""
        action = plan.bridge.native_assignment
        match action:
            case AssignmentMode.NONE:
                return self._lower_module_setter_none(plan)
            case AssignmentMode.VALUE_COPY:
                return self._lower_module_setter_value_copy(plan)
        raise ValueError(f"Unsupported Fortran module setter assignment for {plan.owner_path!r}: {action!r}")

    def _lower_module_setter_none(self, _plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Return no native setter when the bridge assignment is omitted."""
        return ()

    def _lower_module_setter_value_copy(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Return one value-copy native module assignment."""
        if plan.bridge.native_getter_action is ModuleGetterAction.CHARACTER_VALUE:
            return self._lower_module_setter_character_value(plan)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        name = self._module_bridge_setter_name(plan)
        return (
            FortranFunction(
                name=name,
                parameters=(FortranParameter("value", scalar_type.fortran_spelling, ("value",)),),
                bind_name=name,
                body=(FortranAssignment(self._native_variable_name(plan), CodeExpression("value")),),
                is_subroutine=True,
            ),
        )

    def _visit_ArgumentTransferPlan(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Lower one argument through the completed optional-mode action."""
        return self._lower_argument(plan)

    def _lower_argument(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Dispatch one completed bridge optional mode explicitly."""
        if plan.callback is not None:
            return ()
        mode = plan.entrypoint.optional_mode
        if plan.object_kind is ObjectKind.DERIVED_TYPE:
            return self._lower_derived_argument(plan, mode)
        if plan.object_kind is ObjectKind.NUMPY_ARRAY:
            return self._lower_array_argument(plan, mode)
        if self._is_character_buffer_argument(plan):
            return self._lower_character_buffer_argument(plan, mode)
        if plan.object_kind not in {ObjectKind.SCALAR, ObjectKind.STRING}:
            raise ValueError(f"Unsupported Fortran argument object kind for {plan.owner_path!r}: {plan.object_kind!r}")
        return self._lower_scalar_or_string_argument(plan, mode)

    # Derived-type argument lowering.
    def _lower_derived_argument(
        self,
        plan: ArgumentTransferPlan,
        _mode: OptionalMode,
    ) -> tuple[FortranParameter, ...]:
        """Receive the generic carrier and typed module-origin operations."""
        name = plan.entrypoint.parameter_name
        return (
            FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),
            FortranParameter(f"bound_{name}_access", "integer(c_int)", ("value",)),
            FortranParameter(f"bound_{name}_identity", "type(c_ptr)", ("value",)),
            *(
                (FortranParameter(f"bound_{name}_polymorphic", "integer(c_int)", ("value",)),)
                if plan.polymorphic is not None
                else ()
            ),
            FortranParameter(f"bound_{name}_scoped", "type(c_funptr)", ("value",)),
            FortranParameter(f"bound_{name}_checkout", "type(c_funptr)", ("value",)),
            FortranParameter(f"bound_{name}_restore", "type(c_funptr)", ("value",)),
            FortranParameter(f"bound_{name}_status", "integer(c_int)", ("intent(out)",)),
            *(
                (
                    FortranParameter(f"bound_{name}_output", "type(c_ptr)", ("intent(out)",)),
                    FortranParameter(
                        f"bound_{name}_output_present",
                        "integer(c_int)",
                        ("intent(out)",),
                    ),
                )
                if plan.entrypoint.descriptor_output_role is not None
                else ()
            ),
        )

    @staticmethod
    def _is_character_buffer_argument(plan: ArgumentTransferPlan) -> bool:
        """Return whether an argument uses the completed character-buffer handoff mode."""
        return (
            plan.object_kind is ObjectKind.STRING
            and plan.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
        )

    def _lower_character_buffer_argument(
        self,
        plan: ArgumentTransferPlan,
        mode: OptionalMode,
    ) -> tuple[FortranParameter, ...]:
        """Lower required or nullable character-buffer parameters."""
        if mode not in {OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE}:
            raise ValueError(f"Unsupported Fortran string presence mode for {plan.owner_path!r}: {mode!r}")
        return self._lower_argument_string_value(plan)

    def _lower_scalar_or_string_argument(
        self,
        plan: ArgumentTransferPlan,
        mode: OptionalMode,
    ) -> tuple[FortranParameter, ...]:
        """Lower non-buffer scalar and string optional modes."""
        match mode:
            case OptionalMode.REQUIRED:
                return self._lower_argument_required(plan)
            case OptionalMode.REQUIRED_DESCRIPTOR:
                return self._lower_argument_required_descriptor(plan)
            case OptionalMode.NULLABLE_VALUE:
                return self._lower_argument_nullable_value(plan)
            case OptionalMode.DESCRIPTOR:
                return self._lower_argument_descriptor(plan)
        raise ValueError(f"Unsupported Fortran argument optional mode for {plan.owner_path!r}: {mode!r}")

    def _lower_argument_required_descriptor(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Receive one required Python argument as a nullable descriptor payload."""
        name = plan.entrypoint.parameter_name
        parameters = [FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",))]
        if plan.entrypoint.descriptor_output_role is not None:
            parameters.extend(
                (
                    FortranParameter(f"bound_{name}_output", "type(c_ptr)", ("value",)),
                    FortranParameter(f"bound_{name}_output_present", "integer(c_int)", ("intent(out)",)),
                )
            )
        return tuple(parameters)

    def _lower_array_argument(
        self,
        plan: ArgumentTransferPlan,
        mode: OptionalMode,
    ) -> tuple[FortranParameter, ...]:
        """Dispatch one array parameter from its completed handoff mode."""
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            if mode not in {OptionalMode.REQUIRED, OptionalMode.DESCRIPTOR}:
                raise ValueError(f"Unsupported Fortran descriptor presence mode for {plan.owner_path!r}: {mode!r}")
            return self._lower_argument_native_array_descriptor(plan)
        if mode not in {OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE}:
            raise ValueError(f"Unsupported Fortran array presence mode for {plan.owner_path!r}: {mode!r}")
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._lower_argument_array_buffer(plan)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            return self._lower_opaque_array_argument(plan, mode)
        raise ValueError(f"Unsupported Fortran array handoff for {plan.owner_path!r}: {plan.entrypoint.handoff_mode!r}")

    def _lower_opaque_array_argument(
        self,
        plan: ArgumentTransferPlan,
        mode: OptionalMode,
    ) -> tuple[FortranParameter, ...]:
        """Lower raw array addresses and rank-zero scalar-storage arrays."""
        if mode is OptionalMode.REQUIRED and self._is_opaque_array_required_argument(plan):
            return self._lower_argument_required_opaque_address(plan)
        if mode is OptionalMode.NULLABLE_VALUE and self._is_scalar_storage_array(plan.array):
            return self._lower_argument_nullable_value(plan)
        raise ValueError(f"Unsupported Fortran array handoff for {plan.owner_path!r}: {plan.entrypoint.handoff_mode!r}")

    def _is_opaque_array_required_argument(self, plan: ArgumentTransferPlan) -> bool:
        """Return whether a required array-shaped argument uses an opaque address."""
        return bool(
            plan.bridge.native_action is NativeBarrierAction.PASS_RAW_ADDRESS
            or self._is_scalar_storage_array(plan.array)
        )

    # Native-array-handle entrypoint parameters.
    def _lower_argument_native_array_descriptor(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Receive one standard descriptor as a typed allocatable/pointer dummy."""
        handle = plan.native_array_handle
        name = plan.entrypoint.parameter_name
        attribute = "allocatable" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "pointer"
        parameters = [
            FortranParameter(
                name,
                self._native_array_argument_element_type(plan),
                (attribute, self._array_dimension_attribute(handle.array.rank)),
            )
        ]
        if plan.entrypoint.optional_mode is OptionalMode.DESCRIPTOR:
            parameters.append(FortranParameter(f"bound_{name}_present", "type(c_ptr)", ("value",)))
        return tuple(parameters)

    def _native_array_argument_element_type(self, plan: ArgumentTransferPlan) -> str:
        """Return one numeric or deferred-character descriptor dummy type."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "character(kind=c_char, len=:)"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).fortran_spelling

    def _lower_argument_required(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Dispatch one required entrypoint parameter from its completed ABI shape."""
        mode = plan.entrypoint.handoff_mode
        match mode:
            case ArgumentHandoffMode.VALUE:
                return self._lower_argument_required_value(plan)
            case ArgumentHandoffMode.TYPED_REFERENCE:
                return self._lower_argument_required_typed_reference(plan)
            case ArgumentHandoffMode.OPAQUE_ADDRESS:
                return self._lower_argument_required_opaque_address(plan)
            case ArgumentHandoffMode.CHARACTER_BUFFER:
                return self._lower_argument_string_value(plan)
        raise ValueError(f"Unsupported Fortran argument handoff for {plan.owner_path!r}: {mode!r}")

    # Scalar argument lowering.
    def _lower_argument_required_value(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Return one interoperable scalar value parameter."""
        return (self._parameter(plan, ("value",)),)

    def _lower_argument_required_typed_reference(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Return one ordinary interoperable scalar reference parameter."""
        return (self._parameter(plan, ()),)

    def _lower_argument_required_opaque_address(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Return one C pointer value for caller-owned opaque storage."""
        name = plan.entrypoint.parameter_name
        return (FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),)

    # String argument lowering.
    def _lower_argument_string_value(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Receive one C UTF-8 payload address and its runtime byte length."""
        name = plan.entrypoint.parameter_name
        return (
            FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),
            FortranParameter(f"{name}_length", "integer(c_int64_t)", ("value",)),
        )

    # Ordinary-array argument lowering.
    def _lower_argument_array_buffer(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Receive exactly the ordinary-array ABI fields named by the plan."""
        array = plan.array
        if array is None:
            raise ValueError(f"Array argument {plan.owner_path!r} has no handoff spec")
        name = plan.entrypoint.parameter_name
        return (
            FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),
            *(
                (FortranParameter(f"{name}_rank", "integer(c_int64_t)", ("value",)),)
                if array.runtime_rank_role is not None
                else ()
            ),
            *(
                (FortranParameter(f"{name}_itemsize", "integer(c_int64_t)", ("value",)),)
                if array.itemsize_role is not None
                else ()
            ),
            *(
                (FortranParameter(f"{name}_dense_actual", "integer(c_int)", ("value",)),)
                if array.dense_actual_role is not None
                else ()
            ),
            *(
                FortranParameter(f"{name}_extent_{axis}", "integer(c_int64_t)", ("value",))
                for axis in range(len(array.extent_roles))
            ),
            *(
                FortranParameter(f"{name}_upper_bound_{axis}", "integer(c_int64_t)", ("value",))
                for axis in range(len(array.upper_bound_roles))
            ),
            *(
                FortranParameter(f"{name}_stride_{axis}", "integer(c_int64_t)", ("value",))
                for axis in range(len(array.stride_roles))
            ),
        )

    def _lower_argument_nullable_value(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Return one nullable C pointer parameter."""
        name = plan.entrypoint.parameter_name
        return (FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),)

    def _lower_argument_descriptor(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Return nullable value and explicit presence pointer parameters."""
        name = plan.entrypoint.parameter_name
        return (
            FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),
            FortranParameter(f"bound_{name}_present", "type(c_ptr)", ("value",)),
        )

    def _parameter(self, plan: ArgumentTransferPlan, attributes: tuple[str, ...]) -> FortranParameter:
        """Return one entrypoint ABI parameter from its completed transfer plan."""
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        return FortranParameter(plan.entrypoint.parameter_name, scalar_type.fortran_spelling, attributes)

    def _function_body(
        self,
        plan: FunctionPlan,
        result_name: str | None,
    ) -> tuple[
        tuple[FortranAssignment | FortranCall | FortranIf | FortranSelectCase, ...],
        tuple[FortranFunction, ...],
    ]:
        """Build one native-call leaf plus linear optional-derived dispatch."""
        result_name = self._native_direct_result_name(plan, result_name)
        derived_optional = tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.projected_call_slot.native_position)
            if argument.derived_call is not None
            and argument.entrypoint.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
        )
        if derived_optional:
            procedures = self._derived_optional_dispatch_procedures(plan, derived_optional, result_name)
            return (FortranCall(self._derived_optional_step_name(0), ()),), procedures
        return self._ordinary_function_body(plan, result_name), ()

    def _ordinary_function_body(
        self,
        plan: FunctionPlan,
        result_name: str | None,
        *,
        present: frozenset[str] = frozenset(),
        replacements: dict[str, str] | None = None,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf | FortranSelectCase, ...]:
        """Build the existing rank and non-derived optional call tree."""
        replacements = dict(replacements or {})
        polymorphic = self._polymorphic_arguments(plan)
        if polymorphic:
            return (
                self._polymorphic_call_tree(
                    plan,
                    polymorphic,
                    0,
                    present,
                    result_name,
                    replacements,
                ),
            )
        assumed_rank = self._assumed_rank_arguments(plan)
        if assumed_rank:
            return (
                self._assumed_rank_call_tree(
                    plan,
                    assumed_rank,
                    0,
                    replacements,
                    result_name,
                    present=present,
                ),
            )
        optional = self._non_derived_optional_arguments(plan)
        if not optional:
            return (self._native_invocation(plan, present, result_name, replacements),)
        return (self._optional_call_tree(plan, optional, 0, present, result_name, replacements),)

    @staticmethod
    def _polymorphic_arguments(plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return polymorphic inputs in original-Fortran call order."""
        return tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.projected_call_slot.native_position)
            if argument.polymorphic is not None
        )

    @staticmethod
    def _assumed_rank_arguments(plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return assumed-rank arrays in original-Fortran call order."""
        return tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.projected_call_slot.native_position)
            if argument.array is not None and argument.array.rank is None
        )

    @staticmethod
    def _non_derived_optional_arguments(plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return optional arguments handled by the ordinary presence tree."""
        return tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.projected_call_slot.native_position)
            if argument.entrypoint.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
            and argument.derived_call is None
        )

    def _polymorphic_call_tree(
        self,
        plan: FunctionPlan,
        arguments: tuple[ArgumentTransferPlan, ...],
        index: int,
        present: frozenset[str],
        result_name: str | None,
        replacements: dict[str, str],
    ) -> FortranAssignment | FortranCall | FortranIf | FortranSelectCase:
        """Dispatch N enumerated scalar inputs without speculative native calls."""
        if index == len(arguments):
            return self._native_invocation(plan, present, result_name, replacements)
        argument = arguments[index]
        cases = []
        for variant in argument.polymorphic.variants:
            replacements[argument.owner_path] = self._polymorphic_variant_name(argument, variant.abi_code)
            cases.append(
                FortranCase(
                    variant.abi_code,
                    (
                        self._polymorphic_call_tree(
                            plan,
                            arguments,
                            index + 1,
                            present,
                            result_name,
                            replacements,
                        ),
                    ),
                )
            )
        replacements.pop(argument.owner_path, None)
        cases.append(FortranCase(None, ()))
        name = argument.entrypoint.parameter_name
        return FortranSelectCase(CodeExpression(f"bound_{name}_polymorphic"), tuple(cases))

    @staticmethod
    def _polymorphic_variant_name(argument: ArgumentTransferPlan, abi_code: int) -> str:
        """Name one bridge-local typed pointer from its stable plan code."""
        return f"{argument.entrypoint.parameter_name}_polymorphic_{abi_code}"

    def _derived_optional_dispatch_procedures(
        self,
        plan: FunctionPlan,
        optional: tuple[ArgumentTransferPlan, ...],
        result_name: str | None,
    ) -> tuple[FortranFunction, ...]:
        """Propagate N optional derived dummies with O(N) adapter procedures."""
        procedures = []
        for index, argument in enumerate(optional):
            carried = optional[:index]
            parameters = tuple(self._derived_optional_parameter(item) for item in carried)
            passed = tuple(CodeExpression(self._derived_optional_parameter_name(item)) for item in carried)
            expression = CodeExpression(self._native_argument_expression(argument))
            procedures.append(
                FortranFunction(
                    name=self._derived_optional_step_name(index),
                    parameters=parameters,
                    body=(
                        FortranIf(
                            CodeExpression(self._presence_condition(argument)),
                            body=(
                                FortranCall(
                                    self._derived_optional_step_name(index + 1),
                                    (*passed, expression),
                                ),
                            ),
                            else_body=(FortranCall(self._derived_optional_step_name(index + 1), passed),),
                        ),
                    ),
                    is_subroutine=True,
                )
            )
        replacements = {argument.owner_path: self._derived_optional_parameter_name(argument) for argument in optional}
        present = frozenset(argument.owner_path for argument in optional)
        procedures.append(
            FortranFunction(
                name=self._derived_optional_step_name(len(optional)),
                parameters=tuple(self._derived_optional_parameter(item) for item in optional),
                body=self._ordinary_function_body(
                    plan,
                    result_name,
                    present=present,
                    replacements=replacements,
                ),
                is_subroutine=True,
            )
        )
        return tuple(procedures)

    def _derived_optional_parameter(self, argument: ArgumentTransferPlan) -> FortranParameter:
        """Mirror the completed native dummy category and add OPTIONAL."""
        return self._derived_native_parameter(
            argument,
            self._derived_optional_parameter_name(argument),
            optional=True,
        )

    def _derived_native_parameter(
        self,
        argument: ArgumentTransferPlan,
        name: str,
        *,
        optional: bool,
        category: DerivedDummyCategory | None = None,
    ) -> FortranParameter:
        """Declare one typed adapter dummy from its completed native category."""
        category = category or argument.derived_call.dummy_category
        attributes = {
            DerivedDummyCategory.OBJECT: (),
            DerivedDummyCategory.TARGET: ("target",),
            DerivedDummyCategory.ALLOCATABLE: ("allocatable",),
            DerivedDummyCategory.ALLOCATABLE_TARGET: ("allocatable", "target"),
            DerivedDummyCategory.POINTER: ("pointer",),
            DerivedDummyCategory.VALUE: ("value",),
        }[category]
        if optional:
            attributes = (*attributes, "optional")
        return FortranParameter(
            name,
            f"type({self._derived_native_alias(argument.derived.backend_symbol)})",
            attributes,
        )

    @staticmethod
    def _derived_optional_parameter_name(argument: ArgumentTransferPlan) -> str:
        """Return the local optional-presence parameter name for one derived argument."""
        return f"prik_optional_{argument.entrypoint.parameter_name}"

    @staticmethod
    def _derived_optional_step_name(index: int) -> str:
        """Return the deterministic nested-procedure name for one optional derived dispatch case."""
        return f"prik_derived_optional_step_{index}"

    def _optional_call_tree(
        self,
        plan: FunctionPlan,
        optional: tuple[ArgumentTransferPlan, ...],
        index: int,
        present: frozenset[str],
        result_name: str | None,
        replacements: dict[str, str],
    ) -> FortranAssignment | FortranCall | FortranIf:
        """Return an exhaustive native-call tree for optional presence states."""
        if index == len(optional):
            return self._native_invocation(plan, present, result_name, replacements)
        argument = optional[index]
        present_roles = present | {argument.owner_path}
        return FortranIf(
            condition=CodeExpression(self._presence_condition(argument)),
            body=(
                *self._present_preparation(argument),
                self._optional_call_tree(plan, optional, index + 1, present_roles, result_name, replacements),
            ),
            else_body=(self._optional_call_tree(plan, optional, index + 1, present, result_name, replacements),),
        )

    def _native_invocation(
        self,
        plan: FunctionPlan,
        present: frozenset[str],
        result_name: str | None,
        replacements: dict[str, str],
    ) -> FortranAssignment | FortranCall | FortranPointerAssignment:
        """Build the native procedure call from the ordered completed call-slot plan."""
        if plan.bridge.native_invocation is NativeInvocationKind.DEFINED_OPERATOR:
            return self._defined_operator_invocation(plan, present, result_name, replacements)
        if plan.bridge.native_invocation is NativeInvocationKind.DEFINED_ASSIGNMENT:
            return self._defined_assignment_invocation(plan, present, replacements)
        native_name, receiver_position = self._native_invocation_target(plan, replacements)
        arguments = self._native_arguments(
            plan,
            present,
            replacements,
            excluded_position=receiver_position,
        )
        if plan.bridge.native_is_subroutine:
            return FortranCall(native_name, arguments)
        return self._native_function_result_invocation(plan, result_name, native_name, arguments)

    def _defined_operator_invocation(
        self,
        plan: FunctionPlan,
        present: frozenset[str],
        result_name: str | None,
        replacements: dict[str, str],
    ) -> FortranAssignment | FortranCall | FortranPointerAssignment:
        """Lower one completed public defined operator without private specifics."""
        token = plan.bridge.native_operator
        arguments = self._native_arguments(plan, present, replacements)
        if token is None or len(arguments) not in {1, 2}:
            raise ValueError(f"Defined operator {plan.owner_path!r} has an incomplete invocation plan")
        values = tuple(argument.text for argument in arguments)
        expression = f"{token} {values[0]}" if len(values) == 1 else f"{values[0]} {token} {values[1]}"
        return self._native_result_expression_invocation(plan, result_name, expression)

    def _defined_assignment_invocation(
        self,
        plan: FunctionPlan,
        present: frozenset[str],
        replacements: dict[str, str],
    ) -> FortranAssignment:
        """Lower one completed defined assignment in native argument order."""
        arguments = self._native_arguments(plan, present, replacements)
        if len(arguments) != 2:
            raise ValueError(f"Defined assignment {plan.owner_path!r} must have two native arguments")
        return FortranAssignment(arguments[0].text, arguments[1])

    def _native_function_result_invocation(
        self,
        plan: FunctionPlan,
        result_name: str | None,
        native_name: str,
        arguments: tuple[CodeExpression, ...],
    ) -> FortranAssignment | FortranCall:
        """Lower one completed function-result handoff through its named leaf."""
        if result_name is None:
            raise ValueError(f"{plan.owner_path!r} native function is missing a bridge result")
        expression = f"{native_name}({', '.join(item.text for item in arguments)})"
        return self._native_result_expression_invocation(plan, result_name, expression)

    def _native_result_expression_invocation(
        self,
        plan: FunctionPlan,
        result_name: str | None,
        expression: str,
    ) -> FortranAssignment | FortranCall | FortranPointerAssignment:
        """Store one completed native result expression through its handoff leaf."""
        direct_result = self._direct_result(plan)
        if self._uses_owned_direct_array_result_collector(plan):
            return FortranCall(
                self._owned_direct_array_result_collector_name(),
                (CodeExpression(expression), CodeExpression("result")),
            )
        if self._uses_allocatable_character_result_collector(direct_result):
            return FortranCall(
                self._allocatable_character_result_collector_name(),
                (CodeExpression(expression), CodeExpression("result_value")),
            )
        if self._uses_pointer_result_assignment(direct_result):
            return FortranPointerAssignment(result_name, CodeExpression(expression))
        return FortranAssignment(result_name, CodeExpression(expression))

    def _uses_pointer_result_assignment(self, result: ResultPlan | None) -> bool:
        """Return whether the completed result keeps native pointer association."""
        if self._is_pointer_derived_holder_result(result):
            return True
        return bool(
            result is not None
            and (
                (
                    result.scalar_descriptor is not None
                    and result.scalar_descriptor.descriptor_kind is NativeArrayDescriptorKind.POINTER
                )
                or (
                    result.native_array_handle is not None
                    and result.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.POINTER
                )
            )
        )

    def _native_invocation_target(
        self,
        plan: FunctionPlan,
        replacements: dict[str, str],
    ) -> tuple[str, int | None]:
        """Select a module procedure or one validated type-bound receiver."""
        class_call = plan.class_call
        if class_call is None or class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE:
            return self._native_function_name(plan), None
        if class_call.passed_object_position is None or class_call.type_bound_name is None:
            raise ValueError(f"Type-bound call {plan.owner_path!r} has incomplete receiver policy")
        receiver = next(
            (argument for argument in plan.arguments if argument.native_position == class_call.passed_object_position),
            None,
        )
        if receiver is None:
            raise ValueError(f"Type-bound call {plan.owner_path!r} has no passed-object argument")
        expression = replacements.get(receiver.owner_path, self._native_argument_expression(receiver))
        return f"{expression}%{class_call.type_bound_name}", receiver.projected_call_slot.native_position

    @staticmethod
    def _is_pointer_derived_holder_result(result: ResultPlan | None) -> bool:
        """Return whether a result uses the completed pointer-holder derived storage mode."""
        return bool(
            result is not None
            and result.object_kind is ObjectKind.DERIVED_TYPE
            and result.derived is not None
            and result.derived.storage is DerivedObjectStorage.POINTER_HOLDER
        )

    def _native_arguments(
        self,
        plan: FunctionPlan,
        present: frozenset[str],
        replacements: dict[str, str],
        *,
        excluded_position: int | None = None,
    ) -> tuple[CodeExpression, ...]:
        """Return native call expressions in planned ABI order without recomputing argument policy."""
        expressions = dict(self._visible_native_argument_entries(plan, present, replacements))
        expressions.update(
            (slot.native_position, CodeExpression(slot.native_name.casefold()))
            for slot in plan.entrypoint.projected_slots
            if slot.adapter is not None
            if slot.projection_action
            in {
                EntrypointProjectionAction.TYPED_LITERAL,
                EntrypointProjectionAction.COMPUTED_LENGTH,
                EntrypointProjectionAction.COMPUTED_PRESENCE,
                EntrypointProjectionAction.COMPUTED_SHAPE,
                EntrypointProjectionAction.COMPUTED_STRIDE,
                EntrypointProjectionAction.WORK_STORAGE,
            }
        )
        expressions.update(self._hidden_native_result_entries(plan))
        return tuple(
            expressions[slot.native_position]
            for slot in self._adapter_slots(plan)
            if slot.native_position in expressions and slot.native_position != excluded_position
        )

    def _visible_native_argument_entries(
        self,
        plan: FunctionPlan,
        present: frozenset[str],
        replacements: dict[str, str],
    ) -> tuple[tuple[int, CodeExpression], ...]:
        """Return native-position entries for present Python arguments."""
        entries = []
        has_optional = self._has_optional_arguments(plan)
        for argument in plan.arguments:
            if (
                argument.entrypoint.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
                and argument.owner_path not in present
            ):
                continue
            expression = replacements.get(argument.owner_path, self._native_argument_expression(argument))
            if has_optional:
                expression = f"{argument.bridge.native_name}={expression}"
            entries.append((argument.projected_call_slot.native_position, CodeExpression(expression)))
        return tuple(entries)

    def _assumed_rank_call_tree(
        self,
        plan: FunctionPlan,
        arguments: tuple[ArgumentTransferPlan, ...],
        index: int,
        replacements: dict[str, str],
        result_name: str | None,
        *,
        present: frozenset[str] = frozenset(),
    ) -> FortranAssignment | FortranCall | FortranIf | FortranSelectCase:
        """Dispatch each runtime-rank array through explicit one-to-fifteen branches."""
        if index == len(arguments):
            optional = tuple(
                argument
                for argument in sorted(plan.arguments, key=lambda item: item.projected_call_slot.native_position)
                if argument.entrypoint.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
                and argument.derived_call is None
            )
            if optional:
                return self._optional_call_tree(plan, optional, 0, present, result_name, replacements)
            return self._native_invocation(plan, present, result_name, replacements)
        argument = arguments[index]
        name = argument.entrypoint.parameter_name
        cases = []
        for rank in range(1, 16):
            rank_name = f"{name}_rank_{rank}"
            replacements[argument.owner_path] = rank_name
            nested = self._assumed_rank_call_tree(
                plan,
                arguments,
                index + 1,
                replacements,
                result_name,
                present=present,
            )
            del replacements[argument.owner_path]
            cases.append(
                FortranCase(
                    rank,
                    (
                        self._assumed_rank_pointer_initializer(argument, rank, rank_name),
                        nested,
                    ),
                )
            )
        cases.append(FortranCase(None, ()))
        return FortranSelectCase(CodeExpression(f"{name}_rank"), tuple(cases))

    def _hidden_native_result_entries(
        self,
        plan: FunctionPlan,
    ) -> tuple[tuple[int, CodeExpression], ...]:
        """Return all mechanically lowered hidden-result native entries."""
        entries = []
        for slot in self._adapter_slots(plan):
            if slot.source_kind != "result":
                continue
            expression = self._native_output_value_name(slot)
            if self._has_optional_arguments(plan):
                expression = f"{slot.native_name}={expression}"
            entries.append((slot.native_position, CodeExpression(expression)))
        return tuple(entries)

    def _native_argument_expression(self, plan: ArgumentTransferPlan) -> str:
        """Return the native actual expression selected by one completed call slot."""
        name = plan.entrypoint.parameter_name
        if plan.callback is not None:
            return plan.callback.bridge.adapter_symbol
        if plan.derived_call is not None:
            if plan.derived_call.dummy_category in {
                DerivedDummyCategory.ALLOCATABLE,
                DerivedDummyCategory.ALLOCATABLE_TARGET,
            }:
                return f"{name}_allocatable_holder%value"
            if plan.derived_call.dummy_category is DerivedDummyCategory.POINTER:
                return f"{name}_call_pointer"
            return name
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._array_native_argument_expression(plan)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return name
        if plan.entrypoint.optional_mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            return f"{name}_descriptor"
        if plan.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
            return f"{name}_native"
        return name

    def _presence_condition(self, plan: ArgumentTransferPlan) -> str:
        """Return the local C-pointer association condition for one nullable entrypoint argument."""
        name = plan.entrypoint.parameter_name
        if plan.derived_call is not None:
            return f"bound_{name}_access /= 0_c_int"
        suffix = "_present" if plan.entrypoint.optional_mode is OptionalMode.DESCRIPTOR else ""
        return f"c_associated(bound_{name}{suffix})"

    def _present_preparation(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranAssignment | FortranPointerAssignment | FortranCall | FortranIf, ...]:
        """Dispatch only the bridge data action completed before lowering."""
        if plan.derived_call is not None:
            return ()
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return ()
        action = plan.bridge.data_action
        match action:
            case BridgeDataAction.ASSOCIATE_VIEW:
                return self._prepare_present_associated_view(plan)
            case BridgeDataAction.COPY_REPRESENTATION:
                return self._prepare_present_representation_copy(plan)
        raise ValueError(f"Unsupported present bridge data action for {plan.owner_path!r}: {action!r}")

    def _prepare_present_associated_view(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranPointerAssignment | FortranCall | FortranIf, ...]:
        """Associate a non-owning native view without copying payload data."""
        name = plan.entrypoint.parameter_name
        if self._uses_allocatable_holder(plan):
            return (
                FortranAssignment(f"bound_{name}_allocation_status", CodeExpression("0_c_int")),
                FortranIf(
                    CodeExpression(f"c_associated(bound_{name})"),
                    body=(
                        FortranCall(
                            "c_f_pointer",
                            (CodeExpression(f"bound_{name}"), CodeExpression(f"{name}_holder")),
                        ),
                    ),
                    else_body=(
                        FortranAllocate(f"{name}_holder", status=f"{name}_allocation_status"),
                        FortranAssignment(
                            f"bound_{name}_allocation_status",
                            CodeExpression(f"{name}_allocation_status"),
                        ),
                    ),
                ),
            )
        if plan.object_kind is ObjectKind.DERIVED_TYPE:
            return (
                FortranCall(
                    "c_f_pointer",
                    (CodeExpression(f"bound_{name}"), CodeExpression(name)),
                ),
            )
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return ()
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._array_pointer_initializer_nodes(plan)
        if plan.entrypoint.optional_mode is OptionalMode.NULLABLE_VALUE:
            return (
                FortranCall(
                    "c_f_pointer",
                    (CodeExpression(f"bound_{name}"), CodeExpression(name)),
                ),
            )
        if plan.entrypoint.optional_mode not in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            raise ValueError(f"Associated-view preparation requires an optional argument: {plan.owner_path!r}")
        if plan.projected_call_slot.value_kind != "pointer":
            raise ValueError(f"Associated descriptor view requires pointer policy: {plan.owner_path!r}")
        return (
            self._descriptor_input_pointer_call(name),
            FortranIf(
                CodeExpression(f"associated({name}_input)"),
                body=(FortranPointerAssignment(f"{name}_descriptor", CodeExpression(f"{name}_input")),),
            ),
        )

    def _prepare_present_representation_copy(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranCall | FortranAssignment | FortranIf, ...]:
        """Copy only when completed policy requires a different native representation."""
        if plan.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY:
            nodes: list[FortranCall | FortranAssignment | FortranIf] = list(self._array_pointer_initializer_nodes(plan))
            if plan.array_copy_in:
                nodes.append(
                    FortranAssignment(
                        self._logical_array_native_name(plan),
                        CodeExpression(self._array_boundary_argument_expression(plan)),
                    )
                )
            return tuple(nodes)
        if plan.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
            name = plan.entrypoint.parameter_name
            return (FortranAssignment(f"{name}_native", CodeExpression(name)),)
        if plan.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER:
            return self._string_value_initializer_nodes(plan)
        if self._is_derived_value_copy(plan):
            name = plan.entrypoint.parameter_name
            return (
                FortranCall(
                    "c_f_pointer",
                    (CodeExpression(f"bound_{name}"), CodeExpression(name)),
                ),
                FortranAssignment(f"{name}_value", CodeExpression(name)),
            )
        if plan.entrypoint.optional_mode not in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            raise ValueError(f"Representation copy requires descriptor policy: {plan.owner_path!r}")
        if plan.projected_call_slot.value_kind != "allocatable":
            raise ValueError(f"Representation copy requires allocatable policy: {plan.owner_path!r}")
        name = plan.entrypoint.parameter_name
        return (
            self._descriptor_input_pointer_call(name),
            FortranIf(
                CodeExpression(f"associated({name}_input)"),
                body=(FortranAssignment(f"{name}_descriptor", CodeExpression(f"{name}_input")),),
            ),
        )

    def _descriptor_input_pointer_call(self, name: str) -> FortranCall:
        """Associate one binding value with a typed descriptor-input view."""
        return FortranCall(
            "c_f_pointer",
            (CodeExpression(f"bound_{name}"), CodeExpression(f"{name}_input")),
        )

    def _optional_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Return helper declarations for every nontrivial optional argument."""
        return tuple(
            declaration for argument in plan.arguments for declaration in self._optional_argument_declarations(argument)
        )

    def _optional_argument_declarations(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Return optional helper declarations for one completed handoff."""
        if argument.derived_call is not None:
            return ()
        mode = argument.entrypoint.optional_mode
        if mode is OptionalMode.REQUIRED or argument.entrypoint.handoff_mode in {
            ArgumentHandoffMode.NATIVE_DESCRIPTOR,
            ArgumentHandoffMode.CHARACTER_BUFFER,
            ArgumentHandoffMode.ARRAY_BUFFER,
        }:
            return ()
        name = argument.entrypoint.parameter_name
        if argument.object_kind is ObjectKind.DERIVED_TYPE:
            if self._uses_allocatable_holder(argument):
                return (
                    FortranDeclaration(
                        f"{name}_holder",
                        f"type({self._allocatable_holder_type_name(argument.derived.backend_symbol)})",
                        ("pointer",),
                    ),
                    FortranDeclaration(f"{name}_allocation_status", "integer(c_int)"),
                )
            return self._derived_argument_declarations(argument)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name)
        if mode is OptionalMode.NULLABLE_VALUE:
            return (FortranDeclaration(name, scalar_type.fortran_spelling, ("pointer",)),)
        declarations = [FortranDeclaration(f"{name}_input", scalar_type.fortran_spelling, ("pointer",))]
        descriptor_attribute = "pointer" if argument.projected_call_slot.value_kind == "pointer" else "allocatable"
        declarations.append(
            FortranDeclaration(f"{name}_descriptor", scalar_type.fortran_spelling, (descriptor_attribute,))
        )
        if mode is OptionalMode.REQUIRED_DESCRIPTOR and argument.entrypoint.descriptor_output_role is not None:
            declarations.append(FortranDeclaration(f"{name}_output", scalar_type.fortran_spelling, ("pointer",)))
        return tuple(declarations)

    def _logical_scalar_argument_declarations(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare exact-kind native locals selected by scalar logical policy."""
        declarations = []
        for argument in plan.arguments:
            if argument.scalar_logical_abi is not ScalarLogicalABI.NATIVE_KIND_COPY:
                continue
            if not argument.scalar_native_type:
                raise ValueError(f"Logical argument {argument.owner_path!r} has no native type spelling")
            declarations.append(
                FortranDeclaration(
                    f"{argument.entrypoint.parameter_name}_native",
                    argument.scalar_native_type,
                )
            )
        return tuple(declarations)

    def _logical_scalar_argument_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment, ...]:
        """Copy required C Boolean values into their exact native kinds."""
        return tuple(
            FortranAssignment(
                f"{argument.entrypoint.parameter_name}_native",
                CodeExpression(argument.entrypoint.parameter_name),
            )
            for argument in plan.arguments
            if argument.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY
            and argument.entrypoint.optional_mode is OptionalMode.REQUIRED
        )

    def _logical_scalar_argument_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy mutable exact-kind logical values back to C Boolean storage."""
        nodes = []
        for argument in plan.arguments:
            if argument.scalar_logical_abi is not ScalarLogicalABI.NATIVE_KIND_COPY or not argument.mutates_native:
                continue
            name = argument.entrypoint.parameter_name
            assignment = FortranAssignment(name, CodeExpression(f"{name}_native"))
            if argument.entrypoint.optional_mode is OptionalMode.REQUIRED:
                nodes.append(assignment)
            else:
                nodes.append(FortranIf(CodeExpression(self._presence_condition(argument)), body=(assignment,)))
        return tuple(nodes)

    def _opaque_address_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Return typed pointer locals for required opaque scalar addresses."""
        return tuple(
            declaration
            for argument in plan.arguments
            if (
                argument.derived_call is None
                and argument.entrypoint.optional_mode is OptionalMode.REQUIRED
                and argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
                and argument.bridge.data_action
                in {BridgeDataAction.ASSOCIATE_VIEW, BridgeDataAction.COPY_REPRESENTATION}
                and (
                    argument.object_kind in {ObjectKind.SCALAR, ObjectKind.DERIVED_TYPE}
                    or self._is_scalar_storage_array(argument.array)
                )
            )
            for declaration in (
                self._derived_argument_declarations(argument)
                if argument.object_kind is ObjectKind.DERIVED_TYPE
                else (
                    FortranDeclaration(
                        argument.entrypoint.parameter_name,
                        self._opaque_argument_type(argument),
                        ("pointer",),
                    ),
                )
            )
        )

    def _derived_argument_declarations(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare the typed pointee and optional bridge-local value copy."""
        name = argument.entrypoint.parameter_name
        derived_type = f"type({self._derived_native_alias(argument.derived.backend_symbol)})"
        declarations = [FortranDeclaration(name, derived_type, ("pointer",))]
        if self._is_derived_value_copy(argument):
            declarations.append(FortranDeclaration(f"{name}_value", derived_type))
        return tuple(declarations)

    def _opaque_argument_type(self, argument: ArgumentTransferPlan) -> str:
        """Return the typed scalar or derived pointee selected by policy."""
        if argument.object_kind is ObjectKind.DERIVED_TYPE:
            return f"type({self._derived_native_alias(argument.derived.backend_symbol)})"
        return PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name).fortran_spelling

    def _opaque_address_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Associate typed scalar locals with caller-provided C addresses."""
        return tuple(
            node
            for argument in plan.arguments
            if (
                argument.derived_call is None
                and argument.entrypoint.optional_mode is OptionalMode.REQUIRED
                and argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
                and argument.bridge.data_action
                in {BridgeDataAction.ASSOCIATE_VIEW, BridgeDataAction.COPY_REPRESENTATION}
                and (
                    argument.object_kind in {ObjectKind.SCALAR, ObjectKind.DERIVED_TYPE}
                    or self._is_scalar_storage_array(argument.array)
                )
            )
            for node in self._opaque_address_initializer_nodes(argument)
        )

    def _opaque_address_initializer_nodes(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Associate one typed pointer and materialize its planned value copy."""
        name = argument.entrypoint.parameter_name
        association = FortranCall(
            "c_f_pointer",
            (CodeExpression(f"bound_{name}"), CodeExpression(name)),
        )
        if not self._is_derived_value_copy(argument):
            return (association,)
        return association, FortranAssignment(f"{name}_value", CodeExpression(name))

    @staticmethod
    def _is_derived_value_copy(argument: ArgumentTransferPlan) -> bool:
        """Return the completed interoperable aggregate-copy selector."""
        return bool(
            argument.derived is not None and argument.derived.native_handoff is DerivedNativeHandoff.TYPED_VALUE
        )

    # Ordinary-array bridge storage.
    def _array_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare boundary views and policy-selected native logical storage."""
        declarations = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER:
                continue
            array = argument.array
            if array is None:
                raise ValueError(f"Array argument {argument.owner_path!r} is missing its handoff")
            if array.rank is None:
                declarations.extend(self._assumed_rank_array_declarations(argument))
            else:
                attributes = ["pointer"]
                if array.contiguous is True:
                    attributes.append("contiguous")
                attributes.append(self._array_dimension_attribute(array.rank))
                declarations.append(
                    FortranDeclaration(
                        self._array_pointer_name(argument),
                        self._array_element_fortran_type(argument),
                        tuple(attributes),
                    )
                )
                if array.dense_actual_role is not None:
                    declarations.append(
                        FortranDeclaration(
                            argument.entrypoint.parameter_name,
                            self._array_element_fortran_type(argument),
                            ("pointer", self._array_dimension_attribute(array.rank)),
                        )
                    )
                if argument.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY:
                    if not argument.array_native_type:
                        raise ValueError(f"Logical array {argument.owner_path!r} has no native type spelling")
                    declarations.append(
                        FortranDeclaration(
                            self._logical_array_native_name(argument),
                            argument.array_native_type,
                            (self._logical_array_dimension_attribute(argument),),
                        )
                    )
            if argument.array_writeback_abi is ArrayWritebackABI.LOGICAL_LOW_BIT_INT8:
                declarations.append(
                    FortranDeclaration(
                        self._logical_array_byte_pointer_name(argument),
                        "integer(c_int8_t)",
                        ("pointer", "dimension(:)"),
                    )
                )
        return tuple(declarations)

    def _logical_array_argument_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment, ...]:
        """Copy required one-byte Boolean inputs into exact-kind native arrays."""
        return tuple(
            FortranAssignment(
                self._logical_array_native_name(argument),
                CodeExpression(self._array_boundary_argument_expression(argument)),
            )
            for argument in plan.arguments
            if argument.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY
            and argument.array_copy_in
            and argument.entrypoint.optional_mode is OptionalMode.REQUIRED
        )

    def _logical_array_argument_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy exact-kind logical outputs into canonical one-byte storage.

        ``merge`` converts truth values while assigning them to the original
        ``logical(c_bool)`` view, so copy-out and canonicalization share one
        array traversal.  Optional buffers are written only when present.
        """
        finalizers = []
        for argument in plan.arguments:
            if argument.array_logical_abi is not ArrayLogicalABI.NATIVE_KIND_COPY or not argument.array_copy_out:
                continue
            target = self._array_boundary_argument_expression(argument)
            native = self._logical_array_native_name(argument)
            assignment = FortranAssignment(
                target,
                CodeExpression(f"merge(.true._c_bool, .false._c_bool, {native})"),
            )
            if argument.entrypoint.optional_mode is OptionalMode.REQUIRED:
                finalizers.append(assignment)
            else:
                finalizers.append(FortranIf(CodeExpression(self._presence_condition(argument)), body=(assignment,)))
        return tuple(finalizers)

    @staticmethod
    def _logical_array_native_name(argument: ArgumentTransferPlan) -> str:
        """Return the bridge-local exact-kind array name for ``argument``."""
        return f"{argument.entrypoint.parameter_name}_native"

    def _logical_array_dimension_attribute(self, argument: ArgumentTransferPlan) -> str:
        """Render automatic-array extents in the completed native orientation."""
        array = argument.array
        if array is None or array.rank is None:
            raise ValueError(f"Logical array {argument.owner_path!r} requires a concrete rank")
        name = argument.entrypoint.parameter_name
        extents = [f"{name}_extent_{axis}" for axis in range(array.rank)]
        if array.native_order == "ORDER_C":
            extents.reverse()
        return f"dimension({', '.join(extents)})"

    def _array_writeback_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf | FortranSelectCase, ...]:
        """Normalize mutable array bytes through their completed writeback ABI."""
        finalizers = []
        for argument in plan.arguments:
            match argument.array_writeback_abi:
                case ArrayWritebackABI.NOT_APPLICABLE | ArrayWritebackABI.NATIVE_ARRAY:
                    continue
                case ArrayWritebackABI.LOGICAL_LOW_BIT_INT8:
                    nodes = self._logical_array_writeback_nodes(argument)
                case _:
                    raise ValueError(
                        f"Unsupported array writeback ABI for {argument.owner_path!r}: {argument.array_writeback_abi!r}"
                    )
            if argument.entrypoint.optional_mode is OptionalMode.REQUIRED:
                finalizers.extend(nodes)
            else:
                finalizers.append(FortranIf(CodeExpression(self._presence_condition(argument)), body=nodes))
        return tuple(finalizers)

    def _logical_array_writeback_nodes(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranSelectCase, ...]:
        """Associate raw Boolean storage and retain only each element's truth bit."""
        array = argument.array
        if array is None:
            raise ValueError(f"Logical array {argument.owner_path!r} has no handoff")
        if array.rank is not None:
            return self._logical_array_writeback_for_rank(argument, array.rank)
        name = argument.entrypoint.parameter_name
        cases = tuple(
            FortranCase(
                rank,
                self._logical_array_writeback_for_rank(argument, rank),
            )
            for rank in range(1, 16)
        )
        return (FortranSelectCase(CodeExpression(f"{name}_rank"), (*cases, FortranCase(None, ()))),)

    def _logical_array_writeback_for_rank(
        self,
        argument: ArgumentTransferPlan,
        rank: int,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Return logical-array writeback nodes for one rank using the completed ABI conversion action."""
        name = argument.entrypoint.parameter_name
        byte_pointer = self._logical_array_byte_pointer_name(argument)
        byte_count = " * ".join(f"{name}_extent_{axis}" for axis in range(rank))
        return (
            FortranCall(
                "c_f_pointer",
                (
                    CodeExpression(f"bound_{name}"),
                    CodeExpression(byte_pointer),
                    CodeExpression(f"[{byte_count}]"),
                ),
            ),
            FortranAssignment(
                byte_pointer,
                CodeExpression(f"iand({byte_pointer}, 1_c_int8_t)"),
            ),
        )

    @staticmethod
    def _logical_array_byte_pointer_name(argument: ArgumentTransferPlan) -> str:
        """Return the bridge-local byte-pointer name for one logical-array rank conversion."""
        return f"{argument.entrypoint.parameter_name}_logical_bytes"

    def _array_initializers(self, plan: FunctionPlan) -> tuple[FortranCall | FortranIf, ...]:
        """Associate each completed ordinary array data/extent handoff."""
        initializers = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER:
                continue
            if argument.entrypoint.optional_mode is not OptionalMode.REQUIRED:
                continue
            if argument.array is not None and argument.array.rank is None:
                continue
            initializers.extend(self._array_pointer_initializer_nodes(argument))
        return tuple(initializers)

    def _raw_array_address_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare typed non-owning views for caller-supplied raw array addresses."""
        return tuple(
            FortranDeclaration(
                self._array_pointer_name(argument),
                self._array_element_fortran_type(argument),
                ("pointer", self._array_dimension_attribute(argument.array.rank)),
            )
            for argument in self._raw_array_address_arguments(plan)
            if argument.array is not None and argument.array.rank is not None
        )

    def _raw_array_address_initializers(self, plan: FunctionPlan) -> tuple[FortranCall, ...]:
        """Associate raw addresses with typed views using only planned shape facts."""
        return tuple(
            self._raw_array_pointer_initializer(plan, argument) for argument in self._raw_array_address_arguments(plan)
        )

    def _raw_array_pointer_initializer(
        self,
        plan: FunctionPlan,
        argument: ArgumentTransferPlan,
    ) -> FortranCall:
        """Associate one raw address with its completed pointee rank and orientation."""
        array = argument.array
        if array is None or array.rank is None:
            raise ValueError(f"Raw array address {argument.owner_path!r} requires a concrete rank")
        shape = list(self._array_shape_from_roles(array, plan))
        if array.native_order == "ORDER_C":
            shape.reverse()
        name = argument.entrypoint.parameter_name
        return FortranCall(
            "c_f_pointer",
            (
                CodeExpression(f"bound_{name}"),
                CodeExpression(self._array_pointer_name(argument)),
                CodeExpression(f"[{', '.join(shape)}]"),
            ),
        )

    def _raw_array_address_arguments(self, plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return raw array address arguments selected by completed actions."""
        return tuple(
            argument
            for argument in plan.arguments
            if argument.object_kind is ObjectKind.NUMPY_ARRAY
            and argument.bridge.native_action is NativeBarrierAction.PASS_RAW_ADDRESS
            and argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
            and argument.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW
        )

    def _array_pointer_initializer(self, argument: ArgumentTransferPlan) -> FortranCall:
        """Associate one fixed-rank array pointer using planned base extents."""
        array = argument.array
        if array is None or array.rank is None:
            raise ValueError(f"Array argument {argument.owner_path!r} requires a concrete rank")
        name = argument.entrypoint.parameter_name
        extents = [f"{name}_extent_{axis}" for axis in range(array.rank)]
        if array.native_order == "ORDER_C":
            extents.reverse()
        return FortranCall(
            "c_f_pointer",
            (
                CodeExpression(f"bound_{name}"),
                CodeExpression(self._array_pointer_name(argument)),
                CodeExpression(f"[{', '.join(extents)}]"),
            ),
        )

    def _array_pointer_initializer_nodes(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranCall | FortranIf, ...]:
        """Associate base storage and select the planned dense or strided view."""
        association = self._array_pointer_initializer(argument)
        array = argument.array
        if array is None or array.dense_actual_role is None:
            return (association,)
        name = argument.entrypoint.parameter_name
        return (
            association,
            FortranIf(
                CodeExpression(f"{name}_dense_actual /= 0_c_int"),
                body=(FortranPointerAssignment(name, CodeExpression(f"{name}_base")),),
                else_body=(
                    FortranPointerAssignment(
                        name,
                        CodeExpression(self._strided_array_section_expression(argument)),
                    ),
                ),
            ),
        )

    def _assumed_rank_array_declarations(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare one readable typed pointer local for every supported runtime rank."""
        name = argument.entrypoint.parameter_name
        element_type = self._array_element_fortran_type(argument)
        attributes = ("pointer", "contiguous") if argument.array.contiguous is True else ("pointer",)
        return tuple(
            FortranDeclaration(
                f"{name}_rank_{rank}",
                element_type,
                (*attributes, self._array_dimension_attribute(rank)),
            )
            for rank in range(1, 16)
        )

    def _assumed_rank_pointer_initializer(
        self,
        argument: ArgumentTransferPlan,
        rank: int,
        pointer_name: str,
    ) -> FortranCall:
        """Associate one runtime-rank branch with its planned extent prefix."""
        name = argument.entrypoint.parameter_name
        extents = ", ".join(f"{name}_extent_{axis}" for axis in range(rank))
        return FortranCall(
            "c_f_pointer",
            (
                CodeExpression(f"bound_{name}"),
                CodeExpression(pointer_name),
                CodeExpression(f"[{extents}]"),
            ),
        )

    def _array_pointer_name(self, argument: ArgumentTransferPlan) -> str:
        """Name the bridge pointer, separating strided base storage visibly."""
        name = argument.entrypoint.parameter_name
        return f"{name}_base" if argument.array is not None and argument.array.contiguous is False else name

    def _array_native_argument_expression(self, argument: ArgumentTransferPlan) -> str:
        """Pass exact-kind logical storage or the planned boundary array view."""
        if argument.array_logical_abi is ArrayLogicalABI.NATIVE_KIND_COPY:
            return self._logical_array_native_name(argument)
        return self._array_boundary_argument_expression(argument)

    def _array_boundary_argument_expression(self, argument: ArgumentTransferPlan) -> str:
        """Return the dense pointer or planned positive-stride boundary view."""
        array = argument.array
        if array is None:
            raise ValueError(f"Array argument {argument.owner_path!r} has no handoff spec")
        name = argument.entrypoint.parameter_name
        if array.rank is None:
            return name
        pointer_name = self._array_pointer_name(argument)
        if array.contiguous is not False:
            return pointer_name
        if array.dense_actual_role is not None:
            return name
        return self._strided_array_section_expression(argument)

    def _strided_array_section_expression(self, argument: ArgumentTransferPlan) -> str:
        """Render one positive-stride section from completed layout roles."""
        array = argument.array
        if array is None or array.rank is None:
            raise ValueError(f"Strided array argument {argument.owner_path!r} requires a concrete rank")
        name = argument.entrypoint.parameter_name
        pointer_name = self._array_pointer_name(argument)
        slices = (f"1:{name}_upper_bound_{axis} + 1:{name}_stride_{axis}" for axis in range(array.rank))
        return f"{pointer_name}({', '.join(slices)})"

    def _array_element_fortran_type(self, argument: ArgumentTransferPlan) -> str:
        """Return the completed primitive or fixed-width character element type."""
        array = argument.array
        if argument.datatype_family is DatatypeFamily.STRING:
            if array is None or array.itemsize is None or array.itemsize <= 0:
                raise ValueError(f"Character array {argument.owner_path!r} has no fixed itemsize")
            return f"character(kind=c_char, len={array.itemsize})"
        return PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name).fortran_spelling

    def _array_dimension_attribute(self, rank: int) -> str:
        """Spell one explicit-rank deferred-shape pointer attribute."""
        return f"dimension({', '.join(':' for _ in range(rank))})"

    # String address bridge storage.
    def _string_address_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare fixed helper-local character storage for address boundaries."""
        declarations = []
        for argument in self._string_address_arguments(plan):
            name = argument.entrypoint.parameter_name
            length = self._string_address_length(argument)
            declarations.extend(
                (
                    FortranDeclaration(
                        f"{name}_bytes",
                        "character(kind=c_char)",
                        ("pointer", "dimension(:)"),
                    ),
                    FortranDeclaration(name, f"character(kind=c_char, len={length})"),
                )
            )
        return tuple(declarations)

    def _string_address_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Associate fixed-width bytes and materialize native character locals."""
        nodes = []
        for argument in self._string_address_arguments(plan):
            name = argument.entrypoint.parameter_name
            length = self._string_address_length(argument)
            nodes.extend(
                (
                    FortranCall(
                        "c_f_pointer",
                        (
                            CodeExpression(f"bound_{name}"),
                            CodeExpression(f"{name}_bytes"),
                            CodeExpression(f"[{length}]"),
                        ),
                    ),
                    FortranAssignment(name, CodeExpression(f"transfer({name}_bytes, {name})")),
                )
            )
        return tuple(nodes)

    def _string_address_finalizers(self, plan: FunctionPlan) -> tuple[FortranAssignment, ...]:
        """Copy every mutated fixed character byte back to caller storage."""
        nodes = []
        for argument in self._string_address_arguments(plan):
            if not argument.mutates_native:
                continue
            name = argument.entrypoint.parameter_name
            length = self._string_address_length(argument)
            nodes.append(
                FortranAssignment(
                    f"{name}_bytes(1:{length})",
                    CodeExpression(f"transfer({name}, {name}_bytes(1:{length}))"),
                )
            )
        return tuple(nodes)

    def _string_address_arguments(self, plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return address-shaped strings selected by completed plan facts."""
        return tuple(
            argument
            for argument in plan.arguments
            if argument.object_kind is ObjectKind.STRING
            and argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
            and argument.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
        )

    def _string_address_length(self, plan: ArgumentTransferPlan) -> int:
        """Return the fixed extent already completed in the shared plan."""
        if plan.character_length is None or plan.character_length <= 0:
            raise ValueError(f"String address {plan.owner_path!r} is missing a fixed character length")
        return plan.character_length

    # String value bridge storage.
    def _string_value_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Return bridge-local character storage for string-value inputs."""
        declarations = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            name = argument.entrypoint.parameter_name
            declarations.extend(
                (
                    FortranDeclaration(
                        f"{name}_bytes",
                        "character(kind=c_char)",
                        ("pointer", "dimension(:)"),
                    ),
                    self._string_value_declaration(argument, name),
                )
            )
            if self._retains_character_local_seed(argument):
                declarations.append(self._string_value_declaration(argument, f"{name}_seed"))
        return tuple(declarations)

    @staticmethod
    def _character_local(plan: ArgumentTransferPlan) -> CharacterLocalPlan:
        """Return the completed adapter-local character storage for one input."""
        local = plan.bridge.character_local
        if local is None:
            raise ValueError(f"String input {plan.owner_path!r} is missing completed character-local policy")
        return local

    @classmethod
    def _retains_character_local_seed(cls, plan: ArgumentTransferPlan) -> bool:
        """Report whether the adapter keeps a second pointer to the storage it allocated.

        A pointer dummy the native procedure may reassociate makes the dummy an
        unreliable handle on that allocation, so the completed release action
        asks for a seed pointer to compare against afterwards.
        """
        return cls._character_local(plan).release is CharacterLocalRelease.DEALLOCATE_IF_RETAINED

    @classmethod
    def _string_value_declaration(cls, plan: ArgumentTransferPlan, name: str) -> FortranDeclaration:
        """Declare the native character local selected by completed bridge policy.

        The C ABI is a byte buffer and a length whatever the dummy declares, so
        only the local changes: an ``allocatable`` or ``pointer`` dummy needs a
        local carrying the same attribute, and a deferred-length dummy is not
        interoperable at all, so no ``bind(C)`` interface could declare it.

        A descriptor local also takes its fixed length from the plan rather than
        from the runtime length beside the buffer.  Neither length is deferred
        there, so the standard requires the actual and the dummy to agree, and
        the declared length is what lets the compiler check that they do.
        """
        local = cls._character_local(plan)
        if local.deferred_length:
            length = ":"
        elif local.descriptor_kind is not None and plan.character_length is not None:
            length = str(plan.character_length)
        else:
            length = f"{plan.entrypoint.parameter_name}_length"
        spelling = f"character(kind=c_char, len={length})"
        if local.descriptor_kind is None:
            return FortranDeclaration(name, spelling)
        return FortranDeclaration(name, spelling, (local.descriptor_kind.value,))

    def _string_value_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Associate and copy C bytes only for completed representation-copy inputs."""
        nodes = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            if argument.entrypoint.optional_mode is not OptionalMode.REQUIRED:
                continue
            if argument.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
                raise ValueError(f"String input {argument.owner_path!r} is missing representation-copy policy")
            nodes.extend(self._string_value_initializer_nodes(argument))
        return tuple(nodes)

    def _string_value_initializer_nodes(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranCall | FortranAssignment | FortranAllocate | FortranPointerAssignment, ...]:
        """Associate and materialize one present string payload."""
        name = plan.entrypoint.parameter_name
        local = self._character_local(plan)
        extent = f"{name}_length + 1" if plan.bridge.codegen_action is CodegenAction.COPY_IN_OUT else f"{name}_length"
        source = (
            f"{name}_bytes(1:{name}_length)"
            if plan.bridge.codegen_action is CodegenAction.COPY_IN_OUT
            else f"{name}_bytes"
        )
        # A deferred-length local has no length until it is allocated, so its
        # mold spells the width instead of naming storage that does not exist.
        mold = f"repeat(' ', {name}_length)" if local.deferred_length else name
        return (
            FortranCall(
                "c_f_pointer",
                (
                    CodeExpression(f"bound_{name}"),
                    CodeExpression(f"{name}_bytes"),
                    CodeExpression(f"[{extent}]"),
                ),
            ),
            *self._character_local_allocation_nodes(plan, name),
            FortranAssignment(name, CodeExpression(f"transfer({source}, {mold})")),
            *self._character_local_seed_nodes(plan, name),
        )

    def _character_local_allocation_nodes(
        self,
        plan: ArgumentTransferPlan,
        name: str,
    ) -> tuple[FortranAllocate, ...]:
        """Allocate the adapter local that intrinsic assignment cannot establish.

        Assignment allocates a deferred-length allocatable on its own, so only a
        pointer local, and a fixed-length allocatable whose mold would otherwise
        be unallocated storage, need an explicit allocation first.
        """
        local = self._character_local(plan)
        if local.descriptor_kind is None:
            return ()
        if local.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE and local.deferred_length:
            return ()
        if local.deferred_length:
            return (FortranAllocate(f"character(kind=c_char, len={name}_length) :: {name}"),)
        return (FortranAllocate(name),)

    def _character_local_seed_nodes(
        self,
        plan: ArgumentTransferPlan,
        name: str,
    ) -> tuple[FortranPointerAssignment, ...]:
        """Record the allocation a reassociable pointer local started out holding."""
        if not self._retains_character_local_seed(plan):
            return ()
        return (FortranPointerAssignment(f"{name}_seed", CodeExpression(name)),)

    def _string_value_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Dispatch completed post-call string copyback actions."""
        nodes = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            action = argument.bridge.codegen_action
            if action is CodegenAction.CALL_LOCAL_INPUT:
                continue
            if action is CodegenAction.COPY_IN_OUT:
                copyback = self._lower_argument_string_copyback(argument)
                if argument.entrypoint.optional_mode is OptionalMode.NULLABLE_VALUE:
                    name = argument.entrypoint.parameter_name
                    nodes.append(FortranIf(CodeExpression(f"c_associated(bound_{name})"), body=copyback))
                else:
                    nodes.extend(copyback)
                continue
            raise ValueError(f"Unsupported Fortran string finalizer for {argument.owner_path!r}: {action!r}")
        return tuple(nodes)

    def _character_local_initializers(self, plan: FunctionPlan) -> tuple[FortranPointerAssignment, ...]:
        """Disassociate pointer character locals before any presence branch runs.

        An absent optional argument never reaches the allocation, so without
        this the local's association status stays undefined and both the
        copy-out test and the release test read it.
        """
        nodes = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            local = self._character_local(argument)
            if local.descriptor_kind is not NativeArrayDescriptorKind.POINTER:
                continue
            name = argument.entrypoint.parameter_name
            nodes.append(FortranPointerAssignment(name, CodeExpression("null()")))
            if self._retains_character_local_seed(argument):
                nodes.append(FortranPointerAssignment(f"{name}_seed", CodeExpression("null()")))
        return tuple(nodes)

    def _character_local_release_finalizers(self, plan: FunctionPlan) -> tuple[FortranIf | FortranDeallocate, ...]:
        """Free the character locals the adapter allocated, after every value is read.

        Only a pointer local is adapter-owned storage; an allocatable local is
        released by the compiler.  A read-only pointer dummy cannot change its
        association, so its allocation is always the one still in hand.  An
        update dummy may have been reassociated or deallocated by the native
        procedure, so the adapter frees its allocation only while the dummy
        still identifies it, leaving native-owned storage untouched.
        """
        nodes: list[FortranIf | FortranDeallocate] = []
        for argument in plan.arguments:
            if argument.entrypoint.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            release = self._character_local(argument).release
            if release is CharacterLocalRelease.NONE:
                continue
            name = argument.entrypoint.parameter_name
            # An absent optional argument skipped the allocation entirely, so
            # every release is guarded by what the local actually holds.
            condition = (
                f"associated({name})"
                if release is CharacterLocalRelease.DEALLOCATE
                else f"associated({name}, {name}_seed)"
            )
            nodes.append(FortranIf(CodeExpression(condition), body=(FortranDeallocate(name),)))
        return tuple(nodes)

    def _lower_argument_string_copyback(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranAssignment, ...]:
        """Copy one complete native character value back to binding storage."""
        name = plan.entrypoint.parameter_name
        return (
            FortranAssignment(
                f"{name}_bytes(1:{name}_length)",
                CodeExpression(f"transfer({name}, {name}_bytes(1:{name}_length))"),
            ),
            FortranAssignment(f"{name}_bytes({name}_length + 1)", CodeExpression("c_null_char")),
        )

    def _descriptor_initializers(self, plan: FunctionPlan) -> tuple[FortranPointerAssignment, ...]:
        """Initialize pointer descriptors required by ordinary nullable descriptor arguments before call preparation."""
        return tuple(
            FortranPointerAssignment(
                f"{argument.entrypoint.parameter_name}_descriptor",
                CodeExpression("null()"),
            )
            for argument in plan.arguments
            if (
                argument.entrypoint.optional_mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}
                and argument.entrypoint.handoff_mode is not ArgumentHandoffMode.NATIVE_DESCRIPTOR
                and argument.projected_call_slot.value_kind == "pointer"
                and argument.object_kind is not ObjectKind.DERIVED_TYPE
            )
        )

    def _required_descriptor_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranPointerAssignment | FortranCall | FortranIf, ...]:
        """Prepare descriptor storage for required nullable descriptor values."""
        return tuple(
            node
            for argument in plan.arguments
            if argument.entrypoint.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR and argument.derived_call is None
            for node in self._present_preparation(argument)
        )

    def _required_descriptor_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranIf, ...]:
        """Copy final descriptor values and states into binding-owned output slots."""
        return tuple(
            self._required_descriptor_finalizer(argument)
            for argument in plan.arguments
            if argument.entrypoint.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR
            and argument.entrypoint.descriptor_output_role is not None
            and argument.derived_call is None
        )

    def _required_descriptor_finalizer(self, argument: ArgumentTransferPlan) -> FortranIf:
        """Lower one planned required-descriptor copy-out ABI."""
        name = argument.entrypoint.parameter_name
        if self._uses_allocatable_holder(argument):
            state = (FortranAssignment(f"bound_{name}_output", CodeExpression(f"c_loc({name}_holder)")),)
            return FortranIf(
                CodeExpression(f"allocated({name}_holder%value)"),
                body=(
                    FortranAssignment(f"bound_{name}_output_present", CodeExpression("1")),
                    *state,
                ),
                else_body=(
                    FortranAssignment(f"bound_{name}_output_present", CodeExpression("0")),
                    *state,
                ),
            )
        inquiry = "associated" if argument.projected_call_slot.value_kind == "pointer" else "allocated"
        return FortranIf(
            CodeExpression(f"{inquiry}({name}_descriptor)"),
            body=(
                FortranAssignment(f"bound_{name}_output_present", CodeExpression("1")),
                FortranCall(
                    "c_f_pointer",
                    (CodeExpression(f"bound_{name}_output"), CodeExpression(f"{name}_output")),
                ),
                FortranAssignment(f"{name}_output", CodeExpression(f"{name}_descriptor")),
            ),
            else_body=(FortranAssignment(f"bound_{name}_output_present", CodeExpression("0")),),
        )

    def _native_output_parameters_for_result(self, result: NativeEntrypointResultPlan) -> tuple[FortranParameter, ...]:
        """Lower one hidden result's completed entrypoint transport."""
        if result.scalar_descriptor is not None:
            return self._scalar_descriptor_output_parameters(result)
        if self._is_owned_native_array_result(result):
            return self._owned_native_array_output_parameters(result)
        name = result.parameter_name
        if name is None:
            raise ValueError(f"Hidden result {result.owner_path!r} has no entrypoint parameter name")
        if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return (FortranParameter(name, "type(c_ptr)"),)
        scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name)
        return (FortranParameter(name, scalar_type.fortran_spelling),)

    def _scalar_descriptor_output_parameters(self, result: NativeEntrypointResultPlan) -> tuple[FortranParameter, ...]:
        """Lower one completed rank-zero descriptor result ABI."""
        descriptor = result.scalar_descriptor
        if descriptor is None:
            raise ValueError(f"Scalar output {result.owner_path!r} has no descriptor plan")
        name = result.parameter_name
        if name is None:
            raise ValueError(f"Scalar output {result.owner_path!r} has no entrypoint parameter name")
        parameters = [
            FortranParameter(name, "type(c_ptr)"),
            FortranParameter(f"{name}_present", "integer(c_int)"),
        ]
        if descriptor.runtime_length:
            parameters.append(FortranParameter(f"{name}_length", "integer(c_int64_t)"))
        return tuple(parameters)

    def _owned_native_array_output_parameters(self, result: NativeEntrypointResultPlan) -> tuple[FortranParameter, ...]:
        """Lower one completed owned rank-positive descriptor result ABI."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned output {result.owner_path!r} has no descriptor rank")
        name = result.parameter_name
        if name is None:
            raise ValueError(f"Owned output {result.owner_path!r} has no entrypoint parameter name")
        if self._is_owned_deferred_character_result(result):
            return (
                FortranParameter(name, "type(c_ptr)"),
                FortranParameter(f"{name}_itemsize", "integer(c_int64_t)"),
                *(FortranParameter(f"{name}_extent_{axis}", "integer(c_int64_t)") for axis in range(handle.array.rank)),
            )
        return (
            FortranParameter(
                name,
                self._array_result_element_type(result),
                (
                    self._owned_native_array_descriptor_attribute(handle),
                    self._array_dimension_attribute(handle.array.rank),
                    "intent(out)",
                ),
            ),
        )

    def _native_output_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Dispatch helper-local output storage from completed bridge data actions."""
        declarations = []
        for slot in self._adapter_slots(plan):
            if slot.source_kind != "result":
                continue
            if slot.scalar_descriptor is not None:
                declarations.extend(self._scalar_descriptor_output_declarations(slot))
                continue
            if self._is_owned_native_array_slot(slot):
                handle = slot.native_array_handle
                if handle is None or handle.array.rank is None:
                    raise ValueError(f"Owned output {slot.owner_path!r} has no descriptor rank")
                declarations.append(
                    FortranDeclaration(
                        f"{slot.native_name.lower()}_value",
                        self._array_result_element_type(slot),
                        (
                            self._owned_native_array_descriptor_attribute(handle),
                            self._array_dimension_attribute(handle.array.rank),
                        ),
                    )
                )
                if self._is_owned_deferred_character_slot(slot):
                    declarations.append(
                        FortranDeclaration(
                            f"{slot.native_name.lower()}_copy",
                            "character(kind=c_char)",
                            ("pointer", "dimension(:)"),
                        )
                    )
                continue
            if slot.adapter.bridge_data_action is BridgeDataAction.DIRECT_TRANSFER:
                continue
            if slot.adapter.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION:
                declarations.extend(self._representation_copy_output_declarations(plan, slot))
                continue
            raise ValueError(
                f"Unsupported native-output bridge data action for {slot.owner_path!r}: "
                f"{slot.adapter.bridge_data_action!r}"
            )
        declarations.extend(self._argument_update_declarations(plan))
        return tuple(declarations)

    def _argument_update_results(
        self,
        plan: FunctionPlan,
    ) -> tuple[tuple[ResultPlan, ArgumentTransferPlan], ...]:
        """Pair each argument-update result with the input storage it returns.

        A character descriptor update has no result call slot: the native
        procedure receives the adapter's call-local input and may reallocate or
        reassociate it, so the copied-out value is read from that same local.
        """
        arguments = {argument.owner_path: argument for argument in plan.arguments}
        pairs = []
        for result in sorted(plan.results, key=lambda item: item.result_position):
            if not result.updates_argument:
                continue
            argument = arguments.get(result.owner_path)
            if argument is None:
                raise ValueError(f"Argument update {result.owner_path!r} has no completed input transfer")
            if result.scalar_descriptor is None:
                raise ValueError(f"Argument update {result.owner_path!r} has no completed descriptor result")
            pairs.append((result, argument))
        return tuple(pairs)

    @staticmethod
    def _argument_update_names(result: ResultPlan, argument: ArgumentTransferPlan) -> tuple[str, str]:
        """Return the planned output-group name and the input local it reads."""
        name = result.entrypoint.parameter_name
        if name is None:
            raise ValueError(f"Argument update {result.owner_path!r} has no entrypoint parameter name")
        return name, argument.entrypoint.parameter_name

    def _argument_update_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare detached-copy storage for every completed argument update."""
        declarations = []
        for result, argument in self._argument_update_results(plan):
            name, value_name = self._argument_update_names(result, argument)
            declarations.extend(self._scalar_descriptor_copy_declarations(result, name, value_name=value_name))
        return tuple(declarations)

    def _direct_result_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare backend-local storage selected by direct-result lowering."""
        result = self._direct_result(plan)
        if result is None:
            return ()
        if result.scalar_descriptor is not None:
            return self._scalar_descriptor_copy_declarations(result, "result")
        if self._is_owned_native_array_result(result):
            return self._owned_direct_result_declarations(plan, result)
        return self._ordinary_direct_result_declarations(plan, result)

    def _owned_direct_result_declarations(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare storage for one completed owned direct-result plan."""
        if self._uses_owned_direct_array_result_collector(plan):
            return ()
        return self._owned_array_result_declarations(result)

    def _ordinary_direct_result_declarations(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Dispatch ordinary direct-result declarations by completed object kind."""
        match result.object_kind:
            case ObjectKind.NUMPY_ARRAY:
                return self._direct_array_result_declarations(plan, result)
            case ObjectKind.DERIVED_TYPE:
                return self._derived_result_declarations(result)
            case ObjectKind.SCALAR:
                return self._direct_scalar_result_declarations(result)
            case ObjectKind.STRING:
                return self._direct_string_result_declarations(result)
            case _:
                return ()

    @staticmethod
    def _direct_scalar_result_declarations(result: ResultPlan) -> tuple[FortranDeclaration, ...]:
        """Declare storage selected by a completed scalar direct-result ABI."""
        match result.entrypoint.direct_result_abi:
            case DirectResultABI.LOGICAL_LOW_BIT_INT8:
                return (FortranDeclaration("c_result", "logical(c_bool)"),)
            case DirectResultABI.NATIVE_SCALAR:
                return ()
            case _:
                raise ValueError(f"Scalar result {result.owner_path!r} has no completed direct-result ABI")

    def _direct_string_result_declarations(self, result: ResultPlan) -> tuple[FortranDeclaration, ...]:
        """Declare fixed-string copy storage for one direct result."""
        length = self._string_result_length(result)
        return (
            FortranDeclaration("result_value", f"character(kind=c_char, len={length})"),
            FortranDeclaration(
                "result_copy",
                "character(kind=c_char)",
                ("pointer", "dimension(:)"),
            ),
        )

    def _owned_array_result_declarations(self, result: ResultPlan) -> tuple[FortranDeclaration, ...]:
        """Declare persistent standard-descriptor result storage."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor rank")
        declarations = [
            FortranDeclaration(
                "result_value",
                self._array_result_element_type(result),
                (
                    self._owned_native_array_descriptor_attribute(handle),
                    self._array_dimension_attribute(handle.array.rank),
                ),
            ),
        ]
        if self._is_owned_deferred_character_result(result):
            declarations.append(
                FortranDeclaration(
                    "result_copy",
                    "character(kind=c_char)",
                    ("pointer", "dimension(:)"),
                )
            )
        return tuple(declarations)

    def _derived_result_declarations(self, result: ResultPlan) -> tuple[FortranDeclaration, ...]:
        """Declare persistent direct or typed-holder derived result storage."""
        if result.derived.storage in {
            DerivedObjectStorage.ALLOCATABLE_HOLDER,
            DerivedObjectStorage.POINTER_HOLDER,
        }:
            holder_type = (
                self._allocatable_holder_type_name(result.derived.backend_symbol)
                if result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER
                else self._pointer_holder_type_name(result.derived.backend_symbol)
            )
            native_attribute = (
                "allocatable" if result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER else "pointer"
            )
            return (
                FortranDeclaration(
                    "result_value",
                    f"type({holder_type})",
                    ("pointer",),
                ),
                FortranDeclaration(
                    "result_native",
                    f"type({self._derived_native_alias(result.derived.backend_symbol)})",
                    (native_attribute,),
                ),
            )
        return (
            FortranDeclaration(
                "result_value",
                f"type({self._derived_native_alias(result.derived.backend_symbol)})",
                ("pointer",),
            ),
        )

    def _derived_result_allocation_declarations(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare one allocation status for persistent derived result storage."""
        if not self._derived_result_storage_names(plan):
            return ()
        return (FortranDeclaration("prik_allocation_status", "integer(c_int)"),)

    def _derived_result_storage_names(self, plan: FunctionPlan) -> tuple[str, ...]:
        """Return every bridge-local persistent derived result allocation."""
        names = []
        direct = self._direct_result(plan)
        if direct is not None and direct.object_kind is ObjectKind.DERIVED_TYPE:
            names.append("result_value")
        names.extend(
            f"{slot.native_name.lower()}_value"
            for slot in self._adapter_slots(plan)
            if slot.source_kind == "result" and slot.object_kind is ObjectKind.DERIVED_TYPE
        )
        return tuple(names)

    def _derived_result_execution(
        self,
        plan: FunctionPlan,
        direct_result_name: str | None,
        success_body: tuple,
    ) -> tuple:
        """Allocate all derived results or return null outputs without invoking native code."""
        storage = self._derived_result_storage_names(plan)
        if not storage:
            return success_body
        null_outputs = [
            FortranAssignment(slot.native_name.lower(), CodeExpression("c_null_ptr"))
            for slot in self._adapter_slots(plan)
            if slot.source_kind == "result" and slot.object_kind is ObjectKind.DERIVED_TYPE
        ]
        direct = self._direct_result(plan)
        if direct is not None and direct.object_kind is ObjectKind.DERIVED_TYPE:
            if direct_result_name is None:
                raise ValueError(f"Derived result {direct.owner_path!r} has no bridge result name")
            null_outputs.insert(0, FortranAssignment(direct_result_name, CodeExpression("c_null_ptr")))
        return (*null_outputs, *self._derived_allocation_tree(storage, success_body, ()))

    def _derived_allocation_tree(
        self,
        storage: tuple[str, ...],
        success_body: tuple,
        allocated: tuple[str, ...],
    ) -> tuple:
        """Nest checked allocations and release earlier storage if a later one fails."""
        if not storage:
            return success_body
        current, *remaining = storage
        return (
            FortranAllocate(current, status="prik_allocation_status"),
            FortranIf(
                CodeExpression("prik_allocation_status == 0"),
                body=self._derived_allocation_tree(tuple(remaining), success_body, (*allocated, current)),
                else_body=tuple(FortranDeallocate(name) for name in reversed(allocated)),
            ),
        )

    def _scalar_descriptor_output_declarations(
        self,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare native and detached-copy storage for one hidden descriptor scalar."""
        return self._scalar_descriptor_copy_declarations(slot, slot.native_name.lower())

    def _scalar_descriptor_copy_declarations(
        self,
        result: ResultPlan | NativeEntrypointProjectedSlotPlan,
        name: str,
        *,
        value_name: str | None = None,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare helper-local storage selected by a scalar descriptor plan.

        ``value_name`` names storage another facet already declares, as an
        argument update does with its call-local input; only the detached copy
        pointer is then declared here.
        """
        descriptor = result.scalar_descriptor
        if descriptor is None:
            return ()
        attribute = "allocatable" if descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "pointer"
        copy_name = f"{name}_copy"
        if result.object_kind is ObjectKind.STRING:
            copy = FortranDeclaration(copy_name, "character(kind=c_char)", ("pointer", "dimension(:)"))
            if value_name is not None:
                return (copy,)
            # An allocatable or pointer dummy accepts a deferred-length actual
            # only when it declares one itself, so the local mirrors the
            # completed length instead of always deferring it.
            length = ":" if result.character_length is None else str(result.character_length)
            return (
                FortranDeclaration(f"{name}_value", f"character(kind=c_char, len={length})", (attribute,)),
                copy,
            )
        scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name)
        copy = FortranDeclaration(copy_name, scalar_type.fortran_spelling, ("pointer",))
        if value_name is not None:
            return (copy,)
        return (
            FortranDeclaration(f"{name}_value", scalar_type.fortran_spelling, (attribute,)),
            copy,
        )

    # Ordinary-array result storage.
    def _direct_array_result_declarations(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare typed native and contiguous-copy storage for one array result."""
        shape = self._array_result_shape(plan, result)
        element_type = self._array_result_element_type(result)
        if self._is_scalar_storage_array(result.array):
            return (
                FortranDeclaration("result_value", element_type),
                FortranDeclaration("result_copy", element_type, ("pointer",)),
            )
        copy_type = "character(kind=c_char)" if result.datatype_family is DatatypeFamily.STRING else element_type
        if "bridge" in result.array.extent_evaluation:
            return (
                FortranDeclaration(
                    "result_value",
                    element_type,
                    ("allocatable", self._array_dimension_attribute(result.array.rank)),
                ),
                FortranDeclaration("result_copy", copy_type, ("pointer", "dimension(:)")),
            )
        return (
            FortranDeclaration("result_value", element_type, (f"dimension({', '.join(shape)})",)),
            FortranDeclaration("result_copy", copy_type, ("pointer", "dimension(:)")),
        )

    def _direct_array_result_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAllocate, ...]:
        """Allocate a native-dependent result from its already evaluated ABI extents."""
        result = self._direct_result(plan)
        if (
            result is None
            or result.object_kind is not ObjectKind.NUMPY_ARRAY
            or result.array is None
            or "bridge" not in result.array.extent_evaluation
            or self._is_scalar_storage_array(result.array)
        ):
            return ()
        shape = list(self._array_result_shape(plan, result))
        for axis, evaluation in enumerate(result.array.extent_evaluation):
            if evaluation == "bridge":
                shape[axis] = self._declaration_extent_result_name(result, axis)
        return (FortranAllocate(f"result_value({', '.join(shape)})"),)

    def _direct_result_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf, ...]:
        """Finalize one direct result into its selected bridge representation."""
        result = self._direct_result(plan)
        if result is None:
            return ()
        if result.scalar_descriptor is not None:
            return self._scalar_descriptor_copy_nodes(result, "result")
        if self._is_owned_native_array_result(result):
            return self._owned_direct_native_array_result_finalizers(plan, result)
        return self._ordinary_direct_result_finalizers(plan, result)

    def _ordinary_direct_result_finalizers(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf, ...]:
        """Dispatch direct-result finalization by completed object kind."""
        match result.object_kind:
            case ObjectKind.NUMPY_ARRAY:
                return self._direct_array_result_finalizers(result)
            case ObjectKind.DERIVED_TYPE:
                return self._derived_direct_result_finalizers(result)
            case ObjectKind.SCALAR:
                return self._direct_scalar_result_finalizers(result)
            case ObjectKind.STRING:
                return self._direct_string_result_finalizers(result)
            case _:
                return ()

    def _direct_array_result_finalizers(
        self,
        result: ResultPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf, ...]:
        """Copy one ordinary array result through its completed shape plan."""
        if result.array is None:
            raise ValueError(f"Array result {result.owner_path!r} has no shape plan")
        return self._fixed_array_copy_nodes(
            result.array.native_order,
            result.array.rank,
            itemsize=self._array_result_itemsize(result),
            target_name="result",
            value_name="result_value",
            copy_name="result_copy",
        )

    @staticmethod
    def _direct_scalar_result_finalizers(
        result: ResultPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf, ...]:
        """Finalize one scalar through its completed direct-result ABI."""
        match result.entrypoint.direct_result_abi:
            case DirectResultABI.LOGICAL_LOW_BIT_INT8:
                return (
                    FortranAssignment(
                        "result",
                        CodeExpression("iand(transfer(c_result, 0_c_int8_t), 1_c_int8_t)"),
                    ),
                )
            case DirectResultABI.NATIVE_SCALAR:
                return ()
            case _:
                raise ValueError(f"Scalar result {result.owner_path!r} has no completed direct-result ABI")

    def _direct_string_result_finalizers(
        self,
        result: ResultPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf, ...]:
        """Copy one fixed-string direct result into its bridge representation."""
        return self._fixed_string_copy_nodes(
            length=self._string_result_length(result),
            target_name="result",
            value_name="result_value",
            copy_name="result_copy",
        )

    def _owned_direct_native_array_result_finalizers(
        self,
        plan: FunctionPlan,
        result: ResultPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf | FortranPointerAssignment, ...]:
        """Finalize one owned result through its completed descriptor kind."""
        if self._uses_owned_direct_array_result_collector(plan):
            return ()
        if self._is_owned_deferred_character_result(result):
            return self._owned_deferred_character_copy_nodes(result, "result", "result_value", "result_copy")
        handle = result.native_array_handle
        if handle is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor policy")
        if handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
            return (FortranPointerAssignment("result", CodeExpression("result_value")),)
        return (
            FortranIf(
                CodeExpression("allocated(result_value)"),
                body=(
                    FortranCall(
                        "move_alloc",
                        (CodeExpression("result_value"), CodeExpression("result")),
                    ),
                ),
                else_body=(
                    FortranIf(
                        CodeExpression("allocated(result)"),
                        body=(FortranDeallocate("result"),),
                    ),
                ),
            ),
        )

    def _direct_result_internal_procedures(self, plan: FunctionPlan) -> tuple[FortranFunction, ...]:
        """Return helper procedures needed by direct-result lowering."""
        result = self._direct_result(plan)
        if result is None:
            return ()
        if self._uses_owned_direct_array_result_collector(plan):
            return (self._owned_direct_array_result_collector(result),)
        if self._uses_allocatable_character_result_collector(result):
            return (self._allocatable_character_result_collector(result),)
        return ()

    @classmethod
    def _uses_allocatable_character_result_collector(cls, result: ResultPlan | None) -> bool:
        """Return whether a direct character result travels through the move helper."""
        descriptor = result.scalar_descriptor if result is not None else None
        return bool(
            result is not None
            and descriptor is not None
            and result.object_kind is ObjectKind.STRING
            and descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
        )

    @staticmethod
    def _allocatable_character_result_collector_name() -> str:
        """Return the fixed internal helper name for collecting allocatable character results."""
        return "prik_collect_allocatable_character_result"

    @classmethod
    def _allocatable_character_result_collector(cls, result: ResultPlan) -> FortranFunction:
        """Move an allocatable character function result without assigning it directly.

        Intrinsic assignment reads the result, which is not permitted when the
        function left it unallocated.  Receiving it through an allocatable dummy
        makes allocation a testable fact, so an unallocated result becomes the
        Python ``None`` the descriptor contract already describes rather than a
        read of storage that was never established.
        """
        length = ":" if result.character_length is None else str(result.character_length)
        element_type = f"character(kind=c_char, len={length})"
        return FortranFunction(
            name=cls._allocatable_character_result_collector_name(),
            parameters=(
                FortranParameter("value", element_type, ("allocatable",)),
                FortranParameter("result", element_type, ("allocatable", "intent(out)")),
            ),
            body=(
                FortranIf(
                    CodeExpression("allocated(value)"),
                    body=(
                        FortranCall(
                            "move_alloc",
                            (CodeExpression("value"), CodeExpression("result")),
                        ),
                    ),
                ),
            ),
            is_subroutine=True,
        )

    def _owned_direct_array_result_collector(self, result: ResultPlan) -> FortranFunction:
        """Move a GNU allocatable function result without the crashing assignment path."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned result {result.owner_path!r} has no descriptor rank")
        element_type = self._array_result_element_type(result)
        dimension = self._array_dimension_attribute(handle.array.rank)
        return FortranFunction(
            name=self._owned_direct_array_result_collector_name(),
            parameters=(
                FortranParameter("value", element_type, ("allocatable", dimension)),
                FortranParameter("result", element_type, ("allocatable", dimension, "intent(out)")),
            ),
            body=(
                FortranIf(
                    CodeExpression("allocated(value)"),
                    body=(
                        FortranCall(
                            "move_alloc",
                            (CodeExpression("value"), CodeExpression("result")),
                        ),
                    ),
                    else_body=(
                        FortranIf(
                            CodeExpression("allocated(result)"),
                            body=(FortranDeallocate("result"),),
                        ),
                    ),
                ),
            ),
            is_subroutine=True,
        )

    @staticmethod
    def _derived_direct_result_finalizers(
        result: ResultPlan,
    ) -> tuple[FortranAssignment | FortranCall | FortranIf, ...]:
        """Build direct-derived result transfer nodes from the completed holder storage category."""
        if result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER:
            return (
                FortranCall(
                    "move_alloc",
                    (CodeExpression("result_native"), CodeExpression("result_value%value")),
                ),
                FortranAssignment("result", CodeExpression("c_loc(result_value)")),
            )
        if result.derived.storage is DerivedObjectStorage.POINTER_HOLDER:
            return (
                FortranIf(
                    CodeExpression("associated(result_native)"),
                    body=(FortranPointerAssignment("result_value%value", CodeExpression("result_native")),),
                    else_body=(FortranNullify("result_value%value"),),
                ),
                FortranAssignment("result", CodeExpression("c_loc(result_value)")),
            )
        return (FortranAssignment("result", CodeExpression("c_loc(result_value)")),)

    def _representation_copy_output_declarations(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare storage only for one justified representation-copy output."""
        if slot.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
            if not slot.scalar_native_type:
                raise ValueError(f"Logical output {slot.owner_path!r} has no native type spelling")
            return (
                FortranDeclaration(
                    f"{slot.native_name.lower()}_value",
                    slot.scalar_native_type,
                ),
            )
        if slot.object_kind is ObjectKind.DERIVED_TYPE:
            if slot.derived is None:
                raise ValueError(f"Derived output {slot.owner_path!r} has no handoff plan")
            if slot.derived.storage in {
                DerivedObjectStorage.ALLOCATABLE_HOLDER,
                DerivedObjectStorage.POINTER_HOLDER,
            }:
                holder = (
                    self._allocatable_holder_type_name(slot.derived.backend_symbol)
                    if slot.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER
                    else self._pointer_holder_type_name(slot.derived.backend_symbol)
                )
                return (
                    FortranDeclaration(
                        f"{slot.native_name.lower()}_value",
                        f"type({holder})",
                        ("pointer",),
                    ),
                )
            return (
                FortranDeclaration(
                    f"{slot.native_name.lower()}_value",
                    f"type({self._derived_native_alias(slot.derived.backend_symbol)})",
                    ("pointer",),
                ),
            )
        if slot.object_kind is ObjectKind.NUMPY_ARRAY:
            return self._array_copy_output_declarations(plan, slot)
        if slot.object_kind is not ObjectKind.STRING:
            raise ValueError(f"Unsupported representation-copy output for {slot.owner_path!r}")
        length = self._string_output_length(slot)
        value_name = self._native_output_value_name(slot)
        return (
            FortranDeclaration(value_name, f"character(kind=c_char, len={length})"),
            FortranDeclaration(
                f"{slot.native_name.lower()}_copy",
                "character(kind=c_char)",
                ("pointer", "dimension(:)"),
            ),
        )

    def _array_copy_output_declarations(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare typed native and contiguous-copy storage for one hidden array."""
        shape = self._array_output_shape(plan, slot)
        if slot.semantic_type_name is None:
            raise ValueError(f"Missing array output datatype for {slot.owner_path!r}")
        element_type = self._array_result_element_type(slot)
        if self._is_scalar_storage_array(slot.array):
            name = slot.native_name.lower()
            return (
                FortranDeclaration(f"{name}_value", element_type),
                FortranDeclaration(f"{name}_copy", element_type, ("pointer",)),
            )
        copy_type = "character(kind=c_char)" if slot.datatype_family is DatatypeFamily.STRING else element_type
        name = slot.native_name.lower()
        return (
            FortranDeclaration(f"{name}_value", element_type, (f"dimension({', '.join(shape)})",)),
            FortranDeclaration(f"{name}_copy", copy_type, ("pointer", "dimension(:)")),
        )

    def _native_output_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Dispatch output finalization from completed bridge data actions."""
        nodes = []
        for slot in self._adapter_slots(plan):
            if slot.source_kind != "result" or slot.adapter.bridge_data_action is BridgeDataAction.DIRECT_TRANSFER:
                continue
            if slot.scalar_descriptor is not None:
                nodes.extend(self._scalar_descriptor_copy_nodes(slot, slot.native_name.lower()))
                continue
            if self._is_owned_native_array_slot(slot):
                name = slot.native_name.lower()
                if self._is_owned_deferred_character_slot(slot):
                    nodes.extend(
                        self._owned_deferred_character_copy_nodes(
                            slot,
                            name,
                            f"{name}_value",
                            f"{name}_copy",
                        )
                    )
                    continue
                if slot.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.POINTER:
                    nodes.append(FortranPointerAssignment(name, CodeExpression(f"{name}_value")))
                    continue
                nodes.append(
                    FortranIf(
                        CodeExpression(f"allocated({name}_value)"),
                        body=(FortranAssignment(name, CodeExpression(f"{name}_value")),),
                    )
                )
                continue
            if slot.adapter.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION:
                if slot.object_kind is ObjectKind.DERIVED_TYPE:
                    name = slot.native_name.lower()
                    nodes.append(FortranAssignment(name, CodeExpression(f"c_loc({name}_value)")))
                    continue
                nodes.extend(self._lower_native_output_representation_copy(plan, slot))
                continue
            raise ValueError(
                f"Unsupported native-output bridge data action for {slot.owner_path!r}: "
                f"{slot.adapter.bridge_data_action!r}"
            )
        nodes.extend(self._argument_update_finalizers(plan))
        return tuple(nodes)

    def _argument_update_finalizers(self, plan: FunctionPlan) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy every reallocated call-local input into its C-owned output group."""
        nodes: list[FortranAssignment | FortranIf] = []
        for result, argument in self._argument_update_results(plan):
            name, value_name = self._argument_update_names(result, argument)
            nodes.extend(self._scalar_descriptor_copy_nodes(result, name, value_name=value_name))
        return tuple(nodes)

    def _scalar_descriptor_copy_nodes(
        self,
        result: ResultPlan | NativeEntrypointProjectedSlotPlan,
        name: str,
        *,
        value_name: str | None = None,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy one present scalar descriptor payload into C-owned storage.

        ``value_name`` overrides the native local read after the call, which an
        argument update points at the call-local input the native procedure may
        have reallocated.
        """
        descriptor = result.scalar_descriptor
        if descriptor is None:
            return ()
        value_name = value_name or f"{name}_value"
        copy_name = f"{name}_copy"
        present = "allocated" if descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "associated"
        initializers: list[FortranAssignment | FortranIf] = [
            FortranAssignment(name, CodeExpression("c_null_ptr")),
            FortranAssignment(f"{name}_present", CodeExpression("0_c_int")),
        ]
        if descriptor.runtime_length:
            initializers.append(FortranAssignment(f"{name}_length", CodeExpression("0_c_int64_t")))
            copy_body: tuple[FortranAssignment | FortranCall | FortranIf, ...] = (
                FortranAssignment(f"{name}_length", CodeExpression(f"len({value_name}, kind=c_int64_t)")),
                FortranAssignment(
                    name,
                    CodeExpression(f"c_malloc(max(1_c_size_t, int({name}_length, c_size_t)))"),
                ),
                FortranIf(
                    CodeExpression(f"c_associated({name})"),
                    body=(
                        FortranCall(
                            "c_f_pointer",
                            (
                                CodeExpression(name),
                                CodeExpression(copy_name),
                                CodeExpression(f"[{name}_length]"),
                            ),
                        ),
                        FortranIf(
                            CodeExpression(f"{name}_length > 0_c_int64_t"),
                            body=(
                                FortranAssignment(
                                    f"{copy_name}(1:{name}_length)",
                                    CodeExpression(f"transfer({value_name}, {copy_name}(1:{name}_length))"),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        else:
            copy_body = (
                FortranAssignment(
                    name,
                    CodeExpression(f"c_malloc(max(1_c_size_t, c_sizeof({value_name})))"),
                ),
                FortranIf(
                    CodeExpression(f"c_associated({name})"),
                    body=(
                        FortranCall("c_f_pointer", (CodeExpression(name), CodeExpression(copy_name))),
                        FortranAssignment(copy_name, CodeExpression(value_name)),
                    ),
                ),
            )
        initializers.append(
            FortranIf(
                CodeExpression(f"{present}({value_name})"),
                body=(FortranAssignment(f"{name}_present", CodeExpression("1_c_int")), *copy_body),
            )
        )
        return tuple(initializers)

    # Deferred-character native-array-handle result copying.
    def _owned_deferred_character_copy_nodes(
        self,
        result: ResultPlan | NativeEntrypointProjectedSlotPlan,
        target_name: str,
        value_name: str,
        copy_name: str,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy a runtime-width character array before persistent CFI materialization."""
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Deferred character result {result.owner_path!r} has no descriptor rank")
        rank = handle.array.rank
        itemsize = f"{target_name}_itemsize"
        extents = tuple(f"{target_name}_extent_{axis}" for axis in range(rank))
        byte_count = " * ".join((itemsize, *extents))
        present_body: list[FortranAssignment | FortranCall | FortranIf] = [
            FortranAssignment(itemsize, CodeExpression(f"len({value_name}, kind=c_int64_t)")),
            *(
                FortranAssignment(
                    extent,
                    CodeExpression(f"size({value_name}, {axis + 1}, kind=c_int64_t)"),
                )
                for axis, extent in enumerate(extents)
            ),
            FortranAssignment(
                target_name,
                CodeExpression(f"c_malloc(max(1_c_size_t, int({byte_count}, c_size_t)))"),
            ),
            FortranIf(
                CodeExpression(f"c_associated({target_name})"),
                body=(
                    FortranCall(
                        "c_f_pointer",
                        (
                            CodeExpression(target_name),
                            CodeExpression(copy_name),
                            CodeExpression(f"[{byte_count}]"),
                        ),
                    ),
                    FortranIf(
                        CodeExpression(f"{byte_count} > 0_c_int64_t"),
                        body=(
                            FortranAssignment(
                                copy_name,
                                CodeExpression(f"transfer({value_name}, {copy_name}, {byte_count})"),
                            ),
                        ),
                    ),
                ),
            ),
        ]
        return (
            FortranAssignment(target_name, CodeExpression("c_null_ptr")),
            FortranAssignment(itemsize, CodeExpression("0_c_int64_t")),
            *(FortranAssignment(extent, CodeExpression("0_c_int64_t")) for extent in extents),
            FortranIf(CodeExpression(f"allocated({value_name})"), body=tuple(present_body)),
        )

    def _lower_native_output_representation_copy(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy one native output only through the explicit policy permission."""
        if slot.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
            name = slot.native_name.lower()
            return (FortranAssignment(name, CodeExpression(f"{name}_value")),)
        if slot.object_kind is ObjectKind.NUMPY_ARRAY:
            if slot.array is None:
                raise ValueError(f"Array output {slot.owner_path!r} has no shape plan")
            name = slot.native_name.lower()
            return self._fixed_array_copy_nodes(
                slot.array.native_order,
                slot.array.rank,
                itemsize=self._array_result_itemsize(slot),
                target_name=name,
                value_name=f"{name}_value",
                copy_name=f"{name}_copy",
            )
        if slot.object_kind is not ObjectKind.STRING:
            raise ValueError(f"Unsupported representation-copy output for {slot.owner_path!r}")
        name = slot.native_name.lower()
        value_name = self._native_output_value_name(slot)
        copy_name = f"{name}_copy"
        length = self._string_output_length(slot)
        return self._fixed_string_copy_nodes(
            length=length,
            target_name=name,
            value_name=value_name,
            copy_name=copy_name,
        )

    def _fixed_array_copy_nodes(
        self,
        order: str | None,
        rank: int | None,
        *,
        itemsize: int | None,
        target_name: str,
        value_name: str,
        copy_name: str,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Allocate and fill one detached contiguous ordinary-array copy."""
        if rank is None or rank < 0:
            raise ValueError(f"Array copy {value_name!r} requires a fixed positive rank")
        if rank == 0:
            return self._fixed_scalar_storage_copy_nodes(
                itemsize,
                target_name=target_name,
                value_name=value_name,
                copy_name=copy_name,
            )
        if order == "ORDER_C" and rank > 1:
            raise ValueError(f"Array copy {value_name!r} requires Fortran element order")
        if itemsize is not None:
            return self._fixed_character_array_copy_nodes(
                itemsize,
                target_name=target_name,
                value_name=value_name,
                copy_name=copy_name,
            )
        return (
            FortranAssignment(
                target_name,
                CodeExpression(
                    "c_malloc(max(1_c_size_t, "
                    f"size({value_name}, kind=c_size_t) * "
                    f"storage_size({value_name}, kind=c_size_t) / 8_c_size_t))"
                ),
            ),
            FortranIf(
                CodeExpression(f"c_associated({target_name})"),
                body=(
                    FortranCall(
                        "c_f_pointer",
                        (
                            CodeExpression(target_name),
                            CodeExpression(copy_name),
                            CodeExpression(f"[size({value_name})]"),
                        ),
                    ),
                    FortranAssignment(
                        copy_name,
                        CodeExpression(f"reshape({value_name}, [size({value_name})])"),
                    ),
                ),
            ),
        )

    def _fixed_scalar_storage_copy_nodes(
        self,
        itemsize: int | None,
        *,
        target_name: str,
        value_name: str,
        copy_name: str,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Allocate and fill one detached copy for a rank-zero NumPy result."""
        if itemsize is not None:
            raise ValueError(f"Scalar-storage copy {value_name!r} does not support character itemsize")
        return (
            FortranAssignment(
                target_name,
                CodeExpression(f"c_malloc(max(1_c_size_t, c_sizeof({value_name})))"),
            ),
            FortranIf(
                CodeExpression(f"c_associated({target_name})"),
                body=(
                    FortranCall(
                        "c_f_pointer",
                        (
                            CodeExpression(target_name),
                            CodeExpression(copy_name),
                        ),
                    ),
                    FortranAssignment(copy_name, CodeExpression(value_name)),
                ),
            ),
        )

    def _fixed_character_array_copy_nodes(
        self,
        itemsize: int,
        *,
        target_name: str,
        value_name: str,
        copy_name: str,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Allocate and copy one fixed-width character array as raw bytes."""
        if itemsize <= 0:
            raise ValueError(f"Character array copy {value_name!r} requires a fixed positive itemsize")
        byte_count = f"{itemsize} * size({value_name})"
        return (
            FortranAssignment(
                target_name,
                CodeExpression(f"c_malloc(max(1_c_size_t, {itemsize}_c_size_t * size({value_name}, kind=c_size_t)))"),
            ),
            FortranIf(
                CodeExpression(f"c_associated({target_name})"),
                body=(
                    FortranCall(
                        "c_f_pointer",
                        (
                            CodeExpression(target_name),
                            CodeExpression(copy_name),
                            CodeExpression(f"[{byte_count}]"),
                        ),
                    ),
                    FortranAssignment(
                        copy_name,
                        CodeExpression(f"transfer({value_name}, {copy_name}, {byte_count})"),
                    ),
                ),
            ),
        )

    def _array_result_element_type(
        self,
        plan: ResultPlan | NativeEntrypointResultPlan | NativeEntrypointProjectedSlotPlan,
    ) -> str:
        """Return the completed numeric, fixed, or deferred character element type."""
        if plan.datatype_family is DatatypeFamily.STRING:
            if plan.native_array_handle is not None and plan.array is not None and plan.array.itemsize is None:
                return "character(kind=c_char, len=:)"
            itemsize = self._array_result_itemsize(plan)
            if itemsize is None:
                raise ValueError(f"Character array result {plan.owner_path!r} has no itemsize")
            return f"character(kind=c_char, len={itemsize})"
        if plan.semantic_type_name is None:
            raise ValueError(f"Array result {plan.owner_path!r} has no element type")
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).fortran_spelling

    def _array_result_itemsize(
        self,
        plan: ResultPlan | NativeEntrypointProjectedSlotPlan,
    ) -> int | None:
        """Return a character-array itemsize after object-kind dispatch."""
        if plan.datatype_family is not DatatypeFamily.STRING:
            return None
        if plan.array is None or plan.array.itemsize is None or plan.array.itemsize <= 0:
            raise ValueError(f"Character array result {plan.owner_path!r} has no fixed itemsize")
        return plan.array.itemsize

    # String result storage.
    def _fixed_string_copy_nodes(
        self,
        *,
        length: int,
        target_name: str,
        value_name: str,
        copy_name: str,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Allocate and fill one justified NUL-terminated fixed string copy."""
        c_length = length + 1
        return (
            FortranAssignment(target_name, CodeExpression(f"c_malloc({c_length}_c_size_t)")),
            FortranIf(
                CodeExpression(f"c_associated({target_name})"),
                body=(
                    FortranCall(
                        "c_f_pointer",
                        (
                            CodeExpression(target_name),
                            CodeExpression(copy_name),
                            CodeExpression(f"[{c_length}]"),
                        ),
                    ),
                    FortranAssignment(
                        f"{copy_name}(1:{length})",
                        CodeExpression(f"transfer({value_name}, {copy_name}(1:{length}))"),
                    ),
                    FortranAssignment(f"{copy_name}({c_length})", CodeExpression("c_null_char")),
                ),
            ),
        )

    def _native_output_value_name(self, slot: NativeEntrypointProjectedSlotPlan) -> str:
        """Return the native-call expression selected for one output slot."""
        name = slot.native_name.lower()
        if slot.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
            return f"{name}_value"
        if slot.scalar_descriptor is not None:
            return f"{name}_value"
        if self._is_owned_native_array_slot(slot):
            return f"{name}_value"
        if (
            slot.object_kind is ObjectKind.DERIVED_TYPE
            and slot.derived is not None
            and slot.derived.storage in {DerivedObjectStorage.ALLOCATABLE_HOLDER, DerivedObjectStorage.POINTER_HOLDER}
        ):
            return f"{name}_value%value"
        return (
            f"{name}_value"
            if slot.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}
            else name
        )

    def _string_output_length(self, slot: NativeEntrypointProjectedSlotPlan) -> int:
        """Return a validated fixed length for a hidden native string output; reject absent or non-positive lengths."""
        if slot.character_length is None or slot.character_length <= 0:
            raise ValueError(f"String output {slot.owner_path!r} is missing a fixed character length")
        return slot.character_length

    def _string_result_length(self, result: ResultPlan) -> int:
        """Return a validated fixed length for a direct native string result; reject absent or non-positive lengths."""
        if result.character_length is None or result.character_length <= 0:
            raise ValueError(f"String result {result.owner_path!r} is missing a fixed character length")
        return result.character_length

    def _native_direct_result_name(self, plan: FunctionPlan, result_name: str | None) -> str | None:
        """Return the native call target selected for the procedure's completed direct result ABI."""
        result = self._direct_result(plan)
        if result is None:
            return result_name
        if result.scalar_descriptor is not None:
            return "result_value"
        if self._is_owned_native_array_result(result):
            return "result_value"
        return self._ordinary_native_direct_result_name(result, result_name)

    def _ordinary_native_direct_result_name(self, result: ResultPlan, result_name: str | None) -> str | None:
        """Select a native-call target from completed direct-result policy."""
        match result.object_kind:
            case ObjectKind.STRING | ObjectKind.NUMPY_ARRAY:
                return "result_value"
            case ObjectKind.DERIVED_TYPE:
                return self._native_derived_direct_result_name(result)
            case ObjectKind.SCALAR:
                return self._native_scalar_direct_result_name(result, result_name)
            case _:
                return result_name

    @staticmethod
    def _native_derived_direct_result_name(result: ResultPlan) -> str:
        """Select the emitted temporary required by completed derived storage."""
        if result.derived.storage in {
            DerivedObjectStorage.ALLOCATABLE_HOLDER,
            DerivedObjectStorage.POINTER_HOLDER,
        }:
            return "result_native"
        return "result_value"

    @staticmethod
    def _native_scalar_direct_result_name(result: ResultPlan, result_name: str | None) -> str | None:
        """Select the native-call target required by a completed scalar ABI."""
        match result.entrypoint.direct_result_abi:
            case DirectResultABI.LOGICAL_LOW_BIT_INT8:
                return "c_result"
            case DirectResultABI.NATIVE_SCALAR:
                return result_name
            case _:
                raise ValueError(f"Scalar result {result.owner_path!r} has no completed direct-result ABI")

    def _entrypoint_result_type(self, plan: FunctionPlan, result: ResultPlan | None = None) -> str:
        """Return the C-interoperable entrypoint result spelling selected by the completed result plan."""
        result = result or self._direct_result(plan)
        if result is None:
            raise ValueError(f"{plan.owner_path!r} native function has no result plan")
        if result.scalar_descriptor is not None:
            return "type(c_ptr)"
        if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return "type(c_ptr)"
        if result.entrypoint.direct_result_abi is DirectResultABI.LOGICAL_LOW_BIT_INT8:
            return "integer(c_int8_t)"
        if result.entrypoint.direct_result_abi is DirectResultABI.NATIVE_SCALAR:
            return PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name).fortran_spelling
        raise ValueError(f"Scalar result {result.owner_path!r} has no completed direct-result ABI")

    def _direct_result(self, plan: FunctionPlan) -> ResultPlan | None:
        """Return the sole direct result used by the Fortran function ABI."""
        return next((result for result in plan.results if result.source_kind == "direct_return"), None)

    def _owned_direct_result(self, plan: FunctionPlan) -> ResultPlan | None:
        """Return the direct result that uses persistent descriptor output storage."""
        result = self._direct_result(plan)
        return result if result is not None and self._is_owned_native_array_result(result) else None

    def _uses_owned_direct_array_result_collector(self, plan: FunctionPlan) -> bool:
        """Return whether a direct function result may be returned unallocated."""
        result = self._direct_result(plan)
        return bool(
            result is not None
            and self._is_owned_native_array_result(result)
            and not self._is_owned_deferred_character_result(result)
            and result.native_array_handle is not None
            and result.native_array_handle.result_allocation is NativeArrayResultAllocation.MAYBE_UNALLOCATED
        )

    @staticmethod
    def _owned_direct_array_result_collector_name() -> str:
        """Return the fixed internal helper name for collecting maybe-unallocated owned array results."""
        return "prik_collect_allocatable_array_result"

    @staticmethod
    def _is_owned_native_array_result(result: ResultPlan | NativeEntrypointResultPlan) -> bool:
        """Return whether one result owns persistent standard-descriptor storage."""
        handle = result.native_array_handle
        return handle is not None and handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE

    @staticmethod
    def _is_owned_native_array_slot(slot: NativeEntrypointProjectedSlotPlan) -> bool:
        """Return whether one hidden slot shares persistent descriptor storage."""
        handle = slot.native_array_handle
        return handle is not None and handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE

    @classmethod
    def _is_owned_deferred_character_result(cls, result: ResultPlan | NativeEntrypointResultPlan) -> bool:
        """Return whether owner storage needs a runtime-width copy ABI."""
        return cls._is_owned_native_array_result(result) and result.datatype_family is DatatypeFamily.STRING

    @classmethod
    def _is_owned_deferred_character_slot(cls, slot: NativeEntrypointProjectedSlotPlan) -> bool:
        """Return whether a hidden owner slot needs a runtime-width copy ABI."""
        return cls._is_owned_native_array_slot(slot) and slot.datatype_family is DatatypeFamily.STRING

    def _native_module_uses(self, plan: ModulePlan) -> tuple[FortranUse, ...]:
        """Collect exact native imports without mixing class invocation policy."""
        modules: dict[str, list[str]] = {}
        self._add_derived_module_uses(plan, modules)
        self._add_function_module_uses(plan, modules)
        self._add_declaration_callable_module_uses(plan, modules)
        self._add_variable_module_uses(plan, modules)
        return tuple(FortranUse(module, tuple(dict.fromkeys(names))) for module, names in modules.items())

    def _add_derived_module_uses(self, plan: ModulePlan, modules: dict[str, list[str]]) -> None:
        """Import each opaque native type under its completed backend alias."""
        for derived in self._derived_types(plan):
            modules.setdefault(derived.native_scope, []).append(
                f"{self._derived_native_alias(derived.backend_symbol)} => {derived.native_type_name}"
            )

    def _add_function_module_uses(self, plan: ModulePlan, modules: dict[str, list[str]]) -> None:
        """Import module procedures, excluding direct type-bound invocation."""
        for function in self._functions(plan):
            if function.bridge is None:
                continue
            if (
                function.bridge.native_module is not None
                and function.bridge.native_invocation is not NativeInvocationKind.PROCEDURE
            ):
                modules.setdefault(function.bridge.native_module, []).append(function.bridge.native_name)
                continue
            if function.bridge.native_module is not None and (
                function.class_call is None or function.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
            ):
                modules.setdefault(function.bridge.native_module, []).append(
                    f"{self._native_function_name(function)} => {function.bridge.native_name}"
                )

    def _add_declaration_callable_module_uses(
        self,
        plan: ModulePlan,
        modules: dict[str, list[str]],
    ) -> None:
        """Import module specification functions under their planned bridge names."""
        for function in self._functions(plan):
            for declaration in function.declaration_callables:
                if declaration.action is not DeclarationCallableAction.MODULE_IMPORT:
                    continue
                if declaration.native_scope is None:
                    raise ValueError(f"Module declaration callable {declaration.owner_path!r} has no module")
                modules.setdefault(declaration.native_scope, []).append(
                    f"{declaration.backend_symbol} => {declaration.native_name}"
                )

    def _add_variable_module_uses(self, plan: ModulePlan, modules: dict[str, list[str]]) -> None:
        """Import only module variables with a planned getter, setter, or proxy."""
        for variable in self._variables(plan):
            if (
                variable.entrypoint.getter_role is not None
                or variable.entrypoint.setter_role is not None
                or variable.derived is not None
            ):
                modules.setdefault(variable.bridge.native_module, []).append(
                    f"{self._native_variable_name(variable)} => {variable.bridge.native_name}"
                )

    def _derived_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return namespace-owned opaque types in stable plan order."""
        return tuple(derived for namespace in plan.namespaces for derived in namespace.derived_types)

    def _bridge_support_types(
        self,
        plan: ModulePlan,
        owner_paths: frozenset[str],
    ) -> tuple[DerivedTypePlan, ...]:
        """Join one planned Fortran support inventory to derived declarations."""
        return tuple(derived for derived in self._derived_types(plan) if derived.owner_path in owner_paths)

    @staticmethod
    def _uses_allocatable_holder(argument: ArgumentTransferPlan) -> bool:
        """Return whether the module plan requires the allocatable holder for one native derived identity."""
        return FortranBridgeGenerator._uses_holder(argument, DerivedActualAccess.ALLOCATABLE_HOLDER)

    @staticmethod
    def _uses_holder(argument: ArgumentTransferPlan, access: DerivedActualAccess) -> bool:
        """Return whether one completed derived matrix includes a holder row."""
        call = argument.derived_call
        return bool(
            call is not None
            and any(case.access is access for case in call.cases if case.action is not DerivedCallAction.INCOMPATIBLE)
        )

    # Derived-type fields and plain module-proxy members.
    def _derived_field_procedures(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Lower typed address-backed and module-path member operations."""
        return (
            *self._direct_field_procedure_entries(plan),
            *self._module_member_procedure_entries(plan),
            *self._allocatable_holder_field_procedure_entries(plan),
            *self._pointer_holder_field_procedure_entries(plan),
        )

    def _direct_field_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Return direct derived-field procedure builders in stable action order."""
        return tuple(
            procedure
            for derived in self._derived_types(plan)
            for field in derived.fields
            for procedure in self._planned_support_procedures(
                f"{derived.owner_path}.{field.name}",
                "field:direct:",
                self._direct_field_procedures(derived, field),
            )
        )

    def _module_member_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Return module-member procedure builders in stable action order."""
        return tuple(
            procedure
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            for procedure in self._planned_support_procedures(
                ".".join((variable.owner_path, *member.path)),
                "field:module:",
                self._module_member_procedures(variable, member),
            )
        )

    def _allocatable_holder_field_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Return allocatable-holder field procedure builders in stable action order."""
        return tuple(
            procedure
            for derived in self._allocatable_holder_field_types(plan)
            for field in derived.fields
            for procedure in self._planned_support_procedures(
                f"{derived.owner_path}.{field.name}",
                "field:allocatable:",
                self._allocatable_holder_field_procedures(derived, field),
            )
        )

    def _pointer_holder_field_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Return pointer-holder field procedure builders in stable action order."""
        return tuple(
            procedure
            for derived in self._pointer_holder_field_types(plan)
            for field in derived.fields
            for procedure in self._planned_support_procedures(
                f"{derived.owner_path}.{field.name}",
                "field:pointer:",
                self._pointer_holder_field_procedures(derived, field),
            )
        )

    def _planned_support_procedures(
        self,
        owner_path: str,
        role_prefix: str,
        candidates: tuple[FortranFunction, ...],
    ) -> tuple[FortranFunction, ...]:
        """Select adapter bodies in the operation order fixed by planning."""
        by_symbol = {candidate.name: candidate for candidate in candidates}
        operations = self._generated_support_procedure_entrypoints_for(owner_path, role_prefix)
        missing = tuple(operation.symbol_name for operation in operations if operation.symbol_name not in by_symbol)
        if missing:
            raise ValueError(f"No Fortran body for planned generated support procedures: {missing!r}")
        return tuple(by_symbol[operation.symbol_name] for operation in operations)

    def _allocatable_holder_field_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return the planned allocatable-holder field-support inventory."""
        return self._bridge_support_types(
            plan,
            self._bridge_allocatable_holder_field_owner_paths,
        )

    def _pointer_holder_field_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return the planned pointer-holder field-support inventory."""
        return self._bridge_support_types(
            plan,
            self._bridge_pointer_holder_field_owner_paths,
        )

    def _allocatable_holder_field_procedures(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[FortranFunction, ...]:
        """Lower scalar fields through the typed holder selected by policy."""
        if field.access is not DerivedFieldAccessMechanism.SCALAR_VALUE:
            raise ValueError(f"Unsupported allocatable-holder field for {field.owner_path!r}: {field.access.value}")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        holder_type = self._allocatable_holder_type_name(derived.backend_symbol)
        getter_name = self._allocatable_holder_field_bridge_name(derived, field, "get")
        getter = FortranFunction(
            name=getter_name,
            parameters=(FortranParameter("owner_address", "type(c_ptr)", ("value",)),),
            result_name="result",
            result_type=scalar.fortran_spelling,
            bind_name=getter_name,
            declarations=(FortranDeclaration("owner", f"type({holder_type})", ("pointer",)),),
            body=(
                self._derived_owner_association(),
                FortranAssignment("result", CodeExpression(f"owner%value%{field.native_name}")),
            ),
        )
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return (getter,)
        setter_name = self._allocatable_holder_field_bridge_name(derived, field, "set")
        setter = FortranFunction(
            name=setter_name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter("value", scalar.fortran_spelling, ("value",)),
            ),
            bind_name=setter_name,
            declarations=(FortranDeclaration("owner", f"type({holder_type})", ("pointer",)),),
            body=(
                self._derived_owner_association(),
                FortranAssignment(f"owner%value%{field.native_name}", CodeExpression("value")),
            ),
            is_subroutine=True,
        )
        return getter, setter

    def _pointer_holder_field_procedures(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[FortranFunction, ...]:
        """Lower scalar fields through a pointer holder without owning its target."""
        if field.access is not DerivedFieldAccessMechanism.SCALAR_VALUE:
            raise ValueError(f"Unsupported pointer-holder field for {field.owner_path!r}: {field.access.value}")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        holder_type = self._pointer_holder_type_name(derived.backend_symbol)
        getter_name = self._pointer_holder_field_bridge_name(derived, field, "get")
        getter = FortranFunction(
            name=getter_name,
            parameters=(FortranParameter("owner_address", "type(c_ptr)", ("value",)),),
            result_name="result",
            result_type=scalar.fortran_spelling,
            bind_name=getter_name,
            declarations=(FortranDeclaration("owner", f"type({holder_type})", ("pointer",)),),
            body=(
                self._derived_owner_association(),
                FortranAssignment("result", CodeExpression(f"owner%value%{field.native_name}")),
            ),
        )
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return (getter,)
        setter_name = self._pointer_holder_field_bridge_name(derived, field, "set")
        setter = FortranFunction(
            name=setter_name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter("value", scalar.fortran_spelling, ("value",)),
            ),
            bind_name=setter_name,
            declarations=(FortranDeclaration("owner", f"type({holder_type})", ("pointer",)),),
            body=(
                self._derived_owner_association(),
                FortranAssignment(f"owner%value%{field.native_name}", CodeExpression("value")),
            ),
            is_subroutine=True,
        )
        return getter, setter

    def _direct_field_procedures(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[FortranFunction, ...]:
        """Dispatch address-backed field access by completed object kind."""
        if field.access is DerivedFieldAccessMechanism.FIXED_STRING_COPY:
            getter = self._direct_string_field_getter(derived, field)
            setter = self._direct_string_field_setter(derived, field)
            return (getter, *((setter,) if setter is not None else ()))
        if field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE:
            return self._direct_native_handle_field_procedures(derived, field)
        if field.access is DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR:
            getter = self._direct_ordinary_array_field_getter(derived, field)
            setter = self._direct_ordinary_array_field_setter(derived, field)
        elif field.access is DerivedFieldAccessMechanism.SCALAR_VALUE:
            getter = self._direct_scalar_field_getter(derived, field)
            setter = self._direct_scalar_field_setter(derived, field)
        elif field.access is DerivedFieldAccessMechanism.NESTED_OBJECT:
            getter = self._direct_nested_field_getter(derived, field)
            setter = self._direct_nested_field_setter(derived, field)
        else:
            raise ValueError(f"Unsupported Fortran field lowering for {field.owner_path!r}")
        return (getter, *((setter,) if setter is not None else ()))

    def _module_member_procedures(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> tuple[FortranFunction, ...]:
        """Dispatch one plain-module member operation by typed field kind."""
        field = member.field
        if field.access is DerivedFieldAccessMechanism.FIXED_STRING_COPY:
            getter = self._module_string_member_getter(variable, member)
            setter = self._module_string_member_setter(variable, member)
            return (getter, *((setter,) if setter is not None else ()))
        if field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE:
            return self._module_native_handle_member_procedures(variable, member)
        if field.access is DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR:
            getter = self._module_ordinary_array_member_getter(variable, member)
            setter = self._module_ordinary_array_member_setter(variable, member)
            return (getter, *((setter,) if setter is not None else ()))
        if field.access is DerivedFieldAccessMechanism.SCALAR_VALUE:
            getter = self._module_scalar_member_getter(variable, member)
            setter = self._module_scalar_member_setter(variable, member)
            return (getter, *((setter,) if setter is not None else ()))
        if field.access is DerivedFieldAccessMechanism.NESTED_OBJECT:
            setter = self._module_nested_member_setter(variable, member)
            return (setter,) if setter is not None else ()
        raise ValueError(f"Unsupported Fortran module member lowering for {field.owner_path!r}")

    def _direct_string_field_getter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> FortranFunction:
        """Copy one fixed native character field into a C byte buffer."""
        length = self._fixed_string_field_length(field)
        name = self._derived_field_bridge_name(derived, field, "get")
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter(
                    "value",
                    "character(kind=c_char)",
                    (f"dimension({length})", "intent(out)"),
                ),
            ),
            bind_name=name,
            declarations=(self._derived_owner_declaration(derived),),
            body=(
                self._derived_owner_association(),
                FortranAssignment("value", CodeExpression(f"transfer(owner%{field.native_name}, value)")),
            ),
            is_subroutine=True,
        )

    def _direct_string_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> FortranFunction | None:
        """Copy one exact-width C byte buffer into a native character field."""
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        length = self._fixed_string_field_length(field)
        name = self._derived_field_bridge_name(derived, field, "set")
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter(
                    "value",
                    "character(kind=c_char)",
                    (f"dimension({length})", "intent(in)"),
                ),
            ),
            bind_name=name,
            declarations=(self._derived_owner_declaration(derived),),
            body=(
                self._derived_owner_association(),
                FortranAssignment(
                    f"owner%{field.native_name}",
                    CodeExpression(f"transfer(value, owner%{field.native_name})"),
                ),
            ),
            is_subroutine=True,
        )

    def _module_string_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction:
        """Copy one fixed module-member string into a C byte buffer."""
        length = self._fixed_string_field_length(member.field)
        name = self._module_member_bridge_name(variable, member, "get")
        expression = self._module_member_expression(variable, member)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter(
                    "value",
                    "character(kind=c_char)",
                    (f"dimension({length})", "intent(out)"),
                ),
            ),
            bind_name=name,
            body=(FortranAssignment("value", CodeExpression(f"transfer({expression}, value)")),),
            is_subroutine=True,
        )

    def _module_string_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction | None:
        """Copy one exact-width C byte buffer into a plain module member."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        length = self._fixed_string_field_length(field)
        name = self._module_member_bridge_name(variable, member, "set")
        expression = self._module_member_expression(variable, member)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter(
                    "value",
                    "character(kind=c_char)",
                    (f"dimension({length})", "intent(in)"),
                ),
            ),
            bind_name=name,
            body=(FortranAssignment(expression, CodeExpression(f"transfer(value, {expression})")),),
            is_subroutine=True,
        )

    @staticmethod
    def _fixed_string_field_length(field: DerivedFieldPlan) -> int:
        """Return a validated fixed length for a derived string field; reject missing lengths."""
        length = field.character_length
        if length is None or length <= 0:
            raise ValueError(f"Fixed string field {field.owner_path!r} has no positive length")
        return length

    def _direct_native_handle_field_procedures(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> tuple[FortranFunction, ...]:
        """Lower Phase 7 handle operations against an address-backed parent."""
        return self._native_handle_field_procedures(derived, field)

    def _module_native_handle_member_procedures(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> tuple[FortranFunction, ...]:
        """Lower Phase 7 handle operations against a typed module member path."""
        return self._native_handle_field_procedures((variable, member), member.field)

    def _native_handle_field_procedures(self, owner, field: DerivedFieldPlan) -> tuple[FortranFunction, ...]:
        """Lower every native-crossing operation selected by one handle plan."""
        handle = field.native_array_handle
        if handle is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no operation plan")
        procedures = []
        for operation in handle.operations:
            if operation in {
                NativeArrayOperation.NATIVE_BYTE_ORDER,
                NativeArrayOperation.ALIGNED,
                NativeArrayOperation.WRITEABLE,
                NativeArrayOperation.LAYOUT,
                NativeArrayOperation.TO_NUMPY,
                NativeArrayOperation.ARRAY_ACTUAL,
            }:
                continue
            procedures.append(self._native_handle_field_procedure(owner, field, operation))
        return tuple(procedures)

    def _native_handle_field_procedure(
        self,
        owner,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction:
        """Dispatch one typed descriptor operation without backend policy inference."""
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            return self._native_handle_field_state_procedure(owner, field, operation)
        if operation is NativeArrayOperation.ELEMENT_LENGTH:
            return self._native_handle_field_length_procedure(owner, field)
        if operation is NativeArrayOperation.SHAPE:
            return self._native_handle_field_shape_procedure(owner, field)
        if operation is NativeArrayOperation.DESCRIPTOR:
            return self._native_handle_field_descriptor_procedure(owner, field)
        if operation is NativeArrayOperation.ASSOCIATE:
            return self._native_handle_field_associate_procedure(owner, field)
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            return self._native_handle_field_resize_procedure(owner, field, operation)
        if operation is NativeArrayOperation.DEALLOCATE:
            return self._native_handle_field_deallocate_procedure(owner, field)
        if operation is NativeArrayOperation.NULLIFY:
            return self._native_handle_field_nullify_procedure(owner, field)
        raise ValueError(f"Unsupported field handle operation {operation!r} for {field.owner_path!r}")

    def _native_handle_field_state_procedure(self, owner, field, operation) -> FortranFunction:
        """Build the state inquiry for one native-array-handle field."""
        expression = self._native_handle_field_expression(owner, field)
        presence = self._native_handle_field_presence(field, expression)
        if operation is NativeArrayOperation.ALLOCATED:
            value = f"allocated({expression})"
        elif operation is NativeArrayOperation.ASSOCIATED:
            value = f"associated({expression})"
        else:
            value = f".not. ({presence}) .or. is_contiguous({expression})"
        name = self._native_handle_field_bridge_name(owner, field, operation)
        return FortranFunction(
            name=name,
            parameters=self._native_handle_field_owner_parameters(owner),
            result_name="result",
            result_type="logical(c_bool)",
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranAssignment("result", CodeExpression(value)),
            ),
        )

    def _native_handle_field_length_procedure(self, owner, field) -> FortranFunction:
        """Build the element-count inquiry for one native-array-handle field."""
        expression = self._native_handle_field_expression(owner, field)
        presence = self._native_handle_field_presence(field, expression)
        name = self._native_handle_field_bridge_name(owner, field, NativeArrayOperation.ELEMENT_LENGTH)
        return FortranFunction(
            name=name,
            parameters=self._native_handle_field_owner_parameters(owner),
            result_name="result",
            result_type="integer(c_int64_t)",
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranIf(
                    CodeExpression(presence),
                    body=(FortranAssignment("result", CodeExpression(f"len({expression}, kind=c_int64_t)")),),
                    else_body=(FortranAssignment("result", CodeExpression("0_c_int64_t")),),
                ),
            ),
        )

    def _native_handle_field_shape_procedure(self, owner, field) -> FortranFunction:
        """Build the per-axis shape inquiry for one native-array-handle field."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no shape rank")
        expression = self._native_handle_field_expression(owner, field)
        presence = self._native_handle_field_presence(field, expression)
        extents = tuple(FortranParameter(f"extent_{axis}", "integer(c_int64_t)") for axis in range(handle.array.rank))
        present = tuple(
            FortranAssignment(
                f"extent_{axis}",
                CodeExpression(f"size({expression}, {axis + 1}, kind=c_int64_t)"),
            )
            for axis in range(handle.array.rank)
        )
        absent = tuple(
            FortranAssignment(f"extent_{axis}", CodeExpression("0_c_int64_t")) for axis in range(handle.array.rank)
        )
        name = self._native_handle_field_bridge_name(owner, field, NativeArrayOperation.SHAPE)
        return FortranFunction(
            name=name,
            parameters=(*self._native_handle_field_owner_parameters(owner), *extents),
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranIf(CodeExpression(presence), body=present, else_body=absent),
            ),
            is_subroutine=True,
        )

    def _native_handle_field_descriptor_procedure(self, owner, field) -> FortranFunction:
        """Build the descriptor-export procedure for one native-array-handle field."""
        name = self._native_handle_field_bridge_name(owner, field, NativeArrayOperation.DESCRIPTOR)
        interface = self._native_handle_field_callback_interface_name(owner, field)
        return FortranFunction(
            name=name,
            parameters=(
                *self._native_handle_field_owner_parameters(owner),
                FortranParameter("callback_address", "type(c_funptr)", ("value",)),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            bind_name=name,
            declarations=(
                *self._native_handle_field_owner_declarations(owner),
                FortranDeclaration("callback", f"procedure({interface})", ("pointer",)),
            ),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranCall(
                    "c_f_procpointer",
                    (CodeExpression("callback_address"), CodeExpression("callback")),
                ),
                FortranCall(
                    "callback",
                    (
                        CodeExpression(self._native_handle_field_expression(owner, field)),
                        CodeExpression("context"),
                    ),
                ),
            ),
            is_subroutine=True,
        )

    def _native_handle_field_resize_procedure(self, owner, field, operation) -> FortranFunction:
        """Build the resize procedure selected for one native-array-handle field."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no mutation rank")
        expression = self._native_handle_field_expression(owner, field)
        extents = tuple(
            FortranParameter(f"extent_{axis}", "integer(c_int64_t)", ("value",)) for axis in range(handle.array.rank)
        )
        name = self._native_handle_field_bridge_name(owner, field, operation)
        return FortranFunction(
            name=name,
            parameters=(*self._native_handle_field_owner_parameters(owner), *extents),
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranIf(
                    CodeExpression(self._native_handle_field_presence(field, expression)),
                    body=(FortranDeallocate(expression),),
                ),
                FortranAllocate(
                    expression,
                    tuple(CodeExpression(f"extent_{axis}") for axis in range(handle.array.rank)),
                ),
            ),
            is_subroutine=True,
        )

    def _native_handle_field_associate_procedure(self, owner, field) -> FortranFunction:
        """Make one pointer field association match the source descriptor."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Pointer field {field.owner_path!r} has no association rank")
        element_type = (
            "character(kind=c_char, len=:)"
            if field.string_element
            else PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name).fortran_spelling
        )
        expression = self._native_handle_field_expression(owner, field)
        name = self._native_handle_field_bridge_name(owner, field, NativeArrayOperation.ASSOCIATE)
        return FortranFunction(
            name=name,
            parameters=(
                *self._native_handle_field_owner_parameters(owner),
                FortranParameter(
                    "source",
                    element_type,
                    ("pointer", self._array_dimension_attribute(handle.array.rank), "intent(in)"),
                ),
            ),
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranPointerAssignment(expression, CodeExpression("source")),
            ),
            is_subroutine=True,
        )

    def _native_handle_field_deallocate_procedure(self, owner, field) -> FortranFunction:
        """Build the deallocation procedure selected for one native-array-handle field."""
        expression = self._native_handle_field_expression(owner, field)
        name = self._native_handle_field_bridge_name(owner, field, NativeArrayOperation.DEALLOCATE)
        return FortranFunction(
            name=name,
            parameters=self._native_handle_field_owner_parameters(owner),
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranIf(
                    CodeExpression(self._native_handle_field_presence(field, expression)),
                    body=(FortranDeallocate(expression),),
                ),
            ),
            is_subroutine=True,
        )

    def _native_handle_field_nullify_procedure(self, owner, field) -> FortranFunction:
        """Build the pointer-nullification procedure selected for one native-array-handle field."""
        expression = self._native_handle_field_expression(owner, field)
        name = self._native_handle_field_bridge_name(owner, field, NativeArrayOperation.NULLIFY)
        return FortranFunction(
            name=name,
            parameters=self._native_handle_field_owner_parameters(owner),
            bind_name=name,
            declarations=self._native_handle_field_owner_declarations(owner),
            body=(
                *self._native_handle_field_owner_body(owner),
                FortranPointerAssignment(expression, CodeExpression("null()")),
            ),
            is_subroutine=True,
        )

    @staticmethod
    def _native_handle_field_owner_parameters(owner) -> tuple[FortranParameter, ...]:
        """Return owner-address ABI parameters for a native-array-handle field procedure."""
        if isinstance(owner, DerivedTypePlan):
            return (FortranParameter("owner_address", "type(c_ptr)", ("value",)),)
        return ()

    def _native_handle_field_owner_declarations(self, owner) -> tuple[FortranDeclaration, ...]:
        """Return local owner declarations required by a native-array-handle field procedure."""
        if isinstance(owner, DerivedTypePlan):
            return (self._derived_owner_declaration(owner),)
        return ()

    def _native_handle_field_owner_body(self, owner) -> tuple[FortranCall, ...]:
        """Return the owner association nodes shared by native-array-handle field procedures."""
        if isinstance(owner, DerivedTypePlan):
            return (self._derived_owner_association(),)
        return ()

    def _native_handle_field_expression(self, owner, field: DerivedFieldPlan) -> str:
        """Return the native field expression after the owner association has been established."""
        if isinstance(owner, DerivedTypePlan):
            return f"owner%{field.native_name}"
        variable, member = owner
        return self._module_member_expression(variable, member)

    @staticmethod
    def _native_handle_field_presence(field: DerivedFieldPlan, expression: str) -> str:
        """Return the allocation or association inquiry selected for one native-array-handle field."""
        handle = field.native_array_handle
        if handle is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no descriptor kind")
        intrinsic = "allocated" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "associated"
        return f"{intrinsic}({expression})"

    def _native_handle_field_bridge_name(self, owner, field, operation) -> str:
        """Return the exported bridge name for a native-array-handle field operation."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_bridge_name(owner, field, operation)
        variable, member = owner
        return self._module_member_handle_bridge_name(variable, member, operation)

    def _native_handle_field_callback_interface_name(self, owner, field) -> str:
        """Return the callback-interface name used by one native-array-handle field."""
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_callback_interface_name(owner, field)
        variable, member = owner
        return self._module_member_handle_callback_interface_name(variable, member)

    def _direct_ordinary_array_field_getter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> FortranFunction:
        """Pass one fixed field through a standard descriptor callback."""
        name = self._derived_field_bridge_name(derived, field, "get")
        interface = self._derived_field_callback_interface_name(derived, field)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter("callback_address", "type(c_funptr)", ("value",)),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            bind_name=name,
            declarations=(
                self._derived_owner_declaration(derived),
                FortranDeclaration("callback", f"procedure({interface})", ("pointer",)),
            ),
            body=(
                self._derived_owner_association(),
                FortranCall(
                    "c_f_procpointer",
                    (CodeExpression("callback_address"), CodeExpression("callback")),
                ),
                FortranCall(
                    "callback",
                    (CodeExpression(f"owner%{field.native_name}"), CodeExpression("context")),
                ),
            ),
            is_subroutine=True,
        )

    def _direct_ordinary_array_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> FortranFunction | None:
        """Copy one validated contiguous buffer into a fixed native field."""
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        name = self._derived_field_bridge_name(derived, field, "set")
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter("value_address", "type(c_ptr)", ("value",)),
            ),
            bind_name=name,
            declarations=(
                self._derived_owner_declaration(derived),
                self._ordinary_array_field_pointer_declaration(field),
            ),
            body=(
                self._derived_owner_association(),
                self._ordinary_array_field_association(field),
                FortranAssignment(f"owner%{field.native_name}", CodeExpression("value")),
            ),
            is_subroutine=True,
        )

    def _module_ordinary_array_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction:
        """Pass a fixed module member through a standard descriptor callback."""
        name = self._module_member_bridge_name(variable, member, "get")
        interface = self._module_member_callback_interface_name(variable, member)
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("callback_address", "type(c_funptr)", ("value",)),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            bind_name=name,
            declarations=(FortranDeclaration("callback", f"procedure({interface})", ("pointer",)),),
            body=(
                FortranCall(
                    "c_f_procpointer",
                    (CodeExpression("callback_address"), CodeExpression("callback")),
                ),
                FortranCall(
                    "callback",
                    (
                        CodeExpression(self._module_member_expression(variable, member)),
                        CodeExpression("context"),
                    ),
                ),
            ),
            is_subroutine=True,
        )

    def _module_ordinary_array_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction | None:
        """Copy one validated buffer into a writable plain-module member."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        name = self._module_member_bridge_name(variable, member, "set")
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("value_address", "type(c_ptr)", ("value",)),),
            bind_name=name,
            declarations=(self._ordinary_array_field_pointer_declaration(field),),
            body=(
                self._ordinary_array_field_association(field),
                FortranAssignment(self._module_member_expression(variable, member), CodeExpression("value")),
            ),
            is_subroutine=True,
        )

    def _ordinary_array_field_pointer_declaration(self, field: DerivedFieldPlan) -> FortranDeclaration:
        """Declare backend-local typed storage for a fixed field assignment."""
        array = field.array
        if array is None or array.rank is None:
            raise ValueError(f"Ordinary array field {field.owner_path!r} has no fixed rank")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        return FortranDeclaration(
            "value",
            scalar.fortran_spelling,
            ("pointer", self._array_dimension_attribute(array.rank)),
        )

    def _ordinary_array_field_association(self, field: DerivedFieldPlan) -> FortranCall:
        """Associate one validated Python buffer with its completed fixed shape."""
        array = field.array
        if array is None or array.rank is None or len(array.shape) != array.rank:
            raise ValueError(f"Ordinary array field {field.owner_path!r} has no fixed shape")
        shape = [render_declaration_extent(expression, {}, target="fortran") for expression in array.shape]
        return FortranCall(
            "c_f_pointer",
            (
                CodeExpression("value_address"),
                CodeExpression("value"),
                CodeExpression(f"[{', '.join(shape)}]"),
            ),
        )

    def _direct_scalar_field_getter(self, derived: DerivedTypePlan, field: DerivedFieldPlan) -> FortranFunction:
        """Build the direct-owner scalar field getter for one completed readable field."""
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        name = self._derived_field_bridge_name(derived, field, "get")
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("owner_address", "type(c_ptr)", ("value",)),),
            result_name="result",
            result_type=scalar.fortran_spelling,
            bind_name=name,
            declarations=(self._derived_owner_declaration(derived),),
            body=(
                self._derived_owner_association(),
                FortranAssignment("result", CodeExpression(f"owner%{field.native_name}")),
            ),
        )

    def _direct_scalar_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> FortranFunction | None:
        """Build the direct-owner scalar field setter only for a completed write-through field."""
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        name = self._derived_field_bridge_name(derived, field, "set")
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter("value", scalar.fortran_spelling, ("value",)),
            ),
            bind_name=name,
            declarations=(self._derived_owner_declaration(derived),),
            body=(
                self._derived_owner_association(),
                FortranAssignment(f"owner%{field.native_name}", CodeExpression("value")),
            ),
            is_subroutine=True,
        )

    def _direct_nested_field_getter(self, derived: DerivedTypePlan, field: DerivedFieldPlan) -> FortranFunction:
        """Build the direct-owner nested derived field getter for one completed field path."""
        if field.derived is None:
            raise ValueError(f"Nested field {field.owner_path!r} has no handoff")
        name = self._derived_field_bridge_name(derived, field, "get")
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("owner_address", "type(c_ptr)", ("value",)),),
            result_name="result",
            result_type="type(c_ptr)",
            bind_name=name,
            declarations=(self._derived_owner_declaration(derived),),
            body=(
                self._derived_owner_association(),
                FortranAssignment("result", CodeExpression(f"c_loc(owner%{field.native_name})")),
            ),
        )

    def _direct_nested_field_setter(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> FortranFunction | None:
        """Build the direct-owner nested derived field setter only for a completed write-through path."""
        if field.setter_action is not SetterAction.WRITE_THROUGH or field.derived is None:
            return None
        name = self._derived_field_bridge_name(derived, field, "set")
        return FortranFunction(
            name=name,
            parameters=(
                FortranParameter("owner_address", "type(c_ptr)", ("value",)),
                FortranParameter("value_address", "type(c_ptr)", ("value",)),
            ),
            bind_name=name,
            declarations=(
                self._derived_owner_declaration(derived),
                FortranDeclaration(
                    "value",
                    f"type({self._derived_native_alias(field.derived.backend_symbol)})",
                    ("pointer",),
                ),
            ),
            body=(
                self._derived_owner_association(),
                FortranCall("c_f_pointer", (CodeExpression("value_address"), CodeExpression("value"))),
                FortranAssignment(f"owner%{field.native_name}", CodeExpression("value")),
            ),
            is_subroutine=True,
        )

    def _module_scalar_member_getter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction:
        """Build the module-origin scalar member getter for one completed member path."""
        scalar = PrimitiveScalarTypeRegistry.type_for(member.field.semantic_type_name)
        name = self._module_member_bridge_name(variable, member, "get")
        return FortranFunction(
            name=name,
            result_name="result",
            result_type=scalar.fortran_spelling,
            bind_name=name,
            body=(FortranAssignment("result", CodeExpression(self._module_member_expression(variable, member))),),
        )

    def _module_scalar_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction | None:
        """Build the module-origin scalar member setter only for a completed write-through path."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return None
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        name = self._module_member_bridge_name(variable, member, "set")
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("value", scalar.fortran_spelling, ("value",)),),
            bind_name=name,
            body=(FortranAssignment(self._module_member_expression(variable, member), CodeExpression("value")),),
            is_subroutine=True,
        )

    def _module_nested_member_setter(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> FortranFunction | None:
        """Build the module-origin nested derived setter only for a completed write-through path."""
        field = member.field
        if field.setter_action is not SetterAction.WRITE_THROUGH or field.derived is None:
            return None
        name = self._module_member_bridge_name(variable, member, "set")
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("value_address", "type(c_ptr)", ("value",)),),
            bind_name=name,
            declarations=(
                FortranDeclaration(
                    "value",
                    f"type({self._derived_native_alias(field.derived.backend_symbol)})",
                    ("pointer",),
                ),
            ),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("value_address"), CodeExpression("value"))),
                FortranAssignment(self._module_member_expression(variable, member), CodeExpression("value")),
            ),
            is_subroutine=True,
        )

    def _derived_owner_declaration(self, derived: DerivedTypePlan) -> FortranDeclaration:
        """Return the local native-derived owner declaration used by direct field procedures."""
        return FortranDeclaration(
            "owner",
            f"type({self._derived_native_alias(derived.backend_symbol)})",
            ("pointer",),
        )

    @staticmethod
    def _derived_owner_association() -> FortranCall:
        """Return the shared C-address-to-owner association call for direct field procedures."""
        return FortranCall("c_f_pointer", (CodeExpression("owner_address"), CodeExpression("owner")))

    def _module_member_expression(self, variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        """Return the native member-access expression for a completed module member path."""
        return "%".join((self._native_variable_name(variable), *member.native_path))

    @staticmethod
    def _derived_field_symbol(derived: DerivedTypePlan, field: DerivedFieldPlan) -> str:
        """Return the normalized symbol fragment shared by all procedures for one derived field."""
        return f"{derived.backend_symbol}_{field.name}".casefold()

    def _derived_field_bridge_name(self, derived: DerivedTypePlan, field: DerivedFieldPlan, action: str) -> str:
        """Return the planner-owned direct-field symbol."""
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

    def _derived_field_callback_interface_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        """Return the consumer-interface name associated with one direct derived field."""
        return f"prik_field_{self._derived_field_symbol(derived, field)}_consumer"

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

    def _derived_handle_callback_interface_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        """Return the consumer-interface name associated with one direct native-array-handle field."""
        return f"prik_field_handle_{self._derived_field_symbol(derived, field)}_consumer"

    @staticmethod
    def _module_member_symbol(variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        """Return the normalized symbol fragment shared by procedures for one module member path."""
        return "_".join((variable.symbol_name, *member.path)).casefold()

    def _module_member_bridge_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        action: str,
    ) -> str:
        """Return the planner-owned module-member symbol."""
        return self._generated_support_procedure_entrypoint(
            ".".join((variable.owner_path, *member.path)), f"field:module:{action}"
        ).symbol_name

    def _module_member_callback_interface_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        """Return the consumer-interface name associated with one module member."""
        return f"prik_module_field_{self._module_member_symbol(variable, member)}_consumer"

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

    def _module_member_handle_callback_interface_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        """Return the consumer-interface name for one module native-array-handle member."""
        return f"prik_module_field_handle_{self._module_member_symbol(variable, member)}_consumer"

    def _derived_member_proxy_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Return derived module variables whose completed access mechanism is member proxying."""
        return tuple(
            variable
            for variable in self._variables(plan)
            if variable.derived is not None and variable.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY
        )

    def _derived_destroy_procedure(self, derived: DerivedTypePlan) -> FortranFunction:
        """Deallocate one wrapper-owned native object exactly once."""
        local = "value"
        return FortranFunction(
            name=self._derived_destroy_bridge_name(derived.backend_symbol),
            parameters=(FortranParameter("address", "type(c_ptr)", ("value",)),),
            bind_name=self._derived_destroy_bridge_name(derived.backend_symbol),
            declarations=(
                FortranDeclaration(
                    local,
                    f"type({self._derived_native_alias(derived.backend_symbol)})",
                    ("pointer",),
                ),
            ),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("address"), CodeExpression(local))),
                FortranIf(CodeExpression(f"associated({local})"), body=(FortranDeallocate(local),)),
            ),
            is_subroutine=True,
        )

    # Class construction is a thin allocator over Phase 8 opaque ownership.
    def _class_constructor_procedures(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Allocate one persistent typed object for each constructible class."""
        derived_by_identity = {derived.type_identity: derived for derived in self._derived_types(plan)}
        return tuple(
            self._class_constructor_procedure(surface, derived_by_identity[surface.type_identity])
            for namespace in plan.namespaces
            for surface in namespace.classes
            if self._has_generated_support_procedure_entrypoint(surface.owner_path, "class:create")
        )

    def _class_constructor_procedure(
        self,
        surface: ClassSurfacePlan,
        derived: DerivedTypePlan,
    ) -> FortranFunction:
        """Return one null-on-allocation-failure native constructor leaf."""
        local = "value"
        status = "allocation_status"
        name = self._class_create_bridge_name(surface)
        return FortranFunction(
            name=name,
            result_name="result",
            result_type="type(c_ptr)",
            bind_name=name,
            declarations=(
                FortranDeclaration(
                    local,
                    f"type({self._derived_native_alias(derived.backend_symbol)})",
                    ("pointer",),
                ),
                FortranDeclaration(status, "integer(c_int)"),
            ),
            body=(
                FortranAssignment("result", CodeExpression("c_null_ptr")),
                FortranAllocate(local, status=status),
                FortranIf(
                    CodeExpression(f"{status} == 0_c_int"),
                    body=(FortranAssignment("result", CodeExpression(f"c_loc({local})")),),
                ),
            ),
        )

    def _class_create_bridge_name(self, surface: ClassSurfacePlan) -> str:
        """Return the planner-owned class-constructor symbol."""
        return self._generated_support_procedure_entrypoint(surface.owner_path, "class:create").symbol_name

    def _allocatable_holder_destroy_procedure(self, derived: DerivedTypePlan) -> FortranFunction:
        """Destroy one wrapper-owned holder and its allocatable component."""
        holder = self._allocatable_holder_type_name(derived.backend_symbol)
        name = self._allocatable_holder_destroy_bridge_name(derived.backend_symbol)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("address", "type(c_ptr)", ("value",)),),
            bind_name=name,
            declarations=(FortranDeclaration("holder", f"type({holder})", ("pointer",)),),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("address"), CodeExpression("holder"))),
                FortranIf(CodeExpression("associated(holder)"), body=(FortranDeallocate("holder"),)),
            ),
            is_subroutine=True,
        )

    def _allocatable_holder_presence_procedure(self, derived: DerivedTypePlan) -> FortranFunction:
        """Report the current allocation state stored in one holder."""
        holder = self._allocatable_holder_type_name(derived.backend_symbol)
        name = self._allocatable_holder_presence_bridge_name(derived.backend_symbol)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("address", "type(c_ptr)", ("value",)),),
            result_name="result",
            result_type="logical(c_bool)",
            bind_name=name,
            declarations=(FortranDeclaration("holder", f"type({holder})", ("pointer",)),),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("address"), CodeExpression("holder"))),
                FortranAssignment("result", CodeExpression("allocated(holder%value)")),
            ),
        )

    def _pointer_holder_destroy_procedure(self, derived: DerivedTypePlan) -> FortranFunction:
        """Release only the pointer holder, never its unknown target."""
        holder = self._pointer_holder_type_name(derived.backend_symbol)
        name = self._pointer_holder_destroy_bridge_name(derived.backend_symbol)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("address", "type(c_ptr)", ("value",)),),
            bind_name=name,
            declarations=(FortranDeclaration("holder", f"type({holder})", ("pointer",)),),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("address"), CodeExpression("holder"))),
                FortranIf(
                    CodeExpression("associated(holder)"),
                    body=(FortranNullify("holder%value"), FortranDeallocate("holder")),
                ),
            ),
            is_subroutine=True,
        )

    def _pointer_holder_presence_procedure(self, derived: DerivedTypePlan) -> FortranFunction:
        """Report the holder's current association state."""
        holder = self._pointer_holder_type_name(derived.backend_symbol)
        name = self._pointer_holder_presence_bridge_name(derived.backend_symbol)
        return FortranFunction(
            name=name,
            parameters=(FortranParameter("address", "type(c_ptr)", ("value",)),),
            result_name="result",
            result_type="logical(c_bool)",
            bind_name=name,
            declarations=(FortranDeclaration("holder", f"type({holder})", ("pointer",)),),
            body=(
                FortranCall("c_f_pointer", (CodeExpression("address"), CodeExpression("holder"))),
                FortranAssignment("result", CodeExpression("associated(holder%value)")),
            ),
        )

    @staticmethod
    def _derived_native_alias(type_name: str) -> str:
        """Return the imported native alias used to disambiguate one derived type in bridge source."""
        return f"prik_type_{type_name.casefold()}"

    def _derived_destroy_bridge_name(self, type_name: str) -> str:
        """Return the planner-owned derived-destroy symbol."""
        return self._generated_support_procedure_entrypoint(
            self._derived_owner_paths[type_name], "derived:destroy"
        ).symbol_name

    @staticmethod
    def _allocatable_holder_type_name(type_name: str) -> str:
        """Return the internal Fortran type name for an allocatable derived holder."""
        return f"prik_{type_name.casefold()}_allocatable_holder"

    @staticmethod
    def _pointer_holder_type_name(type_name: str) -> str:
        """Return the internal Fortran type name for a pointer derived holder."""
        return f"prik_{type_name.casefold()}_pointer_holder"

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

    def _module_derived_presence_bridge_name(self, plan: ModuleVariablePlan) -> str:
        """Return the planner-owned nullable module-derived presence symbol."""
        return self._generated_support_procedure_entrypoint(plan.owner_path, "module:derived:present").symbol_name

    def _external_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        """Declare ordinary standalone wrapper targets with explicit interfaces."""
        native_procedures = tuple(
            self._external_interface_procedure(function)
            for function in self._functions(plan)
            if function.bridge is not None
            and function.bridge.external_declaration is ExternalDeclarationMode.EXPLICIT_INTERFACE
        )
        return (FortranInterface(native_procedures),) if native_procedures else ()

    def _prototype_interfaces(
        self,
        plan: ModulePlan,
    ) -> tuple[FortranInterface, ...]:
        """Emit every used prototype through the one abstract-interface path."""
        prototypes = self._prototype_plans(plan)
        procedures = tuple(self._procedure_prototype_interface(item) for item in prototypes)
        return (FortranInterface(procedures, abstract=True),) if procedures else ()

    def _prototype_plans(self, plan: ModulePlan) -> tuple[ProcedurePrototypePlan, ...]:
        """Deduplicate callback and direct-call uses by generated interface symbol."""
        candidates = (
            *(callback.prototype for callback in self._callback_sites(plan)),
            *(
                declaration.prototype
                for function in self._functions(plan)
                for declaration in function.declaration_callables
                if declaration.prototype is not None
            ),
        )
        prototypes: dict[str, ProcedurePrototypePlan] = {}
        for prototype in candidates:
            key = prototype.interface_symbol.casefold()
            previous = prototypes.setdefault(key, prototype)
            if previous is not prototype and not self._same_procedure_prototype(previous, prototype):
                raise ValueError(f"Conflicting prototype signatures for {prototype.name!r}")
        return tuple(prototypes.values())

    def _same_procedure_prototype(
        self,
        left: ProcedurePrototypePlan,
        right: ProcedurePrototypePlan,
    ) -> bool:
        """Compare only characteristics represented in one abstract interface."""
        return self._procedure_prototype_interface(left) == self._procedure_prototype_interface(right)

    def _procedure_prototype_interface(
        self,
        prototype: ProcedurePrototypePlan,
    ) -> FortranInterfaceProcedure:
        """Lower one shared signature to its generated abstract interface body."""
        result = prototype.result
        return FortranInterfaceProcedure(
            name=prototype.interface_symbol,
            imports=self._procedure_prototype_imports(prototype),
            parameters=tuple(self._procedure_prototype_parameter(item) for item in prototype.arguments),
            result_name="prik_result" if result is not None else None,
            result_type=self._procedure_prototype_result_type(result) if result is not None else None,
            is_subroutine=result is None,
            pure=prototype.pure,
        )

    def _procedure_prototype_parameter(
        self,
        argument: ProcedurePrototypeArgumentPlan,
    ) -> FortranParameter:
        """Declare one exact dummy from the shared prototype plan."""
        attributes = []
        if argument.passed_by_value:
            attributes.append("value")
        if argument.intent is not None:
            attributes.append(f"intent({argument.intent})")
        if argument.rank:
            attributes.append(f"dimension({self._procedure_prototype_shape(argument.array, argument.owner_path)})")
        return FortranParameter(
            argument.name,
            self._procedure_prototype_type(argument),
            tuple(attributes),
        )

    def _procedure_prototype_result_type(
        self,
        result: ProcedurePrototypeResultPlan,
    ) -> str:
        """Declare one exact function result from the shared prototype plan."""
        result_type = self._procedure_prototype_type(result)
        if result.rank:
            result_type += f", dimension({self._procedure_prototype_shape(result.array, result.owner_path)})"
        return result_type

    def _procedure_prototype_type(
        self,
        value: ProcedurePrototypeArgumentPlan | ProcedurePrototypeResultPlan,
    ) -> str:
        """Return the native type shared by callback and direct prototype uses."""
        if value.derived_backend_symbol is not None:
            return f"type({self._derived_native_alias(value.derived_backend_symbol)})"
        if value.semantic_type_name == "String":
            if value.character_length is None:
                raise ValueError(f"Prototype value {value.owner_path!r} has no fixed character length")
            return f"character(kind=c_char, len={value.character_length})"
        return PrimitiveScalarTypeRegistry.type_for(value.semantic_type_name).fortran_spelling

    @staticmethod
    def _procedure_prototype_shape(array: ArrayHandoffPlan | None, owner_path: str) -> str:
        """Render an exact prototype array shape without backend role substitution."""
        if array is None or array.rank is None:
            raise ValueError(f"Prototype value {owner_path!r} has no concrete shape")
        return ", ".join(render_declaration_extent(expression, {}, target="fortran") for expression in array.shape)

    def _procedure_prototype_imports(
        self,
        prototype: ProcedurePrototypePlan,
    ) -> tuple[str, ...]:
        """Import every kind or derived alias referenced by an interface body."""
        values = (
            *prototype.arguments,
            *((prototype.result,) if prototype.result is not None else ()),
        )
        return tuple(dict.fromkeys(self._procedure_prototype_import(item) for item in values))

    def _procedure_prototype_import(
        self,
        value: ProcedurePrototypeArgumentPlan | ProcedurePrototypeResultPlan,
    ) -> str:
        """Return the host symbol needed to spell one prototype value type."""
        if value.derived_backend_symbol is not None:
            return self._derived_native_alias(value.derived_backend_symbol)
        if value.semantic_type_name == "String":
            return "c_char"
        return self._iso_symbol(value.semantic_type_name)

    def _prototype_entity_declarations(self, plan: ModulePlan) -> tuple[FortranDeclaration, ...]:
        """Declare directly called standalone entities from their abstract signatures."""
        entities: dict[str, DeclarationCallablePlan] = {}
        for function in self._functions(plan):
            for declaration in function.declaration_callables:
                if declaration.action is not DeclarationCallableAction.STANDALONE_PROCEDURE:
                    continue
                previous = entities.setdefault(declaration.backend_symbol.casefold(), declaration)
                if previous is not declaration and not self._same_prototype_entity(previous, declaration):
                    raise ValueError(f"Conflicting standalone prototype entities for {declaration.native_name!r}")
        return tuple(
            FortranDeclaration(
                declaration.backend_symbol,
                f"procedure({self._required_declaration_prototype(declaration).interface_symbol})",
            )
            for declaration in entities.values()
        )

    def _same_prototype_entity(
        self,
        left: DeclarationCallablePlan,
        right: DeclarationCallablePlan,
    ) -> bool:
        """Return whether two direct uses declare the same native entity exactly."""
        return self._same_procedure_prototype(
            self._required_declaration_prototype(left),
            self._required_declaration_prototype(right),
        )

    @staticmethod
    def _required_declaration_prototype(
        declaration: DeclarationCallablePlan,
    ) -> ProcedurePrototypePlan:
        """Return a direct entity's completed prototype or reject an edited plan."""
        if declaration.prototype is None:
            raise ValueError(f"Declaration callable {declaration.owner_path!r} has no prototype")
        return declaration.prototype

    def _native_external_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Lower the completed implicit-external declaration mode."""
        mode = plan.bridge.external_declaration
        if mode in {ExternalDeclarationMode.NONE, ExternalDeclarationMode.EXPLICIT_INTERFACE}:
            return ()
        if mode is not ExternalDeclarationMode.IMPLICIT_EXTERNAL:
            raise ValueError(f"Unsupported external declaration mode for {plan.owner_path!r}: {mode!r}")
        name = self._native_function_name(plan)
        if plan.bridge.native_is_subroutine:
            return (FortranDeclaration(name, "external"),)
        return (
            FortranDeclaration(
                name,
                self._native_result_type(plan, self._direct_result(plan)),
                ("external",),
            ),
        )

    def _callback_sites(self, plan: ModulePlan) -> tuple[CallbackHandoffPlan, ...]:
        """Return callback sites in stable native-call order."""
        return tuple(
            argument.callback
            for function in self._functions(plan)
            for argument in sorted(function.arguments, key=lambda item: item.native_position)
            if argument.callback is not None
        )

    def _callback_c_interface(
        self,
        callback: CallbackHandoffPlan,
        *,
        name: str,
        bind_name: str,
    ) -> FortranInterfaceProcedure:
        """Declare the flattened C ABI implemented by one Python trampoline."""
        operation = callback.entrypoint.support_procedure
        if operation.implementation_owner is not GeneratedSupportProcedureImplementationOwner.BINDING:
            raise ValueError(f"Callback trampoline {operation.key!r} is not binding-owned")
        is_subroutine = operation.signature.result.kind is NativeEntrypointABIValueKind.VOID
        return FortranInterfaceProcedure(
            name=name,
            imports=self._callback_c_imports(callback),
            parameters=tuple(
                self._support_procedure_fortran_parameter(parameter) for parameter in operation.signature.parameters
            ),
            result_name=None if is_subroutine else "callback_result",
            result_type=(None if is_subroutine else self._support_procedure_fortran_type(operation.signature.result)),
            is_subroutine=is_subroutine,
            bind_name=bind_name,
            bind_c=True,
        )

    def _callback_c_imports(self, callback: CallbackHandoffPlan) -> tuple[str, ...]:
        """Import only ISO C kinds referenced by the flattened interface."""
        imports = []
        transfers = (
            *callback.arguments,
            *((callback.result.transfer,) if callback.result.transfer is not None else ()),
        )
        for transfer in transfers:
            if transfer.abi is CallbackABIKind.VALUE:
                imports.append(self._iso_symbol(transfer.semantic_type_name))
            else:
                imports.append("c_ptr")
            if transfer.abi in {CallbackABIKind.DATA_AND_SHAPE, CallbackABIKind.DATA_AND_LENGTH}:
                imports.append("c_int64_t")
        return tuple(dict.fromkeys(imports))

    def _callback_native_imports(self, callback: CallbackHandoffPlan) -> tuple[str, ...]:
        """Import native kinds and exact derived aliases used by the adapter."""
        imports = []
        transfers = (
            *callback.arguments,
            *((callback.result.transfer,) if callback.result.transfer is not None else ()),
        )
        for transfer in transfers:
            if transfer.abi is CallbackABIKind.DERIVED_ADDRESS:
                if transfer.derived_backend_symbol is None:
                    raise ValueError(f"Callback derived transfer {transfer.owner_path!r} has no backend symbol")
                imports.append(self._derived_native_alias(transfer.derived_backend_symbol))
            elif transfer.abi is CallbackABIKind.DATA_AND_LENGTH:
                imports.append("c_char")
            else:
                imports.append(self._iso_symbol(transfer.semantic_type_name))
        return tuple(dict.fromkeys(imports))

    def _derived_call_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        """Declare the typed callback ABI shared by every scalar-derived call."""
        if not any(
            argument.derived_call is not None for function in self._functions(plan) for argument in function.arguments
        ) and not any(variable.derived is not None for variable in self._variables(plan)):
            return ()
        procedures = (
            FortranInterfaceProcedure(
                "prik_derived_consumer",
                imports=("c_ptr", "c_int"),
                parameters=(
                    FortranParameter("address", "type(c_ptr)", ("value",)),
                    FortranParameter("context", "type(c_ptr)", ("value",)),
                ),
                result_name="status",
                result_type="integer(c_int)",
                bind_c=True,
            ),
            FortranInterfaceProcedure(
                "prik_derived_scoped",
                imports=("c_ptr", "c_funptr", "c_int"),
                parameters=(
                    FortranParameter("consumer", "type(c_funptr)", ("value",)),
                    FortranParameter("context", "type(c_ptr)", ("value",)),
                ),
                result_name="status",
                result_type="integer(c_int)",
                bind_c=True,
            ),
            FortranInterfaceProcedure(
                "prik_derived_checkout",
                imports=("c_ptr", "c_int"),
                parameters=(FortranParameter("holder", "type(c_ptr)", ("intent(out)",)),),
                result_name="status",
                result_type="integer(c_int)",
                bind_c=True,
            ),
            FortranInterfaceProcedure(
                "prik_derived_restore",
                imports=("c_ptr", "c_int"),
                parameters=(FortranParameter("holder", "type(c_ptr)", ("value",)),),
                result_name="status",
                result_type="integer(c_int)",
                bind_c=True,
            ),
        )
        return (FortranInterface(procedures, abstract=True),)

    def _module_descriptor_callback_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        """Declare typed C callbacks used to expose plain module allocatables."""
        procedures = tuple(
            self._module_descriptor_callback_interface(variable)
            for variable in self._variables(plan)
            if self._uses_module_allocatable_descriptor(variable)
        )
        return (FortranInterface(procedures),) if procedures else ()

    def _derived_array_callback_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        """Declare standard-descriptor callbacks for live ordinary array fields."""
        procedures = (
            *self._direct_ordinary_array_callback_interfaces(plan),
            *self._module_ordinary_array_callback_interfaces(plan),
            *self._direct_handle_callback_interfaces(plan),
            *self._module_handle_callback_interfaces(plan),
        )
        return (FortranInterface(procedures),) if procedures else ()

    def _direct_ordinary_array_callback_interfaces(self, plan: ModulePlan) -> tuple:
        """Return callback interfaces required by direct ordinary-array field procedures."""
        return tuple(
            self._ordinary_array_callback_interface(
                field,
                self._derived_field_callback_interface_name(derived, field),
            )
            for derived in self._derived_types(plan)
            for field in derived.fields
            if field.access is DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR
        )

    def _module_ordinary_array_callback_interfaces(self, plan: ModulePlan) -> tuple:
        """Return callback interfaces required by module ordinary-array member procedures."""
        return tuple(
            self._ordinary_array_callback_interface(
                member.field,
                self._module_member_callback_interface_name(variable, member),
            )
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            if member.field.access is DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR
        )

    def _direct_handle_callback_interfaces(self, plan: ModulePlan) -> tuple:
        """Return callback interfaces required by direct native-array-handle field procedures."""
        return tuple(
            self._native_handle_callback_interface(
                field,
                self._derived_handle_callback_interface_name(derived, field),
            )
            for derived in self._derived_types(plan)
            for field in derived.fields
            if field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE
        )

    def _module_handle_callback_interfaces(self, plan: ModulePlan) -> tuple:
        """Return callback interfaces required by module native-array-handle member procedures."""
        return tuple(
            self._native_handle_callback_interface(
                member.field,
                self._module_member_handle_callback_interface_name(variable, member),
            )
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            if member.field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE
        )

    def _ordinary_array_callback_interface(
        self,
        field: DerivedFieldPlan,
        name: str,
    ) -> FortranInterfaceProcedure:
        """Return one element- and rank-typed descriptor consumer interface."""
        array = field.array
        if array is None or array.rank is None:
            raise ValueError(f"Ordinary array field {field.owner_path!r} has no callback rank")
        scalar = PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name)
        return FortranInterfaceProcedure(
            name=name,
            imports=(self._iso_symbol(field.semantic_type_name), "c_ptr"),
            parameters=(
                FortranParameter(
                    "value",
                    scalar.fortran_spelling,
                    (self._array_dimension_attribute(array.rank), "intent(in)"),
                ),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            is_subroutine=True,
            bind_name=name,
        )

    def _native_handle_callback_interface(
        self,
        field: DerivedFieldPlan,
        name: str,
    ) -> FortranInterfaceProcedure:
        """Return one descriptor-kind-typed field callback interface."""
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no callback rank")
        attribute = "allocatable" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "pointer"
        element_type = (
            "character(kind=c_char, len=:)"
            if field.string_element
            else PrimitiveScalarTypeRegistry.type_for(field.semantic_type_name).fortran_spelling
        )
        imports = (self._iso_symbol(field.semantic_type_name), "c_ptr")
        return FortranInterfaceProcedure(
            name=name,
            imports=imports,
            parameters=(
                FortranParameter(
                    "value",
                    element_type,
                    (attribute, self._array_dimension_attribute(handle.array.rank), "intent(in)"),
                ),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            is_subroutine=True,
            bind_name=name,
        )

    def _module_descriptor_callback_interface(
        self,
        plan: ModuleVariablePlan,
    ) -> FortranInterfaceProcedure:
        """Return one rank- and element-typed descriptor consumer interface."""
        handle = plan.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {plan.owner_path!r} has no descriptor rank")
        return FortranInterfaceProcedure(
            name=self._module_descriptor_callback_interface_name(plan),
            imports=(self._iso_symbol(plan.semantic_type_name), "c_ptr"),
            parameters=(
                FortranParameter(
                    "value",
                    self._module_native_array_element_type(plan),
                    ("allocatable", self._array_dimension_attribute(handle.array.rank), "intent(in)"),
                ),
                FortranParameter("context", "type(c_ptr)", ("value",)),
            ),
            is_subroutine=True,
            bind_name=self._module_descriptor_callback_interface_name(plan),
        )

    def _module_descriptor_callback_interface_name(self, plan: ModuleVariablePlan) -> str:
        """Return one unique typed callback interface name."""
        return f"prik_{plan.symbol_name}_descriptor_consumer"

    def _allocator_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        """Return the allocator interface required by detached bridge copies."""
        if not self._needs_allocator_interface(plan):
            return ()
        procedure = FortranInterfaceProcedure(
            name="c_malloc",
            imports=("c_ptr", "c_size_t"),
            parameters=(FortranParameter("size", "integer(c_size_t)", ("value",)),),
            result_name="ptr",
            result_type="type(c_ptr)",
            bind_name="prik_malloc",
        )
        return (FortranInterface((procedure,)),)

    def _needs_allocator_interface(self, plan: ModulePlan) -> bool:
        """Return whether module getter values or function copies allocate storage."""
        return self._needs_module_getter_allocator(plan) or self._needs_function_copy_allocator(plan)

    def _needs_module_getter_allocator(self, plan: ModulePlan) -> bool:
        """Return whether a nullable scalar descriptor getter copies one value."""
        return any(
            variable.bridge.native_getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
            for variable in self._variables(plan)
        )

    def _needs_function_copy_allocator(self, plan: ModulePlan) -> bool:
        """Return whether any function copies an array or string result."""
        return any(self._function_needs_copy_allocator(function) for function in self._functions(plan))

    def _function_needs_copy_allocator(self, function: FunctionPlan) -> bool:
        """Return whether one function owns a result-copy allocation."""
        return self._result_plans_need_allocator(function) or self._native_result_slots_need_allocator(function)

    def _result_plans_need_allocator(self, function: FunctionPlan) -> bool:
        """Return whether one Python result is an array or string copy."""
        return any(
            result.scalar_descriptor is not None or result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY}
            for result in function.results
        )

    def _native_result_slots_need_allocator(self, function: FunctionPlan) -> bool:
        """Return whether one hidden native result is an array or string copy."""
        return any(
            slot.scalar_descriptor is not None or slot.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY}
            for slot in self._adapter_slots(function)
            if slot.source_kind == "result"
        )

    def _external_interface_procedure(self, plan: FunctionPlan) -> FortranInterfaceProcedure:
        """Declare one standalone native target from its completed function plan."""
        slots = self._adapter_slots(plan)
        arguments = {argument.owner_path: argument for argument in plan.arguments}
        parameters = tuple(self._external_interface_slot_parameter(plan, slot, arguments) for slot in slots)
        result_name, result_type, direct_result = self._external_interface_result(plan)
        imports = self._external_interface_imports(plan, slots, direct_result)
        return FortranInterfaceProcedure(
            name=plan.bridge.native_name,
            imports=imports,
            parameters=parameters,
            parameter_declarations=self._external_interface_parameter_declarations(slots, parameters),
            result_name=result_name,
            result_type=result_type,
            is_subroutine=plan.bridge.native_is_subroutine,
        )

    def _external_interface_result(
        self,
        plan: FunctionPlan,
    ) -> tuple[str | None, str | None, ResultPlan | None]:
        """Return the standalone target's result declaration, if it is a function."""
        if plan.bridge.native_is_subroutine:
            return None, None, None
        direct_result = self._direct_result(plan)
        return "native_result", self._native_result_type(plan, direct_result), direct_result

    def _external_interface_imports(
        self,
        plan: FunctionPlan,
        slots: tuple[NativeEntrypointProjectedSlotPlan, ...],
        direct_result: ResultPlan | None,
    ) -> tuple[str, ...]:
        """Collect type and declaration-callable symbols visible in the interface body."""
        imports = [self._iso_symbol(slot.semantic_type_name) for slot in slots if slot.semantic_type_name is not None]
        imports.extend(
            declaration.backend_symbol
            for declaration in plan.declaration_callables
            if declaration.action is DeclarationCallableAction.STANDALONE_PROCEDURE
        )
        if direct_result is not None:
            imports.append(self._iso_symbol(direct_result.semantic_type_name))
        return tuple(dict.fromkeys(imports))

    @staticmethod
    def _external_interface_parameter_declarations(
        slots: tuple[NativeEntrypointProjectedSlotPlan, ...],
        parameters: tuple[FortranParameter, ...],
    ) -> tuple[FortranParameter, ...]:
        """Declare extent providers first without changing native ABI order."""
        pending = list(zip(slots, parameters, strict=True))
        declarations = []
        emitted_roles = set()
        while pending:
            for index, (slot, parameter) in enumerate(pending):
                dependencies = (
                    {role for axis_roles in slot.array.extent_reference_roles for role in axis_roles}
                    if slot.array is not None
                    else set()
                )
                if dependencies <= emitted_roles:
                    declarations.append(parameter)
                    emitted_roles.add(slot.symbolic_role)
                    if slot.array is not None:
                        emitted_roles.update(slot.array.extent_roles)
                    pending.pop(index)
                    break
            else:
                # Central plan validation owns missing or cyclic extent roles.
                # Preserve native order here so emission remains deterministic.
                declarations.extend(parameter for _, parameter in pending)
                break
        return tuple(declarations)

    def _external_interface_slot_parameter(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
        arguments: dict[str, ArgumentTransferPlan],
    ) -> FortranParameter:
        """Declare one external dummy from its completed ordered ABI slot."""
        if slot.source_kind in {"implicit", "projection"}:
            argument = arguments.get(slot.owner_path)
            if argument is None:
                raise ValueError(f"External native slot {slot.owner_path!r} has no argument transfer plan")
            return self._external_interface_parameter(plan, argument, name=slot.native_name.lower())
        if slot.source_kind == "result":
            return self._external_interface_result_parameter(plan, slot)
        if slot.source_kind == "literal":
            return self._external_interface_literal_parameter(slot)
        raise ValueError(f"Unsupported external native slot source kind {slot.source_kind!r}")

    def _external_interface_result_parameter(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one hidden output dummy from completed result-slot policy."""
        if slot.scalar_descriptor is not None:
            return self._external_interface_scalar_descriptor_result_parameter(slot)
        match slot.object_kind:
            case ObjectKind.SCALAR:
                return self._external_interface_scalar_result_parameter(slot)
            case ObjectKind.STRING:
                return self._external_interface_string_result_parameter(slot)
            case ObjectKind.NUMPY_ARRAY:
                return self._external_interface_array_result_parameter(plan, slot)
            case ObjectKind.DERIVED_TYPE:
                return self._external_interface_derived_result_parameter(slot)
            case _:
                raise ValueError(f"Unsupported external hidden output {slot.owner_path!r}")

    @staticmethod
    def _external_interface_scalar_descriptor_result_parameter(
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one completed allocatable or pointer scalar output."""
        descriptor = slot.scalar_descriptor
        if descriptor is None:
            raise ValueError(f"Scalar descriptor output {slot.owner_path!r} has no descriptor plan")
        attribute = "allocatable" if descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "pointer"
        if slot.object_kind is ObjectKind.STRING:
            return FortranParameter(slot.native_name.lower(), "character(kind=c_char, len=:)", (attribute,))
        if slot.semantic_type_name is None:
            raise ValueError(f"Scalar descriptor output {slot.owner_path!r} has no element type")
        scalar_type = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name)
        return FortranParameter(slot.native_name.lower(), scalar_type.fortran_spelling, (attribute,))

    @staticmethod
    def _external_interface_scalar_result_parameter(
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one completed primitive scalar output."""
        if slot.semantic_type_name is None:
            raise ValueError(f"Scalar output {slot.owner_path!r} has no element type")
        scalar_type = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name)
        return FortranParameter(slot.native_name.lower(), scalar_type.fortran_spelling)

    @staticmethod
    def _external_interface_string_result_parameter(
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one completed fixed or assumed-length string output."""
        length = "*" if slot.character_length is None else str(slot.character_length)
        return FortranParameter(slot.native_name.lower(), f"character(kind=c_char, len={length})")

    def _external_interface_array_result_parameter(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one completed ordinary or descriptor array output."""
        if slot.array is None:
            raise ValueError(f"Array output {slot.owner_path!r} has no shape plan")
        if self._is_scalar_storage_array(slot.array):
            return FortranParameter(slot.native_name.lower(), self._array_result_element_type(slot))
        attributes = []
        if slot.native_array_handle is not None:
            attributes.append(
                "allocatable"
                if slot.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
                else "pointer"
            )
        dimension = self._external_array_dimension_from_plan(slot.array, plan)
        attributes.append(f"dimension({dimension})")
        return FortranParameter(
            slot.native_name.lower(),
            self._array_result_element_type(slot),
            tuple(attributes),
        )

    def _external_interface_derived_result_parameter(
        self,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one completed scalar-derived output."""
        if slot.derived is None:
            raise ValueError(f"Derived output {slot.owner_path!r} has no handoff plan")
        attribute = {
            DerivedObjectStorage.ALLOCATABLE_HOLDER: ("allocatable",),
            DerivedObjectStorage.POINTER_HOLDER: ("pointer",),
        }.get(slot.derived.storage, ())
        return FortranParameter(
            slot.native_name.lower(),
            f"type({self._derived_native_alias(slot.derived.backend_symbol)})",
            attribute,
        )

    @staticmethod
    def _external_interface_literal_parameter(
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> FortranParameter:
        """Declare one hidden literal dummy from its completed scalar type."""
        if slot.semantic_type_name is None:
            raise ValueError(f"External literal slot {slot.owner_path!r} has no scalar type")
        scalar_type = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name)
        return FortranParameter(slot.native_name.lower(), scalar_type.fortran_spelling)

    def _native_result_type(self, plan: FunctionPlan, result: ResultPlan | None) -> str:
        """Return the native procedure result type inside an external interface."""
        if result is None:
            raise ValueError("External native function is missing its direct result plan")
        if result.scalar_descriptor is not None:
            attribute = (
                "allocatable"
                if result.scalar_descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
                else "pointer"
            )
            if result.object_kind is ObjectKind.STRING:
                return f"character(kind=c_char, len=:), {attribute}"
            scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name)
            return f"{scalar_type.fortran_spelling}, {attribute}"
        if result.object_kind is ObjectKind.NUMPY_ARRAY:
            if self._is_scalar_storage_array(result.array):
                return self._array_result_element_type(result)
            shape = self._array_result_shape(plan, result)
            return f"{self._array_result_element_type(result)}, dimension({', '.join(shape)})"
        if result.object_kind is ObjectKind.STRING:
            return f"character(kind=c_char, len={self._string_result_length(result)})"
        if result.object_kind is ObjectKind.DERIVED_TYPE:
            if result.derived is None:
                raise ValueError(f"Derived result {result.owner_path!r} has no handoff plan")
            attribute = {
                DerivedObjectStorage.ALLOCATABLE_HOLDER: ", allocatable",
                DerivedObjectStorage.POINTER_HOLDER: ", pointer",
            }.get(result.derived.storage, "")
            return f"type({self._derived_native_alias(result.derived.backend_symbol)}){attribute}"
        return PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name).fortran_spelling

    def _external_interface_parameter(
        self,
        plan: FunctionPlan,
        argument: ArgumentTransferPlan,
        *,
        name: str | None = None,
    ) -> FortranParameter:
        """Return the native external dummy declaration for one planned argument."""
        parameter_name = name or argument.bridge.native_name.casefold()
        if argument.callback is not None:
            return FortranParameter(parameter_name, "external")
        attributes = (
            ("optional",)
            if argument.entrypoint.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
            else ()
        )
        if argument.object_kind is ObjectKind.NUMPY_ARRAY:
            return self._external_interface_array_argument_parameter(
                plan,
                argument,
                parameter_name,
                attributes,
            )
        if argument.object_kind is ObjectKind.STRING:
            length = argument.projected_call_slot.character_length
            length_text = "*" if length is None else str(length)
            return FortranParameter(
                parameter_name,
                f"character(kind=c_char, len={length_text})",
                attributes,
            )
        return FortranParameter(
            parameter_name,
            PrimitiveScalarTypeRegistry.type_for(argument.semantic_type_name).fortran_spelling,
            attributes,
        )

    def _external_interface_array_argument_parameter(
        self,
        plan: FunctionPlan,
        argument: ArgumentTransferPlan,
        parameter_name: str,
        attributes: tuple[str, ...],
    ) -> FortranParameter:
        """Declare a native array or scalar-storage dummy from completed array facts."""
        array = argument.array
        if array is None:
            raise ValueError(f"Array argument {argument.owner_path!r} has no shape plan")
        element_type = self._array_element_fortran_type(argument)
        if self._is_scalar_storage_array(array):
            return FortranParameter(parameter_name, element_type, attributes)
        dimension = self._external_array_dimension(plan, argument)
        if argument.native_array_handle is not None:
            descriptor_attribute = (
                "allocatable"
                if argument.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
                else "pointer"
            )
            attributes = (*attributes, descriptor_attribute)
        return FortranParameter(
            parameter_name,
            element_type,
            (*attributes, f"dimension({dimension})"),
        )

    def _external_array_dimension(self, plan: FunctionPlan, argument: ArgumentTransferPlan) -> str:
        """Lower the completed native dummy shape without changing its ABI category."""
        array = argument.array
        if array is None:
            raise ValueError(f"Array argument {argument.owner_path!r} has no shape plan")
        return self._external_array_dimension_from_plan(array, plan)

    def _external_array_dimension_from_plan(self, array: ArrayHandoffPlan, plan: FunctionPlan) -> str:
        """Render rank/category facts already selected in one array plan."""
        if array.rank is None:
            return ".."
        if array.category in {"assumed_shape", "deferred_shape"}:
            return ", ".join(":" for _ in range(array.rank))
        shape = list(self._array_shape_from_roles(array, plan))
        if array.native_order == "ORDER_C":
            shape.reverse()
        if array.category != "assumed_size":
            return ", ".join(shape)
        return self._external_assumed_size_dimension(array, shape)

    @staticmethod
    def _external_assumed_size_dimension(array: ArrayHandoffPlan, shape: list[str]) -> str:
        """Use a legal assumed-size spelling while retaining plan rank elsewhere."""
        if array.native_order == "ORDER_C" or any(item == ":" for item in shape[:-1]):
            return "*"
        shape[-1] = "*"
        return ", ".join(shape)

    @staticmethod
    def _is_scalar_storage_array(array: ArrayHandoffPlan | None) -> bool:
        """Return whether an array plan represents rank-zero scalar storage rather than an ordinary array."""
        return bool(array is not None and array.rank == 0 and array.category == SCALAR_STORAGE_CATEGORY)

    # Ordinary-array result-shape lowering.
    def _array_result_shape(self, plan: FunctionPlan, result: ResultPlan) -> tuple[str, ...]:
        """Lower one result shape through the plan's native scalar roles."""
        if result.array is None:
            raise ValueError(f"Array result {result.owner_path!r} has no shape plan")
        return self._array_shape_from_roles(result.array, plan)

    def _array_output_shape(
        self,
        plan: FunctionPlan,
        slot: NativeEntrypointProjectedSlotPlan,
    ) -> tuple[str, ...]:
        """Lower one hidden-output shape through the plan's native scalar roles."""
        if slot.array is None:
            raise ValueError(f"Array output {slot.owner_path!r} has no shape plan")
        return self._array_shape_from_roles(slot.array, plan)

    def _array_shape_from_roles(self, array: ArrayHandoffPlan, plan: FunctionPlan) -> tuple[str, ...]:
        """Render validated shape tokens with their planned native role names."""
        role_names = self._array_shape_role_names(plan)
        return tuple(
            self._render_array_shape_axis(array, axis, expression, role_names)
            for axis, expression in enumerate(array.shape)
        )

    @staticmethod
    def _array_shape_role_names(plan: FunctionPlan) -> dict[str, str]:
        """Map planned scalar, extent, and callable roles to bridge spellings."""
        role_names = {
            argument.entrypoint.handoff_role: argument.entrypoint.parameter_name for argument in plan.arguments
        }
        role_names.update(
            {
                role: f"{argument.entrypoint.parameter_name}_extent_{axis}"
                for argument in plan.arguments
                if argument.array is not None
                for axis, role in enumerate(argument.array.extent_roles)
            }
        )
        role_names.update(
            {declaration.symbolic_role: declaration.backend_symbol for declaration in plan.declaration_callables}
        )
        return role_names

    def _render_array_shape_axis(
        self,
        array: ArrayHandoffPlan,
        axis: int,
        expression: str,
        role_names: dict[str, str],
    ) -> str:
        """Render one axis after resolving its value and callable symbols."""
        substitutions = self._shape_role_substitutions(
            array.extent_reference_tokens[axis],
            array.extent_reference_roles[axis],
            role_names,
            "Array extent role",
            "bridge value",
        )
        substitutions.update(
            self._shape_role_substitutions(
                array.extent_callable_tokens[axis],
                array.extent_callable_roles[axis],
                role_names,
                "Array extent callable role",
                "bridge symbol",
            )
        )
        return render_declaration_extent(expression, substitutions, target="fortran")

    @staticmethod
    def _shape_role_substitutions(
        tokens: tuple[str, ...],
        roles: tuple[str, ...],
        role_names: dict[str, str],
        label: str,
        value_label: str,
    ) -> dict[str, str]:
        """Resolve one aligned token-role list or reject a missing bridge producer."""
        substitutions = {}
        for token, role in zip(tokens, roles, strict=True):
            try:
                substitutions[token] = role_names[role]
            except KeyError:
                raise ValueError(f"{label} {role!r} has no {value_label}") from None
        return substitutions

    def _has_optional_arguments(self, plan: FunctionPlan) -> bool:
        """Return whether a function plan contains a nullable-value or descriptor optional argument."""
        return any(
            argument.entrypoint.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
            for argument in plan.arguments
        )

    def _literal_expression(self, value: object) -> str:
        """Render a Python literal as the equivalent Fortran expression used by a planned native call."""
        if isinstance(value, bool):
            return ".true." if value else ".false."
        if isinstance(value, complex):
            return f"({value.real}, {value.imag})"
        return str(value)

    def _entrypoint_function_name(self, plan: FunctionPlan) -> str:
        """Return the shared C-ABI symbol implemented by this adapter."""
        return plan.entrypoint.symbol_name

    def _module_bridge_getter_name(self, plan: ModuleVariablePlan) -> str:
        """Return the shared module-variable getter entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(plan.owner_path, "module:get").symbol_name

    def _module_bridge_setter_name(self, plan: ModuleVariablePlan) -> str:
        """Return the shared module-variable setter entrypoint symbol."""
        return self._generated_support_procedure_entrypoint(plan.owner_path, "module:set").symbol_name

    def _native_function_name(self, plan: FunctionPlan) -> str:
        """Return the in-module alias or standalone symbol selected for the native procedure."""
        return plan.bridge.native_name if plan.bridge.standalone else f"native_{plan.symbol_name}"

    def _native_variable_name(self, plan: ModuleVariablePlan) -> str:
        """Return the imported native alias used by one module variable."""
        return f"native_{plan.symbol_name}"

    def _functions(self, plan: ModulePlan) -> tuple[FunctionPlan, ...]:
        """Flatten namespaces into function plans while preserving module and namespace order."""
        return tuple(function for namespace in plan.namespaces for function in namespace.functions)

    def _variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        """Flatten namespaces into module-variable plans while preserving module and namespace order."""
        return tuple(variable for namespace in plan.namespaces for variable in namespace.variables)

    def _iso_symbol(self, semantic_type_name: str) -> str:
        """Return the iso_c_binding symbol required by one semantic primitive type."""
        if is_boolean_semantic_type_name(semantic_type_name):
            return "c_bool"
        symbols = {
            "Int8": "c_int8_t",
            "Int16": "c_int16_t",
            "Int32": "c_int32_t",
            "Int64": "c_int64_t",
            "Float32": "c_float",
            "Float64": "c_double",
            "Complex64": "c_float_complex",
            "Complex128": "c_double_complex",
            "String": "c_char",
        }
        return symbols[semantic_type_name]

    def _iso_c_symbols(self, plan: ModulePlan) -> tuple[str, ...]:
        """Return the de-duplicated iso_c_binding import set required by the completed module plan."""
        symbols = [
            "c_associated",
            "c_bool",
            "c_char",
            "c_double",
            "c_double_complex",
            "c_f_pointer",
            "c_float",
            "c_float_complex",
            "c_int8_t",
            "c_int16_t",
            "c_int",
            "c_int32_t",
            "c_int64_t",
            "c_loc",
            "c_null_char",
            "c_ptr",
            "c_null_ptr",
            "c_size_t",
            "c_sizeof",
        ]
        if self._uses_c_function_pointer_symbols(plan):
            symbols.extend(("c_funptr", "c_f_procpointer"))
        if self._uses_derived_interop_symbols(plan):
            symbols.extend(("c_funloc", "c_funptr", "c_f_procpointer"))
        return tuple(dict.fromkeys(symbols))

    def _uses_c_function_pointer_symbols(self, plan: ModulePlan) -> bool:
        """Return whether completed module or field descriptor actions require C procedure-pointer support."""
        module_descriptors = any(
            self._uses_module_allocatable_descriptor(variable) for variable in self._variables(plan)
        )
        field_descriptors = any(
            field.access
            in {
                DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR,
                DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE,
            }
            for derived in self._derived_types(plan)
            for field in derived.fields
        )
        return module_descriptors or field_descriptors

    def _uses_derived_interop_symbols(self, plan: ModulePlan) -> bool:
        """Return whether completed derived call or module-variable actions require derived interop support."""
        derived_calls = any(
            argument.derived_call is not None for function in self._functions(plan) for argument in function.arguments
        )
        derived_variables = any(variable.derived is not None for variable in self._variables(plan))
        return derived_calls or derived_variables


if __name__ == "__main__":
    from prik.planning.planner import WrapperPlanner
    from prik.policy.completion import complete_semantic_policies
    from prik.printers.fortran import FortranSourcePrinter
    from prik.semantics.models import SemanticArgument, SemanticFunction, SemanticModule, SemanticType

    module = SemanticModule(
        name="bridge_demo",
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
    bridge = FortranBridgeGenerator()
    bridge.require_supported(plan)
    fortran_module = bridge.visit(plan)

    print("Rendered Fortran bridge source:")
    print(FortranSourcePrinter().doprint(fortran_module))
