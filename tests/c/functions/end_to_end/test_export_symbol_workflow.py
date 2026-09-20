"""Compiled and CLI evidence for selecting functions from a private C include."""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import build_c_extension
from prik.preprocessing import PreprocessingConfig
from tests.c._support.paths import REPO_ROOT
from tests.c._support.runtime import sole_native_module


pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")


def _write_private_include_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    header = tmp_path / "reviewed_api.h"
    header.write_text(
        "extern int private_state;\nint increment(int __value);\nint omitted(int __value);\n",
        encoding="utf-8",
    )
    probe = tmp_path / "probe.c"
    probe.write_text('#include "reviewed_api.h"\n', encoding="utf-8")
    implementation = tmp_path / "implementation.c"
    implementation.write_text(
        '#include "reviewed_api.h"\nint increment(int value) { return value + 1; }\n',
        encoding="utf-8",
    )
    return header, probe, implementation


def _stated_exports(contract: Path) -> list[str]:
    """Return the ``__all__`` a generated contract states about itself."""
    module = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    for statement in module.body:
        targets = getattr(statement, "targets", [])
        if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            return [ast.literal_eval(element) for element in statement.value.elts]
    raise AssertionError(f"{contract} states no __all__")


def _generate_contract(probe: Path, exports: Path, contract: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            "--language",
            "c",
            str(probe),
            "--compiler",
            shutil.which("cc") or "cc",
            "--include-exposure",
            "roots-only",
            "--export-symbols",
            str(exports),
            "--out",
            str(contract),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_generate_pyi_selects_one_function_from_a_private_include(tmp_path: Path):
    _header, probe, _implementation = _write_private_include_project(tmp_path)
    exports = tmp_path / "exports.txt"
    exports.write_text("# reviewed public surface\nincrement\n", encoding="utf-8")
    contract = tmp_path / "api.pyi"

    _generate_contract(probe, exports, contract)

    text = contract.read_text(encoding="utf-8")
    assert "def increment(" in text
    assert "omitted" not in text
    assert "private_state" not in text
    assert _stated_exports(contract) == ["increment"]


def test_generated_all_states_the_selected_declarations_not_the_allowlist_lines(tmp_path: Path):
    """The allowlist selects declarations; __all__ states the Python names they publish."""
    header = tmp_path / "reviewed_api.h"
    header.write_text("int zulu(int __v);\nint alpha(int __v);\nint omitted(int __v);\n", encoding="utf-8")
    probe = tmp_path / "probe.c"
    probe.write_text('#include "reviewed_api.h"\n', encoding="utf-8")
    exports = tmp_path / "exports.txt"
    exports.write_text("# reviewed public surface\n\nalpha\n\nzulu\n", encoding="utf-8")
    contract = tmp_path / "api.pyi"

    _generate_contract(probe, exports, contract)

    # Declaration order, not allowlist order: the list follows the declarations
    # the selection kept, so comments, blank lines, and the file's own ordering
    # never reach it.
    assert _stated_exports(contract) == ["zulu", "alpha"]
    assert "omitted" not in contract.read_text(encoding="utf-8")


def test_a_repeated_allowlist_name_is_rejected_rather_than_stated_twice(tmp_path: Path):
    """A stated surface names each declaration once, so a repeat is a request error."""
    _header, probe, _implementation = _write_private_include_project(tmp_path)
    exports = tmp_path / "exports.txt"
    exports.write_text("increment\nincrement\n", encoding="utf-8")
    contract = tmp_path / "api.pyi"

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        _generate_contract(probe, exports, contract)

    assert "Repeated C function name in --export-symbols" in exc_info.value.stderr
    assert not contract.exists()


def test_source_build_reuses_selection_with_positional_and_collision_policies(tmp_path: Path):
    _header, probe, implementation = _write_private_include_project(tmp_path)
    preprocessing = PreprocessingConfig(
        mode="compiler",
        compiler=shutil.which("cc") or "cc",
        include_exposure="roots-only",
    )

    result = build_c_extension(
        probe,
        output_dir=tmp_path / "build",
        output_name="selected_api",
        input_c_compiler=shutil.which("cc") or "cc",
        preprocessing=preprocessing,
        export_symbols=["increment"],
        native_c_sources=[implementation],
        positional_only=True,
        collision_adapter_all=True,
    )
    module = sole_native_module(result.import_module())

    assert module.increment(np.int32(4)) == np.int32(5)
    with pytest.raises(TypeError, match="keyword"):
        module.increment(arg0=np.int32(4))
    assert {name for name in dir(module) if not name.startswith("_")} == {"increment"}
