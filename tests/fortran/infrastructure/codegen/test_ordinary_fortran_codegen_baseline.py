"""Exact generated-output baseline for an ordinary Fortran procedure."""

from __future__ import annotations

from hashlib import sha256

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies


def test_ordinary_fortran_wrapper_preserves_exact_generated_bytes():
    module = parse_pyi_text(
        "def scale(value: Float64) -> Float64: ...\n",
        module_name="ordinary_entrypoint_baseline",
    )
    complete_semantic_policies(module)

    generated = WrapperGenerator().generate(WrapperPlanner().build(module))

    expected = {
        "bind_c_ordinary_entrypoint_baseline_wrapper.f90": (
            740,
            "cdda3f054ab348a128cfc31bb338fe0ec12277d41c607b209c8b401cc2a29004",
        ),
        "ordinary_entrypoint_baseline_wrapper.c": (
            1860,
            "0401eb6eae8b2b3682a6f04986b8da1553fe77cf070fe4b981e642c7ed13c6d2",
        ),
        "ordinary_entrypoint_baseline_wrapper.h": (
            248,
            "6b29d016c71f463b5395d8875c1e1f04b98a625241baaf8f85685eee4fe2ce63",
        ),
    }
    actual = {
        source.path.name: (len(payload), sha256(payload).hexdigest())
        for source in generated.sources
        for payload in (source.text.encode("utf-8"),)
    }

    assert actual == expected
