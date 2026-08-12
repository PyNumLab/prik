"""Semantic scalar catalogue invariants."""

import pytest

from prik.semantics.scalar_types import (
    BOOLEAN_SEMANTIC_TYPE_NAMES,
    SEMANTIC_SCALAR_TYPES,
    SEMANTIC_SCALAR_TYPE_NAMES,
    SemanticScalarFamily,
    boolean_storage_bits,
    is_boolean_semantic_type_name,
)


def test_scalar_catalogue_exposes_semantic_family_and_storage_without_numpy_facts():
    assert SEMANTIC_SCALAR_TYPES["Int32"].family is SemanticScalarFamily.SIGNED_INTEGER
    assert SEMANTIC_SCALAR_TYPES["Int32"].storage_bits == 32
    assert SEMANTIC_SCALAR_TYPES["Float64"].family is SemanticScalarFamily.REAL
    assert SEMANTIC_SCALAR_TYPES["Float64"].storage_bits == 64
    assert SEMANTIC_SCALAR_TYPES["String"].family is SemanticScalarFamily.CHARACTER
    assert SEMANTIC_SCALAR_TYPES["String"].storage_bits is None
    assert frozenset(SEMANTIC_SCALAR_TYPES) == SEMANTIC_SCALAR_TYPE_NAMES


def test_boolean_catalogue_preserves_native_widths_that_numpy_bool_cannot_distinguish():
    names = ("Bool", "Bool8", "Bool16", "Bool32", "Bool64")

    assert frozenset(names) == BOOLEAN_SEMANTIC_TYPE_NAMES
    assert all(is_boolean_semantic_type_name(name) for name in names)
    assert [boolean_storage_bits(name) for name in names] == [8, 8, 16, 32, 64]
    assert not is_boolean_semantic_type_name(None)
    assert not is_boolean_semantic_type_name("Int8")

    with pytest.raises(KeyError):
        boolean_storage_bits("Int8")


def test_target_dependent_semantic_names_do_not_invent_storage_widths():
    assert SEMANTIC_SCALAR_TYPES["Int"].storage_bits is None
    assert SEMANTIC_SCALAR_TYPES["UInt"].storage_bits is None
    assert SEMANTIC_SCALAR_TYPES["SizeT"].storage_bits is None
    assert SEMANTIC_SCALAR_TYPES["Float128"].storage_bits is None
    assert SEMANTIC_SCALAR_TYPES["Complex256"].storage_bits is None
