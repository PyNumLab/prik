"""Public code-generation API for lowering completed wrapper plans.

``CBindingGenerator`` and ``FortranBridgeGenerator`` turn a validated
``ModulePlan`` into typed backend nodes. The selected node records and scalar
registry re-exported here are the shared vocabulary for direct backend use and
printers. Policy completion, plan construction, source rendering, and build
integration remain in their owning stages.
"""

from __future__ import annotations

from .c.binding import CBindingGenerator
from .fortran.bridge import FortranBridgeGenerator
from .nodes import (
    BackendScalarType,
    CAllowThreadsBegin,
    CAllowThreadsEnd,
    CCase,
    CDeclaration,
    CExpressionStatement,
    CFunction,
    CFunctionPrototype,
    CGoto,
    CHeader,
    CIf,
    CInclude,
    CLabel,
    CMacroDefinition,
    CMethodDefEntry,
    CMethodDefTable,
    CModule,
    CModuleDef,
    CModulePropertyEntry,
    CModulePropertySupport,
    CParameter,
    CReturn,
    CSwitch,
    CodeExpression,
    FortranAllocate,
    FortranAssignment,
    FortranCall,
    FortranCase,
    FortranDeclaration,
    FortranDeallocate,
    FortranFunction,
    FortranIf,
    FortranInterface,
    FortranInterfaceProcedure,
    FortranModule,
    FortranParameter,
    FortranPointerAssignment,
    FortranSelectCase,
    FortranUse,
)
from .primitive_scalar_types import PrimitiveScalarTypeRegistry
from .visitor import ClassVisitor, UnsupportedWrapperCodegenNodeError

__all__ = (
    "BackendScalarType",
    "CAllowThreadsBegin",
    "CAllowThreadsEnd",
    "CBindingGenerator",
    "CCase",
    "CDeclaration",
    "CExpressionStatement",
    "CFunction",
    "CFunctionPrototype",
    "CGoto",
    "CHeader",
    "CIf",
    "CInclude",
    "CLabel",
    "CMacroDefinition",
    "CMethodDefEntry",
    "CMethodDefTable",
    "CModule",
    "CModuleDef",
    "CModulePropertyEntry",
    "CModulePropertySupport",
    "CParameter",
    "CReturn",
    "CSwitch",
    "ClassVisitor",
    "CodeExpression",
    "FortranAllocate",
    "FortranAssignment",
    "FortranBridgeGenerator",
    "FortranCall",
    "FortranCase",
    "FortranDeallocate",
    "FortranDeclaration",
    "FortranFunction",
    "FortranIf",
    "FortranInterface",
    "FortranInterfaceProcedure",
    "FortranModule",
    "FortranParameter",
    "FortranPointerAssignment",
    "FortranSelectCase",
    "FortranUse",
    "PrimitiveScalarTypeRegistry",
    "UnsupportedWrapperCodegenNodeError",
)
