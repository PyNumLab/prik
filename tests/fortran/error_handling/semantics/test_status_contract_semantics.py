"""Semantic round-trip and policy validation for runtime status errors."""

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.semantics.models import RUNTIME_RELEASE_GIL_METADATA, RUNTIME_STATUS_ERROR_METADATA
from prik.policy.completion import complete_semantic_policies
from prik.printers import emit_module


_CONTRACT_IMPORTS = """from prik.contracts import (
    Float64, Int32, Returns, String, nogil, raises
)
"""


def _parse_pyi_text(source: str, *, module_name: str):
    return pyi_text_to_semantic_module(f"{_CONTRACT_IMPORTS}{source}", module_name=module_name)


def test_runtime_policy_decorators_round_trip_through_pyi():
    loaded = _parse_pyi_text(
        """
@raises(status="status", message="message", success=0)
def solve(
    x: Float64
) -> tuple[Float64, Returns["status", Int32], Returns["message", String]]: ...

@nogil
def concurrent(x: Float64) -> Float64: ...
""",
        module_name="runtime_policy",
    )

    func = loaded.functions[0]
    assert func.metadata[RUNTIME_STATUS_ERROR_METADATA] == {
        "status": "status",
        "message": "message",
        "success": 0,
    }
    assert loaded.functions[1].metadata[RUNTIME_RELEASE_GIL_METADATA] is True

    code = emit_module(loaded)
    assert '@raises(status="status", message="message", success=0)' in code
    assert "@nogil" in code
    assert emit_module(pyi_text_to_semantic_module(code, module_name="runtime_policy")) == code


def test_status_projection_accepts_an_optional_missing_message_target():
    loaded = _parse_pyi_text(
        '@raises(status="status", success=7)\ndef solve() -> Returns["status", Int32]: ...',
        module_name="status_only_policy",
    )

    complete_semantic_policies(loaded)

    assert loaded.functions[0].metadata[RUNTIME_STATUS_ERROR_METADATA] == {
        "status": "status",
        "success": 7,
    }
    code = emit_module(loaded)
    assert '@raises(status="status", success=7)' in code


@pytest.mark.parametrize(
    "source, message",
    [
        (
            '@raises(status="status")\ndef solve() -> Returns["status", Float64]: ...',
            "must be a scalar integer hidden output",
        ),
        (
            '@raises(status="status")\ndef solve(status: Int32) -> None: ...',
            "status target must name a hidden output",
        ),
        (
            '@raises(status="status", message="message")\n'
            'def solve() -> tuple[Returns["status", Int32], Returns["message", Int32]]: ...',
            "must be a scalar string hidden output",
        ),
    ],
)
def test_runtime_status_policy_rejects_invalid_output_contracts(source: str, message: str):
    loaded = _parse_pyi_text(source, module_name="invalid_runtime_policy")

    with pytest.raises(ValueError, match=message):
        complete_semantic_policies(loaded)
