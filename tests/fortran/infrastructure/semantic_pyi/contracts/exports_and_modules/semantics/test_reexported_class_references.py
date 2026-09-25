"""A contract class imported through a module that re-exports it is its declaration."""

from __future__ import annotations

from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_paths_to_semantic_modules
from prik.semantics.models import EXTERNAL_TYPE_REF_METADATA

HANDLES = """\
from prik.contracts import Int32

class Handle:
    def __init__(
        self,
        *,
        value: Int32 = ...
    ) -> None: ...

__all__ = ["Handle"]
"""

API = """\
from prik.contracts import Int32
from .{importer} import Handle

def value_of(handle: Handle) -> Int32: ...

__all__ = ["value_of"]
"""


@pytest.mark.parametrize("chain", [("facade",), ("facade", "outer")], ids=["one-reexport", "reexport-chain"])
def test_class_imported_through_reexports_references_its_declaring_module(tmp_path: Path, chain: tuple[str, ...]):
    (tmp_path / "handles.pyi").write_text(HANDLES, encoding="utf-8")
    source = "handles"
    for name in chain:
        (tmp_path / f"{name}.pyi").write_text(
            f'from .{source} import Handle\n\n__all__ = ["Handle"]\n', encoding="utf-8"
        )
        source = name
    (tmp_path / "api.pyi").write_text(API.format(importer=source), encoding="utf-8")

    modules = pyi_paths_to_semantic_modules(tmp_path)

    api = next(module for module in modules if module.name == "api")
    ref = api.functions[0].arguments[0].semantic_type.metadata[EXTERNAL_TYPE_REF_METADATA]
    assert (ref["origin_module"], ref["wrapped"], ref["representation"]) == ("handles", True, "wrapped")
