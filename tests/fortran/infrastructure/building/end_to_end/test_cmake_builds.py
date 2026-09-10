"""CMake integration tests for the PRIK wrapper-generation boundary."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv

import numpy as np
import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
USE_PRIK_DIR = REPOSITORY_ROOT / "cmake"
BRIDGE_CONTRACT = (
    REPOSITORY_ROOT
    / "tests"
    / "fortran"
    / "functions"
    / "end_to_end"
    / "fixtures"
    / "contracts"
    / "free_external"
    / "__init__.pyi"
)
BRIDGE_NATIVE = (
    REPOSITORY_ROOT / "tests" / "fortran" / "functions" / "end_to_end" / "fixtures" / "native" / "free_external.f90"
)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT) + (os.pathsep + existing if existing else "")
    return environment


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=environment or _environment(), capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _configure_and_build(
    project: Path,
    build: Path,
    *,
    language: str,
    use_ninja: bool = True,
    build_project: bool = True,
    environment: dict[str, str] | None = None,
    python_executable: Path | None = None,
) -> None:
    command = ["cmake", "-S", str(project), "-B", str(build)]
    if use_ninja and shutil.which("ninja"):
        command.extend(("-G", "Ninja"))
    command.append(f"-DCMAKE_C_COMPILER={shutil.which('gcc')}")
    if language == "fortran":
        command.append(f"-DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}")
    if python_executable is not None:
        command.append(f"-DPython_EXECUTABLE={python_executable}")
    _run(command, environment=environment)
    if build_project:
        _run(["cmake", "--build", str(build), "-j2"], environment=environment)


def _import_extension(module_name: str, build: Path):
    artifacts = tuple(build.rglob(f"{module_name}*.so"))
    assert artifacts, f"no CMake extension artifact in {build}"
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(artifacts[0].parent))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(artifacts[0].parent))


def _write_project(project: Path, body: str, *, languages: str = "C Fortran") -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / "CMakeLists.txt").write_text(
        f"""cmake_minimum_required(VERSION 3.20)
project(cmake_test LANGUAGES {languages})
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
list(APPEND CMAKE_MODULE_PATH "{USE_PRIK_DIR.as_posix()}")
include(UsePRIK)
{body}
""",
        encoding="utf-8",
    )


def _cmake_finds_blas() -> bool:
    if shutil.which("cmake") is None or shutil.which("gfortran") is None:
        return False
    with tempfile.TemporaryDirectory(prefix="prik-cmake-blas-") as probe_directory:
        result = subprocess.run(
            [
                "cmake",
                "--find-package",
                "-DNAME=BLAS",
                "-DCOMPILER_ID=GNU",
                "-DLANGUAGE=Fortran",
                "-DMODE=EXIST",
            ],
            cwd=probe_directory,
            capture_output=True,
            text=True,
        )
    return result.returncode == 0


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_builds_source_first_fortran_module(tmp_path: Path):
    project = tmp_path / "user project with spaces"
    project.mkdir()
    (project / "square.f90").write_text(
        """real(8) function square(x) result(y)
  real(8), intent(in) :: x
  y = x * x
end function square
""",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  square
  SOURCES square.f90
  FORTRAN_FLAGS -O0
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran", build_project=False)
    assert not tuple((build / "prik" / "square").glob("*_wrapper.*"))
    _run(["cmake", "--build", str(build), "-j2"])
    native_support_header = build / "prik" / "square" / "binding_support" / "prik_binding.h"
    assert native_support_header.is_file()
    native_support_header.unlink()
    _run(["cmake", "--build", str(build), "-j2"])
    assert native_support_header.is_file()
    module = _import_extension("square", build)
    assert module.square(np.float64(3.0)) == np.float64(9.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_preserves_per_source_compile_flags(tmp_path: Path):
    project = tmp_path / "compile flag scopes"
    project.mkdir()
    (project / "native.f90").write_text(
        "real(8) function native_value(x) result(y)\n  real(8), intent(in) :: x\n  y = x\nend function native_value\n",
        encoding="utf-8",
    )
    (project / "support.c").write_text("int prik_native_support(void) { return 0; }\n", encoding="utf-8")
    _write_project(
        project,
        """set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
