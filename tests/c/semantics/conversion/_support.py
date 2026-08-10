"""C parser model to semantic IR conversion tests."""

from dataclasses import asdict


def _function(module, name):
    return next(function for function in module.functions if function.name == name)


def _c_origin(
    *,
    native_name=None,
    native_scope=None,
    source_kind=None,
    source_type=None,
    source_location=None,
    metadata=None,
):
    return {
        "source_language": "c",
        "native_name": native_name,
        "native_scope": native_scope,
        "source_kind": source_kind,
        "source_type": source_type,
        "source_location": source_location or {},
        "metadata": metadata or {},
    }


def _blocker(code, message, item):
    return {"code": code, "message": message, "items": [item]}


def _assert_unsupported_type(semantic_type, *, code, message, owner, source_type):
    _ = (code, message, owner)
    assert semantic_type.name == "CUnsupported"
    assert semantic_type.dtype == "CUnsupported"
    assert semantic_type.metadata == {}
    assert asdict(semantic_type.origin) == _c_origin(
        source_kind="unsupported_type",
        source_type=source_type,
    )
