from pathlib import Path

import pytest

import prik

from prik.contracts import CONTRACT_SYMBOLS

from prik import parse_fortran_file as parse_fortran_source


from prik.semantics.fortran2ir import (
    fortran_module_to_semantic_module,
)

from prik.pipeline.pyi import pyi_text_to_semantic_module as _parse_pyi_text

from prik.wrapper_codegen.printers import (
    emit_module,
    emit_module_stubs,
    opaque_dependency_modules,
    PyiPrinter,
)
from prik.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner

from prik.semantics.models import (
    PROTOTYPE_REF_METADATA,
    ProjectionMapping,
    RUNTIME_RELEASE_GIL_METADATA,
    RUNTIME_STATUS_ERROR_METADATA,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticImport,
    SemanticMethod,
    SemanticModule,
    SemanticOrigin,
    SemanticPrototype,
    SemanticFunction,
    SemanticField,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
)

from prik.semantics.policy_completion import complete_semantic_policies

OPERATOR_F90_SOURCE = (
    Path(__file__).parents[1] / "generic_interfaces" / "end_to_end" / "fixtures" / "foperators_f90.f90"
)

CONTRACT_IMPORT = f"from prik.contracts import {', '.join(sorted(CONTRACT_SYMBOLS))}\n"


def parse_pyi_text(source: str, *args, **kwargs):
    if "prik.contracts" in source:
        return _parse_pyi_text(source, *args, **kwargs)
    return _parse_pyi_text(f"{CONTRACT_IMPORT}{source}", *args, **kwargs)


def generate_pyi(source: str) -> str:
    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    return emit_module(smod)


def generate_wrapper_artifacts(module: SemanticModule):
    """Generate wrapper sources through the canonical plan implementation."""
    complete_semantic_policies(module)
    return WrapperCodeGenerator().generate(WrapperPlanner().build(module))


def rendered_source(artifacts, suffix: str) -> str:
    """Return the sole rendered source with ``suffix``."""
    matches = [source.text for source in artifacts.sources if source.path.suffix == suffix]
    assert len(matches) == 1
    return matches[0]


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


__all__ = (
    "OPERATOR_F90_SOURCE",
    "PROTOTYPE_REF_METADATA",
    "RUNTIME_RELEASE_GIL_METADATA",
    "RUNTIME_STATUS_ERROR_METADATA",
    "Path",
    "ProjectionMapping",
    "PyiPrinter",
    "SemanticArgument",
    "SemanticArrayContract",
    "SemanticClass",
    "SemanticConstraint",
    "SemanticField",
    "SemanticFunction",
    "SemanticImport",
    "SemanticMethod",
    "SemanticModule",
    "SemanticOrigin",
    "SemanticPrototype",
    "SemanticStorageContract",
    "SemanticType",
    "SemanticVariable",
    "_parse_pyi_text",
    "complete_semantic_policies",
    "emit_module",
    "emit_module_stubs",
    "fortran_module_to_semantic_module",
    "generate_pyi",
    "generate_wrapper_artifacts",
    "normalize",
    "opaque_dependency_modules",
    "parse_fortran_source",
    "parse_pyi_text",
    "prik",
    "pytest",
    "rendered_source",
)
