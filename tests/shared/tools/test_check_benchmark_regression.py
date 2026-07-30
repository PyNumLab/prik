"""Tests for the staged benchmark artifact comparison policy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.check_benchmark_regression import compare_reports, load_benchmark_medians, main

pytestmark = pytest.mark.skip(reason="Benchmark regression policy tests are parked until benchmark adoption resumes.")


def _write_report(path: Path, *benchmarks: tuple[str, float]) -> Path:
    path.write_text(
        json.dumps(
            {
                "benchmarks": [
                    {
                        "fullname": name,
                        "stats": {"median": benchmark_median},
                    }
                    for name, benchmark_median in benchmarks
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_load_benchmark_medians_reads_benchmark_json(tmp_path: Path):
    report = _write_report(tmp_path / "current.json", ("test_fast", 0.1), ("test_slow", 0.2))

    assert load_benchmark_medians(report) == {"test_fast": 0.1, "test_slow": 0.2}


def test_compare_reports_uses_history_median_and_readiness_threshold(tmp_path: Path):
    current = _write_report(tmp_path / "current.json", ("test_parse", 0.12))
    baselines = [
        _write_report(tmp_path / f"baseline-{index}.json", ("test_parse", value))
        for index, value in enumerate([0.09, 0.10, 0.11])
    ]

    [comparison] = compare_reports(current, baselines, threshold_percent=15.0, min_baselines=3)

    assert comparison.baseline_median == 0.10
    assert comparison.baseline_count == 3
    assert comparison.ready is True
    assert comparison.slowdown_percent == pytest.approx(20.0)
    assert comparison.regressed is True


def test_main_keeps_advisory_mode_non_blocking_until_history_is_ready(tmp_path: Path):
    current = _write_report(tmp_path / "current.json", ("test_parse", 0.12))
    baseline = _write_report(tmp_path / "baseline.json", ("test_parse", 0.10))

    assert main([str(current), str(baseline)]) == 0
    assert main([str(current), str(baseline), "--require-ready"]) == 1
    assert (
        main(
            [
                str(current),
                str(baseline),
                "--min-baselines",
                "1",
                "--fail-on-regression",
            ]
        )
        == 1
    )


def test_load_benchmark_medians_rejects_invalid_report(tmp_path: Path):
    report = tmp_path / "invalid.json"
    report.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a benchmarks list"):
        load_benchmark_medians(report)

    zero_median = _write_report(tmp_path / "zero.json", ("test_parse", 0.0))
    with pytest.raises(ValueError, match="invalid benchmark entry"):
        load_benchmark_medians(zero_median)


def test_compare_reports_rejects_invalid_policy_arguments(tmp_path: Path):
    current = _write_report(tmp_path / "current.json", ("test_parse", 0.1))

    with pytest.raises(ValueError, match="must be non-negative"):
        compare_reports(current, [], threshold_percent=-1)
    with pytest.raises(ValueError, match="must be positive"):
        compare_reports(current, [], min_baselines=0)
