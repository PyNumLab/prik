from pathlib import Path
from types import SimpleNamespace

from tools import warm_real_library_native_cache


def test_warm_real_library_native_cache_defaults_to_all_libraries(monkeypatch, capsys):
    calls = []

    def build_reference_library(library: str):
        calls.append(library)
        return SimpleNamespace(shared_library=Path("/cache") / f"libprik_full_{library}.so")

    monkeypatch.setattr(
        warm_real_library_native_cache,
        "_native_library_module",
        lambda: SimpleNamespace(
            native_cache_root=lambda: Path("/cache"),
            build_reference_library=build_reference_library,
        ),
    )

    assert warm_real_library_native_cache.main([]) == 0

    assert calls == ["blas", "lapack"]
    assert capsys.readouterr().out.splitlines() == [
        "native cache root: /cache",
        "blas: /cache/libprik_full_blas.so",
        "lapack: /cache/libprik_full_lapack.so",
    ]


def test_warm_real_library_native_cache_accepts_selected_libraries(monkeypatch, capsys):
    calls = []

    def build_reference_library(library: str):
        calls.append(library)
        return SimpleNamespace(shared_library=Path("/cache") / f"libprik_full_{library}.so")

    monkeypatch.setattr(
        warm_real_library_native_cache,
        "_native_library_module",
        lambda: SimpleNamespace(
            native_cache_root=lambda: Path("/cache"),
            build_reference_library=build_reference_library,
        ),
    )

    assert warm_real_library_native_cache.main(["lapack"]) == 0

    assert calls == ["lapack"]
    assert capsys.readouterr().out.splitlines() == [
        "native cache root: /cache",
        "lapack: /cache/libprik_full_lapack.so",
    ]


def test_warm_real_library_native_cache_rejects_unknown_library(monkeypatch):
    monkeypatch.setattr(
        warm_real_library_native_cache,
        "_native_library_module",
        lambda: SimpleNamespace(
            native_cache_root=lambda: Path("/cache"),
            build_reference_library=lambda library: SimpleNamespace(shared_library=Path("/cache") / library),
        ),
    )

    try:
        warm_real_library_native_cache.main(["unknown"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected invalid library to stop argument parsing")
