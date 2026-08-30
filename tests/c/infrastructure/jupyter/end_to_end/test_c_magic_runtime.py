"""Compiled C-cell evidence for the IPython magic."""

from __future__ import annotations

from pathlib import Path
import shutil

import numpy as np
import pytest
from IPython.lib.pretty import pretty

import prik.jupyter.magic as magic_module
from prik.jupyter.magic import PrikMagics


class _Shell:
    def __init__(self) -> None:
        self.user_ns: dict[str, object] = {}
        self.next_inputs: list[str] = []

    def push(self, values: dict[str, object]) -> None:
        self.user_ns.update(values)

    def set_next_input(self, text: str, *, replace: bool = False) -> None:
        assert replace is False
        self.next_inputs.append(text)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_cell_compiles_once_and_publishes_direct_function(tmp_path: Path, monkeypatch):
    build_calls = 0
    build_c_extension = magic_module.build_c_extension

    def counting_build(*args, **kwargs):
        nonlocal build_calls
        build_calls += 1
        return build_c_extension(*args, **kwargs)

    monkeypatch.setattr(magic_module, "build_c_extension", counting_build)
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")
    cell = "double square(double x) { return x * x; }\n"

    magic.c("", cell)
    first_function = shell.user_ns["square"]
    assert first_function(np.float64(4.0)) == np.float64(16.0)
    assert first_function.__module__ is None
    assert pretty(first_function) == "<function square>"

    magic.c("", cell)
    assert build_calls == 1
    assert shell.user_ns["square"] is first_function


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_generated_c_contract_can_be_edited_then_compiled_once(tmp_path: Path, monkeypatch):
    build_calls = 0
    build_pyi_extension = magic_module.build_pyi_extension

    def counting_build(*args, **kwargs):
        nonlocal build_calls
        build_calls += 1
        return build_pyi_extension(*args, **kwargs)

    monkeypatch.setattr(magic_module, "build_pyi_extension", counting_build)
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")
    source = "double square(double x) { return x * x; }\n"

    magic.c("--pyi", source)

    assert len(shell.next_inputs) == 1
    magic_line, contract = shell.next_inputs[0].split("\n", 1)
    contract = contract.replace(
        "from prik.contracts import Float64",
        "from prik.contracts import Float64, bind",
    )
    contract = contract.replace("def square(", '@bind("square")\ndef squared(')
    line = magic_line.removeprefix("%%pyi").strip()

    magic.pyi(line, contract)
    first_function = shell.user_ns["squared"]
    assert first_function(np.float64(4.0)) == np.float64(16.0)
    assert first_function.__module__ is None
    assert pretty(first_function) == "<function squared>"
    assert "square" not in shell.user_ns

    magic.pyi(line, contract)
    assert build_calls == 1
    assert shell.user_ns["squared"] is first_function


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_handwritten_c_contract_builds_existing_source_and_reuses_exact_cell(
    tmp_path: Path,
    monkeypatch,
):
    build_calls = 0
    build_pyi_extension = magic_module.build_pyi_extension

    def counting_build(*args, **kwargs):
        nonlocal build_calls
        build_calls += 1
        return build_pyi_extension(*args, **kwargs)

    monkeypatch.setattr(magic_module, "build_pyi_extension", counting_build)
    source = tmp_path / "square.c"
    source.write_text("double square(double value) { return value * value; }\n", encoding="utf-8")
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")
    contract = """from prik.contracts import Float64

def square(value: Float64) -> Float64: ...
"""
    line = f"--native-c-sources {source}"

    magic.pyi(line, contract)

    first_function = shell.user_ns["square"]
    assert first_function(np.float64(4.0)) == np.float64(16.0)
    assert first_function.__module__ is None
    assert pretty(first_function) == "<function square>"

    magic.pyi(line, contract)
    assert build_calls == 1
    assert shell.user_ns["square"] is first_function
