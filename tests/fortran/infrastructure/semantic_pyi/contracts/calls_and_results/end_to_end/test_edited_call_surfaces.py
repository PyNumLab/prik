"""Runtime behavior of edited native calls and result projections."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension

FIXTURES = Path(__file__).parent / "fixtures"
CONTRACTS = FIXTURES / "edited_contracts"
NATIVE = FIXTURES / "native"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture(scope="module")
def call_native_object(tmp_path_factory) -> Path:
    return _compile_native_object(
        NATIVE / "fnative_call_examples_f90.f90",
        tmp_path_factory.mktemp("editable_calls") / "native",
    )


@pytest.fixture(scope="module")
def output_native_object(tmp_path_factory) -> Path:
    return _compile_native_object(
        NATIVE / "foutputs_f90.f90",
        tmp_path_factory.mktemp("editable_outputs") / "native",
    )


@pytest.fixture(scope="module")
def character_literal_native_object(tmp_path_factory) -> Path:
    return _compile_native_object(
        NATIVE / "fcharacter_literal_f90.f90",
        tmp_path_factory.mktemp("character_literal") / "native",
    )


def _build(case: str, native_object: Path, output_dir: Path):
    result = build_pyi_extension(
        CONTRACTS / case / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def test_native_order_exposes_writable_slots_without_projection(
    call_native_object: Path,
    tmp_path: Path,
):
    contract_text = (CONTRACTS / "native_order" / "fnative_call_examples_f90.pyi").read_text(encoding="utf-8")
    assert "@native_call" not in contract_text
    module = _build("native_order", call_native_object, tmp_path / "build")

    base = np.array(4, dtype=np.int32)
    status = np.empty((), dtype=np.int32)
    assert module.scalar_status(base, status) is None
    assert status[()] == np.int32(15)
    with pytest.raises(TypeError, match=r"numpy.ndarray"):
        module.scalar_status(np.int32(4), status)

    vector_size = np.array(4, dtype=np.int32)
    vector = np.empty(4, dtype=np.float64)
    assert module.fill_vector(vector_size, vector) is None
    np.testing.assert_allclose(vector, np.array([1.5, 3.0, 4.5, 6.0], dtype=np.float64))

    rows = np.array(2, dtype=np.int32)
    cols = np.array(3, dtype=np.int32)
    matrix = np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]], dtype=np.float64, order="F")
    shifted = np.empty((2, 3), dtype=np.float64, order="F")
    assert module.shift_matrix(rows, cols, matrix, shifted) is None
    np.testing.assert_allclose(shifted, matrix + 10.0)

    values = np.array([2.0, 5.0, 7.0], dtype=np.float64)
    scale_status = np.empty((), dtype=np.int32)
    assert module.scale_with_status(values, scale_status) is None
    assert scale_status[()] == np.int32(3)
    np.testing.assert_allclose(values, np.array([4.0, 10.0, 14.0], dtype=np.float64))

    original_label = "abc     "
    assert module.fixed_inout(original_label) is None
    assert original_label == "abc     "
    assert module.make_label("      ") is None

    mixed_values = np.empty(3, dtype=np.float64)
    mixed_status = np.empty((), dtype=np.int32)
    assert module.summarize_mixed(np.array(3, dtype=np.int32), mixed_values, mixed_status, "      ") == np.float64(3.75)
    assert mixed_status[()] == np.int32(23)
    np.testing.assert_allclose(mixed_values, np.array([11.0, 12.0, 13.0], dtype=np.float64))

    point = module.summary_point()
    assert module.make_point(np.array(7, dtype=np.int32), point) is None
    assert (point.total, point.code) == (np.float64(7.5), np.int32(107))


def test_native_call_reorders_arguments_and_projects_mixed_results(
    call_native_object: Path,
    tmp_path: Path,
):
    module = _build("projected_results", call_native_object, tmp_path / "build")

    assert module.scalar_status(np.int32(4)) == np.int32(15)

    vector = np.empty(4, dtype=np.float64)
    assert module.fill_vector(np.int32(4), vector) is None
    np.testing.assert_allclose(vector, np.array([1.5, 3.0, 4.5, 6.0], dtype=np.float64))

    matrix = np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]], dtype=np.float64, order="F")
    shifted = np.empty((2, 3), dtype=np.float64, order="F")
    assert module.shift_matrix(np.int32(2), np.int32(3), matrix, shifted) is None
    np.testing.assert_allclose(shifted, matrix + 10.0)

    values = np.array([2.0, 5.0, 7.0], dtype=np.float64)
    assert module.scale_with_status(values) == np.int32(3)
    np.testing.assert_allclose(values, np.array([4.0, 10.0, 14.0], dtype=np.float64))

    assert module.fixed_inout("abc     ") == "Xbc    !"
    assert module.make_label() == "done  "

    mixed_values = np.empty(3, dtype=np.float64)
    total, status, label = module.summarize_mixed(np.int32(3), mixed_values)
    assert (total, status, label) == (np.float64(3.75), np.int32(23), "mix   ")
    np.testing.assert_allclose(mixed_values, np.array([11.0, 12.0, 13.0], dtype=np.float64))

    point = module.summary_point()
    assert module.make_point(np.int32(7), point) is None
    assert (point.total, point.code) == (np.float64(7.5), np.int32(107))


def test_immutable_values_return_replacements_without_mutating_inputs(
    call_native_object: Path,
    tmp_path: Path,
):
    module = _build("immutable_replacements", call_native_object, tmp_path / "build")

    assert module.scalar_status(np.int32(4)) == np.int32(15)

    original_label = "abc     "
    assert module.fixed_inout(original_label) == "Xbc    !"
    assert original_label == "abc     "

    original_values = np.array([2.0, 5.0, 7.0], dtype=np.float64)
    status = np.empty((), dtype=np.int32)
    replacement_values = module.scale_with_status(original_values, status)
    np.testing.assert_allclose(original_values, np.array([2.0, 5.0, 7.0], dtype=np.float64))
    np.testing.assert_allclose(replacement_values, np.array([4.0, 10.0, 14.0], dtype=np.float64))

    replacement_point = module.make_point(np.int32(7))
    assert (replacement_point.total, replacement_point.code) == (np.float64(7.5), np.int32(107))


def test_declared_character_literal_is_supplied_by_both_entrypoint_routes(
    character_literal_native_object: Path,
    tmp_path: Path,
):
    """``String[1]("N")`` declares the character the native parameter receives.

    The same completed decision reaches a bridged ``character(len=1)`` dummy and
    a direct ``bind(C)`` entrypoint, so neither route needs the character to be
    a visible Python argument.
    """
    result = build_pyi_extension(
        CONTRACTS / "character_literal" / "__init__.pyi",
        native_objects=[character_literal_native_object],
        native_include_dirs=[character_literal_native_object.parent],
        output_dir=tmp_path / "build",
    )
    bridge = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".f90")
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "character(kind=c_char, len=1), value :: literal_0" in bridge
    assert f"'\\{ord('L'):03o}'" in binding
    assert f"'\\{ord('R'):03o}'" in binding

    module = _import_from_build_dir(result.module_name, result.output_dir)
    left, right = np.float64(1.5), np.float64(9.5)
    bridged = module.fcharacter_literal_f90
    assert (bridged.take_left(left, right), bridged.take_right(left, right)) == (left, right)
    assert (module.pick_left(left, right), module.pick_right(left, right)) == (left, right)


def test_typed_extent_projection_reaches_a_default_fortran_integer_dummy(
    output_native_object: Path,
    tmp_path: Path,
):
    """``Int32(Arg(0).shape[0])`` materializes the extent as the dummy's own type.

    ``fill_vector`` declares ``integer, intent(in) :: n``.  Without the stated
    type the binding would produce a ``size_t`` for a four-byte dummy, so the
    generated bridge parameter is part of the contract, not an incidental
    spelling.
    """
    result = build_pyi_extension(
        CONTRACTS / "typed_extent" / "__init__.pyi",
        native_objects=[output_native_object],
        native_include_dirs=[output_native_object.parent],
        output_dir=tmp_path / "build",
    )
    bridge = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".f90")
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "integer(c_int32_t), value :: shape_0" in bridge
    assert "(int32_t)PyArray_DIM" in binding
    assert "(size_t)PyArray_DIM" not in binding

    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))
    values = np.empty(4, dtype=np.float64)
    assert module.fill_vector(values) is None
    np.testing.assert_allclose(values, np.array([2.0, 4.0, 6.0, 8.0]))
    empty = np.empty(0, dtype=np.float64)
    assert module.fill_vector(empty) is None


def test_hidden_fixed_shape_array_output_is_allocated_and_returned(
    output_native_object: Path,
    tmp_path: Path,
    monkeypatch,
):
    module = _build("hidden_array_output", output_native_object, tmp_path / "build")

    np.testing.assert_array_equal(module.fill_vector(np.int32(4)), np.array([2.0, 4.0, 6.0, 8.0]))
    assert module.fill_vector(np.int32(0)).shape == (0,)

    monkeypatch.setenv("PRIK_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError, match="Unable to allocate copy-return output array"):
        module.fill_vector(np.int32(2))
