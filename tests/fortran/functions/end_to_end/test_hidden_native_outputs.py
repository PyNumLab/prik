"""``Hidden`` outputs cross the bridge normally but are never published.

The bridge plans a hidden output exactly like a returned one, so its native
storage is allocated and released on the ordinary path. Only the binding
differs: it builds no Python result from it.
"""

from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = """module {name}
contains
  subroutine tally(n, doubled, note)
    integer, intent(in) :: n
    integer, intent(out) :: doubled
    character(len=*), intent(out) :: note
    doubled = n * 2
    note = "seen"
  end subroutine
end module
"""


def _build(tmp_path: Path, name: str, contract: str):
    (tmp_path / f"{name}.f90").write_text(SOURCE.format(name=name), encoding="utf-8")
    (tmp_path / f"{name}.pyi").write_text(contract, encoding="utf-8")
    result = build_pyi_extension(
        tmp_path / f"{name}.pyi",
        native_fortran_sources=[tmp_path / f"{name}.f90"],
        output_dir=tmp_path / f"build_{name}",
        output_name=name,
    )
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")
    bridge = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".f90")
    return result, binding, bridge


def test_hidden_outputs_are_released_but_never_returned(tmp_path: Path):
    """The adapter still allocates the string, so the binding still frees it."""
    result, binding, bridge = _build(
        tmp_path,
        "hidden_all",
        """from prik.contracts import Arg, Hidden, Int32, String, native_call

@native_call([Arg(0), Hidden("doubled", Int32), Hidden("note", String[16])])
def tally(n: Int32) -> None: ...
""",
    )
    module = result.import_module()

    # The bridge is the ordinary owned-allocation adapter for a character output.
    assert "note = c_malloc(17_c_size_t)" in bridge
    # ... so the binding must still release it even though nothing is published.
    assert "free(note)" in binding

    assert module.tally(np.int32(5)) is None
    assert module.tally.__doc__.splitlines()[0] == "tally(n) -> None"


def test_hidden_and_returned_outputs_share_one_bridge(tmp_path: Path):
    """Only the binding distinguishes them; the native call is the same."""
    result, _, bridge = _build(
        tmp_path,
        "hidden_mixed",
        """from prik.contracts import Arg, Hidden, Int32, Return, Returns, String, native_call

@native_call([Arg(0), Return("doubled", 0), Hidden("note", String[16])])
def tally(n: Int32) -> Returns["doubled", Int32]: ...
""",
    )
    module = result.import_module()

    assert 'subroutine bind_c_tally(n, doubled, note) bind(c, name="bind_c_tally")' in bridge
    assert module.tally(np.int32(5)) == np.int32(10)
    assert module.tally.__doc__.splitlines()[0] == "tally(n) -> int32"


def test_hidden_outputs_do_not_leak_across_repeated_calls(tmp_path: Path):
    """A discarded output must not leak its adapter allocation or a reference."""
    result, _, _ = _build(
        tmp_path,
        "hidden_leak",
        """from prik.contracts import Arg, Hidden, Int32, String, native_call

@native_call([Arg(0), Hidden("doubled", Int32), Hidden("note", String[16])])
def tally(n: Int32) -> None: ...
""",
    )
    module = result.import_module()

    import sys

    def refcount_growth(calls: int) -> int:
        """Return how much ``None``'s refcount moved across ``calls`` calls."""
        value = np.int32(3)
        before = sys.getrefcount(None)
        for _ in range(calls):
            module.tally(value)
        return sys.getrefcount(None) - before

    refcount_growth(200)  # settle any first-call bookkeeping
    # A leaked reference scales with the call count; a fixed offset does not.
    assert refcount_growth(20_000) == refcount_growth(200)
