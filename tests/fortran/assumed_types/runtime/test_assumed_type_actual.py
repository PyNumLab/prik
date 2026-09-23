"""Runtime native actual identity is independent of the dummy ABI."""

import importlib.util
import subprocess
import sysconfig
from pathlib import Path

import numpy as np
import pytest

from prik.compiler.native_support import install_native_support
from prik.pipeline.build import build_fortran_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir


FIXTURES = Path(__file__).parent / "fixtures" / "native"


@pytest.fixture(scope="module")
def actuals(tmp_path_factory):
    output = tmp_path_factory.mktemp("assumed-type-actuals")
    install_native_support(("binding_support/prik_binding.h",), prik_dirpath=output)
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    probe_path = output / f"assumed_type_probe{suffix}"
    subprocess.run(
        [
            "cc",
            "-shared",
            "-fPIC",
            "-O3",
            f"-I{output / 'binding_support'}",
            f"-I{np.get_include()}",
            f"-I{sysconfig.get_path('include')}",
            str(FIXTURES / "assumed_type_probe.c"),
            "-o",
            str(probe_path),
        ],
        check=True,
        capture_output=True,
        text=True,
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
    assert first_actual[2:] == second_actual[2:] == (8, 0)
    assert first_actual[1] != second_actual[1]
    assert derived.scalar(first) == derived.scalar(second) == 1
    assert derived.any_rank(first) == derived.any_rank(second) == 0
    assert derived.scalar(derived.addressable) == 1


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
