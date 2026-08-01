from __future__ import annotations

from datetime import date
from pathlib import Path
from xml.etree import ElementTree

import pyperf
import pytest

from tools.generate_performance_docs import (
    BUILD_SHARED_METADATA,
    _format_factor,
    _format_ratio,
    generate,
    load_snapshot,
    render_chart,
    render_page,
)


COMMON_METADATA = {
    "cpu_affinity": "2",
    "cpu_model_name": "Benchmark CPU C Processor",
    "hostname": "private-runner-name",
    "numpy_version": "2.5.1",
    "perf_version": "2.10.0",
    "platform_details": "Linux-test-x86_64",
    "python_version": "3.12.11 (test build)",
    "unit": "second",
}
TEST_OS = "Test Linux 1.0"


def _write_suite(
    path: Path,
    tool: str,
    benchmarks: list[tuple[str, list[float]]],
    *,
    platform_details: str = "Linux-test-x86_64",
    extra_metadata: dict[str, object] | None = None,
) -> Path:
    suite_benchmarks = []
    for name, values in benchmarks:
        metadata = {
            **COMMON_METADATA,
            "binding_tool": tool,
            "date": "2026-08-01 12:00:00",
            "name": name,
            "platform_details": platform_details,
            **(extra_metadata or {}),
        }
        run = pyperf.Run(values, metadata=metadata, collect_metadata=False)
        suite_benchmarks.append(pyperf.Benchmark([run]))
    pyperf.BenchmarkSuite(suite_benchmarks).dump(str(path), replace=True)
    return path


def _paired_suites(tmp_path: Path) -> tuple[Path, Path]:
    f2py = _write_suite(
        tmp_path / "f2py.json",
        "f2py",
        [
            ("call.noop", [2.0e-6, 2.1e-6, 1.9e-6, 2.05e-6, 1.95e-6]),
            ("call.add_scalars", [0.8e-6, 0.82e-6, 0.78e-6, 0.81e-6, 0.79e-6]),
            ("array.increment_vector.n=1", [1.0e-6, 1.02e-6, 0.98e-6, 1.01e-6, 0.99e-6]),
        ],
    )
    x2py = _write_suite(
        tmp_path / "x2py.json",
        "x2py",
        [
            ("call.noop", [1.0e-6, 1.1e-6, 0.9e-6, 1.05e-6, 0.95e-6]),
            ("call.add_scalars", [1.0e-6, 1.02e-6, 0.98e-6, 1.01e-6, 0.99e-6]),
            ("array.increment_vector.n=1", [0.98e-6, 1.01e-6, 1.0e-6, 1.02e-6, 0.99e-6]),
        ],
    )
    return f2py, x2py


def _paired_build_suites(tmp_path: Path) -> tuple[Path, Path]:
    metadata = {
        "build_runs": 6,
        "build_scope": "clean source-to-extension generation, compilation, and linking",
        "build_warmups": 1,
        "compiler": "/usr/bin/gfortran",
    }
    f2py = _write_suite(
        tmp_path / "f2py-build.json",
        "f2py",
        [
            ("build.small_module", [2.0, 2.1, 1.9, 2.05, 1.95]),
            ("build.full_blas", [10.0, 10.2, 9.8, 10.1, 9.9]),
        ],
        extra_metadata=metadata,
    )
    x2py = _write_suite(
        tmp_path / "x2py-build.json",
        "x2py",
        [
            ("build.small_module", [1.0, 1.1, 0.9, 1.05, 0.95]),
            ("build.full_blas", [12.0, 12.2, 11.8, 12.1, 11.9]),
        ],
        extra_metadata=metadata,
    )
    return f2py, x2py


def _page_template() -> str:
    return """before
<!-- x2py-performance-summary:start -->
old summary
<!-- x2py-performance-summary:end -->
between summary and table
<!-- x2py-performance-table:start -->
old table
<!-- x2py-performance-table:end -->
between table and build
<!-- x2py-performance-build:start -->
old build results
<!-- x2py-performance-build:end -->
between build and environment
<!-- x2py-performance-environment:start -->
old environment
<!-- x2py-performance-environment:end -->
after
"""


def test_load_snapshot_classifies_results_and_formats_public_values(tmp_path: Path) -> None:
    f2py, x2py = _paired_suites(tmp_path)

    snapshot = load_snapshot(
        f2py,
        x2py,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0",
        commit="1234567890abcdef",
    )

    assert [result.outcome for result in snapshot.results] == ["x2py", "f2py", "parity"]
    assert snapshot.results[0].f2py_display == "2.00 µs"
    assert snapshot.results[2].table_label == "Increment vector, 1 element"
    assert snapshot.recorded_date == date(2026, 8, 1)
    assert snapshot.compiler_version == "GNU Fortran 13.3.0"
    assert snapshot.commit == "1234567890ab"
    assert "hostname" not in snapshot.metadata


def test_format_factor_keeps_small_significant_differences_visible() -> None:
    assert _format_factor(1.004) == "1.004\N{MULTIPLICATION SIGN}"
    assert _format_factor(1.04) == "1.04\N{MULTIPLICATION SIGN}"
    assert _format_ratio(0.996) == "0.996\N{MULTIPLICATION SIGN}"


