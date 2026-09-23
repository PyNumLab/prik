"""Compiled address and descriptor marshalling for one native actual."""

from pathlib import Path

import numpy as np
import pytest

from prik.pipeline.build import build_fortran_extension, build_pyi_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir


SOURCE = Path(__file__).parent / "fixtures" / "native" / "assumed_type_calls.f90"
MUTATION_SOURCE = Path(__file__).parent / "fixtures" / "native" / "assumed_type_mutation.f90"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture(scope="module", params=("source", "generated-pyi"))
def calls(request, tmp_path_factory):
    output = tmp_path_factory.mktemp(f"assumed-type-{request.param}")
    built = build_fortran_extension(SOURCE, output_name="assumed_type_api", output_dir=output)
    if request.param == "source":
        return _import_from_build_dir(built.module_name, built.output_dir).assumed_type_calls
    replay_dir = tmp_path_factory.mktemp("assumed-type-replay")
    replay = build_pyi_extension(
        output / "contracts" / "assumed_type_calls.pyi",
        native_objects=[output / "assumed_type_calls.o"],
        output_name="assumed_type_replay",
        output_dir=replay_dir,
    )
    return _import_from_build_dir(replay.module_name, replay.output_dir)


def test_same_actual_uses_address_or_descriptor_from_dummy(calls):
    values = np.arange(5, dtype=np.int64)
    assert calls.assumed_size(values) == 20
    assert calls.assumed_shape(values) == 5
    assert calls.assumed_rank(values) == 1
    assert calls.assumed_shape(values[::-1]) == 5
    assert calls.assumed_shape_three(np.ones((2, 3, 4), dtype=np.float64, order="F")) == 9
    assert calls.assumed_rank(values[::-1]) == 1
    assert calls.assumed_rank(np.array([[1.0, 2.0]], dtype=np.float64, order="F")) == 2
    assert calls.assumed_rank(np.array(3, dtype=np.int64)) == 0
    assert calls.assumed_rank(np.int64(3)) == 0
    assert calls.assumed_rank(np.complex128(1 + 2j)) == 0
    assert calls.assumed_rank(np.bool_(True)) == 0
    assert calls.scalar(np.int64(3)) == 10
    assert calls.scalar(np.float64(3)) == 10
    assert calls.scalar(np.complex128(3)) == 10
    assert calls.scalar(np.uint64(3)) == 10
    assert calls.scalar_without_intent(np.array(3, dtype=np.int64)) == 11
    assert calls.adapted_rank(np.float64(3)) == 0
    assert calls.assumed_size(np.arange(3, dtype=np.uint64)) == 20
    with pytest.raises(TypeError, match="no supported descriptor dtype"):
        calls.assumed_rank(np.arange(3, dtype=np.uint64))
    with pytest.raises(TypeError, match="cannot contain Python object references"):
        calls.assumed_size(np.array([object()], dtype=object))


def test_optional_absence_uses_dummy_specific_null_representation(calls):
    assert calls.optional_address() == 0
    assert calls.optional_address(None) == 0
    assert calls.optional_address(np.int64(4)) == 1
    assert calls.optional_descriptor() == 0
    assert calls.optional_descriptor(None) == 0
    assert calls.optional_descriptor(np.arange(2, dtype=np.int64)) == 1


def test_arbitrary_python_object_is_not_a_native_actual(calls):
    with pytest.raises(TypeError, match="requires NumPy storage or a PRIK native object"):
        calls.scalar(object())


def test_writable_scalar_requires_ndarray_storage(calls):
    with pytest.raises(TypeError, match="writable TYPE\\(\\*\\) requires a writable NumPy ndarray"):
        calls.modify_scalar(np.int64(7))
    value = np.array(7, dtype=np.int64)
    assert calls.modify_scalar(value) is None


def test_mutation_uses_the_address_or_descriptor_selected_by_the_dummy(tmp_path):
    built = build_fortran_extension(
        MUTATION_SOURCE,
        native_c_sources=[MUTATION_SOURCE.with_suffix(".c")],
        compile_input_sources=False,
        output_name="assumed_mutation_api",
        output_dir=tmp_path,
    )
    module = _import_from_build_dir(built.module_name, built.output_dir)
    raw = np.array([1, 2, 3], dtype=np.int64)
    strided = np.arange(5, dtype=np.int64)[::-1]
    scalar = np.array(7, dtype=np.int64)
    assert module.bump_address(raw) is None
    assert module.bump_descriptor(strided) is None
    assert module.bump_scalar(scalar) is None
    np.testing.assert_array_equal(raw, [2, 2, 3])
    np.testing.assert_array_equal(strided, [5, 3, 2, 1, 1])
    assert scalar == 8
