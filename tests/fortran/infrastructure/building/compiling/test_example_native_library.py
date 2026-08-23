"""Focused checks for the copyable example native-library builder."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from examples import native_library


@pytest.mark.parametrize("example", ("blas", "lapack"))
def test_aggregate_example_build_restores_the_workspace(example: str) -> None:
    script = (native_library.EXAMPLES_ROOT / example / "build_all.sh").read_text(encoding="utf-8")
    lines = script.splitlines()

    f2py_build = next(index for index, line in enumerate(lines) if "build_f2py.sh" in line)
    restore_workspace = lines.index('cd "$EXAMPLE_WORKSPACE"')
    python_path_export = next(index for index, line in enumerate(lines) if line.startswith("export PYTHONPATH="))
    assert f2py_build < restore_workspace < python_path_export


def test_native_cache_preserves_module_files_for_wrapper_compilation(tmp_path: Path, monkeypatch) -> None:
    sources = (
        native_library.LAPACK_SOURCE_ROOT / "la_constants.f90",
        native_library.LAPACK_SOURCE_ROOT / "la_xisnan.F90",
        native_library.LAPACK_SOURCE_ROOT / "dlamch.f",
    )

    def compile_source(_compiler: str, source: Path, native_object: Path, module_dir: Path) -> None:
        native_object.parent.mkdir(parents=True, exist_ok=True)
        native_object.touch()
        if source.stem.lower() in native_library.NATIVE_MODULE_SOURCE_STEMS:
            (module_dir / f"{source.stem.lower()}.mod").touch()

    def compile_independent_sources(
        compiler: str,
        selected_sources: tuple[Path, ...],
        objects_dir: Path,
        module_dir: Path,
        _jobs: int,
    ) -> None:
        for source in selected_sources:
            compile_source(
                compiler,
                source,
                native_library._cached_object_path(objects_dir, source),
                module_dir,
            )

    monkeypatch.setattr(native_library, "_compile_source", compile_source)
    monkeypatch.setattr(native_library, "_compile_independent_sources", compile_independent_sources)

    cache_dir = tmp_path / "native"
    objects = native_library._cached_objects(cache_dir, sources, "gfortran", 2)

    assert all(path.is_file() for path in objects)
    assert (cache_dir / "modules" / "la_constants.mod").is_file()
    assert (cache_dir / "modules" / "la_xisnan.mod").is_file()

    def fail_if_recompiled(*_args) -> None:
        raise AssertionError("warm cache recompiled a module")

    monkeypatch.setattr(native_library, "_compile_source", fail_if_recompiled)
    assert native_library._cached_objects(cache_dir, sources, "gfortran", 2) == objects


@pytest.mark.parametrize(
    ("platform", "library", "expected_dependencies", "suffix"),
    (
        ("linux", "blas", (), ".so"),
        ("linux", "lapack", ("-llapack", "-lblas"), ".so"),
        ("darwin", "blas", (), ".dylib"),
        ("darwin", "lapack", ("-llapack", "-lblas"), ".dylib"),
    ),
)
def test_shared_example_library_links_its_native_dependencies(
    tmp_path: Path,
    monkeypatch,
    platform: str,
    library: str,
    expected_dependencies: tuple[str, ...],
    suffix: str,
) -> None:
    commands = []

    def run(command: tuple[str, ...], *, check: bool) -> None:
        assert check is True
        commands.append(command)
        Path(command[3]).touch()

    monkeypatch.setattr(native_library.subprocess, "run", run)
    monkeypatch.setattr(native_library.sys, "platform", platform)
    archive = tmp_path / f"libprik_full_{library}.a"
    archive.touch()

    shared_library = native_library._cached_shared_library(tmp_path, library, archive, "gfortran")

    assert shared_library.is_file()
    assert shared_library.suffix == suffix
    if platform == "darwin":
        expected_link_flags = (
            f"-Wl,-install_name,{shared_library}",
            "-Wl,-force_load",
            str(archive),
        )
        shared_mode = "-dynamiclib"
    else:
        expected_link_flags = ("-Wl,--whole-archive", str(archive), "-Wl,--no-whole-archive")
        shared_mode = "-shared"
    assert commands == [
        (
            "gfortran",
            shared_mode,
            "-o",
            str(tmp_path / f"{shared_library.name}.{os.getpid()}.tmp"),
            *expected_link_flags,
            *expected_dependencies,
        )
    ]


@pytest.mark.parametrize(
    ("filename", "expected"),
    (("libprik_full_blas.so", "prik_full_blas"), ("libprik_full_lapack.dylib", "prik_full_lapack")),
)
def test_example_linker_name_accepts_linux_and_macos_shared_libraries(filename: str, expected: str) -> None:
    assert native_library.linker_name(Path(filename)) == expected
