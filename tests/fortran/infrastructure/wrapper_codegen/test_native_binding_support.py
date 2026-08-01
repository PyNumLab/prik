"""Public native-binding support surface checks."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SUPPORT_HEADER = ROOT / "x2py" / "binding_support" / "x2py_binding.h"
SUPPORT_SOURCE = ROOT / "x2py" / "binding_support" / "x2py_binding.c"


def test_native_binding_support_is_header_only_and_exposes_the_small_x2py_api():
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    assert not SUPPORT_SOURCE.exists()
    assert '#define X2PY_NATIVE_ARRAY_HANDLE_CAPSULE_NAME "x2py.native_array_handle.v1"' in header
    assert "#define X2PY_NATIVE_ARRAY_HANDLE_ABI_VERSION 1u" in header
    assert "typedef struct {" in header
    assert "x2py_native_array_release_fn release;" in header

    expected_api = (
        "x2py_native_array_handle_release",
        "x2py_native_array_handle_capsule_destructor",
        "x2py_native_array_handle_capsule_new",
        "x2py_native_array_handle_from_capsule",
        "x2py_array_actual_unpack",
        "x2py_array_validate",
        "x2py_release_owned_memory",
    )
    for name in expected_api:
        assert name in header
    assert "X2PY_NO_INLINE static int x2py_array_actual_unpack(" in header
    assert "static inline int x2py_array_validate(" in header
    assert "X2PY_ARRAY_LAYOUT_POSITIVE_STRIDED_F" in header
    assert "x2py_array_actual" in header

    scalar_suffixes = (
        "bool",
        "int8",
        "int16",
        "int32",
        "int64",
        "float32",
        "float64",
        "complex64",
        "complex128",
    )
    for suffix in scalar_suffixes:
        assert f"x2py_{suffix}_unpack_exact" in header
        assert f"x2py_{suffix}_unpack" in header
        assert f"x2py_{suffix}_to_python" in header
        assert f"x2py_{suffix}_to_numpy" in header
    assert header.count("static inline") == 42

    removed_compatibility_names = (
        "PyInt32_to_Int32",
        "Double_to_PyDouble",
        "Complex128_to_PyComplex",
        "capsule_cleanup",
        "pyarray_check",
        "to_pyarray",
    )
    for name in removed_compatibility_names:
        assert name not in header
