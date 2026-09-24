"""Logical scalar dummies share the storage width their logical arrays use."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import

SOURCE = Path(__file__).parent / "fixtures" / "native" / "flogical_storage_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end


def test_logical_reference_dummies_borrow_native_width_storage(pyi_parity_build_mode: str, tmp_path: Path):
    """A wider logical crosses as integer storage of its own width, with no copy."""
    module = _build_source_or_generated_pyi_and_import(
        SOURCE,
        tmp_path,
        {
            "bind_c_flogical_storage_f90_wrapper.f90",
            "flogical_storage_f90_wrapper.c",
            "flogical_storage_f90_wrapper.h",
        },
        None,
        pyi_parity_build_mode,
    )

    # A Python bool uses call-local storage and returns the native update.
    assert module.flip(True) is False
    assert module.flip(np.bool_(False)) is True

    # Rank-zero storage of the logical's own width is updated in place.
    flag = np.array(0, dtype=np.int32)
    assert module.flip(flag) is True
    assert flag[()] == 1
    wide = np.array(1, dtype=np.int64)
    assert module.flip_wide(wide) is False
    assert wide[()] == 0
    with pytest.raises(TypeError, match="int32"):
        module.flip(np.array(True))

    # A c_bool logical borrows bool storage.
    c_flag = np.array(True)
    assert module.flip_c_bool(c_flag) is False
    assert not c_flag[()]

    # An omitted optional lends no storage, so nothing is returned.
    assert module.maybe_flip() is None
    assert module.maybe_flip(False) is True
    optional_flag = np.array(1, dtype=np.int32)
    assert module.maybe_flip(optional_flag) is False
    assert optional_flag[()] == 0

    assert module.count_value(True) == np.int32(1)
    assert module.count_value(np.array(1, dtype=np.int32)) == np.int32(1)
