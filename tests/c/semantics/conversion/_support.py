"""C parser model to semantic IR conversion tests."""

from dataclasses import asdict

from typing import ClassVar

import pytest

from x2py.parsers.c import parse_c_file, parse_c_project

from x2py.parsers.c.models import (
    CArray,
    CAtomic,
    CBool,
    CChar,
    CComposedType,
    CConst,
    CDiagnostic,
    CDouble,
    CDoubleComplex,
    CEnum,
    CFile,
    CFloat,
    CFloatComplex,
    CFunction,
    CFunctionType,
    CInitializer,
    CInt,
    CLong,
    CLongDouble,
    CLongDoubleComplex,
    CLongLong,
    CMacro,
    CMacroDependency,
    CParameter,
    CPointer,
    CProject,
    CRestrict,
    CShort,
    CSignedChar,
    CSourceLocation,
    CStruct,
    CTypedef,
    CUnion,
    CUnknownType,
    CUnsignedChar,
    CUnsignedInt,
    CUnsignedLong,
    CUnsignedLongLong,
    CUnsignedShort,
    CVariable,
    CVolatile,
    CVoid,
)

from x2py.semantics.c2ir import (
    CToIRConverter,
    c_file_to_semantic_module,
    c_file_to_semantic_modules,
    c_function_to_semantic_function,
    c_parameter_to_semantic_argument,
    c_project_to_semantic_module,
    c_project_to_semantic_modules,
    c_struct_to_semantic_class,
    c_type_to_semantic_type,
)

from x2py.semantics.models import (
    SemanticArgument,
    SemanticClass,
    SemanticField,
    SemanticModule,
    SemanticOrigin,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
)

from x2py.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


from x2py.wrapper_codegen.printers import emit_module, emit_module_stubs


def _function(module, name):
    return next(function for function in module.functions if function.name == name)


def _c_origin(
    *,
    native_name=None,
    native_scope=None,
    source_kind=None,
    source_type=None,
    source_location=None,
    metadata=None,
):
    return {
        "source_language": "c",
        "native_name": native_name,
        "native_scope": native_scope,
        "source_kind": source_kind,
        "source_type": source_type,
        "source_location": source_location or {},
        "metadata": metadata or {},
    }


def _blocker(code, message, item):
    return {"code": code, "message": message, "items": [item]}


def _assert_unsupported_type(semantic_type, *, code, message, owner, source_type):
    _ = (code, message, owner)
    assert semantic_type.name == "CUnsupported"
    assert semantic_type.dtype == "CUnsupported"
    assert semantic_type.metadata == {}
    assert asdict(semantic_type.origin) == _c_origin(
        source_kind="unsupported_type",
        source_type=source_type,
    )


__all__ = (
    "CArray",
    "CAtomic",
    "CBool",
    "CChar",
    "CComposedType",
    "CConst",
    "CDiagnostic",
    "CDouble",
    "CDoubleComplex",
    "CEnum",
    "CFile",
    "CFloat",
    "CFloatComplex",
    "CFunction",
    "CFunctionType",
    "CInitializer",
    "CInt",
    "CLong",
    "CLongDouble",
    "CLongDoubleComplex",
    "CLongLong",
    "CMacro",
    "CMacroDependency",
    "CParameter",
    "CPointer",
    "CProject",
    "CRestrict",
    "CShort",
    "CSignedChar",
    "CSourceLocation",
    "CStruct",
    "CToIRConverter",
    "CTypedef",
    "CUnion",
    "CUnknownType",
    "CUnsignedChar",
    "CUnsignedInt",
    "CUnsignedLong",
    "CUnsignedLongLong",
    "CUnsignedShort",
    "CVariable",
    "CVoid",
    "CVolatile",
    "ClassVar",
    "SemanticArgument",
    "SemanticClass",
    "SemanticField",
    "SemanticModule",
    "SemanticOrigin",
    "SemanticStorageContract",
    "SemanticType",
    "SemanticVariable",
    "_assert_unsupported_type",
    "_c_origin",
    "_function",
    "asdict",
    "c_file_to_semantic_module",
    "c_file_to_semantic_modules",
    "c_function_to_semantic_function",
    "c_parameter_to_semantic_argument",
    "c_project_to_semantic_module",
    "c_project_to_semantic_modules",
    "c_struct_to_semantic_class",
    "c_type_to_semantic_type",
    "emit_module",
    "emit_module_stubs",
    "parse_c_file",
    "parse_c_project",
    "parse_pyi_text",
    "pytest",
)
