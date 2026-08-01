"""Runtime status projection through a reviewed edited semantic contract."""

from pathlib import Path
import threading
import time

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_pyi_extension


FIXTURES = Path(__file__).parent / "fixtures"
RUNTIME_POLICY_SOURCE = FIXTURES / "native" / "fruntime_policy_f90.f90"
EDITED_POLICY_CONTRACT = FIXTURES / "edited_contract" / "fruntime_policy_f90.pyi"
pytestmark = pytest.mark.fortran_end_to_end


def _python_thread_runs_before_native_return(native_call) -> bool:
    observed: dict[str, float] = {}

    def observe() -> None:
        time.sleep(0.05)
        observed["time"] = time.monotonic()

    worker = threading.Thread(target=observe)
    worker.start()
    native_call()
    returned = time.monotonic()
    worker.join(timeout=2.0)
    assert not worker.is_alive()
    return observed["time"] < returned


def test_status_projection_consumes_outputs_raises_message_and_recovers(tmp_path: Path):
    native_object = _compile_native_object(RUNTIME_POLICY_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        EDITED_POLICY_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert _python_thread_runs_before_native_return(module.pause_for_one_second)
    assert module.solve(np.int32(1)) is None
    for _ in range(3):
        with pytest.raises(RuntimeError, match="negative input"):
            module.solve(np.int32(-1))
    assert module.solve(np.int32(2)) is None

    binding = (result.output_dir / "fruntime_policy_f90_wrapper.c").read_text(encoding="utf-8")
    held = binding[
        binding.index("static PyObject * wrap_pause_with_gil") : binding.index("static PyObject * wrap_solve")
    ]
    assert "Py_BEGIN_ALLOW_THREADS" not in held
    assert "Py_END_ALLOW_THREADS" not in held
    solve = binding[binding.index("static PyObject * wrap_solve") : binding.index("PyMODINIT_FUNC")]
    assert solve.index("Py_END_ALLOW_THREADS") < solve.index("status != 0")
    assert solve.index("PyUnicode_FromString") < solve.index("free(message)") < solve.index("status != 0")
    error_start = solve.index("if (status != 0)")
    error_path = solve[error_start : solve.index("Py_RETURN_NONE")]
    assert error_path.index("PyErr_SetObject(PyExc_RuntimeError, message_obj)") < error_path.index(
        "Py_DECREF(message_obj)"
    )
    assert error_path.index("Py_DECREF(message_obj)") < error_path.index("return NULL")
