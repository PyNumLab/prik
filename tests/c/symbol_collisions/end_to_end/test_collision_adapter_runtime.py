"""A native symbol the binding's own headers declare is callable through an adapter."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import build_fortran_extension, build_pyi_extension, build_pyi_extension_from_manifest
from tests.c._support.paths import REPO_ROOT
from tests.c._support.runtime import sole_native_module

# This user API deliberately reuses the `Py_Initialize` identifier with a
# different signature from the declaration brought in directly by Python.h.
_CONTRACT = """from prik.contracts import Arg, CLongLong, Int64, Return, native_call

@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))
def Py_Initialize(value: Int64) -> Int64: ...
"""

_NATIVE_SOURCE = """__attribute__((visibility("hidden")))
long long Py_Initialize(long long value) { return value + 7; }
"""

_ALIASED_CONTRACT = """from prik.contracts import Arg, CLongLong, Int64, Return, bind, native_call

@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))
def Py_Initialize(value: Int64) -> Int64: ...

@bind("Py_Initialize")
@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))
def initialize_alias(value: Int64) -> Int64: ...
"""

_BIND_C_SOURCE = """module m
  use iso_c_binding
  implicit none
contains
  real(c_double) function scaled(x) bind(c, name="scaled")
    real(c_double), intent(in), value :: x
    scaled = 2.0_c_double * x
  end function scaled
end module m
"""


def _contract(tmp_path: Path) -> Path:
    path = tmp_path / "libm_contract.pyi"
    path.write_text(_CONTRACT, encoding="utf-8")
    return path


def _native_source(tmp_path: Path) -> Path:
    path = tmp_path / "collision_native.c"
    path.write_text(_NATIVE_SOURCE, encoding="utf-8")
    return path


def _aliased_contract(tmp_path: Path) -> Path:
    path = tmp_path / "aliased_contract.pyi"
    path.write_text(_ALIASED_CONTRACT, encoding="utf-8")
    return path


def _bind_c_source(tmp_path: Path) -> Path:
    path = tmp_path / "bind_c_collision.f90"
    path.write_text(_BIND_C_SOURCE, encoding="utf-8")
    return path


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_a_symbol_declared_by_the_binding_headers_fails_to_compile_unadapted(tmp_path: Path):
    with pytest.raises(RuntimeError, match="conflicting types for"):
        build_pyi_extension(
            _contract(tmp_path),
            native_language="c",
            native_c_sources=[_native_source(tmp_path)],
            output_dir=tmp_path / "unadapted",
            output_name="libm_unadapted",
        )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_a_collision_adapted_symbol_compiles_and_calls_the_native_implementation(tmp_path: Path):
    result = build_pyi_extension(
        _contract(tmp_path),
        native_language="c",
        native_c_sources=[_native_source(tmp_path)],
        collision_adapters=["Py_Initialize"],
        output_dir=tmp_path / "adapted",
        output_name="libm_adapted",
    )
    module = sole_native_module(result.import_module())

    assert module.Py_Initialize(np.int64(5)) == np.int64(12)
    assert module.Py_Initialize(np.int64(-9)) == np.int64(-2)

    binding = next(path for path in result.generated_sources if path.name.endswith("_wrapper.c"))
    adapters = next(path for path in result.generated_sources if path.name.endswith("_adapters.c"))
    assert "long long Py_Initialize(long long value);" not in binding.read_text(encoding="utf-8")
    adapter_text = adapters.read_text(encoding="utf-8")
    assert "long long Py_Initialize(long long value);" in adapter_text
    assert "return (Py_Initialize)(value);" in adapter_text


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_aliased_callables_compile_and_share_one_collision_adapter(tmp_path: Path):
    result = build_pyi_extension(
        _aliased_contract(tmp_path),
        native_language="c",
        native_c_sources=[_native_source(tmp_path)],
        collision_adapter_all=True,
        output_dir=tmp_path / "aliased",
        output_name="aliased_collision",
    )
    module = sole_native_module(result.import_module())

    assert module.Py_Initialize(np.int64(5)) == np.int64(12)
    assert module.initialize_alias(np.int64(-9)) == np.int64(-2)


@pytest.mark.skipif(
    shutil.which("cc") is None or shutil.which("gfortran") is None,
    reason="requires C and Fortran compilers",
)
def test_collision_adapter_all_builds_a_fortran_bind_c_module_without_an_adapter(tmp_path: Path):
    result = build_fortran_extension(
        _bind_c_source(tmp_path),
        collision_adapter_all=True,
        output_dir=tmp_path / "bind_c",
        output_name="bind_c_collision",
    )
    module = sole_native_module(result.import_module())

    assert module.scaled(np.float64(3.0)) == np.float64(6.0)
    assert not any(path.name.endswith("_adapters.c") for path in result.generated_sources)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_an_unknown_collision_adapter_name_fails_before_wrapper_planning(tmp_path: Path):
    with pytest.raises(ValueError, match="unknown or ineligible names: missing"):
        build_pyi_extension(
            _contract(tmp_path),
            native_language="c",
            native_c_sources=[_native_source(tmp_path)],
            collision_adapters=["missing"],
            generate_sources=True,
            output_dir=tmp_path / "unknown",
            output_name="unknown_collision",
        )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_build_manifest_replay_retains_the_selected_collision_adapter(tmp_path: Path):
    generated = build_pyi_extension(
        _contract(tmp_path),
        native_language="c",
        native_c_sources=[_native_source(tmp_path)],
        collision_adapters=["Py_Initialize"],
        makefile=True,
        output_dir=tmp_path / "replay",
        output_name="collision_replay",
    )

    assert generated.build_manifest is not None
    assert generated.manifest["extension"]["collision_adapters"] == ["Py_Initialize"]
    replay = build_pyi_extension_from_manifest(generated.build_manifest)
    module = sole_native_module(replay.import_module())

    assert module.Py_Initialize(np.int64(5)) == np.int64(12)
    assert any(path.name.endswith("_adapters.c") for path in replay.generated_sources)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_cli_selected_collision_adapter_builds_an_importable_extension(tmp_path: Path):
    output_dir = tmp_path / "cli"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "--language",
            "c",
            str(_contract(tmp_path)),
            "--native-c-sources",
            str(_native_source(tmp_path)),
            "--collision-adapter",
            "Py_Initialize",
            "--lto",
            "--out",
            "collision_cli",
            "--out-dir",
            str(output_dir),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert any(path.endswith("collision_cli_adapters.c") for path in payload["generated_sources"])
    assert payload["manifest"]["compiler"]["c_flags"][-1] == "-flto"
    assert payload["manifest"]["compiler"]["wrapper_c_flags"][-1] == "-flto"
    sys.path.insert(0, str(output_dir))
    try:
        module = sole_native_module(importlib.import_module("collision_cli"))
        assert module.Py_Initialize(np.int64(5)) == np.int64(12)
    finally:
        sys.path.remove(str(output_dir))
        sys.modules.pop("collision_cli", None)
