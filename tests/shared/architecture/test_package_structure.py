"""Mechanical checks for the top-level prik package architecture."""

from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[3] / "prik"
ROOT_PYTHON_MODULES = {"__init__.py", "__main__.py", "cli.py", "stage_values.py"}


def test_prik_root_contains_only_public_entrypoint_modules():
    assert {path.name for path in PACKAGE_ROOT.glob("*.py")} == ROOT_PYTHON_MODULES
