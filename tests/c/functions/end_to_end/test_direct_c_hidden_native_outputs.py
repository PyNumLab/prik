"""Direct C ``Hidden`` storage never becomes part of the Python result.

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

void split_four(int n, int *doubled, int *tripled, int *quadrupled, int *quintupled) {
    *doubled = n * 2;
    *tripled = n * 3;
    *quadrupled = n * 4;
    *quintupled = n * 5;
}

int split_target_int(int value, int *copy) {
    *copy = value;
    return 0;
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
def test_target_c_int_hidden_output_keeps_int_pointer_abi(tmp_path: Path):
    """A projected ``Int`` output resolves storage without losing C identity."""
    result = _build(
        tmp_path,
        """from prik.contracts import Arg, Int, Return, Returns, native_call

@native_call([Arg(0), Return("copy", 1)])
def split_target_int(value: Int) -> tuple[Int, Returns["copy", Int]]: ...
""",
        "target_int_output",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "int split_target_int(int value, int * copy);" in binding
    assert module.split_target_int(np.intc(7)) == (np.intc(0), np.intc(7))


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


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_four_returned_outputs_compile_and_use_shared_failure_cleanup(tmp_path: Path):
    """A linear cleanup suffix preserves the successful four-result surface."""
    result = _build(
        tmp_path,
        """from prik.contracts import Arg, Int32, Return, Returns, bind, native_call

@bind("split_four")
@native_call([
    Arg(0),
    Return("doubled", 0),
    Return("tripled", 1),
    Return("quadrupled", 2),
    Return("quintupled", 3),
])
def split_four(n: Int32) -> tuple[
    Returns["doubled", Int32],
    Returns["tripled", Int32],
    Returns["quadrupled", Int32],
    Returns["quintupled", Int32],
]: ...
""",
        "four_returned",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert module.split_four(np.int32(5)) == tuple(np.int32(value) for value in (10, 15, 20, 25))
    assert "goto prik_output_cleanup_4;" in binding
    assert binding.count("Py_XDECREF(result_0_obj);") == 1
