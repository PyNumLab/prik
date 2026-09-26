"""Typed native-array handle and descriptor planning across storage owners."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    NativeArrayDescriptorInterop,
    NativeArrayDescriptorOwnership,
    NativeArrayDestroyBehavior,
    NativeArrayOperation,
    NativeArrayRelease,
    NativeArrayResultAllocation,
    NativeDescriptorHandoffABI,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _native_handle_plan():
    module = parse_pyi_text(
        """
from prik.contracts import (
    Addr,
    Allocatable,
    Annotated,
    Arg,
    Float64,
    Int32,
    MaybeUnallocated,
    Pointer,
    PointerPolicy,
    Return,
    Returns,
    String,
    native_call,
)

def normal(values: Float64[:]) -> Float64: ...
def alloc(values: Allocatable[Float64[:]]) -> Float64: ...
def pointer(values: Pointer[Float64[:]]) -> Float64: ...
def optional(values: Allocatable[Float64[:]] | None = ...) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def replace(
    values: Allocatable[Float64[:]],
    mode: Int32,
) -> Returns["values", Allocatable[Float64[:]]]: ...

@native_call([Addr(Arg(0))])
def make(n: Int32) -> Allocatable[Float64[:]]: ...

@native_call([Addr(Arg(0))])
def maybe_make(n: Int32) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_matrix(n: Int32, m: Int32) -> Allocatable[Float64[:, :]]: ...

@native_call([Arg(0), Allocatable(Return("value", 0))])
def deferred(text: String) -> String | None: ...

def make_names() -> Allocatable[String[:][:]]: ...

def make_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]: ...

@native_call([Arg(0), Return("selected", 0)])
def select_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]: ...

def make_managed_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="wrapper",
        lifetime="wrapper",
        deallocation="deallocate_resize",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="allocate_resize",
        aliasing="descriptor",
        mutability="mutable",
    ),
]: ...

def replace_names(
    names: Allocatable[String[:][:]],
) -> Returns["names", Allocatable[String[:][:]]]: ...
""",
        module_name="memory_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _functions(plan):
    return {function.binding.python_name: function for function in plan.namespaces[0].functions}


def _module_handle_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Aliased, Allocatable, Annotated, Float64, Pointer, PointerAssociation, PointerPolicy, String

module_allocatable: Annotated[Allocatable[Float64[:]], Aliased]
plain_allocatable: Allocatable[Float64[:]]
module_names: Annotated[Allocatable[String[:][:]], Aliased]
module_pointer: Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]
""",
        module_name="memory_module_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _handle_row(handle):
    default_operations = handle.default_handle.operations if handle.default_handle else ()
    return (
        handle.descriptor_kind.value,
        handle.handoff.abi.value,
        handle.descriptor_ownership.value,
        handle.owner_storage.value,
        handle.default_handle.construction.value if handle.default_handle else "none",
        NativeArrayOperation.DESTROY in handle.operations,
        NativeArrayOperation.DESTROY in default_operations,
    )


def test_native_handle_plans_select_one_descriptor_abi_and_release_owner_per_origin():
    """Every descriptor slot names how its descriptor crosses and who destroys it.

    Neither an allocatable nor a pointer argument is established from C.  An
    allocatable cannot be: the standard requires a null base address for that
    attribute.  A pointer could be, but a descriptor C built is not the
    caller's entity, so a callee that re-associates the dummy would change only
    that copy.  Both therefore take the descriptor the Fortran runtime made,
    and a caller-created handle lazily gets wrapper storage its finalizer
    destroys.  Owned results destroy their own descriptor; borrowed module
    descriptors are never destroyed by a handle.
    """
    plan = _native_handle_plan()
    functions = _functions(plan)
    rows = {name: _handle_row(functions[name].arguments[0].native_array_handle) for name in _ARGUMENT_ROWS}
    rows.update({name: _handle_row(functions[name].results[0].native_array_handle) for name in _RESULT_ROWS})
    module_plan = _module_handle_plan()
    rows.update({variable.symbol_name: _handle_row(variable.native_array_handle) for variable in module_plan.variables})

    assert rows == {**_ARGUMENT_ROWS, **_RESULT_ROWS, **_MODULE_ROWS}

    optional = functions["optional"].arguments[0]
    assert optional.native_array_handle.optional_absent is True
    assert optional.native_array_handle.handoff.presence_role == optional.entrypoint.presence_role
    assert functions["alloc"].arguments[0].native_array_handle.handoff.presence_role is None
    assert functions["maybe_make"].results[0].native_array_handle.result_allocation is (
        NativeArrayResultAllocation.MAYBE_UNALLOCATED
    )
    assert functions["select_pointer"].results[0].source_kind == "hidden_output"
    deferred = functions["deferred"].results[0]
    assert deferred.native_array_handle is None
    assert deferred.scalar_descriptor.runtime_length is True
    # Only a deferred length needs a width to allocate from its extents.
    assert functions["make_names"].results[0].native_array_handle.element_length_argument is True
    assert functions["make"].results[0].native_array_handle.element_length_argument is False
    assert plan.required_headers == module_plan.required_headers == ("ISO_Fortran_binding.h",)


