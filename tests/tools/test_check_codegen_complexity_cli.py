"""Command behavior for the advisory codegen reviewer."""

from pathlib import Path

from prik.codegen.checks import WrapperCodegenViolation
from tools import check_codegen_complexity


def _recommendation() -> WrapperCodegenViolation:
    return WrapperCodegenViolation(
        path=Path("prik/codegen/example.py"),
        lineno=12,
        code="complexity",
        message="example recommendation",
    )


def test_codegen_review_is_advisory_by_default(monkeypatch, capsys) -> None:
    monkeypatch.setattr(check_codegen_complexity, "check_codegen_package", lambda: (_recommendation(),))

    assert check_codegen_complexity.main([]) == 0
    output = capsys.readouterr().out
    assert "example recommendation" in output
    assert "advisory codegen recommendation" in output


def test_codegen_review_can_be_requested_as_strict(monkeypatch) -> None:
    monkeypatch.setattr(check_codegen_complexity, "check_codegen_package", lambda: (_recommendation(),))

    assert check_codegen_complexity.main(["--strict"]) == 1
