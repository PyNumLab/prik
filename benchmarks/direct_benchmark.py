"""Shared inputs and untimed verification for direct-entrypoint benchmarks."""

from __future__ import annotations

from collections.abc import Mapping
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess  # nosec B404 - fixed local benchmark build commands
import sys
from typing import Literal

import numpy as np


BENCHMARK_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = BENCHMARK_ROOT / "sources"
DIRECT_SOURCE = SOURCE_ROOT / "direct_kernels.f90"
DIRECT_SIGNATURE = SOURCE_ROOT / "direct_kernels.pyf"
ADAPTED_SOURCE = SOURCE_ROOT / "adapted_kernels.f90"
OPTIMIZED_FLAGS = "-O3 -march=native -mtune=native"
ROUTES = ("prik-direct", "f2py-direct", "prik-adapted")
DIRECT_SYMBOLS = ("noop", "add_scalars", "add_scalars_out")
Route = Literal["prik-direct", "f2py-direct", "prik-adapted"]


def module_name(route: Route) -> str:
    """Return the import name kept distinct for each measured route."""
    return {
        "prik-direct": "bench_prik_direct",
        "f2py-direct": "bench_f2py_direct",
        "prik-adapted": "bench_prik_adapted",
    }[route]


def route_action(route: Route) -> str:
    """Return the completed PRIK route or equivalent comparison label."""
    return "generated_fortran_adapter" if route == "prik-adapted" else "direct_c_abi"


def wrapper_mode(route: Route) -> str:
    """Describe the generated native wrapper mode without implying no C binding."""
    if route == "f2py-direct":
        return "python_c_api;no_wrap_functions;skip_empty_wrappers;intent_c_signature"
    if route == "prik-direct":
        return "python_c_binding;no_user_fortran_adapter"
    return "python_c_binding;generated_fortran_adapter"


def natural_result_type(route: Route) -> str:
    """Return the unnormalized public scalar result class for one route."""
    return "builtins.float" if route == "f2py-direct" else "numpy.float64"


def native_source(route: Route) -> Path:
    """Return the native source used by one route."""
    return ADAPTED_SOURCE if route == "prik-adapted" else DIRECT_SOURCE


def build_command(
    route: Route,
    workdir: Path,
    *,
    compiler: str,
    jobs: int,
) -> tuple[str, ...]:
    """Return a clean source-to-extension command for one benchmark route."""
    name = module_name(route)
    generated = workdir / "generated"
    source = str(native_source(route).resolve())
    if route.startswith("prik-"):
        return (
            sys.executable,
            "-m",
            "prik",
            source,
            "--out",
            name,
            "--out-dir",
            str(generated),
            "--compiler",
            compiler,
            "--jobs",
            str(jobs),
            f"--native-compile-flags={OPTIMIZED_FLAGS}",
            f"--wrapper-fortran-flags={OPTIMIZED_FLAGS}",
            f"--wrapper-c-flags={OPTIMIZED_FLAGS}",
        )
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-c",
        "-m",
        name,
        str(DIRECT_SIGNATURE.resolve()),
        source,
        "--build-dir",
        str(generated),
        "--no-wrap-functions",
        "--skip-empty-wrappers",
        f"--f77flags={OPTIMIZED_FLAGS}",
        f"--f90flags={OPTIMIZED_FLAGS}",
        f"--opt={OPTIMIZED_FLAGS}",
    )


def build_environment(compiler: str) -> dict[str, str]:
    """Return the common optimized native compilation environment."""
    environment = dict(os.environ)
    environment.update(
        {
            "CFLAGS": OPTIMIZED_FLAGS,
            "FC": compiler,
            "F77": compiler,
            "F90": compiler,
            "FFLAGS": OPTIMIZED_FLAGS,
            "F90FLAGS": OPTIMIZED_FLAGS,
        }
    )
    return environment


def failure_message(command: tuple[str, ...], result: subprocess.CompletedProcess[str]) -> str:
    """Render one failed fixed benchmark command with captured diagnostics."""
    stdout = result.stdout.rstrip() or "<empty>"
    stderr = result.stderr.rstrip() or "<empty>"
    return (
        f"Build command failed with exit code {result.returncode}:\n"
        f"{' '.join(command)}\nstdout:\n{stdout}\nstderr:\n{stderr}"
    )