prik_add_module(
  compile_flag_scopes
  SOURCES native.f90
  C_SOURCES support.c
  FORTRAN_FLAGS -DPRIK_NATIVE_FORTRAN
  C_FLAGS -DPRIK_NATIVE_C
  WRAPPER_FORTRAN_FLAGS -DPRIK_WRAPPER_FORTRAN
  WRAPPER_C_FLAGS -DPRIK_WRAPPER_C
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    commands = json.loads((build / "compile_commands.json").read_text(encoding="utf-8"))
    by_name = {Path(record["file"]).name: record["command"] for record in commands}

    assert "-DPRIK_NATIVE_FORTRAN" in by_name["native.f90"]
    assert "-DPRIK_WRAPPER_FORTRAN" not in by_name["native.f90"]
    assert "-DPRIK_NATIVE_C" in by_name["support.c"]
    assert "-DPRIK_WRAPPER_C" not in by_name["support.c"]
    bridge_command = next(command for name, command in by_name.items() if name.endswith("_wrapper.f90"))
    binding_command = next(command for name, command in by_name.items() if name.endswith("_wrapper.c"))
    assert "-DPRIK_WRAPPER_FORTRAN" in bridge_command
    assert "-DPRIK_NATIVE_FORTRAN" not in bridge_command
    assert "-DPRIK_WRAPPER_C" in binding_command
    assert "-DPRIK_NATIVE_C" not in binding_command


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_keeps_native_flags_target_local(tmp_path: Path):
    project = tmp_path / "shared native source"
    project.mkdir()
    source = project / "common.f90"
    source.write_text(
        "real(8) function common_value(value) result(result)\n"
        "  real(8), intent(in) :: value\n"
        "  result = value\n"
        "end function common_value\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
prik_add_module(first SOURCES common.f90 FORTRAN_FLAGS -DFIRST_MODULE)
prik_add_module(second SOURCES common.f90 FORTRAN_FLAGS -DSECOND_MODULE)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    commands = json.loads((build / "compile_commands.json").read_text(encoding="utf-8"))
    native_commands = [record["command"] for record in commands if Path(record["file"]).resolve() == source.resolve()]
    assert len(native_commands) == 2
    assert any("-DFIRST_MODULE" in command and "-DSECOND_MODULE" not in command for command in native_commands)
    assert any("-DSECOND_MODULE" in command and "-DFIRST_MODULE" not in command for command in native_commands)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_maps_required_logical_abi_flags(tmp_path: Path):
    project = tmp_path / "logical abi flags"
    toolchain = project / "toolchain"
    toolchain.mkdir(parents=True)
    for name, compiler in (("ifort", shutil.which("gfortran")), ("icx", shutil.which("gcc"))):
        executable = toolchain / name
        executable.write_text(f'#!/bin/sh\nexec "{compiler}" "$@"\n', encoding="utf-8")
        executable.chmod(0o755)
    source_text = (
        "logical function logical_identity(value) result(output)\n"
        "  logical, intent(in) :: value\n"
        "  output = value\n"
        "end function logical_identity\n"
    )
    (project / "logical_default.f90").write_text(source_text, encoding="utf-8")
    (project / "logical_disabled.f90").write_text(source_text, encoding="utf-8")
    _write_project(
        project,
        """set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
prik_add_module(abi_default SOURCES logical_default.f90)
prik_add_module(abi_disabled SOURCES logical_disabled.f90 NO_STANDARD_LOGICALS)
""",
    )
    build = project / "build"
    _run(
        [
            "cmake",
            "-S",
            str(project),
            "-B",
            str(build),
            "-G",
            "Ninja" if shutil.which("ninja") else "Unix Makefiles",
            f"-DCMAKE_C_COMPILER={shutil.which('gcc')}",
            f"-DCMAKE_Fortran_COMPILER={toolchain / 'ifort'}",
        ]
    )
    commands = json.loads((build / "compile_commands.json").read_text(encoding="utf-8"))
    default_commands = [record["command"] for record in commands if "abi_default" in record["command"]]
    disabled_commands = [record["command"] for record in commands if "abi_disabled" in record["command"]]

    assert default_commands
    assert any("-standard-semantics" in command for command in default_commands)
    assert disabled_commands
    assert all("-standard-semantics" not in command for command in disabled_commands)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_builds_a_fortran_module(tmp_path: Path):
    project = tmp_path / "fortran module"
    project.mkdir()
    (project / "math_mod.f90").write_text(
        """module math_mod
contains
  real(8) function add(a, b) result(c)
    real(8), intent(in) :: a, b
    c = a + b
  end function add
end module math_mod
""",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  math_mod
  SOURCES math_mod.f90
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    module = _import_extension("math_mod", build)
    assert module.math_mod.add(np.float64(2.0), np.float64(3.0)) == np.float64(5.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_generate_cmake_builds_standalone_project_in_a_path_with_spaces(tmp_path: Path):
    source = tmp_path / "standalone.f90"
    source.write_text(
        """real(8) function square(x) result(y)
  real(8), intent(in) :: x
  y = x * x
end function square
""",
        encoding="utf-8",
    )
    project = tmp_path / "generated project with spaces"
    generated = _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(source),
            "--module-name",
            "generated_square",
            "--out-dir",
            str(project),
            "--json",
        ]
    )
    assert Path(json.loads(generated.stdout)["cmake_project"]) == project / "CMakeLists.txt"
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "include(UsePRIK)" in cmake_lists
    assert "prik_add_module(\n    generated_square" in cmake_lists
    build = project / "cmake-build"
    _configure_and_build(project, build, language="fortran", use_ninja=False)
    module = _import_extension("generated_square", build)
    assert module.square(np.float64(4.0)) == np.float64(16.0)


@pytest.mark.fortran_end_to_end
def test_generate_cmake_preserves_ordered_native_link_items(tmp_path: Path):
    source = tmp_path / "ordered.f90"
    source.write_text("subroutine ordered()\nend subroutine ordered\n", encoding="utf-8")
    archive = tmp_path / "libordered.a"
    archive.touch()
    project = tmp_path / "ordered project"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(source),
            "--native-link-item",
            "arg:-Wl,--start-group",
            f"archive:{archive}",
            "library:ordered",
            "arg:-Wl,--end-group",
            "--out-dir",
            str(project),
        ]
    )
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")
    ordered_items = (
        '"-Wl,--start-group"',
        f'"{Path(os.path.relpath(archive, project)).as_posix()}"',
        '"ordered"',
        '"-Wl,--end-group"',
    )
    positions = tuple(cmake_lists.index(item) for item in ordered_items)
    assert positions == tuple(sorted(positions))


