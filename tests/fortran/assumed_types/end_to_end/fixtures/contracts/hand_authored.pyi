from prik.contracts import AnyNative, Flat, Int32, native_abi


@native_abi("c")
def scalar(x: AnyNative) -> Int32: ...


@native_abi("c")
def assumed_size(x: AnyNative[Flat]) -> Int32: ...


@native_abi("c")
def assumed_shape(x: AnyNative[:]) -> Int32: ...


@native_abi("c")
def assumed_shape_two(x: AnyNative[:, :]) -> Int32: ...


@native_abi("c")
def assumed_shape_three(x: AnyNative[:, :, :]) -> Int32: ...


@native_abi("c")
def assumed_rank(x: AnyNative[...]) -> Int32: ...
