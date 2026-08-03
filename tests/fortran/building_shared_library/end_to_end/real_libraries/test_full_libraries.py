"""Real BLAS/LAPACK full-contract wrapper import and runtime tests."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from examples.blas.helpers import assert_runtime_smoke as assert_blas_runtime_smoke
from examples.lapack.contracts import remove_internal_root_imports
from examples.lapack.helpers import assert_runtime_smoke as assert_lapack_runtime_smoke
from examples.native_library import (
    BLAS_SOURCE_ROOT,
    LAPACK_SOURCE_ROOT,
    build_reference_library,
    library_sources,
    native_cache_root,
    require_tool,
)
from prik import build_pyi_extension
from prik.pipeline.pyi import pyi_paths_to_semantic_modules

pytestmark = pytest.mark.fortran_end_to_end
FULL_LIBRARY_WRAPPER_FLAGS = ("-O0", "-g0")
FULL_LIBRARY_CASES = {
    "blas": {
        "root_function_count": 155,
        "source_stem_exceptions": set(),
        "extra_function_names": set(),
        "sentinel_functions": {"dasum", "daxpy", "ddot", "dgemm", "dscal", "lsame", "xerbla"},
    },
    "lapack": {
        "root_function_count": 2064,
        "source_stem_exceptions": {"la_constants", "la_xisnan"},
        "extra_function_names": {"dladiv1", "dladiv2", "sladiv1", "sladiv2"},
        "sentinel_functions": {"dgesv", "dgetrf", "dgetrs", "dlamch", "dlamrg", "zgesv"},
    },
}


def _compiler() -> str:
    try:
        return require_tool("gfortran")
    except RuntimeError as error:
        pytest.skip(str(error))


def _library_sources(library: str) -> tuple[Path, ...]:
    return library_sources(library)


def _source_stems(library: str) -> set[str]:
    return {path.stem.lower() for path in _library_sources(library)}


def _generate_contract(source_root: Path, package: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source_root),
            "--language",
            "fortran",
            "--out",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return package / "__init__.pyi"


def _contract_modules(package: Path):
    return pyi_paths_to_semantic_modules([package])


def _root_module(package: Path):
    return next(module for module in _contract_modules(package) if module.name == "__init__")


def _function_names(package: Path) -> set[str]:
    return {function.name for module in _contract_modules(package) for function in module.functions}


def _runtime_entry(library: str, entry: Path) -> Path:
    if library != "lapack":
        return entry
    return remove_internal_root_imports(entry)


def _import_extension(module_name: str, build_dir: Path, *, lazy: bool = False):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    old_flags = sys.getdlopenflags()
    if lazy:
        sys.setdlopenflags(getattr(os, "RTLD_LAZY", old_flags) | getattr(os, "RTLD_GLOBAL", 0))
    try:
        return importlib.import_module(module_name)
    finally:
        if lazy:
            sys.setdlopenflags(old_flags)
        sys.path.remove(str(build_dir))


@pytest.mark.real_library
@pytest.mark.parametrize("library", ["blas", "lapack"])
def test_full_library_wrapper_imports_every_root_procedure_from_cached_shared_library(library: str, tmp_path: Path):
    source_root = BLAS_SOURCE_ROOT if library == "blas" else LAPACK_SOURCE_ROOT
    entry = _generate_contract(source_root, tmp_path / "contracts" / library)

    root = _root_module(entry.parent)
    all_function_names = _function_names(entry.parent)
    case = FULL_LIBRARY_CASES[library]

    assert len(root.functions) == case["root_function_count"]
    assert case["sentinel_functions"] <= all_function_names
    assert _source_stems(library) - all_function_names == case["source_stem_exceptions"]
    assert all_function_names - _source_stems(library) == case["extra_function_names"]

    cache_root = (
        native_cache_root() if os.environ.get("PRIK_REAL_LIBRARY_NATIVE_CACHE_DIR") else tmp_path / "native-cache"
    )
    shared = build_reference_library(library, cache_root=cache_root, compiler=_compiler()).shared_library
    runtime_entry = _runtime_entry(library, entry)
    expected_root_names = {function.name for function in _root_module(runtime_entry.parent).functions}
    result = build_pyi_extension(
        runtime_entry,
        output_name=f"full_{library}",
        output_dir=tmp_path / "build" / library,
        native_objects=[shared],
        wrapper_fortran_flags=FULL_LIBRARY_WRAPPER_FLAGS,
        wrapper_c_flags=FULL_LIBRARY_WRAPPER_FLAGS,
    )
    module = _import_extension(result.module_name, result.output_dir, lazy=library == "lapack")

    missing = sorted(name for name in expected_root_names if not hasattr(module, name))
    assert missing == []
    native_plan = result.native_build_plan.to_dict()
    assert native_plan["link_items"] == [{"kind": "shared_library", "path": str(shared)}]
    assert native_plan["compilation_units"] == []
    assert native_plan["module_dirs"] == []
    assert result.manifest is not None
    assert result.manifest["compiler"]["wrapper_fortran_flags"] == list(FULL_LIBRARY_WRAPPER_FLAGS)
    assert result.manifest["compiler"]["wrapper_c_flags"] == list(FULL_LIBRARY_WRAPPER_FLAGS)

    if library == "blas":
        bridge = (result.output_dir / "bind_c_full_blas_wrapper.f90").read_text(encoding="utf-8").lower()
        assert "use full_blas_interfaces" not in bridge
        assert "external :: daxpy" in bridge
        assert "subroutine daxpy(" not in bridge
        assert "private\n" not in bridge
        assert "public :: bind_c_daxpy" not in bridge
        assert_blas_runtime_smoke(module)
    else:
        assert_lapack_runtime_smoke(module)