@pytest.mark.fortran_end_to_end
def test_generate_cmake_emits_contract_and_linker_languages_separately(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    contract.write_text(
        "from prik.contracts import Float64\ndef add(value: Float64) -> Float64: ...\n", encoding="utf-8"
    )
    archive = tmp_path / "libimplementation.a"
    archive.touch()
    project = tmp_path / "contract project"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            "--language",
            "c",
            str(contract),
            "--native-objects",
            str(archive),
            "--native-linker-language",
            "fortran",
            "--out-dir",
            str(project),
        ]
    )
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "CONTRACT" in cmake_lists
    assert "NATIVE_LANGUAGE C" in cmake_lists
    assert "LINKER_LANGUAGE Fortran" in cmake_lists


@pytest.mark.fortran_end_to_end
def test_generate_cmake_preserves_contract_language_with_different_source_language(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    contract.write_text(
        "from prik.contracts import Float64\ndef add(value: Float64) -> Float64: ...\n", encoding="utf-8"
    )
    implementation = tmp_path / "implementation.f90"
    implementation.write_text("subroutine implementation()\nend subroutine implementation\n", encoding="utf-8")
    project = tmp_path / "mixed language contract project"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            "--language",
            "c",
            str(contract),
            "--native-fortran-sources",
            str(implementation),
            "--out-dir",
            str(project),
        ]
    )
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "NATIVE_LANGUAGE C" in cmake_lists
    assert "FORTRAN_SOURCES" in cmake_lists


@pytest.mark.fortran_end_to_end
def test_generate_cmake_keeps_compile_option_ownership_explicit(tmp_path: Path):
    source = tmp_path / "interface.f90"
    source.write_text("subroutine interface()\nend subroutine interface\n", encoding="utf-8")
    archive = tmp_path / "libimplementation.a"
    archive.touch()
    project = tmp_path / "explicit options"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(source),
            "--no-compile-input-sources",
            "--native-objects",
            str(archive),
            "--native-linker-language",
            "fortran",
            "--native-compile-flags=-DPRIK_NATIVE",
            "--wrapper-fortran-flags=-DPRIK_WRAPPER_FORTRAN",
            "--wrapper-c-flags=-DPRIK_WRAPPER_C",
            "--no-standard-logicals",
            "--lto",
            "--out-dir",
            str(project),
        ]
    )
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")

    assert 'FORTRAN_FLAGS\n        "-DPRIK_NATIVE"' in cmake_lists
    assert 'WRAPPER_FORTRAN_FLAGS\n        "-DPRIK_WRAPPER_FORTRAN"' in cmake_lists
    assert 'WRAPPER_C_FLAGS\n        "-DPRIK_WRAPPER_C"' in cmake_lists
    assert "LINKER_LANGUAGE Fortran" in cmake_lists
    assert "NO_STANDARD_LOGICALS" in cmake_lists
    assert "INTERPROCEDURAL_OPTIMIZATION TRUE" in cmake_lists
    assert "--compiler" not in cmake_lists


