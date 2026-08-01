"""End-to-end projection rules from the Wrapping Subroutines guide."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import
from prik.runtime.handles import AllocatableArray

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "documented_subroutines.f90"


def test_subroutine_outputs_and_caller_storage_follow_documented_projection_rules(
    tmp_path: Path,
):
    module = _build_source_and_import(
        SOURCE,
        tmp_path,
        {
            "bind_c_documented_subroutines_wrapper.f90",
            "documented_subroutines_wrapper.c",
            "documented_subroutines_wrapper.h",
        },
    )

    data = np.array([4.0, -2.0, 7.0], dtype=np.float64)
    assert module.bounds(data) == (np.float64(-2.0), np.float64(7.0))

    scalar = np.float64(4.0)
    assert module.scale_scalar(scalar, np.float64(2.5)) == np.float64(10.0)
    assert scalar == np.float64(4.0)

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.scale_in_place(values, np.float64(3.0)) is None
    np.testing.assert_array_equal(values, np.array([3.0, 6.0, 9.0]))

    target = np.empty(4, dtype=np.float64)
    assert module.fill(target) is None
    np.testing.assert_array_equal(target, np.ones(4))

    no_intent = np.float64(5.0)
    assert module.no_intent_scalar(no_intent) == np.float64(6.0)
    assert no_intent == np.float64(5.0)

    point = module.point()
    assert module.fill_point(point) is None
    assert point.x == np.float64(9.5)

    made = module.make_values(np.int32(3))
    assert isinstance(made, AllocatableArray)
    np.testing.assert_array_equal(made.to_numpy(), np.array([1.0, 2.0, 3.0]))
    made.close()

    with pytest.raises(TypeError):
        module.bounds(np.array([1.0], dtype=np.float32))
    read_only = np.ones(2, dtype=np.float64)
    read_only.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.fill(read_only)
