from pathlib import Path
from types import SimpleNamespace

from tools import warm_real_library_native_cache


def test_warm_real_library_native_cache_defaults_to_all_libraries(monkeypatch, capsys):
    calls = []

    def cached_native_shared_library(library: str) -> Path:
        calls.append(library)
        return Path("/cache") / f"libx2py_full_{library}.so"

    monkeypatch.setattr(
        warm_real_library_native_cache,
        "_real_library_cache_module",
        lambda: SimpleNamespace(
            _native_cache_root=lambda: Path("/cache"),
            _cached_native_shared_library=cached_native_shared_library,
        ),
    )

    assert warm_real_library_native_cache.main([]) == 0

    assert calls == ["blas", "lapack"]
    assert capsys.readouterr().out.splitlines() == [
        "native cache root: /cache",
        "blas: /cache/libx2py_full_blas.so",
        "lapack: /cache/libx2py_full_lapack.so",
    ]


def test_warm_real_library_native_cache_accepts_selected_libraries(monkeypatch, capsys):
    calls = []

    def cached_native_shared_library(library: str) -> Path:
        calls.append(library)
        return Path("/cache") / f"libx2py_full_{library}.so"

    monkeypatch.setattr(
        warm_real_library_native_cache,
        "_real_library_cache_module",
        lambda: SimpleNamespace(
            _native_cache_root=lambda: Path("/cache"),
            _cached_native_shared_library=cached_native_shared_library,
        ),
    )

    assert warm_real_library_native_cache.main(["lapack"]) == 0

    assert calls == ["lapack"]
    assert capsys.readouterr().out.splitlines() == [
        "native cache root: /cache",
        "lapack: /cache/libx2py_full_lapack.so",
    ]


def test_warm_real_library_native_cache_rejects_unknown_library(monkeypatch):
    monkeypatch.setattr(
        warm_real_library_native_cache,
        "_real_library_cache_module",
        lambda: SimpleNamespace(
            _native_cache_root=lambda: Path("/cache"),
            _cached_native_shared_library=lambda library: Path("/cache") / library,
        ),
    )

    try:
        warm_real_library_native_cache.main(["unknown"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected invalid library to stop argument parsing")
