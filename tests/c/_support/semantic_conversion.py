"""C parser model to semantic IR conversion tests."""

from prik.semantics.models import SemanticOrigin


def _function(module, name):
    return next(function for function in module.functions if function.name == name)


def _assert_c_origin(
    origin: SemanticOrigin,
    *,
    native_name=None,
    native_scope=None,
    source_kind=None,
    source_type=None,
    source_location=None,
    metadata=None,
) -> None:
    """Assert the meaningful C identity and provenance carried by an origin."""
    assert origin.source_language == "c"
    assert origin.native_name == native_name
    assert origin.native_abi is None
    assert origin.native_symbol is None
    assert origin.native_scope == native_scope
    assert origin.source_kind == source_kind
    assert origin.source_type == source_type
    assert origin.source_location == (source_location or {})
    assert origin.metadata == (metadata or {})


def _blocker(code, message, item):
    return {"code": code, "message": message, "items": [item]}


def _assert_unsupported_type(semantic_type, *, code, message, owner, source_type):
    _ = (code, message, owner)
    assert semantic_type.name == "CUnsupported"
    assert semantic_type.dtype == "CUnsupported"
    assert semantic_type.metadata == {}
    _assert_c_origin(
        semantic_type.origin,
        source_kind="unsupported_type",
        source_type=source_type,
    )
