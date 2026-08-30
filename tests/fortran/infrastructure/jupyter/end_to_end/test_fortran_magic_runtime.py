"""Compiled Fortran-cell evidence for the IPython magic."""

from __future__ import annotations

from pathlib import Path
import shutil

from IPython.core.interactiveshell import InteractiveShell
import numpy as np
import pytest

import prik.jupyter.magic as magic_module
from prik.jupyter import load_ipython_extension


pytestmark = pytest.mark.fortran_end_to_end


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran")
def test_fortran_cell_compiles_once_and_publishes_its_declared_module(tmp_path: Path, monkeypatch):
    build_calls = 0
    build_fortran_extension = magic_module.build_fortran_extension

    def counting_build(*args, **kwargs):
        nonlocal build_calls
        build_calls += 1
        return build_fortran_extension(*args, **kwargs)

    monkeypatch.setattr(magic_module, "build_fortran_extension", counting_build)
    monkeypatch.setenv("PRIK_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "ipython"))
    shell = InteractiveShell()
    load_ipython_extension(shell)
    cell = """module maths
contains
    real(8) function square(x)
        real(8), intent(in) :: x
        square = x*x
    end function
end module
"""

    shell.run_cell_magic("fortran", "", cell)
    first_namespace = shell.user_ns["maths"]
    assert first_namespace.square(np.float64(4.0)) == np.float64(16.0)

    shell.run_cell_magic("fortran", "", cell)
    assert build_calls == 1
    assert shell.user_ns["maths"] is first_namespace


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran")
def test_generated_fortran_contract_can_be_edited_then_compiled_once(tmp_path: Path, monkeypatch):
    build_calls = 0
    build_pyi_extension = magic_module.build_pyi_extension

    def counting_build(*args, **kwargs):
        nonlocal build_calls
        build_calls += 1
        return build_pyi_extension(*args, **kwargs)

    monkeypatch.setattr(magic_module, "build_pyi_extension", counting_build)
    monkeypatch.setenv("PRIK_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "ipython"))
    shell = InteractiveShell()
    inserted: list[str] = []
    monkeypatch.setattr(shell, "set_next_input", lambda text, replace=False: inserted.append(text))
    load_ipython_extension(shell)
    source = """module maths
contains
    real(8) function square(x)
        real(8), intent(in) :: x
        square = x*x
    end function
end module
"""

    shell.run_cell_magic("fortran", "--pyi", source)

    assert len(inserted) == 1
    magic_line, contract = inserted[0].split("\n", 1)
    contract = contract.replace(
        "from prik.contracts import Addr, Arg, Float64, native_call",
        "from prik.contracts import Addr, Arg, Float64, bind, native_call",
    )
    contract = contract.replace("@native_call", '@bind("square")\n@native_call')
    contract = contract.replace("def square(", "def squared(")
    line = magic_line.removeprefix("%%pyi").strip()

    shell.run_cell_magic("pyi", line, contract)
    first_namespace = shell.user_ns["maths"]
    assert first_namespace.squared(np.float64(4.0)) == np.float64(16.0)
    assert not hasattr(first_namespace, "square")

    shell.run_cell_magic("pyi", line, contract)
    assert build_calls == 1
    assert shell.user_ns["maths"] is first_namespace


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran")
def test_generated_standalone_contract_publishes_direct_function(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PRIK_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "ipython"))
    shell = InteractiveShell()
    inserted: list[str] = []
    monkeypatch.setattr(shell, "set_next_input", lambda text, replace=False: inserted.append(text))
    load_ipython_extension(shell)
    source = """real(8) function square(x)
    real(8), intent(in) :: x
    square = x*x
end function
"""

    shell.run_cell_magic("fortran", "--pyi", source)

    magic_line, contract = inserted[0].split("\n", 1)
    assert " file=" not in contract
    assert "@standalone" in contract
    shell.run_cell_magic("pyi", magic_line.removeprefix("%%pyi").strip(), contract)

    assert shell.user_ns["square"](np.float64(4.0)) == np.float64(16.0)
    assert "cell" not in shell.user_ns
