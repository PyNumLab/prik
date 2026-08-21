"""Public C starter contracts preserve pointer ambiguity for author edits."""

import subprocess
import sys
from pathlib import Path

from tests.c._support.paths import REPO_ROOT


def test_c_starter_contract_preserves_every_documented_pointer_row(tmp_path: Path):
    source = REPO_ROOT / "tests/c/primitive_pointers/fixtures/native/starter_contracts.c"
    output = tmp_path / "starter_contracts.pyi"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--language",
            "c",
            "--out",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    contract = output.read_text(encoding="utf-8")
    assert "def by_value(\n    value: Float64\n) -> Float64" in contract
    assert contract.count("@native_call([Addr(Arg(0))])") == 2
    assert "def scalar_reference(\n    value: Float64\n) -> None" in contract
    assert "def const_scalar_reference(\n    value: Float64\n) -> None" in contract
    assert "def unsupported_multiple_reference(\n    value: Addr[2](Float64)\n) -> None" in contract
    assert "def primitive_result() -> Float64" in contract
    assert "def unsupported_pointer_result() -> Addr(Float64)" in contract
