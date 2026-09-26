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


RUNTIME_GROUPS = (
    "calls",
    "vector-latency",
    "vector-bulk",
    "matrix-sum-latency",
    "matrix-sum-bulk",
    "matrix-update-latency",
    "matrix-update-bulk",
)


def _run_runtime_group(monkeypatch: pytest.MonkeyPatch, group: str) -> dict[str, object]:
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
    return observed


def test_runtime_groups_partition_all_cases_and_sample_latency_cases_more(monkeypatch: pytest.MonkeyPatch) -> None:
    every_case = _run_runtime_group(monkeypatch, "all")["names"]
    groups = {group: _run_runtime_group(monkeypatch, group) for group in RUNTIME_GROUPS}

    # The reduced per-group budget still measures every public case exactly once, in table order.
    assert [name for group in RUNTIME_GROUPS for name in groups[group]["names"]] == every_case
    for observed in groups.values():
        assert observed["metadata"]["cpu_model_name"] == "Published Benchmark CPU"
        assert observed["metadata"]["runtime_order_pass"] == "prik-first"
        assert observed["metadata"]["runtime_order_protocol"] == "balanced_ab_ba"

    # Nanosecond-scale latency cases are the noisy ones and get more processes and values than bulk cases.
    samples = {group: observed["processes"] * observed["values"] for group, observed in groups.items()}
    latency = [samples[group] for group in RUNTIME_GROUPS if group == "calls" or group.endswith("-latency")]
    bulk = [samples[group] for group in RUNTIME_GROUPS if group.endswith("-bulk")]
    assert min(latency) > max(bulk)


def test_run_script_balances_order_passes_and_keeps_direct_results_separate() -> None:
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

    # The direct-entrypoint cohort is preflighted, runs its own balanced passes,
    # and merges into per-route results that never join the default population.
    assert "python3 direct_preflight.py" in source
    assert "python3 direct_build_time.py" in source
    assert "direct_runtime.py" in source
    assert "direct_runtime_passes=(forward reverse)" in source
    assert "direct_routes=(prik-adapted f2py-direct prik-direct)" in source
    assert '--output "results/$direct_route.json"' in source


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
