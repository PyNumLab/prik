"""Verbose direct-build and default output-location tests."""

import importlib
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _sole_native_module
from prik.pipeline.preprocessing import PreprocessingConfig
from prik.pipeline.build import NativeBuildPlan, NativeLinkItem, build_fortran_extension

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"
VERBOSE_SOURCE = NATIVE_FIXTURES / "verbose_api.f90"
DEFAULT_OUTPUT_SOURCE = NATIVE_FIXTURES / "fdefault_output.f"
SCALE_SOURCE = NATIVE_FIXTURES / "scale.f90"
SCALAR_SOURCE = SCALE_SOURCE
HOME_POINTS_SOURCE = NATIVE_FIXTURES / "home_points.f90"
BUILD_MODULE = Path(__file__).resolve().parents[4] / "prik" / "pipeline" / "build.py"
pytestmark = pytest.mark.fortran_end_to_end


def test_build_module_direct_execution_runs_the_public_api_example():
    result = subprocess.run(
        [sys.executable, str(BUILD_MODULE)],
        capture_output=True,
        text=True,
        check=True,
        cwd=BUILD_MODULE.parents[2],
    )

    assert result.stdout == "scale(3.0, 2.5) = 7.5\n"


def test_verbose_mode_prints_full_direct_build_commands(tmp_path: Path):
    source = tmp_path / "verbose_api.f90"
    shutil.copyfile(VERBOSE_SOURCE, source)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(source),
            "--verbose",
            "--out-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    command_lines = result.stdout.splitlines()

    assert any(str(source) in line and "-c" in line for line in command_lines)
    assert any("bind_c_verbose_api_wrapper.f90" in line and "-c" in line for line in command_lines)
    assert any("verbose_api_wrapper.c" in line and "-c" in line for line in command_lines)
    c_wrapper_command = next(line for line in command_lines if "verbose_api_wrapper.c" in line and "-c" in line)
    c_wrapper_parts = shlex.split(c_wrapper_command)
    assert "-O3" in c_wrapper_parts
    assert "-DNDEBUG" in c_wrapper_parts
    assert "-g" not in c_wrapper_parts
    link_command = next(line for line in command_lines if "-shared" in line and "verbose_api" in line)
    link_parts = shlex.split(link_command)
    link_output = link_parts[link_parts.index("-o") + 1]
    step_lines = [
        line.removeprefix(">> ")
        for line in command_lines
        if line.startswith(">> ") and not line.startswith((">> Timing", ">> Total build time"))
    ]
    bridge_source = tmp_path / "bind_c_verbose_api_wrapper.f90"
    binding_source = tmp_path / "verbose_api_wrapper.c"
    header = tmp_path / "verbose_api_wrapper.h"
    native_object = tmp_path / "verbose_api.o"
    bridge_object = tmp_path / "bind_c_verbose_api_wrapper.o"
    binding_object = tmp_path / "verbose_api_wrapper.o"
    assert step_lines[:4] == [
        "Complete wrapper policies",
        "Generate binding source",
        "Generate bridge source",
        "Generate binding header",
    ]
    binding_generation = command_lines.index(">> Generate binding source")
    bridge_generation = command_lines.index(">> Generate bridge source")
    header_generation = command_lines.index(">> Generate binding header")
    assert bridge_generation == binding_generation + 2
    assert header_generation == bridge_generation + 2
    assert command_lines[binding_generation + 1].startswith(">> Timing: ")
    assert command_lines[bridge_generation + 1].startswith(">> Timing: ")
    assert command_lines[header_generation + 1].startswith(">> Timing: ")
    assert f"Compile native source: {source} -> {native_object}" in step_lines
    assert f"Write bridge source: {bridge_source}" in step_lines
    assert f"Write binding source: {binding_source}" in step_lines
    assert f"Write binding header: {header}" in step_lines
    assert f"Compile bridge source: {bridge_source} -> {bridge_object}" in step_lines
    assert f"Compile binding source: {binding_source} -> {binding_object}" in step_lines
    assert f"Create shared library: {link_output}" in step_lines
    assert any(line.startswith(">> Timing: ") for line in command_lines)
    assert command_lines[-1].startswith(">> Total build time: ")
    assert "Built extension:" in result.stdout


