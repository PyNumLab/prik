@native_abi("c")
@standalone
def external(value: Float64) -> Float64: ...

@private
@native_abi("c")
def specific(value: Float64) -> Float64: ...

@native_abi("c")
@bind("generic_label")
@overload("specific")
def generic(value: Float64) -> Float64: ...

@native_abi("c")
@bind("callback_label")
@prototype
def callback(value: Float64) -> Float64: ...

class State:
    @native_abi("c")
    @staticmethod
    def reset(value: Float64) -> None: ...
