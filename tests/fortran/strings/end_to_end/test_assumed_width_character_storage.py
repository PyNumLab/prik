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

SOURCE = """module assumed_width
contains
  subroutine stamp(text)
    character(len=*), intent(inout) :: text
    text = "abc"
  end subroutine

  integer function stamp_all(text)
    character(len=*), intent(inout) :: text(:)
    stamp_all = size(text) * 100 + len(text)
    text(1)(1:1) = 'Z'
  end function
end module
"""

CONTRACT = """from prik.contracts import Int32, String, bind

def stamp(text: String[...][()]) -> None: ...

@bind("stamp")
def stamp_declared(text: String[8][()]) -> None: ...

def stamp_all(text: String[...][:]) -> Int32: ...

@bind("stamp_all")
def stamp_all_declared(text: String[8][:]) -> Int32: ...
"""


def test_assumed_width_storage_accepts_any_itemsize_and_declared_width_still_checks(tmp_path: Path):
    """``String[...]`` takes its width from the caller's buffer; a stated width keeps its check.

    The width always crosses beside the address, declared or not, so a scalar
    buffer of any itemsize is stamped in place and a character array reports
    the itemsize the ABI already carries.
    """
    (tmp_path / "assumed_width.f90").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "assumed_width.pyi").write_text(CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        tmp_path / "assumed_width.pyi",
        native_fortran_sources=[tmp_path / "assumed_width.f90"],
        output_dir=tmp_path / "build",
        output_name="assumed_width",
    )
    module = result.import_module()

    for width, expected in (("S8", b"abc     "), ("S32", b"abc" + b" " * 29)):
        buffer = np.array(b"Z", dtype=width)
        assert module.stamp(buffer) is None
        assert buffer.tobytes() == expected
    declared = np.array(b"Z", dtype="S8")
    assert module.stamp_declared(declared) is None
    assert declared.tobytes() == b"abc     "

    for width in ("S8", "S16", "S32"):
        values = np.array([b"alpha", b"beta"], dtype=width)
        assert module.stamp_all(values) == np.int32(200 + int(width[1:]))
        assert values[0] == b"Zlpha"

    assert module.stamp_all_declared(np.array([b"alpha"], dtype="S8")) == np.int32(108)
    with pytest.raises(TypeError, match="itemsize 8"):
        module.stamp_all_declared(np.array([b"alpha"], dtype="S16"))
