"""Public native-binding support surface checks."""

from tests.fortran._support.paths import REPO_ROOT


SUPPORT_HEADER = REPO_ROOT / "prik" / "runtime" / "native_support" / "prik_binding.h"
SUPPORT_SOURCE = REPO_ROOT / "prik" / "runtime" / "native_support" / "prik_binding.c"


def test_native_binding_support_is_header_only_and_exposes_the_small_prik_api():
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    assert not SUPPORT_SOURCE.exists()
    assert '#define PRIK_NATIVE_ARRAY_HANDLE_CAPSULE_NAME "prik.native_array_handle.v1"' in header
    assert "#define PRIK_NATIVE_ARRAY_HANDLE_ABI_VERSION 1u" in header
    assert "typedef struct {" in header
    assert "prik_native_array_release_fn release;" in header

    expected_api = (
        "prik_native_array_handle_release",
        "prik_native_array_handle_capsule_destructor",
        "prik_native_array_handle_capsule_new",
        "prik_native_array_handle_from_capsule",
        "prik_array_actual_unpack",
        "prik_array_validate",
        "prik_release_owned_memory",
        "prik_capture_address",
    )
    for name in expected_api:
        assert name in header
    assert "PRIK_NO_INLINE static int prik_array_actual_unpack(" in header
    assert "static inline int prik_array_validate(" in header
    assert "static inline int prik_array_validate_ndarray(" in header
    assert "PyArrayObject *array," in header
    assert header.count("PyArray_Check(value)") == 1
    assert "PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F" in header
    assert "prik_array_actual" in header

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
        assert f"prik_{suffix}_unpack_exact" in header
        assert f"prik_{suffix}_unpack" in header
        assert f"prik_{suffix}_to_python" in header
        assert f"prik_{suffix}_to_numpy" in header


def test_address_capture_primitive_has_external_linkage_behind_one_opt_in():
    """The one support symbol the generated Fortran bridge links against.

    Every other helper here is `static`, which the bridge could not call. This
    one stands in for `c_loc` where Fortran cannot form it, so it must be
    externally visible -- and therefore defined in exactly one translation unit,
    which the opt-in macro is what enforces.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert "#ifdef PRIK_BINDING_CAPTURE_ADDRESS" in header
    assert "void *prik_capture_address(void *base)" in header
    assert "static inline void *prik_capture_address" not in header
