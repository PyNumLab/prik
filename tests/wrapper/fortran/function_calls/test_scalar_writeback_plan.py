"""Compiled canonical-plan coverage for scalar writeback."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from tests.wrapper.fortran._support import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_fortran_extension, build_pyi_extension


def test_scalar_copy_in_out_returns_replacement(tmp_path: Path):
    source = tmp_path / "scalar_writeback.f90"
    source.write_text(
        """
module scalar_writeback
contains
  subroutine bump(value)
    integer(4), intent(inout) :: value
    value = value + 1
  end subroutine bump
end module scalar_writeback
""",
        encoding="utf-8",
    )
    contract = tmp_path / "scalar_writeback.pyi"
    contract.write_text(
        """
from x2py.contracts import Annotated, Immutable, Int32, Returns

def bump(
    value: Annotated[Int32, Immutable]
) -> Returns["value", Int32]: ...
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native")

    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert tuple(path.name for path in result.generated_sources) == (
        "bind_c_scalar_writeback_wrapper.f90",
        "scalar_writeback_wrapper.c",
        "scalar_writeback_wrapper.h",
    )
    plan_bridge = (result.output_dir / "bind_c_scalar_writeback_wrapper.f90").read_text(encoding="utf-8")
    plan_c = (result.output_dir / "scalar_writeback_wrapper.c").read_text(encoding="utf-8")
    assert 'subroutine bind_c_bump(value) bind(c, name="bind_c_bump")' in plan_bridge
    assert "void bind_c_bump(int32_t * value);" in plan_c
    original = np.int32(4)
    replacement = module.bump(original)
    assert original == np.int32(4)
    assert replacement == np.int32(5)
    with pytest.raises(TypeError):
        module.bump("bad")


def test_source_generated_scalar_inout_contract_returns_replacement_and_keeps_namespace(tmp_path: Path):
    source = tmp_path / "outputs.f90"
    source.write_text(
        """
module outputs
  implicit none
contains
  subroutine scale_in_place(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
    value = factor * value
  end subroutine scale_in_place
end module outputs
""",
        encoding="utf-8",
    )

    source_result = build_fortran_extension(source, output_dir=tmp_path / "source_build")
    source_module = _import_from_build_dir(source_result.module_name, source_result.output_dir)
    assert not hasattr(source_module, "scale_in_place")
    assert source_module.outputs.scale_in_place(np.float64(4.0), np.float64(2.5)) == np.float64(10.0)

    contract_package = tmp_path / "contracts" / "outputs"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(contract_package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    entry = contract_package / "__init__.pyi"
    leaf = contract_package / "outputs.pyi"
    assert entry.read_text(encoding="utf-8") == "from . import outputs\n"
    leaf_text = leaf.read_text(encoding="utf-8")
    assert (
        'def scale_in_place(\n    value: Float64,\n    factor: Float64\n) -> Returns["value", Float64]: ...'
        in leaf_text
    )

    native_object = _compile_native_object(source, tmp_path / "native")
    package_result = build_pyi_extension(
        entry,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "package_build",
    )
    sys.modules.pop("outputs.outputs", None)
    package_module = _import_from_build_dir(package_result.module_name, package_result.output_dir)

    assert package_result.module_name == "outputs"
    assert not hasattr(package_module, "scale_in_place")
    assert package_module.outputs.scale_in_place(np.float64(5.0), np.float64(3.0)) == np.float64(15.0)

    leaf_result = build_pyi_extension(
        leaf,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_name="leaf_outputs",
        output_dir=tmp_path / "leaf_build",
    )
    leaf_module = _import_from_build_dir(leaf_result.module_name, leaf_result.output_dir)

    assert leaf_module.scale_in_place(np.float64(6.0), np.float64(4.0)) == np.float64(24.0)
    assert not hasattr(leaf_module, "outputs")

    entry.write_text("from .outputs import *\n", encoding="utf-8")
    flat_result = build_pyi_extension(
        entry,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_name="flat_outputs",
        output_dir=tmp_path / "flat_build",
    )
    flat_module = _import_from_build_dir(flat_result.module_name, flat_result.output_dir)

    assert flat_module.scale_in_place(np.float64(7.0), np.float64(5.0)) == np.float64(35.0)
    assert not hasattr(flat_module, "outputs")
