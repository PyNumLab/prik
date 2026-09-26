"""CMake integration tests for the PRIK wrapper-generation boundary."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import venv

import numpy as np
import pytest

from tests.fortran._support.installed_distribution import (
    UNAVAILABLE_MARKERS,
    clean_environment,
    installed_prik_python,
    prik_wheel,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
USE_PRIK_DIR = REPOSITORY_ROOT / "prik" / "cmake_modules"
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
    defines: tuple[str, ...] = (),
) -> None:
    command = ["cmake", "-S", str(project), "-B", str(build)]
    if use_ninja and shutil.which("ninja"):
        command.extend(("-G", "Ninja"))
    command.append(f"-DCMAKE_C_COMPILER={shutil.which('gcc')}")
    if language == "fortran":
        command.append(f"-DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}")
    if python_executable is not None:
        command.append(f"-DPython_EXECUTABLE={python_executable}")
    command.extend(f"-D{define}" for define in defines)
    _run(command, environment=environment)
    if build_project:
        _run(["cmake", "--build", str(build), "-j2"], environment=environment)


def _extension_artifact(module_name: str, build: Path) -> Path:
    artifacts = tuple(
        path
        for path in build.rglob(f"{module_name}.*")
        if path.suffix == ".so" and path.name.split(".")[0] == module_name
    )
    assert len(artifacts) == 1, f"expected one {module_name} extension artifact in {build}: {artifacts}"
    return artifacts[0]


def _import_extension(module_name: str, build: Path):
    directory = str(_extension_artifact(module_name, build).parent)
    sys.modules.pop(module_name, None)
    sys.path.insert(0, directory)
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(directory)


def _call_extension(
    module_name: str, build: Path, expression: str, *, environment: dict[str, str] | None = None
) -> str:
    """Import the built extension in a fresh interpreter and evaluate one call.

    A rebuilt extension cannot be re-imported in this process: CPython caches
    an extension module for the life of the interpreter, so a second import
    returns the shared library the first one loaded.
    """
    environment = dict(environment or _environment())
    directory = str(_extension_artifact(module_name, build).parent)
    environment["PYTHONPATH"] = directory + os.pathsep + environment["PYTHONPATH"]
    program = f"import numpy, {module_name}\nprint({expression})\n"
    return _run([sys.executable, "-c", program], environment=environment).stdout.strip()


def _call_with_unassisted_loader(module_name: str, build: Path, expression: str, *, native_library: Path) -> str:
    """Import the built extension with no loader path able to find its native library.

    The interpreter keeps whatever loader environment it was started with, since
    a shared-libpython build needs it, but that environment is asserted not to
    resolve ``native_library``. Only the extension's own build rpath can.
    """
    environment = _environment()
    for variable in ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH"):
        searched = tuple(entry for entry in environment.get(variable, "").split(os.pathsep) if entry)
        assert not any((Path(entry) / native_library.name).exists() for entry in searched), (
            f"{variable} already resolves {native_library.name}, so the import would not prove a build rpath"
        )
    return _call_extension(module_name, build, expression, environment=environment)


def _write_project(project: Path, body: str, *, languages: str = "C Fortran") -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / "CMakeLists.txt").write_text(
        f"""cmake_minimum_required(VERSION 3.21)
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


REQUIRES_CMAKE_FORTRAN = pytest.mark.skipif(
    shutil.which("cmake") is None
    or shutil.which("gfortran") is None
    or shutil.which("gcc") is None
    or shutil.which("ar") is None,
    reason="CMake, gfortran, gcc, and ar are required",
)
GENERATION_COMMENT = re.compile(r"Generate PRIK wrapper sources for (\w+)")


def _regenerated(output: str) -> set[str]:
    """Return the modules whose wrapper generation a build ran."""
    return set(GENERATION_COMMENT.findall(output))


def _compile_archive(source: Path, archive: Path) -> Path:
    native_object = archive.with_suffix(".o")
    _run([shutil.which("gfortran"), "-fPIC", "-c", str(source), "-o", str(native_object)])
    _run([shutil.which("ar"), "rcs", str(archive), str(native_object)])
    native_object.unlink()
    return archive


