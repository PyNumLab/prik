"""Edited semantic-contract journey from the Strings User Guide."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _import_from_build_dir, _sole_native_module
from prik import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "documented_strings_api.f90"


def test_documented_edited_pyi_distinguishes_values_scalar_storage_and_string_arrays(
    tmp_path: Path,
):
    contract = tmp_path / "contract"
    contract.mkdir()
    (contract / "__init__.pyi").write_text("from . import documented_strings_api\n", encoding="utf-8")
    (contract / "documented_strings_api.pyi").write_text(
        """from prik.contracts import Addr, Arg, Int32, Returns, String, native_call

def edit_text(text: String[8]) -> Returns["text", String[8]]: ...

def edit_buffer(text: String[8][()]) -> None: ...

def make_text() -> String[8]: ...

def make_labels() -> String[8][2]: ...

@native_call([Addr(Arg(0)), Arg(1)])
def edit_labels(count: Int32, labels: String[8][count]) -> None: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract / "__init__.pyi",
        native_fortran_sources=[SOURCE],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    original = "alpha   "
    assert module.edit_text(original) == "Xlpha   "
    assert original == "alpha   "
    assert module.make_text() == "ready   "
    made_labels = module.make_labels()
    assert made_labels.dtype == np.dtype("S8")
    assert made_labels.shape == (2,)
    np.testing.assert_array_equal(made_labels, np.array([b"alpha   ", b"beta    "], dtype="S8"))
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.edit_text("short")
    with pytest.raises(TypeError, match="embedded NUL"):
        module.edit_text("abc\0defg")

    buffer = np.array("alpha   ", dtype="S8")
    assert module.edit_buffer(buffer) is None
    assert buffer[()] == np.bytes_(b"Xlpha   ")

    labels = np.array([b"alpha   ", b"beta    "], dtype="S8")
    assert module.edit_labels(np.int32(labels.size), labels) is None
    np.testing.assert_array_equal(labels, np.array([b"Xlpha   ", b"Xeta    "], dtype="S8"))
    empty = np.empty(0, dtype="S8")
    assert module.edit_labels(np.int32(0), empty) is None

    invalid_values = (
        np.array("alpha   ", dtype="S7"),
        np.array([b"alpha   "], dtype="S8"),
        np.array("alpha   ", dtype="U8"),
        np.array(b"alpha   ", dtype=object),
    )
    for invalid in invalid_values:
        with pytest.raises(TypeError):
            module.edit_buffer(invalid)

    invalid_arrays = (
        np.array([b"alpha"], dtype="S7"),
        np.array([[b"alpha   "]], dtype="S8"),
        np.array(["alpha"], dtype="U8"),
        np.array([b"alpha"], dtype=object),
    )
    for invalid in invalid_arrays:
        with pytest.raises(TypeError):
            module.edit_labels(np.int32(invalid.size), invalid)

    read_only_buffer = np.array("alpha   ", dtype="S8")
    read_only_buffer.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.edit_buffer(read_only_buffer)

    read_only_labels = np.array([b"alpha   "], dtype="S8")
    read_only_labels.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.edit_labels(np.int32(1), read_only_labels)
