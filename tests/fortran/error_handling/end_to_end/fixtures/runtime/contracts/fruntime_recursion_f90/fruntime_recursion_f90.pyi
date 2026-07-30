from x2py.contracts import Addr, Arg, Int32, native_call

@native_call([Addr(Arg(0))])
def factorial(
    n: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def add_one(
    n: Int32
) -> Int32: ...
