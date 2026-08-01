"""Scalar callbacks, callback lifetime, GIL handling, and fatal errors."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
CALLBACK_SCALAR_F90_SOURCE = FIXTURES / "fcallback_scalar_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def _callback_scalar_build_dir(tmp_path: Path, build_mode: str) -> Path:
    if build_mode == "source":
        return tmp_path / "source_build"
    return tmp_path / "generated_pyi_build" / "pyi_build"


@pytest.fixture
def compiled_scalar_callback_module(pyi_parity_build_mode: str, tmp_path: Path):
    module = _build_source_or_generated_pyi_and_import(
        CALLBACK_SCALAR_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fcallback_scalar_f90_wrapper.f90",
            "fcallback_scalar_f90_wrapper.c",
            "fcallback_scalar_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fcallback_scalar_f90",
        pyi_parity_build_mode,
    )
    return module, _callback_scalar_build_dir(tmp_path, pyi_parity_build_mode), pyi_parity_build_mode


def test_immediate_scalar_dummy_procedure_calls_python_callback(compiled_scalar_callback_module):
    module, build_dir, build_mode = compiled_scalar_callback_module

    def triple(value):
        assert isinstance(value, np.float64)
        return float(value) * 3.0

    def decrement(value):
        assert isinstance(value, np.float64)
        return value - 1.0

    assert module.apply_scalar(triple, np.float64(2.5)) == np.float64(7.5)
    assert module.apply_explicit(decrement, np.float64(2.5)) == np.float64(1.5)
    notified = []

    def notify(value):
        assert isinstance(value, np.float64)
        notified.append(value)

    assert module.call_notify(notify, np.float64(6.0)) is None
    assert notified == [6.0]
    assert module.apply_scalar(
        lambda value: module.apply_scalar(lambda nested: nested + 1.0, np.float64(value)) * 2.0,
        np.float64(3.0),
    ) == np.float64(8.0)

    class Callback:
        def __call__(self, value):
            return value

    callback = Callback()
    references_before = sys.getrefcount(callback)
    assert module.apply_scalar(callback, np.float64(3.0)) == np.float64(3.0)
    assert sys.getrefcount(callback) == references_before
    with pytest.raises(TypeError, match="must be callable"):
        module.apply_scalar(42, np.float64(1.0))

    if build_mode == "source":
        wrapper_source = (build_dir / "fcallback_scalar_f90_wrapper.c").read_text(encoding="utf-8")
        assert "static _Thread_local" in wrapper_source
        assert "PyThread_get_thread_ident()" in wrapper_source
        assert "PyGILState_Ensure()" in wrapper_source
        assert "PyGILState_Release(" in wrapper_source
        assert "Py_BEGIN_ALLOW_THREADS" not in wrapper_source
        assert "Py_END_ALLOW_THREADS" not in wrapper_source
        assert "PyErr_PrintEx(0);" in wrapper_source
        assert "abort();" in wrapper_source
        assert "callback_callback_context.callable = bound_callback_obj;" in wrapper_source
        assert "Py_INCREF(bound_callback_obj);" in wrapper_source
        assert "Py_DECREF(" in wrapper_source

    _assert_callback_failures_abort(build_dir)


def _assert_callback_failures_abort(build_dir: Path):
    script = """
import numpy as np
import fcallback_scalar_f90 as module
module = module.fcallback_scalar_f90

def fail(value):
    raise ValueError(f"callback exploded at {value}")

module.apply_scalar(fail, np.float64(4.0))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=build_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Traceback (most recent call last)" in result.stderr
    assert "ValueError: callback exploded at 4.0" in result.stderr

    invalid_return = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import numpy as np; import fcallback_scalar_f90 as root; module = root.fcallback_scalar_f90; "
                "module.apply_scalar(lambda value: 'wrong', np.float64(4.0))"
            ),
        ],
        cwd=build_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert invalid_return.returncode != 0
    assert "TypeError" in invalid_return.stderr

    invalid_signature = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import numpy as np; import fcallback_scalar_f90 as root; module = root.fcallback_scalar_f90; "
                "module.apply_scalar(lambda: np.float64(1.0), np.float64(4.0))"
            ),
        ],
        cwd=build_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert invalid_signature.returncode != 0
    assert "TypeError" in invalid_signature.stderr
