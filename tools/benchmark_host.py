#!/usr/bin/env python3
"""Detect and export stable CPU metadata for published benchmarks."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import platform
import sys


DEFAULT_CPUINFO = Path("/proc/cpuinfo")
CPU_MODEL_ENVIRONMENT = "X2PY_BENCHMARK_CPU_MODEL"
KNOWN_ARM_MODELS = {
    ("0x41", "0xd49"): "Arm Neoverse N2",
    ("0x6d", "0xd49"): "Microsoft Azure Cobalt 100",
}


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _cpuinfo_values(cpuinfo: str) -> dict[str, set[str]]:
    values: dict[str, set[str]] = defaultdict(set)
    for line in cpuinfo.splitlines():
        key, separator, value = line.partition(":")
        normalized = _normalized(value)
        if separator and normalized:
            values[key.strip().lower()].add(normalized)
    return dict(values)


def _one_value(values: dict[str, set[str]], key: str) -> str | None:
    candidates = values.get(key, set())
    if len(candidates) > 1:
        rendered = ", ".join(sorted(candidates))
        raise ValueError(f"CPU information reports multiple {key} values: {rendered}")
    return next(iter(candidates), None)


def cpu_model_from_cpuinfo(cpuinfo: str) -> str:
    """Return one displayable CPU identity from Linux cpuinfo text."""
    values = _cpuinfo_values(cpuinfo)
    model_name = _one_value(values, "model name")
    if model_name:
        return model_name

    implementer = _one_value(values, "cpu implementer")
    part = _one_value(values, "cpu part")
    if implementer and part:
        known_model = KNOWN_ARM_MODELS.get((implementer.lower(), part.lower()))
        if known_model:
            return known_model
        architecture = _one_value(values, "cpu architecture")
        architecture_label = f", architecture {architecture}" if architecture else ""
        return f"ARM implementer {implementer}, part {part}{architecture_label}"

    machine = _one_value(values, "machine")
    if machine:
        return machine
    raise ValueError("CPU information does not contain a supported processor identity")


def read_cpuinfo(cpuinfo_path: Path = DEFAULT_CPUINFO) -> str:
    """Read Linux CPU information for benchmark-host validation."""
    try:
        return cpuinfo_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read CPU information from {cpuinfo_path}: {exc}") from exc


def verify_machine(expected: str, actual: str) -> None:
    """Require the workflow architecture selected by benchmark policy."""
    aliases = {"arm64": "aarch64"}
    normalized_expected = aliases.get(expected.lower(), expected.lower())
    normalized_actual = aliases.get(actual.lower(), actual.lower())
    if normalized_actual != normalized_expected:
        raise ValueError(f"benchmark architecture mismatch: expected {expected!r}, found {actual!r}")


def verify_arm_part(cpuinfo: str, expected: str) -> None:
    """Require the reviewed ARM core used by the hosted benchmark pool."""
    actual = _one_value(_cpuinfo_values(cpuinfo), "cpu part")
    if actual is None or actual.lower() != expected.lower():
        raise ValueError(f"benchmark ARM CPU mismatch: expected part {expected!r}, found {actual!r}")


def write_github_environment(path: Path, cpu_model: str) -> None:
    """Append the detected model to a GitHub Actions environment file."""
    try:
        with path.open("a", encoding="utf-8") as environment:
            environment.write(f"{CPU_MODEL_ENVIRONMENT}={cpu_model}\n")
    except OSError as exc:
        raise ValueError(f"cannot write benchmark metadata to {path}: {exc}") from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpuinfo", type=Path, default=DEFAULT_CPUINFO)
    parser.add_argument("--require-machine")
    parser.add_argument("--require-arm-part")
    parser.add_argument("--github-env", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    try:
        if args.require_machine:
            verify_machine(args.require_machine, platform.machine())
        cpuinfo = read_cpuinfo(args.cpuinfo)
        if args.require_arm_part:
            verify_arm_part(cpuinfo, args.require_arm_part)
        cpu_model = cpu_model_from_cpuinfo(cpuinfo)
        if args.github_env:
            write_github_environment(args.github_env, cpu_model)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Verified benchmark host: {platform.machine()} · {cpu_model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
