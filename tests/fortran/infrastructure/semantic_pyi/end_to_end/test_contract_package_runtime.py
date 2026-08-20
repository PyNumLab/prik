"""Source-free `.pyi` contract package runtime tests."""

from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture
from tests.fortran._support.wrapper_build import REPO_ROOT

SEMANTIC_PYI_FIXTURES = REPO_ROOT / "tests" / "fortran" / "infrastructure" / "semantic_pyi" / "pipeline" / "fixtures"
NATIVE_FIXTURES = SEMANTIC_PYI_FIXTURES / "native"
CONTRACT_FIXTURES = SEMANTIC_PYI_FIXTURES / "contracts"
STANDALONE_ONLY = NATIVE_FIXTURES / "contract_standalone_only.f90"
pytestmark = pytest.mark.fortran_end_to_end


def _compiler() -> str:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("gfortran is required for contract package runtime tests")
    return compiler


def _copy_source(source_template: Path, workdir: Path) -> Path:
    source = workdir / source_template.name
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_template, source)
    return source


def _compile_native(source: Path, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    native_object = workdir / f"{source.stem}.o"
    subprocess.run(
        [
            _compiler(),
            "-fPIC",
            "-c",
            str(source),
            "-o",
            str(native_object),
            "-J",
            str(workdir),
        ],
        check=True,
    )
    return native_object


def _generate_contract_package(source: Path, output_parent: Path) -> Path:
    package = output_parent / source.stem
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert_generated_pyi_package_matches_fixture(
        package,
        CONTRACT_FIXTURES / source.stem / "generated",
    )
    return package / "__init__.pyi"


def _run_json(command: list[str], *, cwd: Path | None = None) -> dict[str, object]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _import_extension(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


def _build_contract(
    entry: Path | str,
    native_object: Path,
    build_dir: Path,
    *,
    cwd: Path | None = None,
    output_name: str | None = None,
):
    invocation_dir = cwd or build_dir
    invocation_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "prik",
        str(entry),
        "--native-objects",
        str(native_object),
        "-I",
        str(native_object.parent),
        "--out-dir",
        str(build_dir),
        "--json",
    ]
    if output_name is not None:
        command.extend(("--out", output_name))
    payload = _run_json(command, cwd=invocation_dir)
    module = _import_extension(str(payload["module_name"]), build_dir)
    return module, payload


def test_output_name_override_replaces_entry_inference(tmp_path: Path):
    source = _copy_source(STANDALONE_ONLY, tmp_path)
    entry = _generate_contract_package(source, tmp_path / "contracts")
    native_object = _compile_native(source, tmp_path / "native")

    module, payload = _build_contract(
        entry,
        native_object,
        tmp_path / "build",
        output_name="custom_api",
    )

    assert payload["module_name"] == "custom_api"
    assert Path(str(payload["shared_library"])).name.startswith("custom_api.")
    assert module.standalone_ping() is None
