"""Shared fixtures and structural enforcement for final Fortran tests."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER_ENV = "PRIK_TEST_FORTRAN_COMPILER"
COMPILER_OPTION = "--prik-fortran-compiler"


@dataclass(frozen=True)
class ToolchainSmokeCase:
    """Required metadata for one exact portable compiled test node."""

    mechanism: str
    build_fixture: str


TOOLCHAIN_SMOKE_CASES = {
    (
        "tests/fortran/data_types/end_to_end/test_primitive_scalar_runtime.py::"
        "test_scalar_kind_coverage_uses_compiler_probed_wrapper_types[source]"
    ): ToolchainSmokeCase("scalar_module_procedure", "compiled_scalar_kind_module"),
    (
        "tests/fortran/arrays/end_to_end/test_layout_and_strided_arrays.py::"
        "test_rank2_contiguous_contract_requires_fortran_contiguous[source]"
    ): ToolchainSmokeCase("numpy_array_layout", "compiled_multid_array_module"),
    (
        "tests/fortran/strings/end_to_end/test_character_edge_cases.py::"
        "test_fortran_character_edge_cases_follow_copy_in_copy_out_policy[source]"
    ): ToolchainSmokeCase("string_copy_in_out", "compiled_character_edges_module"),
    (
        "tests/fortran/derived_types/end_to_end/test_borrowed_components.py::"
        "test_borrowed_child_wrapper_never_finalizes_native_component[source]"
    ): ToolchainSmokeCase("derived_type_lifecycle", "compiled_borrowed_component_module"),
    (
        "tests/fortran/allocatables/end_to_end/test_allocatable_handles.py::"
        "test_allocatable_module_fields_and_results_expose_lifetime_safe_handles[source]"
    ): ToolchainSmokeCase("allocatable_ownership", "compiled_allocatable_module"),
    (
        "tests/fortran/callbacks/end_to_end/test_scalar_callbacks.py::"
        "test_immediate_scalar_dummy_procedure_calls_python_callback[source]"
    ): ToolchainSmokeCase("callback_boundary", "compiled_scalar_callback_module"),
    (
        "tests/fortran/generic_interfaces/end_to_end/test_generic_interfaces.py::"
        "test_fortran_generic_interfaces_dispatch_in_generated_c_extension[source]"
    ): ToolchainSmokeCase("generic_overload_dispatch", "compiled_generic_module"),
    (
        "tests/fortran/infrastructure/semantic_pyi/end_to_end/test_authoritative_contract_runtime.py::"
        "test_generated_contract_rebuilds_without_native_source_fallback"
    ): ToolchainSmokeCase("source_generated_pyi_rebuild", "compiled_contract_rebuild"),
}

_CONDITIONAL_MARKS = {"skip", "skipif", "xfail"}
_PLATFORM_MARKS = {
    "aarch64",
    "arm64",
    "darwin",
    "gfortran",
    "ifort",
    "ifx",
    "linux",
    "macos",
    "nvfortran",
    "flang",
    "windows",
    "x86_64",
}


@pytest.fixture(params=("source", "generated-pyi"), ids=("source", "generated-pyi"))
def pyi_parity_build_mode(request: pytest.FixtureRequest) -> str:
    """Select an equivalent source or generated-contract wrapper build."""

    return request.param


def _compiler_was_requested_explicitly(config: pytest.Config) -> bool:
    if COMPILER_ENV in os.environ:
        return True
    return any(
        str(argument) == COMPILER_OPTION or str(argument).startswith(f"{COMPILER_OPTION}=")
        for argument in config.invocation_params.args
    )


def _resolve_compiler(config: pytest.Config) -> None:
    requested = config.getoption(COMPILER_OPTION)
    strict = config.getoption("--require-toolchain-smoke")
    explicit = _compiler_was_requested_explicitly(config)
    resolved = shutil.which(requested)
    if resolved is None:
        if strict or explicit:
            raise pytest.UsageError(f"requested Fortran compiler is unavailable: {requested}")
        config._prik_fortran_compiler = None
        config._prik_fortran_compiler_version = None
        return

    version_result = subprocess.run(
        [resolved, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    version_lines = (version_result.stdout or version_result.stderr).splitlines()
    if version_result.returncode != 0 or not version_lines:
        message = f"requested Fortran compiler cannot report its version: {resolved}"
        if strict or explicit:
            raise pytest.UsageError(message)
        config._prik_fortran_compiler = None
        config._prik_fortran_compiler_version = None
        return

    compiler = str(Path(resolved).resolve())
    os.environ[COMPILER_ENV] = compiler
    config._prik_fortran_compiler = compiler
    config._prik_fortran_compiler_version = version_lines[0]


def pytest_configure(config: pytest.Config) -> None:
    _resolve_compiler(config)
    config._prik_toolchain_smoke_runtime_failures = set()
    config._prik_toolchain_smoke_report = ()


def pytest_report_header(config: pytest.Config) -> str:
    compiler = config._prik_fortran_compiler
    if compiler is None:
        return "Fortran compiler: unavailable (compiled tests may skip)"
    return f"Fortran compiler: {compiler} ({config._prik_fortran_compiler_version})"


def _relative_test_path(item: pytest.Item) -> Path:
    return Path(str(item.path)).resolve().relative_to(REPO_ROOT)


def _is_fortran_end_to_end(item: pytest.Item) -> bool:
    parts = _relative_test_path(item).parts
    return len(parts) >= 5 and parts[:2] == ("tests", "fortran") and "end_to_end" in parts[3:-1]


def _is_platform_mark(name: str) -> bool:
    return name in _PLATFORM_MARKS or name.startswith(("compiler_", "os_", "platform_"))


def _validate_smoke_item(item: pytest.Item, errors: list[str]) -> None:
    marker = item.get_closest_marker("toolchain_smoke")
    if marker is None:
        return
    if not _is_fortran_end_to_end(item):
        errors.append(f"toolchain_smoke is outside a Fortran end_to_end directory: {item.nodeid}")
    if item.get_closest_marker("fortran_end_to_end") is None:
        errors.append(f"toolchain_smoke lacks fortran_end_to_end: {item.nodeid}")
    if marker.args or set(marker.kwargs) != {"mechanism", "build_fixture"}:
        errors.append(f"toolchain_smoke metadata has the wrong schema: {item.nodeid}")
        return
    mechanism = marker.kwargs["mechanism"]
    build_fixture = marker.kwargs["build_fixture"]
    if not isinstance(mechanism, str) or not mechanism.strip():
        errors.append(f"toolchain_smoke mechanism is empty: {item.nodeid}")
    if not isinstance(build_fixture, str) or not build_fixture.strip():
        errors.append(f"toolchain_smoke build_fixture is empty: {item.nodeid}")
    elif build_fixture not in item.fixturenames:
        errors.append(f"toolchain_smoke fixture {build_fixture!r} is not in the closure: {item.nodeid}")
    prohibited = sorted(
        mark.name
        for mark in item.iter_markers()
        if mark.name in _CONDITIONAL_MARKS or mark.name == "real_library" or _is_platform_mark(mark.name)
    )
    if prohibited:
        errors.append(f"toolchain_smoke has prohibited marks {prohibited}: {item.nodeid}")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        case = TOOLCHAIN_SMOKE_CASES.get(item.nodeid)
        if case is not None:
            item.add_marker(
                pytest.mark.toolchain_smoke(
                    mechanism=case.mechanism,
                    build_fixture=case.build_fixture,
                )
            )

    errors = []
    for item in items:
        is_end_to_end = _is_fortran_end_to_end(item)
        has_end_to_end_mark = item.get_closest_marker("fortran_end_to_end") is not None
        if is_end_to_end != has_end_to_end_mark:
            errors.append(
                f"fortran_end_to_end path/marker mismatch ({is_end_to_end=}, {has_end_to_end_mark=}): {item.nodeid}"
            )
        _validate_smoke_item(item, errors)

    if errors:
        raise pytest.UsageError("Fortran test structure violations:\n" + "\n".join(sorted(errors)))


def pytest_collection_finish(session: pytest.Session) -> None:
    smoke_items = [item for item in session.items if item.get_closest_marker("toolchain_smoke") is not None]
    session.config._prik_toolchain_smoke_report = tuple(
        sorted(
            (
                item.nodeid,
                item.get_closest_marker("toolchain_smoke").kwargs["mechanism"],
                item.get_closest_marker("toolchain_smoke").kwargs["build_fixture"],
            )
            for item in smoke_items
        )
    )
    if not session.config.getoption("--require-toolchain-smoke"):
        return
    if not smoke_items:
        session.shouldfail = "strict toolchain smoke selected no tests"
        return
    non_smoke = sorted(item.nodeid for item in session.items if item not in smoke_items)
    if non_smoke:
        session.shouldfail = "strict toolchain smoke selected non-smoke nodes: " + ", ".join(non_smoke)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if not item.config.getoption("--require-toolchain-smoke"):
        return
    if report.skipped or getattr(report, "wasxfail", None):
        item.config._prik_toolchain_smoke_runtime_failures.add(f"{report.nodeid} [{report.when}] {report.outcome}")


def pytest_sessionfinish(session: pytest.Session) -> None:
    failures = session.config._prik_toolchain_smoke_runtime_failures
    if session.config.getoption("--require-toolchain-smoke") and failures:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, config: pytest.Config) -> None:
    if not config.getoption("--require-toolchain-smoke"):
        return
    terminalreporter.write_sep("=", "toolchain smoke selection")
    compiler = config._prik_fortran_compiler
    terminalreporter.write_line(f"compiler: {compiler} ({config._prik_fortran_compiler_version})")
    for nodeid, mechanism, build_fixture in config._prik_toolchain_smoke_report:
        terminalreporter.write_line(f"{nodeid} | mechanism={mechanism} | build_fixture={build_fixture}")
    for failure in sorted(config._prik_toolchain_smoke_runtime_failures):
        terminalreporter.write_line(f"strict failure: {failure}")
