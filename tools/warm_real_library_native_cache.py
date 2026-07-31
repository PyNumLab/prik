"""Warm the BLAS/LAPACK native artifact cache used by CI."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Sequence
from pathlib import Path

DEFAULT_LIBRARIES = ("blas", "lapack")


def _real_library_cache_module():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return importlib.import_module(
        "tests.fortran.building_shared_library.end_to_end.real_libraries.test_full_libraries"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Build or verify cached real-library shared libraries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "libraries",
        metavar="{blas,lapack}",
        nargs="*",
        help="Real libraries to warm; defaults to both BLAS and LAPACK",
    )
    args = parser.parse_args(argv)
    libraries = tuple(args.libraries or DEFAULT_LIBRARIES)
    invalid_libraries = sorted(set(libraries) - set(DEFAULT_LIBRARIES))
    if invalid_libraries:
        parser.error(
            "invalid library choice: "
            + ", ".join(repr(library) for library in invalid_libraries)
            + " (choose from blas, lapack)"
        )

    cache_module = _real_library_cache_module()
    print(f"native cache root: {cache_module._native_cache_root()}")
    for library in libraries:
        shared = cache_module._cached_native_shared_library(library)
        print(f"{library}: {shared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
