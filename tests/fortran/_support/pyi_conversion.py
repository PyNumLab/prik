import ast

import re

from dataclasses import asdict

from pathlib import Path

import pytest

import prik.pipeline.pyi as pyi_pipeline

from prik.contracts import CONTRACT_SYMBOLS

from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    ADDRESS_ROLE_RAW,
    BIND_TARGET_METADATA,
    NATIVE_ARRAY_DESCRIPTOR_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    PROJECTED_OUTPUT_METADATA,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
    USER_PRIVATE_METADATA,
)

from prik.semantics.fortran2ir import fortran_file_to_semantic_modules

from prik.semantics.native_array_handles import (
    is_native_array_handle,
    native_array_data_type,
    native_array_descriptor_kind,
    native_array_handle_facts,
)

from prik.semantics.models import (
    ProjectionMapping,
    PYTHON_VALUE_IMMUTABLE,
    PYTHON_VALUE_MUTABILITY_METADATA,
    SemanticArgument,
    SemanticConstraint,
    SemanticField,
    SemanticFunction,
    SemanticImport,
    SemanticImportItem,
    SemanticModule,
    SemanticType,
    SemanticVariable,
)

from prik.semantics.pyi2ir import (
    _PyiAstParser,
    _node_text,
    convert_pyi_to_ir,
)

from prik.pipeline.pyi import pyi_file_to_semantic_module, pyi_paths_to_semantic_modules, pyi_text_to_semantic_module

from prik.parsers.pyi import parse_pyi_text as parse_pyi_ast_text

from prik.semantics.native_contract import native_contract_issues

from prik.semantics.policy_completion import complete_semantic_policies


from prik.wrapper_codegen.printers import emit_module

from prik import parse_fortran_file

CONTRACT_IMPORT = f"from prik.contracts import {', '.join(sorted(CONTRACT_SYMBOLS))}\n"


def parse_pyi_text(source: str, *args, **kwargs):
    if "prik.contracts" in source:
        return pyi_text_to_semantic_module(source, *args, **kwargs)
    return pyi_text_to_semantic_module(f"{CONTRACT_IMPORT}{source}", *args, **kwargs)


__all__ = (
    "ADDRESS_ROLE_METADATA",
    "ADDRESS_ROLE_PROJECTION",
    "ADDRESS_ROLE_RAW",
    "BIND_TARGET_METADATA",
    "CONTRACT_IMPORT",
    "CONTRACT_SYMBOLS",
    "NATIVE_ARRAY_DESCRIPTOR_METADATA",
    "OPTIONAL_ABSENT_HANDLE_METADATA",
    "PROJECTED_OUTPUT_METADATA",
    "PYTHON_VALUE_IMMUTABLE",
    "PYTHON_VALUE_MUTABILITY_METADATA",
    "SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA",
    "USER_PRIVATE_METADATA",
    "Path",
    "ProjectionMapping",
    "SemanticArgument",
    "SemanticConstraint",
    "SemanticField",
    "SemanticFunction",
    "SemanticImport",
    "SemanticImportItem",
    "SemanticModule",
    "SemanticType",
    "SemanticVariable",
    "_PyiAstParser",
    "_node_text",
    "asdict",
    "ast",
    "complete_semantic_policies",
    "convert_pyi_to_ir",
    "emit_module",
    "fortran_file_to_semantic_modules",
    "is_native_array_handle",
    "native_array_data_type",
    "native_array_descriptor_kind",
    "native_array_handle_facts",
    "native_contract_issues",
    "parse_fortran_file",
    "parse_pyi_ast_text",
    "parse_pyi_text",
    "pyi_file_to_semantic_module",
    "pyi_paths_to_semantic_modules",
    "pyi_pipeline",
    "pyi_text_to_semantic_module",
    "pytest",
    "re",
)