def test_render_page_updates_only_marked_blocks(tmp_path: Path) -> None:
    f2py, x2py = _paired_suites(tmp_path)
    f2py_build, x2py_build = _paired_build_suites(tmp_path)
    snapshot = load_snapshot(
        f2py,
        x2py,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran 13.3.0",
        commit="1234567890abcdef",
    )
    build_snapshot = load_snapshot(
        f2py_build,
        x2py_build,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran 13.3.0",
        commit="1234567890abcdef",
        metadata_keys=BUILD_SHARED_METADATA,
    )

    rendered = render_page(_page_template(), snapshot, build_snapshot)

    assert rendered.startswith("before\n")
    assert rendered.endswith("after\n")
    assert "between summary and table" in rendered
    assert "1 of 3" in rendered
    assert "No significant difference" in rendered
    assert "Small module (1 source, 5 procedures)" in rendered
    assert "Full reference BLAS (155 sources)" in rendered
    assert "mean of 6 clean builds after 1 untimed warm-up" in rendered
    assert "private-runner-name" not in rendered
    assert "CPU: Benchmark CPU &#67; Processor." in rendered
    assert "CPU: Benchmark CPU C Processor." not in rendered
    assert "Operating system: Test Linux 1.0" in rendered
    assert "GNU Fortran 13.3.0" in rendered
    assert "`1234567890ab`" in rendered


def test_render_page_rejects_missing_or_duplicate_markers(tmp_path: Path) -> None:
    f2py, x2py = _paired_suites(tmp_path)
    f2py_build, x2py_build = _paired_build_suites(tmp_path)
    snapshot = load_snapshot(
        f2py,
        x2py,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran 13.3.0",
        commit="1234567890abcdef",
    )
    build_snapshot = load_snapshot(
        f2py_build,
        x2py_build,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran 13.3.0",
        commit="1234567890abcdef",
        metadata_keys=BUILD_SHARED_METADATA,
    )

    with pytest.raises(ValueError, match="exactly one 'summary' marker pair"):
        render_page(
            _page_template().replace("<!-- x2py-performance-summary:end -->", ""),
            snapshot,
            build_snapshot,
        )


def test_render_chart_is_valid_accessible_svg(tmp_path: Path) -> None:
    f2py, x2py = _paired_suites(tmp_path)
    snapshot = load_snapshot(
        f2py,
        x2py,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran 13.3.0",
        commit="1234567890abcdef",
    )

    chart = render_chart(snapshot)
    root = ElementTree.fromstring(chart)

    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"
    assert "no significant difference" in chart
    assert "Geometric mean:" in chart


def test_load_snapshot_rejects_incompatible_platforms(tmp_path: Path) -> None:
    f2py, _x2py = _paired_suites(tmp_path)
    x2py = _write_suite(
        tmp_path / "other-x2py.json",
        "x2py",
        [
            ("call.noop", [1.0e-6, 1.1e-6, 0.9e-6, 1.05e-6, 0.95e-6]),
            ("call.add_scalars", [1.0e-6, 1.02e-6, 0.98e-6, 1.01e-6, 0.99e-6]),
            ("array.increment_vector.n=1", [0.98e-6, 1.01e-6, 1.0e-6, 1.02e-6, 0.99e-6]),
        ],
        platform_details="different-platform",
    )

    with pytest.raises(ValueError, match="disagree on metadata 'platform_details'"):
        load_snapshot(
            f2py,
            x2py,
            operating_system=TEST_OS,
            compiler_version="GNU Fortran 13.3.0",
            commit="12345678",
        )


def test_load_snapshot_rejects_swapped_tool_results(tmp_path: Path) -> None:
    f2py, x2py = _paired_suites(tmp_path)

    with pytest.raises(ValueError, match="expected 'f2py' results, found binding_tool='x2py'"):
        load_snapshot(
            x2py,
            f2py,
            operating_system=TEST_OS,
            compiler_version="GNU Fortran 13.3.0",
            commit="12345678",
        )


def test_generate_writes_page_and_chart(tmp_path: Path) -> None:
    f2py, x2py = _paired_suites(tmp_path)
    f2py_build, x2py_build = _paired_build_suites(tmp_path)
    page = tmp_path / "performance.md"
    chart = tmp_path / "assets/performance.svg"
    page.write_text(_page_template(), encoding="utf-8")

    generate(
        f2py,
        x2py,
        f2py_build,
        x2py_build,
        page,
        chart,
        operating_system=TEST_OS,
        compiler_version="GNU Fortran 13.3.0",
        commit="1234567890abcdef",
        recorded_date=date(2026, 8, 2),
    )

    assert "August 2, 2026" in page.read_text(encoding="utf-8")
    assert chart.is_file()
    ElementTree.parse(chart)


def test_current_performance_page_has_one_complete_marker_pair_per_generated_block() -> None:
    page = Path("docs/user/performance.md").read_text(encoding="utf-8")

    for name in ("summary", "table", "build", "environment"):
        assert page.count(f"<!-- x2py-performance-{name}:start -->") == 1
        assert page.count(f"<!-- x2py-performance-{name}:end -->") == 1


def test_pyperf_is_pinned_for_documentation_and_generator_tests() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert pyproject.count('"pyperf==2.10.0"') == 2
