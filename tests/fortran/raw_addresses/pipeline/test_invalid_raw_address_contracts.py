"""Raw address contracts fail before wrapper source generation."""

from pathlib import Path

import pytest

from prik import build_pyi_extension


def test_pyi_python_api_rejects_invalid_address_contracts_before_codegen(tmp_path: Path):
    """The public build stops at policy completion; every diagnostic is covered in semantics."""
    contract = tmp_path / "invalid_address.pyi"
    contract.write_text(
        "from prik.contracts import Addr, Float64\n\n"
        "class particle:\n    value: Float64\n\n"
        "def invalid(value: Addr(particle)) -> None: ...\n",
        encoding="utf-8",
    )
    native_object = tmp_path / "native.o"
    native_object.touch()

    with pytest.raises(ValueError, match=r"Addr\(WrappedType\) is not allowed"):
        build_pyi_extension(contract, native_objects=[native_object], output_dir=tmp_path / "build")

    assert not list((tmp_path / "build").glob("*_wrapper.*"))
