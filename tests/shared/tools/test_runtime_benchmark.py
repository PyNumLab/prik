from __future__ import annotations

import importlib
from pathlib import Path
import runpy
from types import SimpleNamespace

import pyperf
import pytest


RUNTIME_SCRIPT = Path("benchmarks/runtime.py")


@pytest.mark.parametrize(
    ("group", "processes", "values", "expected_names"),
    [
        ("calls", 64, 4, ("call.noop", "call.add_scalars")),
        ("vector-latency", 64, 4, ("array.increment_vector.n=1", "array.increment_vector.n=16")),
        ("vector-bulk", 16, 3, ("array.increment_vector.n=1024", "array.increment_vector.n=1000000")),
        ("matrix-sum-latency", 64, 4, ("matrix.sum.4x4.order=F",)),
        (
            "matrix-sum-bulk",
            4,
            3,
            ("matrix.sum.32x32.order=F", "matrix.sum.256x256.order=F", "matrix.sum.1024x1024.order=F"),
        ),
        ("matrix-update-latency", 64, 4, ("matrix.update.4x4.order=F", "matrix.update.256x256.order=F")),
        ("matrix-update-bulk", 32, 3, ("matrix.update.1024x1024.order=F",)),
    ],
)
def test_runtime_groups_assign_more_samples_only_to_noisy_cases(
    monkeypatch: pytest.MonkeyPatch,
    group: str,
    processes: int,
    values: int,
    expected_names: tuple[str, ...],
) -> None:
    observed: dict[str, object] = {"names": []}

    class FakeRunner:
        def __init__(self, **kwargs):
            observed.update(kwargs)

        def timeit(self, name: str, **_kwargs) -> None:
            observed["names"].append(name)

    kernels = SimpleNamespace(
        noop=lambda: None,
        add_scalars=lambda *_args: None,
        increment_vector=lambda *_args: None,
        sum_matrix=lambda *_args: None,
        matrix_update=lambda *_args: None,
    )
    monkeypatch.setenv("BINDING_TOOL", "x2py")
    monkeypatch.setenv("X2PY_RUNTIME_BENCHMARK_GROUP", group)
    monkeypatch.setenv("X2PY_BENCHMARK_CPU_MODEL", "Published Benchmark CPU")
    monkeypatch.setattr(importlib, "import_module", lambda _name: SimpleNamespace(kernels=kernels))
    monkeypatch.setattr(pyperf, "Runner", FakeRunner)

    runpy.run_path(RUNTIME_SCRIPT, run_name="__main__")

    assert observed["processes"] == processes
    assert observed["values"] == values
    assert observed["metadata"]["cpu_model_name"] == "Published Benchmark CPU"
    assert observed["names"] == list(expected_names)


def test_run_script_appends_runtime_groups_in_public_table_order() -> None:
    source = Path("benchmarks/run.sh").read_text(encoding="utf-8")

    positions = [
        source.index(group)
        for group in (
            "calls",
            "vector-latency",
            "vector-bulk",
            "matrix-sum-latency",
            "matrix-sum-bulk",
            "matrix-update-latency",
            "matrix-update-bulk",
        )
    ]
    assert positions == sorted(positions)
    assert 'result_args=(--append "results/$binding_tool.json")' in source
    assert "X2PY_BENCHMARK_CPU_MODEL" in source
