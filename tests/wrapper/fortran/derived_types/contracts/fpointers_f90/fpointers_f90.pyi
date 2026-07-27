from x2py.contracts import Addr, Aliased, Annotated, Arg, Destruction, Float64, Int32, Ownership, Pointer, PointerAssociation, Return, Transfer, native_call

@native_call([Pointer(Arg(0))])
def read_pointer(
    value: Annotated[Float64, Ownership("caller"), Transfer("call_local"), Destruction("call_local")] | None
) -> Float64: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))], result=Pointer(Return(0)))
def pointer_to_scalar(
    value: Annotated[Float64, Aliased],
    use_value: Int32
) -> Annotated[Float64, Ownership("python"), Transfer("snapshot_copy"), Destruction("python_refcount")] | None: ...

def sum_pointer(
    values: Annotated[Pointer[Float64[:]], PointerAssociation("runtime"), Ownership("caller"), Transfer("call_local"), Destruction("none")]
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def pointer_to_values(
    values: Annotated[Float64[::], Aliased],
    use_values: Int32
) -> Annotated[Pointer[Float64[:]], PointerAssociation("runtime")]: ...
