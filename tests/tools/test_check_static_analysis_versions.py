from pathlib import Path

from tools.check_static_analysis_versions import (
    EXPECTED_STATIC_ANALYSIS_VERSIONS,
    static_analysis_version_errors,
)


def test_static_analysis_version_errors_reports_missing_and_mismatched_tools():
    installed = {
        "bandit": None,
        "radon": "6.0.1",
        "ruff": "0.11.7",
        "vulture": "2.16",
    }

    assert static_analysis_version_errors(installed) == [
        "bandit: not installed, expected 1.9.4",
        "ruff: installed 0.11.7, expected 0.15.17",
    ]


def test_static_analysis_version_errors_accepts_exact_pins():
    assert static_analysis_version_errors(EXPECTED_STATIC_ANALYSIS_VERSIONS) == []


def test_static_analysis_version_pins_match_qa_extra():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"bandit[toml]==1.9.4"' in pyproject
    assert '"radon[toml]==6.0.1"' in pyproject
    assert '"ruff==0.15.17"' in pyproject
    assert '"vulture==2.16"' in pyproject