def test_verbose_mode_prints_custom_wrapper_flags(tmp_path: Path):
    source = tmp_path / SCALE_SOURCE.name
    shutil.copyfile(SCALE_SOURCE, source)
    include_dir = tmp_path / "include"
    include_dir.mkdir()
    selected_compiler = tmp_path / "selected-gfortran"
    selected_compiler.symlink_to(shutil.which("gfortran"))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(source),
            "--out",
            "SCALE_debug",
            "--out-dir",
            str(tmp_path / "build" / "SCALE_debug"),
            "--verbose",
            "--compiler",
            str(selected_compiler),
            "-I",
            str(include_dir),
            "--native-compile-flags=-O1",
            "--wrapper-fortran-flags=-O2",
            "--wrapper-c-flags=-O2",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    command_lines = result.stdout.splitlines()

    native_command = next(line for line in command_lines if str(source) in line and "-c" in line)
    fortran_wrapper_command = next(
        line for line in command_lines if "bind_c_SCALE_debug_wrapper.f90" in line and "-c" in line
    )
    c_wrapper_command = next(line for line in command_lines if "SCALE_debug_wrapper.c" in line and "-c" in line)
    link_command = next(line for line in command_lines if "-shared" in line and "SCALE_debug" in line)
    assert "-O1" in shlex.split(native_command)
    assert "-O2" not in shlex.split(native_command)
    assert "-O2" in shlex.split(fortran_wrapper_command)
    assert "-O2" in shlex.split(c_wrapper_command)
    assert "-O2" in shlex.split(link_command)
    assert shlex.split(native_command)[0] == str(selected_compiler)
    assert shlex.split(fortran_wrapper_command)[0] == str(selected_compiler)
    assert shlex.split(link_command)[0] == str(selected_compiler)
    for command in (native_command, fortran_wrapper_command, c_wrapper_command):
        tokens = shlex.split(command)
        include_values = tuple(tokens[index + 1] for index, token in enumerate(tokens) if token == "-I")
        assert str(include_dir) in include_values


