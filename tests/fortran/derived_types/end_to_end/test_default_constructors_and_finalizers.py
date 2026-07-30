"""Default/keyword construction and owned-instance finalization evidence."""

import gc
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
CONSTRUCTOR_F90_SOURCE = FIXTURES / "fconstructors_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_fortran_default_constructor_keywords_and_finalization(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        CONSTRUCTOR_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fconstructors_f90_wrapper.f90",
            "fconstructors_f90_wrapper.c",
            "fconstructors_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fconstructors_f90",
        pyi_parity_build_mode,
    )

    module.reset_final_count()

    defaulted = module.initialized()
    assert defaulted.id == np.int32(7)
    assert defaulted.scale == np.float64(2.5)

    partial = module.initialized(id=np.int32(11))
    assert partial.id == np.int32(11)
    assert partial.scale == np.float64(2.5)

    keyword = module.initialized(id=np.int32(4), scale=np.float64(6.5))
    assert keyword.id == np.int32(4)
    assert keyword.scale == np.float64(6.5)

    del defaulted
    gc.collect()
    gc.collect()
    assert module.get_final_count() == np.int32(1)

    del partial
    del keyword
    gc.collect()
    gc.collect()
    assert module.get_final_count() == np.int32(3)

    with pytest.raises(TypeError):
        module.initialized(np.int32(1))
    gc.collect()
    assert module.get_final_count() == np.int32(4)

    with pytest.raises(TypeError):
        module.initialized(missing=np.int32(1))
    gc.collect()
    assert module.get_final_count() == np.int32(5)

    gc.collect()
    gc.collect()
    assert module.get_final_count() == np.int32(5)
