"""Built-extension behavior of the assumed scalar-intent build option."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "native" / "assumed_scalar_intent.f90"
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
    """Primitive and character scalars without intent share one conservative default."""
    module = _module(tmp_path, assume_intent_in_scalars=False)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    assert module.weighted(np.int32(3), values, np.float64(2.0)) == (
        np.float64(12.0),
        np.int32(3),
        np.float64(2.0),
    )
    assert module.label_width("abcd") == (np.int32(4), "abcd")


def test_assumed_scalar_intent_drops_only_undeclared_scalar_results(tmp_path: Path):
    """The option reaches undeclared scalars, primitive and character alike.

    A declared intent keeps its replacement result, and arrays and derived
    objects keep writing back in place.
    """
    module = _module(tmp_path, assume_intent_in_scalars=True)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    assert module.weighted(np.int32(3), values, np.float64(2.0)) == np.float64(12.0)
    assert module.label_width("abcd") == np.int32(4)
    assert module.declared(np.float64(4.0)) == np.float64(5.0)

    item = module.Sample(x=np.float64(1.0))
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.touch(np.int32(5), item, values) is None
    assert item.x == np.float64(2.0)
    np.testing.assert_array_equal(values, np.array([2.0, 4.0, 6.0]))
