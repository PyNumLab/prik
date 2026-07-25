"""Public names used by x2py semantic ``.pyi`` contracts.

The objects in this module exist so generated stubs have one explicit import
source. X2py parses their syntax; applications should not execute contract
expressions at runtime.
"""

from __future__ import annotations

from typing import Annotated as Annotated, Any as Any, Final as Final


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


class _ContractType:
    """Subscriptable and callable placeholder for semantic contract types."""

    def __class_getitem__(cls, item: object) -> type[_ContractType]:
        del item
        return cls

    def __new__(cls, *args: object, **kwargs: object) -> _ContractExpression:
        return _ContractExpression(*args, **kwargs)


def _expression(*args: object, **kwargs: object) -> _ContractExpression:
    return _ContractExpression(*args, **kwargs)


def _decorator(*args: object, **kwargs: object):
    del args, kwargs

    def apply(target):
        return target

    return apply


Bool = _ContractType
Byte = _ContractType
CEnum = _ContractType
Char = _ContractType
Complex64 = _ContractType
Complex128 = _ContractType
Complex256 = _ContractType
Float16 = _ContractType
Float32 = _ContractType
Float64 = _ContractType
Float128 = _ContractType
Int = _ContractType
Int8 = _ContractType
Int16 = _ContractType
Int32 = _ContractType
Int64 = _ContractType
Matrix = _ContractType
SizeT = _ContractType
String = _ContractType
UInt = _ContractType
UInt8 = _ContractType
UInt16 = _ContractType
UInt32 = _ContractType
UInt64 = _ContractType
Vector = _ContractType
Void = _ContractType

Addr = _ContractType
Returns = _ContractType
private = _ContractType

Aliased = _ContractExpression()
Allocatable = _ContractExpression()
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
Pointer = _ContractExpression()
Polymorphic = _ContractExpression()
Strided = _ContractExpression()

Arg = _expression
ArrayCategory = _expression
Bounded = _expression
Destruction = _expression
Finite = _expression
IsPresent = _expression
Len = _expression
Ownership = _expression
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
external = _decorator
hold_gil = _decorator
native_call = _decorator
native_type = _decorator
overload = _decorator
prototype = _decorator
raises = _decorator

CAnonymous = _ContractType
CAnonymousMember = _ContractType
CStruct = _ContractType
CUnion = _ContractType
Opaque = _ContractType
OpaqueHandle = _ContractType
WrappedType = _ContractType


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
        "external",
        "hold_gil",
        "native_call",
        "native_type",
        "overload",
        "prototype",
        "private",
        "raises",
    }
)

CONTRACT_TYPE_NAMES = frozenset(
    {
        "Addr",
        "Allocatable",
        "Annotated",
        "Any",
        "Bool",
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
