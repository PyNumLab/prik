"""Validate the exact portable toolchain smoke selection."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.fortran.conftest import TOOLCHAIN_SMOKE_CASES

REPO_ROOT = Path(__file__).parents[3]
FEATURE_ROOT = REPO_ROOT / "tests/fortran"
CONTRACT_LEDGER = REPO_ROOT / "tests/fortran/CONTRACT_COVERAGE.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
REQUIRED_MECHANISMS = {
    "allocatable_ownership",
    "callback_boundary",
    "derived_type_lifecycle",
    "generic_overload_dispatch",
    "numpy_array_layout",
    "scalar_module_procedure",
    "source_generated_pyi_rebuild",
    "string_copy_in_out",
}
PROHIBITED_PATH_PARTS = {
    "platform",
    "platforms",
    "profile",
    "profiles",
}


def _collect(*args: str) -> tuple[set[str], str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    nodes = {
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("tests/fortran/") and "::" in line and " | mechanism=" not in line
    }
    return nodes, result.stdout


def test_toolchain_smoke_marker_is_registered_with_the_exact_contract() -> None:
    expected = (
        '"toolchain_smoke: portable compiled Fortran end-to-end cases reused across compiler, OS, '
        'and architecture lanes"'
    )
    assert expected in PYPROJECT.read_text(encoding="utf-8")


def test_toolchain_smoke_manifest_has_the_required_mechanisms_and_build_budget() -> None:
    mechanisms = {case.mechanism for case in TOOLCHAIN_SMOKE_CASES.values()}
    build_fixtures = {case.build_fixture for case in TOOLCHAIN_SMOKE_CASES.values()}

    assert mechanisms == REQUIRED_MECHANISMS
    assert len(mechanisms) == len(TOOLCHAIN_SMOKE_CASES)
    assert 6 <= len(build_fixtures) <= 8
    assert len(build_fixtures) == len(TOOLCHAIN_SMOKE_CASES)


def test_toolchain_smoke_manifest_uses_only_feature_end_to_end_nodes() -> None:
    for nodeid in TOOLCHAIN_SMOKE_CASES:
        path_text, separator, test_name = nodeid.partition("::")
        path = Path(path_text)
        assert separator and test_name
        assert path.parts[:2] == ("tests", "fortran")
        assert path.parts[2] not in {"_support", "infrastructure"}
        assert "end_to_end" in path.parts
        assert PROHIBITED_PATH_PARTS.isdisjoint(path.parts)
        assert (REPO_ROOT / path).is_file()


def test_every_toolchain_smoke_node_is_permanent_contract_evidence() -> None:
    ledger = CONTRACT_LEDGER.read_text(encoding="utf-8")
    for nodeid in TOOLCHAIN_SMOKE_CASES:
        assert f"`{nodeid}`" in ledger


def test_toolchain_smoke_collects_exactly_the_manifest_and_reports_it_in_sorted_order() -> None:
    nodes, output = _collect(
        str(FEATURE_ROOT.relative_to(REPO_ROOT)),
        "-m",
        "toolchain_smoke",
        "--require-toolchain-smoke",
        f"--prik-fortran-compiler={sys.executable}",
    )
    assert nodes == set(TOOLCHAIN_SMOKE_CASES)

    reported_nodes = [
        line.split(" | mechanism=", maxsplit=1)[0]
        for line in output.splitlines()
        if line.startswith("tests/fortran/") and " | mechanism=" in line
    ]
    assert reported_nodes == sorted(TOOLCHAIN_SMOKE_CASES)


def test_toolchain_smoke_nodes_are_in_the_ordinary_end_to_end_suite() -> None:
    ordinary_nodes, _output = _collect(
        str(FEATURE_ROOT.relative_to(REPO_ROOT)),
        "-m",
        "fortran_end_to_end",
    )
    assert set(TOOLCHAIN_SMOKE_CASES) <= ordinary_nodes


def test_explicit_missing_toolchain_smoke_compiler_is_an_error() -> None:
    missing = REPO_ROOT / ".missing-prik-fortran-compiler"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            str(FEATURE_ROOT.relative_to(REPO_ROOT)),
            "-m",
            "toolchain_smoke",
            "--require-toolchain-smoke",
            f"--prik-fortran-compiler={missing}",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == pytest_usage_error_exit_code()
    assert f"requested Fortran compiler is unavailable: {missing}" in result.stderr


def pytest_usage_error_exit_code() -> int:
    """Keep the subprocess assertion readable without importing pytest internals."""

    return 4
