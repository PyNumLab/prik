from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import warm_real_library_native_cache


def test_warm_real_library_native_cache_builds_selected_or_all_libraries(monkeypatch, capsys):
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

    calls.clear()
    assert warm_real_library_native_cache.main(["lapack"]) == 0
    assert calls == ["lapack"]
    assert capsys.readouterr().out.splitlines() == [
        "native cache root: /cache",
        "lapack: /cache/libprik_full_lapack.so",
    ]

    with pytest.raises(SystemExit) as stopped:
        warm_real_library_native_cache.main(["unknown"])
    assert stopped.value.code == 2
    assert calls == ["lapack"]