def test_fortran_wrapper_default_places_artifacts_in_invocation_directory(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    source = source_dir / DEFAULT_OUTPUT_SOURCE.name
    shutil.copyfile(DEFAULT_OUTPUT_SOURCE, source)

    cmd = [sys.executable, "-m", "prik", str(source), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=run_dir)
    payload = json.loads(result.stdout)

    build_dir = run_dir / "__prik__"
    shared_library = Path(payload["shared_library"])
    assert shared_library.parent == run_dir
    assert shared_library.name == "fdefault_output.so"
    assert shared_library.exists()
    assert Path(payload["output_dir"]) == build_dir
    assert (build_dir / "bind_c_fdefault_output_wrapper.f90").exists()
    assert len(tuple(build_dir.glob("fdefault_output.*.so"))) == 1
    assert not list(source_dir.glob("*_wrapper.c"))


def test_fortran_wrapper_out_dir_separates_abi_artifact_from_cli_alias(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    source = source_dir / DEFAULT_OUTPUT_SOURCE.name
    shutil.copyfile(DEFAULT_OUTPUT_SOURCE, source)

    result = subprocess.run(
        [sys.executable, "-m", "prik", str(source), "--out-dir", "build", "--json"],
        capture_output=True,
        text=True,
        check=True,
        cwd=run_dir,
    )
    payload = json.loads(result.stdout)

    build_dir = run_dir / "build"
    assert Path(payload["shared_library"]) == run_dir / "fdefault_output.so"
    assert (run_dir / "fdefault_output.so").is_file()
    assert len(tuple(build_dir.glob("fdefault_output.*.so"))) == 1
    assert not (build_dir / "fdefault_output.so").exists()


def test_fortran_wrapper_default_module_name_does_not_collide_with_root_function(tmp_path: Path):
    source = tmp_path / SCALE_SOURCE.name
    shutil.copyfile(SCALE_SOURCE, source)

    result = subprocess.run(
        [sys.executable, "-m", "prik", str(source), "--json"],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    payload = json.loads(result.stdout)

    shared_library = Path(payload["shared_library"])
    assert payload["module_name"] == "scale"
    assert shared_library.parent == tmp_path
    assert shared_library.name == "scale.so"
    assert shared_library.exists()

    sys.modules.pop("scale", None)
    sys.path.insert(0, str(tmp_path))
    try:
        module = importlib.import_module("scale")
    finally:
        sys.path.remove(str(tmp_path))
    assert module.scale(np.float64(3.0), np.float64(2.5)) == np.float64(7.5)


def test_fortran_wrapper_out_names_importable_shared_library(tmp_path: Path):
    source = tmp_path / SCALE_SOURCE.name
    output_name = tmp_path / "SCALE"
    shutil.copyfile(SCALE_SOURCE, source)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(source),
            "--out",
            str(output_name),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    payload = json.loads(result.stdout)

    shared_library = Path(payload["shared_library"])
    assert shared_library == output_name.with_suffix(".so")
    assert shared_library.is_file()
    assert payload["module_name"] == "SCALE"
    assert any(path.name.startswith("SCALE.") and path.suffix == ".so" for path in (tmp_path / "__prik__").iterdir())
    assert str(shared_library) in payload["generated_files"]

    sys.modules.pop("SCALE", None)
    sys.path.insert(0, str(tmp_path))
    try:
        module = importlib.import_module("SCALE")
    finally:
        sys.path.remove(str(tmp_path))
    assert module.scale(np.float64(3.0), np.float64(2.5)) == np.float64(7.5)


def test_documented_readme_points_example_builds_and_imports(tmp_path: Path):
    source = tmp_path / "points.f90"
    build_dir = tmp_path / "build" / "geometry"
    shutil.copyfile(HOME_POINTS_SOURCE, source)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(source),
            "--out",
            "geometry",
            "--out-dir",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert (tmp_path / "geometry.so").is_file()
    assert len(tuple(build_dir.glob("geometry.*.so"))) == 1

    sys.modules.pop("geometry.points", None)
    sys.modules.pop("geometry", None)
    sys.path.insert(0, str(tmp_path))
    try:
        geometry = importlib.import_module("geometry")
        points = geometry.points
        item = points.point(x=np.float64(3.0), y=np.float64(4.0))
        points.move(item, np.float64(1.0), np.float64(-2.0))
        assert item.x == np.float64(4.0)
        assert item.y == np.float64(2.0)
        assert points.norm_squared(item) == np.float64(20.0)
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("geometry.points", None)
        sys.modules.pop("geometry", None)


def test_internal_preprocessing_mode_still_builds_importable_runtime_wrapper(tmp_path: Path):
    source = tmp_path / SCALAR_SOURCE.name
    build_dir = tmp_path / "build"
    shutil.copyfile(SCALAR_SOURCE, source)

    result = build_fortran_extension(
        source,
        output_dir=build_dir,
        preprocessing=PreprocessingConfig(),
    )

    assert result.compiled is True
    assert result.build_makefile is None
    assert any(
        path.name == "prik_binding.h" and path.parent.name == "binding_support" for path in result.generated_files
    )
    support_license = build_dir / "binding_support" / "LICENSE"
    assert support_license in result.generated_files
    assert "Copyright (c) 2026 Said Hadjout" in support_license.read_text(encoding="utf-8")

    sys.modules.pop(result.module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        module = _sole_native_module(importlib.import_module(result.module_name))
    finally:
        sys.path.remove(str(build_dir))
    assert module.scale(np.float64(3.0), np.float64(2.5)) == np.float64(7.5)


def test_source_build_result_records_structured_native_plan(tmp_path: Path):
    source = tmp_path / SCALAR_SOURCE.name
    shutil.copyfile(SCALAR_SOURCE, source)

    result = build_fortran_extension(source, output_dir=tmp_path)

    plan = result.native_build_plan
    object_path = tmp_path / "scale.o"
    assert isinstance(plan, NativeBuildPlan)
    assert result.to_dict()["native_build_plan"] == plan.to_dict()
    assert plan.compilation_units[0].source == source
    assert plan.compilation_units[0].object_path == object_path
    assert plan.compilation_units[0].language == "fortran"
    assert plan.produced_objects == (object_path,)
    assert plan.prebuilt_artifacts == ()
    assert plan.module_dirs == (tmp_path,)
    assert plan.include_dirs == (tmp_path,)
    assert plan.link_items == (NativeLinkItem("object", object_path),)
    assert "native_inputs" not in result.to_dict()


def test_source_build_reuses_native_plan_for_additional_compile_and_link_inputs(tmp_path: Path):
    source = tmp_path / SCALAR_SOURCE.name
    support = tmp_path / "support.f90"
    output_dir = tmp_path / "generated"
    include_dir = tmp_path / "include"
    library_dir = tmp_path / "lib"
    object_path = tmp_path / "support.o"
    shutil.copyfile(SCALAR_SOURCE, source)
    shutil.copyfile(VERBOSE_SOURCE, support)
    include_dir.mkdir()
    library_dir.mkdir()
    object_path.write_bytes(b"source-only native link fixture")

    result = build_fortran_extension(
        source,
        output_dir=output_dir,
        native_fortran_sources=[support],
        native_fortran_flags=["-O1", "-g0"],
        native_objects=[object_path],
        native_libraries=["solver"],
        native_link_items=[{"kind": "linker_argument", "argument": "-Wl,--as-needed"}],
        native_library_dirs=[library_dir],
        native_include_dirs=[include_dir],
        generate_sources=True,
    )

    plan = result.native_build_plan
    assert result.compiled is False
    assert [unit.source for unit in plan.compilation_units] == [source, support]
    assert all(unit.flags == ("-O1", "-g0") for unit in plan.compilation_units)
    assert plan.prebuilt_artifacts[0].path == object_path
    assert include_dir in plan.include_dirs
    assert plan.library_dirs == (library_dir,)
    assert plan.link_items[-3:] == (
        NativeLinkItem("object", object_path),
        NativeLinkItem("linker_argument", "-Wl,--as-needed"),
        NativeLinkItem("named_library", "solver"),
    )


def test_source_directory_can_plan_a_wrapper_without_compiling_input_sources(tmp_path: Path):
    source_dir = tmp_path / "native"
    nested_dir = source_dir / "nested"
    output_dir = tmp_path / "generated"
    native_library = tmp_path / "libnative.so"
    source_dir.mkdir()
    nested_dir.mkdir()
    shutil.copyfile(VERBOSE_SOURCE, source_dir / VERBOSE_SOURCE.name)
    shutil.copyfile(SCALE_SOURCE, nested_dir / SCALE_SOURCE.name)
    native_library.write_bytes(b"prebuilt native library fixture")

    result = build_fortran_extension(
        source_dir,
        output_name="prebuilt_sources",
        output_dir=output_dir,
        compile_input_sources=False,
        native_objects=[native_library],
        generate_sources=True,
    )

    plan = result.native_build_plan
    assert result.sources == (nested_dir / SCALE_SOURCE.name, source_dir / VERBOSE_SOURCE.name)
    assert plan.compilation_units == ()
    assert plan.produced_objects == ()
    assert [artifact.path for artifact in plan.prebuilt_artifacts] == [native_library]
    assert plan.module_dirs == ()
    assert plan.link_items == (NativeLinkItem("shared_library", native_library),)


def test_source_build_still_compiles_explicit_hidden_sources_when_input_compilation_is_disabled(tmp_path: Path):
    source = tmp_path / SCALAR_SOURCE.name
    support = tmp_path / VERBOSE_SOURCE.name
    native_library = tmp_path / "libnative.so"
    shutil.copyfile(SCALAR_SOURCE, source)
    shutil.copyfile(VERBOSE_SOURCE, support)
    native_library.write_bytes(b"prebuilt native library fixture")

    result = build_fortran_extension(
        source,
        output_dir=tmp_path / "generated",
        compile_input_sources=False,
        native_fortran_sources=[support],
        native_objects=[native_library],
        generate_sources=True,
    )

    plan = result.native_build_plan
    assert [unit.source for unit in plan.compilation_units] == [support]
    assert source not in [unit.source for unit in plan.compilation_units]


def test_cli_builds_from_a_source_directory_and_prebuilt_object_only(tmp_path: Path):
    source_dir = tmp_path / "native"
    native_dir = tmp_path / "prebuilt"
    output_dir = tmp_path / "wrapper"
    source_dir.mkdir()
    native_dir.mkdir()
    source = source_dir / SCALE_SOURCE.name
    native_object = native_dir / "scale.o"
    shutil.copyfile(SCALE_SOURCE, source)
    subprocess.run(
        ["gfortran", "-c", "-fPIC", str(source), "-o", str(native_object)],
        check=True,
        capture_output=True,
        text=True,
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(source_dir),
            "--no-compile-input-sources",
            "--native-objects",
            str(native_object),
            "--out",
            "prebuilt_scale",
            "--out-dir",
            str(output_dir),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    payload = json.loads(completed.stdout)
    plan = payload["native_build_plan"]

    assert payload["sources"] == [str(source)]
    assert plan["compilation_units"] == []
    assert plan["produced_objects"] == []
    assert plan["prebuilt_artifacts"] == [{"kind": "object", "path": str(native_object)}]
    assert not (output_dir / "scale.o").exists()

    sys.modules.pop("prebuilt_scale", None)
    sys.path.insert(0, str(tmp_path))
    try:
        module = importlib.import_module("prebuilt_scale")
    finally:
        sys.path.remove(str(tmp_path))
    assert module.scale(np.float64(3.0), np.float64(2.5)) == np.float64(7.5)


def test_native_link_plan_serializes_interleaved_item_kinds():
    plan = NativeBuildPlan(
        link_items=(
            NativeLinkItem("object", Path("objects/entry.o")),
            NativeLinkItem("linker_argument", "-Wl,--start-group"),
            NativeLinkItem("archive", Path("lib/libsolver.a")),
            NativeLinkItem("shared_library", Path("lib/libsupport.so")),
            NativeLinkItem("named_library", "lapack"),
            NativeLinkItem("linker_argument", "-Wl,--end-group"),
        )
    )

    assert plan.to_dict()["link_items"] == [
        {"kind": "object", "path": "objects/entry.o"},
        {"kind": "linker_argument", "argument": "-Wl,--start-group"},
        {"kind": "archive", "path": "lib/libsolver.a"},
        {"kind": "shared_library", "path": "lib/libsupport.so"},
        {"kind": "named_library", "name": "lapack"},
        {"kind": "linker_argument", "argument": "-Wl,--end-group"},
    ]


def test_wrapper_build_rejects_empty_source_list(tmp_path: Path):
    with pytest.raises(ValueError, match="at least one Fortran source"):
        build_fortran_extension([], output_dir=tmp_path)


def test_wrapper_build_rejects_missing_source(tmp_path: Path):
    missing = tmp_path / "missing.f90"

    with pytest.raises(FileNotFoundError, match="Fortran source not found"):
        build_fortran_extension(missing, output_dir=tmp_path)


@pytest.mark.parametrize("mode", ["makefile", "sources"])
def test_wrapper_build_rejects_generation_verbose_combination(tmp_path: Path, mode: str):
    source = tmp_path / DEFAULT_OUTPUT_SOURCE.name
    shutil.copyfile(DEFAULT_OUTPUT_SOURCE, source)

    generation_options = {"makefile": mode == "makefile", "generate_sources": mode == "sources"}
    with pytest.raises(ValueError, match="source/Makefile generation and verbose direct compilation"):
        build_fortran_extension(source, output_dir=tmp_path, verbose=True, **generation_options)


def test_generate_sources_cli_writes_wrapper_sources_without_native_outputs(tmp_path: Path):
    source = tmp_path / SCALE_SOURCE.name
    output_dir = tmp_path / "generated"
    shutil.copyfile(SCALE_SOURCE, source)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--sources",
            str(source),
            "--out-dir",
            str(output_dir),
            "--native-compile-flags=-g0",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["compiled"] is False
    assert payload["build_makefile"] is None
    assert payload["generated_sources"]
    assert payload["native_build_plan"]["compilation_units"][0]["flags"] == ["-g0"]
    assert all(Path(path).is_file() for path in payload["generated_sources"])
    assert not Path(payload["shared_library"]).exists()
    assert not tuple(output_dir.glob("*.o"))
    assert not tuple(output_dir.glob("*.so"))
