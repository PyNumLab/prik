"""Scalar allocatable values across source and generated-contract builds."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = FIXTURES / "fscalar_allocatables_f90.f90"
CONTRACT = FIXTURES / "contracts" / "fscalar_allocatables_f90"
pytestmark = pytest.mark.fortran_end_to_end


def test_scalar_allocatables_project_values_and_unallocated_state(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        SOURCE,
        tmp_path,
        {
            "bind_c_fscalar_allocatables_f90_wrapper.f90",
            "fscalar_allocatables_f90_wrapper.c",
            "fscalar_allocatables_f90_wrapper.h",
        },
        CONTRACT,
        pyi_parity_build_mode,
    )

    module.clear_module_value()
    assert module.optional_scale is None
    assert not hasattr(module, "get_optional_scale")
    assert not hasattr(module, "set_optional_scale")
    with pytest.raises(AttributeError):
        module.optional_scale = np.float64(9.0)

    module.set_module_value(np.float64(1.5))
    snapshot = module.optional_scale
    assert snapshot == np.float64(1.5)
    module.bump_module_value()
    assert snapshot == np.float64(1.5)
    assert module.optional_scale == np.float64(11.5)

    assert module.echo_allocatable(np.float64(3.0)) == np.float64(4.0)
    assert module.echo_allocatable(None) == np.float64(-1.0)
    assert module.update_allocatable(np.float64(3.0)) == np.float64(13.0)
    assert module.update_allocatable(None) == np.float64(10.0)
    assert module.clear_allocatable_value(np.float64(3.0)) is None
    assert module.create_allocatable() == np.float64(30.0)
    assert module.maybe_allocatable(np.int32(1)) == np.float64(3.5)
    assert module.maybe_allocatable(np.int32(0)) is None

    module.clear_module_value()
    assert module.optional_scale is None
