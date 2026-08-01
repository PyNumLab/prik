"""Run the isolated wrapper-codegen structural and complexity checker."""

from __future__ import annotations

from pathlib import Path

from prik.wrapper_codegen.checks import check_wrapper_codegen_package


def main() -> int:
    """Print checker violations and return a process status for automation."""
    package_root = Path(__file__).resolve().parents[1] / "prik" / "wrapper_codegen"
    violations = check_wrapper_codegen_package(package_root)
    for violation in violations:
        print(violation.label)
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
