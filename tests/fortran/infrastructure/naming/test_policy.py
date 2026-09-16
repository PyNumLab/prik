"""Unified naming-policy tests."""

import pytest

from prik.naming import NamingPolicy
from prik.naming import normalize_public_name, preserves_source_case


def test_only_a_case_insensitive_language_gives_up_its_own_spelling():
    """Case is a name's identity everywhere a source distinguishes two spellings."""
    assert preserves_source_case("c") is True
    assert preserves_source_case("pyi") is True
    assert preserves_source_case(None) is True
    assert preserves_source_case("fortran") is False
    assert preserves_source_case("FORTRAN") is False


def test_a_folded_name_loses_a_spelling_a_preserved_one_keeps():
    """Folding is right only where the source never meant the two to differ."""
    assert normalize_public_name("BarBaz").name == "barbaz"
    assert normalize_public_name("BarBaz", preserve_case=True).name == "BarBaz"
    # Python still cannot bind a keyword, whichever rule names the declaration.
    assert normalize_public_name("lambda", preserve_case=True).name == "lambda_"
    # Casing alone is not a rename, so strict naming has nothing to reject.
    assert normalize_public_name("BarBaz", preserve_case=True).needs_fix is False


def test_two_spellings_collide_only_where_the_source_folds_them():
    """A case-sensitive source names two declarations; folding invents a collision."""
    folding = NamingPolicy()
    assert folding.reserve_public_name((), "Foo", category="function") == "foo"
    assert folding.reserve_public_name((), "foo", category="function") == "foo_2"

    preserving = NamingPolicy(preserve_case=True)
    assert preserving.reserve_public_name((), "Foo", category="function") == "Foo"
    assert preserving.reserve_public_name((), "foo", category="function") == "foo"


def test_a_wrapped_type_is_named_as_a_python_class():
    """A derived type reaches Python as a class, so PRIK spells it like one."""
    assert normalize_public_name("point_t", category="class").name == "Point_T"
    assert normalize_public_name("my_particle_type", category="class").name == "My_Particle_Type"
    assert normalize_public_name("accumulator", category="class").name == "Accumulator"
    # Fortran writes one type under many spellings, so the style does not
    # depend on which one the source happened to use.
    assert normalize_public_name("POINT_T", category="class").name == "Point_T"
    # Every other declaration keeps the lower-case form.
    assert normalize_public_name("point_t").name == "point_t"


def test_a_source_that_spells_its_own_types_keeps_that_spelling():
    """C names each declaration exactly, so PRIK has no spelling to choose."""
    assert normalize_public_name("point", preserve_case=True, category="class").name == "point"
    assert normalize_public_name("Point", preserve_case=True, category="class").name == "Point"


def test_a_chosen_class_style_is_not_a_name_python_forced():
    """Strict naming rejects what Python cannot spell, not how PRIK cases it."""
    assert normalize_public_name("point_t", category="class").needs_fix is False
    assert normalize_public_name("point t", category="class").needs_fix is True


def test_public_python_names_escape_keywords_and_collisions():
    policy = NamingPolicy()

    assert normalize_public_name("def").name == "def_"
    assert policy.reserve_public_name(("mod",), "def", category="function") == "def_"
    assert policy.reserve_public_name(("mod",), "def_", category="function") == "def__2"


def test_python_keyword_is_renamed_only_at_the_python_boundary():
    policy = NamingPolicy()

    assert policy.reserve_public_name(("mod",), "lambda", category="variable") == "lambda_"
    assert (
        policy.generated_symbol(
            "lambda",
            set(),
            language="fortran",
            prefix="mod__",
            context="variable",
            parent_context="function",
        )
        == "lambda"
    )


def test_strict_public_names_reject_keyword_escaping():
    policy = NamingPolicy(strict_public_names=True)

    with pytest.raises(ValueError, match="strict wrapper naming"):
        policy.reserve_public_name(("mod",), "def", category="function")


def test_generated_symbols_apply_target_language_rules():
    policy = NamingPolicy()

    assert (
        policy.generated_symbol(
            "module",
            set(),
            language="fortran",
            prefix="owner__",
            context="function",
            parent_context="module",
        )
        == "module_prik"
    )
    assert (
        policy.generated_symbol(
            "return",
            set(),
            language="c",
            prefix="owner__",
            context="function",
            parent_context="module",
        )
        == "owner__return"
    )
    assert (
        policy.generated_symbol(
            "answer",
            {"Answer"},
            language="fortran",
            prefix="owner__",
            context="variable",
            parent_context="function",
        )
        == "answer_2"
    )


def test_generated_symbols_reserve_c_entry_point_and_rewrite_special_methods():
    policy = NamingPolicy()

    assert (
        policy.generated_symbol(
            "main",
            set(),
            language="c",
            prefix="owner__",
            context="module",
            parent_context="module",
        )
        == "main_prik"
    )
    assert (
        policy.generated_symbol(
            "__init__",
            set(),
            language="fortran",
            prefix="owner__",
            context="function",
            parent_context="module",
        )
        == "owner__init"
    )


def test_generated_symbols_number_after_an_escaped_native_name():
    policy = NamingPolicy()

    assert (
        policy.generated_symbol(
            "module",
            {"MODULE_PRIK"},
            language="fortran",
            prefix="owner__",
            context="function",
            parent_context="module",
        )
        == "module_prik_2"
    )
