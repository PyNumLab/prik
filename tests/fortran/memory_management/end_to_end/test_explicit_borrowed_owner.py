"""Runtime evidence for explicit editable ownership and destruction triples."""

import gc
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension
from tests.fortran._support.paths import FORTRAN_ROOT

FINALIZER_SOURCE = FORTRAN_ROOT / "derived_types" / "end_to_end" / "fixtures" / "fborrowed_finalizer_f90.f90"
FINALIZER_CONTRACT = Path(__file__).parent / "fixtures" / "edited_contracts" / "borrowed_owner" / "__init__.pyi"
pytestmark = pytest.mark.fortran_end_to_end


def test_wrapper_owned_borrow_keeps_owner_alive_and_finalizes_exactly_once(tmp_path: Path):
    native_object = _compile_native_object(FINALIZER_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        FINALIZER_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    module.reset_final_count()
    owner = module.parent()
    borrowed = owner.value

    del owner
    gc.collect()
    assert module.get_final_count() == np.int32(0)

    del borrowed
    gc.collect()
    gc.collect()
    assert module.get_final_count() == np.int32(1)
