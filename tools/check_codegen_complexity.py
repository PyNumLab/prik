"""Run the isolated wrapper-codegen structural and complexity checker."""

from __future__ import annotations

from prik.codegen.checks import check_codegen_package


def main() -> int:
    """Print checker violations and return a process status for automation."""
    violations = check_codegen_package()
    for violation in violations:
        print(violation.label)
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
