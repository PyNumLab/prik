"""Compiled immediate-callback direct and mixed entrypoint evidence."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
pytestmark = pytest.mark.fortran_end_to_end


def test_callbacks_all_direct_route_uses_binding_trampolines_without_adapter(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "callbacks_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"callbacks_direct_bind_c_f90_wrapper.c", "callbacks_direct_bind_c_f90_wrapper.h"},
        FIXTURES / "contracts" / "callbacks_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    calls = []
    assert module.direct_apply(lambda value: np.float64(2.0) * value, np.float64(3.0)) == np.float64(6.0)
    assert module.direct_call_notify(lambda value: calls.append(value), np.int32(7)) is None
    assert calls == [np.int32(7)]
    assert module.direct_apply(
        lambda value: module.direct_apply(lambda nested: nested + 1.0, np.float64(value)) * 2.0,
        np.float64(3.0),
    ) == np.float64(8.0)

    class Callback:
        def __call__(self, value):
            return value

    callback = Callback()
    references_before = sys.getrefcount(callback)
    assert module.direct_apply(callback, np.float64(3.0)) == np.float64(3.0)
    assert sys.getrefcount(callback) == references_before
    with pytest.raises(TypeError, match="must be callable"):
        module.direct_apply(42, np.float64(1.0))

    if pyi_parity_build_mode == "source":
        binding = (tmp_path / "source_build" / "callbacks_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "double direct_apply(double (*callback)(double), double value);" in binding
        assert "void direct_call_notify(void (*callback)(int32_t), int32_t value);" in binding
        assert "static _Thread_local" in binding
        assert "PyGILState_Ensure()" in binding
        assert "direct_apply(prik_callback_trampoline_" in binding

    build_dir = (
        tmp_path / "source_build"
        if pyi_parity_build_mode == "source"
        else tmp_path / "generated_pyi_build" / "pyi_build"
    )
    failure = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import numpy as np; import callbacks_direct_bind_c_f90 as root; "
                "module = getattr(root, 'callbacks_direct_bind_c_f90', root); "
                "module.direct_apply(lambda value: (_ for _ in ()).throw("
                "ValueError(f'callback exploded at {value}')), np.float64(4.0))"
            ),
        ],
        cwd=build_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert failure.returncode != 0
    assert "ValueError: callback exploded at 4.0" in failure.stderr


def test_callbacks_mixed_route_adapts_only_non_c_callback_signature(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "callbacks_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "callbacks_mixed_bind_c_f90_wrapper.c",
            "callbacks_mixed_bind_c_f90_wrapper.h",
            "bind_c_callbacks_mixed_bind_c_f90_wrapper.f90",
        },
        FIXTURES / "contracts" / "callbacks_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_apply(lambda value: np.float64(value + 1.0), np.float64(3.0)) == np.float64(4.0)
    assert module.adapted_apply(lambda value: np.float64(value + 2.0), np.float64(3.0)) == np.float64(5.0)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_callbacks_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        assert "bind_c_adapted_apply" in bridge
        assert "direct_apply" not in bridge

        binding = (tmp_path / "source_build" / "callbacks_mixed_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "bind_c_adapted_apply(bound_value)" in binding


def test_callbacks_mixed_route_matches_edited_source_free_contract(tmp_path: Path):
    stem = "callbacks_mixed_bind_c_f90"
    source = (FIXTURES / "native" / f"{stem}.f90").read_text(encoding="utf-8")
    contract = (FIXTURES / "contracts" / stem / f"{stem}.pyi").read_text(encoding="utf-8")
    contract = contract.replace("from prik.contracts import ", "from prik.contracts import nogil, ")
    contract = contract.replace("def direct_apply(", "@nogil\ndef direct_apply(").replace(
        "def adapted_apply(", "@nogil\ndef adapted_apply("
    )
    module, result = _build_inline_pyi_contract_module(
        tmp_path, module_name=stem, source_text=source, contract_text=contract
    )

    assert module.direct_apply(lambda value: np.float64(value + 1.0), np.float64(3.0)) == np.float64(4.0)
    assert module.adapted_apply(lambda value: np.float64(value + 2.0), np.float64(3.0)) == np.float64(5.0)
    bridge = (result.output_dir / f"bind_c_{stem}_wrapper.f90").read_text(encoding="utf-8").casefold()
    assert "bind_c_adapted_apply" in bridge
    assert "function bind_c_direct_apply" not in bridge