def _write_files(root: Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


SHARED_PROJECT_FILES = {
    "square.f90": "real(8) function square(x) result(y)\n  real(8), intent(in) :: x\n  y = x * x\nend function square\n",
    "math_mod.f90": (
        "module math_mod\ncontains\n  real(8) function add(a, b) result(c)\n    real(8), intent(in) :: a, b\n"
        "    c = a + b\n  end function add\nend module math_mod\n"
    ),
    "flag_native.f90": (
        "real(8) function native_value(x) result(y)\n  real(8), intent(in) :: x\n  y = x\nend function native_value\n"
    ),
    "flag_support.c": "int prik_native_support(void) { return 0; }\n",
    "common.f90": (
        "real(8) function common_value(value) result(result)\n  real(8), intent(in) :: value\n"
        "  result = value\nend function common_value\n"
    ),
    "include files/cmath_api.h": "double c_add(double, double);\n",
    "cexample.c": (
        '#include "cmath_api.h"\n#ifdef PRIK_CMAKE_TEST_FLAG\n'
        "double c_add(double a, double b) { return a + b + 1.0; }\n#else\n"
        "double c_add(double a, double b) { return a + b; }\n#endif\n"
    ),
    "dependency_interface.c": "double dependency_add(double value);\n",
    "dependency_implementation.c": (
        "#ifndef PRIK_REQUIRED_DEFINE\n#error missing dependency compile definition\n#endif\n"
        "double dependency_add(double value) { return value + 1.0; }\n"
    ),
    "external_math.f90": (
        "real(8) function native_add(x, y) result(z)\n  real(8), intent(in) :: x, y\n  z = x + y\n"
        "end function native_add\n"
    ),
    "external_wrapper.f90": (
        "real(8) function call_native(x, y) result(z)\n  real(8), intent(in) :: x, y\n  interface\n"
        "    function native_add(a, b) result(c)\n      real(8), intent(in) :: a, b\n      real(8) :: c\n"
        "    end function native_add\n  end interface\n  z = native_add(x, y)\nend function call_native\n"
    ),
    "target_interface.f90": (
        "real(8) function target_square(value) result(result)\n  real(8), intent(in) :: value\n"
        "  result = value * value\nend function target_square\n"
    ),
    "target_implementation.f90": (
        "real(8) function target_square(value) result(result)\n  real(8), intent(in) :: value\n"
        "  result = value * value\nend function target_square\n"
    ),
    "raw_interface.f90": (
        "integer(c_int) function raw_add_two(value) bind(C, name='raw_add_two_symbol') result(output)\n"
        "  use iso_c_binding, only: c_int\n  integer(c_int), value, intent(in) :: value\n"
        "  character(len=16) :: buffer\n  write(buffer, '(I0)') value\n  read(buffer, *) output\n"
        "  output = output + 2_c_int\nend function raw_add_two\n"
    ),
    "c_contract/api.pyi": "from prik.contracts import Float64\n\ndef add_one(value: Float64) -> Float64: ...\n",
    "c_contract_implementation.f90": (
        "real(c_double) function add_one(value) bind(C, name='add_one') result(result)\n"
        "  use iso_c_binding, only: c_double\n  real(c_double), value, intent(in) :: value\n"
        "  result = value + 1.0_c_double\nend function add_one\n"
    ),
    "c_contract_source/api.pyi": "from prik.contracts import Float64\n\ndef add_two(value: Float64) -> Float64: ...\n",
    "c_contract_source_implementation.f90": (
        "real(c_double) function add_two(value) bind(C, name='add_two') result(result)\n"
        "  use iso_c_binding, only: c_double\n  real(c_double), value, intent(in) :: value\n"
        "  result = value + 2.0_c_double\nend function add_two\n"
    ),
    "adapter_plain.c": "double capi_add(double value) { return value + 1.0; }\n",
    "adapter_adapted.c": "double capi_add(double value) { return value + 1.0; }\n",
}

SHARED_PROJECT_MODULES = f"""set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
prik_add_module(square SOURCES square.f90 FORTRAN_FLAGS -O0)
prik_add_module(math_mod SOURCES math_mod.f90)
prik_add_module(
  compile_flag_scopes
  SOURCES flag_native.f90
  C_SOURCES flag_support.c
  FORTRAN_FLAGS -DPRIK_NATIVE_FORTRAN
  C_FLAGS -DPRIK_NATIVE_C
  WRAPPER_FORTRAN_FLAGS -DPRIK_WRAPPER_FORTRAN
  WRAPPER_C_FLAGS -DPRIK_WRAPPER_C
)
prik_add_module(first SOURCES common.f90 FORTRAN_FLAGS -DFIRST_MODULE)
prik_add_module(second SOURCES common.f90 FORTRAN_FLAGS -DSECOND_MODULE)
prik_add_module(
  free_external
  CONTRACT "{BRIDGE_CONTRACT.as_posix()}"
  FORTRAN_SOURCES "{BRIDGE_NATIVE.as_posix()}"
)
prik_add_module(
  cexample
  C_SOURCES cexample.c
  INCLUDE_DIRS "${{CMAKE_CURRENT_SOURCE_DIR}}/include files"
  C_FLAGS -DPRIK_CMAKE_TEST_FLAG
  PRIK_ARGS --define PRIK_CMAKE_TEST_FLAG
)
add_library(native_dependency INTERFACE)
target_compile_definitions(native_dependency INTERFACE PRIK_REQUIRED_DEFINE)
prik_add_module(
  dependency_usage
  SOURCES dependency_interface.c
  C_SOURCES dependency_implementation.c
  LINK_LIBRARIES native_dependency
)
add_library(external_math STATIC external_math.f90)
prik_add_module(external_target SOURCES external_wrapper.f90 LINK_LIBRARIES external_math)
add_library(target_math STATIC target_implementation.f90)
prik_add_module(
  target_only
  SOURCES target_interface.f90
  NO_COMPILE_INPUT_SOURCES
  LINK_LIBRARIES target_math
)
prik_add_module(
  raw_archive
  SOURCES raw_interface.f90
  NO_COMPILE_INPUT_SOURCES
  LINKER_LANGUAGE Fortran
  LINK_LIBRARIES "${{CMAKE_CURRENT_SOURCE_DIR}}/libraw_math.a"
)
prik_add_module(
  c_contract
  CONTRACT c_contract/api.pyi
  NATIVE_LANGUAGE C
  LINKER_LANGUAGE Fortran
  LINK_LIBRARIES "${{CMAKE_CURRENT_SOURCE_DIR}}/libimplementation.a"
)
prik_add_module(
  c_contract_source
  CONTRACT c_contract_source/api.pyi
  NATIVE_LANGUAGE C
  FORTRAN_SOURCES c_contract_source_implementation.f90
)
prik_add_module(adapter_plain C_SOURCES adapter_plain.c)
prik_add_module(adapter_adapted C_SOURCES adapter_adapted.c PRIK_ARGS --collision-adapter-all)
"""


@pytest.fixture(scope="module")
def shared_project(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """Configure and build one CMake project that finds PRIK and declares many independent modules.

    Every module here is read-only evidence for the tests below, so one
    configure and one parallel build serve all of them. Tests that edit a
    project after it is built keep their own project.
    """
    if any(shutil.which(tool) is None for tool in ("cmake", "gfortran", "gcc", "ar")):
        pytest.skip("CMake, gfortran, gcc, and ar are required")
    project = tmp_path_factory.mktemp("use-prik") / "shared project with spaces"
    _write_files(project, SHARED_PROJECT_FILES)
    raw_source = project / "raw_implementation.f90"
    raw_source.write_text(SHARED_PROJECT_FILES["raw_interface.f90"], encoding="utf-8")
    _compile_archive(raw_source, project / "libraw_math.a")
    _compile_archive(project / "c_contract_implementation.f90", project / "libimplementation.a")
    (project / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.21)\n"
        "project(cmake_test LANGUAGES C Fortran)\n"
        "find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)\n"
        "find_package(PRIK CONFIG REQUIRED)\n" + SHARED_PROJECT_MODULES,
        encoding="utf-8",
    )
    build = project / "build"
    _configure_and_build(
        project,
        build,
        language="fortran",
        build_project=False,
        defines=(f"PRIK_DIR={USE_PRIK_DIR.as_posix()}",),
    )
    configured_wrappers = tuple((build / "prik").rglob("*_wrapper.*")) if (build / "prik").exists() else ()
    _run(["cmake", "--build", str(build), "-j2"])
    return SimpleNamespace(project=project, build=build, configured_wrappers=configured_wrappers)


@pytest.mark.fortran_end_to_end
def test_find_package_prik_builds_source_contract_and_c_modules_at_build_time(shared_project: SimpleNamespace):
    """``find_package(PRIK CONFIG)`` provides the helper, and configure plans without generating."""
    build = shared_project.build
    assert shared_project.configured_wrappers == ()

    square = _import_extension("square", build)
    assert square.square(np.float64(3.0)) == np.float64(9.0)
    math_mod = _import_extension("math_mod", build)
    assert math_mod.math_mod.add(np.float64(2.0), np.float64(3.0)) == np.float64(5.0)

    generated = build / "prik" / "free_external"
    assert tuple(generated.glob("*.f90")), "the generated Fortran bridge is missing"
    assert tuple(generated.glob("*.c")), "the generated C binding is missing"
    free_external = _import_extension("free_external", build)
    assert free_external.free_square(np.int32(6)) == np.int32(36)

    # The C flag reaches both native compilation and semantic preprocessing,
    # and the include directory with a space in its path reaches both too.
    cexample = _import_extension("cexample", build)
    assert cexample.c_add(np.float64(2.0), np.float64(3.0)) == np.float64(6.0)

    # A C contract may be implemented by native Fortran sources.
    c_contract_source = _import_extension("c_contract_source", build)
    assert c_contract_source.add_two(np.float64(5.0)) == np.float64(7.0)


@pytest.mark.fortran_end_to_end
def test_use_prik_cmake_scopes_native_and_wrapper_flags_per_source_and_target(shared_project: SimpleNamespace):
    commands = json.loads((shared_project.build / "compile_commands.json").read_text(encoding="utf-8"))
    by_name = {Path(record["file"]).name: record["command"] for record in commands}

    assert "-DPRIK_NATIVE_FORTRAN" in by_name["flag_native.f90"]
    assert "-DPRIK_WRAPPER_FORTRAN" not in by_name["flag_native.f90"]
    assert "-DPRIK_NATIVE_C" in by_name["flag_support.c"]
    assert "-DPRIK_WRAPPER_C" not in by_name["flag_support.c"]
    bridge_command = by_name["bind_c_compile_flag_scopes_wrapper.f90"]
    binding_command = by_name["compile_flag_scopes_wrapper.c"]
    assert "-DPRIK_WRAPPER_FORTRAN" in bridge_command
    assert "-DPRIK_NATIVE_FORTRAN" not in bridge_command
    assert "-DPRIK_WRAPPER_C" in binding_command
    assert "-DPRIK_NATIVE_C" not in binding_command

    # One native source shared by two modules compiles once per target, each
    # with only its own module's flags.
    common = (shared_project.project / "common.f90").resolve()
    native_commands = [record["command"] for record in commands if Path(record["file"]).resolve() == common]
    assert len(native_commands) == 2
    assert any("-DFIRST_MODULE" in command and "-DSECOND_MODULE" not in command for command in native_commands)
    assert any("-DSECOND_MODULE" in command and "-DFIRST_MODULE" not in command for command in native_commands)


@pytest.mark.fortran_end_to_end
def test_use_prik_cmake_links_native_implementations_from_targets_and_archives(shared_project: SimpleNamespace):
    build = shared_project.build

    # An INTERFACE dependency's usage requirements reach the native C objects.
    dependency_usage = _import_extension("dependency_usage", build)
    assert dependency_usage.dependency_add(np.float64(2.0)) == np.float64(3.0)
    # A normal CMake library target links beside compiled semantic sources.
    external_target = _import_extension("external_target", build)
    assert external_target.call_native(np.float64(2.0), np.float64(3.0)) == np.float64(5.0)
    # With input compilation off, the target is the only native implementation.
    target_only = _import_extension("target_only", build)
    assert target_only.target_square(np.float64(4.0)) == np.float64(16.0)
    # A raw Fortran archive that needs the Fortran runtime links with the Fortran driver.
    raw_archive = _import_extension("raw_archive", build)
    assert raw_archive.raw_add_two(np.int32(5)) == np.int32(7)
    # A C contract keeps its contract language while Fortran links its archive.
    c_contract = _import_extension("c_contract", build)
    assert c_contract.add_one(np.float64(5.0)) == np.float64(6.0)


@pytest.mark.fortran_end_to_end
def test_use_prik_cmake_keeps_the_adapter_filename_fixed(shared_project: SimpleNamespace):
    """The adapter unit is declared either way: a stub without adapters, real content with them."""
    results = {}
    for label in ("plain", "adapted"):
        module_name = f"adapter_{label}"
        adapters = shared_project.build / "prik" / module_name / f"{module_name}_adapters.c"
        assert adapters.is_file(), f"the deterministic adapter source is missing for {label}"
        results[label] = adapters.read_text(encoding="utf-8")
        module = _import_extension(module_name, shared_project.build)
        assert module.capi_add(np.float64(2.0)) == np.float64(3.0)

    assert "prik_unused_adapter_stub" in results["plain"]
    assert "prik_unused_adapter_stub" not in results["adapted"]
    assert "capi_add" in results["adapted"]


ROUTING_DIRECT = """integer(c_int) function standalone_direct(value) bind(C, name="standalone_direct_symbol") result(output)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value

  output = value + 2_c_int
end function standalone_direct
"""
ROUTING_MIXED = """integer(c_int) function standalone_direct(value) bind(C, name="standalone_mixed_direct") result(output)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value

  output = value + 2_c_int
end function standalone_direct

integer(c_int) function standalone_adapted(value) result(output)
  use iso_c_binding
  integer(c_int), intent(in) :: value

  output = value + 3_c_int
end function standalone_adapted
"""


@pytest.mark.fortran_end_to_end
@REQUIRES_CMAKE_FORTRAN
def test_use_prik_cmake_rebuilds_regenerate_only_the_changed_module(tmp_path: Path):
    """Each generation input is a build dependency of its own module, and nothing else is."""
    project = tmp_path / "incremental project"
    native = project / "contract native.f90"
    _write_files(
        project,
        {
            "contract native.f90": (
                "real(8) function square(x) result(y)\n  real(8), intent(in) :: x\n  y = x * x\nend function square\n"
            ),
            "include/inner.h": "double c_square(double value);\n",
            "include/api.h": '#include "inner.h"\n',
            "c_header_module.c": '#include "api.h"\ndouble c_square(double value) { return value * value; }\n',
            "declarations.inc": "implicit none\n  real(8), intent(in) :: x\n",
            "included.f90": (
                "real(8) function included_square(x) result(y)\n  include 'declarations.inc'\n  y = x * x\n"
                "end function included_square\n"
            ),
            "routing.f90": ROUTING_DIRECT,
        },
    )
    contracts = tmp_path / "contracts"
    _run([sys.executable, "-m", "prik", "generate", "--pyi", str(native), "--out", str(contracts)])
    contract_dir = tmp_path / "contract_example"
    contract_dir.mkdir()
    contract_leaf = contract_dir / "marker.pyi"
    (contract_dir / "__init__.pyi").write_text(
        (contracts / "__init__.pyi").read_text(encoding="utf-8") + "\nfrom . import marker\n",
        encoding="utf-8",
    )
    contract_leaf.write_text("# included contract dependency\n", encoding="utf-8")
    _write_project(
        project,
        f"""prik_add_module(
  contract_example
  CONTRACT "{(contract_dir / "__init__.pyi").as_posix()}"
  FORTRAN_SOURCES "{native.as_posix()}"
)
prik_add_module(
  c_header_dependency
  C_SOURCES c_header_module.c
  INCLUDE_DIRS "{(project / "include").as_posix()}"
)
prik_add_module(fortran_include_dependency FORTRAN_SOURCES included.f90)
prik_add_module(routing SOURCES routing.f90)
""",
    )
    build = project / "build"
    _configure_and_build(project, build, language="fortran")

    def rebuild(*arguments: str) -> str:
        result = _run(["cmake", "--build", str(build), *arguments, "-j2"])
        return result.stdout + result.stderr

    assert _regenerated(rebuild()) == set(), "an unchanged build reran PRIK generation"

    native_support_header = build / "prik" / "routing" / "binding_support" / "prik_binding.h"
    assert native_support_header.is_file()
    native_support_header.unlink()
    rebuild()
    assert native_support_header.is_file()

    contract_example = _import_extension("contract_example", build)
    assert contract_example.square(np.float64(3.0)) == np.float64(9.0)
    native.write_text(native.read_text(encoding="utf-8").replace("y = x * x", "y = x * x + 1.0"), encoding="utf-8")
    native_output = rebuild("--verbose")
    assert "contract_native.f90" in native_output
    assert _regenerated(native_output) == set(), "a native-only edit reran contract generation"

    contract_leaf.write_text(contract_leaf.read_text(encoding="utf-8") + "\n# contract changed\n", encoding="utf-8")
    assert _regenerated(rebuild()) == {"contract_example"}

    (project / "include" / "inner.h").write_text("double c_square(double input);\n", encoding="utf-8")
    assert _regenerated(rebuild()) == {"c_header_dependency"}

    (project / "declarations.inc").write_text("implicit none\n  double precision, intent(in) :: x\n", encoding="utf-8")
    assert _regenerated(rebuild()) == {"fortran_include_dependency"}

    # A semantic edit changes the bridge file's contents, never the build graph.
    # This module needs no bridge, but the declared source still exists so
    # CMake's source list does not depend on semantic analysis.
    bridge = build / "prik" / "routing" / "bind_c_routing_wrapper.f90"
    assert "prik_unused_bridge_stub" in bridge.read_text(encoding="utf-8")
    assert _call_extension("routing", build, "routing.standalone_direct(numpy.int32(4))") == "6"
    # Adding a procedure that needs a bridge must not require a reconfigure.
    (project / "routing.f90").write_text(ROUTING_MIXED, encoding="utf-8")
    assert _regenerated(rebuild()) == {"routing"}
    bridge_text = bridge.read_text(encoding="utf-8")
    assert "prik_unused_bridge_stub" not in bridge_text, "the bridge stub was not replaced by real content"
    assert "bind_c_routing_wrapper" in bridge_text
    assert _call_extension("routing", build, "routing.standalone_adapted(numpy.int32(4))") == "7"
    # ... and reverting is symmetric: real content becomes a stub again.
    (project / "routing.f90").write_text(ROUTING_DIRECT, encoding="utf-8")
    rebuild()
    assert "prik_unused_bridge_stub" in bridge.read_text(encoding="utf-8")
    assert _call_extension("routing", build, "routing.standalone_direct(numpy.int32(4))") == "6"


@pytest.mark.fortran_end_to_end
@REQUIRES_CMAKE_FORTRAN
def test_generate_cmake_builds_a_standalone_project_from_every_native_input_kind(tmp_path: Path):
    """A generated project links a native source, object, archive, and directory-found library.

    The semantic sources are not compiled, so every value below comes from the
    separate native implementation, and the named library resolves at import
    through the build's own runtime search path.
    """
    sources = tmp_path / "sources"
    library_dir = tmp_path / "native runtime lib"
    library_dir.mkdir()

    def function(name: str, expression: str) -> str:
        return f"real(8) function {name}(x) result(y)\n  real(8), intent(in) :: x\n  y = {expression}\nend function {name}\n"

    _write_files(
        sources,
        {
            "scaled.f90": function("scaled", "x * 3.0d0"),
            "shifted.f90": function("shifted", "x + 7.0d0"),
            "runtime_value.f90": function("runtime_value", "x * 5.0d0"),
            "implementation.f90": function("square", "x * x + 1.0d0"),
            "interface.f90": "".join(function(name, "x") for name in ("scaled", "shifted", "runtime_value", "square")),
        },
    )
    archive = _compile_archive(sources / "scaled.f90", sources / "libscaled.a")
    linked_object = sources / "shifted.o"
    _run(["gfortran", "-c", "-fPIC", "-o", str(linked_object), str(sources / "shifted.f90")])
    native_library = library_dir / "libprikruntime.so"
    _run(["gfortran", "-shared", "-fPIC", "-o", str(native_library), str(sources / "runtime_value.f90")])

    project = tmp_path / "generated project with spaces"
    generated = _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(sources / "interface.f90"),
            "--module-name",
            "generated_inputs",
            "--no-compile-input-sources",
            "--native-fortran-sources",
            str(sources / "implementation.f90"),
            "--native-objects",
            str(linked_object),
            "--native-link-item",
            f"archive:{archive}",
            "--native-library",
            "prikruntime",
            "--native-library-dir",
            str(library_dir),
            "--native-linker-language",
            "fortran",
            "--out-dir",
            str(project),
            "--json",
        ]
    )

    assert Path(json.loads(generated.stdout)["cmake_project"]) == project / "CMakeLists.txt"
    cmake_lists = (project / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "include(UsePRIK)" in cmake_lists
    assert "prik_add_module(\n    generated_inputs" in cmake_lists
    assert "NO_COMPILE_INPUT_SOURCES" in cmake_lists
    for prebuilt_path in (linked_object, archive):
        relative = Path(os.path.relpath(prebuilt_path, project)).as_posix()
        assert f'"${{CMAKE_CURRENT_LIST_DIR}}/{relative}"' in cmake_lists
    relative_library_dir = Path(os.path.relpath(library_dir, project)).as_posix()
    assert f'LIBRARY_DIRS\n        "{relative_library_dir}"' in cmake_lists
    # The directory carries CMake link and runtime meaning, so it is not also
    # repeated as a bare -L linker flag.
    assert "LINK_OPTIONS" not in cmake_lists

    build = project / "cmake-build"
    _configure_and_build(project, build, language="fortran", use_ninja=False)
    called = _call_with_unassisted_loader(
        "generated_inputs",
        build,
        "[float(generated_inputs.scaled(numpy.float64(4.0))), float(generated_inputs.shifted(numpy.float64(4.0))), "
        "float(generated_inputs.runtime_value(numpy.float64(3.0))), float(generated_inputs.square(numpy.float64(3.0)))]",
        native_library=native_library,
    )
    assert called == "[12.0, 11.0, 15.0, 10.0]"


@pytest.mark.fortran_end_to_end
def test_generate_cmake_emits_contract_source_and_linker_languages_separately(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    contract.write_text(
        "from prik.contracts import Float64\ndef add(value: Float64) -> Float64: ...\n", encoding="utf-8"
    )
    archive = tmp_path / "libimplementation.a"
    archive.touch()
    implementation = tmp_path / "implementation.f90"
    implementation.write_text("subroutine implementation()\nend subroutine implementation\n", encoding="utf-8")
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
            "--native-fortran-sources",
            str(implementation),
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
    assert "FORTRAN_SOURCES" in cmake_lists
    assert "LINKER_LANGUAGE Fortran" in cmake_lists


@pytest.mark.fortran_end_to_end
@REQUIRES_CMAKE_FORTRAN
def test_generate_cmake_lto_reaches_native_and_generated_compilation(tmp_path: Path):
    """--lto must reach both target kinds, and a supplemental C source stays out of the Python API."""
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
    project = tmp_path / "lto project"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            str(source),
            "--native-c-sources",
            str(native_c),
            "--module-name",
            "lto_module",
            "--lto",
            "--out-dir",
            str(project),
        ]
    )
    assert "C_SOURCES" in (project / "CMakeLists.txt").read_text(encoding="utf-8")

    build = project / "build"
    _configure_and_build(project, build, language="fortran", defines=("CMAKE_EXPORT_COMPILE_COMMANDS=ON",))

    entries = json.loads((build / "compile_commands.json").read_text(encoding="utf-8"))
    compiled = {Path(entry["file"]).name: entry["command"] for entry in entries}
    # The caller's native sources and every generated unit must all carry it.
    for name in ("mixed.f90", "native.c", "lto_module_wrapper.c", "bind_c_lto_module_wrapper.f90"):
        assert name in compiled, f"{name} was not compiled"
        assert "flto" in compiled[name], f"link-time optimization missing from {name}"

    called = _call_extension(
        "lto_module",
        build,
        "float(lto_module.add_one(numpy.float64(4.0))), hasattr(lto_module, 'native_add_one')",
    )
    assert called == "5.0 False"


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
        f'"${{CMAKE_CURRENT_LIST_DIR}}/{Path(os.path.relpath(archive, project)).as_posix()}"',
        '"ordered"',
        '"-Wl,--end-group"',
    )
    positions = tuple(cmake_lists.index(item) for item in ordered_items)
    assert positions == tuple(sorted(positions))


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
    lto_initializer = "set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)"
    assert lto_initializer in cmake_lists
    assert cmake_lists.index(lto_initializer) < cmake_lists.index("prik_add_module(")
    assert "set_property(TARGET explicit_options PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)" not in cmake_lists
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
@pytest.mark.skipif(shutil.which("cmake") is None or shutil.which("gcc") is None, reason="CMake and gcc are required")
@pytest.mark.parametrize(
    ("build_type", "expected", "rejected"),
    [("Debug", "PRIK_DEBUG_DEFINE", "PRIK_RELEASE_DEFINE"), ("Release", "PRIK_RELEASE_DEFINE", "PRIK_DEBUG_DEFINE")],
)
def test_use_prik_cmake_keeps_configuration_specific_link_usage_requirements(
    tmp_path: Path, build_type: str, expected: str, rejected: str
):
    project = tmp_path / f"configuration usage {build_type}"
    project.mkdir()
    (project / "interface.c").write_text("double configured_add(double value);\n", encoding="utf-8")
    (project / "implementation.c").write_text(
        f"#ifndef {expected}\n"
        f"#error missing {build_type} dependency compile definition\n"
        "#endif\n"
        f"#ifdef {rejected}\n"
        f"#error unexpected {rejected} in a {build_type} build\n"
        "#endif\n"
        "double configured_add(double value) { return value + 1.0; }\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """add_library(debug_dependency INTERFACE)
target_compile_definitions(debug_dependency INTERFACE PRIK_DEBUG_DEFINE)
add_library(release_dependency INTERFACE)
target_compile_definitions(release_dependency INTERFACE PRIK_RELEASE_DEFINE)
prik_add_module(
  configuration_usage
  SOURCES interface.c
  C_SOURCES implementation.c
  LINK_LIBRARIES debug debug_dependency optimized release_dependency
)
""",
        languages="C",
    )
    build = project / "build"
    command = ["cmake", "-S", str(project), "-B", str(build), f"-DCMAKE_BUILD_TYPE={build_type}"]
    if shutil.which("ninja"):
        command.extend(("-G", "Ninja"))
    command.append(f"-DCMAKE_C_COMPILER={shutil.which('gcc')}")
    _run(command)
    _run(["cmake", "--build", str(build), "-j2"])

    module = _import_extension("configuration_usage", build)
    assert module.configured_add(np.float64(2.0)) == np.float64(3.0)


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(shutil.which("cmake") is None or shutil.which("gcc") is None, reason="CMake and gcc are required")
def test_use_prik_cmake_rejects_an_uppercase_c_suffix(tmp_path: Path):
    project = tmp_path / "uppercase c suffix"
    project.mkdir()
    (project / "interface.C").write_text("double uppercase_add(double value);\n", encoding="utf-8")
    _write_project(
        project,
        """prik_add_module(
  uppercase_suffix
  C_SOURCES interface.C
)
""",
        languages="C",
    )
    result = subprocess.run(
        [
            "cmake",
            "-S",
            str(project),
            "-B",
            str(project / "build"),
            f"-DCMAKE_C_COMPILER={shutil.which('gcc')}",
        ],
        env=_environment(),
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "must use the .c suffix" in result.stderr


@pytest.mark.fortran_end_to_end
def test_generate_cmake_rejects_an_uppercase_c_suffix(tmp_path: Path):
    source = tmp_path / "api.C"
    source.write_text("double uppercase_add(double value) { return value + 1.0; }\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--cmake",
            "--language",
            "c",
            str(source),
            "--module-name",
            "uppercase_api",
            "--out-dir",
            str(tmp_path / "project"),
        ],
        env=_environment(),
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "must use the .c suffix" in result.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(shutil.which("cmake") is None or shutil.which("gcc") is None, reason="CMake and gcc are required")
def test_use_prik_cmake_requires_fortran_for_native_fortran_sources(tmp_path: Path):
    project = tmp_path / "c only project with fortran sources"
    project.mkdir()
    (project / "interface.c").write_text("double native_add(double value);\n", encoding="utf-8")
    (project / "implementation.f90").write_text(
        "real(8) function native_add(value) result(output)\n"
        "  real(8), intent(in) :: value\n"
        "  output = value + 1.0d0\n"
        "end function native_add\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  native_fortran_language
  SOURCES interface.c
  FORTRAN_SOURCES implementation.f90
)
""",
        languages="C",
    )
    result = subprocess.run(
        [
            "cmake",
            "-S",
            str(project),
            "-B",
            str(project / "build"),
            f"-DCMAKE_C_COMPILER={shutil.which('gcc')}",
        ],
        env=_environment(),
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "native Fortran sources" in result.stderr


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_use_prik_cmake_configure_does_not_run_the_semantic_pipeline(tmp_path: Path):
    """Configure plans structurally, so a source PRIK cannot parse still configures.

    The failure surfaces at build time, where the semantic pipeline actually
    runs. That is the whole point of the split: CMake learns its source graph
    without parsing, completing policy, or generating code.
    """
    project = tmp_path / "unparsable project"
    project.mkdir()
    (project / "broken.f90").write_text(
        "real(8) function broken(x) result(y)\n  this is not valid Fortran at all @@@\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        """prik_add_module(
  broken
  SOURCES broken.f90
)
""",
    )
    build = project / "build"
    configure = subprocess.run(
        [
            "cmake",
            "-S",
            str(project),
            "-B",
            str(build),
            f"-DCMAKE_C_COMPILER={shutil.which('gcc')}",
            f"-DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}",
        ],
        env=_environment(),
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, f"configure ran semantic analysis:\n{configure.stderr}"
    assert not tuple((build / "prik" / "broken").glob("*.c")), "configure generated wrapper sources"

    built = subprocess.run(["cmake", "--build", str(build), "-j2"], env=_environment(), capture_output=True, text=True)
    assert built.returncode != 0, "the unparsable source should fail during build-time generation"


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("gfortran") is None or shutil.which("gcc") is None, reason="gfortran and gcc are required"
)
def test_generated_placeholder_units_compile_under_strict_flags(tmp_path: Path):
    """Unused optional units must not cost the caller a warning."""
    source = tmp_path / "strict.f90"
    source.write_text(
        'integer(c_int) function strict(value) bind(C, name="strict_symbol") result(output)\n'
        "  use iso_c_binding\n"
        "  integer(c_int), value, intent(in) :: value\n"
        "  output = value\n"
        "end function strict\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "generated"
    _run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--sources",
            str(source),
            "--module-name",
            "strict",
            "--declared-layout",
            "--out-dir",
            str(out_dir),
        ]
    )

    adapter_stub = out_dir / "strict_adapters.c"
    bridge_stub = out_dir / "bind_c_strict_wrapper.f90"
    assert "prik_unused_adapter_stub" in adapter_stub.read_text(encoding="utf-8")
    assert "prik_unused_bridge_stub" in bridge_stub.read_text(encoding="utf-8")

    _run(
        [
            "gcc",
            "-c",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-Werror",
            "-std=c11",
            "-fPIC",
            str(adapter_stub),
            "-o",
            str(tmp_path / "adapter.o"),
        ]
    )
    _run(
        [
            "gfortran",
            "-c",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-Werror",
            "-fPIC",
            str(bridge_stub),
            "-o",
            str(tmp_path / "bridge.o"),
        ],
        cwd=tmp_path,
    )


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
            f"-DCMAKE_C_COMPILER={shutil.which('gcc')}",
            f"-DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}",
        ],
        env=_environment(),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "PRIK Python extensions require CMake's C language to be enabled" in result.stdout + result.stderr


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
    installed_environment = clean_environment()
    installed_python = installed_prik_python()
    discovery = _run(
        [
            str(installed_python),
            "-I",
            "-c",
            "from prik.cmake import cmake_module_dir; print(cmake_module_dir() / 'UsePRIK.cmake')",
        ],
        environment=installed_environment,
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
        environment=installed_environment,
    )
    build = project / "build"
    _configure_and_build(
        project,
        build,
        language="fortran",
        environment=installed_environment,
        python_executable=installed_python,
    )
    artifact = next(build.rglob("installed_square*.so"))
    imported = _run(
        [
            str(installed_python),
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(artifact.parent)!r}); "
            "import numpy, installed_square; "
            "assert installed_square.installed_square(numpy.float64(3.0)) == 9.0",
        ],
        cwd=artifact.parent,
        environment=installed_environment,
    )
    assert imported.returncode == 0


EXAMPLE_PROJECT = REPOSITORY_ROOT / "examples" / "cmake"


@pytest.mark.fortran_end_to_end
@pytest.mark.slow
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None or shutil.which("gcc") is None,
    reason="CMake, gfortran, and gcc are required",
)
def test_isolated_scikit_build_core_wheel_finds_prik_without_any_argument(tmp_path: Path):
    """The end-user route: pip builds in its own environment and no -D flag names PRIK.

    Build isolation is what makes this the real experience -- the build
    environment holds only what ``[build-system] requires`` installs, so
    ``find_package(PRIK CONFIG REQUIRED)`` has to resolve from PRIK's own
    ``cmake.root`` entry point. The requirement is redirected to the wheel
    built from this checkout, which is the only difference from a user's
    ``pip wheel .``.

    ``CMAKE_ARGS`` names the compilers the way every other CMake test here
    does, because PRIK pairs the C driver with the Fortran vendor: a generated
    binding can include the Fortran runtime's ``ISO_Fortran_binding.h``, which
    Apple Clang does not find beside a Homebrew GNU Fortran. That is ordinary
    toolchain configuration, and no argument here names PRIK.
    """
    wheel = prik_wheel()
    project = tmp_path / "isolated example"
    shutil.copytree(EXAMPLE_PROJECT, project)
    manifest = project / "pyproject.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace('"prik"', f'"prik @ {wheel.as_uri()}"'),
        encoding="utf-8",
    )
    environment_dir = tmp_path / "user environment"
    venv.EnvBuilder(with_pip=True).create(environment_dir)
    user_python = environment_dir / "bin" / "python"
    build_environment = clean_environment()
    build_environment["CMAKE_ARGS"] = (
        f"-DCMAKE_C_COMPILER={shutil.which('gcc')} -DCMAKE_Fortran_COMPILER={shutil.which('gfortran')}"
    )
    assert "PRIK" not in build_environment["CMAKE_ARGS"]

    built = subprocess.run(
        [str(user_python), "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(tmp_path / "dist"), str(project)],
        env=build_environment,
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        output = built.stderr.strip() or built.stdout.strip()
        if any(marker.lower() in output.lower() for marker in UNAVAILABLE_MARKERS):
            pytest.skip(f"an isolated build environment is unavailable: {output}")
        pytest.fail(f"isolated scikit-build-core build failed:\n{output}")
    wheels = tuple((tmp_path / "dist").glob("prik_cmake_example-*.whl"))
    assert wheels, "the isolated build produced no example wheel"

    _run(
        [str(user_python), "-m", "pip", "install", str(wheels[0]), "numpy"],
        environment=clean_environment(),
    )
    called = _run(
        [
            str(user_python),
            "-c",
            "import numpy, heat; print(heat.kernel.diffuse(numpy.array([0.0, 1.0, 0.0]), numpy.float64(0.25)))",
        ],
        environment=clean_environment(),
    )
    assert called.stdout.split() == ["[0.", "0.5", "0.", "]"], called.stdout


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None, reason="CMake and gfortran are required"
)
def test_structural_planning_failure_names_the_interpreter_that_cannot_import_prik(tmp_path: Path):
    """A configure-time import failure is an environment problem, so it says which one."""
    project = tmp_path / "unusable interpreter"
    project.mkdir()
    (project / "square.f90").write_text(
        "real(8) function square(x) result(y)\n  real(8), intent(in) :: x\n  y = x * x\nend function square\n",
        encoding="utf-8",
    )
    _write_project(project, "prik_add_module(square FORTRAN_SOURCES square.f90)\n")
    environment_dir = tmp_path / "environment without prik"
    venv.EnvBuilder(with_pip=False).create(environment_dir)
    bare_python = environment_dir / "bin" / "python"

    result = subprocess.run(
        ["cmake", "-S", str(project), "-B", str(project / "build"), f"-DPython_EXECUTABLE={bare_python}"],
        env=clean_environment(),
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert str(bare_python) in output
    assert "No module named prik" in output
    assert "must be importable by the interpreter" in output


@pytest.mark.fortran_end_to_end
@pytest.mark.skipif(
    shutil.which("cmake") is None or shutil.which("gfortran") is None, reason="CMake and gfortran are required"
)
def test_structural_planning_failure_keeps_a_real_error_unexplained(tmp_path: Path):
    """A generation error must reach the user as itself, not as a dependency story."""
    project = tmp_path / "rejected option"
    project.mkdir()
    (project / "square.f90").write_text(
        "real(8) function square(x) result(y)\n  real(8), intent(in) :: x\n  y = x * x\nend function square\n",
        encoding="utf-8",
    )
    _write_project(
        project,
        "prik_add_module(square FORTRAN_SOURCES square.f90 PRIK_ARGS --definitely-not-an-option)\n",
    )

    result = subprocess.run(
        ["cmake", "-S", str(project), "-B", str(project / "build")],
        env=_environment(),
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "unrecognized arguments" in output
    assert "must be importable by the interpreter" not in output
