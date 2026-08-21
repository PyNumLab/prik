"""Built-extension behavior of the assumed scalar-intent build option."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "assumed_scalar_intent.f90"
GENERATED = {
    "bind_c_assumed_scalar_intent_wrapper.f90",
    "assumed_scalar_intent_wrapper.c",
    "assumed_scalar_intent_wrapper.h",
}


def _module(workdir: Path, *, assume_intent_in_scalars: bool):
    return _build_source_and_import(
        SOURCE,
        workdir,
        GENERATED,
        assume_intent_in_scalars=assume_intent_in_scalars,
    )


def test_conservative_default_returns_every_undeclared_scalar(tmp_path: Path):
    module = _module(tmp_path, assume_intent_in_scalars=False)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    assert module.weighted(np.int32(3), values, np.float64(2.0)) == (
        np.float64(12.0),
        np.int32(3),
        np.float64(2.0),
    )


def test_assumed_scalar_intent_returns_only_the_function_result(tmp_path: Path):
    module = _module(tmp_path, assume_intent_in_scalars=True)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    assert module.weighted(np.int32(3), values, np.float64(2.0)) == np.float64(12.0)


def test_assumed_scalar_intent_keeps_array_and_derived_writeback(tmp_path: Path):
    module = _module(tmp_path, assume_intent_in_scalars=True)
    item = module.sample(x=np.float64(1.0))
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    assert module.touch(np.int32(5), item, values) is None
    assert item.x == np.float64(2.0)
    np.testing.assert_array_equal(values, np.array([2.0, 4.0, 6.0]))


def test_undeclared_character_scalar_follows_the_same_conservative_default(tmp_path: Path):
    """A character dummy with no intent is returned exactly like a primitive one."""
    module = _module(tmp_path, assume_intent_in_scalars=False)

    assert module.label_width("abcd") == (np.int32(4), "abcd")


def test_assumed_scalar_intent_also_drops_the_character_result(tmp_path: Path):
    module = _module(tmp_path, assume_intent_in_scalars=True)

    assert module.label_width("abcd") == np.int32(4)


def test_assumed_scalar_intent_does_not_change_a_declared_intent(tmp_path: Path):
    module = _module(tmp_path, assume_intent_in_scalars=True)

    assert module.declared(np.float64(4.0)) == np.float64(5.0)
