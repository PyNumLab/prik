"""Assumed-width character contracts take their width from the caller's array.

Every element of a NumPy ``S`` array shares one itemsize, and a Fortran
``character(len=n)`` array is uniform by definition, so a contract may leave the
width unstated and let the runtime value cross beside the buffer.
"""

from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end

SCALAR_SOURCE = """module {name}
contains
  subroutine stamp(text)
    character(len=*), intent(inout) :: text
    text = "abc"
  end subroutine
end module
"""

ARRAY_SOURCE = """module {name}
contains
  integer function stamp_all(text)
    character(len=*), intent(inout) :: text(:)
    stamp_all = size(text)
    text(1)(1:1) = 'Z'
  end function
end module
"""


def _build(tmp_path: Path, name: str, source: str, contract: str):
    (tmp_path / f"{name}.f90").write_text(source.format(name=name), encoding="utf-8")
    (tmp_path / f"{name}.pyi").write_text(contract, encoding="utf-8")
    result = build_pyi_extension(
        tmp_path / f"{name}.pyi",
        native_fortran_sources=[tmp_path / f"{name}.f90"],
        output_dir=tmp_path / f"build_{name}",
        output_name=name,
    )
    adapter = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".f90")
    return result, adapter


def test_assumed_width_scalar_storage_accepts_any_caller_itemsize(tmp_path: Path):
    """``String[...][()]`` declares its adapter local from the runtime width."""
    result, adapter = _build(
        tmp_path,
        "assumed_scalar_any",
        SCALAR_SOURCE,
        "from prik.contracts import String\n\ndef stamp(text: String[...][()]) -> None: ...\n",
    )
    module = result.import_module()

    assert "character(kind=c_char, len=text_length) :: text" in adapter
    for width, expected in (("S8", b"abc     "), ("S32", b"abc" + b" " * 29)):
        buffer = np.array(b"Z", dtype=width)
        assert module.stamp(buffer) is None
        assert buffer.tobytes() == expected


def test_declared_and_assumed_scalar_storage_share_one_adapter_shape(tmp_path: Path):
    """The width always crosses beside the address, declared or not."""
    _, assumed = _build(
        tmp_path,
        "assumed_scalar_shape",
        SCALAR_SOURCE,
        "from prik.contracts import String\n\ndef stamp(text: String[...][()]) -> None: ...\n",
    )
    (tmp_path / "declared").mkdir()
    _, declared = _build(
        tmp_path / "declared",
        "declared_scalar_shape",
        SCALAR_SOURCE,
        "from prik.contracts import String\n\ndef stamp(text: String[8][()]) -> None: ...\n",
    )

    signature = 'subroutine bind_c_stamp(bound_text, text_length) bind(c, name="bind_c_stamp")'
    assert signature in assumed
    assert signature in declared


def test_assumed_width_character_array_accepts_any_caller_itemsize(tmp_path: Path):
    """``String[...][:]`` names the itemsize the ABI already reports."""
    result, adapter = _build(
        tmp_path,
        "assumed_array_any",
        ARRAY_SOURCE,
        "from prik.contracts import Int32, String\n\ndef stamp_all(text: String[...][:]) -> Int32: ...\n",
    )
    module = result.import_module()

    assert "character(kind=c_char, len=text_itemsize)" in adapter
    for width in ("S8", "S16", "S32"):
        values = np.array([b"alpha", b"beta"], dtype=width)
        assert module.stamp_all(values) == np.int32(2)
        assert values[0] == b"Zlpha"


def test_declared_array_width_still_checks_the_caller_itemsize(tmp_path: Path):
    """A stated width keeps its validation; only an assumed one accepts any."""
    result, _ = _build(
        tmp_path,
        "declared_array_width",
        ARRAY_SOURCE,
        "from prik.contracts import Int32, String\n\ndef stamp_all(text: String[8][:]) -> Int32: ...\n",
    )
    module = result.import_module()

    assert module.stamp_all(np.array([b"alpha"], dtype="S8")) == np.int32(1)
    with pytest.raises(TypeError, match="itemsize 8"):
        module.stamp_all(np.array([b"alpha"], dtype="S16"))
