"""A generic's specific takes a callback whose prototype and types come from ``use`` in bodies.

``register`` is a generic whose interface body imports its callback prototype
with a ``use`` of its own, and that prototype imports its argument's derived
type with a ``use`` in its body. Built from source and replayed from a
selected contract, the generic dispatches a Python callable to the callback.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from prik import build_fortran_extension, build_pyi_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "native" / "generic_callback_prototype_imports.f90"


def test_a_generic_dispatches_a_callable_to_a_prototype_imported_inside_bodies(tmp_path: Path):
    contract = tmp_path / "contract"
    symbols = tmp_path / "exports.txt"
    symbols.write_text("facade::register\n", encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(SOURCE),
            "--export-symbols",
            str(symbols),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    # The prototype names its argument's type through the module declaring it,
    # and that module is part of the selected contract set.
    prototypes = (contract / "cbs.pyi").read_text(encoding="utf-8")
    assert "h: handles.Handle" in prototypes and (contract / "handles.pyi").is_file()
    assert "from .cbs import copy_fn" in (contract / "ifaces.pyi").read_text(encoding="utf-8")

    source = build_fortran_extension(
        SOURCE,
        output_dir=tmp_path / "source",
        output_name="callback_imports_source",
        export_symbols=["facade::register"],
    )
    replay = build_pyi_extension(
        contract / "__init__.pyi",
        native_fortran_sources=(SOURCE,),
        output_dir=tmp_path / "replay",
        output_name="callback_imports_replay",
    )

    def callback(handle, value):
        value[()] = value + handle.val

    for result in (source, replay):
        facade = _import_from_build_dir(result.module_name, result.output_dir).facade
        assert facade.register(callback) == 18
        with pytest.raises(TypeError, match="no matching overload"):
            facade.register(3)
