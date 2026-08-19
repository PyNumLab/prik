from prik.contracts import Allocatable, Annotated, Arg, Destruction, Int32, Ownership, Pointer, Return, Returns, String, Transfer, native_call

@native_call([Allocatable(Arg(0))])
def grow(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Allocatable(Arg(0))])
def shrink(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Allocatable(Arg(0))])
def drop(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Allocatable(Arg(0))])
def optional_grow(
    value: String[:] | None = ...
) -> Returns["value", String[:]] | None: ...

@native_call([Allocatable(Arg(0)), Allocatable(Arg(1))])
def grow_both(
    first: String[:] | None,
    second: String[:] | None
) -> tuple[Returns["first", String[:]] | None, Returns["second", String[:]] | None]: ...

@native_call([Allocatable(Arg(0)), Return('length', 1)])
def grow_and_measure(
    value: String[:] | None
) -> tuple[Returns["value", String[:]] | None, Int32]: ...

@native_call([Allocatable(Arg(0)), Return('length', 0)])
def measure(
    value: String[:] | None
) -> Int32: ...

@native_call([Allocatable(Return('value', 0))])
def make() -> String[:] | None: ...

@native_call([Allocatable(Arg(0)), Return('length', 0)])
def measure_fixed_allocatable(
    value: String[4] | None
) -> Int32: ...

@native_call([Allocatable(Return('value', 0))])
def make_fixed_allocatable() -> String[4] | None: ...

@native_call([Allocatable(Arg(0))])
def relabel_fixed_allocatable(
    value: String[4] | None
) -> Returns["value", String[4]] | None: ...

@native_call([Allocatable(Arg(0))])
def drop_fixed_allocatable(
    value: String[4] | None
) -> Returns["value", String[4]] | None: ...

@native_call([Pointer(Arg(0)), Return('length', 0)])
def measure_pointer(
    value: Annotated[String[:], Ownership("caller"), Transfer("call_local"), Destruction("call_local")] | None
) -> Int32: ...

@native_call([Pointer(Return('value', 0))])
def point_at_static() -> String[:] | None: ...

@native_call([Pointer(Arg(0))])
def edit_pointer_in_place(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Pointer(Arg(0))])
def reassociate_pointer(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Pointer(Arg(0))])
def deallocate_pointer(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Pointer(Arg(0))])
def nullify_pointer(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Pointer(Arg(0)), Return('length', 0)])
def optional_pointer_measure(
    value: Annotated[String[:], Ownership("caller"), Transfer("call_local"), Destruction("call_local")] | None = ...
) -> Int32: ...

@native_call([Pointer(Arg(0))])
def optional_pointer_edit(
    value: String[:] | None = ...
) -> Returns["value", String[:]] | None: ...

@native_call([Pointer(Arg(0))])
def regrow_pointer(
    value: String[:] | None
) -> Returns["value", String[:]] | None: ...

@native_call([Pointer(Arg(0)), Return('length', 0)])
def measure_fixed_pointer(
    value: Annotated[String[4], Ownership("caller"), Transfer("call_local"), Destruction("call_local")] | None
) -> Int32: ...

@native_call([Pointer(Return('value', 0))])
def point_at_fixed_static() -> String[4] | None: ...

@native_call([Pointer(Arg(0))])
def relabel_fixed_pointer(
    value: String[4] | None
) -> Returns["value", String[4]] | None: ...

@native_call([], result=Allocatable(Return(0)))
def allocatable_result() -> String[:] | None: ...

@native_call([], result=Allocatable(Return(0)))
def fixed_allocatable_result() -> String[4] | None: ...

@native_call([], result=Pointer(Return(0)))
def pointer_result() -> Annotated[String[:], Ownership("python"), Transfer("snapshot_copy"), Destruction("python_refcount")] | None: ...

@native_call([], result=Pointer(Return(0)))
def fixed_pointer_result() -> Annotated[String[4], Ownership("python"), Transfer("snapshot_copy"), Destruction("python_refcount")] | None: ...
