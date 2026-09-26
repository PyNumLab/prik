"""C input-language CLI argument contracts.

Shared CLI validation, routing, and help completeness are proved once by
``tests/fortran/infrastructure/cli/pipeline/``; these rows are the diagnostics
only a C input or a C-only option can reach. They run real command lines
through ``prik.cli.main``.
"""

from pathlib import Path

import pytest

import prik.cli as prik_cli


def _invoke(argv: list[str], capsys) -> tuple[int, str, str]:
    """Run one command line in-process and return its exit code and output."""
    try:
        code = prik_cli.main(argv)
    except SystemExit as exc:
        code = exc.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def c_inputs(tmp_path: Path, monkeypatch) -> Path:
    """Write one input of each kind the rows name, relative to the working directory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "api.h").write_text("int add(int a, int b);\n", encoding="utf-8")
    (tmp_path / "api.c").write_text("int increment(int value) { return value + 1; }\n", encoding="utf-8")
    (tmp_path / "contract.pyi").write_text("from prik.contracts import Int\n", encoding="utf-8")
    (tmp_path / "exports.txt").write_text("increment\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        pytest.param(
            ["parse", "api.h", "--language", "c", "--show-vars"],
            "--show-vars is Fortran-only and is not supported for --language c",
            id="c-parse-with-fortran-only-option",
        ),
        pytest.param(
            ["generate", "--pyi", "api.h", "--out"],
            "C input api.h requires explicit --language c",
            id="c-input-without-explicit-language",
        ),
        pytest.param(
            ["generate", "--pyi", "api.h", "--language", "fortran", "--out"],
            "C input api.h is incompatible with --language fortran; pass --language c",
            id="c-input-with-fortran-frontend",
        ),
        pytest.param(
            ["contract.pyi", "--native-c-sources", "api.c", "--export-symbols", "exports.txt"],
            "--export-symbols selects the public surface while reading native source; "
            "a semantic .pyi contract already states its public surface in __all__",
            id="contract-with-c-export-allowlist",
        ),
    ],
)
def test_c_cli_rejects_invalid_invocation_with_its_documented_diagnostic(
    c_inputs: Path, capsys, argv: list[str], message: str
):
    before = sorted(c_inputs.iterdir())

    code, out, err = _invoke(argv, capsys)

    assert code == 2
    assert out == ""
    assert message in " ".join(err.split())
    # A rejected invocation writes nothing next to its inputs.
    assert sorted(c_inputs.iterdir()) == before
