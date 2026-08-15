"""Compiled status checking and GIL policy across direct and mixed routes."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def _build(tmp_path: Path, stem: str):
    return _build_inline_pyi_contract_module(
        tmp_path,
        module_name=stem,
        source_text=(FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8"),
        contract_text=(FIXTURES / "contracts" / f"{stem}.pyi").read_text(encoding="utf-8"),
    )


def test_status_and_gil_all_direct_route_has_no_adapter(tmp_path: Path):
    module, result = _build(tmp_path, "error_handling_direct_bind_c_f90")

    assert module.direct_solve(np.int32(4)) == np.int32(8)
    with pytest.raises(RuntimeError, match="status 5"):
        module.direct_solve(np.int32(-1))
    assert {path.name for path in result.generated_sources} == {
        "error_handling_direct_bind_c_f90_wrapper.c",
        "error_handling_direct_bind_c_f90_wrapper.h",
    }

    binding = (result.output_dir / "error_handling_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
    wrapper = binding[binding.index("static PyObject * wrap_direct_solve") : binding.index("PyMODINIT_FUNC")]
    assert wrapper.index("Py_BEGIN_ALLOW_THREADS") < wrapper.index("direct_solve(bound_value, &output, &status)")
    assert wrapper.index("Py_END_ALLOW_THREADS") < wrapper.index("status != 0")


def test_status_and_gil_mixed_route_adapts_only_ordinary_operation(tmp_path: Path):
    module, result = _build(tmp_path, "error_handling_mixed_bind_c_f90")

    assert module.direct_solve(np.int32(4)) == np.int32(8)
    assert module.adapted_solve(np.int32(4)) == np.int32(12)
    with pytest.raises(RuntimeError):
        module.direct_solve(np.int32(-1))
    with pytest.raises(RuntimeError):
        module.adapted_solve(np.int32(-1))

    bridge = (
        (result.output_dir / "bind_c_error_handling_mixed_bind_c_f90_wrapper.f90")
        .read_text(encoding="utf-8")
        .casefold()
    )
    assert "bind_c_adapted_solve" in bridge
    assert "direct_solve" not in bridge
