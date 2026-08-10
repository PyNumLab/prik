"""Internal semantic pyi printer contracts."""

from pathlib import Path
import subprocess
import sys


def test_pyi_printer_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [sys.executable, str(repository_root / "prik/codegen/printers/pyi_printer.py")],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "Semantic module: printer_demo" in result.stdout
