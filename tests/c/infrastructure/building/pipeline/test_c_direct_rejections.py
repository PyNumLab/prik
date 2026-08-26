"""Pipeline boundary tests for fail-closed C direct adoption."""

import shutil
from pathlib import Path

import pytest

from prik import build_c_extension, build_pyi_extension
from prik.preprocessing import PreprocessingConfig


def test_unsupported_c_callback_fails_before_build_output_or_native_compilation(tmp_path: Path):
    source = tmp_path / "callback.c"
    output_dir = tmp_path / "build"
    source.write_text(
        "int identity(int value);\nvoid callback(void (*action)(int));\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="C_DIRECT_CALLBACK:action"):
        build_c_extension(
            source,
            preprocessing=PreprocessingConfig(mode="compiler", compiler="cc"),
            input_c_compiler="compiler-that-must-not-run",
            output_dir=output_dir,
        )

    assert not output_dir.exists()


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_later_c_module_blocker_fails_before_earlier_module_abi_probe(tmp_path: Path):
    primitive = tmp_path / "primitive.c"
    callback = tmp_path / "callback.c"
    output_dir = tmp_path / "build"
    primitive.write_text("int identity(int value);\n", encoding="utf-8")
    callback.write_text("void callback(void (*action)(int));\n", encoding="utf-8")

    with pytest.raises(ValueError, match="C_DIRECT_CALLBACK:action"):
        build_c_extension(
            [primitive, callback],
            preprocessing=PreprocessingConfig(mode="compiler", compiler="cc"),
            input_c_compiler="compiler-that-must-not-run",
            output_dir=output_dir,
        )

    assert not output_dir.exists()


def test_volatile_c_access_fails_before_build_output_or_native_compilation(tmp_path: Path):
    source = tmp_path / "volatile.c"
    output_dir = tmp_path / "build"
    source.write_text("void update(volatile int *value);\n", encoding="utf-8")

    with pytest.raises(ValueError, match="C_DIRECT_UNSUPPORTED_QUALIFIER:value"):
        build_c_extension(source, output_dir=output_dir)

    assert not output_dir.exists()


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_aggregate_fails_before_target_probe_or_build_output(tmp_path: Path):
    source = tmp_path / "aggregate.c"
    output_dir = tmp_path / "build"
    source.write_text(
        "struct pair { int left; int right; };\nint accept_pair(struct pair value);\n",
        encoding="utf-8",
    )

    # Source preparation uses a working preprocessor; the target ABI probe uses
    # the executable that must never run, so reaching it would fail differently.
    with pytest.raises(ValueError, match="C_DIRECT_AGGREGATE_TYPE:pair"):
        build_c_extension(
            source,
            preprocessing=PreprocessingConfig(mode="compiler", compiler="cc"),
            input_c_compiler="compiler-that-must-not-run",
            output_dir=output_dir,
        )

    assert not output_dir.exists()


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_native_global_state_fails_before_any_generated_adapter_source(tmp_path: Path):
    source = tmp_path / "globals.c"
    output_dir = tmp_path / "build"
    source.write_text("int scale(int value) { return value; }\nint gain = 2;\n", encoding="utf-8")

    with pytest.raises(ValueError, match="C_DIRECT_NATIVE_GLOBAL_STATE:gain"):
        build_c_extension(
            source,
            preprocessing=PreprocessingConfig(mode="compiler", compiler="cc"),
            input_c_compiler="compiler-that-must-not-run",
            output_dir=output_dir,
        )

    assert not output_dir.exists()


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_enum_constants_fail_before_wrapper_planning(tmp_path: Path):
    source = tmp_path / "enums.c"
    output_dir = tmp_path / "build"
    source.write_text("enum color { RED, GREEN };\nint pick(int value) { return value; }\n", encoding="utf-8")

    with pytest.raises(ValueError, match="C_DIRECT_ENUM_CONSTANT:RED"):
        build_c_extension(source, output_dir=output_dir)

    assert not output_dir.exists()


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_source_free_contract_module_variable_generates_no_fortran_adapter(tmp_path: Path):
    contract = tmp_path / "api.pyi"
    implementation = tmp_path / "implementation.c"
    output_dir = tmp_path / "build"
    contract.write_text(
        "from prik.contracts import Float64\n\ngain: Float64\n\ndef scale(value: Float64) -> Float64: ...\n",
        encoding="utf-8",
    )
    implementation.write_text("double gain = 2.0;\ndouble scale(double value) { return value; }\n", encoding="utf-8")

    with pytest.raises(ValueError, match="C_DIRECT_NATIVE_GLOBAL_STATE:gain"):
        build_pyi_extension(
            contract,
            native_language="c",
            native_c_sources=[implementation],
            output_dir=output_dir,
        )

    assert not output_dir.exists()


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_unmodeled_c_declaration_is_not_silently_dropped_from_the_public_api(tmp_path: Path):
    source = tmp_path / "attributes.c"
    output_dir = tmp_path / "build"
    source.write_text(
        "__attribute__((stdcall)) int convention(int value);\nint ordinary(int value) { return value; }\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="C_DIRECT_UNMODELED_DECLARATION"):
        build_c_extension(source, output_dir=output_dir)

    assert not output_dir.exists()


def test_raw_c_contract_address_fails_before_target_probe_or_build_output(tmp_path: Path):
    contract = tmp_path / "raw_address.pyi"
    implementation = tmp_path / "implementation.c"
    output_dir = tmp_path / "build"
    contract.write_text(
        "from prik.contracts import Addr, Int\n\ndef consume(value: Addr(Int)) -> Int: ...\n",
        encoding="utf-8",
    )
    implementation.write_text("int consume(int value) { return value; }\n", encoding="utf-8")

    with pytest.raises(ValueError, match="C_DIRECT_RAW_ADDRESS:value"):
        build_pyi_extension(
            contract,
            native_language="c",
            native_c_sources=[implementation],
            input_c_compiler="compiler-that-must-not-run",
            output_dir=output_dir,
        )

    assert not output_dir.exists()
