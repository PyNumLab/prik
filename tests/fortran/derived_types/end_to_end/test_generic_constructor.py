"""Generated Python constructor for each Fortran constructor source."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "generic_constructor.f90"
GENERATED = {
    "bind_c_generic_constructor_wrapper.f90",
    "generic_constructor_wrapper.c",
    "generic_constructor_wrapper.h",
}


@pytest.fixture(scope="module")
def module(tmp_path_factory):
    return _build_source_and_import(SOURCE, tmp_path_factory.mktemp("generic_constructor"), GENERATED)


def test_type_without_a_constructor_interface_keeps_keyword_fields(module):
    """No user constructor: the keyword-field `__init__` is unchanged."""
    value = module.plain(tag=np.int32(5))

    assert value.tag == np.int32(5)


def test_constructor_interface_overloads_init_from_its_specifics(module):
    """`interface <typename>`: each specific becomes an accepted signature."""
    empty = module.box()
    from_count = module.box(np.int32(7))
    from_value = module.box(np.float64(2.5))

    assert (empty.count, empty.value) == (np.int32(0), np.float64(0.0))
    assert (from_count.count, from_count.value) == (np.int32(7), np.float64(7.0))
    assert (from_value.count, from_value.value) == (np.int32(2), np.float64(2.5))


def test_constructor_overload_rejects_an_unmatched_signature(module):
    """A call matching no specific is refused rather than guessed at."""
    with pytest.raises(TypeError, match="no matching overload"):
        module.box("not a supported signature")


def test_constructed_instances_are_independent_wrapper_objects(module):
    """Each accepted signature produces its own wrapper-owned instance."""
    first = module.box(np.int32(1))
    second = module.box(np.int32(2))

    assert first is not second
    first.count = np.int32(9)
    assert second.count == np.int32(2)


def test_constructor_contract_states_no_redundant_link_name(tmp_path: Path):
    """A constructor's native generic is named for its type, so `@bind` is omitted.

    `@overload` names the specific this candidate selects; the class name already
    states the generic that reaches it, exactly as an unrenamed method omits
    `@bind`.
    """
    from prik.pipeline.pyi import emit_module_stubs
    from prik.parsers.fortran import parse_fortran_file
    from prik.semantics.fortran2ir import fortran_file_to_semantic_modules

    modules = fortran_file_to_semantic_modules(parse_fortran_file(str(SOURCE)))
    contract = emit_module_stubs(modules)["generic_constructor"]

    assert '@overload("box_from_count")' in contract
    assert '@bind("box")' not in contract
    assert "@private\n    def __init__" not in contract
