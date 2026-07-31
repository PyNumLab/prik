"""Unified naming-policy tests."""

import pytest

from x2py.naming import NamingPolicy
from x2py.naming import normalize_public_name


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
        == "module_x2py"
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
        == "main_x2py"
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
            {"MODULE_X2PY"},
            language="fortran",
            prefix="owner__",
            context="function",
            parent_context="module",
        )
        == "module_x2py_2"
    )
