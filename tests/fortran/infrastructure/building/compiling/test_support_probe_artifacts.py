"""Artifact-isolation checks for native capability probes used by tests."""

from pathlib import Path

from tests.fortran._support import wrapper_build


def test_allocatable_result_probe_keeps_fortran_modules_out_of_invocation_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    invocation_dir = tmp_path / "invocation"
    invocation_dir.mkdir()
    monkeypatch.chdir(invocation_dir)
    wrapper_build._supports_maybe_unallocated_function_result.cache_clear()

    wrapper_build._supports_maybe_unallocated_function_result()

    assert not tuple(invocation_dir.glob("*.mod"))
