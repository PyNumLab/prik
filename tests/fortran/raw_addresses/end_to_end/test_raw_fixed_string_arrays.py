"""Fixed-width character-array raw address runtime boundary."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension

STRING_FIXTURES = Path(__file__).resolve().parents[2] / "strings" / "end_to_end" / "fixtures"
STRING_F90_SOURCE = STRING_FIXTURES / "fstrings_f90.f90"
RAW_CONTRACT = Path(__file__).parent / "fixtures" / "edited_contracts" / "raw_string_array" / "__init__.pyi"
pytestmark = pytest.mark.fortran_end_to_end


def _build_contract_module(contract: Path, native_object: Path, output_dir: Path, symbol: str):
    """Build one edited character contract through the canonical wrapper plan."""
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    return package if hasattr(package, symbol) else _sole_native_module(package)


def test_raw_fixed_width_character_arrays_use_canonical_plan(tmp_path: Path):
    """Replay one fixed-width character array through its raw address contract."""
    native_object = _compile_native_object(STRING_F90_SOURCE, tmp_path / "native")
    module = _build_contract_module(RAW_CONTRACT, native_object, tmp_path / "build", "fixed_array_extent_raw")

    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent_raw(labels.ctypes.data) == 16
    with pytest.raises(TypeError):
        module.fixed_array_extent_raw(labels)
