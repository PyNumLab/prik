"""Direct C ``Hidden`` storage never becomes part of the Python result.

A hidden slot is passed to the native call like any other output, but it is not
a Python result, so the return annotation states exactly what the caller gets.
Every output form shares one module-scoped build.
"""

import shutil

import numpy as np
import pytest

from prik import build_pyi_extension
from tests.c._support.runtime import sole_native_module


pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")

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

CONTRACT = """from prik.contracts import Arg, Hidden, Int, Int32, Return, Returns, bind, native_call

@bind("tally")
@native_call([Arg(0), Hidden("doubled", Int32), Hidden("squared", Int32)])
def tally_hidden(n: Int32) -> None: ...

@bind("tally")
@native_call([Arg(0), Return("doubled", 0), Hidden("squared", Int32)])
def tally_mixed(n: Int32) -> Returns["doubled", Int32]: ...

@native_call([Arg(0), Return("copy", 1)])
def split_target_int(value: Int) -> tuple[Int, Returns["copy", Int]]: ...

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
"""


@pytest.fixture(scope="module")
def outputs_build(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("c_hidden_outputs")
    (tmp_path / "outputs.pyi").write_text(CONTRACT, encoding="utf-8")
    (tmp_path / "outputs.c").write_text(SOURCE, encoding="utf-8")
    result = build_pyi_extension(
        tmp_path / "outputs.pyi",
        native_language="c",
        native_c_sources=[tmp_path / "outputs.c"],
        output_dir=tmp_path / "build",
        output_name="outputs",
    )
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")
    return binding, sole_native_module(result.import_module())


def test_hidden_and_returned_outputs_reach_the_native_call(outputs_build):
    """Every hidden slot is passed by address; only ``Returns`` comes back."""
    binding, module = outputs_build

    assert "void tally(int32_t n, int32_t * doubled, int32_t * squared);" in binding
    assert module.tally_hidden(np.int32(5)) is None
    assert module.tally_hidden.__doc__.splitlines()[0] == "tally_hidden(n) -> None"
    # Both outputs still cross the boundary; only one is a Python result.
    assert module.tally_mixed(np.int32(5)) == np.int32(10)
    assert module.tally_mixed.__doc__.splitlines()[0] == "tally_mixed(n) -> int32"


def test_target_c_int_hidden_output_keeps_int_pointer_abi(outputs_build):
    """A projected ``Int`` output resolves storage without losing C identity."""
    binding, module = outputs_build

    assert "int split_target_int(int value, int * copy);" in binding
    assert module.split_target_int(np.intc(7)) == (np.intc(0), np.intc(7))


def test_four_returned_outputs_compile_and_use_shared_failure_cleanup(outputs_build):
    """A linear cleanup suffix preserves the successful four-result surface."""
    binding, module = outputs_build

    assert module.split_four(np.int32(5)) == tuple(np.int32(value) for value in (10, 15, 20, 25))
    assert "goto prik_output_cleanup_4;" in binding
    assert binding.count("Py_XDECREF(result_0_obj);") == 1
