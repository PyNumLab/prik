"""Carry completed native-array handle policy into planning and build setup.

``completion`` attaches ``NativeArrayHandlePolicy`` records to descriptor-backed
array declarations. This module does not infer their ownership, lifetime, or
operations. It provides immutable ABI selectors and dispatchers for lower
stages, plus ``native_array_handle_build_requirements`` to collect generated
header requirements from completed semantic modules.

Ordinary arrays select the data-buffer ABI; native allocatable and pointer
handles select the descriptor ABI. Missing completed policy is an error rather
than a reason to choose a fallback.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from prik.semantics.models import (
    RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    ProcedureOverloadSet,
    SemanticClass,
    SemanticFunction,
    SemanticModule,
    SemanticType,
    SemanticVariable,
)
from prik.semantics.native_array_handles import native_array_descriptor_kind


NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER = "ISO_Fortran_binding.h"


@dataclass(frozen=True)
class NativeArrayHandlePolicy:
    """Completed post-IR policy for a native allocatable or pointer array handle."""

    descriptor_kind: str
    handle_kind: str
    origin: str
    owner: str
    owner_retention: str
    descriptor_ownership: str
    borrowed: bool
    getter_behavior: str
    python_setter: str
    native_setter: str
    output_projection: str
    result_allocation: str
    release: str
    target_lifetime: str
    destroy_behavior: str
    to_numpy: str
    descriptor_interop: str
    nullable: bool
    optional_absent: bool
    storage_mode: str
    operations: tuple[str, ...] = ()
    blocker: str | None = None
    default_construction: str = "none"
    default_descriptor_ownership: str = "unknown"
    default_release: str = "none"
    default_destroy_behavior: str = "none"
    default_operations: tuple[str, ...] = ()

    @property
    def is_blocked(self) -> bool:
        """Return whether this completed policy blocks wrapper generation."""
        return self.handle_kind == "unsupported" or self.blocker is not None

    def allows(self, operation: str) -> bool:
        """Return whether a descriptor operation is explicitly permitted."""
        return operation in self.operations

    @property
    def requires_pointer_c_descriptor_interop(self) -> bool:
        """Return whether this handle path needs TS 29113 C descriptor interop."""
        return self.descriptor_interop == "pointer_c_descriptor"

    @property
    def requires_c_descriptor_interop(self) -> bool:
        """Return whether generated code needs standard C descriptor support."""
        return self.descriptor_interop in {
            "module_allocatable_c_descriptor",
            "owned_allocatable_c_descriptor",
            "pointer_c_descriptor",
        }


@dataclass(frozen=True)
class ArrayInteropPolicy:
    """Completed selector for the ABI lane used by an array-like boundary."""

    abi: str
    owner: str
    descriptor_kind: str | None = None
    handle_kind: str | None = None

    @property
    def is_data_buffer(self) -> bool:
        """Return whether this boundary uses ordinary data-pointer array ABI."""
        return self.abi == "data_buffer"

    @property
    def is_descriptor(self) -> bool:
        """Return whether this boundary uses native descriptor-handle ABI."""
        return self.abi == "descriptor"


@dataclass(frozen=True)
class ArrayInteropPolicyDispatcher:
    """Dispatch array-like bridge/binding work from the completed ABI selector."""

    handlers: Mapping[tuple[str, str], str]

    def handler_name_for_policy(self, policy: ArrayInteropPolicy, context: str, name: str) -> str:
        key = (context, policy.abi)
        try:
            return self.handlers[key]
        except KeyError:
            raise ValueError(f"No array interop codegen handler for {name!r}: {context}/{policy.abi}") from None

    def dispatch(
        self,
        target: Any,
        subject: Any,
        policy: ArrayInteropPolicy,
        context: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        name = str(getattr(subject, "name", getattr(subject, "python_name", type(subject).__name__)))
        handler = getattr(target, self.handler_name_for_policy(policy, context, name))
        return handler(subject, policy, *args, **kwargs)


@dataclass(frozen=True)
class NativeArrayHandlePolicyDispatcher:
    """Dispatch generated handle work from completed native-array policy."""

    handlers: Mapping[tuple[str, str], str]

    def handler_name_for_policy(self, policy: NativeArrayHandlePolicy, name: str) -> str:
        key = (policy.descriptor_kind, policy.handle_kind)
        try:
            return self.handlers[key]
        except KeyError:
            descriptor_kind, handle_kind = key
            raise ValueError(
                f"No native-array-handle codegen handler for {name!r}: {descriptor_kind}/{handle_kind}"
            ) from None

    def dispatch(
        self,
        target: Any,
        subject: Any,
        policy: NativeArrayHandlePolicy,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        name = str(getattr(subject, "name", getattr(subject, "python_name", type(subject).__name__)))
        handler = getattr(target, self.handler_name_for_policy(policy, name))
        return handler(subject, policy, *args, **kwargs)


@dataclass(frozen=True)
class NativeArrayOutputProjectionDispatcher:
    """Dispatch handle boundary work from completed output projection."""

    handlers: Mapping[str, str]

    def dispatch(
        self,
        target: Any,
        subject: Any,
        policy: NativeArrayHandlePolicy,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        try:
            handler_name = self.handlers[policy.output_projection]
        except KeyError:
            name = str(getattr(subject, "name", getattr(subject, "python_name", type(subject).__name__)))
            raise ValueError(
                f"No native-array output-projection handler for {name!r}: {policy.output_projection}"
            ) from None
        return getattr(target, handler_name)(subject, policy, *args, **kwargs)


@dataclass(frozen=True)
class NativeArrayBuildRequirement:
    """One build requirement selected by a completed native-array handle policy."""

    owner: str
    item: str
    descriptor_kind: str
    handle_kind: str
    descriptor_interop: str
    headers: tuple[str, ...]


@dataclass(frozen=True)
class NativeArrayBuildRequirements:
    """Build requirements selected by all completed native-array handle policies."""

    pointer_c_descriptor_interop: bool
    headers: tuple[str, ...]
    items: tuple[NativeArrayBuildRequirement, ...]

    @property
    def requires_iso_fortran_binding(self) -> bool:
        """Return whether generated wrapper C code needs ISO_Fortran_binding.h."""
        return NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER in self.headers


def array_interop_policy(
    semantic_type: SemanticType | None,
    *,
    owner: str,
    native_array_handle_policy: NativeArrayHandlePolicy | None = None,
) -> ArrayInteropPolicy | None:
    """Return the completed ABI selector for an array-like boundary."""
    if native_array_handle_policy is not None:
        return ArrayInteropPolicy(
            abi="descriptor",
            owner=owner,
            descriptor_kind=native_array_handle_policy.descriptor_kind,
            handle_kind=native_array_handle_policy.handle_kind,
        )
    if semantic_type is None:
        return None
    storage = semantic_type.storage
    if semantic_type.rank > 0 and storage is not None and storage.array is not None:
        return ArrayInteropPolicy(abi="data_buffer", owner=owner)
    return None


def native_array_handle_build_requirements(
    semantic_ir: SemanticModule | Iterable[SemanticModule],
) -> NativeArrayBuildRequirements:
    """Return build requirements selected by completed native-array handle policies."""
    modules = [semantic_ir] if isinstance(semantic_ir, SemanticModule) else list(semantic_ir)
    requirements = tuple(
        _c_descriptor_requirement(owner, item, policy)
        for owner, item, policy in _iter_native_array_handle_policies(modules)
        if policy.requires_c_descriptor_interop
    )
    headers = (NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER,) if requirements else ()
    return NativeArrayBuildRequirements(
        pointer_c_descriptor_interop=any(
            requirement.descriptor_interop == "pointer_c_descriptor" for requirement in requirements
        ),
        headers=headers,
        items=requirements,
    )


def _c_descriptor_requirement(
    owner: str,
    item: str,
    policy: NativeArrayHandlePolicy,
) -> NativeArrayBuildRequirement:
    return NativeArrayBuildRequirement(
        owner=owner,
        item=item,
        descriptor_kind=policy.descriptor_kind,
        handle_kind=policy.handle_kind,
        descriptor_interop=policy.descriptor_interop,
        headers=(NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER,),
    )


def _iter_native_array_handle_policies(modules: Iterable[SemanticModule]):
    for module in modules:
        for variable in module.variables:
            yield from _variable_native_array_policy(variable, owner=f"{module.name}.{variable.name}")
        for semantic_class in module.classes:
            yield from _iter_class_native_array_policies(semantic_class, owner=f"{module.name}.{semantic_class.name}")
        for function in module.functions:
            yield from _iter_function_native_array_policies(function, owner=f"{module.name}.{function.name}")
        for overload_set in module.overload_sets:
            yield from _iter_overload_native_array_policies(overload_set, owner=f"{module.name}.{overload_set.name}")


def _iter_class_native_array_policies(semantic_class: SemanticClass, *, owner: str):
    for field in semantic_class.fields:
        yield from _variable_native_array_policy(field, owner=f"{owner}.{field.name}")
    for nested in semantic_class.classes:
        yield from _iter_class_native_array_policies(nested, owner=f"{owner}.{nested.name}")
    for method in semantic_class.methods:
        yield from _iter_function_native_array_policies(method, owner=f"{owner}.{method.name}")
    for overload_set in semantic_class.overload_sets:
        yield from _iter_overload_native_array_policies(overload_set, owner=f"{owner}.{overload_set.name}")


def _iter_overload_native_array_policies(overload_set: ProcedureOverloadSet, *, owner: str):
    for procedure in overload_set.procedures:
        yield from _iter_function_native_array_policies(procedure, owner=owner)


def _iter_function_native_array_policies(function: SemanticFunction, *, owner: str):
    for argument in function.arguments:
        yield from _variable_native_array_policy(argument, owner=f"{owner}.{argument.name}")
    if native_array_descriptor_kind(function.return_type) is not None:
        policy = function.metadata.get(RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA)
        if policy is None:
            raise ValueError(
                f"Native array handle {owner}.return is missing completed policy; "
                "run complete_semantic_policies before collecting build requirements"
            )
        yield f"{owner}.return", "return", policy


def _variable_native_array_policy(variable: SemanticVariable, *, owner: str):
    if native_array_descriptor_kind(variable.semantic_type) is None:
        return
    policy = variable.metadata.get(RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA)
    if policy is None:
        raise ValueError(
            f"Native array handle {owner} is missing completed policy; "
            "run complete_semantic_policies before collecting build requirements"
        )
    yield owner, variable.name, policy


__all__ = (
    "NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER",
    "ArrayInteropPolicy",
    "ArrayInteropPolicyDispatcher",
    "NativeArrayBuildRequirement",
    "NativeArrayBuildRequirements",
    "NativeArrayHandlePolicy",
    "NativeArrayHandlePolicyDispatcher",
    "array_interop_policy",
    "native_array_handle_build_requirements",
)


if __name__ == "__main__":
    from prik.semantics.models import (
        RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
        SemanticArrayContract,
        SemanticModule,
        SemanticStorageContract,
        SemanticType,
        SemanticVariable,
    )
    from prik.semantics.native_array_handles import mark_native_array_handle

    example_type = SemanticType(
        "Float64",
        rank=1,
        dtype="float64",
        shape=["n"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=["n"], pointer=True),
        ),
    )
    mark_native_array_handle(example_type, "pointer")
    example_policy = NativeArrayHandlePolicy(
        descriptor_kind="pointer",
        handle_kind="pointer",
        origin="module",
        owner="native",
        owner_retention="native",
        descriptor_ownership="borrowed",
        borrowed=True,
        getter_behavior="view",
        python_setter="blocked",
        native_setter="reassociate",
        output_projection="handle",
        result_allocation="none",
        release="none",
        target_lifetime="owner",
        destroy_behavior="nullify",
        to_numpy="borrowed_view",
        descriptor_interop="pointer_c_descriptor",
        nullable=True,
        optional_absent=False,
        storage_mode="alias",
        operations=("to_numpy", "nullify"),
    )
    example_variable = SemanticVariable(
        "values",
        example_type,
        metadata={RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA: example_policy},
    )
    example_module = SemanticModule("state", variables=[example_variable])
    example_interop = array_interop_policy(
        example_type,
        owner="state.values",
        native_array_handle_policy=example_policy,
    )
    example_requirements = native_array_handle_build_requirements(example_module)

    print(
        f"Handle policy: {example_policy.descriptor_kind}/{example_policy.handle_kind}, "
        f"storage={example_policy.storage_mode}"
    )
    print(f"Allowed operations: {', '.join(example_policy.operations)}")
    print(f"Array ABI: {example_interop.abi}")
    print(f"Selected build header: {example_requirements.headers[0]}")
