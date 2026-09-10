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


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=_environment(), capture_output=True, text=True)
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
) -> None:
    command = ["cmake", "-S", str(project), "-B", str(build)]
    if use_ninja and shutil.which("ninja"):
        command.extend(("-G", "Ninja"))
    command.append(f"-DCMAKE_C_COMPILER={shutil.which('gcc')}")
    if language == "fortran":
        command.append(f"-DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}")
    _run(command)
    if build_project:
        _run(["cmake", "--build", str(build), "-j2"])


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
