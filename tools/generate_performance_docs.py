#!/usr/bin/env python3
"""Generate the public Performance snapshot from paired pyperf results."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from html import escape
import math
from pathlib import Path
import re
import subprocess  # nosec B404 - fixed argv commands collect local tool versions
import sys
import textwrap
from typing import Literal

import pyperf
from pyperf._compare import is_significant_benchs


REPOSITORY_ROOT = Path(__file__).parents[1]
DEFAULT_F2PY_RESULTS = REPOSITORY_ROOT / "benchmarks/results/f2py.json"
DEFAULT_X2PY_RESULTS = REPOSITORY_ROOT / "benchmarks/results/x2py.json"
DEFAULT_PAGE = REPOSITORY_ROOT / "docs/user/performance.md"
DEFAULT_CHART = REPOSITORY_ROOT / "docs/user/assets/performance-comparison.svg"
COMPILE_FLAGS = "-O3 -march=native -mtune=native"
TIMES = "\N{MULTIPLICATION SIGN}"
MARKER_NAMES = ("summary", "table", "environment")
SHARED_METADATA = (
    "cpu_affinity",
    "cpu_model_name",
    "numpy_version",
    "perf_version",
    "platform_details",
    "python_version",
)
Outcome = Literal["x2py", "f2py", "parity"]


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    table_label: str
    chart_label: str
    f2py_value: float
    x2py_value: float
    f2py_display: str
    x2py_display: str
    ratio: float
    outcome: Outcome

    @property
    def factor(self) -> float:
        return self.ratio if self.ratio >= 1.0 else 1.0 / self.ratio


@dataclass(frozen=True)
class PerformanceSnapshot:
    results: tuple[BenchmarkResult, ...]
    metadata: dict[str, object]
    recorded_date: date
    compiler_version: str
    commit: str

    @property
    def geometric_mean_ratio(self) -> float:
        return math.exp(sum(math.log(result.ratio) for result in self.results) / len(self.results))

    @property
    def x2py_wins(self) -> tuple[BenchmarkResult, ...]:
        return tuple(result for result in self.results if result.outcome == "x2py")

    @property
    def f2py_wins(self) -> tuple[BenchmarkResult, ...]:
        return tuple(result for result in self.results if result.outcome == "f2py")

    @property
    def parity_results(self) -> tuple[BenchmarkResult, ...]:
        return tuple(result for result in self.results if result.outcome == "parity")


def _format_factor(factor: float) -> str:
    precision = 3 if factor < 1.01 else 2
    return f"{factor:.{precision}f}{TIMES}"


def _format_ratio(ratio: float) -> str:
    precision = 3 if abs(ratio - 1.0) < 0.01 else 2
    return f"{ratio:.{precision}f}{TIMES}"


def _procedure_labels(name: str) -> tuple[str, str]:
    fixed = {
        "call.noop": ("Empty function call", "Empty call"),
        "call.add_scalars": ("Add two scalars", "Add scalars"),
    }
    if name in fixed:
        return fixed[name]

    vector_match = re.fullmatch(r"array\.increment_vector\.n=(\d+)", name)
    if vector_match:
        size = f"{int(vector_match.group(1)):,}"
        return (f"Increment vector, {size} element{'s' if size != '1' else ''}", f"Increment vector · n={size}")

    matrix_match = re.fullmatch(r"matrix\.(sum|update)\.(\d+)x(\d+)\.order=([A-Za-z])", name)
    if matrix_match:
        operation, rows, columns, order = matrix_match.groups()
        title = operation.capitalize()
        shape = f"{int(rows):,}{TIMES}{int(columns):,}"
        return (f"{title} {shape} {order}-order matrix", f"{title} matrix · {shape}")

    readable = name.replace("_", " ").replace(".", " · ")
    return readable, readable


def _outcome(f2py_benchmark: pyperf.Benchmark, x2py_benchmark: pyperf.Benchmark) -> Outcome:
    significant, _score = is_significant_benchs(f2py_benchmark, x2py_benchmark)
    if not significant:
        return "parity"
    return "x2py" if f2py_benchmark.mean() > x2py_benchmark.mean() else "f2py"


def _format_benchmark_value(benchmark: pyperf.Benchmark, value: float) -> str:
    return benchmark.format_value(value).replace(" us", " µs")


def _compatible_metadata(
    f2py_suite: pyperf.BenchmarkSuite,
    x2py_suite: pyperf.BenchmarkSuite,
) -> dict[str, object]:
    f2py_metadata = f2py_suite.get_metadata()
    x2py_metadata = x2py_suite.get_metadata()
    shared: dict[str, object] = {}
    for key in SHARED_METADATA:
        f2py_value = f2py_metadata.get(key)
        x2py_value = x2py_metadata.get(key)
        if f2py_value is None or x2py_value is None:
            raise ValueError(f"paired pyperf results are missing required metadata {key!r}")
        if f2py_value != x2py_value:
            raise ValueError(f"paired pyperf results disagree on metadata {key!r}")
        shared[key] = f2py_value
    return shared


def _validate_suite_identity(suite: pyperf.BenchmarkSuite, expected: str) -> None:
    actual = suite.get_metadata().get("binding_tool")
    if actual != expected:
        raise ValueError(f"expected {expected!r} results, found binding_tool={actual!r}")


def load_snapshot(
    f2py_path: Path,
    x2py_path: Path,
    *,
    compiler_version: str,
    commit: str,
    recorded_date: date | None = None,
) -> PerformanceSnapshot:
    """Load and validate one paired benchmark snapshot."""
    f2py_suite = pyperf.BenchmarkSuite.load(str(f2py_path))
    x2py_suite = pyperf.BenchmarkSuite.load(str(x2py_path))
    _validate_suite_identity(f2py_suite, "f2py")
    _validate_suite_identity(x2py_suite, "x2py")
    f2py_names = f2py_suite.get_benchmark_names()
    x2py_names = x2py_suite.get_benchmark_names()
    if f2py_names != x2py_names:
        raise ValueError("paired pyperf results must contain the same benchmarks in the same order")
    if not f2py_names:
        raise ValueError("paired pyperf results contain no benchmarks")

    results = []
    for name in f2py_names:
        f2py_benchmark = f2py_suite.get_benchmark(name)
        x2py_benchmark = x2py_suite.get_benchmark(name)
        f2py_value = f2py_benchmark.mean()
        x2py_value = x2py_benchmark.mean()
        table_label, chart_label = _procedure_labels(name)
        results.append(
            BenchmarkResult(
                name=name,
                table_label=table_label,
                chart_label=chart_label,
                f2py_value=f2py_value,
                x2py_value=x2py_value,
                f2py_display=_format_benchmark_value(f2py_benchmark, f2py_value),
                x2py_display=_format_benchmark_value(x2py_benchmark, x2py_value),
                ratio=f2py_value / x2py_value,
                outcome=_outcome(f2py_benchmark, x2py_benchmark),
            )
        )

    latest_date = max(f2py_suite.get_dates()[1], x2py_suite.get_dates()[1]).date()
    return PerformanceSnapshot(
        results=tuple(results),
        metadata=_compatible_metadata(f2py_suite, x2py_suite),
        recorded_date=recorded_date or latest_date,
        compiler_version=compiler_version,
        commit=commit[:12],
    )


def _geometric_result(snapshot: PerformanceSnapshot) -> tuple[str, str]:
    ratio = snapshot.geometric_mean_ratio
    if math.isclose(ratio, 1.0, rel_tol=0.005):
        return f"1.00{TIMES}", "geometric-mean parity"
    if ratio > 1.0:
        return f"{ratio:.2f}{TIMES}", "x2py geometric-mean speedup"
    return f"{1.0 / ratio:.2f}{TIMES}", "f2py geometric-mean speedup"


def _geometric_sentence(snapshot: PerformanceSnapshot) -> str:
    ratio = snapshot.geometric_mean_ratio
    if math.isclose(ratio, 1.0, rel_tol=0.005):
        return "the geometric-mean runtime of x2py and NumPy's f2py was at parity"
    if ratio > 1.0:
        return f"the normal x2py interface delivered a **{ratio:.2f}{TIMES} geometric-mean speedup over NumPy's f2py**"
    return f"NumPy's f2py delivered a **{1.0 / ratio:.2f}{TIMES} geometric-mean speedup over x2py**"


def _outcome_sentence(snapshot: PerformanceSnapshot) -> str:
    total = len(snapshot.results)
    x2py_count = len(snapshot.x2py_wins)
    f2py_count = len(snapshot.f2py_wins)
    parity_count = len(snapshot.parity_results)
    comparison = f"Across {total} workloads, x2py was faster in {x2py_count} and f2py in {f2py_count}"
    if parity_count:
        noun = "workload" if parity_count == 1 else "workloads"
        return f"{comparison}; {parity_count} {noun} showed no statistically significant difference."
    return f"{comparison}; all comparisons were statistically significant."


def _summary_markdown(snapshot: PerformanceSnapshot) -> str:
    geometric_value, geometric_label = _geometric_result(snapshot)
    best = max(snapshot.x2py_wins, key=lambda result: result.factor, default=None)
    best_value = _format_factor(best.factor) if best else "—"
    best_label = "best measured x2py speedup" if best else "no measured x2py speedup"
    total = len(snapshot.results)
    summary = textwrap.fill(
        f"On the benchmark system, {_geometric_sentence(snapshot)}. {_outcome_sentence(snapshot)}",
        width=88,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return "\n".join(
        [
            summary,
            "",
            '<div class="x2py-performance-summary" role="group" aria-label="Benchmark summary">',
            '  <div class="x2py-performance-metric">',
            f"    <strong>{geometric_value}</strong>",
            f"    <span>{geometric_label}</span>",
            "  </div>",
            '  <div class="x2py-performance-metric">',
            f"    <strong>{len(snapshot.x2py_wins)} of {total}</strong>",
            "    <span>workloads faster with x2py</span>",
            "  </div>",
            '  <div class="x2py-performance-metric">',
            f"    <strong>{best_value}</strong>",
            f"    <span>{best_label}</span>",
            "  </div>",
            "</div>",
        ]
    )


def _relative_result(result: BenchmarkResult) -> str:
    if result.outcome == "parity":
        return "No significant difference"
    winner = result.outcome
    return f"{winner} {_format_factor(result.factor)} faster"


def _table_value(value: str, *, winner: bool) -> str:
    return f"**{value}**" if winner else value


def _geometric_table_result(snapshot: PerformanceSnapshot) -> str:
    ratio = snapshot.geometric_mean_ratio
    if math.isclose(ratio, 1.0, rel_tol=0.005):
        return "**At parity**"
    if ratio > 1.0:
        return f"**x2py {ratio:.2f}{TIMES} faster**"
    return f"**f2py {1.0 / ratio:.2f}{TIMES} faster**"


def _table_markdown(snapshot: PerformanceSnapshot) -> str:
    rows = [
        "| Workload | f2py | x2py | Relative result |",
        "| --- | ---: | ---: | ---: |",
    ]
    for result in snapshot.results:
        f2py_value = _table_value(result.f2py_display, winner=result.outcome == "f2py")
        x2py_value = _table_value(result.x2py_display, winner=result.outcome == "x2py")
        rows.append(f"| {result.table_label} | {f2py_value} | {x2py_value} | {_relative_result(result)} |")
    rows.append(f"| **Geometric mean** | reference | — | {_geometric_table_result(snapshot)} |")
    return "\n".join(rows)


def _month_date(value: date) -> str:
    months = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    return f"{months[value.month - 1]} {value.day}, {value.year}"


def _metadata_text(metadata: dict[str, object], key: str) -> str:
    return str(metadata[key]).replace("`", "'")


def _environment_markdown(snapshot: PerformanceSnapshot) -> str:
    python_version = _metadata_text(snapshot.metadata, "python_version").split(maxsplit=1)[0]
    affinity = _metadata_text(snapshot.metadata, "cpu_affinity")
    compiler_version = snapshot.compiler_version.replace("`", "'")
    lines = [
        f"- Native and generated sources use `{COMPILE_FLAGS}`.",
        "- Both interfaces keep the GIL held.",
        "- OpenMP, OpenBLAS, and MKL are limited to one thread.",
        f"- `pyperf --rigorous` pins each benchmark to logical CPU `{affinity}`.",
        f"- CPU: {_metadata_text(snapshot.metadata, 'cpu_model_name')}.",
        f"- Platform: `{_metadata_text(snapshot.metadata, 'platform_details')}`.",
        f"- Python: {python_version}.",
        f"- NumPy/f2py: {_metadata_text(snapshot.metadata, 'numpy_version')}.",
        f"- Fortran compiler: {compiler_version}.",
        f"- pyperf: {_metadata_text(snapshot.metadata, 'perf_version')}.",
        f"- x2py revision: `{snapshot.commit}`.",
        "",
        f"These results were recorded on {_month_date(snapshot.recorded_date)}. Performance depends on the CPU,",
        "compiler, operating system, and background activity, so comparisons should use",
        "results produced together on the same machine.",
    ]
    return "\n".join(lines)


def _replace_block(markdown: str, name: str, replacement: str) -> str:
    start = f"<!-- x2py-performance-{name}:start -->"
    end = f"<!-- x2py-performance-{name}:end -->"
    if markdown.count(start) != 1 or markdown.count(end) != 1:
        raise ValueError(f"Performance page must contain exactly one {name!r} marker pair")
    before, remainder = markdown.split(start, maxsplit=1)
    _old, after = remainder.split(end, maxsplit=1)
    return f"{before}{start}\n{replacement.rstrip()}\n{end}{after}"


def render_page(markdown: str, snapshot: PerformanceSnapshot) -> str:
    """Replace only the generated blocks in a Performance page."""
    replacements = {
        "summary": _summary_markdown(snapshot),
        "table": _table_markdown(snapshot),
        "environment": _environment_markdown(snapshot),
    }
    for name in MARKER_NAMES:
        markdown = _replace_block(markdown, name, replacements[name])
    return markdown


def _axis_bounds(results: tuple[BenchmarkResult, ...]) -> tuple[float, float]:
    ratios = [result.ratio for result in results]
    lower = max(0.1, math.floor((min(ratios) - 0.03) * 10.0) / 10.0)
    upper = math.ceil((max(ratios) + 0.03) * 10.0) / 10.0
    if upper - lower < 0.2:
        lower = max(0.1, lower - 0.1)
        upper += 0.1
    return lower, upper


def _axis_ticks(lower: float, upper: float) -> list[float]:
    span = upper - lower
    step = 0.1 if span <= 0.5 else 0.2 if span <= 1.0 else 0.5
    first = math.ceil(lower / step) * step
    ticks = {lower, upper, 1.0}
    value = first
    while value <= upper + 1e-9:
        ticks.add(round(value, 10))
        value += step
    return sorted(tick for tick in ticks if lower <= tick <= upper)


def _chart_geometric_label(snapshot: PerformanceSnapshot) -> str:
    ratio = snapshot.geometric_mean_ratio
    if math.isclose(ratio, 1.0, rel_tol=0.005):
        return "Geometric mean: parity"
    if ratio > 1.0:
        return f"Geometric mean: x2py {ratio:.2f}{TIMES} faster"
    return f"Geometric mean: f2py {1.0 / ratio:.2f}{TIMES} faster"


def render_chart(snapshot: PerformanceSnapshot) -> str:
    """Render an accessible SVG lollipop chart for a snapshot."""
    width = 1000
    plot_left = 350
    plot_right = 920
    top = 115
    row_start = 150
    row_step = 38
    final_row = row_start + (len(snapshot.results) - 1) * row_step
    footer = final_row + 58
    height = footer + 38
    lower, upper = _axis_bounds(snapshot.results)

    def x_position(value: float) -> float:
        return plot_left + ((value - lower) / (upper - lower)) * (plot_right - plot_left)

    baseline = x_position(1.0)
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="title description">'
        ),
        '  <title id="title">x2py performance relative to f2py</title>',
        '  <desc id="description">',
        (
            f"    Relative speed across {len(snapshot.results)} benchmarks. Values above one indicate x2py is faster. "
            f"x2py is faster in {len(snapshot.x2py_wins)} benchmarks."
        ),
        "  </desc>",
        f'  <rect x="1" y="1" width="998" height="{height - 2}" rx="16" fill="#ffffff" stroke="#d8e1e8" stroke-width="2"/>',
        '  <g font-family="Inter, -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif" fill="#17212b">',
        '    <text x="28" y="42" font-size="24" font-weight="700">x2py relative performance</text>',
        '    <text x="28" y="70" font-size="14" fill="#52616f">f2py time ÷ x2py time · farther right means faster x2py calls</text>',
        '    <g stroke="#e4eaef" stroke-width="1">',
    ]
    for tick in _axis_ticks(lower, upper):
        tick_x = x_position(tick)
        lines.append(f'      <line x1="{tick_x:.1f}" y1="{top}" x2="{tick_x:.1f}" y2="{final_row + 20}"/>')
    lines.extend(
        [
            "    </g>",
            (
                f'    <line x1="{baseline:.1f}" y1="{top - 5}" x2="{baseline:.1f}" y2="{final_row + 20}" '
                'stroke="#52616f" stroke-width="2"/>'
            ),
            '    <g font-size="12" fill="#607080" text-anchor="middle">',
        ]
    )
    for tick in _axis_ticks(lower, upper):
        tick_x = x_position(tick)
        lines.append(f'      <text x="{tick_x:.1f}" y="{top - 12}">{tick:.1f}{TIMES}</text>')
    lines.append(
        f'      <text x="{baseline:.1f}" y="{top - 30}" font-weight="700" fill="#344453">1.0{TIMES} equal</text>'
    )
    lines.extend(["    </g>", '    <g font-size="14">'])

    colors = {"x2py": "#0f766e", "f2py": "#b45309", "parity": "#64748b"}
    for index, result in enumerate(snapshot.results):
        y = row_start + index * row_step
        point = x_position(result.ratio)
        color = colors[result.outcome]
        anchor = "start" if point >= baseline else "end"
        label_x = point + 14 if point >= baseline else point - 14
        lines.extend(
            [
                f'      <text x="28" y="{y + 5}">{escape(result.chart_label)}</text>',
                (
                    f'      <line x1="{min(baseline, point):.1f}" y1="{y}" '
                    f'x2="{max(baseline, point):.1f}" y2="{y}" stroke="{color}" '
                    'stroke-width="5" stroke-linecap="round"/>'
                ),
                f'      <circle cx="{point:.1f}" cy="{y}" r="7" fill="{color}"/>',
                (
                    f'      <text x="{label_x:.1f}" y="{y + 5}" fill="{color}" font-weight="700" '
                    f'text-anchor="{anchor}">{_format_ratio(result.ratio)}</text>'
                ),
            ]
        )
    lines.extend(
        [
            "    </g>",
            '    <g font-size="13">',
            f'      <circle cx="30" cy="{footer}" r="6" fill="#0f766e"/>',
            f'      <text x="43" y="{footer + 5}" fill="#52616f">x2py faster</text>',
            f'      <circle cx="160" cy="{footer}" r="6" fill="#b45309"/>',
            f'      <text x="173" y="{footer + 5}" fill="#52616f">f2py faster</text>',
            f'      <circle cx="285" cy="{footer}" r="6" fill="#64748b"/>',
            f'      <text x="298" y="{footer + 5}" fill="#52616f">no significant difference</text>',
            (
                f'      <text x="970" y="{footer + 5}" text-anchor="end" fill="#52616f">'
                f"{escape(_chart_geometric_label(snapshot))}</text>"
            ),
            "    </g>",
            "  </g>",
            "</svg>",
            "",
        ]
    )
    return "\n".join(lines)


def _command_first_line(argv: list[str], *, description: str) -> str:
    try:
        result = subprocess.run(argv, check=True, capture_output=True, text=True)  # nosec B603
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot determine {description}: {exc}") from exc
    first_line = result.stdout.splitlines()[0].strip() if result.stdout.splitlines() else ""
    if not first_line:
        raise ValueError(f"cannot determine {description}: command produced no output")
    return first_line


def generate(
    f2py_path: Path,
    x2py_path: Path,
    page_path: Path,
    chart_path: Path,
    *,
    compiler_version: str,
    commit: str,
    recorded_date: date | None = None,
) -> PerformanceSnapshot:
    """Generate the marked page sections and SVG from paired results."""
    snapshot = load_snapshot(
        f2py_path,
        x2py_path,
        compiler_version=compiler_version,
        commit=commit,
        recorded_date=recorded_date,
    )
    original_page = page_path.read_text(encoding="utf-8")
    generated_page = render_page(original_page, snapshot)
    page_path.write_text(generated_page, encoding="utf-8")
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    chart_path.write_text(render_chart(snapshot), encoding="utf-8")
    return snapshot


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f2py-results", type=Path, default=DEFAULT_F2PY_RESULTS)
    parser.add_argument("--x2py-results", type=Path, default=DEFAULT_X2PY_RESULTS)
    parser.add_argument("--page", type=Path, default=DEFAULT_PAGE)
    parser.add_argument("--chart", type=Path, default=DEFAULT_CHART)
    parser.add_argument("--compiler", default="gfortran")
    parser.add_argument("--compiler-version")
    parser.add_argument("--commit")
    parser.add_argument("--recorded-date", type=date.fromisoformat)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    try:
        compiler_version = args.compiler_version or _command_first_line(
            [args.compiler, "--version"],
            description="Fortran compiler version",
        )
        commit = args.commit or _command_first_line(
            ["git", "rev-parse", "HEAD"],
            description="x2py revision",
        )
        snapshot = generate(
            args.f2py_results,
            args.x2py_results,
            args.page,
            args.chart,
            compiler_version=compiler_version,
            commit=commit,
            recorded_date=args.recorded_date,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot generate Performance documentation: {exc}", file=sys.stderr)
        return 2

    print(
        f"Generated Performance documentation from {len(snapshot.results)} benchmarks "
        f"recorded on {snapshot.recorded_date.isoformat()}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
