"""Optional argument runtime wrapper tests."""

from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension
from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _compiler,
    _import_from_build_dir,
    _sole_native_module,
)
from prik.contracts import Allocatable, Float64, Pointer

FIXTURES = Path(__file__).parent / "fixtures"
OPTIONAL_F90_SOURCE = FIXTURES / "native" / "foptional_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_optional_scalar_descriptors_distinguish_omitted_none_and_value(tmp_path: Path):
    source = FIXTURES / "native" / "optional_scalar_descriptors.f90"
    native_object = _compile_native_object(source, tmp_path / "native")
    entry = FIXTURES / "edited_contracts" / "scalar_optional_descriptors" / "scalar_optional_descriptors.pyi"

    result = build_pyi_extension(
        entry,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert tuple(path.name for path in result.generated_sources) == (
        "bind_c_scalar_optional_descriptors_wrapper.f90",
        "scalar_optional_descriptors_wrapper.c",
        "scalar_optional_descriptors_wrapper.h",
    )
    for function_name in ("alloc_state", "pointer_state"):
        function = getattr(module, function_name)
        assert function() == np.int32(0)
        assert function(None) == np.int32(1)
        assert function(np.float64(2.5)) == np.int32(2)
        with pytest.raises(TypeError):
            function("bad")
    plan_c = (result.output_dir / "scalar_optional_descriptors_wrapper.c").read_text(encoding="utf-8")
    assert "int32_t bind_c_alloc_state(double * value, void * value_present);" in plan_c
    assert "Omit to make the native optional dummy absent." in module.alloc_state.__doc__
    assert "Pass None for a present unallocated or unassociated descriptor." in module.alloc_state.__doc__
    assert "Default is None." not in module.alloc_state.__doc__


def test_optional_array_descriptors_preserve_presence_and_storage_state(tmp_path: Path):
    """Distinguish omitted/None from present absent-state descriptor handles."""
    source = FIXTURES / "native" / "optional_array_descriptors.f90"
    native_object = _compile_native_object(source, tmp_path / "native_array_descriptors")
    contract = FIXTURES / "edited_contracts" / "optional_array_descriptors" / "optional_array_descriptors.pyi"

    result = build_pyi_extension(
        contract,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "array_descriptors",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    for function_name in ("alloc_state", "pointer_state"):
        function = getattr(module, function_name)
        assert function() == np.int32(0)
        assert function(None) == np.int32(0)

    # A handle that is present but empty must stay distinguishable from an
    # absent argument, and the descriptor the callee fills has to be the
    # handle's own for the third state to be reachable at all.
    for function_name, contract, fill_name in (
        ("alloc_state", Allocatable[Float64[:]], "alloc_fill"),
        ("pointer_state", Pointer[Float64[:]], "pointer_bind"),
    ):
        function = getattr(module, function_name)
        handle = contract()
        assert function(handle) == np.int32(1)
        getattr(module, fill_name)(handle)
        assert function(handle) == np.int32(6)


def test_optional_arguments_drive_fortran_present_behavior(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        OPTIONAL_F90_SOURCE,
        tmp_path,
        {
            "bind_c_foptional_f90_wrapper.f90",
            "foptional_f90_wrapper.c",
            "foptional_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "foptional_f90",
        pyi_parity_build_mode,
    )

    assert "scale : int32 or None" in module.summarize.__doc__
    assert "May be omitted or passed as None." in module.summarize.__doc__

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    item = module.sample()
    item.value = np.int32(7)

    assert module.summarize(np.int32(5)) == np.int32(5)
    assert module.summarize(np.int32(5), np.int32(4)) == np.int32(9)
    assert module.summarize(np.int32(5), None) == np.int32(5)
    assert module.summarize(np.int32(5), scale=None) == np.int32(5)
    assert module.summarize(np.int32(5), values=values) == np.int32(11)
    assert module.summarize(np.int32(5), label="trimmed") == np.int32(12)
    assert module.summarize(np.int32(5), item=item) == np.int32(12)
    assert module.summarize(np.int32(5), item=item, values=values, label="abc") == np.int32(21)
    assert module.summarize(np.int32(5), None, values=values, item=item) == np.int32(18)

    mutable = np.array([1.0, 2.0], dtype=np.float64)
    assert module.mutate_optional() is None
    assert module.mutate_optional(None, np.float64(100.0)) is None
    assert module.mutate_optional(mutable) is None
    np.testing.assert_allclose(mutable, np.array([2.0, 3.0], dtype=np.float64))
    assert module.mutate_optional(mutable, None) is None
    np.testing.assert_allclose(mutable, np.array([3.0, 4.0], dtype=np.float64))
    assert module.mutate_optional(mutable, np.float64(2.5)) is None
    np.testing.assert_allclose(mutable, np.array([5.5, 6.5], dtype=np.float64))

    output = np.empty(3, dtype=np.float64)
    assert module.fill_optional(np.int32(3), output) is None
    np.testing.assert_allclose(output, np.array([11.0, 12.0, 13.0], dtype=np.float64))
    assert module.fill_optional(np.int32(3)) is None
    assert module.fill_optional(np.int32(3), None) is None
    assert module.optional_status(np.int32(8)) == (np.int32(8), None)
    assert module.optional_status(np.int32(8), None) == (np.int32(8), None)
    status = np.empty((), dtype=np.int32)
    returned_base, returned_status = module.optional_status(np.int32(8), status)
    assert returned_base == np.int32(8)
    assert returned_status is status
    assert status[()] == np.int32(58)

    with pytest.raises(TypeError):
        module.summarize(np.int32(5), scale="bad")
    with pytest.raises(TypeError):
        module.fill_optional(np.int32(3), np.empty(3, dtype=np.float32))


def test_optional_array_buffers_preserve_omission_and_identity(tmp_path: Path):
    """Replay omitted, explicit-None, and present ordinary array storage."""
    native_object = _compile_native_object(OPTIONAL_F90_SOURCE, tmp_path / "native")
    contract_package = FIXTURES / "edited_contracts" / "optional_arrays"
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    imported = _import_from_build_dir(result.module_name, result.output_dir)
    module = imported if hasattr(imported, "mutate_optional") else _sole_native_module(imported)

    assert module.mutate_optional() is None
    assert module.mutate_optional(None, np.float64(2.0)) is None
    values = np.array([1.0, 2.0], dtype=np.float64)
    assert module.mutate_optional(values, np.float64(2.5)) is None
    np.testing.assert_array_equal(values, np.array([3.5, 4.5]))

    output = np.empty(3, dtype=np.float64)
    assert module.fill_optional(np.int32(3), output) is output
    np.testing.assert_array_equal(output, np.array([11.0, 12.0, 13.0]))
    assert module.fill_optional(np.int32(3)) is None
    assert module.fill_optional(np.int32(3), None) is None

    with pytest.raises(TypeError):
        module.fill_optional(np.int32(3), np.empty(3, dtype=np.float32))
