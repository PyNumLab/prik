"""Direct recursive Fortran bridge generation from shared wrapper plans."""

from __future__ import annotations

import re

from x2py.semantics.ownership import (
    AssignmentMode,
    CodegenAction,
    NativeBarrierAction,
    ObjectKind,
    PythonBarrierAction,
    SetterAction,
)
from x2py.semantics.metadata import SCALAR_STORAGE_CATEGORY
from x2py.semantics.wrapper_policy import (
    ArgumentHandoffMode,
    ArrayWritebackABI,
    BridgeDataAction,
    CallbackABIKind,
    CallbackResultAction,
    CallbackTransferAction,
    ClassConstructorKind,
    ClassInvocationKind,
    DerivedActualAccess,
    DerivedCallAction,
    DerivedFieldAccessMechanism,
    DerivedNativeHandoff,
    DerivedDummyCategory,
    DerivedObjectStorage,
    DerivedRelease,
    DirectResultABI,
    ExternalDeclarationMode,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorInterop,
    NativeArrayDefaultConstruction,
    NativeArrayOperation,
    NativeArrayResultAllocation,
    NativeDescriptorHandoffABI,
    NativeInvocationKind,
    OptionalMode,
)
from x2py.wrapper_codegen.nodes import (
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
from x2py.wrapper_codegen.naming import NativeSymbolNames
from x2py.wrapper_codegen.plan import (
    ArrayHandoffPlan,
    ArgumentTransferPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    ClassSurfacePlan,
    DatatypeFamily,
    DerivedFieldPlan,
    DerivedMemberPathPlan,
    DerivedTypePlan,
    FunctionPlan,
    ModulePlan,
    ModuleVariablePlan,
    NamespacePlan,
    NativeArrayHandlePlan,
    NativeCallSlotPlan,
    ResultPlan,
)
from x2py.wrapper_codegen.primitive_scalar_types import PrimitiveScalarTypeRegistry
from x2py.wrapper_codegen.visitor import ClassVisitor


class FortranBridgeGenerator(ClassVisitor):
    """Recursively lower bridge plan views directly into Fortran nodes."""

    def __init__(self, *, method_prefix: str | None = None):
        super().__init__(method_prefix=method_prefix)
        self._active_scoped_type_identities: frozenset[tuple[str, str]] = frozenset()

    def require_supported(self, plan: ModulePlan) -> None:
        """Preflight Fortran scalar types after shared plan validation."""
        for derived in self._derived_types(plan):
            self._require_derived_type_supported(derived)
        for function in self._functions(plan):
            self._require_function_supported(function)
        for variable in self._variables(plan):
            self._require_variable_supported(variable)

    def _require_function_supported(self, function: FunctionPlan) -> None:
        """Preflight primitive types after shared plan validation."""
        for argument in function.arguments:
            self._require_argument_supported(argument)
        for result in function.results:
            self._require_backend_type_supported(result.semantic_type_name, result.datatype_family)
        for slot in function.native_call_slots:
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

    def _visit_ModulePlan(self, plan: ModulePlan) -> FortranModule:
        """Return one complete Fortran bridge module."""
        previous_scoped = self._active_scoped_type_identities
        self._active_scoped_type_identities = self._scoped_origin_type_identities(plan)
        try:
            return FortranModule(
                name=f"bind_c_{plan.bridge.owner_path}_wrapper",
                uses=(
                    FortranUse("iso_c_binding", self._iso_c_symbols(plan)),
                    *self._native_module_uses(plan),
                ),
                type_definitions=self._derived_holder_definitions(plan),
                interfaces=(
                    *self._derived_call_interfaces(plan),
                    *self._external_interfaces(plan),
                    *self._module_descriptor_callback_interfaces(plan),
                    *self._derived_array_callback_interfaces(plan),
                    *self._allocator_interfaces(plan),
                ),
                procedures=(
                    *(procedure for namespace in plan.namespaces for procedure in self.visit(namespace)),
                    # Typed derived-field access remains separate from class orchestration.
                    *self._derived_field_procedures(plan),
                    # Native-aware opaque-owner destruction is Phase 8 substrate, not class orchestration.
                    *self._class_constructor_procedures(plan),
                    *(self._derived_destroy_procedure(derived) for derived in self._owned_derived_types(plan)),
                    *(
                        self._allocatable_holder_destroy_procedure(derived)
                        for derived in self._allocatable_holder_types(plan)
                    ),
                    *(
                        self._allocatable_holder_presence_procedure(derived)
                        for derived in self._allocatable_holder_types(plan)
                    ),
                    *(self._pointer_holder_destroy_procedure(derived) for derived in self._pointer_holder_types(plan)),
                    *(self._pointer_holder_presence_procedure(derived) for derived in self._pointer_holder_types(plan)),
                    *(
                        procedure
                        for variable in self._derived_origin_variables(plan)
                        for procedure in self._derived_origin_procedures(variable)
                    ),
                ),
                external_procedures=self._callback_external_adapter_procedures(plan),
            )
        finally:
            self._active_scoped_type_identities = previous_scoped

    def _callback_external_adapter_procedures(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        """Return separately linked callback adapters in stable site order."""
        return tuple(
            self._callback_external_adapter_procedure(callback, plan) for callback in self._callback_sites(plan)
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
            for derived in self._allocatable_holder_types(plan)
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
            for derived in self._pointer_holder_types(plan)
        )
        return (*allocatable, *pointers)

    def _visit_NamespacePlan(self, plan: NamespacePlan) -> tuple[FortranFunction, ...]:
        """Return bridge procedures directly owned by one Python namespace."""
        return (
            *(
                procedure
                for function in plan.functions
                for procedure in (
                    self.visit(function),
                    *self._owned_native_array_result_operations(function),
                    *self._default_native_array_argument_operations(function),
                )
            ),
            *(procedure for variable in plan.variables for procedure in self.visit(variable)),
        )

    def _visit_FunctionPlan(self, plan: FunctionPlan) -> FortranFunction:
        """Recursively assemble one complete bridge procedure."""
        result_name, result_type = self._lower_result(plan)
        owned_direct_result = self._owned_direct_result(plan)
        parameters = tuple(
            parameter
            for argument in sorted(plan.arguments, key=lambda item: item.bridge.abi_position)
            for parameter in self.visit(argument)
        )
        parameters = (
            *parameters,
            *self._native_output_parameters(plan),
            *self._owned_direct_result_parameters(owned_direct_result),
            *self._scalar_descriptor_direct_result_parameters(plan),
        )
        bridge_name = self._bridge_function_name(plan)
        is_subroutine = plan.bridge.native_is_subroutine or owned_direct_result is not None
        function_body, optional_procedures = self._function_body(plan, result_name)
        native_body = (
            *self._derived_pointer_call_initializers(plan),
            *function_body,
            *self._array_writeback_finalizers(plan),
            *self._derived_pointer_call_finalizers(plan),
            *self._required_descriptor_finalizers(plan),
            *self._string_value_finalizers(plan),
            *self._string_address_finalizers(plan),
            *self._direct_result_finalizers(plan),
            *self._native_output_finalizers(plan),
        )
        call_body = self._derived_result_execution(plan, result_name, native_body)
        derived_body, internal_procedures = self._derived_call_execution(plan, call_body)
        return FortranFunction(
            name=bridge_name,
            parameters=parameters,
            result_name=result_name,
            result_type=result_type,
            bind_name=bridge_name,
            declarations=(
                *self._callback_external_declarations(plan),
                *self._native_external_declarations(plan),
                *self._optional_declarations(plan),
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
                *self._descriptor_initializers(plan),
                *self._required_descriptor_initializers(plan),
                *self._opaque_address_initializers(plan),
                *self._array_initializers(plan),
                *self._raw_array_address_initializers(plan),
                *self._string_value_initializers(plan),
                *self._string_address_initializers(plan),
                *derived_body,
            ),
            is_subroutine=is_subroutine,
            internal_procedures=(
                *optional_procedures,
                *self._direct_result_internal_procedures(plan),
                *internal_procedures,
            ),
        )

    # Immediate callback adapters.
    def _callback_external_adapter_procedure(
        self,
        callback: CallbackHandoffPlan,
        plan: ModulePlan,
    ) -> FortranFunction:
        """Adapt one native callback through a separately declared external procedure."""
        result = callback.result.transfer
        is_subroutine = callback.result.action is CallbackResultAction.RETURN_VOID
        trampoline_name = f"{callback.trampoline_symbol}_call"
        return FortranFunction(
            name=callback.adapter_symbol,
            parameters=tuple(self._callback_native_parameter(transfer) for transfer in callback.arguments),
            result_name=None if is_subroutine else "callback_result",
            result_type=None if is_subroutine else self._callback_native_result_type(result),
            uses=self._callback_external_adapter_uses(callback, plan),
            implicit_none=True,
            interfaces=(
                FortranInterface(
                    (
                        self._callback_c_interface(
                            callback,
                            name=trampoline_name,
                            bind_name=callback.trampoline_symbol,
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

    def _callback_external_adapter_uses(
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
            symbol for symbol in (*native_imports, *adapter_imports) if not symbol.startswith("x2py_type_")
        )
        derived_imports = tuple(symbol for symbol in native_imports if symbol.startswith("x2py_type_"))
        return (
            FortranUse(
                "iso_c_binding",
                tuple(dict.fromkeys((*iso_imports, *self._callback_c_imports(callback)))),
            ),
            *(
                (
                    FortranUse(
                        f"bind_c_{plan.bridge.owner_path}_wrapper",
                        derived_imports,
                    ),
                )
                if derived_imports
                else ()
            ),
        )

    def _callback_external_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Declare external callback adapters from completed callback policy."""
        declarations = []
        for callback in (
            argument.callback
            for argument in sorted(plan.arguments, key=lambda item: item.native_position)
            if argument.callback is not None
        ):
            if callback.declaration_mode is ExternalDeclarationMode.EXPLICIT_INTERFACE:
                declarations.append(
                    FortranDeclaration(
                        callback.adapter_symbol,
                        f"procedure({self._callback_imported_prototype_symbol(callback)})",
                    )
                )
                continue
            if callback.declaration_mode is not ExternalDeclarationMode.IMPLICIT_EXTERNAL:
                raise ValueError(
                    f"Callback {callback.owner_path!r} has unsupported declaration mode {callback.declaration_mode!r}"
                )
            if callback.result.action is CallbackResultAction.RETURN_VOID:
                declarations.append(FortranDeclaration(callback.adapter_symbol, "external"))
                continue
            declarations.append(
                FortranDeclaration(
                    callback.adapter_symbol,
                    self._callback_native_result_type(callback.result.transfer),
                    ("external",),
                )
            )
        return tuple(declarations)

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
        return re.sub(r"\W", "_", transfer.name).casefold()

    def _callback_shape(self, transfer: CallbackTransferPlan) -> str:
        if transfer.array is None or transfer.array.rank is None:
            raise ValueError(f"Callback array transfer {transfer.owner_path!r} has no shape plan")
        return ", ".join(transfer.array.shape)

    def _callback_address_source(self, transfer: CallbackTransferPlan) -> str:
        if transfer.adapter_action in {
            CallbackTransferAction.COPY_IN,
            CallbackTransferAction.COPY_OUT,
            CallbackTransferAction.COPY_IN_OUT,
        }:
            return self._callback_storage_name(transfer)
        return self._callback_parameter_base_name(transfer)

    def _callback_storage_name(self, transfer: CallbackTransferPlan) -> str:
        return f"{self._callback_parameter_base_name(transfer)}_callback_storage"

    # Scalar-derived carrier preparation, invocation, and restoration.
    def _derived_arguments(self, plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
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
        declarations = [FortranDeclaration("x2py_derived_ready", "logical")]
        for argument in arguments:
            name = argument.bridge.native_name.lower()
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
                    FortranDeclaration(f"{name}_scoped_proc", "procedure(x2py_derived_scoped)", ("pointer",)),
                    FortranDeclaration(
                        f"{name}_checkout_proc",
                        "procedure(x2py_derived_checkout)",
                        ("pointer",),
                    ),
                    FortranDeclaration(
                        f"{name}_restore_proc",
                        "procedure(x2py_derived_restore)",
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
    ) -> tuple[tuple, tuple[FortranFunction, ...]]:
        """Prepare all carriers, invoke once, then restore in reverse order."""
        arguments = self._derived_arguments(plan)
        if not arguments:
            return call_body, ()
        body = list(self._derived_call_preparation_nodes(arguments))
        scoped = self._scoped_derived_arguments(arguments)
        invocation, internal = self._derived_call_invocation(arguments, scoped, call_body)
        body.append(invocation)
        body.extend(self._derived_transaction_restoration(argument) for argument in reversed(arguments))
        body.extend(node for argument in arguments for node in self._derived_argument_output_and_cleanup(argument))
        return tuple(body), internal

    def _derived_call_preparation_nodes(self, arguments: tuple[ArgumentTransferPlan, ...]) -> tuple:
        return (
            *(node for argument in arguments for node in self._derived_argument_initializers(argument)),
            FortranAssignment("x2py_derived_ready", CodeExpression(".true.")),
            *(self._derived_argument_preparation(argument) for argument in arguments),
            *(self._derived_transaction_acquisition(arguments, index) for index in range(len(arguments))),
        )

    def _scoped_derived_arguments(
        self,
        arguments: tuple[ArgumentTransferPlan, ...],
    ) -> tuple[ArgumentTransferPlan, ...]:
        return tuple(
            argument
            for argument in arguments
            if self._derived_argument_uses_access(argument, DerivedActualAccess.SCOPED_ADDRESS)
            and self._has_scoped_origin_for_argument(argument)
        )

    @staticmethod
    def _derived_argument_uses_access(argument: ArgumentTransferPlan, access: DerivedActualAccess) -> bool:
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
        name = argument.bridge.native_name.lower()
        nodes = [
            FortranAssignment(f"bound_{name}_status", CodeExpression("0_c_int")),
            FortranAssignment(f"{name}_created", CodeExpression(".false.")),
            FortranAssignment(f"{name}_acquired", CodeExpression(".false.")),
            FortranAssignment(f"{name}_transaction_address", CodeExpression("c_null_ptr")),
            FortranNullify(name),
            FortranNullify(f"{name}_call_pointer"),
        ]
        if argument.bridge.descriptor_output_role is not None:
            nodes.extend(
                (
                    FortranAssignment(f"bound_{name}_output", CodeExpression("c_null_ptr")),
                    FortranAssignment(f"bound_{name}_output_present", CodeExpression("0_c_int")),
                )
            )
        return tuple(nodes)

    def _derived_argument_preparation(self, argument: ArgumentTransferPlan) -> FortranSelectCase:
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
            if code in builders and (code != 2 or self._has_scoped_origin_for_argument(argument))
        )
        cases.append(
            FortranCase(
                None,
                (FortranAssignment(self._derived_status_parameter(argument), CodeExpression("6_c_int")),),
            )
        )
        return FortranSelectCase(
            CodeExpression(f"bound_{argument.bridge.native_name.lower()}_access"),
            tuple(cases),
        )

    def _derived_direct_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        if argument.polymorphic is not None:
            return self._polymorphic_direct_preparation(argument)
        name = argument.bridge.native_name.lower()
        return (
            FortranIf(
                CodeExpression(f"c_associated(bound_{name})"),
                body=(FortranCall("c_f_pointer", (CodeExpression(f"bound_{name}"), CodeExpression(name))),),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
            ),
        )

    def _polymorphic_direct_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        """Associate one carrier with the concrete type selected by the binding."""
        name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
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
        if argument.derived_call.dummy_category in {
            DerivedDummyCategory.ALLOCATABLE,
            DerivedDummyCategory.ALLOCATABLE_TARGET,
        }:
            return ()
        name = argument.bridge.native_name.lower()
        return (
            FortranIf(
                CodeExpression(f"allocated({name}_allocatable_holder%value)"),
                body=(FortranPointerAssignment(name, CodeExpression(f"{name}_allocatable_holder%value")),),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
            ),
        )

    def _derived_pointer_holder_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        name = argument.bridge.native_name.lower()
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
        if argument.derived_call.dummy_category is DerivedDummyCategory.POINTER:
            return ()
        name = argument.bridge.native_name.lower()
        return (
            FortranIf(
                CodeExpression(f"associated({name}_pointer_holder%value)"),
                body=(FortranPointerAssignment(name, CodeExpression(f"{name}_pointer_holder%value")),),
                else_body=(FortranAssignment(f"bound_{name}_status", CodeExpression("1_c_int")),),
            ),
        )

    def _derived_allocatable_transaction_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        return self._derived_transaction_operation_preparation(argument)

    def _derived_pointer_transaction_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        return self._derived_transaction_operation_preparation(argument)

    def _derived_transaction_operation_preparation(self, argument: ArgumentTransferPlan) -> tuple:
        name = argument.bridge.native_name.lower()
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
        argument = arguments[index]
        name = argument.bridge.native_name.lower()
        acquisition = FortranSelectCase(
            CodeExpression(f"bound_{name}_access"),
            (
                FortranCase(5, self._one_derived_transaction_acquisition(argument, allocatable=True)),
                FortranCase(6, self._one_derived_transaction_acquisition(argument, allocatable=False)),
                FortranCase(None, ()),
            ),
        )
        return FortranIf(
            CodeExpression("x2py_derived_ready"),
            body=(
                FortranIf(
                    CodeExpression(f"bound_{name}_status == 0_c_int"),
                    body=(
                        acquisition,
                        FortranIf(
                            CodeExpression(f"bound_{name}_status /= 0_c_int"),
                            body=(FortranAssignment("x2py_derived_ready", CodeExpression(".false.")),),
                        ),
                    ),
                    else_body=(FortranAssignment("x2py_derived_ready", CodeExpression(".false.")),),
                ),
            ),
        )

    def _one_derived_transaction_acquisition(
        self,
        argument: ArgumentTransferPlan,
        *,
        allocatable: bool,
    ) -> tuple:
        name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
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
        procedures = []
        for index, argument in enumerate(scoped):
            name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
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
            prior = candidate.bridge.native_name.lower()
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
        return tuple(
            node
            for argument in self._derived_arguments(plan)
            if argument.derived_call.dummy_category is DerivedDummyCategory.POINTER
            for node in self._one_derived_pointer_call_initializer(argument)
        )

    def _one_derived_pointer_call_initializer(self, argument: ArgumentTransferPlan) -> tuple:
        name = argument.bridge.native_name.lower()
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
        return tuple(
            node
            for argument in self._derived_arguments(plan)
            if argument.derived_call.dummy_category is DerivedDummyCategory.POINTER
            for node in self._one_derived_pointer_call_finalizer(argument)
        )

    def _one_derived_pointer_call_finalizer(self, argument: ArgumentTransferPlan) -> tuple:
        name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
        nodes = []
        if argument.bridge.descriptor_output_role is not None:
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
        name = argument.bridge.native_name.lower()
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
        return "x2py_derived_ready" if arguments else ".true."

    @staticmethod
    def _derived_status_parameter(argument: ArgumentTransferPlan) -> str:
        return f"bound_{argument.bridge.native_name.lower()}_status"

    @staticmethod
    def _derived_step_name(index: int) -> str:
        return f"x2py_derived_step_{index}"

    @staticmethod
    def _derived_consumer_name(index: int) -> str:
        return f"x2py_derived_consumer_{index}"

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
        return "result", self._bridge_result_type(plan, result)

    def _owned_direct_result_parameters(
        self,
        result: ResultPlan | None,
    ) -> tuple[FortranParameter, ...]:
        """Expose persistent binding-owned descriptor storage as one output dummy."""
        if result is None:
            return ()
        handle = result.native_array_handle
        if handle is None or handle.array.rank is None:
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

    def _scalar_descriptor_direct_result_parameters(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranParameter, ...]:
        """Expose runtime metadata associated with a direct descriptor result."""
        result = self._direct_result(plan)
        if result is None or result.scalar_descriptor is None:
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
            handle = result.native_array_handle
            if handle is None:
                continue
            for operation in handle.operations:
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
            for operation in handle.default_handle.operations:
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
        """Return the C-visible typed operation name for one owned result."""
        preferred = result.bridge.native_name or "result"
        owner = NativeSymbolNames.compact(result.owner_path, preferred, limit=38)
        return f"bind_c_owned_{owner}_{operation.value}"

    def _visit_ModuleVariablePlan(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Lower bridge-owned getter and setter actions into procedures."""
        if plan.binding.getter_action is ModuleGetterAction.NATIVE_ARRAY_HANDLE:
            return self._lower_module_native_array_operations(plan)
        return (
            *self._lower_module_getter(plan),
            *self._lower_module_setter(plan),
        )

    def _lower_module_getter(self, plan: ModuleVariablePlan) -> tuple[FortranFunction, ...]:
        """Dispatch one completed bridge getter action explicitly."""
        action = plan.bridge.getter_action
        match action:
            case ModuleGetterAction.CONSTANT_VALUE:
                return self._lower_module_getter_constant_value(plan)
            case ModuleGetterAction.DIRECT_VALUE:
                return self._lower_module_getter_direct_value(plan)
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
        return tuple(variable for variable in self._variables(plan) if variable.derived is not None)

    def _scoped_origin_type_identities(self, plan: ModulePlan) -> frozenset[tuple[str, str]]:
        """Return derived identities with at least one scoped module-origin producer."""
        return frozenset(
            variable.derived.handoff.type_identity
            for variable in self._derived_origin_variables(plan)
            if self._derived_origin_supports(variable, "scoped")
        )

    def _has_scoped_origin_for_argument(self, argument: ArgumentTransferPlan) -> bool:
        """Return whether this bridge module can produce a scoped origin for the argument type."""
        return argument.derived is not None and argument.derived.type_identity in self._active_scoped_type_identities

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
        invoke = CodeExpression(f"x2py_invoke_origin({native})")
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
            name="x2py_invoke_origin",
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
            declarations=(FortranDeclaration("consume", "procedure(x2py_derived_consumer)", ("pointer",)),),
            body=tuple(body),
            internal_procedures=(internal,),
        )

    def _derived_origin_checkout_procedure(self, variable: ModuleVariablePlan) -> FortranFunction:
        storage = variable.derived.handoff.storage
        return (
            self._derived_origin_allocatable_checkout(variable)
            if storage in {DerivedObjectStorage.MODULE_ALLOCATABLE, DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET}
            else self._derived_origin_pointer_checkout(variable)
        )

    def _derived_origin_allocatable_checkout(self, variable: ModuleVariablePlan) -> FortranFunction:
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
        storage = variable.derived.handoff.storage
        return (
            self._derived_origin_allocatable_restore(variable)
            if storage in {DerivedObjectStorage.MODULE_ALLOCATABLE, DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET}
            else self._derived_origin_pointer_restore(variable)
        )

    def _derived_origin_allocatable_restore(self, variable: ModuleVariablePlan) -> FortranFunction:
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

    @staticmethod
    def _derived_origin_supports(variable: ModuleVariablePlan, operation: str) -> bool:
        storage = variable.derived.handoff.storage
        support = {
            DerivedObjectStorage.MODULE_PROXY: {"scoped"},
            DerivedObjectStorage.MODULE_TARGET: {"address"},
            DerivedObjectStorage.MODULE_ALLOCATABLE: {"present", "scoped", "checkout", "restore"},
            DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET: {
                "present",
                "address",
                "checkout",
                "restore",
            },
            DerivedObjectStorage.MODULE_POINTER: {"present", "scoped", "checkout", "restore"},
        }
        return operation in support.get(storage, set())

    @staticmethod
    def _derived_origin_symbol(variable: ModuleVariablePlan) -> str:
        return NativeSymbolNames.compact(variable.owner_path, variable.symbol_name)

    def _derived_origin_bridge_name(self, variable: ModuleVariablePlan, operation: str) -> str:
        return f"bind_c_x2py_origin_{self._derived_origin_symbol(variable)}_{operation}"

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
                    FortranDeclaration("x2py_allocation_status", "integer(c_int)"),
                ),
                body=(
                    FortranAssignment("result", CodeExpression("c_null_ptr")),
                    FortranAllocate(local, status="x2py_allocation_status"),
                    FortranIf(
                        CodeExpression("x2py_allocation_status == 0"),
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
        handle = plan.native_array_handle
        if handle is None:
            raise ValueError(f"Module handle {plan.owner_path!r} has no operation plan")
        procedures = []
        for operation in handle.operations:
            procedure = self._lower_module_native_array_operation(plan, operation)
            if procedure is not None:
                procedures.append(procedure)
        return tuple(procedures)

    def _lower_module_native_array_operation(
        self,
        plan: ModuleVariablePlan,
        operation: NativeArrayOperation,
    ) -> FortranFunction | None:
        """Dispatch one operation using only the completed typed operation selector."""
        if operation in {
            NativeArrayOperation.NATIVE_BYTE_ORDER,
            NativeArrayOperation.ALIGNED,
            NativeArrayOperation.WRITEABLE,
            NativeArrayOperation.LAYOUT,
        }:
            return None
        if operation is NativeArrayOperation.TO_NUMPY:
            return None
        return self._lower_module_native_array_bridge_operation(plan, operation)

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
        """Return the C-visible operation name derived from plan ownership."""
        return f"bind_c_{plan.symbol_name}_{operation.value}"

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
        presence = "allocated" if plan.bridge.descriptor_kind == "allocatable" else "associated"
        return self._lower_nullable_module_getter(plan, f"{presence}({self._native_variable_name(plan)})")

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
        mode = plan.bridge.optional_mode
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
        name = plan.bridge.native_name.lower()
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
                if plan.bridge.descriptor_output_role is not None
                else ()
            ),
        )

    @staticmethod
    def _is_character_buffer_argument(plan: ArgumentTransferPlan) -> bool:
        return (
            plan.object_kind is ObjectKind.STRING and plan.bridge.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
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
        name = plan.bridge.native_name.lower()
        parameters = [FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",))]
        if plan.bridge.descriptor_output_role is not None:
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
        if plan.bridge.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            if mode not in {OptionalMode.REQUIRED, OptionalMode.DESCRIPTOR}:
                raise ValueError(f"Unsupported Fortran descriptor presence mode for {plan.owner_path!r}: {mode!r}")
            return self._lower_argument_native_array_descriptor(plan)
        if mode not in {OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE}:
            raise ValueError(f"Unsupported Fortran array presence mode for {plan.owner_path!r}: {mode!r}")
        if plan.bridge.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._lower_argument_array_buffer(plan)
        if plan.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS:
            return self._lower_opaque_array_argument(plan, mode)
        raise ValueError(f"Unsupported Fortran array handoff for {plan.owner_path!r}: {plan.bridge.handoff_mode!r}")

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
        raise ValueError(f"Unsupported Fortran array handoff for {plan.owner_path!r}: {plan.bridge.handoff_mode!r}")

    def _is_opaque_array_required_argument(self, plan: ArgumentTransferPlan) -> bool:
        """Return whether a required array-shaped argument uses an opaque address."""
        return bool(
            plan.binding.python_action is PythonBarrierAction.RAW_ADDRESS or self._is_scalar_storage_array(plan.array)
        )

    # Native-array-handle bridge parameters.
    def _lower_argument_native_array_descriptor(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Receive one standard descriptor as a typed allocatable/pointer dummy."""
        handle = plan.native_array_handle
        name = plan.bridge.native_name.lower()
        attribute = "allocatable" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "pointer"
        parameters = [
            FortranParameter(
                name,
                self._native_array_argument_element_type(plan),
                (attribute, self._array_dimension_attribute(handle.array.rank)),
            )
        ]
        if plan.bridge.optional_mode is OptionalMode.DESCRIPTOR:
            parameters.append(FortranParameter(f"bound_{name}_present", "type(c_ptr)", ("value",)))
        return tuple(parameters)

    def _native_array_argument_element_type(self, plan: ArgumentTransferPlan) -> str:
        """Return one numeric or deferred-character descriptor dummy type."""
        if plan.datatype_family is DatatypeFamily.STRING:
            return "character(kind=c_char, len=:)"
        return PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name).fortran_spelling

    def _lower_argument_required(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Dispatch one required bridge parameter from its completed ABI shape."""
        mode = plan.bridge.handoff_mode
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
        name = plan.bridge.native_name.lower()
        return (FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),)

    # String argument lowering.
    def _lower_argument_string_value(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranParameter, ...]:
        """Receive one C UTF-8 payload address and its runtime byte length."""
        name = plan.bridge.native_name.lower()
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
        name = plan.bridge.native_name.lower()
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
        name = plan.bridge.native_name.lower()
        return (FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),)

    def _lower_argument_descriptor(self, plan: ArgumentTransferPlan) -> tuple[FortranParameter, ...]:
        """Return nullable value and explicit presence pointer parameters."""
        name = plan.bridge.native_name.lower()
        return (
            FortranParameter(f"bound_{name}", "type(c_ptr)", ("value",)),
            FortranParameter(f"bound_{name}_present", "type(c_ptr)", ("value",)),
        )

    def _parameter(self, plan: ArgumentTransferPlan, attributes: tuple[str, ...]) -> FortranParameter:
        scalar_type = PrimitiveScalarTypeRegistry.type_for(plan.semantic_type_name)
        return FortranParameter(plan.bridge.native_name.lower(), scalar_type.fortran_spelling, attributes)

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
            for argument in sorted(plan.arguments, key=lambda item: item.bridge.abi_position)
            if argument.derived_call is not None
            and argument.bridge.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
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
        """Return polymorphic inputs in bridge ABI order."""
        return tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.bridge.abi_position)
            if argument.polymorphic is not None
        )

    @staticmethod
    def _assumed_rank_arguments(plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return assumed-rank arrays in bridge ABI order."""
        return tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.bridge.abi_position)
            if argument.array is not None and argument.array.rank is None
        )

    @staticmethod
    def _non_derived_optional_arguments(plan: FunctionPlan) -> tuple[ArgumentTransferPlan, ...]:
        """Return optional arguments handled by the ordinary presence tree."""
        return tuple(
            argument
            for argument in sorted(plan.arguments, key=lambda item: item.bridge.abi_position)
            if argument.bridge.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
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
        name = argument.bridge.native_name.lower()
        return FortranSelectCase(CodeExpression(f"bound_{name}_polymorphic"), tuple(cases))

    @staticmethod
    def _polymorphic_variant_name(argument: ArgumentTransferPlan, abi_code: int) -> str:
        """Name one bridge-local typed pointer from its stable plan code."""
        return f"{argument.bridge.native_name.lower()}_polymorphic_{abi_code}"

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
        return f"x2py_optional_{argument.bridge.native_name.lower()}"

    @staticmethod
    def _derived_optional_step_name(index: int) -> str:
        return f"x2py_derived_optional_step_{index}"

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
        return f"{expression}%{class_call.type_bound_name}", receiver.native_call_slot.native_position

    @staticmethod
    def _is_pointer_derived_holder_result(result: ResultPlan | None) -> bool:
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
        expressions = dict(self._visible_native_argument_entries(plan, present, replacements))
        expressions.update(
            (slot.native_position, CodeExpression(self._literal_expression(slot.literal_value)))
            for slot in plan.native_call_slots
            if slot.source_kind == "literal"
        )
        expressions.update(self._hidden_native_result_entries(plan))
        return tuple(
            expressions[slot.native_position]
            for slot in sorted(plan.native_call_slots, key=lambda item: item.native_position)
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
                argument.bridge.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
                and argument.owner_path not in present
            ):
                continue
            expression = replacements.get(argument.owner_path, self._native_argument_expression(argument))
            if has_optional:
                expression = f"{argument.bridge.native_name}={expression}"
            entries.append((argument.native_call_slot.native_position, CodeExpression(expression)))
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
                for argument in sorted(plan.arguments, key=lambda item: item.bridge.abi_position)
                if argument.bridge.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
                and argument.derived_call is None
            )
            if optional:
                return self._optional_call_tree(plan, optional, 0, present, result_name, replacements)
            return self._native_invocation(plan, present, result_name, replacements)
        argument = arguments[index]
        name = argument.bridge.native_name.lower()
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
        for slot in plan.native_call_slots:
            if slot.source_kind != "result":
                continue
            expression = self._native_output_value_name(slot)
            if self._has_optional_arguments(plan):
                expression = f"{slot.native_name}={expression}"
            entries.append((slot.native_position, CodeExpression(expression)))
        return tuple(entries)

    def _native_argument_expression(self, plan: ArgumentTransferPlan) -> str:
        name = plan.bridge.native_name.lower()
        if plan.callback is not None:
            return plan.callback.adapter_symbol
        if plan.derived_call is not None:
            if plan.derived_call.dummy_category in {
                DerivedDummyCategory.ALLOCATABLE,
                DerivedDummyCategory.ALLOCATABLE_TARGET,
            }:
                return f"{name}_allocatable_holder%value"
            if plan.derived_call.dummy_category is DerivedDummyCategory.POINTER:
                return f"{name}_call_pointer"
            return name
        if plan.bridge.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return self._array_native_argument_expression(plan)
        if plan.bridge.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return name
        if plan.bridge.optional_mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            return f"{name}_descriptor"
        return name

    def _presence_condition(self, plan: ArgumentTransferPlan) -> str:
        name = plan.bridge.native_name.lower()
        if plan.derived_call is not None:
            return f"bound_{name}_access /= 0_c_int"
        suffix = "_present" if plan.bridge.optional_mode is OptionalMode.DESCRIPTOR else ""
        return f"c_associated(bound_{name}{suffix})"

    def _present_preparation(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranAssignment | FortranPointerAssignment | FortranCall | FortranIf, ...]:
        """Dispatch only the bridge data action completed before lowering."""
        if plan.derived_call is not None:
            return ()
        if plan.bridge.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
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
        name = plan.bridge.native_name.lower()
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
        if plan.bridge.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
            return ()
        if plan.bridge.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER:
            return (self._array_pointer_initializer(plan),)
        if plan.bridge.optional_mode is OptionalMode.NULLABLE_VALUE:
            return (
                FortranCall(
                    "c_f_pointer",
                    (CodeExpression(f"bound_{name}"), CodeExpression(name)),
                ),
            )
        if plan.bridge.optional_mode not in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            raise ValueError(f"Associated-view preparation requires an optional argument: {plan.owner_path!r}")
        if plan.native_call_slot.value_kind != "pointer":
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
        if plan.bridge.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER:
            return self._string_value_initializer_nodes(plan)
        if self._is_derived_value_copy(plan):
            name = plan.bridge.native_name.lower()
            return (
                FortranCall(
                    "c_f_pointer",
                    (CodeExpression(f"bound_{name}"), CodeExpression(name)),
                ),
                FortranAssignment(f"{name}_value", CodeExpression(name)),
            )
        if plan.bridge.optional_mode not in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
            raise ValueError(f"Representation copy requires descriptor policy: {plan.owner_path!r}")
        if plan.native_call_slot.value_kind != "allocatable":
            raise ValueError(f"Representation copy requires allocatable policy: {plan.owner_path!r}")
        name = plan.bridge.native_name.lower()
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
        mode = argument.bridge.optional_mode
        if mode is OptionalMode.REQUIRED or argument.bridge.handoff_mode in {
            ArgumentHandoffMode.NATIVE_DESCRIPTOR,
            ArgumentHandoffMode.CHARACTER_BUFFER,
            ArgumentHandoffMode.ARRAY_BUFFER,
        }:
            return ()
        name = argument.bridge.native_name.lower()
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
        descriptor_attribute = "pointer" if argument.native_call_slot.value_kind == "pointer" else "allocatable"
        declarations.append(
            FortranDeclaration(f"{name}_descriptor", scalar_type.fortran_spelling, (descriptor_attribute,))
        )
        if mode is OptionalMode.REQUIRED_DESCRIPTOR and argument.bridge.descriptor_output_role is not None:
            declarations.append(FortranDeclaration(f"{name}_output", scalar_type.fortran_spelling, ("pointer",)))
        return tuple(declarations)

    def _opaque_address_declarations(self, plan: FunctionPlan) -> tuple[FortranDeclaration, ...]:
        """Return typed pointer locals for required opaque scalar addresses."""
        return tuple(
            declaration
            for argument in plan.arguments
            if (
                argument.derived_call is None
                and argument.bridge.optional_mode is OptionalMode.REQUIRED
                and argument.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
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
                        argument.bridge.native_name.lower(),
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
        name = argument.bridge.native_name.lower()
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
                and argument.bridge.optional_mode is OptionalMode.REQUIRED
                and argument.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
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
        name = argument.bridge.native_name.lower()
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
        """Declare typed pointer views for ordinary array buffers."""
        declarations = []
        for argument in plan.arguments:
            if argument.bridge.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER:
                continue
            array = argument.array
            if array is None:
                raise ValueError(f"Array argument {argument.owner_path!r} is missing its handoff")
            if array.rank is None:
                declarations.extend(self._assumed_rank_array_declarations(argument))
            else:
                declarations.append(
                    FortranDeclaration(
                        self._array_pointer_name(argument),
                        self._array_element_fortran_type(argument),
                        ("pointer", self._array_dimension_attribute(array.rank)),
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
            if argument.bridge.optional_mode is OptionalMode.REQUIRED:
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
        name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
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
        return f"{argument.bridge.native_name.lower()}_logical_bytes"

    def _array_initializers(self, plan: FunctionPlan) -> tuple[FortranCall, ...]:
        """Associate each completed ordinary array data/extent handoff."""
        initializers = []
        for argument in plan.arguments:
            if argument.bridge.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER:
                continue
            if argument.bridge.optional_mode is not OptionalMode.REQUIRED:
                continue
            if argument.array is not None and argument.array.rank is None:
                continue
            initializers.append(self._array_pointer_initializer(argument))
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
        shape = list(self._array_shape_from_roles(array, plan.arguments))
        if array.native_order == "ORDER_C":
            shape.reverse()
        name = argument.bridge.native_name.lower()
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
            and argument.binding.python_action is PythonBarrierAction.RAW_ADDRESS
            and argument.bridge.native_action is NativeBarrierAction.PASS_RAW_ADDRESS
            and argument.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
            and argument.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW
        )

    def _array_pointer_initializer(self, argument: ArgumentTransferPlan) -> FortranCall:
        """Associate one fixed-rank array pointer using planned base extents."""
        array = argument.array
        if array is None or array.rank is None:
            raise ValueError(f"Array argument {argument.owner_path!r} requires a concrete rank")
        name = argument.bridge.native_name.lower()
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

    def _assumed_rank_array_declarations(
        self,
        argument: ArgumentTransferPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare one readable typed pointer local for every supported runtime rank."""
        name = argument.bridge.native_name.lower()
        element_type = self._array_element_fortran_type(argument)
        return tuple(
            FortranDeclaration(
                f"{name}_rank_{rank}",
                element_type,
                ("pointer", self._array_dimension_attribute(rank)),
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
        name = argument.bridge.native_name.lower()
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
        name = argument.bridge.native_name.lower()
        return f"{name}_base" if argument.array is not None and argument.array.contiguous is False else name

    def _array_native_argument_expression(self, argument: ArgumentTransferPlan) -> str:
        """Pass a dense pointer or the explicitly planned positive-stride slice."""
        array = argument.array
        if array is None:
            raise ValueError(f"Array argument {argument.owner_path!r} has no handoff spec")
        name = argument.bridge.native_name.lower()
        if array.rank is None:
            return name
        pointer_name = self._array_pointer_name(argument)
        if array.contiguous is not False:
            return pointer_name
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
            name = argument.bridge.native_name.lower()
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
            name = argument.bridge.native_name.lower()
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
            name = argument.bridge.native_name.lower()
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
            and argument.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
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
            if argument.bridge.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            name = argument.bridge.native_name.lower()
            declarations.extend(
                (
                    FortranDeclaration(
                        f"{name}_bytes",
                        "character(kind=c_char)",
                        ("pointer", "dimension(:)"),
                    ),
                    FortranDeclaration(name, f"character(kind=c_char, len={name}_length)"),
                )
            )
        return tuple(declarations)

    def _string_value_initializers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Associate and copy C bytes only for completed representation-copy inputs."""
        nodes = []
        for argument in plan.arguments:
            if argument.bridge.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            if argument.bridge.optional_mode is not OptionalMode.REQUIRED:
                continue
            if argument.bridge.data_action is not BridgeDataAction.COPY_REPRESENTATION:
                raise ValueError(f"String input {argument.owner_path!r} is missing representation-copy policy")
            nodes.extend(self._string_value_initializer_nodes(argument))
        return tuple(nodes)

    def _string_value_initializer_nodes(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranCall | FortranAssignment, ...]:
        """Associate and materialize one present string payload."""
        name = plan.bridge.native_name.lower()
        extent = f"{name}_length + 1" if plan.bridge.codegen_action is CodegenAction.COPY_IN_OUT else f"{name}_length"
        source = (
            f"{name}_bytes(1:{name}_length)"
            if plan.bridge.codegen_action is CodegenAction.COPY_IN_OUT
            else f"{name}_bytes"
        )
        return (
            FortranCall(
                "c_f_pointer",
                (
                    CodeExpression(f"bound_{name}"),
                    CodeExpression(f"{name}_bytes"),
                    CodeExpression(f"[{extent}]"),
                ),
            ),
            FortranAssignment(name, CodeExpression(f"transfer({source}, {name})")),
        )

    def _string_value_finalizers(
        self,
        plan: FunctionPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Dispatch completed post-call string copyback actions."""
        nodes = []
        for argument in plan.arguments:
            if argument.bridge.handoff_mode is not ArgumentHandoffMode.CHARACTER_BUFFER:
                continue
            action = argument.bridge.codegen_action
            if action is CodegenAction.CALL_LOCAL_INPUT:
                continue
            if action is CodegenAction.COPY_IN_OUT:
                copyback = self._lower_argument_string_copyback(argument)
                if argument.bridge.optional_mode is OptionalMode.NULLABLE_VALUE:
                    name = argument.bridge.native_name.lower()
                    nodes.append(FortranIf(CodeExpression(f"c_associated(bound_{name})"), body=copyback))
                else:
                    nodes.extend(copyback)
                continue
            raise ValueError(f"Unsupported Fortran string finalizer for {argument.owner_path!r}: {action!r}")
        return tuple(nodes)

    def _lower_argument_string_copyback(
        self,
        plan: ArgumentTransferPlan,
    ) -> tuple[FortranAssignment, ...]:
        """Copy one complete native character value back to binding storage."""
        name = plan.bridge.native_name.lower()
        return (
            FortranAssignment(
                f"{name}_bytes(1:{name}_length)",
                CodeExpression(f"transfer({name}, {name}_bytes(1:{name}_length))"),
            ),
            FortranAssignment(f"{name}_bytes({name}_length + 1)", CodeExpression("c_null_char")),
        )

    def _descriptor_initializers(self, plan: FunctionPlan) -> tuple[FortranPointerAssignment, ...]:
        return tuple(
            FortranPointerAssignment(
                f"{argument.bridge.native_name.lower()}_descriptor",
                CodeExpression("null()"),
            )
            for argument in plan.arguments
            if (
                argument.bridge.optional_mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}
                and argument.bridge.handoff_mode is not ArgumentHandoffMode.NATIVE_DESCRIPTOR
                and argument.native_call_slot.value_kind == "pointer"
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
            if argument.bridge.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR and argument.derived_call is None
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
            if argument.bridge.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR
            and argument.bridge.descriptor_output_role is not None
            and argument.derived_call is None
        )

    def _required_descriptor_finalizer(self, argument: ArgumentTransferPlan) -> FortranIf:
        """Lower one planned required-descriptor copy-out ABI."""
        name = argument.bridge.native_name.lower()
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
        inquiry = "associated" if argument.native_call_slot.value_kind == "pointer" else "allocated"
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

    def _native_output_parameters(self, plan: FunctionPlan) -> tuple[FortranParameter, ...]:
        """Return bridge ABI parameters for every typed native result slot."""
        parameters = []
        for slot in sorted(plan.native_call_slots, key=lambda item: item.native_position):
            if slot.source_kind != "result":
                continue
            parameters.extend(self._native_output_parameters_for_slot(slot))
        return tuple(parameters)

    def _native_output_parameters_for_slot(self, slot: NativeCallSlotPlan) -> tuple[FortranParameter, ...]:
        """Lower one completed result-slot kind into bridge ABI parameters."""
        if slot.scalar_descriptor is not None:
            return self._scalar_descriptor_output_parameters(slot)
        if self._is_owned_native_array_slot(slot):
            return self._owned_native_array_output_parameters(slot)
        if slot.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return (FortranParameter(slot.native_name.lower(), "type(c_ptr)"),)
        if slot.semantic_type_name is None:
            raise ValueError(f"Missing native output datatype for {slot.owner_path!r}")
        scalar_type = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name)
        return (FortranParameter(slot.native_name.lower(), scalar_type.fortran_spelling),)

    def _scalar_descriptor_output_parameters(self, slot: NativeCallSlotPlan) -> tuple[FortranParameter, ...]:
        """Lower one completed rank-zero descriptor result ABI."""
        descriptor = slot.scalar_descriptor
        if descriptor is None:
            raise ValueError(f"Scalar output {slot.owner_path!r} has no descriptor plan")
        name = slot.native_name.lower()
        parameters = [
            FortranParameter(name, "type(c_ptr)"),
            FortranParameter(f"{name}_present", "integer(c_int)"),
        ]
        if descriptor.runtime_length:
            parameters.append(FortranParameter(f"{name}_length", "integer(c_int64_t)"))
        return tuple(parameters)

    def _owned_native_array_output_parameters(self, slot: NativeCallSlotPlan) -> tuple[FortranParameter, ...]:
        """Lower one completed owned rank-positive descriptor result ABI."""
        handle = slot.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Owned output {slot.owner_path!r} has no descriptor rank")
        name = slot.native_name.lower()
        if self._is_owned_deferred_character_slot(slot):
            return (
                FortranParameter(name, "type(c_ptr)"),
                FortranParameter(f"{name}_itemsize", "integer(c_int64_t)"),
                *(FortranParameter(f"{name}_extent_{axis}", "integer(c_int64_t)") for axis in range(handle.array.rank)),
            )
        return (
            FortranParameter(
                name,
                self._array_result_element_type(slot),
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
        for slot in plan.native_call_slots:
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
            if slot.bridge_data_action is BridgeDataAction.DIRECT_TRANSFER:
                continue
            if slot.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION:
                declarations.extend(self._representation_copy_output_declarations(plan, slot))
                continue
            raise ValueError(
                f"Unsupported native-output bridge data action for {slot.owner_path!r}: {slot.bridge_data_action!r}"
            )
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
        match result.direct_result_abi:
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
        return (FortranDeclaration("x2py_allocation_status", "integer(c_int)"),)

    def _derived_result_storage_names(self, plan: FunctionPlan) -> tuple[str, ...]:
        """Return every bridge-local persistent derived result allocation."""
        names = []
        direct = self._direct_result(plan)
        if direct is not None and direct.object_kind is ObjectKind.DERIVED_TYPE:
            names.append("result_value")
        names.extend(
            f"{slot.native_name.lower()}_value"
            for slot in plan.native_call_slots
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
            for slot in plan.native_call_slots
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
            FortranAllocate(current, status="x2py_allocation_status"),
            FortranIf(
                CodeExpression("x2py_allocation_status == 0"),
                body=self._derived_allocation_tree(tuple(remaining), success_body, (*allocated, current)),
                else_body=tuple(FortranDeallocate(name) for name in reversed(allocated)),
            ),
        )

    def _scalar_descriptor_output_declarations(
        self,
        slot: NativeCallSlotPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare native and detached-copy storage for one hidden descriptor scalar."""
        return self._scalar_descriptor_copy_declarations(slot, slot.native_name.lower())

    def _scalar_descriptor_copy_declarations(
        self,
        result: ResultPlan | NativeCallSlotPlan,
        name: str,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare helper-local storage selected by a scalar descriptor plan."""
        descriptor = result.scalar_descriptor
        if descriptor is None:
            return ()
        attribute = "allocatable" if descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "pointer"
        value_name = f"{name}_value"
        copy_name = f"{name}_copy"
        if result.object_kind is ObjectKind.STRING:
            return (
                FortranDeclaration(value_name, "character(kind=c_char, len=:)", (attribute,)),
                FortranDeclaration(copy_name, "character(kind=c_char)", ("pointer", "dimension(:)")),
            )
        scalar_type = PrimitiveScalarTypeRegistry.type_for(result.semantic_type_name)
        return (
            FortranDeclaration(value_name, scalar_type.fortran_spelling, (attribute,)),
            FortranDeclaration(copy_name, scalar_type.fortran_spelling, ("pointer",)),
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
        return (
            FortranDeclaration("result_value", element_type, (f"dimension({', '.join(shape)})",)),
            FortranDeclaration("result_copy", copy_type, ("pointer", "dimension(:)")),
        )

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
        match result.direct_result_abi:
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
        if result is None or not self._uses_owned_direct_array_result_collector(plan):
            return ()
        return (self._owned_direct_array_result_collector(result),)

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
        slot: NativeCallSlotPlan,
    ) -> tuple[FortranDeclaration, ...]:
        """Declare storage only for one justified representation-copy output."""
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
        slot: NativeCallSlotPlan,
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
        for slot in plan.native_call_slots:
            if slot.source_kind != "result" or slot.bridge_data_action is BridgeDataAction.DIRECT_TRANSFER:
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
            if slot.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION:
                if slot.object_kind is ObjectKind.DERIVED_TYPE:
                    name = slot.native_name.lower()
                    nodes.append(FortranAssignment(name, CodeExpression(f"c_loc({name}_value)")))
                    continue
                nodes.extend(self._lower_native_output_representation_copy(plan, slot))
                continue
            raise ValueError(
                f"Unsupported native-output bridge data action for {slot.owner_path!r}: {slot.bridge_data_action!r}"
            )
        return tuple(nodes)

    def _scalar_descriptor_copy_nodes(
        self,
        result: ResultPlan | NativeCallSlotPlan,
        name: str,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy one present scalar descriptor payload into C-owned storage."""
        descriptor = result.scalar_descriptor
        if descriptor is None:
            return ()
        value_name = f"{name}_value"
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
        result: ResultPlan | NativeCallSlotPlan,
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
        slot: NativeCallSlotPlan,
    ) -> tuple[FortranAssignment | FortranIf, ...]:
        """Copy one native output only through the explicit policy permission."""
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

    def _array_result_element_type(self, plan: ResultPlan | NativeCallSlotPlan) -> str:
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

    def _array_result_itemsize(self, plan: ResultPlan | NativeCallSlotPlan) -> int | None:
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

    def _native_output_value_name(self, slot: NativeCallSlotPlan) -> str:
        """Return the native-call expression selected for one output slot."""
        name = slot.native_name.lower()
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

    def _string_output_length(self, slot: NativeCallSlotPlan) -> int:
        if slot.character_length is None or slot.character_length <= 0:
            raise ValueError(f"String output {slot.owner_path!r} is missing a fixed character length")
        return slot.character_length

    def _string_result_length(self, result: ResultPlan) -> int:
        if result.character_length is None or result.character_length <= 0:
            raise ValueError(f"String result {result.owner_path!r} is missing a fixed character length")
        return result.character_length

    def _native_direct_result_name(self, plan: FunctionPlan, result_name: str | None) -> str | None:
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
        match result.direct_result_abi:
            case DirectResultABI.LOGICAL_LOW_BIT_INT8:
                return "c_result"
            case DirectResultABI.NATIVE_SCALAR:
                return result_name
            case _:
                raise ValueError(f"Scalar result {result.owner_path!r} has no completed direct-result ABI")

    def _bridge_result_type(self, plan: FunctionPlan, result: ResultPlan | None = None) -> str:
        result = result or self._direct_result(plan)
        if result is None:
            raise ValueError(f"{plan.owner_path!r} native function has no result plan")
        if result.scalar_descriptor is not None:
            return "type(c_ptr)"
        if result.object_kind in {ObjectKind.STRING, ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return "type(c_ptr)"
        if result.direct_result_abi is DirectResultABI.LOGICAL_LOW_BIT_INT8:
            return "integer(c_int8_t)"
        if result.direct_result_abi is DirectResultABI.NATIVE_SCALAR:
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
        return "x2py_collect_allocatable_array_result"

    @staticmethod
    def _is_owned_native_array_result(result: ResultPlan) -> bool:
        """Return whether one result owns persistent standard-descriptor storage."""
        handle = result.native_array_handle
        return handle is not None and handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE

    @staticmethod
    def _is_owned_native_array_slot(slot: NativeCallSlotPlan) -> bool:
        """Return whether one hidden slot shares persistent descriptor storage."""
        handle = slot.native_array_handle
        return handle is not None and handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE

    @classmethod
    def _is_owned_deferred_character_result(cls, result: ResultPlan) -> bool:
        """Return whether owner storage needs a runtime-width copy ABI."""
        return cls._is_owned_native_array_result(result) and result.datatype_family is DatatypeFamily.STRING

    @classmethod
    def _is_owned_deferred_character_slot(cls, slot: NativeCallSlotPlan) -> bool:
        """Return whether a hidden owner slot needs a runtime-width copy ABI."""
        return cls._is_owned_native_array_slot(slot) and slot.datatype_family is DatatypeFamily.STRING

    def _native_module_uses(self, plan: ModulePlan) -> tuple[FortranUse, ...]:
        """Collect exact native imports without mixing class invocation policy."""
        modules: dict[str, list[str]] = {}
        self._add_derived_module_uses(plan, modules)
        self._add_function_module_uses(plan, modules)
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
            self._add_callback_prototype_uses(function, modules)
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

    def _add_callback_prototype_uses(
        self,
        function: FunctionPlan,
        modules: dict[str, list[str]],
    ) -> None:
        """Import named prototypes selected by completed callback policy."""
        for argument in function.arguments:
            callback = argument.callback
            if (
                callback is not None
                and callback.declaration_mode is ExternalDeclarationMode.EXPLICIT_INTERFACE
                and callback.prototype_module is not None
            ):
                modules.setdefault(callback.prototype_module, []).append(
                    f"{self._callback_imported_prototype_symbol(callback)} => {callback.prototype_name}"
                )

    def _add_variable_module_uses(self, plan: ModulePlan, modules: dict[str, list[str]]) -> None:
        """Import only module variables with a planned getter, setter, or proxy."""
        for variable in self._variables(plan):
            if (
                variable.bridge.getter_role is not None
                or variable.bridge.setter_role is not None
                or variable.derived is not None
            ):
                modules.setdefault(variable.bridge.native_module, []).append(
                    f"{self._native_variable_name(variable)} => {variable.bridge.native_name}"
                )

    def _derived_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return namespace-owned opaque types in stable plan order."""
        return tuple(derived for namespace in plan.namespaces for derived in namespace.derived_types)

    def _owned_derived_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return only native types with completed wrapper-owned result storage."""
        identities = self._owned_derived_result_identities(plan)
        identities.update(self._owned_derived_module_identities(plan))
        identities.update(self._constructible_class_identities(plan))
        return tuple(derived for derived in self._derived_types(plan) if derived.type_identity in identities)

    @staticmethod
    def _constructible_class_identities(plan: ModulePlan) -> set[tuple[str, str]]:
        """Return class identities whose completed constructor allocates storage."""
        return {
            surface.type_identity
            for namespace in plan.namespaces
            for surface in namespace.classes
            if surface.constructor.kind is not ClassConstructorKind.ABSENT
        }

    def _owned_derived_result_identities(self, plan: ModulePlan) -> set[tuple[str, str]]:
        return {
            result.derived.type_identity
            for function in self._functions(plan)
            for result in function.results
            if result.derived is not None
            and result.derived.release is DerivedRelease.WRAPPER_DESTROY
            and result.derived.storage
            not in {DerivedObjectStorage.ALLOCATABLE_HOLDER, DerivedObjectStorage.POINTER_HOLDER}
        }

    def _owned_derived_module_identities(self, plan: ModulePlan) -> set[tuple[str, str]]:
        return {
            variable.derived.handoff.type_identity
            for variable in self._variables(plan)
            if variable.derived is not None and variable.derived.access is ModuleObjectAccessMechanism.VALUE_COPY
        }

    def _allocatable_holder_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return types whose completed storage or call action uses a typed holder."""
        identities = self._allocatable_holder_result_identities(plan)
        identities.update(self._allocatable_holder_argument_identities(plan))
        return tuple(derived for derived in self._derived_types(plan) if derived.type_identity in identities)

    def _allocatable_holder_result_identities(self, plan: ModulePlan) -> set[tuple[str, str]]:
        return {
            result.derived.type_identity
            for function in self._functions(plan)
            for result in function.results
            if result.derived is not None and result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER
        }

    def _allocatable_holder_argument_identities(self, plan: ModulePlan) -> set[tuple[str, str]]:
        return {
            argument.derived.type_identity
            for function in self._functions(plan)
            for argument in function.arguments
            if argument.derived is not None
            and argument.derived_call is not None
            and any(
                case.access is DerivedActualAccess.ALLOCATABLE_HOLDER
                for case in argument.derived_call.cases
                if case.action is not DerivedCallAction.INCOMPATIBLE
            )
        }

    def _pointer_holder_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return types whose results or call rows use pointer holders."""
        identities = self._pointer_holder_result_identities(plan)
        identities.update(self._pointer_holder_argument_identities(plan))
        return tuple(derived for derived in self._derived_types(plan) if derived.type_identity in identities)

    def _pointer_holder_result_identities(self, plan: ModulePlan) -> set[tuple[str, str]]:
        return {
            result.derived.type_identity
            for function in self._functions(plan)
            for result in function.results
            if result.derived is not None and result.derived.storage is DerivedObjectStorage.POINTER_HOLDER
        }

    def _pointer_holder_argument_identities(self, plan: ModulePlan) -> set[tuple[str, str]]:
        return {
            argument.derived.type_identity
            for function in self._functions(plan)
            for argument in function.arguments
            if argument.derived is not None
            and argument.derived_call is not None
            and any(
                case.access is DerivedActualAccess.POINTER_HOLDER
                for case in argument.derived_call.cases
                if case.action is not DerivedCallAction.INCOMPATIBLE
            )
        }

    @staticmethod
    def _uses_allocatable_holder(argument: ArgumentTransferPlan) -> bool:
        return FortranBridgeGenerator._uses_holder(argument, DerivedActualAccess.ALLOCATABLE_HOLDER)

    @staticmethod
    def _uses_pointer_holder(argument: ArgumentTransferPlan) -> bool:
        return FortranBridgeGenerator._uses_holder(argument, DerivedActualAccess.POINTER_HOLDER)

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
        return tuple(
            procedure
            for derived in self._derived_types(plan)
            for field in derived.fields
            for procedure in self._direct_field_procedures(derived, field)
        )

    def _module_member_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        return tuple(
            procedure
            for variable in self._derived_member_proxy_variables(plan)
            for member in variable.derived.member_paths
            for procedure in self._module_member_procedures(variable, member)
        )

    def _allocatable_holder_field_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        return tuple(
            procedure
            for derived in self._allocatable_holder_field_types(plan)
            for field in derived.fields
            for procedure in self._allocatable_holder_field_procedures(derived, field)
        )

    def _pointer_holder_field_procedure_entries(self, plan: ModulePlan) -> tuple[FortranFunction, ...]:
        return tuple(
            procedure
            for derived in self._pointer_holder_field_types(plan)
            for field in derived.fields
            for procedure in self._pointer_holder_field_procedures(derived, field)
        )

    def _allocatable_holder_field_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return holders that can cross back to Python and need field operations."""
        identities = self._allocatable_holder_result_identities(plan)
        identities.update(
            argument.derived.type_identity
            for function in self._functions(plan)
            for argument in function.arguments
            if argument.derived is not None
            and argument.bridge.descriptor_output_role is not None
            and self._uses_allocatable_holder(argument)
        )
        return tuple(derived for derived in self._derived_types(plan) if derived.type_identity in identities)

    def _pointer_holder_field_types(self, plan: ModulePlan) -> tuple[DerivedTypePlan, ...]:
        """Return pointer holders that can cross back to Python and need fields."""
        identities = self._pointer_holder_result_identities(plan)
        identities.update(
            argument.derived.type_identity
            for function in self._functions(plan)
            for argument in function.arguments
            if argument.derived is not None
            and argument.bridge.descriptor_output_role is not None
            and self._uses_pointer_holder(argument)
        )
        return tuple(derived for derived in self._derived_types(plan) if derived.type_identity in identities)

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
        if isinstance(owner, DerivedTypePlan):
            return (FortranParameter("owner_address", "type(c_ptr)", ("value",)),)
        return ()

    def _native_handle_field_owner_declarations(self, owner) -> tuple[FortranDeclaration, ...]:
        if isinstance(owner, DerivedTypePlan):
            return (self._derived_owner_declaration(owner),)
        return ()

    def _native_handle_field_owner_body(self, owner) -> tuple[FortranCall, ...]:
        if isinstance(owner, DerivedTypePlan):
            return (self._derived_owner_association(),)
        return ()

    def _native_handle_field_expression(self, owner, field: DerivedFieldPlan) -> str:
        if isinstance(owner, DerivedTypePlan):
            return f"owner%{field.native_name}"
        variable, member = owner
        return self._module_member_expression(variable, member)

    @staticmethod
    def _native_handle_field_presence(field: DerivedFieldPlan, expression: str) -> str:
        handle = field.native_array_handle
        if handle is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no descriptor kind")
        intrinsic = "allocated" if handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE else "associated"
        return f"{intrinsic}({expression})"

    def _native_handle_field_bridge_name(self, owner, field, operation) -> str:
        if isinstance(owner, DerivedTypePlan):
            return self._derived_handle_bridge_name(owner, field, operation)
        variable, member = owner
        return self._module_member_handle_bridge_name(variable, member, operation)

    def _native_handle_field_callback_interface_name(self, owner, field) -> str:
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
        return FortranCall(
            "c_f_pointer",
            (
                CodeExpression("value_address"),
                CodeExpression("value"),
                CodeExpression(f"[{', '.join(array.shape)}]"),
            ),
        )

    def _direct_scalar_field_getter(self, derived: DerivedTypePlan, field: DerivedFieldPlan) -> FortranFunction:
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
        return FortranDeclaration(
            "owner",
            f"type({self._derived_native_alias(derived.backend_symbol)})",
            ("pointer",),
        )

    @staticmethod
    def _derived_owner_association() -> FortranCall:
        return FortranCall("c_f_pointer", (CodeExpression("owner_address"), CodeExpression("owner")))

    def _module_member_expression(self, variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        return "%".join((self._native_variable_name(variable), *member.native_path))

    @staticmethod
    def _derived_field_symbol(derived: DerivedTypePlan, field: DerivedFieldPlan) -> str:
        return f"{derived.backend_symbol}_{field.name}".casefold()

    def _derived_field_bridge_name(self, derived: DerivedTypePlan, field: DerivedFieldPlan, action: str) -> str:
        return f"bind_c_x2py_field_{self._derived_field_symbol(derived, field)}_{action}"

    def _allocatable_holder_field_bridge_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        return f"bind_c_x2py_allocatable_holder_field_{self._derived_field_symbol(derived, field)}_{action}"

    def _pointer_holder_field_bridge_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        action: str,
    ) -> str:
        return f"bind_c_x2py_pointer_holder_field_{self._derived_field_symbol(derived, field)}_{action}"

    def _derived_field_callback_interface_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        return f"x2py_field_{self._derived_field_symbol(derived, field)}_consumer"

    def _derived_handle_bridge_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
        operation: NativeArrayOperation,
    ) -> str:
        return f"bind_c_x2py_field_handle_{self._derived_field_symbol(derived, field)}_{operation.value}"

    def _derived_handle_callback_interface_name(
        self,
        derived: DerivedTypePlan,
        field: DerivedFieldPlan,
    ) -> str:
        return f"x2py_field_handle_{self._derived_field_symbol(derived, field)}_consumer"

    @staticmethod
    def _module_member_symbol(variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        return "_".join((variable.symbol_name, *member.path)).casefold()

    def _module_member_bridge_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        action: str,
    ) -> str:
        return f"bind_c_x2py_module_field_{self._module_member_symbol(variable, member)}_{action}"

    def _module_member_callback_interface_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        return f"x2py_module_field_{self._module_member_symbol(variable, member)}_consumer"

    def _module_member_handle_bridge_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
        operation: NativeArrayOperation,
    ) -> str:
        return f"bind_c_x2py_module_field_handle_{self._module_member_symbol(variable, member)}_{operation.value}"

    def _module_member_handle_callback_interface_name(
        self,
        variable: ModuleVariablePlan,
        member: DerivedMemberPathPlan,
    ) -> str:
        return f"x2py_module_field_handle_{self._module_member_symbol(variable, member)}_consumer"

    def _derived_member_proxy_variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
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
            if surface.constructor.kind is not ClassConstructorKind.ABSENT
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

    @staticmethod
    def _class_create_bridge_name(surface: ClassSurfacePlan) -> str:
        return f"bind_c_x2py_create_{surface.type_identity[1].casefold()}"

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
        return f"x2py_type_{type_name.casefold()}"

    @staticmethod
    def _derived_destroy_bridge_name(type_name: str) -> str:
        return f"bind_c_x2py_destroy_{type_name.casefold()}"

    @staticmethod
    def _allocatable_holder_type_name(type_name: str) -> str:
        return f"x2py_{type_name.casefold()}_allocatable_holder"

    @staticmethod
    def _pointer_holder_type_name(type_name: str) -> str:
        return f"x2py_{type_name.casefold()}_pointer_holder"

    @staticmethod
    def _allocatable_holder_destroy_bridge_name(type_name: str) -> str:
        return f"bind_c_x2py_destroy_{type_name.casefold()}_allocatable_holder"

    @staticmethod
    def _allocatable_holder_presence_bridge_name(type_name: str) -> str:
        return f"bind_c_x2py_{type_name.casefold()}_allocatable_holder_present"

    @staticmethod
    def _pointer_holder_destroy_bridge_name(type_name: str) -> str:
        return f"bind_c_x2py_destroy_{type_name.casefold()}_pointer_holder"

    @staticmethod
    def _pointer_holder_presence_bridge_name(type_name: str) -> str:
        return f"bind_c_x2py_{type_name.casefold()}_pointer_holder_present"

    @staticmethod
    def _module_derived_presence_bridge_name(plan: ModuleVariablePlan) -> str:
        return f"bind_c_x2py_module_{plan.symbol_name.casefold()}_present"

    def _external_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        procedures = tuple(
            self._external_interface_procedure(function)
            for function in self._functions(plan)
            if function.bridge.external_declaration is ExternalDeclarationMode.EXPLICIT_INTERFACE
        )
        return (FortranInterface(procedures),) if procedures else ()

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
        result = callback.result.transfer
        is_subroutine = callback.result.action is CallbackResultAction.RETURN_VOID
        return FortranInterfaceProcedure(
            name=name,
            imports=self._callback_c_imports(callback),
            parameters=tuple(
                parameter for transfer in callback.arguments for parameter in self._callback_c_parameters(transfer)
            ),
            result_name=None if is_subroutine else "callback_result",
            result_type=None if is_subroutine else self._callback_c_result_type(result),
            is_subroutine=is_subroutine,
            bind_name=bind_name,
            bind_c=True,
        )

    def _callback_c_parameters(self, transfer: CallbackTransferPlan) -> tuple[FortranParameter, ...]:
        """Flatten one callback transfer into interoperable C parameters."""
        base = self._callback_parameter_base_name(transfer)
        if transfer.abi is CallbackABIKind.VALUE:
            return (
                FortranParameter(
                    base,
                    PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name).fortran_spelling,
                    ("value",),
                ),
            )
        parameters = [FortranParameter(f"{base}_data", "type(c_ptr)", ("value",))]
        if transfer.abi is CallbackABIKind.DATA_AND_SHAPE:
            parameters.extend(
                FortranParameter(f"{base}_extent_{axis}", "integer(c_int64_t)", ("value",))
                for axis in range(transfer.rank)
            )
        elif transfer.abi is CallbackABIKind.DATA_AND_LENGTH:
            parameters.append(FortranParameter(f"{base}_length", "integer(c_int64_t)", ("value",)))
        return tuple(parameters)

    def _callback_c_result_type(self, transfer: CallbackTransferPlan | None) -> str:
        """Return the interoperable C trampoline result type."""
        if transfer is None:
            raise ValueError("Callback function result is missing its transfer plan")
        if transfer.abi is CallbackABIKind.VALUE:
            return PrimitiveScalarTypeRegistry.type_for(transfer.semantic_type_name).fortran_spelling
        return "type(c_ptr)"

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

    @staticmethod
    def _callback_imported_prototype_symbol(callback: CallbackHandoffPlan) -> str:
        return f"{callback.adapter_symbol}_prototype"

    def _derived_call_interfaces(self, plan: ModulePlan) -> tuple[FortranInterface, ...]:
        """Declare the typed callback ABI shared by every scalar-derived call."""
        if not any(
            argument.derived_call is not None for function in self._functions(plan) for argument in function.arguments
        ) and not any(variable.derived is not None for variable in self._variables(plan)):
            return ()
        procedures = (
            FortranInterfaceProcedure(
                "x2py_derived_consumer",
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
                "x2py_derived_scoped",
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
                "x2py_derived_checkout",
                imports=("c_ptr", "c_int"),
                parameters=(FortranParameter("holder", "type(c_ptr)", ("intent(out)",)),),
                result_name="status",
                result_type="integer(c_int)",
                bind_c=True,
            ),
            FortranInterfaceProcedure(
                "x2py_derived_restore",
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
        return f"x2py_{plan.symbol_name}_descriptor_consumer"

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
            bind_name="x2py_malloc",
        )
        return (FortranInterface((procedure,)),)

    def _needs_allocator_interface(self, plan: ModulePlan) -> bool:
        """Return whether module getter values or function copies allocate storage."""
        return self._needs_module_getter_allocator(plan) or self._needs_function_copy_allocator(plan)

    def _needs_module_getter_allocator(self, plan: ModulePlan) -> bool:
        """Return whether a nullable scalar descriptor getter copies one value."""
        return any(
            variable.bridge.getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT for variable in self._variables(plan)
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
            for slot in function.native_call_slots
            if slot.source_kind == "result"
        )

    def _external_interface_procedure(self, plan: FunctionPlan) -> FortranInterfaceProcedure:
        slots = tuple(sorted(plan.native_call_slots, key=lambda item: item.native_position))
        arguments = {argument.owner_path: argument for argument in plan.arguments}
        parameters = tuple(self._external_interface_slot_parameter(plan, slot, arguments) for slot in slots)
        imports = tuple(
            dict.fromkeys(
                self._iso_symbol(slot.semantic_type_name) for slot in slots if slot.semantic_type_name is not None
            )
        )
        result_name = None if plan.bridge.native_is_subroutine else "native_result"
        direct_result = self._direct_result(plan)
        result_type = self._native_result_type(plan, direct_result) if result_name is not None else None
        if result_type is not None and direct_result is not None:
            imports = tuple(dict.fromkeys((*imports, self._iso_symbol(direct_result.semantic_type_name))))
        return FortranInterfaceProcedure(
            name=plan.bridge.native_name,
            imports=imports,
            parameters=parameters,
            parameter_declarations=self._external_interface_parameter_declarations(slots, parameters),
            result_name=result_name,
            result_type=result_type,
            is_subroutine=plan.bridge.native_is_subroutine,
        )

    @staticmethod
    def _external_interface_parameter_declarations(
        slots: tuple[NativeCallSlotPlan, ...],
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
        slot: NativeCallSlotPlan,
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
        slot: NativeCallSlotPlan,
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
    def _external_interface_scalar_descriptor_result_parameter(slot: NativeCallSlotPlan) -> FortranParameter:
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
    def _external_interface_scalar_result_parameter(slot: NativeCallSlotPlan) -> FortranParameter:
        """Declare one completed primitive scalar output."""
        if slot.semantic_type_name is None:
            raise ValueError(f"Scalar output {slot.owner_path!r} has no element type")
        scalar_type = PrimitiveScalarTypeRegistry.type_for(slot.semantic_type_name)
        return FortranParameter(slot.native_name.lower(), scalar_type.fortran_spelling)

    @staticmethod
    def _external_interface_string_result_parameter(slot: NativeCallSlotPlan) -> FortranParameter:
        """Declare one completed fixed or assumed-length string output."""
        length = "*" if slot.character_length is None else str(slot.character_length)
        return FortranParameter(slot.native_name.lower(), f"character(kind=c_char, len={length})")

    def _external_interface_array_result_parameter(
        self,
        plan: FunctionPlan,
        slot: NativeCallSlotPlan,
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

    def _external_interface_derived_result_parameter(self, slot: NativeCallSlotPlan) -> FortranParameter:
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
    def _external_interface_literal_parameter(slot: NativeCallSlotPlan) -> FortranParameter:
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
        parameter_name = name or argument.bridge.native_name.lower()
        if argument.callback is not None:
            return FortranParameter(parameter_name, "external")
        attributes = (
            ("optional",)
            if argument.bridge.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
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
            length = argument.native_call_slot.character_length
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
        shape = list(self._array_shape_from_roles(array, plan.arguments))
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
        return bool(array is not None and array.rank == 0 and array.category == SCALAR_STORAGE_CATEGORY)

    # Ordinary-array result-shape lowering.
    def _array_result_shape(self, plan: FunctionPlan, result: ResultPlan) -> tuple[str, ...]:
        """Lower one result shape through the plan's native scalar roles."""
        if result.array is None:
            raise ValueError(f"Array result {result.owner_path!r} has no shape plan")
        return self._array_shape_from_roles(result.array, plan.arguments)

    def _array_output_shape(self, plan: FunctionPlan, slot: NativeCallSlotPlan) -> tuple[str, ...]:
        """Lower one hidden-output shape through the plan's native scalar roles."""
        if slot.array is None:
            raise ValueError(f"Array output {slot.owner_path!r} has no shape plan")
        return self._array_shape_from_roles(slot.array, plan.arguments)

    def _array_shape_from_roles(self, array, arguments) -> tuple[str, ...]:
        """Replace validated shape references with their native dummy names."""
        lowered_shape = []
        role_names = {argument.binding.handoff_role: argument.bridge.native_name.lower() for argument in arguments}
        for axis, expression in enumerate(array.shape):
            lowered = expression
            for role in array.extent_reference_roles[axis]:
                native_name = role_names.get(role)
                if native_name is None:
                    reference_name = role.rsplit(".", 1)[-1].split(":", 1)[0]
                    native_name = reference_name
                reference_name = role.rsplit(".", 1)[-1].split(":", 1)[0]
                lowered = re.sub(rf"\b{re.escape(reference_name)}\b", native_name, lowered)
            lowered_shape.append(lowered)
        return tuple(lowered_shape)

    def _has_optional_arguments(self, plan: FunctionPlan) -> bool:
        return any(
            argument.bridge.optional_mode in {OptionalMode.NULLABLE_VALUE, OptionalMode.DESCRIPTOR}
            for argument in plan.arguments
        )

    def _literal_expression(self, value: object) -> str:
        if isinstance(value, bool):
            return ".true." if value else ".false."
        if isinstance(value, complex):
            return f"({value.real}, {value.imag})"
        return str(value)

    def _bridge_function_name(self, plan: FunctionPlan) -> str:
        return f"bind_c_{plan.symbol_name}"

    def _module_bridge_getter_name(self, plan: ModuleVariablePlan) -> str:
        return f"bind_c_get_{plan.symbol_name}"

    def _module_bridge_setter_name(self, plan: ModuleVariablePlan) -> str:
        return f"bind_c_set_{plan.symbol_name}"

    def _native_function_name(self, plan: FunctionPlan) -> str:
        return plan.bridge.native_name if plan.bridge.external else f"native_{plan.symbol_name}"

    def _native_variable_name(self, plan: ModuleVariablePlan) -> str:
        return f"native_{plan.symbol_name}"

    def _functions(self, plan: ModulePlan) -> tuple[FunctionPlan, ...]:
        return tuple(function for namespace in plan.namespaces for function in namespace.functions)

    def _variables(self, plan: ModulePlan) -> tuple[ModuleVariablePlan, ...]:
        return tuple(variable for namespace in plan.namespaces for variable in namespace.variables)

    def _iso_symbol(self, semantic_type_name: str) -> str:
        symbols = {
            "Bool": "c_bool",
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
        derived_calls = any(
            argument.derived_call is not None for function in self._functions(plan) for argument in function.arguments
        )
        derived_variables = any(variable.derived is not None for variable in self._variables(plan))
        return derived_calls or derived_variables
