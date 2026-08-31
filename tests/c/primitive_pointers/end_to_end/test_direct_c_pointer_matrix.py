"""Compiled all-primitive evidence for source-generated C pointer contracts."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from prik import build_c_extension, build_pyi_extension
from prik.parsers.c import parse_c_file
from prik.preprocessing import PreprocessingConfig
from prik.preprocessing.probes.c_types import probe_c_standard_types
from prik.codegen.primitive_scalar_types import NativeCArrayStorageRegistry
from prik.contracts import NATIVE_C_SCALAR_IDENTITIES
from prik.semantics.c2ir import c_file_to_semantic_module
from prik.semantics.metadata import (
    NATIVE_C_ARRAY_ELEMENT_IDENTITY_METADATA,
    NATIVE_C_SCALAR_IDENTITY_METADATA,
)
from tests.c._support.runtime import sole_native_module


_C_PRIMITIVES = (
    ("bool", "_Bool"),
    ("char", "char"),
    ("signed_char", "signed char"),
    ("unsigned_char", "unsigned char"),
    ("short", "short"),
    ("unsigned_short", "unsigned short"),
    ("int", "int"),
    ("unsigned_int", "unsigned int"),
    ("long", "long"),
    ("unsigned_long", "unsigned long"),
    ("long_long", "long long"),
    ("unsigned_long_long", "unsigned long long"),
    ("float", "float"),
    ("double", "double"),
    ("long_double", "long double"),
    ("float_complex", "float _Complex"),
    ("double_complex", "double _Complex"),
    ("long_double_complex", "long double _Complex"),
    ("size", "size_t"),
)
_VALUES = {
    "Bool": True,
    "Bool8": True,
    "Int8": np.int8(-7),
    "UInt8": np.uint8(7),
    "Int16": np.int16(-300),
    "UInt16": np.uint16(300),
    "Int32": np.int32(-70000),
    "UInt32": np.uint32(70000),
    "Int64": np.int64(-7000000000),
    "UInt64": np.uint64(7000000000),
    "Float32": np.float32(1.25),
    "Float64": np.float64(1.25),
    "Float128": np.longdouble("1.25"),
    "Complex64": np.complex64(1.25 + 2.5j),
    "Complex128": np.complex128(1.25 + 2.5j),
    "Complex256": np.clongdouble(1.25 + 2.5j),
}


def _accepted_pointer_dtype(semantic_type, value) -> np.dtype:
    """Return the NumPy storage one generated pointer argument accepts.

    An array buffer reaches C as it already is, so its elements are the
    declared C type rather than another type of the same width. That keeps one
    accepted dtype per C spelling on every target, however the target resolves
    ``int64_t``. Only an element with no probed C primitive falls back to the
    canonical storage of the semantic type PRIK resolved.
    """
    identity = semantic_type.metadata.get(NATIVE_C_SCALAR_IDENTITY_METADATA)
    declared = (
        NATIVE_C_SCALAR_IDENTITIES[identity]
        if identity is not None
        else semantic_type.metadata.get(NATIVE_C_ARRAY_ELEMENT_IDENTITY_METADATA)
    )
    if not isinstance(declared, str):
        return np.asarray(value).dtype
    exact = NativeCArrayStorageRegistry.type_for(declared, semantic_type.name)
    return np.dtype(getattr(np, exact.python_type_name.removeprefix("numpy.")))


def _pointer_source() -> str:
    declarations = ["#include <stddef.h>", "#include <complex.h>"]
    for name, c_type in _C_PRIMITIVES:
        declarations.extend(
            (
                f"{c_type} pointer_read_{name}({c_type} *value) {{ return *value; }}",
                f"{c_type} const_pointer_read_{name}(const {c_type} *value) {{ return *value; }}",
            )
        )
    return "\n".join(declarations) + "\n"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_non_boolean_c_primitive_pointers_default_to_runtime_rank_numpy_storage(tmp_path: Path):
    """Source ``T *`` accepts rank-zero and ranked storage without selecting a fixed rank."""
    source = tmp_path / "pointer_defaults.c"
    source.write_text(_pointer_source(), encoding="utf-8")
    report = probe_c_standard_types(PreprocessingConfig(mode="compiler", compiler="cc"))
    semantic = c_file_to_semantic_module(parse_c_file(source), standard_type_report=report)
    result_types = {function.name: function.return_type.dtype for function in semantic.functions}
    functions = {function.name: function for function in semantic.functions}
    # A typedef spelling such as ``size_t`` is declared through the builtin the
    # probe resolved it to, because the binding writes the prototype itself.
    declared_types = {
        c_type: str(report.types.get(c_type, {}).get("underlying_c_type") or c_type) for _name, c_type in _C_PRIMITIVES
    }

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="pointer_defaults")
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    for name, c_type in _C_PRIMITIVES:
        value = _VALUES[result_types[f"pointer_read_{name}"]]
        for prefix in ("pointer_read", "const_pointer_read"):
            function_name = f"{prefix}_{name}"
            function = functions[function_name]
            call = getattr(module, function_name)
            if name == "bool":
                assert function.arguments[0].semantic_type.storage.kind == "reference"
                output = call(value)
                assert type(output) is bool and output is value
            else:
                array = function.arguments[0].semantic_type.storage.array
                assert array.category == "runtime_rank"
                assert array.shape == ["..."]
                dtype = _accepted_pointer_dtype(function.arguments[0].semantic_type, value)
                for storage in (np.array(value, dtype=dtype), np.array([value], dtype=dtype)):
                    output = call(storage)
                    assert output.dtype == np.asarray(value).dtype
                    assert output == value
        declared = declared_types[c_type]
        assert f"{declared} pointer_read_{name}({declared} * value);" in binding
        assert f"{declared} const_pointer_read_{name}(const {declared} * value);" in binding


def _source_free_pointer_contract(type_names: tuple[str, ...]) -> str:
    imports = ", ".join((*type_names, "Arg", "Return", "native_call"))
    declarations = [f"from prik.contracts import {imports}"]
    for type_name in type_names:
        declarations.extend(
            (
                "",
                '@native_call([Arg(0), Return("output", 0)])',
                f"def hidden_{type_name.lower()}(value: {type_name}) -> {type_name}: ...",
                "",
                f"def rank_zero_{type_name.lower()}(value: {type_name}[()]) -> None: ...",
            )
        )
    return "\n".join(declarations) + "\n"


def _source_free_pointer_implementation(type_to_c_type: dict[str, str]) -> str:
    declarations = ["#include <stddef.h>", "#include <complex.h>"]
    for type_name, c_type in type_to_c_type.items():
        suffix = type_name.lower()
        declarations.append(f"void hidden_{suffix}({c_type} value, {c_type} *output) {{ *output = value; }}")
        if type_name in {"Bool", "Bool8"}:
            declarations.append(f"void rank_zero_{suffix}({c_type} *value) {{ *value = !*value; }}")
        else:
            declarations.append(f"void rank_zero_{suffix}({c_type} *value) {{ *value += ({c_type})1; }}")
    return "\n".join(declarations) + "\n"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_every_c_primitive_supports_rank_zero_storage_and_hidden_output(tmp_path: Path):
    """Authoritative C contracts select the rank-zero and ``Return`` mechanisms."""
    source = tmp_path / "pointer_contracts.c"
    source.write_text(_pointer_source(), encoding="utf-8")
    report = probe_c_standard_types(PreprocessingConfig(mode="compiler", compiler="cc"))
    semantic = c_file_to_semantic_module(parse_c_file(source), standard_type_report=report)
    type_to_c_type: dict[str, str] = {}
    for function in semantic.functions:
        if function.name.startswith("const_pointer_read_"):
            continue
        name = function.name.removeprefix("pointer_read_")
        type_to_c_type.setdefault(function.return_type.dtype, dict(_C_PRIMITIVES)[name])

    contract = tmp_path / "pointer_contracts.pyi"
    type_names = tuple(sorted(type_to_c_type))
    contract.write_text(_source_free_pointer_contract(type_names), encoding="utf-8")
    source.write_text(_source_free_pointer_implementation(type_to_c_type), encoding="utf-8")

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
    )
    module = sole_native_module(result.import_module())

    for type_name in type_names:
        value = _VALUES[type_name]
        hidden = getattr(module, f"hidden_{type_name.lower()}")
        rank_zero = getattr(module, f"rank_zero_{type_name.lower()}")
        output = hidden(value)
        if type_name in {"Bool", "Bool8"}:
            assert type(output) is bool
            assert output is bool(value)
        else:
            assert output.dtype == np.asarray(value).dtype
            assert output == value

        storage = np.array(value)
        assert rank_zero(storage) is None
        if type_name in {"Bool", "Bool8"}:
            assert storage[()] == (not bool(value))
        else:
            assert storage[()] == np.asarray(value + 1, dtype=storage.dtype)[()]
