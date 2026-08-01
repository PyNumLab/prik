"""Concise CLI diagnostics for expected Fortran failures."""

from pathlib import Path
import subprocess
import sys


def test_cli_formats_parse_errors_without_traceback(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "parse", str(f90), "--no-color"]
    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 1
    assert res.stdout == ""
    assert "Traceback" not in res.stderr
    assert f"{f90}:" in res.stderr
    assert "error[PARSE_UNSUPPORTED_DECLARATION]:" in res.stderr
    assert "|   weirdtype :: x" in res.stderr
