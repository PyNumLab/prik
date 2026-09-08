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
    ("uint32_t", "descriptor_attribute"),
    ("uint32_t", "rank"),
    ("uint32_t", "descriptor_size"),
    ("int32_t", "cfi_type"),
    ("size_t", "element_size"),
    ("uint32_t", "context_kind"),
    ("uint64_t", "owner_abi"),
    ("uint64_t", "owner_signature"),
    ("void *", "context"),
    ("prik_native_array_with_descriptor_fn", "with_descriptor"),
    ("prik_native_array_release_fn", "release"),
    ("uint32_t", "active_calls"),
    ("uint32_t", "release_pending"),
    ("uint32_t", "capsule_released"),
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


def test_the_capsule_name_covers_semantic_version_and_the_whole_record():
    """The name protects the callback contract and the compiled record layout."""
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert '#define PRIK_NATIVE_ARRAY_BACKEND_CAPSULE_PREFIX "prik.native_array_backend.v2"' in header
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

    assert "invalid prik native array descriptor attribute" in header
    assert "backend->descriptor_attribute != expected_descriptor_attribute" in header
    assert "does not expose the descriptor attribute required by the dummy argument" in header


def test_native_array_backend_release_is_idempotent_and_defers_active_storage():
    """Owned storage is cleared once and remains alive through active calls."""
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    start = header.index("static inline void prik_native_array_backend_release(")
    body = header[start : header.index("\n}\n", start)]
    release_now_start = header.index("static inline void prik_native_array_backend_release_now(")
    release_now = header[release_now_start : header.index("\n}\n", release_now_start)]

    assert "backend->release == NULL || backend->context == NULL" in body
    assert "backend->active_calls != 0" in body
    assert "backend->release_pending = 1u;" in body
    assert "prik_native_array_backend_release_now(backend);" in body
    assert "backend->context = NULL;" in release_now
    assert "backend->release(context);" in release_now
    assert "context_kind == PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR" in release_now
    assert "free(context);" in release_now
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


def test_a_fortran_owner_context_is_never_freed_as_c_storage():
    """Release frees C storage only; a Fortran owner belongs to its runtime.

    v1 called ``free()`` on every released context because an owned context was
    always ``malloc``'d descriptor storage. An owner is allocated by the Fortran
    runtime instead, so freeing it here as well would be undefined.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert "if (context_kind == PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR) {\n        free(context);" in header


def test_owning_storage_is_no_longer_the_same_fact_as_owning_a_descriptor():
    """The owned-descriptor accessor refuses a context that is not a descriptor.

    Its callers cast the result straight to ``CFI_cdesc_t *``, so a Fortran
    owner reaching it would be reinterpreted rather than diagnosed.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    start = header.index("prik_native_array_backend_owned_descriptor(")
    body = header[start : header.index("\n}", start)]

    assert "backend->context_kind != PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR" in body
    assert "owns a Fortran entity" in body


def test_a_fortran_owner_cannot_be_published_without_an_identity():
    """An owner is the one context a reader cannot check by inspection.

    Nothing about the address says which compiler laid out the bytes behind it
    or which entity it was generated for, so publishing one without both values
    would leave a foreign reader nothing to compare.
    """
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert "PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER && (owner_abi == 0 || owner_signature == 0)" in header
    assert "prik native array Fortran owner needs an owner ABI identity" in header
    # And the identity is meaningless on any other kind.
    assert (
        "context_kind != PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER && (owner_abi != 0 || owner_signature != 0)" in header
    )
    assert "#define PRIK_FORTRAN_OWNER_ABI UINT64_C(0)" in header


def test_context_kind_agrees_with_storage_ownership():
    """A backend cannot publish owned storage as borrowed, or the reverse."""
    header = SUPPORT_HEADER.read_text(encoding="utf-8")

    assert "context == NULL && context_kind != PRIK_NATIVE_ARRAY_CONTEXT_NONE" in header
    assert "prik native array backend cannot release borrowed context storage" in header
    assert "prik native array owned context needs a release entry point" in header


def test_owner_identity_is_compared_before_any_dereference():
    """Both halves of the identity gate the read, and each reports its own cause."""
    header = SUPPORT_HEADER.read_text(encoding="utf-8")
    start = header.index("prik_native_array_backend_for_owner(")
    body = header[start : header.index("\n}", start)]

    assert "backend->owner_abi != expected_owner_abi" in body
    assert "backend->owner_signature != expected_owner_signature" in body
    assert "different Fortran compiler ABI" in body
    assert "does not match the entity this argument declares" in body
