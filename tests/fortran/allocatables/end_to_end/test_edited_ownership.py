"""Edited `.pyi` ownership policy for allocatable handle origins."""

import gc
from pathlib import Path
import weakref

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension

FIXTURES = Path(__file__).parent / "fixtures"
NATIVE_SOURCE = FIXTURES / "native" / "fallocatable_views_f90.f90"
OWNERSHIP_CONTRACT = FIXTURES / "edited_contracts" / "explicit_ownership" / "__init__.pyi"
pytestmark = pytest.mark.fortran_end_to_end


def test_explicit_handle_ownership_uses_native_wrapper_and_result_lifetimes(tmp_path: Path):
    native_object = _compile_native_object(NATIVE_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        OWNERSHIP_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    module.allocate_module_values(np.int32(3))
    native_handle = module.module_values
    native_view = native_handle.to_numpy()
    np.testing.assert_allclose(native_view, np.array([1.0, 2.0, 3.0], dtype=np.float64))
    del native_view
    gc.collect()
    assert module.module_values_sum() == np.float64(6.0)
    module.deallocate_module_values()
    assert native_handle.allocated is False

    owner = module.buffer()
    owner.allocate_values(np.int32(3))
    wrapper_handle = owner.values
    wrapper_view = wrapper_handle.to_numpy()
    assert wrapper_handle.owner is owner
    del owner
    gc.collect()
    np.testing.assert_allclose(wrapper_view, np.array([1.0, 2.0, 3.0], dtype=np.float64))
    retained_owner = wrapper_handle.owner
    retained_owner.deallocate_values()
    assert wrapper_handle.allocated is False

    result_handle = module.build_values(np.int32(4))
    np.testing.assert_allclose(result_handle.to_numpy(), np.array([2.0, 4.0, 6.0, 8.0], dtype=np.float64))
    released: list[bool] = []
    weakref.finalize(result_handle, released.append, True)
    del result_handle
    gc.collect()
    assert released == [True]
