"""Project generated support procedures into one shared C-ABI registry.

Ordinary wrapped functions own specialized entrypoint facets directly. This
module covers every other externally linked callable emitted by the current
Fortran adapter. It runs inside :class:`WrapperPlanner`; generators consume the
resulting operation records and do not decide which helpers exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from prik.naming.native_symbols import NativeSymbolNames
from prik.policy.models import (
    CallbackABIKind,
    CallbackResultAction,
    ClassConstructorKind,
    DerivedActualAccess,
    DerivedCallAction,
    DerivedFieldAccessMechanism,
    DerivedObjectStorage,
    DerivedRelease,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    NativeArrayDefaultConstruction,
    NativeArrayDescriptorInterop,
    NativeArrayOperation,
    NativeDescriptorHandoffABI,
)
from prik.policy.ownership import ObjectKind, SetterAction

from .models import (
    ArgumentTransferPlan,
    CallbackHandoffPlan,
    CallbackTransferPlan,
    DatatypeFamily,
    DerivedFieldPlan,
    DerivedMemberPathPlan,
    DerivedTypePlan,
    ModuleVariablePlan,
    NamespacePlan,
    NativeArrayHandlePlan,
    NativeEntrypointABIValueKind,
    NativeEntrypointABIValuePlan,
    GeneratedSupportProcedureImplementationOwner,
    GeneratedSupportProcedureEntrypointPlan,
    NativeEntrypointSignaturePlan,
    ResultPlan,
)


_FIELD_HANDLE_LOCAL_OPERATIONS = frozenset(
    {
        NativeArrayOperation.NATIVE_BYTE_ORDER,
        NativeArrayOperation.ALIGNED,
        NativeArrayOperation.WRITEABLE,
        NativeArrayOperation.LAYOUT,
        NativeArrayOperation.TO_NUMPY,
        NativeArrayOperation.ARRAY_ACTUAL,
    }
)
_MODULE_HANDLE_LOCAL_OPERATIONS = frozenset(
    {
        NativeArrayOperation.NATIVE_BYTE_ORDER,
        NativeArrayOperation.ALIGNED,
        NativeArrayOperation.WRITEABLE,
        NativeArrayOperation.LAYOUT,
        NativeArrayOperation.TO_NUMPY,
    }
)
_OWNED_HANDLE_ENTRYPOINT_OPERATIONS = frozenset(
    {
        NativeArrayOperation.ALLOCATED,
        NativeArrayOperation.ASSOCIATED,
        NativeArrayOperation.CONTIGUOUS,
        NativeArrayOperation.SHAPE,
        NativeArrayOperation.ASSOCIATE,
        NativeArrayOperation.DEALLOCATE,
        NativeArrayOperation.NULLIFY,
        NativeArrayOperation.DESTROY,
    }
)


@dataclass(frozen=True)
class GeneratedSupportProcedureProjection:
    """Keep external entrypoints and backend-local support in one projection."""

    support_procedures: tuple[GeneratedSupportProcedureEntrypointPlan, ...]
    binding_owned_derived_type_owner_paths: tuple[str, ...]
    binding_allocatable_holder_type_owner_paths: tuple[str, ...]
    binding_pointer_holder_type_owner_paths: tuple[str, ...]
    bridge_allocatable_holder_type_owner_paths: tuple[str, ...]
    bridge_pointer_holder_type_owner_paths: tuple[str, ...]
    bridge_allocatable_holder_field_type_owner_paths: tuple[str, ...]
    bridge_pointer_holder_field_type_owner_paths: tuple[str, ...]


def build_generated_support_procedure_projection(
    namespaces: tuple[NamespacePlan, ...],
) -> GeneratedSupportProcedureProjection:
    """Return external and backend-local support membership in stable order."""
    builder = _GeneratedSupportProcedureEntrypointBuilder(namespaces)
    projection = builder.build()
    procedures = projection.support_procedures
    keys = [procedure.key for procedure in procedures]
    symbols = [procedure.symbol_name for procedure in procedures]
    if len(keys) != len(set(keys)):
        duplicates = tuple(key for key in dict.fromkeys(keys) if keys.count(key) > 1)
        raise ValueError(f"Generated support procedure entrypoint keys are not unique: {duplicates!r}")
    if len(symbols) != len(set(symbols)):
        duplicates = tuple(symbol for symbol in dict.fromkeys(symbols) if symbols.count(symbol) > 1)
        raise ValueError(f"Generated support procedure entrypoint symbols are not unique: {duplicates!r}")
    return projection


def build_callback_support_procedure_entrypoint(
    owner_path: str,
    symbol_name: str,
    arguments: tuple[CallbackTransferPlan, ...],
    result,
) -> GeneratedSupportProcedureEntrypointPlan:
    """Project the binding trampoline once while its callback site is planned."""
    builder = _GeneratedSupportProcedureEntrypointBuilder(())
    parameters = tuple(
        parameter for transfer in arguments for parameter in builder._callback_transfer_parameters(transfer)
    )
    return builder._operation(
        owner_path,
        "callback:trampoline",
        symbol_name,
        parameters,
        builder._callback_result_from_plan(result),
        implementation_owner=GeneratedSupportProcedureImplementationOwner.BINDING,
    )


class _GeneratedSupportProcedureEntrypointBuilder:
    """Project operation existence, symbols, and ABI signatures from completed plans."""

    def __init__(self, namespaces: tuple[NamespacePlan, ...]) -> None:
        self.namespaces = namespaces
        self.functions = tuple(function for namespace in namespaces for function in namespace.functions)
        self.variables = tuple(variable for namespace in namespaces for variable in namespace.variables)
        self.derived_types = tuple(derived for namespace in namespaces for derived in namespace.derived_types)
        self.classes = tuple(surface for namespace in namespaces for surface in namespace.classes)

    def build(self) -> GeneratedSupportProcedureProjection:
        """Collect external and binding-local support in declaration order."""
        owned_types = self._owned_derived_types()
        allocatable_holders = self._allocatable_holder_types()
        pointer_holders = self._pointer_holder_types()
        binding_allocatable_holders = self._allocatable_holder_field_types()
        binding_pointer_holders = self._pointer_holder_field_types()
        binding_allocatable_owner_paths = tuple(derived.owner_path for derived in binding_allocatable_holders)
        binding_pointer_owner_paths = tuple(derived.owner_path for derived in binding_pointer_holders)
        return GeneratedSupportProcedureProjection(
            support_procedures=(
                *self._callback_operations(),
                *self._class_constructor_operations(),
                *(self._derived_destroy_operation(derived) for derived in owned_types),
                *(self._holder_destroy_operation(derived, "allocatable") for derived in allocatable_holders),
                *(self._holder_destroy_operation(derived, "pointer") for derived in pointer_holders),
                *(self._holder_presence_operation(derived, "allocatable") for derived in allocatable_holders),
                *(self._holder_presence_operation(derived, "pointer") for derived in pointer_holders),
                *self._owned_native_array_operations(),
                *self._derived_field_operations(
                    binding_allocatable_holders,
                    binding_pointer_holders,
                ),
                *self._module_variable_operations(),
                *self._derived_origin_operations(),
            ),
            binding_owned_derived_type_owner_paths=tuple(derived.owner_path for derived in owned_types),
            binding_allocatable_holder_type_owner_paths=binding_allocatable_owner_paths,
            binding_pointer_holder_type_owner_paths=binding_pointer_owner_paths,
            bridge_allocatable_holder_type_owner_paths=tuple(derived.owner_path for derived in allocatable_holders),
            bridge_pointer_holder_type_owner_paths=tuple(derived.owner_path for derived in pointer_holders),
            bridge_allocatable_holder_field_type_owner_paths=binding_allocatable_owner_paths,
            bridge_pointer_holder_field_type_owner_paths=binding_pointer_owner_paths,
        )

    # ------------------------------------------------------------------
    # Generic ABI records
    # ------------------------------------------------------------------

    @staticmethod
    def _value(
        role: str,
        kind: NativeEntrypointABIValueKind,
        *,
        c_name: str | None = None,
        fortran_name: str | None = None,
        pointer_depth: int = 0,
        const: bool = False,
        semantic_type_name: str | None = None,
        rank: int | None = None,
        character_length: int | None = None,
        descriptor_kind=None,
        intent: str | None = None,
        c_type_name: str | None = None,
        callback_signature: NativeEntrypointSignaturePlan | None = None,
    ) -> NativeEntrypointABIValuePlan:
        name = c_name or role
        return NativeEntrypointABIValuePlan(
            role=role,
            c_name=name,
            fortran_name=fortran_name or name,
            kind=kind,
            pointer_depth=pointer_depth,
            const=const,
            semantic_type_name=semantic_type_name,
            rank=rank,
            character_length=character_length,
            descriptor_kind=descriptor_kind,
            intent=intent,
            c_type_name=c_type_name,
            callback_signature=callback_signature,
        )

    @classmethod
    def _void_result(cls) -> NativeEntrypointABIValuePlan:
        return cls._value("result", NativeEntrypointABIValueKind.VOID)

    @classmethod
    def _operation(
        cls,
        owner_path: str,
        role: str,
        symbol_name: str,
        parameters: tuple[NativeEntrypointABIValuePlan, ...] = (),
        result: NativeEntrypointABIValuePlan | None = None,
        *,
        implementation_owner: GeneratedSupportProcedureImplementationOwner = (
            GeneratedSupportProcedureImplementationOwner.FORTRAN
        ),
    ) -> GeneratedSupportProcedureEntrypointPlan:
        return GeneratedSupportProcedureEntrypointPlan(
            key=f"{owner_path}::{role}",
            owner_path=owner_path,
            role=role,
            symbol_name=symbol_name,
            signature=NativeEntrypointSignaturePlan(
                parameters=parameters,
                result=result or cls._void_result(),
            ),
            implementation_owner=implementation_owner,
        )

    @classmethod
    def _opaque_parameter(
        cls,
        role: str,
        *,
        c_name: str | None = None,
        fortran_name: str | None = None,
        output: bool = False,
        intent: str | None = None,
    ) -> NativeEntrypointABIValuePlan:
        return cls._value(
            role,
            NativeEntrypointABIValueKind.OPAQUE,
            c_name=c_name,
            fortran_name=fortran_name,
            pointer_depth=2 if output else 1,
            intent=intent,
        )

    @classmethod
    def _opaque_result(cls) -> NativeEntrypointABIValuePlan:
        return cls._value("result", NativeEntrypointABIValueKind.OPAQUE, pointer_depth=1)

    @classmethod
    def _scalar_parameter(
        cls,
        semantic_type_name: str,
        *,
        role: str = "value",
        reference: bool = False,
    ) -> NativeEntrypointABIValuePlan:
        return cls._value(
            role,
            NativeEntrypointABIValueKind.SEMANTIC_SCALAR,
            pointer_depth=int(reference),
            semantic_type_name=semantic_type_name,
        )

    @classmethod
    def _scalar_result(cls, semantic_type_name: str) -> NativeEntrypointABIValuePlan:
        return cls._value(
            "result",
            NativeEntrypointABIValueKind.SEMANTIC_SCALAR,
            semantic_type_name=semantic_type_name,
        )

    @classmethod
    def _bool_result(cls) -> NativeEntrypointABIValuePlan:
        return cls._value("result", NativeEntrypointABIValueKind.BOOL)

    @classmethod
    def _int_result(cls) -> NativeEntrypointABIValuePlan:
        return cls._value("result", NativeEntrypointABIValueKind.INT)

    @classmethod
    def _int64_result(cls) -> NativeEntrypointABIValuePlan:
        return cls._value("result", NativeEntrypointABIValueKind.INT64)

    @classmethod
    def _int64_parameter(
        cls,
        name: str,
        *,
        reference: bool = False,
        intent: str | None = None,
    ) -> NativeEntrypointABIValuePlan:
        return cls._value(
            name,
            NativeEntrypointABIValueKind.INT64,
            pointer_depth=int(reference),
            intent=intent,
        )

    @classmethod
    def _descriptor_parameter(
        cls,
        name: str,
        handle: NativeArrayHandlePlan,
        semantic_type_name: str,
        *,
        intent: str,
    ) -> NativeEntrypointABIValuePlan:
        return cls._value(
            name,
            NativeEntrypointABIValueKind.DESCRIPTOR,
            pointer_depth=1,
            semantic_type_name=semantic_type_name,
            rank=handle.array.rank,
            character_length=handle.array.itemsize if semantic_type_name == "String" else None,
            descriptor_kind=handle.descriptor_kind,
            intent=intent,
        )

    @classmethod
    def _descriptor_callback_parameter(
        cls,
        *,
        semantic_type_name: str,
        rank: int,
        descriptor_kind,
        c_name: str = "callback",
        fortran_name: str = "callback_address",
    ) -> NativeEntrypointABIValuePlan:
        descriptor = cls._value(
            "descriptor",
            NativeEntrypointABIValueKind.DESCRIPTOR,
            pointer_depth=1,
            semantic_type_name=semantic_type_name,
            rank=rank,
            descriptor_kind=descriptor_kind,
            intent="inout",
        )
        context = cls._opaque_parameter("context")
        return cls._value(
            "callback",
            NativeEntrypointABIValueKind.CALLBACK,
            c_name=c_name,
            fortran_name=fortran_name,
            callback_signature=NativeEntrypointSignaturePlan((descriptor, context), cls._void_result()),
        )

    # ------------------------------------------------------------------
    # Callback trampoline boundary
    # ------------------------------------------------------------------

    def _callback_operations(self) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        return tuple(callback.entrypoint.support_procedure for callback in self._callback_sites())

    def _callback_sites(self) -> tuple[CallbackHandoffPlan, ...]:
        return tuple(
            argument.callback
            for function in self.functions
            for argument in sorted(function.arguments, key=lambda item: item.native_position)
            if argument.callback is not None
        )

    def _callback_transfer_parameters(
        self,
        transfer: CallbackTransferPlan,
    ) -> tuple[NativeEntrypointABIValuePlan, ...]:
        base = re.sub(r"\W", "_", transfer.name).casefold()
        if transfer.abi is CallbackABIKind.VALUE:
            return (self._scalar_parameter(transfer.semantic_type_name, role=base),)
        parameters = [self._opaque_parameter(f"{base}_data")]
        if transfer.abi is CallbackABIKind.DATA_AND_SHAPE:
            parameters.extend(self._int64_parameter(f"{base}_extent_{axis}") for axis in range(transfer.rank))
        elif transfer.abi is CallbackABIKind.DATA_AND_LENGTH:
            parameters.append(self._int64_parameter(f"{base}_length"))
        return tuple(parameters)

    def _callback_result_from_plan(self, result) -> NativeEntrypointABIValuePlan:
        transfer = result.transfer
        if result.action is CallbackResultAction.RETURN_VOID:
            return self._void_result()
        if result.action is CallbackResultAction.RETURN_SCALAR and transfer is not None:
            return self._scalar_result(transfer.semantic_type_name)
        return self._opaque_result()

    # ------------------------------------------------------------------
    # Constructors and derived lifecycles
    # ------------------------------------------------------------------

    def _class_constructor_operations(self) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        return tuple(
            self._operation(
                surface.owner_path,
                "class:create",
                f"bind_c_prik_create_{surface.type_identity[1].casefold()}",
                result=self._opaque_result(),
            )
            for surface in self.classes
            if surface.constructor.kind is not ClassConstructorKind.ABSENT
        )

    def _derived_destroy_operation(self, derived: DerivedTypePlan) -> GeneratedSupportProcedureEntrypointPlan:
        return self._operation(
            derived.owner_path,
            "derived:destroy",
            f"bind_c_prik_destroy_{derived.backend_symbol.casefold()}",
            (self._opaque_parameter("address"),),
        )

    def _holder_destroy_operation(
        self, derived: DerivedTypePlan, holder: str
    ) -> GeneratedSupportProcedureEntrypointPlan:
        return self._operation(
            derived.owner_path,
            f"holder:{holder}:destroy",
            f"bind_c_prik_destroy_{derived.backend_symbol.casefold()}_{holder}_holder",
            (self._opaque_parameter("address"),),
        )

    def _holder_presence_operation(
        self, derived: DerivedTypePlan, holder: str
    ) -> GeneratedSupportProcedureEntrypointPlan:
        return self._operation(
            derived.owner_path,
            f"holder:{holder}:present",
            f"bind_c_prik_{derived.backend_symbol.casefold()}_{holder}_holder_present",
            (self._opaque_parameter("address"),),
            self._bool_result(),
        )

    def _owned_derived_types(self) -> tuple[DerivedTypePlan, ...]:
        identities = {
            result.derived.type_identity
            for function in self.functions
            for result in function.results
            if result.derived is not None
            and result.derived.release is DerivedRelease.WRAPPER_DESTROY
            and result.derived.storage
            not in {DerivedObjectStorage.ALLOCATABLE_HOLDER, DerivedObjectStorage.POINTER_HOLDER}
        }
        identities.update(
            variable.derived.handoff.type_identity
            for variable in self.variables
            if variable.derived is not None and variable.derived.access is ModuleObjectAccessMechanism.VALUE_COPY
        )
        identities.update(
            surface.type_identity
            for surface in self.classes
            if surface.constructor.kind is not ClassConstructorKind.ABSENT
        )
        return tuple(derived for derived in self.derived_types if derived.type_identity in identities)

    def _allocatable_holder_types(self) -> tuple[DerivedTypePlan, ...]:
        identities = {
            result.derived.type_identity
            for function in self.functions
            for result in function.results
            if result.derived is not None and result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER
        }
        identities.update(
            argument.derived.type_identity
            for function in self.functions
            for argument in function.arguments
            if argument.derived is not None
            and argument.derived_call is not None
            and any(
                case.access is DerivedActualAccess.ALLOCATABLE_HOLDER
                for case in argument.derived_call.cases
                if case.action is not DerivedCallAction.INCOMPATIBLE
            )
        )
        return tuple(derived for derived in self.derived_types if derived.type_identity in identities)

    def _pointer_holder_types(self) -> tuple[DerivedTypePlan, ...]:
        identities = {
            result.derived.type_identity
            for function in self.functions
            for result in function.results
            if result.derived is not None and result.derived.storage is DerivedObjectStorage.POINTER_HOLDER
        }
        identities.update(
            argument.derived.type_identity
            for function in self.functions
            for argument in function.arguments
            if argument.derived is not None
            and argument.derived_call is not None
            and any(
                case.access is DerivedActualAccess.POINTER_HOLDER
                for case in argument.derived_call.cases
                if case.action is not DerivedCallAction.INCOMPATIBLE
            )
        )
        return tuple(derived for derived in self.derived_types if derived.type_identity in identities)

    def _allocatable_holder_field_types(self) -> tuple[DerivedTypePlan, ...]:
        identities = {
            result.derived.type_identity
            for function in self.functions
            for result in function.results
            if result.derived is not None and result.derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER
        }
        identities.update(
            argument.derived.type_identity
            for function in self.functions
            for argument in function.arguments
            if argument.derived is not None
            and argument.derived_call is not None
            and argument.entrypoint.descriptor_output_role is not None
            and any(
                case.access is DerivedActualAccess.ALLOCATABLE_HOLDER
                for case in argument.derived_call.cases
                if case.action is not DerivedCallAction.INCOMPATIBLE
            )
        )
        return tuple(derived for derived in self.derived_types if derived.type_identity in identities)

    def _pointer_holder_field_types(self) -> tuple[DerivedTypePlan, ...]:
        identities = {
            result.derived.type_identity
            for function in self.functions
            for result in function.results
            if result.derived is not None and result.derived.storage is DerivedObjectStorage.POINTER_HOLDER
        }
        identities.update(
            argument.derived.type_identity
            for function in self.functions
            for argument in function.arguments
            if argument.derived is not None
            and argument.derived_call is not None
            and argument.entrypoint.descriptor_output_role is not None
            and any(
                case.access is DerivedActualAccess.POINTER_HOLDER
                for case in argument.derived_call.cases
                if case.action is not DerivedCallAction.INCOMPATIBLE
            )
        )
        return tuple(derived for derived in self.derived_types if derived.type_identity in identities)

    # ------------------------------------------------------------------
    # Derived fields and module-derived members
    # ------------------------------------------------------------------

    def _derived_field_operations(
        self,
        allocatable_holders: tuple[DerivedTypePlan, ...],
        pointer_holders: tuple[DerivedTypePlan, ...],
    ) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        operations = []
        for derived in self.derived_types:
            # An abstract type has no instance to address, so it publishes no
            # accessor of its own; each concrete extension already generates one
            # for every component it inherits.
            if derived.abstract:
                continue
            for field in derived.fields:
                operations.extend(self._field_operations(derived, field, "direct"))
        for variable in self.variables:
            if variable.derived is None or variable.derived.access is not ModuleObjectAccessMechanism.MEMBER_PROXY:
                continue
            for member in variable.derived.member_paths:
                operations.extend(self._field_operations((variable, member), member.field, "module"))
        for derived in allocatable_holders:
            for field in derived.fields:
                operations.extend(self._field_operations(derived, field, "allocatable"))
        for derived in pointer_holders:
            for field in derived.fields:
                operations.extend(self._field_operations(derived, field, "pointer"))
        return tuple(operations)

    def _field_operations(
        self,
        owner: DerivedTypePlan | tuple[ModuleVariablePlan, DerivedMemberPathPlan],
        field: DerivedFieldPlan,
        route: str,
    ) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        owner_path = self._field_owner_path(owner, field)
        owner_parameter = route != "module"
        if route in {"allocatable", "pointer"}:
            if field.access is not DerivedFieldAccessMechanism.SCALAR_VALUE:
                raise ValueError(f"Unsupported {route}-holder field entrypoint for {field.owner_path!r}")
            return self._scalar_field_operations(owner, field, route, owner_path, owner_parameter=True)
        if field.access is DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE:
            return self._field_handle_operations(owner, field, route, owner_path, owner_parameter)
        if field.access is DerivedFieldAccessMechanism.FIXED_STRING_COPY:
            return self._string_field_operations(owner, field, route, owner_path, owner_parameter)
        if field.access is DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR:
            return self._ordinary_array_field_operations(owner, field, route, owner_path, owner_parameter)
        if route == "module" and field.object_kind is ObjectKind.DERIVED_TYPE:
            return self._nested_module_field_operations(owner, field, route, owner_path)
        return self._scalar_field_operations(
            owner,
            field,
            route,
            owner_path,
            owner_parameter=owner_parameter,
        )

    def _scalar_field_operations(self, owner, field, route, owner_path, *, owner_parameter):
        parameters = (self._opaque_parameter("owner", fortran_name="owner_address"),) if owner_parameter else ()
        result = (
            self._opaque_result()
            if field.object_kind is ObjectKind.DERIVED_TYPE
            else self._scalar_result(field.semantic_type_name)
        )
        operations = [
            self._operation(
                owner_path,
                f"field:{route}:get",
                self._field_symbol(owner, field, route, "get"),
                parameters,
                result,
            )
        ]
        if field.setter_action is SetterAction.WRITE_THROUGH:
            value = (
                self._opaque_parameter("value", fortran_name="value_address")
                if field.object_kind is ObjectKind.DERIVED_TYPE
                else self._scalar_parameter(field.semantic_type_name)
            )
            operations.append(
                self._operation(
                    owner_path,
                    f"field:{route}:set",
                    self._field_symbol(owner, field, route, "set"),
                    (*parameters, value),
                )
            )
        return tuple(operations)

    def _nested_module_field_operations(self, owner, field, route, owner_path):
        if field.setter_action is not SetterAction.WRITE_THROUGH:
            return ()
        return (
            self._operation(
                owner_path,
                f"field:{route}:set",
                self._field_symbol(owner, field, route, "set"),
                (self._opaque_parameter("value", fortran_name="value_address"),),
            ),
        )

    def _string_field_operations(self, owner, field, route, owner_path, owner_parameter):
        owner_values = (self._opaque_parameter("owner", fortran_name="owner_address"),) if owner_parameter else ()
        output = self._value(
            "value",
            NativeEntrypointABIValueKind.CHARACTER,
            pointer_depth=1,
            character_length=field.character_length,
            intent="out",
        )
        operations = [
            self._operation(
                owner_path,
                f"field:{route}:get",
                self._field_symbol(owner, field, route, "get"),
                (*owner_values, output),
            )
        ]
        if field.setter_action is SetterAction.WRITE_THROUGH:
            value = self._value(
                "value",
                NativeEntrypointABIValueKind.CHARACTER,
                pointer_depth=1,
                const=True,
                character_length=field.character_length,
                intent="in",
            )
            operations.append(
                self._operation(
                    owner_path,
                    f"field:{route}:set",
                    self._field_symbol(owner, field, route, "set"),
                    (*owner_values, value),
                )
            )
        return tuple(operations)

    def _ordinary_array_field_operations(self, owner, field, route, owner_path, owner_parameter):
        owner_values = (self._opaque_parameter("owner", fortran_name="owner_address"),) if owner_parameter else ()
        callback = self._descriptor_callback_parameter(
            semantic_type_name=field.semantic_type_name,
            rank=field.array.rank,
            descriptor_kind=None,
        )
        operations = [
            self._operation(
                owner_path,
                f"field:{route}:get",
                self._field_symbol(owner, field, route, "get"),
                (*owner_values, callback, self._opaque_parameter("context")),
            )
        ]
        if field.setter_action is SetterAction.WRITE_THROUGH:
            operations.append(
                self._operation(
                    owner_path,
                    f"field:{route}:set",
                    self._field_symbol(owner, field, route, "set"),
                    (*owner_values, self._opaque_parameter("value", fortran_name="value_address")),
                )
            )
        return tuple(operations)

    def _field_handle_operations(self, owner, field, route, owner_path, owner_parameter):
        handle = field.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Native handle field {field.owner_path!r} has no completed rank")
        owner_values = (self._opaque_parameter("owner", fortran_name="owner_address"),) if owner_parameter else ()
        operations = []
        for operation in handle.operations:
            if operation in _FIELD_HANDLE_LOCAL_OPERATIONS:
                continue
            signature = self._field_handle_signature(field, handle, operation, owner_values)
            operations.append(
                self._operation(
                    owner_path,
                    f"field:{route}:handle:{operation.value}",
                    self._field_handle_symbol(owner, field, route, operation),
                    signature.parameters,
                    signature.result,
                )
            )
        return tuple(operations)

    def _field_handle_signature(self, field, handle, operation, owner_values):
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            return NativeEntrypointSignaturePlan(owner_values, self._bool_result())
        if operation is NativeArrayOperation.ELEMENT_LENGTH:
            return NativeEntrypointSignaturePlan(owner_values, self._int64_result())
        if operation is NativeArrayOperation.SHAPE:
            extents = tuple(
                self._int64_parameter(f"extent_{axis}", reference=True) for axis in range(handle.array.rank)
            )
            return NativeEntrypointSignaturePlan((*owner_values, *extents), self._void_result())
        if operation is NativeArrayOperation.DESCRIPTOR:
            callback = self._descriptor_callback_parameter(
                semantic_type_name=field.semantic_type_name,
                rank=handle.array.rank,
                descriptor_kind=handle.descriptor_kind,
            )
            return NativeEntrypointSignaturePlan(
                (*owner_values, callback, self._opaque_parameter("context")), self._void_result()
            )
        if operation is NativeArrayOperation.ASSOCIATE:
            source = self._descriptor_parameter("source", handle, field.semantic_type_name, intent="in")
            return NativeEntrypointSignaturePlan((*owner_values, source), self._void_result())
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            extents = tuple(self._int64_parameter(f"extent_{axis}") for axis in range(handle.array.rank))
            return NativeEntrypointSignaturePlan((*owner_values, *extents), self._void_result())
        if operation in {NativeArrayOperation.DEALLOCATE, NativeArrayOperation.NULLIFY}:
            return NativeEntrypointSignaturePlan(owner_values, self._void_result())
        raise ValueError(f"Unsupported native field handle operation {operation.value!r}")

    @staticmethod
    def _field_owner_path(owner, field: DerivedFieldPlan) -> str:
        if isinstance(owner, DerivedTypePlan):
            return f"{owner.owner_path}.{field.name}"
        variable, member = owner
        return ".".join((variable.owner_path, *member.path))

    @staticmethod
    def _derived_field_stem(derived: DerivedTypePlan, field: DerivedFieldPlan) -> str:
        return f"{derived.backend_symbol}_{field.name}".casefold()

    @staticmethod
    def _module_member_stem(variable: ModuleVariablePlan, member: DerivedMemberPathPlan) -> str:
        return "_".join((variable.symbol_name, *member.path)).casefold()

    def _field_symbol(self, owner, field, route, action):
        if isinstance(owner, tuple):
            variable, member = owner
            return f"bind_c_prik_module_field_{self._module_member_stem(variable, member)}_{action}"
        stem = self._derived_field_stem(owner, field)
        prefix = {
            "direct": "bind_c_prik_field",
            "allocatable": "bind_c_prik_allocatable_holder_field",
            "pointer": "bind_c_prik_pointer_holder_field",
        }[route]
        return f"{prefix}_{stem}_{action}"

    def _field_handle_symbol(self, owner, field, route, operation):
        if isinstance(owner, tuple):
            variable, member = owner
            return f"bind_c_prik_module_field_handle_{self._module_member_stem(variable, member)}_{operation.value}"
        return f"bind_c_prik_field_handle_{self._derived_field_stem(owner, field)}_{operation.value}"

    # ------------------------------------------------------------------
    # Owned/default descriptor operations
    # ------------------------------------------------------------------

    def _owned_native_array_operations(self) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        operations = []
        transfers: list[ArgumentTransferPlan | ResultPlan] = [
            result
            for function in self.functions
            for result in function.results
            if result.native_array_handle is not None
            and result.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
            and result.datatype_family.value != "string"
        ]
        transfers.extend(
            argument
            for function in self.functions
            for argument in function.arguments
            if argument.native_array_handle is not None
            and argument.native_array_handle.default_handle.construction
            is NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR
        )
        for transfer in transfers:
            handle = transfer.native_array_handle
            selected = handle.operations if isinstance(transfer, ResultPlan) else handle.default_handle.operations
            for operation in selected:
                if operation not in _OWNED_HANDLE_ENTRYPOINT_OPERATIONS:
                    continue
                signature = self._owned_native_array_signature(transfer, handle, operation)
                preferred = transfer.entrypoint.parameter_name or "result"
                owner = NativeSymbolNames.compact(transfer.owner_path, preferred, limit=38)
                operations.append(
                    self._operation(
                        transfer.owner_path,
                        f"native_array:owned:{operation.value}",
                        f"bind_c_owned_{owner}_{operation.value}",
                        signature.parameters,
                        signature.result,
                    )
                )
        return tuple(operations)

    def _owned_native_array_signature(self, transfer, handle, operation):
        intent = (
            "inout"
            if operation
            in {
                NativeArrayOperation.ASSOCIATE,
                NativeArrayOperation.DEALLOCATE,
                NativeArrayOperation.NULLIFY,
                NativeArrayOperation.DESTROY,
            }
            else "in"
        )
        result = self._descriptor_parameter("result", handle, transfer.semantic_type_name, intent=intent)
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            return NativeEntrypointSignaturePlan((result,), self._bool_result())
        if operation is NativeArrayOperation.SHAPE:
            extents = tuple(
                self._int64_parameter(f"extent_{axis}", reference=True) for axis in range(handle.array.rank)
            )
            return NativeEntrypointSignaturePlan((result, *extents), self._void_result())
        if operation is NativeArrayOperation.ASSOCIATE:
            source = self._descriptor_parameter("source", handle, transfer.semantic_type_name, intent="in")
            return NativeEntrypointSignaturePlan((result, source), self._void_result())
        return NativeEntrypointSignaturePlan((result,), self._void_result())

    # ------------------------------------------------------------------
    # Module variables and native-array module operations
    # ------------------------------------------------------------------

    def _module_variable_operations(self) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        operations = []
        for variable in self.variables:
            operations.extend(self._primary_module_variable_operations(variable))
            if variable.bridge.native_getter_action is ModuleGetterAction.NATIVE_ARRAY_HANDLE:
                operations.extend(self._module_native_array_operations(variable))
            if self._nullable_derived_module_proxy(variable):
                operations.append(
                    self._operation(
                        variable.owner_path,
                        "module:derived:present",
                        f"bind_c_prik_module_{variable.symbol_name.casefold()}_present",
                        result=self._bool_result(),
                    )
                )
        return tuple(operations)

    def _primary_module_variable_operations(self, variable):
        operations = []
        if (
            variable.entrypoint.getter_role is not None
            and variable.bridge.native_getter_action is not ModuleGetterAction.NATIVE_ARRAY_HANDLE
        ):
            if variable.bridge.native_getter_action in {
                ModuleGetterAction.BORROWED_ARRAY_VIEW,
                ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
            }:
                # A character element reports the width its own declaration
                # carries, which for a parameter may come from an initializer.
                width = (
                    (self._int64_parameter("itemsize", reference=True, intent="out"),)
                    if variable.datatype_family is DatatypeFamily.STRING
                    else ()
                )
                parameters = (
                    *width,
                    *(
                        self._int64_parameter(f"extent_{axis}", reference=True, intent="out")
                        for axis in range(variable.array.rank)
                    ),
                )
                result = self._opaque_result()
            elif (
                variable.bridge.native_getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
                and variable.datatype_family is DatatypeFamily.STRING
            ):
                parameters = (self._int64_parameter("length", reference=True, intent="out"),)
                result = self._opaque_result()
            elif variable.bridge.native_getter_action in {
                ModuleGetterAction.NULLABLE_SNAPSHOT,
                ModuleGetterAction.DERIVED_OBJECT,
            }:
                parameters = ()
                result = self._opaque_result()
            elif variable.bridge.native_getter_action is ModuleGetterAction.CHARACTER_VALUE:
                # A character value has no by-value C ABI, so it copies out
                # through the same fixed-width buffer a character field uses.
                parameters = (
                    self._value(
                        "value",
                        NativeEntrypointABIValueKind.CHARACTER,
                        pointer_depth=1,
                        character_length=variable.character_length,
                        intent="out",
                    ),
                )
                result = self._void_result()
            else:
                parameters = ()
                result = self._scalar_result(variable.semantic_type_name)
            operations.append(
                self._operation(
                    variable.owner_path,
                    "module:get",
                    f"bind_c_get_{variable.symbol_name}",
                    parameters,
                    result,
                )
            )
        if variable.entrypoint.setter_role is not None:
            if variable.bridge.native_getter_action is ModuleGetterAction.CHARACTER_VALUE:
                value = self._value(
                    "value",
                    NativeEntrypointABIValueKind.CHARACTER,
                    pointer_depth=1,
                    const=True,
                    character_length=variable.character_length,
                    intent="in",
                )
            else:
                value = self._scalar_parameter(variable.semantic_type_name)
            operations.append(
                self._operation(
                    variable.owner_path,
                    "module:set",
                    f"bind_c_set_{variable.symbol_name}",
                    (value,),
                )
            )
        return tuple(operations)

    def _module_native_array_operations(self, variable):
        handle = variable.native_array_handle
        if handle is None or handle.array.rank is None:
            raise ValueError(f"Module handle {variable.owner_path!r} has no completed operation plan")
        operations = []
        for operation in handle.operations:
            if operation in _MODULE_HANDLE_LOCAL_OPERATIONS:
                continue
            signature = self._module_native_array_signature(variable, handle, operation)
            if signature is None:
                continue
            operations.append(
                self._operation(
                    variable.owner_path,
                    f"module:native_array:{operation.value}",
                    f"bind_c_{variable.symbol_name}_{operation.value}",
                    signature.parameters,
                    signature.result,
                )
            )
        return tuple(operations)

    def _module_native_array_signature(self, variable, handle, operation):
        if operation in {
            NativeArrayOperation.ALLOCATED,
            NativeArrayOperation.ASSOCIATED,
            NativeArrayOperation.CONTIGUOUS,
        }:
            return NativeEntrypointSignaturePlan((), self._bool_result())
        if operation is NativeArrayOperation.ELEMENT_LENGTH:
            return NativeEntrypointSignaturePlan((), self._int64_result())
        if operation is NativeArrayOperation.ARRAY_ACTUAL:
            if self._uses_module_allocatable_descriptor(variable):
                return self._module_descriptor_callback_signature(variable, handle)
            return NativeEntrypointSignaturePlan((), self._opaque_result())
        if operation is NativeArrayOperation.SHAPE:
            extents = tuple(
                self._int64_parameter(f"extent_{axis}", reference=True, intent="out")
                for axis in range(handle.array.rank)
            )
            return NativeEntrypointSignaturePlan(extents, self._void_result())
        if operation is NativeArrayOperation.DESCRIPTOR:
            if self._uses_module_allocatable_descriptor(variable):
                return self._module_descriptor_callback_signature(variable, handle)
            if handle.descriptor_kind.value != "pointer":
                return None
            descriptor = self._descriptor_parameter("descriptor", handle, variable.semantic_type_name, intent="out")
            return NativeEntrypointSignaturePlan((descriptor,), self._void_result())
        if operation is NativeArrayOperation.ASSOCIATE:
            source = self._descriptor_parameter("source", handle, variable.semantic_type_name, intent="in")
            return NativeEntrypointSignaturePlan((source,), self._void_result())
        if operation in {NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE}:
            extents = tuple(self._int64_parameter(f"extent_{axis}") for axis in range(handle.array.rank))
            return NativeEntrypointSignaturePlan(extents, self._void_result())
        if operation in {NativeArrayOperation.DEALLOCATE, NativeArrayOperation.NULLIFY}:
            return NativeEntrypointSignaturePlan((), self._void_result())
        raise ValueError(f"Unsupported module native-array entrypoint {operation.value!r}")

    def _module_descriptor_callback_signature(self, variable, handle):
        callback = self._descriptor_callback_parameter(
            semantic_type_name=variable.semantic_type_name,
            rank=handle.array.rank,
            descriptor_kind=handle.descriptor_kind,
        )
        return NativeEntrypointSignaturePlan((callback, self._opaque_parameter("context")), self._void_result())

    @staticmethod
    def _uses_module_allocatable_descriptor(variable: ModuleVariablePlan) -> bool:
        handle = variable.native_array_handle
        return bool(
            handle is not None
            and handle.descriptor_interop is NativeArrayDescriptorInterop.MODULE_ALLOCATABLE_C_DESCRIPTOR
        )

    @staticmethod
    def _nullable_derived_module_proxy(variable: ModuleVariablePlan) -> bool:
        return bool(
            variable.derived is not None
            and variable.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY
            and variable.derived.handoff.storage
            in {
                DerivedObjectStorage.MODULE_ALLOCATABLE,
                DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
                DerivedObjectStorage.MODULE_POINTER,
            }
        )

    # ------------------------------------------------------------------
    # Derived module-origin transactions
    # ------------------------------------------------------------------

    def _derived_origin_operations(self) -> tuple[GeneratedSupportProcedureEntrypointPlan, ...]:
        operations = []
        for variable in self.variables:
            if variable.derived is None:
                continue
            stem = NativeSymbolNames.compact(variable.owner_path, variable.symbol_name)
            for operation in ("present", "address", "scoped", "checkout", "restore"):
                if not self._derived_origin_supports(variable, operation):
                    continue
                signature = self._derived_origin_signature(operation)
                operations.append(
                    self._operation(
                        variable.owner_path,
                        f"derived_origin:{operation}",
                        f"bind_c_prik_origin_{stem}_{operation}",
                        signature.parameters,
                        signature.result,
                    )
                )
        return tuple(operations)

    def _derived_origin_signature(self, operation):
        if operation == "present":
            return NativeEntrypointSignaturePlan((), self._bool_result())
        if operation == "address":
            return NativeEntrypointSignaturePlan((), self._opaque_result())
        if operation == "scoped":
            callback_signature = NativeEntrypointSignaturePlan(
                (self._opaque_parameter("address"), self._opaque_parameter("context")),
                self._int_result(),
            )
            consumer = self._value(
                "consumer",
                NativeEntrypointABIValueKind.CALLBACK,
                fortran_name="consumer",
                c_type_name="prik_derived_consumer_fn",
                callback_signature=callback_signature,
            )
            return NativeEntrypointSignaturePlan((consumer, self._opaque_parameter("context")), self._int_result())
        if operation == "checkout":
            return NativeEntrypointSignaturePlan(
                (self._opaque_parameter("holder", fortran_name="holder_address", output=True, intent="out"),),
                self._int_result(),
            )
        if operation == "restore":
            return NativeEntrypointSignaturePlan(
                (self._opaque_parameter("holder", fortran_name="holder_address"),), self._int_result()
            )
        raise ValueError(f"Unsupported derived-origin operation {operation!r}")

    @staticmethod
    def _derived_origin_supports(variable: ModuleVariablePlan, operation: str) -> bool:
        storage = variable.derived.handoff.storage
        support = {
            # A derived constant is copied through its getter and needs no
            # persistent-origin operation.
            DerivedObjectStorage.DIRECT: set(),
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
        try:
            operations = support[storage]
        except KeyError as error:
            raise ValueError(
                f"Derived module object {variable.owner_path!r} has unsupported origin storage: {storage.value}"
            ) from error
        return operation in operations
