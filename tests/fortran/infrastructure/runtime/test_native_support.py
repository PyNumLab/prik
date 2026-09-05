"""Public native-binding support surface checks."""

from tests.fortran._support.paths import REPO_ROOT


SUPPORT_HEADER = REPO_ROOT / "prik" / "runtime" / "native_support" / "prik_binding.h"
SUPPORT_SOURCE = REPO_ROOT / "prik" / "runtime" / "native_support" / "prik_binding.c"


def test_native_binding_support_is_header_only_and_exposes_the_small_prik_api():
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    assert not SUPPORT_SOURCE.exists()

    assert "static inline int prik_array_validate(" in header
    assert "static inline int prik_array_validate_ndarray(" in header
    assert "PyArrayObject *array," in header
    assert header.count("PyArray_Check(value)") == 1
    assert "PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F" in header
    assert "prik_array_actual" in header
    assert "prik_release_owned_memory" in header
    assert "prik_capture_address" in header

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


def test_native_array_backend_capsule_states_one_version_and_one_entry_point():
    """The cross-extension array ABI: its version, layout, and validation.

    Independently generated extensions exchange array handles through this one
    capsule, so its name carries the version -- PyCapsule_GetPointer refuses a
    capsule created under any other name -- and the record carries only what a
    reader must compare before it interprets a descriptor it did not build.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert '#define PRIK_NATIVE_ARRAY_BACKEND_CAPSULE_NAME "prik.native_array_backend.v1"' in header
    # One entry point reaches the descriptor; the context is what it needs to
    # get there, and a release marks that context as this extension's to free.
    assert "prik_native_array_with_descriptor_fn with_descriptor;" in header
    assert "prik_native_array_release_fn release;" in header
    assert "void *context;" in header
    # The compatibility tags a reader compares before trusting the producer.
    for field in ("uint32_t struct_size;", "uint32_t descriptor_kind;", "uint32_t rank;"):
        assert field in header
    assert "uint32_t descriptor_size;" in header
    assert "int32_t cfi_type;" in header
    assert "size_t element_size;" in header
    # No second version word, and no per-operation table.
    assert "MAGIC" not in header
    assert "ABI_VERSION" not in header

    for name in (
        "prik_native_array_backend_capsule_new",
        "prik_native_array_backend_capsule_destructor",
        "prik_native_array_backend_from_capsule",
        "prik_native_array_backend_for_descriptor",
        "prik_native_array_backend_for_actual",
        "prik_native_array_backend_release",
        "prik_native_array_owned_with_descriptor",
    ):
        assert name in header


def test_native_array_backend_release_is_idempotent_and_never_frees_borrowed_storage():
    """Owned storage is released once; borrowed storage is never released here.

    A backend owns its context exactly when it carries a release callback, so a
    module variable's or a field's backend -- which carries none -- cannot reach
    the free below, and clearing the context makes an explicit close() and
    finalization both safe.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    start = header.index("static inline void prik_native_array_backend_release(")
    body = header[start : header.index("\n}\n", start)]

    assert "backend->release == NULL || backend->context == NULL" in body
    assert "backend->context = NULL;" in body
    assert "backend->release(context);" in body
    assert "free(context);" in body
    # A released owned backend reports itself closed rather than handing over
    # storage that is gone.
    reader = header[header.index("static inline prik_native_array_backend *prik_native_array_backend_from_capsule(") :]
    reader = reader[: reader.index("\n}\n")]
    assert "backend->release != NULL && backend->context == NULL" in reader
    assert "prik native array handle is closed" in reader


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
