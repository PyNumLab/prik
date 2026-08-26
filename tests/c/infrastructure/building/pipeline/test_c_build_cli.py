"""CLI evidence for explicit C wrapper-build inputs."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import build_c_extension, build_pyi_extension, build_pyi_extension_from_manifest
from tests.c._support.paths import REPO_ROOT
from tests.c._support.runtime import sole_native_module


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_cli_builds_a_c_source_only_when_the_c_language_is_explicit(tmp_path: Path):
    source = tmp_path / "answer.c"
    source.write_text("int answer(int value) { return value + 1; }\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "--language",
            "c",
            str(source),
            "--out-dir",
            str(tmp_path / "build"),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert Path(payload["shared_library"]).is_file()
    assert payload["native_build_plan"]["compilation_units"][0]["language"] == "c"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_cli_marks_a_source_free_pyi_contract_as_c_native_explicitly(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    contract.write_text("from prik.contracts import Int\ndef add(value: Int) -> Int: ...\n", encoding="utf-8")
    source = tmp_path / "implementation.c"
    source.write_text("int add(int value) { return value + 1; }\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "--language",
            "c",
            str(contract),
            "--native-c-sources",
            str(source),
            "--out-dir",
            str(tmp_path / "build"),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["manifest"]["extension"]["native_language"] == "c"
    assert payload["native_build_plan"]["compilation_units"][0]["language"] == "c"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_native_manifest_replay_and_makefile_retain_the_c_language(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    contract.write_text("from prik.contracts import Int\ndef add(value: Int) -> Int: ...\n", encoding="utf-8")
    source = tmp_path / "implementation.c"
    source.write_text("int add(int value) { return value + 1; }\n", encoding="utf-8")

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
        makefile=True,
    )

    assert result.build_manifest is not None
    assert result.build_makefile is not None
    assert result.manifest["extension"]["native_language"] == "c"
    makefile = result.build_makefile.read_text(encoding="utf-8")
    assert "CC :=" in makefile
    assert "implementation.c" in makefile
    assert all(path.suffix != ".f90" for path in result.generated_sources)

    replay = build_pyi_extension_from_manifest(result.build_manifest)
    module = sole_native_module(replay.import_module())
    assert module.add(np.int32(4)) == np.int32(5)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_manifest_replay_rejects_a_changed_contract_graph_before_compiler_selection(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    contract.write_text("from prik.contracts import Int\ndef add(value: Int) -> Int: ...\n", encoding="utf-8")
    source = tmp_path / "implementation.c"
    source.write_text("int add(int value) { return value + 1; }\n", encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
        makefile=True,
    )
    manifest = json.loads(result.build_manifest.read_text(encoding="utf-8"))
    manifest["contract_paths"].append("contract-that-was-not-recorded.pyi")
    result.build_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="import graph does not match"):
        build_pyi_extension_from_manifest(
            result.build_manifest,
            input_c_compiler="compiler-that-must-not-run",
        )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_verbose_c_build_reports_c_compilation_and_link_commands(tmp_path: Path, capsys):
    source = tmp_path / "answer.c"
    source.write_text("int answer(int value) { return value + 1; }\n", encoding="utf-8")

    build_c_extension(source, output_dir=tmp_path / "build", verbose=True)

    output = capsys.readouterr().out
    assert "cc" in output
    assert "-shared" in output


@pytest.mark.skipif(
    shutil.which("gcc") is None or shutil.which("gfortran") is None,
    reason="requires a matching GNU C and Fortran compiler pair",
)
def test_c_direct_symbol_survives_a_mixed_language_link_with_the_fortran_driver(tmp_path: Path, capsys):
    source = tmp_path / "answer.c"
    fortran_dependency = tmp_path / "dependency.f90"
    source.write_text("int answer(int value) { return value + 1; }\n", encoding="utf-8")
    fortran_dependency.write_text(
        "subroutine linked_dependency() bind(C)\nend subroutine linked_dependency\n",
        encoding="utf-8",
    )

    result = build_c_extension(
        source,
        native_fortran_sources=[fortran_dependency],
        output_dir=tmp_path / "build",
        verbose=True,
    )
    module = sole_native_module(result.import_module())

    assert module.answer(np.int32(4)) == np.int32(5)
    assert {unit.language for unit in result.native_build_plan.compilation_units} == {"c", "fortran"}
    build_output = capsys.readouterr().out
    assert "gcc" in build_output
    assert "gfortran" in build_output


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("make") is None or shutil.which("cc") is None,
    reason="requires GNU Make, a POSIX shell, and a C compiler",
)
def test_generated_c_makefile_builds_an_importable_extension_from_relative_paths(tmp_path: Path):
    """A generated Makefile must run on a clean tree, not only after a build."""
    source = tmp_path / "src" / "answer.c"
    source.parent.mkdir()
    source.write_text("int answer(int value) { return value + 1; }\n", encoding="utf-8")

    generated = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--makefile",
            "--language",
            "c",
            "src/answer.c",
            "--out-dir",
            "build",
            "--compiler",
            "cc",
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    makefile = Path(json.loads(generated.stdout)["build_makefile"])
    subprocess.run(
        ["make", "-j4", "-f", str(makefile), "all"], cwd=tmp_path, capture_output=True, text=True, check=True
    )

    sys.modules.pop("answer", None)
    sys.path.insert(0, str(tmp_path / "build"))
    try:
        module = sole_native_module(importlib.import_module("answer"))
        assert module.answer(np.int32(4)) == np.int32(5)
    finally:
        sys.path.remove(str(tmp_path / "build"))
        sys.modules.pop("answer", None)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_saved_c_contract_describes_only_the_wrapped_translation_unit(tmp_path: Path):
    """Preprocessed headers stay inspection facts, not part of the built API."""
    source = tmp_path / "mathlib.c"
    source.write_text(
        """#include <stddef.h>
#include <math.h>

#define DEFAULT_GAIN 2.0

double amplify(double value) { return value * DEFAULT_GAIN; }
double hypotenuse(double a, double b) { return sqrt(a * a + b * b); }
""",
        encoding="utf-8",
    )

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="mathlib")
    module = sole_native_module(result.import_module())
    contract_path = tmp_path / "build" / "contracts" / "mathlib.pyi"
    package_path = tmp_path / "build" / "contracts" / "__init__.pyi"
    contract = contract_path.read_text(encoding="utf-8")

    assert contract_path in result.generated_files
    assert package_path in result.generated_files
    assert module.amplify(np.float64(3.0)) == np.float64(6.0)
    assert module.hypotenuse(np.float64(3.0), np.float64(4.0)) == np.float64(5.0)
    assert "def amplify(" in contract
    assert "def hypotenuse(" in contract
    assert "private" not in contract
    assert "__fpclassify" not in contract
    assert "signgam" not in contract

    # The saved contract is the input of the next build without editing.
    replay = build_pyi_extension(
        tmp_path / "build" / "contracts" / "mathlib.pyi",
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "replay",
        output_name="mathlib_replay",
    )
    replayed = sole_native_module(replay.import_module())
    assert replayed.amplify(np.float64(3.0)) == np.float64(6.0)