_LAZY_ARGUMENT = ("direct_standard_descriptor", "borrowed", "borrowed_entity", "lazy_owned_descriptor", False, True)
_OWNED_RESULT = ("owned_result_storage", "owned", "c_descriptor", "none", True, False)
_BORROWED_MODULE = ("direct_standard_descriptor", "borrowed", "borrowed_entity", "none", False, False)
_ARGUMENT_ROWS = {
    "alloc": ("allocatable", *_LAZY_ARGUMENT),
    "pointer": ("pointer", *_LAZY_ARGUMENT),
    "optional": ("allocatable", *_LAZY_ARGUMENT),
    "replace": ("allocatable", *_LAZY_ARGUMENT),
    "replace_names": (
        "allocatable",
        "direct_standard_descriptor",
        "borrowed",
        "fortran_owner",
        "lazy_fortran_owner",
        False,
        True,
    ),
}
_RESULT_ROWS = {
    "make": ("allocatable", *_OWNED_RESULT),
    "maybe_make": ("allocatable", *_OWNED_RESULT),
    "make_matrix": ("allocatable", *_OWNED_RESULT),
    "make_names": ("allocatable", "fortran_owner", "owned", "fortran_owner", "none", True, False),
    "make_pointer": ("pointer", *_OWNED_RESULT),
    "select_pointer": ("pointer", *_OWNED_RESULT),
    "make_managed_pointer": ("pointer", *_OWNED_RESULT),
}
_MODULE_ROWS = {
    "module_allocatable": ("allocatable", *_BORROWED_MODULE),
    "plain_allocatable": ("allocatable", *_BORROWED_MODULE),
    "module_names": ("allocatable", *_BORROWED_MODULE),
    "module_pointer": ("pointer", *_BORROWED_MODULE),
}


def test_absent_optional_allocatable_gets_an_unallocated_placeholder_descriptor():
    """The absent branch pairs a null-address allocatable descriptor with a present flag.

    A null base address is the only form the standard lets C establish for this
    attribute (ifx rejects any other), and absence is when there is nothing to
    point at.
    """
    artifacts = WrapperGenerator().generate(_native_handle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    optional_start = bridge_source.index("function bind_c_optional(")
    optional_bridge = bridge_source[
        optional_start : bridge_source.index("end function bind_c_optional", optional_start)
    ]
    assert "type(c_ptr), value :: bound_values_present" in optional_bridge
    optional_c_start = c_source.index("static PyObject * wrap_optional(")
    optional_binding = c_source[optional_c_start : c_source.index("static PyObject * wrap_replace(", optional_c_start)]
    assert "CFI_establish((CFI_cdesc_t *)&bound_values_storage, NULL, CFI_attribute_allocatable" in optional_binding


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("required_presence", "inconsistent-native-descriptor-presence"),
        ("owned_storage", "invalid-owned-native-descriptor-roles"),
        ("default_storage", "inconsistent-default-handle-owner-storage-role"),
        ("default_ownership", "invalid-default-handle-descriptor-ownership"),
        ("default_lifecycle", "invalid-default-handle-lifecycle"),
        ("default_operation", "incomplete-default-handle-operations"),
        ("default_roles", "inconsistent-default-handle-operation-roles"),
        ("default_abi", "inconsistent-default-handle-descriptor-abi"),
        ("operation", "incomplete-native-array-operations"),
        ("header", "inconsistent-required-headers"),
    ],
)
def test_native_handle_plan_edits_fail_central_validation(edit: str, diagnostic: str):
    plan = _native_handle_plan()
    functions = _functions(plan)
    if edit == "required_presence":
        functions["alloc"].arguments[0].native_array_handle.handoff.presence_role = "edited:present"
    elif edit == "owned_storage":
        functions["make"].results[0].native_array_handle.handoff.owner_storage_role = None
    elif edit == "default_storage":
        functions["replace"].arguments[0].native_array_handle.default_handle.owner_storage_role = None
    elif edit == "default_ownership":
        functions["replace"].arguments[
            0
        ].native_array_handle.default_handle.descriptor_ownership = NativeArrayDescriptorOwnership.BORROWED
    elif edit == "default_lifecycle":
        default = functions["replace"].arguments[0].native_array_handle.default_handle
        default.release = NativeArrayRelease.NONE
        default.destroy_behavior = NativeArrayDestroyBehavior.NONE
    elif edit == "default_operation":
        functions["replace"].arguments[0].native_array_handle.default_handle.operations = ()
    elif edit == "default_roles":
        functions["replace"].arguments[0].native_array_handle.default_handle.operation_roles = ()
    elif edit == "default_abi":
        functions["replace"].arguments[
            0
        ].native_array_handle.handoff.abi = NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    elif edit == "operation":
        functions["pointer"].arguments[0].native_array_handle.operations = ()
    else:
        plan.required_headers = ()

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


def test_plain_module_descriptor_view_requires_matching_completed_interop():
    plan = _module_handle_plan()
    plain = next(variable for variable in plan.variables if variable.symbol_name == "plain_allocatable")
    assert plain.native_array_handle is not None
    plain.native_array_handle.descriptor_interop = NativeArrayDescriptorInterop.NONE
    plain.native_array_handle.required_headers = ()

    with pytest.raises(ValueError, match="missing-module-allocatable-descriptor-interop"):
        WrapperGenerator().generate(plan)