@pytest.mark.parametrize("option", ["--compiler=gfortran", "--wrapper-compiler-debug"])
@pytest.mark.fortran_end_to_end
def test_generate_cmake_rejects_ambiguous_direct_compiler_options(tmp_path: Path, option: str):
    source = tmp_path / "source.f90"
    source.write_text("subroutine source()\nend subroutine source\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "prik", "generate", "--cmake", str(source), option],
        env=_environment(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "generate --cmake" in result.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_generate_cmake_keeps_supplemental_c_sources_out_of_the_python_api(tmp_path: Path):
    source = tmp_path / "mixed.f90"
    source.write_text(
        """real(8) function add_one(value) result(result)
  use iso_c_binding, only: c_double
  real(8), intent(in) :: value
  interface
    function native_add_one(input) bind(C, name="native_add_one") result(output)
      import c_double
      real(c_double), value :: input
      real(c_double) :: output
    end function native_add_one
  end interface
  result = native_add_one(value)
end function add_one
""",
        encoding="utf-8",
    )
    native_c = tmp_path / "native.c"
    native_c.write_text("double native_add_one(double value) { return value + 1.0; }\n", encoding="utf-8")
    project = tmp_path / "generated mixed project"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(source),
            "--module-name",
            "mixed_extension",
            "--native-c-sources",
            str(native_c),
            "--out-dir",
            str(project),
        ]
    )
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "SOURCES" in cmake_lists
    assert "C_SOURCES" in cmake_lists
    build = project / "cmake-build"
    _configure_and_build(project, build, language="fortran")
    module = _import_extension("mixed_extension", build)
    assert module.add_one(np.float64(4.0)) == np.float64(5.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_contract_dependency_regenerates_wrapper(tmp_path: Path):
    native = tmp_path / "contract native.f90"
    native.write_text(
        """real(8) function square(x) result(y)
  real(8), intent(in) :: x
  y = x * x
end function square
""",
        encoding="utf-8",
    )
    contracts = tmp_path / "contracts"
    _run([sys.executable, "-m", "prik", "generate", "--pyi", str(native), "--out", str(contracts)])
    contract_dir = tmp_path / "contract_example"
    contract_dir.mkdir()
    contract = contract_dir / "__init__.pyi"
    contract_leaf = contract_dir / "marker.pyi"
    contract.write_text(
        (contracts / "__init__.pyi").read_text(encoding="utf-8") + "\nfrom . import marker\n",
        encoding="utf-8",
    )
    contract_leaf.write_text("# included contract dependency\n", encoding="utf-8")
    project = tmp_path / "contract project"
    _write_project(
        project,
        f"""prik_add_module(
  contract_example
  CONTRACT "{contract.as_posix()}"
  FORTRAN_SOURCES "{native.as_posix()}"
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    module = _import_extension("contract_example", build)
    assert module.square(np.float64(3.0)) == np.float64(9.0)
    native.write_text(native.read_text(encoding="utf-8").replace("y = x * x", "y = x * x + 1.0"), encoding="utf-8")
    native_rebuild = _run(["cmake", "--build", str(build), "--verbose", "-j2"])
    native_output = native_rebuild.stdout + native_rebuild.stderr
    assert "contract_native.f90" in native_output
    assert "Generate PRIK wrapper sources for contract_example" not in native_output
    contract_leaf.write_text(contract_leaf.read_text(encoding="utf-8") + "\n# contract changed\n", encoding="utf-8")
    contract_rebuild = _run(["cmake", "--build", str(build), "-j2"])
    contract_output = contract_rebuild.stdout + contract_rebuild.stderr
    assert "Generate PRIK wrapper sources for contract_example" in contract_output


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(shutil.which("cmake") is None or shutil.which("gcc") is None, reason="CMake and gcc are required")
def test_use_prik_cmake_regenerates_after_nested_c_header_changes(tmp_path: Path):
    project = tmp_path / "nested c dependency"
    include_dir = project / "include"
    include_dir.mkdir(parents=True)
    inner_header = include_dir / "inner.h"
    inner_header.write_text("double c_square(double value);\n", encoding="utf-8")
    (include_dir / "api.h").write_text('#include "inner.h"\n', encoding="utf-8")
    (project / "module.c").write_text(
        '#include "api.h"\ndouble c_square(double value) { return value * value; }\n',
        encoding="utf-8",
    )
    _write_project(
        project,
        f"""prik_add_module(
  c_header_dependency
  C_SOURCES module.c
  INCLUDE_DIRS "{include_dir.as_posix()}"
)
""",
        languages="C",
    )
    build = project / "build"
    _configure_and_build(project, build, language="c")

    inner_header.write_text("double c_square(double input);\n", encoding="utf-8")
    rebuilt = _run(["cmake", "--build", str(build), "-j2"])

    assert "Generate PRIK wrapper sources for c_header_dependency" in rebuilt.stdout + rebuilt.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_regenerates_after_fortran_include_changes(tmp_path: Path):
    project = tmp_path / "fortran include dependency"
    project.mkdir()
    include = project / "declarations.inc"
    include.write_text("implicit none\n  real(8), intent(in) :: x\n", encoding="utf-8")
    (project / "included.f90").write_text(
        "real(8) function included_square(x) result(y)\n"
        "  include 'declarations.inc'\n"
        "  y = x * x\n"
        "end function included_square\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  fortran_include_dependency
  FORTRAN_SOURCES included.f90
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    include.write_text("implicit none\n  double precision, intent(in) :: x\n", encoding="utf-8")
    rebuilt = _run(["cmake", "--build", str(build), "-j2"])

    assert "Generate PRIK wrapper sources for fortran_include_dependency" in rebuilt.stdout + rebuilt.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_compiles_generated_fortran_bridge_and_binding(tmp_path: Path):
    project = tmp_path / "bridge project"
    _write_project(
        project,
        f"""prik_add_module(
  free_external
  CONTRACT "{BRIDGE_CONTRACT.as_posix()}"
  FORTRAN_SOURCES "{BRIDGE_NATIVE.as_posix()}"
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    generated = build / "prik" / "free_external"
    assert tuple(generated.glob("*.f90")), "the generated Fortran bridge is missing"
    assert tuple(generated.glob("*.c")), "the generated C binding is missing"
    module = _import_extension("free_external", build)
    assert module.free_square(np.int32(6)) == np.int32(36)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_reconfigures_when_source_adds_a_fortran_bridge(tmp_path: Path):
    project = tmp_path / "routing project"
    project.mkdir()
    source = project / "routing.f90"
    source.write_text(
        """integer(c_int) function standalone_direct(value) bind(C, name="standalone_direct_symbol") result(output)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value

  output = value + 2_c_int
end function standalone_direct
""",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  routing
  SOURCES routing.f90
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    generated = build / "prik" / "routing"
    assert not tuple(generated.glob("*.f90"))
    module = _import_extension("routing", build)
    assert module.standalone_direct(np.int32(4)) == np.int32(6)

    source.write_text(
        """integer(c_int) function standalone_direct(value) bind(C, name="standalone_mixed_direct") result(output)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value

  output = value + 2_c_int
end function standalone_direct

integer(c_int) function standalone_adapted(value) result(output)
  use iso_c_binding
  integer(c_int), intent(in) :: value

  output = value + 3_c_int
end function standalone_adapted
""",
        encoding="utf-8",
    )
    _run(["cmake", "--build", str(build), "-j2"])
    assert tuple(generated.glob("*.f90")), "CMake did not reconfigure the generated bridge source set"


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(shutil.which("cmake") is None or shutil.which("gcc") is None, reason="CMake and gcc are required")
def test_use_prik_cmake_builds_c_source_with_include_directory_and_flag(tmp_path: Path):
    project = tmp_path / "c project with spaces"
    include_dir = project / "include files"
    include_dir.mkdir(parents=True)
    (include_dir / "cmath_api.h").write_text("double c_add(double, double);\n", encoding="utf-8")
    (project / "cexample.c").write_text(
        '#include "cmath_api.h"\n#ifdef PRIK_CMAKE_TEST_FLAG\ndouble c_add(double a, double b) { return a + b + 1.0; }\n#else\ndouble c_add(double a, double b) { return a + b; }\n#endif\n',
        encoding="utf-8",
    )
    _write_project(
        project,
        f"""prik_add_module(
  cexample
  C_SOURCES cexample.c
  INCLUDE_DIRS "{include_dir.as_posix()}"
  C_FLAGS -DPRIK_CMAKE_TEST_FLAG
  PRIK_ARGS --define PRIK_CMAKE_TEST_FLAG
)
""",
        languages="C",
    )
    build = project / "build"
    _configure_and_build(project, build, language="c")
    module = _import_extension("cexample", build)
    assert module.c_add(np.float64(2.0), np.float64(3.0)) == np.float64(6.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
@pytest.mark.parametrize(
    ("module_arguments", "expected_error_fragment"),
    (
        (
            "SOURCES source.f90\n  PRIK_ARGS --module-name hijacked",
            "PRIK_ARGS cannot override prik_add_module build ownership",
        ),
        (
            "FORTRAN_SOURCES source.f90\n  NO_COMPILE_INPUT_SOURCES",
            "NO_COMPILE_INPUT_SOURCES",
        ),
        (
            "SOURCES source.f90\n  NO_COMPILE_INPUT_SOURCES",
            "requires native implementation sources",
        ),
    ),
)
def test_use_prik_cmake_rejects_invalid_generation_ownership(
    tmp_path: Path,
    module_arguments: str,
    expected_error_fragment: str,
):
    project = tmp_path / "reserved args"
    project.mkdir()
    (project / "source.f90").write_text("subroutine source()\nend subroutine source\n", encoding="utf-8")
    _write_project(
        project,
        f"""prik_add_module(
  reserved_args
  {module_arguments}
)
""",
    )
    result = subprocess.run(
        ["cmake", "-S", str(project), "-B", str(project / "build")],
        env=_environment(),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert expected_error_fragment in result.stdout + result.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None, reason="CMake and gfortran are required"
)
def test_use_prik_cmake_requires_the_c_language(tmp_path: Path):
    project = tmp_path / "fortran-only project"
    project.mkdir()
    (project / "source.f90").write_text(
        "real(8) function source(value) result(result)\n"
        "  real(8), intent(in) :: value\n"
        "  result = value\n"
        "end function source\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(source SOURCES source.f90)
""",
        languages="Fortran",
    )
    result = subprocess.run(
        [
            "cmake",
            "-S",
            str(project),
            "-B",
            str(project / "build"),
            f"-DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}",
        ],
        env=_environment(),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "PRIK Python extensions require CMake's C language to be enabled" in result.stdout + result.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_links_a_normal_fortran_library_target(tmp_path: Path):
    project = tmp_path / "external target"
    project.mkdir()
    (project / "native_math.f90").write_text(
        "real(8) function native_add(x, y) result(z)\n"
        "  real(8), intent(in) :: x, y\n"
        "  z = x + y\n"
        "end function native_add\n",
        encoding="utf-8",
    )
    (project / "wrapper.f90").write_text(
        "real(8) function call_native(x, y) result(z)\n"
        "  real(8), intent(in) :: x, y\n"
        "  interface\n"
        "    function native_add(a, b) result(c)\n"
        "      real(8), intent(in) :: a, b\n"
        "      real(8) :: c\n"
        "    end function native_add\n"
        "  end interface\n"
        "  z = native_add(x, y)\n"
        "end function call_native\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """add_library(native_math STATIC native_math.f90)
prik_add_module(
  external_target
  SOURCES wrapper.f90
  LINK_LIBRARIES native_math
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    module = _import_extension("external_target", build)
    assert module.call_native(np.float64(2.0), np.float64(3.0)) == np.float64(5.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_uses_target_as_the_only_native_implementation(tmp_path: Path):
    project = tmp_path / "target only implementation"
    project.mkdir()
    interface = (
        "real(8) function target_square(value) result(result)\n"
        "  real(8), intent(in) :: value\n"
        "  result = value * value\n"
        "end function target_square\n"
    )
    (project / "interface.f90").write_text(interface, encoding="utf-8")
    (project / "implementation.f90").write_text(interface, encoding="utf-8")
    _write_project(
        project,
        """add_library(native_math STATIC implementation.f90)
prik_add_module(
  target_only
  SOURCES interface.f90
  NO_COMPILE_INPUT_SOURCES
  LINK_LIBRARIES native_math
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    module = _import_extension("target_only", build)
    assert module.target_square(np.float64(4.0)) == np.float64(16.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None
    or shutil.which("gfortran") is None
    or shutil.which("gcc") is None
    or shutil.which("ar") is None,
    reason="CMake, gfortran, gcc, and ar are required",
)
def test_use_prik_cmake_selects_fortran_linker_for_raw_archive(tmp_path: Path):
    project = tmp_path / "raw fortran archive"
    project.mkdir()
    source_text = (
        "integer(c_int) function raw_add_two(value) bind(C, name='raw_add_two_symbol') result(output)\n"
        "  use iso_c_binding, only: c_int\n"
        "  integer(c_int), value, intent(in) :: value\n"
        "  character(len=16) :: buffer\n"
        "  write(buffer, '(I0)') value\n"
        "  read(buffer, *) output\n"
        "  output = output + 2_c_int\n"
        "end function raw_add_two\n"
    )
    interface = project / "interface.f90"
    implementation = project / "implementation.f90"
    interface.write_text(source_text, encoding="utf-8")
    implementation.write_text(source_text, encoding="utf-8")
    native_object = project / "implementation.o"
    archive = project / "libraw_math.a"
    _run([shutil.which("gfortran"), "-fPIC", "-c", str(implementation), "-o", str(native_object)])
    _run([shutil.which("ar"), "rcs", str(archive), str(native_object)])
    _write_project(
        project,
        f"""prik_add_module(
  raw_archive
  SOURCES interface.f90
  NO_COMPILE_INPUT_SOURCES
  LINKER_LANGUAGE Fortran
  LINK_LIBRARIES "{archive.as_posix()}"
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    module = _import_extension("raw_archive", build)
    assert module.raw_add_two(np.int32(5)) == np.int32(7)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None
    or shutil.which("gfortran") is None
    or shutil.which("gcc") is None
    or shutil.which("ar") is None,
    reason="CMake, gfortran, gcc, and ar are required",
)
def test_use_prik_cmake_separates_c_contract_and_fortran_linker_languages(tmp_path: Path):
    project = tmp_path / "c contract with fortran implementation"
    project.mkdir()
    (project / "api.pyi").write_text(
        "from prik.contracts import Float64\n\ndef add_one(value: Float64) -> Float64: ...\n",
        encoding="utf-8",
    )
    implementation = project / "implementation.f90"
    implementation.write_text(
        "real(c_double) function add_one(value) bind(C, name='add_one') result(result)\n"
        "  use iso_c_binding, only: c_double\n"
        "  real(c_double), value, intent(in) :: value\n"
        "  result = value + 1.0_c_double\n"
        "end function add_one\n",
        encoding="utf-8",
    )
    native_object = project / "implementation.o"
    archive = project / "libimplementation.a"
    _run([shutil.which("gfortran"), "-fPIC", "-c", str(implementation), "-o", str(native_object)])
    _run([shutil.which("ar"), "rcs", str(archive), str(native_object)])
    _write_project(
        project,
        """prik_add_module(
  c_contract
  CONTRACT api.pyi
  NATIVE_LANGUAGE C
  LINKER_LANGUAGE Fortran
  LINK_LIBRARIES "${CMAKE_CURRENT_SOURCE_DIR}/libimplementation.a"
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    module = _import_extension("c_contract", build)
    assert module.add_one(np.float64(5.0)) == np.float64(6.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_allows_contract_language_to_differ_from_source_language(tmp_path: Path):
    project = tmp_path / "c contract with fortran source"
    project.mkdir()
    (project / "api.pyi").write_text(
        "from prik.contracts import Float64\n\ndef add_two(value: Float64) -> Float64: ...\n",
        encoding="utf-8",
    )
    (project / "implementation.f90").write_text(
        "real(c_double) function add_two(value) bind(C, name='add_two') result(result)\n"
        "  use iso_c_binding, only: c_double\n"
        "  real(c_double), value, intent(in) :: value\n"
        "  result = value + 2.0_c_double\n"
        "end function add_two\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  c_contract_source
  CONTRACT api.pyi
  NATIVE_LANGUAGE C
  FORTRAN_SOURCES implementation.f90
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    module = _import_extension("c_contract_source", build)
    assert module.add_two(np.float64(5.0)) == np.float64(7.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_generate_cmake_can_keep_semantic_sources_out_of_native_compilation(tmp_path: Path):
    project = tmp_path / "separate implementation"
    project.mkdir()
    (project / "interface.f90").write_text(
        """real(8) function square(value) result(result)
  real(8), intent(in) :: value
  result = value * value
end function square
""",
        encoding="utf-8",
    )
    (project / "implementation.f90").write_text(
        """real(8) function square(value) result(result)
  real(8), intent(in) :: value
  result = value * value + 1.0
end function square
""",
        encoding="utf-8",
    )
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            "--module-name",
            "separate_implementation",
            "--no-compile-input-sources",
            str(project / "interface.f90"),
            "--native-fortran-sources",
            str(project / "implementation.f90"),
            "--out-dir",
            str(project),
        ]
    )
    assert "NO_COMPILE_INPUT_SOURCES" in (project / "CMakeLists.txt").read_text(encoding="utf-8")
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    module = _import_extension("separate_implementation", build)
    assert module.square(np.float64(3.0)) == np.float64(10.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(not _cmake_finds_blas(), reason="CMake cannot discover a Fortran BLAS implementation")
def test_use_prik_cmake_links_a_cmake_discovered_blas_target(tmp_path: Path):
    project = tmp_path / "blas target"
    (project / "blas_example.f90").parent.mkdir(parents=True)
    (project / "blas_example.f90").write_text(
        "real(8) function blas_dot(x, y) result(value)\n"
        "  real(8), intent(in) :: x(2), y(2)\n"
        "  real(8) ddot\n"
        "  external ddot\n"
        "  value = ddot(2, x, 1, y, 1)\n"
        "end function blas_dot\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """find_package(BLAS REQUIRED)
if(TARGET BLAS::BLAS)
  set(PRIK_TEST_BLAS_TARGET BLAS::BLAS)
else()
  set(PRIK_TEST_BLAS_TARGET ${BLAS_LIBRARIES})
endif()
prik_add_module(
  blas_example
  FORTRAN_SOURCES blas_example.f90
  LINK_LIBRARIES ${PRIK_TEST_BLAS_TARGET}
)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")
    module = _import_extension("blas_example", build)
    assert module.blas_dot(np.array([1.0, 2.0]), np.array([3.0, 4.0])) == np.float64(11.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.slow
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_installed_wheel_discovers_and_builds_with_use_prik(tmp_path: Path):
    distribution_dir = tmp_path / "dist"
    clean_environment = os.environ.copy()
    clean_environment.pop("PYTHONPATH", None)
    wheel_build = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(distribution_dir),
            ".",
        ],
        cwd=REPOSITORY_ROOT,
        env=clean_environment,
        capture_output=True,
        text=True,
    )
    if wheel_build.returncode != 0:
        wheel_output = wheel_build.stderr.strip() or wheel_build.stdout.strip()
        unavailable_markers = (
            "No module named pip",
            "No module named build",
            "No matching distribution found",
            "Could not find a version that satisfies",
            "Could not fetch URL",
            "Temporary failure in name resolution",
            "Network is unreachable",
            "Connection timed out",
        )
        if any(marker.lower() in wheel_output.lower() for marker in unavailable_markers):
            pytest.skip(f"isolated wheel construction is unavailable: {wheel_output}")
        pytest.fail(f"isolated wheel construction failed:\n{wheel_output}")
    wheels = tuple(distribution_dir.glob("prik-*.whl"))
    if not wheels:
        pytest.skip("isolated wheel construction produced no wheel")
    wheel = wheels[0]
    environment_dir = tmp_path / "installed"
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment_dir)
    installed_python = environment_dir / "bin" / "python"
    _run(
        [str(installed_python), "-m", "pip", "install", "--no-deps", str(wheel)],
        environment=clean_environment,
    )
    discovery = _run(
        [
            str(installed_python),
            "-I",
            "-c",
            "from prik.cmake import cmake_module_dir; print(cmake_module_dir() / 'UsePRIK.cmake')",
        ],
        environment=clean_environment,
    )
    helper = Path(discovery.stdout.strip())
    assert helper.is_file()
    assert REPOSITORY_ROOT not in helper.parents

    source = tmp_path / "installed_square.f90"
    source.write_text(
        "real(8) function installed_square(value) result(output)\n"
        "  real(8), intent(in) :: value\n"
        "  output = value * value\n"
        "end function installed_square\n",
        encoding="utf-8",
    )
    project = tmp_path / "installed project"
    _run(
        [
            str(installed_python),
            "-I",
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(source),
            "--out-dir",
            str(project),
        ],
        environment=clean_environment,
    )
    build = project / "build"
    _configure_and_build(
        project,
        build,
        language="fortran",
        environment=clean_environment,
        python_executable=installed_python,
    )
    artifact = next(build.rglob("installed_square*.so"))
    imported = _run(
        [
            str(installed_python),
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(artifact.parent)!r}); "
            "import installed_square; assert installed_square.installed_square(3.0) == 9.0",
        ],
        cwd=artifact.parent,
        environment=clean_environment,
    )
    assert imported.returncode == 0
