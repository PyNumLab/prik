from __future__ import annotations

import importlib
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pyperf
import pytest


RUNTIME_SCRIPT = Path("benchmarks/runtime.py")


@pytest.mark.parametrize(
    ("group", "processes", "values", "expected_names"),
    [
        ("calls", 16, 4, ("call.noop", "call.add_scalars")),
        ("vector-latency", 16, 4, ("array.increment_vector.n=1", "array.increment_vector.n=16")),
        ("vector-bulk", 4, 3, ("array.increment_vector.n=1024", "array.increment_vector.n=1000000")),
        ("matrix-sum-latency", 16, 4, ("matrix.sum.4x4.order=F",)),
        (
            "matrix-sum-bulk",
            2,
            3,
            ("matrix.sum.32x32.order=F", "matrix.sum.256x256.order=F", "matrix.sum.1024x1024.order=F"),
        ),
        ("matrix-update-latency", 16, 4, ("matrix.update.4x4.order=F", "matrix.update.256x256.order=F")),
        ("matrix-update-bulk", 8, 3, ("matrix.update.1024x1024.order=F",)),
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
    monkeypatch.setenv("BINDING_TOOL", "prik")
    monkeypatch.setenv("PRIK_RUNTIME_BENCHMARK_GROUP", group)
    monkeypatch.setenv("PRIK_RUNTIME_ORDER_PASS", "prik-first")
    monkeypatch.setenv("PRIK_BENCHMARK_CPU_MODEL", "Published Benchmark CPU")
    monkeypatch.setattr(importlib, "import_module", lambda _name: SimpleNamespace(kernels=kernels))
    monkeypatch.setattr(pyperf, "Runner", FakeRunner)

    runpy.run_path(RUNTIME_SCRIPT, run_name="__main__")

    assert observed["processes"] == processes
    assert observed["values"] == values
    assert observed["metadata"]["cpu_model_name"] == "Published Benchmark CPU"
    assert observed["metadata"]["runtime_order_pass"] == "prik-first"
    assert observed["metadata"]["runtime_order_protocol"] == "balanced_ab_ba"
    assert observed["names"] == list(expected_names)


def test_run_script_balances_reduced_runtime_budget_in_public_table_order() -> None:
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
    assert source.index('for runtime_group in "${runtime_groups[@]}"') < source.index(
        'for runtime_pass in "${runtime_passes[@]}"'
    )
    assert "runtime_passes=(prik-first f2py-first)" in source
    assert "binding_tools=(prik f2py)" in source
    assert "binding_tools=(f2py prik)" in source
    assert 'PRIK_RUNTIME_ORDER_PASS="$runtime_pass"' in source
    assert "results/$binding_tool-$runtime_pass.json" in source
    assert '--add "results/$binding_tool-f2py-first.json"' in source
    assert '--output "results/$binding_tool.json"' in source
    assert "PRIK_BUILD_BENCHMARK_RUNS:-4" in source
    assert "PRIK_BENCHMARK_CPU_MODEL" in source


def test_pyperf_merge_preserves_both_runtime_order_passes(tmp_path: Path) -> None:
    pass_paths = []
    for index, order_pass in enumerate(("prik-first", "f2py-first"), 1):
        run = pyperf.Run(
            [float(index), float(index) + 0.1],
            warmups=[(1, float(index))],
            metadata={
                "name": "call.noop",
                "unit": "second",
                "loops": 1,
                "binding_tool": "prik",
                "runtime_order_pass": order_pass,
                "runtime_order_protocol": "balanced_ab_ba",
            },
        )
        suite = pyperf.BenchmarkSuite([pyperf.Benchmark([run])])
        pass_path = tmp_path / f"{order_pass}.json"
        suite.dump(str(pass_path), compact=False)
        pass_paths.append(pass_path)

    merged_path = tmp_path / "merged.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pyperf",
            "convert",
            str(pass_paths[0]),
            "--add",
            str(pass_paths[1]),
            "--output",
            str(merged_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    merged = pyperf.BenchmarkSuite.load(str(merged_path)).get_benchmark("call.noop")
    assert len(merged.get_runs()) == 2
    assert merged.get_nvalue() == 4
    assert merged.get_metadata()["runtime_order_protocol"] == "balanced_ab_ba"
    assert {run.get_metadata()["runtime_order_pass"] for run in merged.get_runs()} == {
        "prik-first",
        "f2py-first",
    }
