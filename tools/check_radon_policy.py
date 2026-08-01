#!/usr/bin/env python3
"""Enforce the staged Radon complexity policy."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys

from radon.complexity import cc_visit


DEFAULT_SOURCE_PATHS = ("prik",)
DEFAULT_MAX_CHANGED_COMPLEXITY = 20
DEFAULT_MAX_HOTSPOT_AVERAGE = 19.01
DEFAULT_HOTSPOT_MIN_COMPLEXITY = 11
ZERO_SHA = "0" * 40
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class ComplexityBlock:
    path: Path
    kind: str
    name: str
    lineno: int
    endline: int
    complexity: int

    @property
    def label(self) -> str:
        return f"{self.path}:{self.lineno} {self.kind} {self.name}"


@dataclass(frozen=True)
class ChangedPythonFile:
    path: str
    base_path: str | None


@dataclass(frozen=True)
class PolicyResult:
    hotspot_average: float
    hotspot_count: int
    changed_blocks_checked: int
    changed_violations: tuple[ComplexityBlock, ...]

    @property
    def ok(self) -> bool:
        return not self.changed_violations


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths",
        nargs="+",
        default=list(DEFAULT_SOURCE_PATHS),
        help="Source roots to analyze.",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help=(
            "Git ref used to find changed Python lines. Use 'auto' to read "
            "PR_BASE_SHA or PUSH_BEFORE_SHA. If omitted, only the hotspot "
            "average baseline is checked."
        ),
    )
    parser.add_argument("--head-ref", default="HEAD", help="Git ref for the changed side.")
    parser.add_argument(
        "--max-changed-complexity",
        type=int,
        default=DEFAULT_MAX_CHANGED_COMPLEXITY,
        help="Maximum allowed complexity for changed source blocks.",
    )
    parser.add_argument(
        "--max-hotspot-average",
        type=float,
        default=DEFAULT_MAX_HOTSPOT_AVERAGE,
        help="Maximum average complexity across C-or-worse blocks.",
    )
    parser.add_argument(
        "--hotspot-min-complexity",
        type=int,
        default=DEFAULT_HOTSPOT_MIN_COMPLEXITY,
        help="Minimum complexity included in the hotspot average.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    source_paths = tuple(Path(path) for path in args.paths)
    base_ref = resolve_base_ref(args.base_ref)
    if args.base_ref == "auto" and base_ref is None:
        print(
            "Radon policy could not resolve --base-ref auto; set PR_BASE_SHA, "
            "PUSH_BEFORE_SHA, or GITHUB_BASE_SHA, or pass an explicit base ref.",
            file=sys.stderr,
        )
        return 2
    result = check_policy(
        source_paths=source_paths,
        base_ref=base_ref,
        head_ref=args.head_ref,
        max_changed_complexity=args.max_changed_complexity,
        hotspot_min_complexity=args.hotspot_min_complexity,
    )

    failed = False
    if result.hotspot_average > args.max_hotspot_average:
        failed = True
        print(
            "Radon hotspot average regressed: "
            f"{result.hotspot_average:.2f} > {args.max_hotspot_average:.2f} "
            f"across {result.hotspot_count} C-or-worse blocks.",
            file=sys.stderr,
        )

    if result.changed_violations:
        failed = True
        print(
            f"Changed source blocks exceed the staged complexity limit ({args.max_changed_complexity}):",
            file=sys.stderr,
        )
        for block in result.changed_violations:
            print(f"  {block.label} has complexity {block.complexity}", file=sys.stderr)

    if failed:
        return 1

    changed_summary = (
        f"{result.changed_blocks_checked} changed block(s) checked"
        if base_ref
        else "no changed-block check; no base ref supplied"
    )
    print(
        "Radon policy passed: "
        f"hotspot average {result.hotspot_average:.2f} "
        f"across {result.hotspot_count} C-or-worse blocks; {changed_summary}."
    )
    return 0


def resolve_base_ref(base_ref: str | None) -> str | None:
    if base_ref != "auto":
        return _clean_base_ref(base_ref)

    return _clean_base_ref(
        subprocess_env("PR_BASE_SHA") or subprocess_env("PUSH_BEFORE_SHA") or subprocess_env("GITHUB_BASE_SHA")
    )


def subprocess_env(name: str) -> str | None:
    import os

    return os.environ.get(name)


def _clean_base_ref(base_ref: str | None) -> str | None:
    if base_ref is None:
        return None
    cleaned = base_ref.strip()
    if not cleaned or cleaned == ZERO_SHA:
        return None
    return cleaned


def check_policy(
    *,
    source_paths: tuple[Path, ...],
    base_ref: str | None,
    head_ref: str,
    max_changed_complexity: int,
    hotspot_min_complexity: int,
) -> PolicyResult:
    all_blocks = list(iter_complexity_blocks(source_paths))
    hotspot_blocks = [block for block in all_blocks if block.complexity >= hotspot_min_complexity]
    hotspot_average = sum(block.complexity for block in hotspot_blocks) / len(hotspot_blocks) if hotspot_blocks else 0.0

    changed_blocks_checked, changed_violations = changed_complexity_blocks(
        source_paths=source_paths,
        base_ref=base_ref,
        head_ref=head_ref,
        max_changed_complexity=max_changed_complexity,
    )

    return PolicyResult(
        hotspot_average=hotspot_average,
        hotspot_count=len(hotspot_blocks),
        changed_blocks_checked=changed_blocks_checked,
        changed_violations=tuple(changed_violations),
    )


def iter_complexity_blocks(source_paths: tuple[Path, ...]) -> list[ComplexityBlock]:
    blocks: list[ComplexityBlock] = []
    for path in iter_python_files(source_paths):
        blocks.extend(complexity_blocks_for_file(path))
    return blocks


def iter_python_files(source_paths: tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for source_path in source_paths:
        if source_path.is_file() and source_path.suffix == ".py":
            files.append(source_path)
        elif source_path.is_dir():
            files.extend(sorted(source_path.rglob("*.py")))
    return sorted(files)


def complexity_blocks_for_file(path: Path) -> list[ComplexityBlock]:
    source = path.read_text(encoding="utf-8")
    return complexity_blocks_for_source(source, path=path)


def complexity_blocks_for_source(source: str, *, path: Path) -> list[ComplexityBlock]:
    blocks: list[ComplexityBlock] = []
    for block in cc_visit(source):
        classname = getattr(block, "classname", None)
        name = f"{classname}.{block.name}" if classname else block.name
        blocks.append(
            ComplexityBlock(
                path=path,
                kind=type(block).__name__.removesuffix("Block").lower(),
                name=name,
                lineno=block.lineno,
                endline=block.endline,
                complexity=block.complexity,
            )
        )
    return blocks


def changed_complexity_blocks(
    *,
    source_paths: tuple[Path, ...],
    base_ref: str | None,
    head_ref: str,
    max_changed_complexity: int,
) -> tuple[int, list[ComplexityBlock]]:
    if base_ref is None:
        return 0, []

    changed_blocks_checked = 0
    changed_violations: list[ComplexityBlock] = []
    source_roots = tuple(path.as_posix().rstrip("/") for path in source_paths)
    for changed_file in changed_python_files(base_ref, head_ref):
        if not is_under_source_roots(changed_file.path, source_roots):
            continue
        path = Path(changed_file.path)
        if not path.exists():
            continue
        changed_lines = changed_line_numbers(base_ref, head_ref, changed_file.path)
        if not changed_lines:
            continue
        base_complexities = base_complexity_by_key(base_ref, changed_file.base_path)
        for block in complexity_blocks_for_file(path):
            if not block_changed(block, changed_lines):
                continue
            changed_blocks_checked += 1
            base_complexity = base_complexities.get(block_key(block))
            if changed_block_violates_policy(block, base_complexity, max_changed_complexity):
                changed_violations.append(block)
    return changed_blocks_checked, changed_violations


def changed_block_violates_policy(
    block: ComplexityBlock,
    base_complexity: int | None,
    max_changed_complexity: int,
) -> bool:
    if block.complexity <= max_changed_complexity:
        return False
    return base_complexity is None or block.complexity > base_complexity


def base_complexity_by_key(base_ref: str, changed_file: str | None) -> dict[tuple[str, str], int]:
    if changed_file is None:
        return {}
    completed = subprocess.run(
        ["git", "show", f"{base_ref}:{changed_file}"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return {}
    return {
        block_key(block): block.complexity
        for block in complexity_blocks_for_source(completed.stdout, path=Path(changed_file))
    }


def block_key(block: ComplexityBlock) -> tuple[str, str]:
    return block.kind, block.name


def changed_python_files(base_ref: str, head_ref: str) -> list[ChangedPythonFile]:
    completed = run_git(
        "diff",
        "--name-status",
        "--find-renames=50%",
        "--diff-filter=ACMRT",
        base_ref,
        head_ref,
        "--",
        "*.py",
    )
    return parse_changed_python_files(completed.stdout)


def parse_changed_python_files(output: str) -> list[ChangedPythonFile]:
    changed_files: list[ChangedPythonFile] = []
    for line in output.splitlines():
        if not line:
            continue
        status, *paths = line.split("\t")
        if status.startswith(("R", "C")):
            old_path, new_path = paths
            changed_files.append(ChangedPythonFile(new_path, old_path))
        else:
            (path,) = paths
            changed_files.append(ChangedPythonFile(path, None if status == "A" else path))
    return changed_files


def changed_line_numbers(base_ref: str, head_ref: str, changed_file: str) -> set[int]:
    completed = run_git(
        "diff",
        "--unified=0",
        "--no-ext-diff",
        base_ref,
        head_ref,
        "--",
        changed_file,
    )
    changed_lines: set[int] = set()
    for line in completed.stdout.splitlines():
        match = HUNK_RE.match(line)
        if not match:
            continue
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        if count == 0:
            continue
        changed_lines.update(range(start, start + count))
    return changed_lines


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    )


def is_under_source_roots(changed_file: str, source_roots: tuple[str, ...]) -> bool:
    return any(changed_file == root or changed_file.startswith(f"{root}/") for root in source_roots)


def block_changed(block: ComplexityBlock, changed_lines: set[int]) -> bool:
    return any(block.lineno <= line <= block.endline for line in changed_lines)


if __name__ == "__main__":
    raise SystemExit(main())
