"""Raw address contracts fail before wrapper source generation."""

from pathlib import Path

import pytest

from prik import build_pyi_extension


@pytest.mark.parametrize(
    ("contract_text", "message"),
    [
        (
            "from prik.contracts import Addr, Float64\n\n"
            "class particle:\n    value: Float64\n\n"
            "def invalid(value: Addr(particle)) -> None: ...\n",
            r"Addr\(WrappedType\) is not allowed",
        ),
        (
            "from prik.contracts import Addr, Arg, Float64, native_call\n\n"
            "@native_call([Addr(Arg(0))])\n"
            "def invalid(values: Float64[:]) -> None: ...\n",
            "only valid for primitive scalar values",
        ),
        (
            "from prik.contracts import Addr, Float64\n\ndef invalid(values: Addr(Float64[:])) -> None: ...\n",
            "raw arrays require a fully resolved rank and shape",
        ),
    ],
)
def test_pyi_python_api_rejects_invalid_address_contracts_before_codegen(
    tmp_path: Path,
    contract_text: str,
    message: str,
):
    contract = tmp_path / "invalid_address.pyi"
    contract.write_text(contract_text, encoding="utf-8")
    native_object = tmp_path / "native.o"
    native_object.touch()

    with pytest.raises(ValueError, match=message):
        build_pyi_extension(contract, native_objects=[native_object], output_dir=tmp_path / "build")

    assert not list((tmp_path / "build").glob("*_wrapper.*"))
