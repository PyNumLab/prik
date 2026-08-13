"""Public root-facade contract for normal wrapper builds."""

import prik
from prik.pipeline.build import build_fortran_extension, build_pyi_extension, build_pyi_extension_from_manifest


def test_root_facade_exposes_only_version_and_build_entrypoints():
    assert prik.__all__ == (
        "__version__",
        "build_fortran_extension",
        "build_pyi_extension",
        "build_pyi_extension_from_manifest",
    )
    assert prik.build_fortran_extension is build_fortran_extension
    assert prik.build_pyi_extension is build_pyi_extension
    assert prik.build_pyi_extension_from_manifest is build_pyi_extension_from_manifest


def test_root_build_entrypoints_support_direct_imports():
    """Normal users can import the documented build functions from ``prik``."""
    from prik import (
        build_fortran_extension,
        build_pyi_extension,
        build_pyi_extension_from_manifest,
    )

    assert build_fortran_extension is prik.build_fortran_extension
    assert build_pyi_extension is prik.build_pyi_extension
    assert build_pyi_extension_from_manifest is prik.build_pyi_extension_from_manifest
