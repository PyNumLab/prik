import json

import re

from dataclasses import asdict

import pytest

from x2py.parsers.fortran.models import (
    FortranArgument,
    FortranBlockData,
    FortranDerivedType,
    FortranFile,
    FortranModule,
    FortranProgram,
    FortranProject,
    FortranProcedureSignature,
    FortranSubmodule,
    FortranUseMapping,
    FortranVariable,
)

from x2py import parse_fortran_file as parse_fortran_source

from x2py import parse_fortran_project

from x2py.semantics.fortran2ir import (
    FortranToIRConverter,
    _compile_time_requirement_message,
    _iter_fortran_variable_contexts,
    _requirement_unit_name,
    _resolve_compile_time_text,
    collect_fortran_type_storage_requirements,
    collect_semantic_compile_time_requirements,
    fortran_type_storage_expression,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    fortran_project_to_semantic_modules,
    resolve_semantic_compile_time_values,
)

from x2py.semantics import models as semantic_models

from x2py.semantics.native_contract import native_contract_issues

from x2py.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text

from x2py.semantics.metadata import SCALAR_STORAGE_CATEGORY


from x2py.wrapper_codegen.printers import emit_module

from x2py.semantics.models import (
    ProjectionMapping,
    SemanticArgument,
    SemanticField,
    SemanticMethod,
    SemanticModule,
    SemanticClass,
    SemanticFunction,
    SemanticConstraint,
    SemanticType,
    SemanticVariable,
)


def get_function(module: SemanticModule, name: str) -> SemanticFunction:
    for f in module.functions:
        if f.name == name:
            return f

    raise AssertionError(f"Function '{name}' not found")


def get_class(module: SemanticModule, name: str) -> SemanticClass:
    for c in module.classes:
        if c.name == name:
            return c

    raise AssertionError(f"Class '{name}' not found")


def has_constraint(obj, name: str) -> bool:
    return any(c.name == name for c in obj.constraints)


def array_contract(semantic_type: SemanticType):
    assert semantic_type.storage is not None
    assert semantic_type.storage.array is not None
    return semantic_type.storage.array


__all__ = (
    "SCALAR_STORAGE_CATEGORY",
    "FortranArgument",
    "FortranBlockData",
    "FortranDerivedType",
    "FortranFile",
    "FortranModule",
    "FortranProcedureSignature",
    "FortranProgram",
    "FortranProject",
    "FortranSubmodule",
    "FortranToIRConverter",
    "FortranUseMapping",
    "FortranVariable",
    "ProjectionMapping",
    "SemanticArgument",
    "SemanticClass",
    "SemanticConstraint",
    "SemanticField",
    "SemanticFunction",
    "SemanticMethod",
    "SemanticModule",
    "SemanticType",
    "SemanticVariable",
    "_compile_time_requirement_message",
    "_iter_fortran_variable_contexts",
    "_requirement_unit_name",
    "_resolve_compile_time_text",
    "array_contract",
    "asdict",
    "collect_fortran_type_storage_requirements",
    "collect_semantic_compile_time_requirements",
    "emit_module",
    "fortran_file_to_semantic_modules",
    "fortran_module_to_semantic_module",
    "fortran_project_to_semantic_modules",
    "fortran_type_storage_expression",
    "get_class",
    "get_function",
    "has_constraint",
    "json",
    "native_contract_issues",
    "parse_fortran_project",
    "parse_fortran_source",
    "parse_pyi_text",
    "pytest",
    "re",
    "resolve_semantic_compile_time_values",
    "semantic_models",
)
