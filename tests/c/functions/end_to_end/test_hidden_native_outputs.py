"""``Hidden`` declares native storage the Python signature never promises back.

A hidden slot is passed to the native call like any other output, but it is not
a Python result, so the return annotation states exactly what the caller gets.
"""

import shutil
from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension
from tests.c._support.runtime import sole_native_module

SOURCE = """void tally(int n, int *doubled, int *squared) {
    *doubled = n * 2;
    *squared = n * n;
}
"""


def _build(tmp_path: Path, contract: str, name: str):
    (tmp_path / f"{name}.pyi").write_text(contract, encoding="utf-8")
    (tmp_path / f"{name}.c").write_text(SOURCE, encoding="utf-8")
    return build_pyi_extension(
        tmp_path / f"{name}.pyi",
        native_language="c",
        native_c_sources=[tmp_path / f"{name}.c"],
        output_dir=tmp_path / f"build_{name}",
        output_name=name,
    )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_hidden_outputs_reach_the_native_call_without_becoming_results(tmp_path: Path):
    """Every hidden slot is passed by address; none of them is returned."""
    result = _build(
        tmp_path,
        """from prik.contracts import Arg, Hidden, Int32, bind, native_call

@bind("tally")
@native_call([Arg(0), Hidden("doubled", Int32), Hidden("squared", Int32)])
def tally(n: Int32) -> None: ...
""",
        "all_hidden",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "void tally(int32_t n, int32_t * doubled, int32_t * squared);" in binding
    assert module.tally(np.int32(5)) is None
    assert module.tally.__doc__.splitlines()[0] == "tally(n) -> None"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_hidden_and_returned_outputs_share_one_native_call(tmp_path: Path):
    """``Returns`` comes back and ``Hidden`` does not, from the same call."""
    result = _build(
        tmp_path,
        """from prik.contracts import Arg, Hidden, Int32, Return, Returns, bind, native_call

@bind("tally")
@native_call([Arg(0), Return("doubled", 0), Hidden("squared", Int32)])
def tally(n: Int32) -> Returns["doubled", Int32]: ...
""",
        "mixed_hidden",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    # Both outputs still cross the boundary; only one is a Python result.
    assert "void tally(int32_t n, int32_t * doubled, int32_t * squared);" in binding
    assert module.tally(np.int32(5)) == np.int32(10)
    assert module.tally.__doc__.splitlines()[0] == "tally(n) -> int32"
