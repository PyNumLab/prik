"""Runtime native actual identity is independent of the dummy ABI."""

import ctypes
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from prik.compiler.native_support import install_native_support
from prik.compiler.compilers import Compiler
from prik.compiler.objects import ObjectFile
from prik.pipeline.build import build_fortran_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir


FIXTURES = Path(__file__).parent / "fixtures" / "native"


@pytest.fixture(scope="module")
def actuals(tmp_path_factory):
    output = tmp_path_factory.mktemp("assumed-type-actuals")
    install_native_support(("binding_support/prik_binding.h",), prik_dirpath=output)
    compiler = Compiler.from_fortran_executable()
    probe_object = ObjectFile(
        source=FIXTURES / "assumed_type_probe.c",
        object_path=output / "assumed_type_probe.o",
        language="c",
        include_dirs=(output / "binding_support",),
        tools=frozenset({"python"}),
    )
    compiler.compile_object(probe_object)
    probe_path = compiler.link_extension(
        module_name="assumed_type_probe",
        output_dir=output,
        language="c",
        objects=(probe_object,),
    )
    spec = importlib.util.spec_from_file_location("assumed_type_probe", probe_path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    built = build_fortran_extension(
        FIXTURES / "assumed_type_derived.f90",
        output_name="assumed_derived_api",
        output_dir=output / "derived",
    )
    derived = _import_from_build_dir(built.module_name, built.output_dir).assumed_type_derived
    return probe, derived


def test_numpy_actuals_keep_native_type_size_and_rank(actuals):
    probe, _ = actuals
    scalar = [np.int64(3), np.float64(3), np.complex128(3)]
    descriptions = [probe.describe(value) for value in scalar]
    assert [item[2:] for item in descriptions] == [(8, 0), (8, 0), (16, 0)]
    assert len({item[0] for item in descriptions}) == 3
    assert len({item[1] for item in descriptions}) == 3
    assert probe.describe(np.arange(3, dtype=np.int64)) == (*descriptions[0][:3], 1)
    assert probe.describe(np.ones((2, 3), dtype=np.float64)) == (*descriptions[1][:3], 2)
    assert probe.describe(np.array(3, dtype=np.int64)) == descriptions[0]


def test_derived_types_of_equal_size_keep_distinct_identity(actuals):
    probe, derived = actuals
    first = derived.make_first()
    second = derived.make_second()
    first_actual = probe.describe(first)
    second_actual = probe.describe(second)
    assert first_actual[0] == second_actual[0] == probe.CFI_TYPE_OTHER
    assert probe.describe(derived.make_interoperable())[0] == probe.CFI_TYPE_STRUCT
    assert first_actual[2:] == second_actual[2:] == (8, 0)
    assert first_actual[1] != second_actual[1]
    assert derived.scalar(first) == derived.scalar(second) == 1
    assert derived.any_rank(first) == derived.any_rank(second) == 0
    assert derived.scalar(derived.addressable) == 1


def test_zero_storage_derived_class_keeps_address_abi_available(actuals):
    probe, derived = actuals
    empty = derived.make_empty()
    assert probe.describe(empty)[2:] == (0, 0)
    assert derived.direct_scalar(empty) == 2
    with pytest.raises(TypeError, match="no native element storage for a descriptor"):
        derived.direct_any_rank(empty)


def test_derived_element_size_cannot_be_overridden_from_python(actuals, monkeypatch):
    probe, derived = actuals
    first = derived.make_first()
    second = derived.make_second()
    monkeypatch.setattr(type(first), "_prik_element_size", 1, raising=False)
    assert probe.describe(first)[2] == 8
    assert derived.any_rank(first) == 0
    monkeypatch.setattr(type(first), "_prik_type_info", type(second)._prik_type_info)
    with pytest.raises(TypeError, match="incompatible type metadata"):
        probe.describe(first)


def test_cross_extension_origin_refuses_an_unversioned_capsule(actuals, monkeypatch):
    probe, derived = actuals
    original = derived.plain._prik_ops["_native_ops"]
    get_name = ctypes.pythonapi.PyCapsule_GetName
    get_name.argtypes = [ctypes.py_object]
    get_name.restype = ctypes.c_char_p
    name = get_name(original)
    assert name.startswith(b"prik.derived_origin_ops.v2.")
    get_pointer = ctypes.pythonapi.PyCapsule_GetPointer
    get_pointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
    get_pointer.restype = ctypes.c_void_p
    pointer = get_pointer(original, name)
    create_capsule = ctypes.pythonapi.PyCapsule_New
    create_capsule.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
    create_capsule.restype = ctypes.py_object
    old_name = ctypes.create_string_buffer(b"prik.derived_origin_ops")
    stale = create_capsule(pointer, ctypes.cast(old_name, ctypes.c_char_p), None)
    monkeypatch.setitem(derived.plain._prik_ops, "_native_ops", stale)
    with pytest.raises(ValueError, match="incorrect name"):
        probe.describe(derived.plain)


def test_module_owned_actuals_keep_address_and_scoped_origins(actuals):
    probe, derived = actuals
    derived.reset_pointer()
    assert derived.addressable._prik_origin == "module_target"
    assert derived.plain._prik_origin == "module_proxy"
    assert derived.pointer_value._prik_origin == "module_pointer"
    assert probe.describe(derived.make_first())[1:3] == probe.describe(derived.plain)[1:3]
    for actual in (derived.addressable, derived.plain, derived.pointer_value):
        assert derived.scalar(actual) == 1
        assert derived.any_rank(actual) == 0
        assert derived.direct_scalar(actual) == 2
        assert derived.direct_any_rank(actual) == 0
        assert derived.optional_scalar(actual) == 1
        assert derived.optional_rank(actual) == 1
    assert derived.optional_scalar() == 0
    assert derived.optional_rank() == 0
    assert derived.two_origins(derived.plain, derived.pointer_value) == 3


def test_module_proxy_crosses_extension_boundary_without_type_enumeration(actuals, tmp_path):
    _, derived = actuals
    source = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "native" / "assumed_type_calls.f90"
    built = build_fortran_extension(source, output_name="cross_type_api", output_dir=tmp_path)
    calls = _import_from_build_dir(built.module_name, built.output_dir).assumed_type_calls
    assert calls.scalar(derived.plain) == 10
    assert calls.assumed_rank(derived.plain) == 0


def test_arbitrary_class_has_no_native_representation(actuals):
    probe, _ = actuals
    with pytest.raises(TypeError, match="requires NumPy storage or a PRIK native object"):
        probe.describe(object())
