"""Tests for the compact GitHub Actions pytest failure summary."""

from pathlib import Path

from tools.print_pytest_failures import failed_pytest_nodes, failure_summary, main


def test_failed_pytest_nodes_preserve_paths_parameters_and_report_order(tmp_path: Path):
    report = tmp_path / "pytest-results.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="tests.test_sample" name="test_passes" file="tests/test_sample.py" />
    <testcase classname="tests.test_sample" name="test_fails[source]" file="tests/test_sample.py">
      <failure message="assert false">traceback</failure>
    </testcase>
    <testcase classname="tests.test_other" name="test_errors[generated-pyi]" file="tests/test_other.py">
      <error message="setup failed">traceback</error>
    </testcase>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )

    assert failed_pytest_nodes(report) == [
        "tests/test_sample.py::test_fails[source]",
        "tests/test_other.py::test_errors[generated-pyi]",
    ]
    assert failure_summary(report).splitlines() == [
        "Failed pytest nodes",
        "- tests/test_sample.py::test_fails[source]",
        "- tests/test_other.py::test_errors[generated-pyi]",
    ]


def test_failure_summary_reports_missing_or_unreadable_reports(tmp_path: Path):
    missing = tmp_path / "missing.xml"
    assert failure_summary(missing) == f"Failed pytest nodes\n- report unavailable: {missing}"

    invalid = tmp_path / "invalid.xml"
    invalid.write_text("<testsuite>", encoding="utf-8")
    assert failure_summary(invalid).startswith("Failed pytest nodes\n- report unreadable:")


def test_main_prints_summary_without_replacing_the_original_test_exit(capsys, tmp_path: Path):
    report = tmp_path / "pytest-results.xml"
    report.write_text("<testsuite />", encoding="utf-8")

    assert main([str(report)]) == 0
    assert capsys.readouterr().out == "Failed pytest nodes\n- no failed nodes recorded\n"
