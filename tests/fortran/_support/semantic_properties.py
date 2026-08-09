"""Property-based invariants for semantic-IR transformations."""

from __future__ import annotations

from dataclasses import asdict

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, strategies as st

from prik.semantics.fortran2ir import fortran_file_to_semantic_modules, resolve_semantic_compile_time_values

from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    OwnershipPolicy,
    ProjectionMapping,
    SemanticArgument,
    SemanticArrayContract,
    SemanticConstraint,
    SemanticFunction,
    SemanticModule,
    SemanticStorageContract,
    SemanticType,
)

from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text

from prik.codegen.printers import emit_module

from prik import parse_fortran_file

_FORTRAN_SCALAR_TYPES = st.sampled_from(
    [
        ("integer", "Int32"),
        ("logical", "Bool"),
        ("real", "Float32"),
        ("real(4)", "Float32"),
    ]
)

_FORTRAN_VALUE_TYPES = st.sampled_from(
    [
        ("logical", "Bool"),
        ("real(8)", "Float64"),
        ("real", "Float32"),
    ]
)

_SEMANTIC_SCALAR_TYPES = st.sampled_from(["Bool", "Float32", "Float64", "Int32"])

_PYI_IDENTIFIER_STEMS = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True)

_NATIVE_NAMES = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_ -!\"'\\\n\t",
    min_size=1,
    max_size=12,
)


@st.composite
def fortran_scalar_subroutines(draw):
    parameter_ids = draw(st.lists(st.integers(min_value=0, max_value=99), max_size=6, unique=True))
    parameter_types = draw(st.lists(_FORTRAN_SCALAR_TYPES, min_size=len(parameter_ids), max_size=len(parameter_ids)))
    parameters = [f"p_{parameter_id}" for parameter_id in parameter_ids]
    declarations = "".join(
        f"  {source_type}, intent(in), value :: {parameter}\n"
        for parameter, (source_type, _semantic_type) in zip(parameters, parameter_types, strict=True)
    )
    source = f"subroutine transform({', '.join(parameters)})\n{declarations}end subroutine transform\n"
    expected_parameters = [
        (parameter, semantic_type)
        for parameter, (_source_type, semantic_type) in zip(parameters, parameter_types, strict=True)
    ]
    return source, expected_parameters


@st.composite
def canonical_semantic_types(draw):
    name = draw(_SEMANTIC_SCALAR_TYPES)
    storage_kind = draw(st.sampled_from(["value", "reference", "array"]))
    read_only = draw(st.booleans())
    constraints = [SemanticConstraint("Finite")] if draw(st.booleans()) else []
    ownership = OwnershipPolicy(mutable=not read_only)

    if storage_kind == "value":
        storage = SemanticStorageContract(kind="value", read_only=True) if read_only else None
        return SemanticType(
            name=name,
            dtype=name,
            constraints=constraints,
            ownership=OwnershipPolicy(),
            storage=storage,
        )

    if storage_kind == "reference":
        storage = SemanticStorageContract(
            kind="reference",
            read_only=read_only,
            mutable=not read_only,
            pointer_depth=1,
        )
        return SemanticType(
            name=name,
            dtype=name,
            constraints=constraints,
            ownership=ownership,
            storage=storage,
        )

    shape = [str(bound) for bound in draw(st.lists(st.integers(min_value=1, max_value=32), min_size=1, max_size=3))]
    order = draw(st.sampled_from(["default", "ORDER_F", "ORDER_ANY"]))
    if order == "default":
        order = "ORDER_C" if len(shape) > 1 else None
    descriptor = draw(st.sampled_from(("none", "allocatable", "pointer")))
    array = SemanticArrayContract(
        rank=len(shape),
        shape=list(shape),
        order=order,
        axes=["dense" for _dimension in shape],
        contiguous=True,
        allocatable=descriptor == "allocatable",
        pointer=descriptor == "pointer",
    )
    storage = SemanticStorageContract(
        kind="array",
        read_only=read_only,
        mutable=not read_only,
        array=array,
    )
    return SemanticType(
        name=name,
        dtype=name,
        rank=len(shape),
        shape=list(shape),
        constraints=constraints,
        ownership=ownership,
        storage=storage,
    )


__all__ = (
    "EXTERNAL_TYPE_REF_METADATA",
    "_FORTRAN_VALUE_TYPES",
    "_NATIVE_NAMES",
    "_PYI_IDENTIFIER_STEMS",
    "ProjectionMapping",
    "SemanticArgument",
    "SemanticArrayContract",
    "SemanticConstraint",
    "SemanticFunction",
    "SemanticModule",
    "SemanticStorageContract",
    "SemanticType",
    "asdict",
    "canonical_semantic_types",
    "emit_module",
    "fortran_file_to_semantic_modules",
    "fortran_scalar_subroutines",
    "given",
    "parse_fortran_file",
    "parse_pyi_text",
    "pytest",
    "resolve_semantic_compile_time_values",
    "st",
)
