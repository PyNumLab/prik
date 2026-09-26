from pathlib import Path

from tools.check_static_analysis_versions import (
    EXPECTED_STATIC_ANALYSIS_VERSIONS,
    static_analysis_version_errors,
)


def test_static_analysis_version_errors_accept_exact_pins_and_report_drift():
    assert static_analysis_version_errors(EXPECTED_STATIC_ANALYSIS_VERSIONS) == []

    installed = {**EXPECTED_STATIC_ANALYSIS_VERSIONS, "bandit": None, "ruff": "0.0.1"}
    assert static_analysis_version_errors(installed) == [
        f"bandit: not installed, expected {EXPECTED_STATIC_ANALYSIS_VERSIONS['bandit']}",
        f"ruff: installed 0.0.1, expected {EXPECTED_STATIC_ANALYSIS_VERSIONS['ruff']}",
    ]


def test_static_analysis_version_pins_match_qa_extra():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    extras = {"bandit": "bandit[toml]", "radon": "radon[toml]"}

    for package, expected in EXPECTED_STATIC_ANALYSIS_VERSIONS.items():
        assert f'"{extras.get(package, package)}=={expected}"' in pyproject, f"{package} is not pinned to {expected}"
