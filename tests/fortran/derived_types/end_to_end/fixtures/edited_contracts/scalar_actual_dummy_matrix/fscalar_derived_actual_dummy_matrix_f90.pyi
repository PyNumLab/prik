from x2py.contracts import (
    Aliased,
    Allocatable,
    Annotated,
    Arg,
    Bool,
    Int32,
    Pointer,
    Return,
    Returns,
    Value,
    native_call,
    nogil,
)
from matrix_left_types import item as left_item
from matrix_right_types import item as right_item


class item:
    value: Int32


class sequence_item:
    value: Int32


ordinary_module: item
ordinary_module_two: item
target_module: Annotated[item, Aliased]
allocatable_module: Allocatable[item]
allocatable_target_module: Allocatable[Annotated[item, Aliased]]
pointer_module: Pointer[item]


def reset_state() -> None: ...


def clear_allocatable_module() -> None: ...


def clear_allocatable_target_module() -> None: ...


def clear_pointer_module() -> None: ...


def associate_allocation_follower() -> None: ...


def allocation_follower_value() -> Int32: ...


def get_writable_call_count() -> Int32: ...


def make_item(initial: Int32) -> item: ...


def make_sequence_item(initial: Int32) -> sequence_item: ...


@native_call([Arg(0), Return("value", 0)])
def make_target_item(initial: Int32) -> Annotated[item, Aliased]: ...


@native_call([Arg(0), Arg(1), Allocatable(Return("value", 0))])
def make_allocatable_item(initial: Int32, make_present: Bool) -> item | None: ...


@native_call([Arg(0), Arg(1), Allocatable(Return("value", 0))])
def make_allocatable_target_item(
    initial: Int32,
    make_present: Bool,
) -> Annotated[item, Aliased] | None: ...


@native_call([Arg(0)], result=Pointer(Return(0)))
def make_pointer_item(selector: Int32) -> item | None: ...


def read_object(value: item) -> Int32: ...


def read_target(value: Annotated[item, Aliased]) -> Int32: ...


@native_call([Allocatable(Arg(0))])
def read_allocatable(value: item | None) -> Int32: ...


@native_call([Allocatable(Arg(0))])
def read_allocatable_target(value: Annotated[item, Aliased] | None) -> Int32: ...


@native_call([Pointer(Arg(0))])
def read_pointer_input(value: item | None) -> Int32: ...


@native_call([Value(Arg(0))])
def read_value(value: item) -> Int32: ...


@native_call([Value(Arg(0))])
def read_sequence_value(value: sequence_item) -> Int32: ...


@native_call([Arg(0), Arg(1)])
def increment_object(value: item, amount: Int32) -> Returns["value", item]: ...


@native_call([Allocatable(Arg(0)), Arg(1)])
def set_allocatable(value: item | None, new_value: Int32) -> Returns["value", item] | None: ...


@native_call([Allocatable(Arg(0)), Arg(1)])
def set_allocatable_target(
    value: Annotated[item, Aliased] | None,
    new_value: Int32,
) -> Returns["value", Annotated[item, Aliased]] | None: ...


@native_call([Pointer(Arg(0)), Arg(1)])
def set_pointer(value: item | None, selector: Int32) -> Returns["value", item] | None: ...


@native_call(
    [
        Arg(0),
        Arg(1),
        Allocatable(Arg(2)),
        Allocatable(Arg(3)),
        Pointer(Arg(4)),
        Value(Arg(5)),
    ]
)
def read_six_forms(
    object_value: item,
    target_value: Annotated[item, Aliased],
    allocatable_value: item | None,
    allocatable_target_value: Annotated[item, Aliased] | None,
    pointer_value: item | None,
    value_value: item,
) -> Int32: ...


def read_qualified(left: left_item, right: right_item) -> Int32: ...


@native_call([Allocatable(Arg(0)), Allocatable(Arg(1)), Pointer(Arg(2)), Arg(3)])
def mutate_three_descriptors(
    first: item | None,
    second: Annotated[item, Aliased] | None,
    third: item | None,
    amount: Int32,
) -> tuple[
    Returns["first", item] | None,
    Returns["second", Annotated[item, Aliased]] | None,
    Returns["third", item] | None,
]: ...


def read_duplicate(first: item, second: item) -> Int32: ...


def read_optional(first: item | None = None, second: item | None = None) -> Int32: ...


@native_call([Arg(0), Arg(1)])
def mutate_duplicate(
    first: item,
    second: item,
) -> tuple[Returns["first", item], Returns["second", item]]: ...


@nogil
@native_call([Allocatable(Arg(0)), Arg(1)])
def hold_allocatable(
    value: item | None,
    milliseconds: Int32,
) -> Returns["value", item] | None: ...


@nogil
@native_call([Arg(0), Arg(1)])
def hold_object(
    value: item,
    milliseconds: Int32,
) -> Returns["value", item]: ...
