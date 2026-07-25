"""Runtime evidence for removing, adding, and renaming editable API members."""

from pathlib import Path

import numpy as np
import pytest

from tests.wrapper.fortran._support import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
    wrapper_source,
)
from x2py import build_pyi_extension

NATIVE_SOURCE = wrapper_source("foverloads_f90.f90")
CONTRACT_ROOT = Path(__file__).parent / "modified_contracts"


def _build_contract(case: str, native_object: Path, output_dir: Path):
    result = build_pyi_extension(
        CONTRACT_ROOT / case / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def test_editable_contract_removes_class_method_constructor_member_and_overload(tmp_path: Path):
    native_object = _compile_native_object(NATIVE_SOURCE, tmp_path / "native")
    pruned = _build_contract("foverloads_pruned_surface", native_object, tmp_path / "pruned")

    assert not hasattr(pruned, "sample")
    accumulator = pruned.accumulator()
    assert accumulator.total == np.float64(0.0)
    assert not hasattr(accumulator, "add")
    assert pruned.convert(np.int32(4)) == np.int32(14)
    assert pruned.convert(np.float64(4.0)) == np.float64(4.5)
    with pytest.raises(TypeError):
        pruned.convert(np.complex128(2.0 + 3.0j))

    without_constructor = _build_contract(
        "foverloads_without_constructor_member",
        native_object,
        tmp_path / "without_constructor",
    )
    assert hasattr(without_constructor, "sample")
    assert not hasattr(without_constructor.sample, "value")
    with pytest.raises(TypeError):
        without_constructor.sample()


def test_editable_contract_adds_renamed_binding_and_overload_group(tmp_path: Path):
    native_object = _compile_native_object(NATIVE_SOURCE, tmp_path / "native")
    module = _build_contract("foverloads_added_bindings", native_object, tmp_path / "added")

    assert module.convert_int(np.int32(5)) == np.int32(15)
    assert module.convert_number(np.int32(6)) == np.int32(16)
    assert module.convert_number(np.float64(6.0)) == np.float64(6.5)
    with pytest.raises(TypeError):
        module.convert_number(np.complex128(1.0 + 0.0j))


def test_private_native_specific_without_overload_bind_fails_fortran_accessibility(tmp_path: Path):
    native_object = _compile_native_object(NATIVE_SOURCE, tmp_path / "native")

    with pytest.raises(RuntimeError) as exc_info:
        _build_contract(
            "foverloads_private_specific_without_bind",
            native_object,
            tmp_path / "inaccessible",
        )

    error = str(exc_info.value).casefold()
    assert "convert_integer" in error
    assert "not found in module" in error
