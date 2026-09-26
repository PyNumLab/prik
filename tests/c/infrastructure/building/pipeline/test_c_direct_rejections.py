"""Pipeline boundary tests for fail-closed C direct adoption.

Every row names a declaration outside the published direct-C boundary and
proves the build stops with its blocker code before writing build output.
Rows that pass ``compiler-that-must-not-run`` as the C compiler also prove the
blocker fires before the target ABI probe or any native compilation.
"""

import shutil
from pathlib import Path

import pytest

from prik import build_c_extension, build_pyi_extension
from prik.preprocessing import PreprocessingConfig

_NO_COMPILER = "compiler-that-must-not-run"
_REQUIRES_CC = pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")


def _compiler_preprocessing() -> dict[str, object]:
    # Source preparation uses a working preprocessor; the target ABI probe uses
    # the executable that must never run, so reaching it would fail differently.
    return {"preprocessing": PreprocessingConfig(mode="compiler", compiler="cc"), "input_c_compiler": _NO_COMPILER}


@pytest.mark.parametrize(
    ("sources", "options", "blocker"),
    [
        pytest.param(
            {"callback.c": "int identity(int value);\nvoid callback(void (*action)(int));\n"},
            _compiler_preprocessing(),
            "C_DIRECT_CALLBACK:action",
            id="callback-parameter",
        ),
        pytest.param(
            {"primitive.c": "int identity(int value);\n", "callback.c": "void callback(void (*action)(int));\n"},
            _compiler_preprocessing(),
            "C_DIRECT_CALLBACK:action",
            marks=_REQUIRES_CC,
            id="later-module-blocker-before-earlier-module-abi-probe",
        ),
        pytest.param(
            {"volatile.c": "void update(volatile int *value);\n"},
            {},
            "C_DIRECT_UNSUPPORTED_QUALIFIER:value",
            id="volatile-access",
        ),
        pytest.param(
            {"aggregate.c": "struct pair { int left; int right; };\nint accept_pair(struct pair value);\n"},
            _compiler_preprocessing(),
            "C_DIRECT_AGGREGATE_TYPE:pair",
            marks=_REQUIRES_CC,
            id="aggregate-by-value",
        ),
        pytest.param(
            {"globals.c": "int scale(int value) { return value; }\nint gain = 2;\n"},
            _compiler_preprocessing(),
            "C_DIRECT_NATIVE_GLOBAL_STATE:gain",
            marks=_REQUIRES_CC,
            id="native-global-state",
        ),
        pytest.param(
            {"enums.c": "enum color { RED, GREEN };\nint pick(int value) { return value; }\n"},
            {},
            "C_DIRECT_ENUM_CONSTANT:RED",
            marks=_REQUIRES_CC,
            id="enum-constants",
        ),
        pytest.param(
            {
                "attributes.c": "__attribute__((stdcall)) int convention(int value);\nint ordinary(int value) { return value; }\n"
            },
            {},
            "C_DIRECT_UNMODELED_DECLARATION",
            marks=_REQUIRES_CC,
            id="unmodeled-declaration-is-not-silently-dropped",
        ),
    ],
)
def test_c_source_outside_the_direct_boundary_fails_before_build_output(
    tmp_path: Path, sources: dict[str, str], options: dict[str, object], blocker: str
):
    paths = []
    for name, text in sources.items():
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        paths.append(path)
    output_dir = tmp_path / "build"

    with pytest.raises(ValueError, match=blocker):
        build_c_extension(paths if len(paths) > 1 else paths[0], output_dir=output_dir, **options)

    assert not output_dir.exists()


@pytest.mark.parametrize(
    ("contract", "implementation", "options", "blocker"),
    [
        pytest.param(
            "from prik.contracts import Float64\n\ngain: Float64\n\ndef scale(value: Float64) -> Float64: ...\n",
            "double gain = 2.0;\ndouble scale(double value) { return value; }\n",
            {},
            "C_DIRECT_NATIVE_GLOBAL_STATE:gain",
            marks=_REQUIRES_CC,
            id="module-variable-generates-no-fortran-adapter",
        ),
        pytest.param(
            "from prik.contracts import Addr, Int\n\ndef consume(value: Addr(Int)) -> Int: ...\n",
            "int consume(int value) { return value; }\n",
            {"input_c_compiler": _NO_COMPILER},
            "C_DIRECT_RAW_ADDRESS:value",
            id="raw-address-before-target-probe",
        ),
    ],
)
def test_c_contract_outside_the_direct_boundary_fails_before_build_output(
    tmp_path: Path, contract: str, implementation: str, options: dict[str, object], blocker: str
):
    contract_path = tmp_path / "api.pyi"
    implementation_path = tmp_path / "implementation.c"
    contract_path.write_text(contract, encoding="utf-8")
    implementation_path.write_text(implementation, encoding="utf-8")
    output_dir = tmp_path / "build"

    with pytest.raises(ValueError, match=blocker):
        build_pyi_extension(
            contract_path,
            native_language="c",
            native_c_sources=[implementation_path],
            output_dir=output_dir,
            **options,
        )

    assert not output_dir.exists()
