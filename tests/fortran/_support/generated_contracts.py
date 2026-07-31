"""Generated `.pyi` fixture assertions for source-driven Fortran subjects."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture
from tests.fortran._support.wrapper_build import wrapper_source


@dataclass(frozen=True)
class GeneratedContractCase:
    name: str
    inputs: tuple[Path, ...]
    expected_package: Path
    language: str | None = None


def source_contract_case(contract_root: Path, filename: str) -> GeneratedContractCase:
    source = wrapper_source(filename)
    return GeneratedContractCase(source.stem, (source,), contract_root / source.stem)


def contract_case_id(case: GeneratedContractCase) -> str:
    return case.name


def assert_generated_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path) -> None:
    generated_package = tmp_path / case.name / "generated"
    language_args = ["--language", case.language] if case.language is not None else []
    command = [
        sys.executable,
        "-m",
        "x2py",
        "generate",
        "--pyi",
        *(str(path) for path in case.inputs),
        *language_args,
        "--out",
        str(generated_package),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    assert result.returncode == 0, (
        "generated .pyi contract command failed\n"
        f"command: {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert_generated_pyi_package_matches_fixture(generated_package, case.expected_package)
