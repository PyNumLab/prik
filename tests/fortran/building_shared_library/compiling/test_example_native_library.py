"""Focused checks for the copyable example native-library builder."""

from __future__ import annotations

from pathlib import Path

from examples import native_library


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
