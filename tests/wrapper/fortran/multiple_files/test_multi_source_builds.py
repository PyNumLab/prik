"""Builds that wrap several related Fortran source files together."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from x2py import build_pyi_extension

from tests._shared.pyi_fixture_packages import assert_generated_pyi_package_matches_fixture
from tests.wrapper.fortran._support import (
    _build_sources_and_import,
    wrapper_source,
)


CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
COMBINED_MODULES_GENERATED = CONTRACT_FIXTURES / "combined_modules"
FIRST_API_SOURCE = wrapper_source("first_api.f90")
SECOND_API_SOURCE = wrapper_source("second_api.f90")
STANDALONE_API_SOURCE = wrapper_source("standalone_api.f")
DOUBLE_VALUE_SOURCE = wrapper_source("double_value.f")
FIRST_COMBINED_SOURCE = """\
module first_math
contains
integer function add_one(value) result(out)
  integer, intent(in) :: value
  out = value + 1
end function add_one
end module first_math

module shared_types
  type :: box
    integer :: value
  end type box
contains
function make_box(value) result(out)
  integer, intent(in) :: value
  type(box) :: out
  out%value = value
end function make_box
end module shared_types
"""
SECOND_COMBINED_SOURCE = """\
module second_math
  use first_math, only: add_one
contains
integer function double_after_add(value) result(out)
  integer, intent(in) :: value
  out = 2 * add_one(value)
end function double_after_add
end module second_math

module box_ops
  use shared_types, only: box
contains
integer function box_value(item) result(out)
  type(box), intent(in) :: item
  out = item%value
