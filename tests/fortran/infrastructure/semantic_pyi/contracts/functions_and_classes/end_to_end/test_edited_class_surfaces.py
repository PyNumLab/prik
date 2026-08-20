"""Runtime behavior of edited method, constructor, and overload surfaces."""

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

FEATURE_ROOT = Path(__file__).parent / "fixtures" / "edited_contracts"
DERIVED_FIXTURES = FORTRAN_ROOT / "derived_types" / "end_to_end" / "fixtures"
GENERIC_FIXTURES = FORTRAN_ROOT / "generic_interfaces" / "end_to_end" / "fixtures"
CLASS_SOURCE = DERIVED_FIXTURES / "fclasses_f90.f90"
OVERLOAD_SOURCE = GENERIC_FIXTURES / "foverloads_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end


def _build(case: str, native_object: Path, output_dir: Path):
    result = build_pyi_extension(
        FEATURE_ROOT / case / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


@pytest.fixture(scope="module")
def overload_native_object(tmp_path_factory):
    return _compile_native_object(OVERLOAD_SOURCE, tmp_path_factory.mktemp("editable_overloads") / "native")


def test_module_procedure_is_reused_by_bound_constructor_method_and_public_function(tmp_path: Path):
    native_object = _compile_native_object(CLASS_SOURCE, tmp_path / "native")
    module = _build("method_and_constructor", native_object, tmp_path / "build")

    value = module.vector(np.float64(2.0), np.float64(3.0))
    assert (value.x, value.y) == (np.float64(2.0), np.float64(3.0))

    value.shift(np.float64(1.0), np.float64(-1.0))
    assert (value.x, value.y) == (np.float64(3.0), np.float64(2.0))

    module.shift_vector(np.float64(2.0), value, np.float64(4.0))
    assert (value.x, value.y) == (np.float64(5.0), np.float64(6.0))
    assert "shift(dx, dy) -> None" in module.vector.shift.__doc__


def test_module_method_and_constructor_overloads_share_one_edited_contract(
    overload_native_object: Path,
    tmp_path: Path,
):
    module = _build("overloaded_api", overload_native_object, tmp_path / "build")

    assert module.convert_int(np.int32(5)) == np.int32(15)
    assert module.convert_number(np.int32(6)) == np.int32(16)
    assert module.convert_number(np.float64(6.0)) == np.float64(6.5)
    with pytest.raises(TypeError):
        module.convert_number(np.complex128(1.0 + 0.0j))

    value = module.accumulator(np.int32(0))
    value.add(np.int32(2))
    value.add(np.float64(0.5))
    assert value.total == np.float64(2.5)
    with pytest.raises(TypeError, match="no matching overload for add"):
        value.add(np.complex128(1.0 + 0.0j))

    integer = module.accumulator(np.int32(3))
    real = module.accumulator(np.float64(1.25))
    assert integer.total == np.float64(3.0)
    assert real.total == np.float64(1.25)
    with pytest.raises(TypeError, match="no matching overload for __init__"):
        module.accumulator("wrong")


def test_editable_contract_removes_class_method_constructor_member_and_overload(
    overload_native_object: Path,
    tmp_path: Path,
):
    pruned = _build("pruned_surface", overload_native_object, tmp_path / "pruned")

    assert not hasattr(pruned, "sample")
    accumulator = pruned.accumulator()
    assert accumulator.total == np.float64(0.0)
    assert not hasattr(accumulator, "add")
    assert pruned.convert(np.int32(4)) == np.int32(14)
    assert pruned.convert(np.float64(4.0)) == np.float64(4.5)
    with pytest.raises(TypeError):
        pruned.convert(np.complex128(2.0 + 3.0j))

    without_constructor = _build(
        "without_constructor_member",
        overload_native_object,
        tmp_path / "without_constructor",
    )
    assert hasattr(without_constructor, "sample")
    assert not hasattr(without_constructor.sample, "value")
    with pytest.raises(TypeError):
        without_constructor.sample()


@pytest.mark.parametrize(
    ("case", "missing_targets"),
    [
        ("private_module_specifics_without_bind", ("convert_integer",)),
        (
            "private_type_bound_specifics_without_bind",
            ("accumulator_add_integer", "accumulator_add_real"),
        ),
    ],
)
def test_private_native_specific_without_overload_bind_fails_at_build(
    case: str,
    missing_targets: tuple[str, ...],
    overload_native_object: Path,
    tmp_path: Path,
):
    with pytest.raises(RuntimeError) as exc_info:
        _build(case, overload_native_object, tmp_path / case)

    error = str(exc_info.value).casefold()
    for target in missing_targets:
        assert target in error
    assert "not found in module" in error
