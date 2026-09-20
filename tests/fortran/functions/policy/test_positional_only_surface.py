"""A positional-only surface drops keyword names policy does not owe the caller."""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file
from prik.policy import complete_semantic_policies
from prik.policy.construction import completed_function_wrapper_policy
from prik.semantics.fortran2ir import fortran_module_to_semantic_module

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


_SOURCE = (NATIVE_FIXTURES / "positional_only_surface.f90").read_text(encoding="utf-8")


def _policies(source: str, **options):
    module = fortran_module_to_semantic_module(parse_fortran_file(source).modules[0])
    complete_semantic_policies(module, **options)
    return {function.name: completed_function_wrapper_policy(function) for function in module.functions}


def test_an_all_required_function_becomes_positional_and_is_renamed_by_position():
    policy = _policies(_SOURCE, positional_only=True)["required_only"]

    assert policy.accepts_keyword_arguments is False
    assert [argument.python_name for argument in policy.arguments] == ["arg0", "arg1"]
    # The native declaration keeps its own names; only the Python surface changes.
    assert [argument.name for argument in policy.arguments] == ["alpha", "beta"]


def test_an_optional_argument_keeps_keywords_because_skipping_one_requires_naming_the_rest():
    policy = _policies(_SOURCE, positional_only=True)["has_optional"]

    assert policy.accepts_keyword_arguments is True
    assert [argument.python_name for argument in policy.arguments] == ["value", "scale"]


def test_the_default_surface_is_unchanged():
    policies = _policies(_SOURCE)

    assert policies["required_only"].accepts_keyword_arguments is True
    assert [argument.python_name for argument in policies["required_only"].arguments] == ["alpha", "beta"]


def test_an_overload_set_cannot_become_positional_only_because_it_dispatches_on_keywords():
    source = """
module dispatch
  implicit none
  interface scale_it
    module procedure scale_real, scale_int
  end interface scale_it
contains
  function scale_real(value) result(total)
    real(8), intent(in) :: value
    real(8) :: total
    total = 2.0d0 * value
  end function scale_real
  function scale_int(value) result(total)
    integer, intent(in) :: value
    integer :: total
    total = 2 * value
  end function scale_int
end module dispatch
"""

    with pytest.raises(ValueError, match="positional-only surface does not support overload sets"):
        _policies(source, positional_only=True)
