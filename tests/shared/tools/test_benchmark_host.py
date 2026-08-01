"""Tests for published benchmark host detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import benchmark_host


X86_CPUINFO = """\
processor : 0
model name : AMD EPYC Test Processor

processor : 1
model name : AMD EPYC Test Processor
"""
COBALT_CPUINFO = """\
processor : 0
CPU implementer : 0x6d
CPU architecture: 8
CPU part : 0xd49

processor : 1
CPU implementer : 0x6d
CPU architecture: 8
CPU part : 0xd49
"""


def test_cpu_model_from_cpuinfo_supports_x86_and_cobalt_arm() -> None:
    assert benchmark_host.cpu_model_from_cpuinfo(X86_CPUINFO) == "AMD EPYC Test Processor"
    assert benchmark_host.cpu_model_from_cpuinfo(COBALT_CPUINFO) == "Microsoft Azure Cobalt 100"


def test_cpu_model_from_cpuinfo_preserves_unknown_arm_identity() -> None:
    cpuinfo = COBALT_CPUINFO.replace("0x6d", "0x42")

    assert benchmark_host.cpu_model_from_cpuinfo(cpuinfo) == "ARM implementer 0x42, part 0xd49, architecture 8"


def test_cpu_model_from_cpuinfo_rejects_missing_or_mixed_identity() -> None:
    with pytest.raises(ValueError, match="does not contain a supported processor identity"):
        benchmark_host.cpu_model_from_cpuinfo("processor : 0\n")
    with pytest.raises(ValueError, match="multiple model name values"):
        benchmark_host.cpu_model_from_cpuinfo(X86_CPUINFO.replace("Test Processor", "Other Processor", 1))


def test_verify_machine_accepts_arm_alias_and_rejects_other_architecture() -> None:
    benchmark_host.verify_machine("aarch64", "arm64")

    with pytest.raises(ValueError, match="benchmark architecture mismatch"):
        benchmark_host.verify_machine("aarch64", "x86_64")


def test_verify_arm_part_requires_neoverse_n2_cobalt_core() -> None:
    benchmark_host.verify_arm_part(COBALT_CPUINFO, "0xd49")

    with pytest.raises(ValueError, match="benchmark ARM CPU mismatch"):
        benchmark_host.verify_arm_part(COBALT_CPUINFO, "0xd40")


def test_main_exports_detected_model_to_github_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(COBALT_CPUINFO, encoding="utf-8")
    github_environment = tmp_path / "github-env"
    monkeypatch.setattr(benchmark_host.platform, "machine", lambda: "aarch64")

    result = benchmark_host.main(
        [
            "--cpuinfo",
            str(cpuinfo),
            "--require-machine",
            "aarch64",
            "--require-arm-part",
            "0xd49",
            "--github-env",
            str(github_environment),
        ]
    )

    assert result == 0
    assert github_environment.read_text(encoding="utf-8") == ("PRIK_BENCHMARK_CPU_MODEL=Microsoft Azure Cobalt 100\n")
    assert "Verified benchmark host: aarch64 · Microsoft Azure Cobalt 100" in capsys.readouterr().out
