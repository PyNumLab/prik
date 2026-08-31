"""Compiled Stage 3 arithmetic matrix for direct C entrypoints."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from prik import build_c_extension
from prik.parsers.c import parse_c_file
from prik.preprocessing import PreprocessingConfig
from prik.preprocessing.probes.c_types import probe_c_standard_types
from prik.semantics.c2ir import c_file_to_semantic_module
from tests.c._support.runtime import sole_native_module


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

_DTYPES = {name: np.asarray(value).dtype for name, value in _VALUES.items() if name not in {"Bool", "Bool8"}}


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_all_documented_c_arithmetic_spellings_return_exact_numpy_scalar_dtypes(tmp_path: Path):
    source = tmp_path / "arithmetic.c"
    source_text = """#include <stddef.h>
#include <complex.h>
_Bool bool_identity(_Bool value) { return value; }
char char_identity(char value) { return value; }
signed char signed_char_identity(signed char value) { return value; }
unsigned char unsigned_char_identity(unsigned char value) { return value; }
short short_identity(short value) { return value; }
unsigned short unsigned_short_identity(unsigned short value) { return value; }
int int_identity(int value) { return value; }
unsigned int unsigned_int_identity(unsigned int value) { return value; }
long long_identity(long value) { return value; }
unsigned long unsigned_long_identity(unsigned long value) { return value; }
long long long_long_identity(long long value) { return value; }
unsigned long long unsigned_long_long_identity(unsigned long long value) { return value; }
float float_identity(float value) { return value; }
double double_identity(double value) { return value; }
long double long_double_identity(long double value) { return value; }
float _Complex float_complex_identity(float _Complex value) { return value; }
double _Complex double_complex_identity(double _Complex value) { return value; }
long double _Complex long_double_complex_identity(long double _Complex value) { return value; }
size_t size_identity(size_t value) { return value; }
void no_result(void) {}
"""
    source.write_text(source_text, encoding="utf-8")
    report = probe_c_standard_types(PreprocessingConfig(mode="compiler", compiler="cc"))
    semantic = c_file_to_semantic_module(parse_c_file(source), standard_type_report=report)
    expected = {function.name: function.return_type.dtype for function in semantic.functions if function.return_type}

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="c_arithmetic")
    module = sole_native_module(result.import_module())

    for function_name, dtype_name in expected.items():
        value = _VALUES[dtype_name]
        output = getattr(module, function_name)(value)
        if dtype_name in {"Bool", "Bool8"}:
            assert type(output) is bool
        else:
            assert isinstance(output, np.generic)
            assert output.dtype == _DTYPES[dtype_name]
            assert output == value
        assert getattr(module, function_name)(output) == value
    assert module.no_result() is None
    with pytest.raises(TypeError, match=r"numpy\.uint8"):
        module.unsigned_char_identity(np.uint16(256))
    # A scalar crosses by value, so either 64-bit spelling is accepted and cast
    # to the exact native storage. Only an array buffer stays exact.
    assert module.long_long_identity(np.longlong(1)) == np.int64(1)
    assert module.long_long_identity(np.int64(1)) == np.int64(1)
