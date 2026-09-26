"""The contract a C build writes names exactly what that build publishes."""

import ast
import shutil
from pathlib import Path

import numpy as np
import pytest

from prik import build_c_extension
from prik.pipeline.build import BUILD_CONTRACT_DIRECTORY_NAME
from prik.preprocessing import PreprocessingConfig
from tests.c._support.runtime import sole_native_module


pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")


def _build(tmp_path: Path, name: str, header_text: str, implementation_text: str, symbols: list[str]):
    """Build one C extension from a private header and return it with its stub."""
    header = tmp_path / "api.h"
    header.write_text(header_text, encoding="utf-8")
    probe = tmp_path / "probe.c"
    probe.write_text('#include "api.h"\n', encoding="utf-8")
    implementation = tmp_path / "implementation.c"
    implementation.write_text(f'#include "api.h"\n{implementation_text}', encoding="utf-8")
    output_dir = tmp_path / "build"

    result = build_c_extension(
        probe,
        output_dir=output_dir,
        output_name=name,
        input_c_compiler=shutil.which("cc") or "cc",
        preprocessing=PreprocessingConfig(
            mode="compiler",
            compiler=shutil.which("cc") or "cc",
            include_exposure="roots-only",
        ),
        export_symbols=symbols,
        native_c_sources=[implementation],
    )
    contract = output_dir / BUILD_CONTRACT_DIRECTORY_NAME / "probe.pyi"
    return sole_native_module(result.import_module()), contract


def _stated_exports(contract: Path) -> list[str]:
    """Return the ``__all__`` a generated contract states about itself."""
    module = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    for statement in module.body:
        targets = getattr(statement, "targets", [])
        if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            return [ast.literal_eval(element) for element in statement.value.elts]
    raise AssertionError(f"{contract} states no __all__")


def test_a_contract_names_what_its_own_build_published(tmp_path: Path):
    """One naming decision reaches the module and its readable, parseable stub."""
    module, contract = _build(
        tmp_path,
        "public_names_api",
        "int lambda(int value);\nint lambda_(int value);\nint ordinary(int value);\n"
        "int Foo(int value);\nint foo(int value);\nint BarBaz(int value);\n",
        "int lambda(int v) { return v + 1; }\n"
        "int lambda_(int v) { return v + 2; }\n"
        "int ordinary(int v) { return v + 3; }\n"
        "int Foo(int v) { return v + 10; }\n"
        "int foo(int v) { return v + 20; }\n"
        "int BarBaz(int v) { return v + 30; }\n",
        ["lambda", "lambda_", "ordinary", "Foo", "foo", "BarBaz"],
    )

    # ``_stated_exports`` parses the stub, so the contract is readable Python.
    published = {name for name in dir(module) if not name.startswith("_")}
    assert published == set(_stated_exports(contract))
    # A name Python cannot bind is moved aside once, for the module and the
    # contract alike, and the C spelling is recorded rather than lost.
    assert published == {"lambda_", "lambda__2", "ordinary", "Foo", "foo", "BarBaz"}
    text = contract.read_text(encoding="utf-8")
    assert '@bind("lambda")' in text
    assert '@bind("lambda_")' in text
    # C spells its declarations exactly: two spellings are two functions, and
    # a mixed-case name is never folded.
    assert module.Foo(np.int32(1)) == np.int32(11)
    assert module.foo(np.int32(1)) == np.int32(21)
    assert module.BarBaz(np.int32(1)) == np.int32(31)
    assert "barbaz" not in text