def run_build(route: Route, workdir: Path, *, compiler: str, jobs: int) -> None:
    """Run one clean benchmark build; correctness and artifacts remain separate."""
    shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True)
    command = build_command(route, workdir, compiler=compiler, jobs=jobs)
    result = subprocess.run(  # nosec B603 - command uses fixed benchmark inputs
        command,
        cwd=workdir,
        env=build_environment(compiler),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(failure_message(command, result))


def extension_path(route: Route, workdir: Path) -> Path:
    """Locate the loadable extension output for the requested route."""
    plain_name = workdir / f"{module_name(route)}.so"
    if plain_name.is_file():
        return plain_name
    matches = tuple(workdir.rglob(f"{module_name(route)}*.so"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {module_name(route)!r} extension, found {len(matches)}")
    return matches[0]


def _global_symbols(path: Path) -> dict[str, str]:
    """Return the globally visible symbol kinds reported by the platform tool."""
    inspector = shutil.which("nm")
    if inspector is None:
        raise RuntimeError("Direct benchmark artifact preflight requires nm")
    result = subprocess.run(  # nosec B603 - fixed tool and inspected build artifact
        (inspector, "-g", "-P", str(path)),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Cannot inspect symbols in {path}: {result.stderr.rstrip() or result.stdout.rstrip()}")
    symbols = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2:
            symbols[fields[0]] = fields[1]
    return symbols


def _compiled_object_symbols(
    workdir: Path,
    files: tuple[str, ...],
) -> dict[Path, dict[str, str]]:
    """Inspect every compiled object without relying on backend filenames."""
    return {
        workdir / relative_path: _global_symbols(workdir / relative_path)
        for relative_path in files
        if Path(relative_path).suffix == ".o"
    }


def _one_direct_symbol_object(
    objects: Mapping[Path, Mapping[str, str]],
    *,
    expected_kinds: frozenset[str],
    description: str,
    relationship: str,
) -> Path:
    """Return the unique object with the requested direct-symbol relationship."""
    matches = tuple(
        path
        for path, symbols in objects.items()
        if all(symbols.get(symbol, "").upper() in expected_kinds for symbol in DIRECT_SYMBOLS)
    )
    if len(matches) != 1:
        observed = {
            path.as_posix(): {symbol: symbols.get(symbol) for symbol in DIRECT_SYMBOLS}
            for path, symbols in objects.items()
        }
        raise RuntimeError(
            f"Expected one {description} that {relationship} every direct symbol, "
            f"found {len(matches)}; observed {observed!r}"
        )
    return matches[0]


def _require_symbol_kinds(
    path: Path,
    symbols: Mapping[str, str],
    *,
    expected_kinds: frozenset[str],
    relationship: str,
) -> None:
    """Require every direct label to have the planned object-file relationship."""
    mismatches = {
        symbol: symbols.get(symbol)
        for symbol in DIRECT_SYMBOLS
        if symbols.get(symbol, "").upper() not in expected_kinds
    }
    if mismatches:
        raise RuntimeError(f"{path} does not {relationship} every direct symbol: {mismatches!r}")


def _direct_symbol_report(route: Route, workdir: Path, files: tuple[str, ...], linked: Path) -> dict[str, object]:
    """Prove binding references and native/linked definitions for a direct route."""
    if route == "prik-adapted":
        return {}
    object_symbols = _compiled_object_symbols(workdir, files)
    binding_object = _one_direct_symbol_object(
        object_symbols,
        expected_kinds=frozenset({"U"}),
        description="direct Python binding object",
        relationship="refers to",
    )
    native_object = _one_direct_symbol_object(
        object_symbols,
        expected_kinds=frozenset({"T", "W"}),
        description="direct native object",
        relationship="defines",
    )
    _require_symbol_kinds(
        binding_object,
        object_symbols[binding_object],
        expected_kinds=frozenset({"U"}),
        relationship="refer to",
    )
    _require_symbol_kinds(
        native_object,
        object_symbols[native_object],
        expected_kinds=frozenset({"T", "W"}),
        relationship="define",
    )
    _require_symbol_kinds(
        linked,
        _global_symbols(linked),
        expected_kinds=frozenset({"T", "W"}),
        relationship="export",
    )
    return {
        "binding_direct_symbol_object": binding_object.relative_to(workdir).as_posix(),
        "binding_direct_symbol_references": DIRECT_SYMBOLS,
        "native_direct_symbol_object": native_object.relative_to(workdir).as_posix(),
        "native_direct_symbol_definitions": DIRECT_SYMBOLS,
        "linked_direct_symbol_definitions": DIRECT_SYMBOLS,
    }


def artifact_report(route: Route, workdir: Path) -> dict[str, object]:
    """Validate and report generated/compiled membership outside any timer."""
    files = tuple(sorted(path.relative_to(workdir).as_posix() for path in workdir.rglob("*") if path.is_file()))
    names = tuple(Path(path).name for path in files)
    adapter_sources = tuple(path for path in files if Path(path).name.startswith("bind_c_") and path.endswith(".f90"))
    f2py_wrapper_sources = tuple(
        path
        for path in files
        if "f2pywrappers" in Path(path).name.casefold() and Path(path).suffix.casefold().startswith(".f")
    )
    if route == "prik-direct" and adapter_sources:
        raise RuntimeError(f"PRIK direct preflight found generated user adapters: {adapter_sources!r}")
    if route == "prik-adapted" and not adapter_sources:
        raise RuntimeError("PRIK adapted preflight found no generated Fortran adapter source")
    if route == "f2py-direct" and f2py_wrapper_sources:
        raise RuntimeError(f"f2py direct preflight found generated Fortran wrapper sources: {f2py_wrapper_sources!r}")
    if route == "f2py-direct" and not any(name.endswith("module.c") for name in names):
        raise RuntimeError("f2py direct preflight found no generated Python C/API module")
    if route.startswith("prik-") and not any(name.endswith("_wrapper.c") for name in names):
        raise RuntimeError("PRIK preflight found no generated Python C binding")
    linked = extension_path(route, workdir)
    report = {
        "route": route_action(route),
        "wrapper_mode": wrapper_mode(route),
        "native_source": native_source(route).name,
        "generated_fortran_adapter_sources": adapter_sources,
        "f2py_fortran_wrapper_sources": f2py_wrapper_sources,
        "generated_c_sources": tuple(path for path in files if path.endswith(".c")),
        "compiled_objects": tuple(path for path in files if path.endswith(".o")),
        "linked_extension": linked.relative_to(workdir).as_posix(),
    }
    report.update(_direct_symbol_report(route, workdir, files, linked))
    return report


def load_extension(route: Route, workdir: Path):
    """Load an isolated extension directly from a completed build."""
    path = extension_path(route, workdir)
    spec = importlib.util.spec_from_file_location(module_name(route), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load extension specification from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_api(api, route: Route) -> None:
    """Check common inputs/values and each tool's natural scalar result class."""
    assert api.noop() is None
    results = (
        api.add_scalars(np.float64(1.25), np.float64(2.75)),
        api.add_scalars_out(np.float64(1.25), np.float64(2.75)),
    )
    expected_type = float if route == "f2py-direct" else np.float64
    for result in results:
        assert type(result) is expected_type
        assert result == np.float64(4.0)


def verify_build(route: Route, workdir: Path) -> dict[str, object]:
    """Validate artifacts, importability, and runtime results outside timing."""
    report = artifact_report(route, workdir)
    check_api(load_extension(route, workdir), route)
    return report


def compact_artifact_membership(report: Mapping[str, object]) -> str:
    """Return stable route facts suitable for scalar pyperf metadata."""
    adapters = len(tuple(report["generated_fortran_adapter_sources"]))
    f2py_wrappers = len(tuple(report["f2py_fortran_wrapper_sources"]))
    c_sources = len(tuple(report["generated_c_sources"]))
    objects = len(tuple(report["compiled_objects"]))
    direct_symbols = len(tuple(report.get("linked_direct_symbol_definitions", ())))
    return (
        f"generated_c={c_sources};fortran_adapters={adapters};"
        f"f2py_fortran_wrappers={f2py_wrappers};objects={objects};direct_symbols={direct_symbols}"
    )


def write_preflight_report(reports: Mapping[str, Mapping[str, object]], path: Path) -> None:
    """Write the complete untimed artifact/correctness record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reports, indent=2, sort_keys=True) + "\n", encoding="utf-8")
