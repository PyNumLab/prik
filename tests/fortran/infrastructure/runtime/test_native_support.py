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


BACKEND_RECORD = (
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
        spelling, _, name = line.strip().rstrip(";").rpartition(" ")
        if name.startswith("*"):
            spelling, name = f"{spelling} *", name[1:]
        fields.append((spelling.strip(), name))
    return tuple(fields)


def _layout_tag_members(header: str) -> tuple[str, ...]:
    """Return the field names the layout tag folds, in the order it folds them."""
    body = re.search(r"\} layout\[\] = \{(.*?)\};", header, re.S)
    assert body is not None, "the layout tag does not declare what it folds"
    return tuple(re.findall(r"PRIK_NATIVE_ARRAY_BACKEND_FIELD\((\w+)\)", body.group(1)))


def test_the_capsule_name_is_derived_from_the_whole_record():
    """Two extensions agree on the name exactly when they agree on the record.

    A capsule carries an address and C has no runtime types, so a reader
    interprets it with offsets its own compiler baked in.  Comparing a version
    field cannot settle a disagreement -- reading the field already assumes the
    layout in question -- and it fails worst on `context`, `with_descriptor`
    and `release`, which are opaque addresses nothing can sanity-check before
    one of them is called.

    So the record names its own capsule, and there is no version number beside
    the tag because nothing is left for one to distinguish: each field folds in
    its name as well as its offset and width, so a field that keeps its shape
    and takes on a new meaning is caught too, as long as it is renamed to say
    so.  Every field must contribute, or a change to the one it forgot would
    keep the old name -- so the record and the tag must list the same fields in
    the same order.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert '#define PRIK_NATIVE_ARRAY_BACKEND_CAPSULE_PREFIX "prik.native_array_backend"' in header
    assert _backend_record_fields(header) == BACKEND_RECORD
    assert _layout_tag_members(header) == tuple(name for _spelling, name in BACKEND_RECORD)
    # Name, offset and width all come from the one token naming the field.
    assert (
        "{#member, offsetof(prik_native_array_backend, member), "
        "sizeof(((prik_native_array_backend *)0)->member)}" in header
    )
    # The size goes in first, so a change that only moves the tail is caught too.
    assert "tag = (tag ^ (uint64_t)sizeof(prik_native_array_backend))" in header
    # And the name is folded, which is what makes a rename reach every reader.
    assert "for (character = layout[index].name; *character != '\\0'; ++character)" in header


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
        "prik_native_array_backend_layout_tag",
        "prik_native_array_backend_capsule_name",
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
