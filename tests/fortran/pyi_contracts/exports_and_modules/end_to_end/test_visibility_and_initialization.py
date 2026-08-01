"""Editable contracts that remove or hide public declarations."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension

MODULE_FIXTURES = Path(__file__).parents[3] / "modules" / "end_to_end" / "fixtures"
FEATURE_FIXTURES = Path(__file__).parent / "fixtures"
MODULE_VARIABLE_SOURCE = MODULE_FIXTURES / "fmodule_vars_f90.f90"
MODIFIED_CONTRACT = FEATURE_FIXTURES / "edited_contracts" / "module_variables_visibility" / "__init__.pyi"
pytestmark = pytest.mark.fortran_end_to_end


def test_editable_contract_removes_hides_and_initializes_module_declarations(tmp_path: Path):
    contract_text = MODIFIED_CONTRACT.parent.joinpath("fmodule_vars_f90.pyi").read_text(encoding="utf-8")
    assert "def next_local" not in contract_text
    assert "counter: Int32 = 9" in contract_text
    assert "scale: private[Float64]" in contract_text
    assert "@private\ndef scaled_counter" in contract_text

    native_object = _compile_native_object(MODULE_VARIABLE_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        MODIFIED_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert module.nmax == np.int32(12)
    assert module.counter == np.int32(9)
    assert module.summarize() == np.int32(21)
    assert not hasattr(module, "set_nmax")

    assert not hasattr(module, "scale")
    assert not hasattr(module, "scaled_counter")
    assert not hasattr(module, "next_local")
