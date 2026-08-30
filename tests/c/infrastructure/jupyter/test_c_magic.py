"""Notebook magic contracts owned by C source cells."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import ModuleType

import prik.jupyter.contracts as contract_cells
import prik.jupyter.magic as magic_module
from prik.jupyter.magic import PrikMagics
from prik.pipeline.build import WrapperBuildResult


class _Shell:
    def __init__(self) -> None:
        self.user_ns: dict[str, object] = {}
        self.next_inputs: list[tuple[str, bool]] = []

    def push(self, values: dict[str, object]) -> None:
        self.user_ns.update(values)

    def set_next_input(self, text: str, *, replace: bool = False) -> None:
        self.next_inputs.append((text, replace))


def test_c_magic_routes_compiler_flags_and_publishes_direct_declarations(tmp_path: Path, monkeypatch):
    modules: dict[str, ModuleType] = {}
    calls: list[tuple[Path, dict[str, object]]] = []

    def build(source: Path, **kwargs) -> WrapperBuildResult:
        calls.append((source, kwargs))
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        module_name = str(kwargs["output_name"])
        shared_library = output_dir / f"{module_name}.so"
        shared_library.write_bytes(b"mock extension")
        extension = ModuleType(module_name)

        def square(value):
            return value * value

        extension.square = square
        modules[module_name] = extension
        return WrapperBuildResult(
            sources=(source,),
            module_name=module_name,
            output_dir=output_dir,
            shared_library=shared_library,
            build_makefile=None,
            compiled=True,
            generated_sources=(),
            generated_files=(),
        )

    monkeypatch.setattr(magic_module, "build_c_extension", build)
    monkeypatch.setattr(WrapperBuildResult, "import_module", lambda self: modules[self.module_name])
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")

    magic.c(
        '--compiler clang --native-compile-flags="-O3 -std=c11"',
        "double square(double x) { return x * x; }\n",
    )

    source, kwargs = calls[0]
    assert source.name == "cell.c"
    assert kwargs["input_c_compiler"] == "clang"
    assert kwargs["preprocessing"].compiler == "clang"
    assert kwargs["native_c_flags"] == ("-O3", "-std=c11")
    assert shell.user_ns["square"](4.0) == 16.0
    assert "cell" not in shell.user_ns
    assert all(not name.startswith("_prik_") for name in shell.user_ns)


def test_generated_c_contract_has_no_artificial_filename_and_builds_against_cached_source(
    tmp_path: Path,
    monkeypatch,
):
    modules: dict[str, ModuleType] = {}
    calls: list[tuple[Path, dict[str, object]]] = []

    def generate(path: Path, *, source_digest: str, options) -> contract_cells.GeneratedContracts:
        return contract_cells.GeneratedContracts(
            language="c",
            source_digest=source_digest,
            module_contracts={},
            direct_contract="def square(value: Float64) -> Float64: ...",
            dependency_contracts={},
        )

    def build(contract: Path, **kwargs) -> WrapperBuildResult:
        calls.append((contract, kwargs))
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        module_name = str(kwargs["output_name"])
        shared_library = output_dir / f"{module_name}.so"
        shared_library.write_bytes(b"mock extension")
        extension = ModuleType(module_name)
        extension.square = lambda value: value * value
        modules[module_name] = extension
        return WrapperBuildResult(
            sources=(contract,),
            module_name=module_name,
            output_dir=output_dir,
            shared_library=shared_library,
            build_makefile=None,
            compiled=True,
            generated_sources=(),
            generated_files=(),
        )

    monkeypatch.setattr(contract_cells, "generate_contracts_from_source", generate)
    monkeypatch.setattr(magic_module, "build_pyi_extension", build)
    monkeypatch.setattr(WrapperBuildResult, "import_module", lambda self: modules[self.module_name])
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")
    source = "double square(double value) { return value * value; }\n"

    magic.c(
        '--pyi --compiler clang --native-compile-flags="-O3 -std=c11"',
        source,
    )
    inserted = shell.next_inputs[0][0]
    magic_line, editable_cell = inserted.split("\n", 1)
    digest = hashlib.sha256(f"c{source}".encode()).hexdigest()
    assert f"# prik: source-sha256={digest}" in editable_cell
    assert " file=" not in editable_cell

    magic.pyi(magic_line.removeprefix("%%pyi").strip(), editable_cell)

    contract, kwargs = calls[0]
    assert kwargs["native_language"] == "c"
    assert kwargs["input_c_compiler"] == "clang"
    assert kwargs["native_c_sources"] == (tmp_path / "cache" / digest / "cell.c",)
    assert kwargs["native_c_flags"] == ("-O3", "-std=c11")
    assert contract.name == "contract.pyi"
    assert shell.user_ns["square"](4.0) == 16.0
