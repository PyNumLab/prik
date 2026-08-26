"""Semantic .pyi driven wrapper build tests."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from prik import build_pyi_extension, build_pyi_extension_from_manifest
from prik.pipeline.build import WrapperBuildResult, build_fortran_extension
from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture

FEATURE_ROOT = Path(__file__).resolve().parents[1]
SOURCE = FEATURE_ROOT / "end_to_end" / "fixtures" / "native" / "fruntime_abi_f90.f90"
CONTRACT_FIXTURES = FEATURE_ROOT / "end_to_end" / "fixtures" / "contracts"
PYI_FIXTURE = CONTRACT_FIXTURES / "runtime_abi" / "fruntime_abi_f90.pyi"
RUNTIME_ABI_GENERATED = CONTRACT_FIXTURES / "runtime_abi"


def _compile_native_object(source: Path, workdir: Path) -> Path:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("gfortran is required to compile native .pyi wrapper test artifacts")

    workdir.mkdir(parents=True, exist_ok=True)
    native_source = workdir / source.name
    shutil.copyfile(source, native_source)
    native_object = workdir / f"{source.stem}.o"
    subprocess.run(
        [
            compiler,
            "-fPIC",
            "-c",
            str(native_source),
            "-o",
            str(native_object),
            "-J",
            str(workdir),
        ],
        check=True,
    )
    return native_object


def _import_from_build_dir(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


def _build_pyi_cli(pyi_path: Path, native_object: Path, build_dir: Path):
    build_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "prik",
        str(pyi_path),
        "--native-objects",
        str(native_object),
        "-I",
        str(native_object.parent),
        "--out-dir",
        str(build_dir),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=build_dir)
    payload = json.loads(result.stdout)
    return _import_from_build_dir(payload["module_name"], build_dir), payload


def _generate_pyi(source: Path, output_parent: Path, expected_package: Path | None = None) -> Path:
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
    if expected_package is not None:
        assert_generated_pyi_package_matches_fixture(package, expected_package)
    return package / "__init__.pyi"


def _sole_native_module(module):
    children = [
        value
        for value in vars(module).values()
        if isinstance(value, ModuleType) and value.__name__.startswith(f"{module.__name__}.")
    ]
    return children[0] if len(children) == 1 else module


def _assert_scale_runtime_contract(module) -> None:
    assert module.scale(np.float64(2.0), np.float64(4.0)) == np.float64(8.0)


def test_wrapper_build_result_import_module_loads_and_caches_a_built_extension(tmp_path: Path):
    result = build_fortran_extension(SOURCE, output_dir=tmp_path / "source_build")

    sys.modules.pop(result.module_name, None)
    try:
        module = result.import_module()
        assert module.__file__ == str(result.shared_library)
        native_module = _sole_native_module(module)
        assert native_module.scale(np.float64(3.0), np.float64(2.5)) == np.float64(7.5)
        assert result.import_module() is module
    finally:
        sys.modules.pop(result.module_name, None)


def test_wrapper_build_result_import_module_requires_a_built_artifact(tmp_path: Path):
    result = WrapperBuildResult(
        sources=(),
        module_name="missing_extension",
        output_dir=tmp_path,
        shared_library=tmp_path / "missing_extension.so",
        build_makefile=None,
        compiled=False,
        generated_sources=(),
        generated_files=(),
    )

    with pytest.raises(FileNotFoundError, match=r"Built extension not found: .+missing_extension\.so"):
        result.import_module()


@pytest.fixture
def scale_runtime_module(pyi_parity_build_mode: str, tmp_path: Path):
    if pyi_parity_build_mode == "source":
        result = build_fortran_extension(SOURCE, output_dir=tmp_path / "source_build")
        return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    generated_pyi = _generate_pyi(SOURCE, tmp_path / "contracts", RUNTIME_ABI_GENERATED)
    native_object = _compile_native_object(SOURCE, tmp_path / "native")
    module, _payload = _build_pyi_cli(generated_pyi, native_object, tmp_path / "pyi_build")
    return _sole_native_module(module)


def test_pyi_cli_requires_a_native_link_input(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, "-m", "prik", str(PYI_FIXTURE), "--out-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "A .pyi wrapper build requires --native-fortran-sources" in result.stderr


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("make") is None or shutil.which("gfortran") is None,
    reason="generated Makefile requires GNU Make and a POSIX shell",
)
def test_pyi_makefile_manifest_and_replay_workflows(tmp_path: Path):
    native_source = tmp_path / SOURCE.name
    build_dir = tmp_path / "pyi_build"
    build_dir.mkdir()
    shutil.copyfile(SOURCE, native_source)
    include_dir = tmp_path / "include"
    include_dir.mkdir()
    selected_compiler = tmp_path / "selected-gfortran"
    selected_compiler.symlink_to(shutil.which("gfortran"))

    generated = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--makefile",
            str(PYI_FIXTURE),
            "--native-fortran-sources",
            str(native_source),
            "--compiler",
            str(selected_compiler),
            "-I",
            str(include_dir),
            "--native-compile-flags=-O2 -g0",
            "--wrapper-compiler-debug",
            "--wrapper-fortran-flags=-fno-range-check -g0",
            "--wrapper-c-flags=-O0 -g0",
            "--out-dir",
            str(build_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=build_dir,
    )
    payload = json.loads(generated.stdout)
    manifest_path = Path(payload["build_manifest"])
    makefile_path = Path(payload["build_makefile"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    makefile_text = makefile_path.read_text(encoding="utf-8")

    assert payload["compiled"] is False
    assert manifest_path == build_dir / "prik-build.json"
    assert makefile_path == build_dir / "Makefile.prik"
    assert manifest == payload["manifest"]
    assert manifest["schema_version"] == 4
    assert manifest["build_kind"] == "pyi-wrapper"
    assert manifest["compiler"]["input_executable"] == str(selected_compiler)
    assert manifest["compiler"]["fortran_flags"] == ["-O2", "-g0"]
    assert manifest["compiler"]["wrapper_compiler_debug"] is True
    assert manifest["compiler"]["wrapper_fortran_flags"] == ["-fno-range-check", "-g0"]
    assert manifest["compiler"]["wrapper_c_flags"] == ["-O0", "-g0"]
    assert manifest["entry_contract"].endswith("fruntime_abi_f90.pyi")
    assert manifest["native_array_build_requirements"] == {
        "pointer_c_descriptor_interop": False,
        "headers": [],
        "items": [],
    }
    assert manifest["generated_wrapper"]["native_code_groups"][0]["kind"] == "fortran_adapters"
    assert any(
        path.endswith("bind_c_fruntime_abi_f90_wrapper.f90") for path in manifest["generated_wrapper"]["sources"]
    )
    assert [item["kind"] for item in manifest["native_build_plan"]["link_items"]] == ["object"]
    assert manifest["native_build_plan"]["compilation_units"][0]["source"].endswith(native_source.name)
    manifest_includes = manifest["native_build_plan"]["compilation_units"][0]["include_dirs"]
    assert include_dir.resolve() in tuple((build_dir / path).resolve() for path in manifest_includes)
    assert str(selected_compiler) in makefile_text
    assert str(include_dir) in makefile_text
    assert "-O2" in makefile_text
    assert "-g0" in makefile_text
    assert "-fno-range-check" in makefile_text
    assert "-O0" in makefile_text
    assert "prik-build.json" in makefile_text
    assert str(PYI_FIXTURE) in makefile_text
    assert not Path(payload["shared_library"]).exists()

    subprocess.run(["make", "-j4", "-f", str(makefile_path), "all"], capture_output=True, text=True, check=True)
    assert Path(payload["shared_library"]).is_file()
    module = _sole_native_module(_import_from_build_dir(payload["module_name"], build_dir))
    _assert_scale_runtime_contract(module)

    makefile_path.unlink()
    regenerated = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--makefile",
            "--build-manifest",
            str(manifest_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=build_dir,
    )
    regenerated_payload = json.loads(regenerated.stdout)
    assert regenerated_payload["compiled"] is False
    assert Path(regenerated_payload["build_makefile"]).is_file()
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest

    Path(payload["shared_library"]).unlink()
    replayed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "--build-manifest",
            str(manifest_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=build_dir,
    )
    replayed_payload = json.loads(replayed.stdout)
    assert replayed_payload["compiled"] is True
    assert Path(replayed_payload["shared_library"]).is_file()
    replayed_module = _sole_native_module(_import_from_build_dir(replayed_payload["module_name"], build_dir))
    _assert_scale_runtime_contract(replayed_module)


def test_all_direct_makefile_and_manifest_record_zero_generated_native_groups(tmp_path: Path):
    contract = tmp_path / "direct_manifest.pyi"
    contract.write_text(
        """from prik.contracts import Int32, native_abi

