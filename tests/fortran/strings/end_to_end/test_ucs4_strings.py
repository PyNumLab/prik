"""UCS-4 character values cross every string boundary the default kind does."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_generated_pyi_and_import,
    _build_source_and_import,
    _require_ucs4_character_support,
)

SOURCE = Path(__file__).parent / "fixtures" / "native" / "fucs4_strings.f90"
GENERATED = {
    "bind_c_fucs4_strings_wrapper.f90",
    "fucs4_strings_wrapper.c",
    "fucs4_strings_wrapper.h",
}
pytestmark = pytest.mark.fortran_end_to_end


def _assert_ucs4_strings(module) -> None:
    """Check scalar, storage, array, handle, and callback UCS-4 boundaries."""
    # Scalar str arguments and results carry code points beyond one byte.
    assert module.count_code("π中πx", np.int32(960)) == 2
    assert module.tag() == "πab"
    assert module.reverse("ab中d") == "d中ba"
    assert module.describe(np.int32(3)) == "πππ"
    assert module.grow("中") == "中中"
    with pytest.raises(TypeError, match="exactly 4 characters"):
        module.reverse("abc")

    # Stored scalars are live U<n> views; assignment and view writes reach native code.
    label = module.label
    assert label.dtype == np.dtype("U4") and label[()] == "abcd"
    label[...] = "π中xy"
    assert module.label_code(np.int32(1)) == 960
    module.label = "wxyz"
    assert module.label_code(np.int32(2)) == ord("x")
    assert module.note is None
    module.note = "héllo"
    assert module.note[()] == "héllo"
    record = module.Record()
    assert record.code.dtype == np.dtype("U3") and record.code[()] == "xyz"

    # Arrays, array results, module arrays, and descriptor handles use U<n>.
    items = np.array(["ab", "中π"], dtype="U2")
    module.shift(items)
    assert items.tolist() == ["中π", "ab"]
    assert module.pair().tolist() == ["π1", "z2"]
    assert module.grid.tolist() == ["aa", "bb", "cc"]
    module.fill_words()
    assert module.words.to_numpy().tolist() == ["abc", "πxy"]

    # A callback receives the characters as a Python str.
    seen = []
    module.each(lambda text: seen.append(str(text)))
    assert seen == ["abπ"]


def test_ucs4_strings_match_in_source_and_contract_builds(tmp_path: Path):
    _require_ucs4_character_support()
    source_module = _build_source_and_import(SOURCE, tmp_path / "source", GENERATED)
    contract_module = _build_generated_pyi_and_import(SOURCE, tmp_path / "contract")
    for module in (source_module, contract_module):
        _assert_ucs4_strings(module)

    contract = (tmp_path / "contract" / "contracts" / SOURCE.stem / "ucs4_strings.pyi").read_text(encoding="utf-8")
    for spelling in ("label: UString[4][()]", "note: Allocatable[UString[:]]", "def tag() -> UString[3]"):
        assert spelling in contract
