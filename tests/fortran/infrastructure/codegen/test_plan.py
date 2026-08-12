"""Internal typed wrapper-plan contracts."""

from pathlib import Path
import subprocess
import sys


def test_plan_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [sys.executable, str(repository_root / "prik/planning/models.py")],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "Plan owner: demo" in result.stdout
