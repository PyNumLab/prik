"""Report wrapper-codegen structural and complexity recommendations."""

from __future__ import annotations

import argparse

from prik.codegen.checks import check_codegen_package


def main(argv: list[str] | None = None) -> int:
    """Print review findings, failing only when strict mode is requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a failure status when recommendations are reported",
    )
    arguments = parser.parse_args(argv)
    violations = check_codegen_package()
    for violation in violations:
        print(violation.label)
    if violations and not arguments.strict:
        print(f"{len(violations)} advisory codegen recommendation(s); review without changing correct behavior.")
    return int(arguments.strict and bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