@native_abi("c")
def direct(value: Int32) -> Int32: ...
""",
        encoding="utf-8",
    )
    native_source = tmp_path / "direct_manifest.f90"
    native_source.write_text("native implementation placeholder\n", encoding="utf-8")

    result = build_pyi_extension(
        contract,
        native_fortran_sources=[native_source],
        output_dir=tmp_path / "build",
        makefile=True,
    )

    manifest = json.loads(result.build_manifest.read_text(encoding="utf-8"))
    generated = manifest["generated_wrapper"]
    makefile = result.build_makefile.read_text(encoding="utf-8")

    assert result.native_generated_code_groups == ()
    assert generated["native_code_groups"] == []
    assert {Path(path).suffix for path in generated["sources"]} == {".c", ".h"}
    assert "bind_c_direct_manifest_wrapper.f90" not in makefile
    assert "direct_manifest.f90" in makefile


def test_manifest_replay_preserves_language_for_named_and_raw_link_items(tmp_path: Path) -> None:
    contract = tmp_path / "api.pyi"
    contract.write_text(
        "from prik.contracts import Int32\ndef identity(value: Int32) -> Int32: ...\n", encoding="utf-8"
    )
    link_items = (
        {"kind": "named_library", "name": "runtime", "language": "fortran"},
        {"kind": "linker_argument", "argument": "-pthread", "language": "c"},
    )

    generated = build_pyi_extension(
        contract,
        native_link_items=link_items,
        output_dir=tmp_path / "generated",
        makefile=True,
    )
    replayed = build_pyi_extension_from_manifest(
        generated.build_manifest,
        generate_sources=True,
    )

    assert [item.to_dict() for item in replayed.native_build_plan.link_items] == [
        {"kind": "named_library", "name": "runtime", "language": "fortran"},
        {"kind": "linker_argument", "argument": "-pthread", "language": "c"},
    ]


def test_pyi_cli_accepts_exactly_one_entry_contract(tmp_path: Path):
    other = tmp_path / "other.pyi"
    other.write_text("", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(PYI_FIXTURE),
            str(other),
            "--native-objects",
            str(tmp_path / "unused.o"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "A .pyi wrapper build accepts exactly one entry contract" in result.stderr


def test_pyi_python_api_rejects_a_missing_native_artifact(tmp_path: Path):
    missing_object = tmp_path / "missing.o"

    with pytest.raises(FileNotFoundError, match=f"Native artifact not found: {missing_object}"):
        build_pyi_extension(PYI_FIXTURE, native_objects=[missing_object], output_dir=tmp_path / "build")


def test_pyi_python_api_rejects_python_suffix_as_semantic_contract(tmp_path: Path):
    contract = tmp_path / "modified_contract.py"
    contract.write_text("def scale(value: Float64) -> Float64: ...\n", encoding="utf-8")
    native_object = tmp_path / "native.o"
    native_object.touch()

    with pytest.raises(ValueError, match=r"\.pyi wrapper build expects one semantic contract file"):
        build_pyi_extension(contract, native_objects=[native_object], output_dir=tmp_path / "build")


def test_pyi_python_api_accepts_exactly_one_entry_contract(tmp_path: Path):
    with pytest.raises(TypeError, match="exactly one entry contract"):
        build_pyi_extension([PYI_FIXTURE], native_objects=[tmp_path / "unused.o"])


def test_generated_pyi_fixture_builds_from_native_object_without_source_reparse(tmp_path: Path):
    native_object = _compile_native_object(SOURCE, tmp_path / "native")
    module, payload = _build_pyi_cli(PYI_FIXTURE, native_object, tmp_path / "pyi_build")
    native_plan = payload["native_build_plan"]

    assert Path(payload["shared_library"]).is_file()
    assert payload["sources"] == [str(PYI_FIXTURE)]
    assert "native_inputs" not in payload
    assert native_plan["compilation_units"] == []
    assert native_plan["produced_objects"] == []
    assert native_plan["prebuilt_artifacts"] == [{"kind": "object", "path": str(native_object)}]
    assert native_plan["module_dirs"] == [str(native_object.parent)]
    assert native_plan["include_dirs"] == [str(native_object.parent)]
    assert native_plan["link_items"] == [{"kind": "object", "path": str(native_object)}]
    assert module.scale(np.float64(2.0), np.float64(4.0)) == np.float64(8.0)


def test_pyi_cli_preserves_explicit_ordered_link_items(tmp_path: Path):
    native_object = tmp_path / "native" / "fruntime_abi_f90.o"
    native_object.parent.mkdir()
    native_object.touch()
    build_dir = tmp_path / "pyi_build"
    build_dir.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--sources",
            str(PYI_FIXTURE),
            "--native-link-item",
            "arg:-Wl,--start-group",
            f"object:{native_object}",
            "arg:-Wl,--end-group",
            "--out-dir",
            str(build_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=build_dir,
    )
    payload = json.loads(result.stdout)
    native_plan = payload["native_build_plan"]

    assert payload["compiled"] is False
    assert all(Path(path).is_file() for path in payload["generated_sources"])
    assert not Path(payload["shared_library"]).exists()
    assert native_plan["link_items"] == [
        {"kind": "linker_argument", "argument": "-Wl,--start-group"},
        {"kind": "object", "path": str(native_object)},
        {"kind": "linker_argument", "argument": "-Wl,--end-group"},
    ]
    manifest_link_items = payload["manifest"]["native_build_plan"]["link_items"]
    assert manifest_link_items[0] == {"argument": "-Wl,--start-group", "kind": "linker_argument"}
    assert manifest_link_items[1]["kind"] == "object"
    assert manifest_link_items[1]["path"].endswith(native_object.name)
    assert manifest_link_items[2] == {"argument": "-Wl,--end-group", "kind": "linker_argument"}


def test_generated_pyi_matches_checked_in_fixture(tmp_path: Path):
    _generate_pyi(SOURCE, tmp_path / "contracts", RUNTIME_ABI_GENERATED)


def test_scale_runtime_contract(scale_runtime_module):
    _assert_scale_runtime_contract(scale_runtime_module)
