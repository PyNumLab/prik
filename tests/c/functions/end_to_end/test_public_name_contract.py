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
    """One naming decision reaches both, so the stub is readable and accurate."""
    module, contract = _build(
        tmp_path,
        "keyword_api",
        "int lambda(int value);\nint lambda_(int value);\nint ordinary(int value);\n",
        "int lambda(int v) { return v + 1; }\n"
        "int lambda_(int v) { return v + 2; }\n"
        "int ordinary(int v) { return v + 3; }\n",
        ["lambda", "lambda_", "ordinary"],
    )

    published = {name for name in dir(module) if not name.startswith("_")}
    assert published == set(_stated_exports(contract))
    # A name Python cannot bind is moved aside once, for the module and the
    # contract alike, and the C spelling is recorded rather than lost.
    assert published == {"lambda_", "lambda__2", "ordinary"}
    text = contract.read_text(encoding="utf-8")
    assert '@bind("lambda")' in text
    assert '@bind("lambda_")' in text


def test_a_generated_contract_is_readable_python(tmp_path: Path):
    """A contract exists to be re-read and edited, so it has to parse."""
    _module, contract = _build(
        tmp_path,
        "readable_api",
        "int lambda(int value);\n",
        "int lambda(int v) { return v + 1; }\n",
        ["lambda"],
    )

    ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))


def test_c_declarations_that_differ_only_in_case_stay_apart(tmp_path: Path):
    """C spells its declarations exactly, so two spellings are two functions."""
    module, contract = _build(
        tmp_path,
        "case_api",
        "int Foo(int value);\nint foo(int value);\n",
        "int Foo(int v) { return v + 1; }\nint foo(int v) { return v + 2; }\n",
        ["Foo", "foo"],
    )

    assert set(_stated_exports(contract)) == {"Foo", "foo"}
    # Each Python name reaches the C function that spells itself that way.
    assert module.Foo(np.int32(10)) == np.int32(11)
    assert module.foo(np.int32(10)) == np.int32(12)


def test_a_mixed_case_c_name_keeps_its_spelling(tmp_path: Path):
    """Folding case would rename a declaration C never asked to rename."""
    module, contract = _build(
        tmp_path,
        "mixed_case_api",
        "int BarBaz(int value);\n",
        "int BarBaz(int v) { return v + 1; }\n",
        ["BarBaz"],
    )

    assert _stated_exports(contract) == ["BarBaz"]
    assert module.BarBaz(np.int32(2)) == np.int32(3)
    assert "barbaz" not in contract.read_text(encoding="utf-8")
