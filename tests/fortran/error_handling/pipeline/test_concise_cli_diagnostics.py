"""CLI diagnostics for expected Fortran failures: concise by default, a traceback with --debug."""

from pathlib import Path
import subprocess
import sys


def test_cli_formats_parse_errors_concisely_and_reraises_with_debug(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    concise = subprocess.run(
        [sys.executable, "-m", "prik", "parse", str(f90), "--no-color"], capture_output=True, text=True
    )
    assert concise.returncode == 1
    assert concise.stdout == ""
    assert "Traceback" not in concise.stderr
    assert f"{f90}:" in concise.stderr
    assert "error[PARSE_UNSUPPORTED_DECLARATION]:" in concise.stderr
    assert "|   weirdtype :: x" in concise.stderr

    debug = subprocess.run([sys.executable, "-m", "prik", "parse", str(f90), "--debug"], capture_output=True, text=True)
    assert debug.returncode == 1
    assert "Traceback" in debug.stderr
    assert "FortranParseError" in debug.stderr
