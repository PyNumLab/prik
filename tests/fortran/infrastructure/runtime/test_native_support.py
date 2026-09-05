"""Public native-binding support surface checks."""

import re

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


BACKEND_RECORD_V1 = (
    ("uint32_t", "struct_size"),
    ("uint32_t", "descriptor_kind"),
    ("uint32_t", "rank"),
    ("uint32_t", "descriptor_size"),
    ("int32_t", "cfi_type"),
    ("size_t", "element_size"),
    ("void *", "context"),
    ("prik_native_array_with_descriptor_fn", "with_descriptor"),
    ("prik_native_array_release_fn", "release"),
)


def _backend_record_fields(header: str) -> tuple[tuple[str, str], ...]:
    """Return the declared record in order, as (type, name) pairs."""
    # A struct body has no braces of its own, so this cannot span the record before it.
    body = re.search(r"typedef struct \{\n([^{}]*?)\n\} prik_native_array_backend;", header, re.S)
    assert body is not None, "prik_native_array_backend is not declared as one struct"
    fields = []
    for line in body.group(1).strip().splitlines():
        declaration = line.strip().rstrip(";")
        spelling, _, name = declaration.rpartition(" ")
        if name.startswith("*"):
            spelling, name = f"{spelling} *", name[1:]
        fields.append((spelling.strip(), name))
    return tuple(fields)


def test_the_backend_record_and_its_version_name_change_together():
    """The capsule name is the ABI version, so the record may not move under it.

    Nothing inside the record says which layout wrote it: a reader asks
    ``PyCapsule_GetPointer`` for the one version it understands, and every
    other producer is refused before a field is read.  That only holds while
    the name is renamed whenever the record changes -- and a same-width
    reordering, `descriptor_kind` and `rank` swapped say, would otherwise be
    read straight through by a consumer that still recognizes the name, since
    `struct_size` sees no difference.

    So the two are pinned here together.  If this test fails because the
    record genuinely changed, publish it under a new version name and update
    both halves; do not update the layout alone.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert '#define PRIK_NATIVE_ARRAY_BACKEND_CAPSULE_NAME "prik.native_array_backend.v1"' in header
    assert _backend_record_fields(header) == BACKEND_RECORD_V1


def test_native_array_backend_capsule_exposes_one_entry_point_and_its_readers():
    """One entry point reaches the descriptor; the readers validate a producer.

    The context is what that entry point needs to get there, and a release
    marks that context as this extension's to free.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    for name in (
        "prik_native_array_backend_capsule_new",
        "prik_native_array_backend_capsule_destructor",
        "prik_native_array_backend_from_capsule",
        "prik_native_array_backend_for_descriptor",
        "prik_native_array_backend_for_actual",
        "prik_native_array_backend_owned_descriptor",
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