end function box_value
end module box_ops
"""


def _source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compiler() -> str:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("gfortran is required for generated-contract multi-source tests")
    return compiler


def _write_combined_sources(workdir: Path) -> tuple[Path, Path]:
    first = workdir / "first_api.f90"
    second = workdir / "second_api.f90"
    first.write_text(FIRST_COMBINED_SOURCE, encoding="utf-8")
    second.write_text(SECOND_COMBINED_SOURCE, encoding="utf-8")
    return first, second


def _generate_combined_contract(sources: tuple[Path, ...], package_dir: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "generate",
            "--pyi",
            *(str(source) for source in sources),
            "--out",
            str(package_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert_generated_pyi_package_matches_fixture(package_dir, COMBINED_MODULES_GENERATED)
    return package_dir / "__init__.pyi"


def _compile_native_objects(sources: tuple[Path, ...], native_dir: Path) -> tuple[Path, ...]:
    native_dir.mkdir(parents=True, exist_ok=True)
    objects = []
    for source in sources:
        native_object = native_dir / f"{source.stem}.o"
        subprocess.run(
            [
                _compiler(),
                "-fPIC",
                "-c",
                str(source),
                "-o",
                str(native_object),
                "-J",
                str(native_dir),
                "-I",
                str(native_dir),
            ],
            check=True,
        )
        objects.append(native_object)
    return tuple(objects)


def _import_extension(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


def _build_sources(sources: tuple[Path, ...], build_dir: Path) -> tuple[object, dict[str, object]]:
    build_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            *(str(source) for source in sources),
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
    return _import_extension(str(payload["module_name"]), build_dir), payload


def _build_contract(
    entry: Path,
    native_objects: tuple[Path, ...],
    build_dir: Path,
    *,
    output_name: str,
):
    result = build_pyi_extension(
        entry,
        native_objects=native_objects,
        native_include_dirs=[native_objects[0].parent],
        output_name=output_name,
        output_dir=build_dir,
    )
    return _import_extension(result.module_name, build_dir), result.to_dict()


def _assert_combined_runtime(module) -> None:
    assert module.first_math.add_one(np.int32(4)) == np.int32(5)
    assert module.second_math.double_after_add(np.int32(4)) == np.int32(10)
    box = module.shared_types.make_box(np.int32(7))
    assert module.box_ops.box_value(box) == np.int32(7)


def test_multi_file_modules_build_one_merged_extension(tmp_path: Path):
    module, payload = _build_sources_and_import(
        [
            ("first_api.f90", _source_text(FIRST_API_SOURCE)),
            ("second_api.f90", _source_text(SECOND_API_SOURCE)),
        ],
        tmp_path,
    )

    assert payload["module_name"] == "first_api"
    assert module.first_api.add_one(np.int32(4)) == 5
    assert module.second_api.double_value(np.int32(4)) == 10
    assert module.second_api.counter == 3
    module.second_api.counter = np.int32(7)
    assert module.second_api.counter == 7
    assert not hasattr(module.second_api, "get_counter")
    assert not hasattr(module.second_api, "set_counter")
    bridge = (tmp_path / "bind_c_first_api_wrapper.f90").read_text(encoding="utf-8").lower()
    assert "use first_api" in bridge
    assert "use second_api" in bridge


def test_generated_child_modules_are_importable_submodules(tmp_path: Path):
    _module, payload = _build_sources_and_import(
        [
            ("first_api.f90", _source_text(FIRST_API_SOURCE)),
            ("second_api.f90", _source_text(SECOND_API_SOURCE)),
        ],
        tmp_path,
    )

    module_name = str(payload["module_name"])
    for name in (module_name, f"{module_name}.first_api", f"{module_name}.second_api"):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(tmp_path))
    try:
        from first_api.first_api import add_one
        from first_api.second_api import double_value

        root = importlib.import_module("first_api")
        assert sys.modules["first_api.first_api"] is root.first_api
        assert sys.modules["first_api.second_api"] is root.second_api
        assert add_one(np.int32(4)) == 5
        assert double_value(np.int32(4)) == 10
    finally:
        sys.path.remove(str(tmp_path))
        for name in (f"{module_name}.second_api", f"{module_name}.first_api", module_name):
            sys.modules.pop(name, None)


def test_multi_file_standalone_procedures_build_one_merged_extension(tmp_path: Path):
    module, payload = _build_sources_and_import(
        [
            ("standalone_api.f", _source_text(STANDALONE_API_SOURCE)),
            ("double_value.f", _source_text(DOUBLE_VALUE_SOURCE)),
        ],
        tmp_path,
    )

    assert payload["module_name"] == "standalone_api"
    assert module.add_one(np.int32(4)) == 5
    assert module.double_value(np.int32(4)) == 8


def test_multi_source_pyi_out_writes_one_flat_combined_package(tmp_path: Path):
    sources = _write_combined_sources(tmp_path)
    package = tmp_path / "contracts"
    entry = _generate_combined_contract(sources, package)

    assert entry == package / "__init__.pyi"
    assert sorted(path.relative_to(package).as_posix() for path in package.rglob("*.pyi")) == [
        "__init__.pyi",
        "box_ops.pyi",
        "first_math.pyi",
        "second_math.pyi",
        "shared_types.pyi",
    ]
    assert not (package / "first_api").exists()
    assert not (package / "second_api").exists()
    assert not (package / "combined_extensions").exists()
    assert entry.read_text(encoding="utf-8") == (
        "from . import first_math\nfrom . import shared_types\nfrom . import second_math\nfrom . import box_ops\n"
    )
    assert "shared_types" in (package / "box_ops.pyi").read_text(encoding="utf-8")


def test_multi_source_generated_contract_build_matches_source_runtime_and_link_order(tmp_path: Path):
    sources = _write_combined_sources(tmp_path)
    source_module, source_payload = _build_sources(sources, tmp_path / "source_build")
    entry = _generate_combined_contract(sources, tmp_path / "contracts")
    native_objects = _compile_native_objects(sources, tmp_path / "native")
    generated_module, generated_payload = _build_contract(
        entry,
        native_objects,
        tmp_path / "generated_build",
        output_name=str(source_payload["module_name"]),
    )

    assert source_payload["module_name"] == "first_api"
    assert generated_payload["module_name"] == source_payload["module_name"]
    assert generated_payload["sources"] == [
        str(entry),
        str(entry.parent / "box_ops.pyi"),
        str(entry.parent / "first_math.pyi"),
        str(entry.parent / "second_math.pyi"),
        str(entry.parent / "shared_types.pyi"),
    ]
    assert [item["path"] for item in source_payload["native_build_plan"]["link_items"]] == [
        str(Path(source_payload["output_dir"]) / f"{source.stem}.o") for source in sources
    ]
    assert generated_payload["native_build_plan"]["link_items"] == [
        {"kind": "object", "path": str(native_objects[0])},
        {"kind": "object", "path": str(native_objects[1])},
    ]
    _assert_combined_runtime(source_module)
    _assert_combined_runtime(generated_module)


def test_multi_source_modified_entry_preserves_modules_and_adds_documented_alias(tmp_path: Path):
    sources = _write_combined_sources(tmp_path)
    source_module, source_payload = _build_sources(sources, tmp_path / "source_build")
    generated_entry = _generate_combined_contract(sources, tmp_path / "contracts")
    native_objects = _compile_native_objects(sources, tmp_path / "native")
    modified_package = tmp_path / "modified_contracts"
    shutil.copytree(generated_entry.parent, modified_package)
    modified_entry = modified_package / "__init__.pyi"
    modified_entry.write_text(
        "# Intentional difference: preserve native module children and add a root alias.\n"
        "from . import first_math\n"
        "from . import shared_types\n"
        "from . import second_math\n"
        "from . import box_ops\n"
        "from .second_math import double_after_add as fused_value\n",
        encoding="utf-8",
    )

    modified_module, modified_payload = _build_contract(
        modified_entry,
        native_objects,
        tmp_path / "modified_build",
        output_name=str(source_payload["module_name"]),
    )

    assert modified_payload["module_name"] == source_payload["module_name"]
    assert not hasattr(source_module, "fused_value")
    assert modified_module.fused_value(np.int32(4)) == np.int32(10)
    _assert_combined_runtime(modified_module)


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("make") is None,
    reason="generated Makefile requires GNU Make and a POSIX shell",
)
def test_makefile_mode_reproduces_multi_source_build(tmp_path: Path):
    first = tmp_path / "first_api.f90"
    second = tmp_path / "second_api.f90"
    shutil.copyfile(FIRST_API_SOURCE, first)
    shutil.copyfile(SECOND_API_SOURCE, second)

    command = [
        sys.executable,
        "-m",
        "x2py",
        "generate",
        "--makefile",
        str(first),
        str(second),
        "--out-dir",
        str(tmp_path),
        "--json",
    ]
    generated = subprocess.run(command, capture_output=True, text=True, check=True)
    payload = json.loads(generated.stdout)
    makefile = Path(payload["build_makefile"])

    assert payload["compiled"] is False
    assert makefile.is_file()
    assert not Path(payload["shared_library"]).exists()
    text = makefile.read_text(encoding="utf-8")
    assert "FC := " in text
    assert "CC := " in text
    assert "X2PY_FFLAGS ?=" in text
    assert f"{tmp_path / 'second_api.o'}: {second} {tmp_path / 'first_api.o'}" in text
    assert f"{tmp_path / 'bind_c_first_api_wrapper.o'}:" in text
    assert str(tmp_path / "first_api.o") in text
    assert str(tmp_path / "second_api.o") in text

    built = subprocess.run(
        [
            "make",
            "-j4",
            "-f",
            str(makefile),
            "all",
            "X2PY_FFLAGS=-O3",
            "X2PY_CFLAGS=-O3",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "-O3" in built.stdout
    assert Path(payload["shared_library"]).is_file()

    sys.modules.pop("first_api", None)
    sys.path.insert(0, str(tmp_path))
    try:
        module = importlib.import_module("first_api")
        assert module.second_api.double_value(np.int32(4)) == 10
    finally:
        sys.path.remove(str(tmp_path))
