"""Public names used by prik semantic ``.pyi`` contracts.

Most objects in this module are syntax markers parsed from generated stubs.
Concrete primitive scalar types and array descriptor annotations additionally
provide the small runtime constructors documented by prik.
"""

from __future__ import annotations

from typing import Annotated as Annotated, Any as Any, Final as Final

import numpy as np


class _ContractExpression:
    """Placeholder produced when a contract helper is evaluated."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    def __getattr__(self, name: str) -> _ContractExpression:
        return _ContractExpression(self, name)

    def __getitem__(self, item: object) -> _ContractExpression:
        return _ContractExpression(self, item)

    def __call__(self, *args: object, **kwargs: object) -> _ContractExpression:
        return _ContractExpression(self, *args, **kwargs)


class _ContractTypeMeta(type):
    """Preserve contract syntax while constructing supported scalar values."""

    def __getitem__(cls, item: object) -> _ArrayContract:
        return _ArrayContract(cls, item)

    def __call__(cls, *args: object, **kwargs: object) -> object:
        constructor_error = getattr(cls, "_constructor_error", None)
        if constructor_error is not None:
            raise TypeError(constructor_error)
        scalar_factory = getattr(cls, "_scalar_factory", None)
        if scalar_factory is not None:
            if args or kwargs:
                raise TypeError(f"{cls.__name__} default constructor takes no arguments")
            return scalar_factory(*args, **kwargs)
        return _ContractExpression(*args, **kwargs)


class _ContractType(metaclass=_ContractTypeMeta):
    """Base for semantic contract types."""


class _ArrayContract:
    """Runtime description retained by a subscripted contract type."""

    def __init__(self, element_type: type[_ContractType], shape: object) -> None:
        self.element_type = element_type
        self.shape = shape
        self.rank = len(shape) if isinstance(shape, tuple) else 1

    def __getitem__(self, item: object) -> _ContractExpression:
        return _ContractExpression(self, item)

    def __call__(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("ordinary array contract annotations are not constructors; create the array with NumPy")


class _DescriptorContract:
    """Subscriptable allocatable or pointer descriptor marker."""

    def __init__(self, descriptor_kind: str) -> None:
        self.descriptor_kind = descriptor_kind

    def __getitem__(self, item: object) -> _DescriptorHandleContract:
        return _DescriptorHandleContract(self.descriptor_kind, item)

    def __call__(self, *args: object, **kwargs: object) -> _ContractExpression:
        return _ContractExpression(*args, **kwargs)


class _DescriptorHandleContract:
    """Construct one typed, initially empty native array descriptor handle."""

    def __init__(self, descriptor_kind: str, array: object) -> None:
        self.descriptor_kind = descriptor_kind
        self.array = array

    def __call__(self, *args: object, **kwargs: object) -> object:
        if args or kwargs:
            raise TypeError(f"{self.descriptor_kind} handle constructor takes no arguments")
        if not isinstance(self.array, _ArrayContract):
            raise TypeError(f"scalar {self.descriptor_kind} contracts are values, not runtime handles")
        shape_items = self.array.shape if isinstance(self.array.shape, tuple) else (self.array.shape,)
        if self.array.rank <= 0 or Ellipsis in shape_items:
            raise TypeError(f"{self.descriptor_kind} handle constructor requires one concrete positive array rank")
        scalar_dtype = getattr(self.array.element_type, "_scalar_dtype", None)
        if scalar_dtype is None:
            name = getattr(self.array.element_type, "__name__", type(self.array.element_type).__name__)
            raise TypeError(f"{self.descriptor_kind} handle element contract {name!r} has no concrete NumPy dtype")
        from prik.runtime.handles import _native_array_handle_from_contract

        return _native_array_handle_from_contract(
            self.descriptor_kind,
            scalar_dtype,
            self.array.rank,
        )


def _contract_type(
    name: str,
    scalar_factory: object | None = None,
    *,
    constructor_error: str | None = None,
) -> type[_ContractType]:
    namespace = {
        "_scalar_factory": scalar_factory,
        "_constructor_error": constructor_error,
    }
    if scalar_factory is not None:
        namespace["_scalar_dtype"] = np.dtype(scalar_factory)
    return _ContractTypeMeta(name, (_ContractType,), namespace)


def _expression(*args: object, **kwargs: object) -> _ContractExpression:
    return _ContractExpression(*args, **kwargs)


def _decorator(*args: object, **kwargs: object):
    del args, kwargs

    def apply(target):
        return target

    return apply


_CONTRACT_NUMPY_FACTORIES: Final[dict[str, object]] = {
    "Bool": np.bool_,
    "Bool8": np.bool_,
    "Bool16": np.bool_,
    "Bool32": np.bool_,
    "Bool64": np.bool_,
    "Complex64": np.complex64,
    "Complex128": np.complex128,
    "Complex256": np.clongdouble,
    "Float16": np.float16,
    "Float32": np.float32,
    "Float64": np.float64,
    "Float128": np.longdouble,
    "Int8": np.int8,
    "Int16": np.int16,
    "Int32": np.int32,
    "Int64": np.int64,
    "SizeT": np.uintp,
    "UInt8": np.uint8,
    "UInt16": np.uint16,
    "UInt32": np.uint32,
    "UInt64": np.uint64,
}


Bool = _contract_type("Bool", _CONTRACT_NUMPY_FACTORIES["Bool"])
Bool8 = _contract_type("Bool8", _CONTRACT_NUMPY_FACTORIES["Bool8"])
Bool16 = _contract_type("Bool16", _CONTRACT_NUMPY_FACTORIES["Bool16"])
Bool32 = _contract_type("Bool32", _CONTRACT_NUMPY_FACTORIES["Bool32"])
Bool64 = _contract_type("Bool64", _CONTRACT_NUMPY_FACTORIES["Bool64"])
Byte = _contract_type("Byte", constructor_error="Byte has no portable NumPy scalar default")
CEnum = _contract_type("CEnum", constructor_error="CEnum requires a resolved native underlying type")
Char = _contract_type("Char", constructor_error="Char has no portable NumPy scalar default")
Complex64 = _contract_type("Complex64", _CONTRACT_NUMPY_FACTORIES["Complex64"])
Complex128 = _contract_type("Complex128", _CONTRACT_NUMPY_FACTORIES["Complex128"])
Complex256 = _contract_type("Complex256", _CONTRACT_NUMPY_FACTORIES["Complex256"])
Float16 = _contract_type("Float16", _CONTRACT_NUMPY_FACTORIES["Float16"])
Float32 = _contract_type("Float32", _CONTRACT_NUMPY_FACTORIES["Float32"])
Float64 = _contract_type("Float64", _CONTRACT_NUMPY_FACTORIES["Float64"])
Float128 = _contract_type("Float128", _CONTRACT_NUMPY_FACTORIES["Float128"])
Int = _contract_type("Int", constructor_error="Int requires a resolved native width")
Int8 = _contract_type("Int8", _CONTRACT_NUMPY_FACTORIES["Int8"])
Int16 = _contract_type("Int16", _CONTRACT_NUMPY_FACTORIES["Int16"])
Int32 = _contract_type("Int32", _CONTRACT_NUMPY_FACTORIES["Int32"])
Int64 = _contract_type("Int64", _CONTRACT_NUMPY_FACTORIES["Int64"])
Matrix = _contract_type("Matrix")
SizeT = _contract_type("SizeT", _CONTRACT_NUMPY_FACTORIES["SizeT"])
String = _contract_type("String", constructor_error="String requires an explicit native length and encoding contract")
UInt = _contract_type("UInt", constructor_error="UInt requires a resolved native width")
UInt8 = _contract_type("UInt8", _CONTRACT_NUMPY_FACTORIES["UInt8"])
UInt16 = _contract_type("UInt16", _CONTRACT_NUMPY_FACTORIES["UInt16"])
UInt32 = _contract_type("UInt32", _CONTRACT_NUMPY_FACTORIES["UInt32"])
UInt64 = _contract_type("UInt64", _CONTRACT_NUMPY_FACTORIES["UInt64"])
Vector = _contract_type("Vector")
Void = _contract_type("Void", constructor_error="Void is not a runtime value")

Addr = _contract_type("Addr")
Returns = _contract_type("Returns")
private = _contract_type("private")

Aliased = _ContractExpression()
Allocatable = _DescriptorContract("allocatable")
AssumedType = _ContractExpression()
Contiguous = _ContractExpression()
COPY_F = _ContractExpression()
Flat = _ContractExpression()
FortranAllocatable = _ContractExpression()
Immutable = _ContractExpression()
MaybeUnallocated = _ContractExpression()
ORDER_ANY = _ContractExpression()
ORDER_C = _ContractExpression()
ORDER_F = _ContractExpression()
Pointer = _DescriptorContract("pointer")
Polymorphic = _ContractExpression()
Strided = _ContractExpression()

Arg = _expression
ArrayCategory = _expression
Bounded = _expression
Destruction = _expression
Finite = _expression
In = _expression
InOut = _expression
IsPresent = _expression
Len = _expression
Ownership = _expression
Out = _expression
Pass = _expression
PointerAssociation = _expression
PointerPolicy = _expression
Range = _expression
Return = _expression
SourceName = _expression
Transfer = _expression
Value = _expression
Work = _expression

bind = _decorator
nogil = _decorator
native_call = _decorator
native_type = _decorator
overload = _decorator
prototype = _decorator
pure = _decorator
raises = _decorator
standalone = _decorator

CAnonymous = _contract_type("CAnonymous")
CAnonymousMember = _contract_type("CAnonymousMember")
CStruct = _contract_type("CStruct")
CUnion = _contract_type("CUnion")
Opaque = _contract_type("Opaque")
OpaqueHandle = _contract_type("OpaqueHandle")
WrappedType = _contract_type("WrappedType")


CONTRACT_SYMBOLS = frozenset(
    {
        "Addr",
        "Aliased",
        "Allocatable",
        "Annotated",
        "Any",
        "Arg",
        "ArrayCategory",
        "AssumedType",
        "Bool",
        "Bool8",
        "Bool16",
        "Bool32",
        "Bool64",
        "Bounded",
        "Byte",
        "CAnonymous",
        "CAnonymousMember",
        "CEnum",
        "CStruct",
        "CUnion",
        "Char",
        "Complex64",
        "Complex128",
        "Complex256",
        "Contiguous",
        "COPY_F",
        "Destruction",
        "Final",
        "Finite",
        "Flat",
        "Float16",
        "Float32",
        "Float64",
        "Float128",
        "FortranAllocatable",
        "Immutable",
        "In",
        "InOut",
        "Int",
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "IsPresent",
        "Len",
        "Matrix",
        "MaybeUnallocated",
        "Opaque",
        "OpaqueHandle",
        "ORDER_ANY",
        "ORDER_C",
        "ORDER_F",
        "Ownership",
        "Out",
        "Pass",
        "Pointer",
        "PointerAssociation",
        "PointerPolicy",
        "Polymorphic",
        "Range",
        "Return",
        "Returns",
        "SizeT",
        "SourceName",
        "Strided",
        "String",
        "Transfer",
        "UInt",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
        "Value",
        "Vector",
        "Void",
        "Work",
        "WrappedType",
        "bind",
        "nogil",
        "native_call",
        "native_type",
        "overload",
        "prototype",
        "pure",
        "private",
        "raises",
        "standalone",
    }
)

CONTRACT_TYPE_NAMES = frozenset(
    {
        "Addr",
        "Allocatable",
        "Annotated",
        "Any",
        "Bool",
        "Bool8",
        "Bool16",
        "Bool32",
        "Bool64",
        "Byte",
        "CAnonymous",
        "CAnonymousMember",
        "CEnum",
        "CStruct",
        "CUnion",
        "Char",
        "Complex64",
        "Complex128",
        "Complex256",
        "Final",
        "Float16",
        "Float32",
        "Float64",
        "Float128",
        "Int",
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "Matrix",
        "Opaque",
        "OpaqueHandle",
        "Pointer",
        "Returns",
        "SizeT",
        "String",
        "UInt",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
        "Vector",
        "Void",
        "WrappedType",
        "private",
    }
)

__all__ = tuple(sorted(CONTRACT_SYMBOLS))
