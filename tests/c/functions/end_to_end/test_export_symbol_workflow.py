"""Compiled and CLI evidence for selecting functions from a private C include."""

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


def test_generate_pyi_selects_one_function_from_a_private_include(tmp_path: Path):
    _header, probe, _implementation = _write_private_include_project(tmp_path)
    exports = tmp_path / "exports.txt"
    exports.write_text("# reviewed public surface\nincrement\n", encoding="utf-8")
    contract = tmp_path / "api.pyi"

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

    text = contract.read_text(encoding="utf-8")
    assert "def increment(" in text
    assert "omitted" not in text
    assert "private_state" not in text


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
