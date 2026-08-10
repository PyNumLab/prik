"""Internal Fortran bridge lowering contracts."""

from pathlib import Path
import subprocess
import sys


def test_bridge_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [sys.executable, str(repository_root / "prik/codegen/fortran/bridge.py")],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "Bridge module: bind_c_bridge_demo_wrapper" in result.stdout
