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

from x2py import build_pyi_extension
from x2py.semantics.native_array_handles import NativeArrayBuildRequirement, NativeArrayBuildRequirements
from x2py.pipeline.build import _manifest_native_array_requirements, build_fortran_extension
from tests._shared.pyi_fixture_packages import assert_generated_pyi_package_matches_fixture
from tests.wrapper.fortran._support import (
    REPO_ROOT,
    wrapper_source,
)

SOURCE = wrapper_source("fruntime_abi_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
MODIFIED_CONTRACT_FIXTURES = Path(__file__).parent / "modified_contracts"
INVALID_CONTRACT_FIXTURES = Path(__file__).parent / "invalid_contracts"
PYI_FIXTURE = CONTRACT_FIXTURES / "runtime_abi" / "fruntime_abi_f90.pyi"
RUNTIME_ABI_GENERATED = CONTRACT_FIXTURES / "runtime_abi"
MODULE_VARIABLES_GENERATED = CONTRACT_FIXTURES / "module_variables"
BASIC_SUBROUTINE_GENERATED = CONTRACT_FIXTURES / "basic_subroutine"
MIXED_API_GENERATED = CONTRACT_FIXTURES / "mixed_api"
MULTI_API_GENERATED = CONTRACT_FIXTURES / "multi_api"
INVALID_NATIVE_CALL_PYI = INVALID_CONTRACT_FIXTURES / "projection_metadata" / "incomplete_native_call.pyi"
MODIFIED_BASIC_CONTRACTS = MODIFIED_CONTRACT_FIXTURES / "basic_subroutine"
BASIC_SOURCE = REPO_ROOT / "tests" / "data" / "fortran" / "general" / "basic_subroutine.f90"
MODULE_VARIABLE_SOURCE = wrapper_source("fmodule_vars_f90.f90")
MIXED_SOURCE = """\
module m1
contains
subroutine add1(n, x)
  integer, intent(in) :: n
  real(kind=8), intent(inout), dimension(n) :: x
  x = x + 1.0d0
end subroutine add1
end module m1

subroutine func()
end subroutine func
"""
MULTI_MODULE_SOURCE = """\
module first_mod
contains
subroutine shared_call()
end subroutine shared_call
end module first_mod

module second_mod
contains
subroutine shared_call()
end subroutine shared_call
end module second_mod
"""


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
        "x2py",
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


def _generated_wrapper_text(payload: dict) -> str:
    paths = [Path(path) for path in payload["generated_sources"] if Path(path).suffix in {".c", ".f90", ".h"}]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def _generate_pyi(source: Path, output_parent: Path, expected_package: Path | None = None) -> Path:
    package = output_parent / source.stem
    subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
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


def _assert_module_variable_runtime_contract(module) -> None:
    assert module.counter == np.int32(3)
    module.counter = np.int32(9)
    assert module.counter == np.int32(9)
    assert module.summarize() == np.int32(21)
    assert not hasattr(module, "get_counter")
    assert not hasattr(module, "set_counter")


def _copy_modified_entry(generated_entry: Path, fixture_name: str) -> None:
    fixture = MODIFIED_BASIC_CONTRACTS / fixture_name
    text = fixture.read_text(encoding="utf-8")
    assert text.startswith("# Intentional difference:")
    generated_entry.write_text(text, encoding="utf-8")


@pytest.fixture
def scale_runtime_module(pyi_parity_build_mode: str, tmp_path: Path):
    if pyi_parity_build_mode == "source":
        result = build_fortran_extension(SOURCE, output_dir=tmp_path / "source_build")
        return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    generated_pyi = _generate_pyi(SOURCE, tmp_path / "contracts", RUNTIME_ABI_GENERATED)
    native_object = _compile_native_object(SOURCE, tmp_path / "native")
    module, _payload = _build_pyi_cli(generated_pyi, native_object, tmp_path / "pyi_build")
    return _sole_native_module(module)


@pytest.fixture
def module_variable_runtime_module(pyi_parity_build_mode: str, tmp_path: Path):
    if pyi_parity_build_mode == "source":
        result = build_fortran_extension(MODULE_VARIABLE_SOURCE, output_dir=tmp_path / "source_build")
        return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    generated_pyi = _generate_pyi(MODULE_VARIABLE_SOURCE, tmp_path / "contracts", MODULE_VARIABLES_GENERATED)
    native_object = _compile_native_object(MODULE_VARIABLE_SOURCE, tmp_path / "native")
    module, _payload = _build_pyi_cli(generated_pyi, native_object, tmp_path / "pyi_build")
    return _sole_native_module(module)


def test_pyi_cli_requires_a_native_link_input(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, "-m", "x2py", str(PYI_FIXTURE), "--out-dir", str(tmp_path)],
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
            "x2py",
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
    assert manifest_path == build_dir / "x2py-build.json"
    assert makefile_path == build_dir / "Makefile.x2py"
    assert manifest == payload["manifest"]
    assert manifest["schema_version"] == 2
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
    assert "x2py-build.json" in makefile_text
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
            "x2py",
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
            "x2py",
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


def test_pyi_cli_accepts_exactly_one_entry_contract(tmp_path: Path):
    other = tmp_path / "other.pyi"
    other.write_text("", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
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


def test_pyi_python_api_rejects_invalid_projection_before_codegen(tmp_path: Path):
    native_object = tmp_path / "native.o"
    native_object.touch()

    with pytest.raises(ValueError, match="native_call argument position is out of range"):
        build_pyi_extension(INVALID_NATIVE_CALL_PYI, native_objects=[native_object], output_dir=tmp_path / "build")

    assert not list((tmp_path / "build").glob("*_wrapper.*"))


@pytest.mark.parametrize(
    ("contract_text", "message"),
    [
        (
            "from x2py.contracts import Addr, Float64\n\n"
            "class particle:\n    value: Float64\n\n"
            "def invalid(value: Addr(particle)) -> None: ...\n",
            r"Addr\(WrappedType\) is not allowed",
        ),
        (
            "from x2py.contracts import Addr, Arg, Float64, native_call\n\n"
            "@native_call([Addr(Arg(0))])\n"
            "def invalid(values: Float64[:]) -> None: ...\n",
            "only valid for primitive scalar values",
        ),
        (
            "from x2py.contracts import Addr, Float64\n\ndef invalid(values: Addr(Float64[:])) -> None: ...\n",
            "raw arrays require a fully resolved rank and shape",
        ),
    ],
)
def test_pyi_python_api_rejects_invalid_address_contracts_before_codegen(
    tmp_path: Path,
    contract_text: str,
    message: str,
):
    contract = tmp_path / "invalid_address.pyi"
    contract.write_text(contract_text, encoding="utf-8")
    native_object = tmp_path / "native.o"
    native_object.touch()

    with pytest.raises(ValueError, match=message):
        build_pyi_extension(contract, native_objects=[native_object], output_dir=tmp_path / "build")

    assert not list((tmp_path / "build").glob("*_wrapper.*"))


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
    native_object = _compile_native_object(SOURCE, tmp_path / "native")
    build_dir = tmp_path / "pyi_build"
    build_dir.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
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
    module = _sole_native_module(_import_from_build_dir(payload["module_name"], build_dir))

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
    assert module.scale(np.float64(2.0), np.float64(4.0)) == np.float64(8.0)


def test_pyi_manifest_records_pointer_descriptor_interop_requirements():
    manifest_section = _manifest_native_array_requirements(
        NativeArrayBuildRequirements(
            pointer_c_descriptor_interop=True,
            headers=("ISO_Fortran_binding.h",),
            items=(
                NativeArrayBuildRequirement(
                    owner="api.inspect.target",
                    item="target",
                    descriptor_kind="pointer",
                    handle_kind="argument_descriptor",
                    descriptor_interop="pointer_c_descriptor",
                    headers=("ISO_Fortran_binding.h",),
                ),
            ),
        )
    )

    assert manifest_section == {
        "pointer_c_descriptor_interop": True,
        "headers": ["ISO_Fortran_binding.h"],
        "items": [
            {
                "owner": "api.inspect.target",
                "item": "target",
                "descriptor_kind": "pointer",
                "handle_kind": "argument_descriptor",
                "descriptor_interop": "pointer_c_descriptor",
                "headers": ["ISO_Fortran_binding.h"],
            }
        ],
    }


def test_generated_pyi_matches_checked_in_fixture(tmp_path: Path):
    _generate_pyi(SOURCE, tmp_path / "contracts", RUNTIME_ABI_GENERATED)


def test_source_named_root_discovers_and_builds_module_leaf(tmp_path: Path):
    root = _generate_pyi(BASIC_SOURCE, tmp_path / "contracts", BASIC_SUBROUTINE_GENERATED)
    leaf = root.parent / "m1.pyi"
    native_object = _compile_native_object(BASIC_SOURCE, tmp_path / "native")

    module, payload = _build_pyi_cli(root, native_object, tmp_path / "pyi_build")

    assert root.read_text(encoding="utf-8") == "from . import m1\n"
    assert leaf.is_file()
    assert payload["module_name"] == "basic_subroutine"
    assert payload["sources"] == [str(root), str(leaf)]
    assert not hasattr(module, "add1")
    values = np.array([1.0, 2.0], dtype=np.float64)
    module.m1.add1(np.int32(values.size), values)
    np.testing.assert_array_equal(values, np.array([1.0, 2.0], dtype=np.float64))


def test_entry_wildcard_import_explicitly_flattens_module_leaf(tmp_path: Path):
    root = _generate_pyi(BASIC_SOURCE, tmp_path / "contracts", BASIC_SUBROUTINE_GENERATED)
    _copy_modified_entry(root, "flatten_m1.pyi")
    native_object = _compile_native_object(BASIC_SOURCE, tmp_path / "native")

    module, _payload = _build_pyi_cli(root, native_object, tmp_path / "pyi_build")

    assert not hasattr(module, "m1")
    values = np.array([1.0, 2.0], dtype=np.float64)
    module.add1(np.int32(values.size), values)
    np.testing.assert_array_equal(values, np.array([1.0, 2.0], dtype=np.float64))


def test_entry_can_alias_one_module_procedure_at_the_root(tmp_path: Path):
    root = _generate_pyi(BASIC_SOURCE, tmp_path / "contracts", BASIC_SUBROUTINE_GENERATED)
    _copy_modified_entry(root, "alias_increment.pyi")
    native_object = _compile_native_object(BASIC_SOURCE, tmp_path / "native")

    module, _payload = _build_pyi_cli(root, native_object, tmp_path / "pyi_build")

    assert not hasattr(module, "m1")
    assert not hasattr(module, "add1")
    values = np.array([1.0, 2.0], dtype=np.float64)
    module.increment(np.int32(values.size), values)
    np.testing.assert_array_equal(values, np.array([1.0, 2.0], dtype=np.float64))


def test_reduced_entry_generates_only_reachable_module_variable_bindings(tmp_path: Path):
    root = _generate_pyi(MODULE_VARIABLE_SOURCE, tmp_path / "contracts", MODULE_VARIABLES_GENERATED)
    root.write_text(
        "\n".join(
            [
                "from .fmodule_vars_f90 import counter",
                "from .fmodule_vars_f90 import counter",
                "from .fmodule_vars_f90 import counter as current_count",
                "from .fmodule_vars_f90 import summarize",
                "",
            ]
        ),
        encoding="utf-8",
    )
    native_object = _compile_native_object(MODULE_VARIABLE_SOURCE, tmp_path / "native")

    module, payload = _build_pyi_cli(root, native_object, tmp_path / "pyi_build")

    assert module.counter == np.int32(3)
    assert module.current_count == np.int32(3)
    assert module.summarize() == np.int32(15)
    module.current_count = np.int32(9)
    assert module.counter == np.int32(9)
    assert module.summarize() == np.int32(21)
    assert not hasattr(module, "scale")
    assert not hasattr(module, "scaled_counter")
    assert not hasattr(module, "saved_counter")
    assert not hasattr(module, "next_local")

    generated_text = _generated_wrapper_text(payload)
    assert "bind_c_get_counter" in generated_text
    assert "bind_c_set_counter" in generated_text
    assert "scaled_counter" not in generated_text
    assert "next_local" not in generated_text
    assert "saved_counter" not in generated_text
    assert "bind_c_get_scale" not in generated_text
    assert "bind_c_set_scale" not in generated_text


def test_mutable_module_variable_default_initializes_native_storage(tmp_path: Path):
    root = _generate_pyi(MODULE_VARIABLE_SOURCE, tmp_path / "contracts", MODULE_VARIABLES_GENERATED)
    leaf = root.parent / "fmodule_vars_f90.pyi"
    leaf.write_text(
        leaf.read_text(encoding="utf-8")
        .replace("counter: Int32", "counter: Int32 = 41")
        .replace("scale: Float64", "scale: Float64 = 2.5"),
        encoding="utf-8",
    )
    root.write_text(
        "\n".join(
            [
                "from .fmodule_vars_f90 import counter",
                "from .fmodule_vars_f90 import scale",
                "from .fmodule_vars_f90 import summarize",
                "",
            ]
        ),
        encoding="utf-8",
    )
    native_object = _compile_native_object(MODULE_VARIABLE_SOURCE, tmp_path / "native")

    module, _payload = _build_pyi_cli(root, native_object, tmp_path / "pyi_build")

    assert module.counter == np.int32(41)
    assert module.scale == np.float64(2.5)
    assert module.summarize() == np.int32(53)
    module.counter = np.int32(5)
    module.scale = np.float64(1.25)
    assert module.summarize() == np.int32(17)
    assert module.scale == np.float64(1.25)


def test_entry_rejects_colliding_wildcard_exports(tmp_path: Path):
    entry = tmp_path / "api.pyi"
    first = tmp_path / "first.pyi"
    second = tmp_path / "second.pyi"
    entry.write_text("from .first import *\nfrom .second import *\n", encoding="utf-8")
    declaration = "from x2py.contracts import Int32\n\ndef update(value: Int32) -> Int32: ...\n"
    first.write_text(declaration, encoding="utf-8")
    second.write_text(declaration, encoding="utf-8")

    with pytest.raises(ValueError, match=r"Conflicting \.pyi exports for 'update'"):
        build_pyi_extension(entry, native_objects=[tmp_path / "unused.o"])


def test_module_leaf_can_be_the_entry_contract(tmp_path: Path):
    root = _generate_pyi(BASIC_SOURCE, tmp_path / "contracts", BASIC_SUBROUTINE_GENERATED)
    leaf = root.parent / "m1.pyi"
    native_object = _compile_native_object(BASIC_SOURCE, tmp_path / "native")

    module, payload = _build_pyi_cli(leaf, native_object, tmp_path / "pyi_build")

    assert payload["module_name"] == "m1"
    assert payload["sources"] == [str(leaf)]
    assert not hasattr(module, "m1")
    values = np.array([1.0, 2.0], dtype=np.float64)
    module.add1(np.int32(values.size), values)


def test_mixed_entry_exposes_externals_at_root_and_modules_as_children(tmp_path: Path):
    source = tmp_path / "mixed_api.f90"
    source.write_text(MIXED_SOURCE, encoding="utf-8")
    entry = _generate_pyi(source, tmp_path / "contracts", MIXED_API_GENERATED)
    native_object = _compile_native_object(source, tmp_path / "native")

    module, payload = _build_pyi_cli(entry, native_object, tmp_path / "pyi_build")

    contract = entry.read_text(encoding="utf-8")
    assert "from . import m1" in contract
    assert "@external\ndef func() -> None: ..." in contract
    assert payload["sources"] == [str(entry), str(entry.parent / "m1.pyi")]
    assert module.func() is None
    values = np.array([1.0, 2.0], dtype=np.float64)
    module.m1.add1(np.int32(values.size), values)
    np.testing.assert_array_equal(values, np.array([2.0, 3.0], dtype=np.float64))


def test_one_entry_preserves_multiple_native_module_namespaces(tmp_path: Path):
    source = tmp_path / "multi_api.f90"
    source.write_text(MULTI_MODULE_SOURCE, encoding="utf-8")
    entry = _generate_pyi(source, tmp_path / "contracts", MULTI_API_GENERATED)
    native_object = _compile_native_object(source, tmp_path / "native")

    module, payload = _build_pyi_cli(entry, native_object, tmp_path / "pyi_build")

    assert entry.read_text(encoding="utf-8") == "from . import first_mod\nfrom . import second_mod\n"
    assert payload["sources"] == [
        str(entry),
        str(entry.parent / "first_mod.pyi"),
        str(entry.parent / "second_mod.pyi"),
    ]
    assert not hasattr(module, "shared_call")
    assert module.first_mod.shared_call() is None
    assert module.second_mod.shared_call() is None


def test_scale_runtime_contract(scale_runtime_module):
    _assert_scale_runtime_contract(scale_runtime_module)


def test_module_variable_runtime_contract(module_variable_runtime_module):
    _assert_module_variable_runtime_contract(module_variable_runtime_module)
