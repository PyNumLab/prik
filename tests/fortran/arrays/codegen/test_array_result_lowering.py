"""Direct and hidden ordinary array result ownership and plan validation."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _result_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, Int32, Return, native_call

def direct(n: Int32) -> Float64[n]: ...

@native_call([Return("out", 0)])
def hidden() -> Float64[3]: ...
""",
        module_name="ordinary_array_results",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_array_result_lowering_transfers_bridge_copy_to_capsule_owned_numpy_storage():
    """The bridge's copy becomes the array's storage, released once by its capsule.

    `PyArray_SetBaseObject` steals the capsule even when it fails, so that
    failure path must neither release the capsule nor free the storage again.
    A double release there is not observable from a successful call.
    """
    artifacts = WrapperGenerator().generate(_result_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert "PyCapsule_New(result, NULL, prik_release_owned_memory)" in c_source
    assert "PyCapsule_New(out, NULL, prik_release_owned_memory)" in c_source
    assert "memcpy(PyArray_DATA((PyArrayObject *)result_obj), result" not in c_source
    base_failure = c_source.split(
        "if (PyArray_SetBaseObject((PyArrayObject *)result_obj, result_obj_base) < 0)",
        maxsplit=1,
    )[1].split("}", maxsplit=1)[0]
    assert "Py_DECREF(result_obj_base)" not in base_failure
    assert "free(result)" not in base_failure


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("rank", "invalid-array-result-rank"),
        ("order", "invalid-array-result-order"),
        ("copy", "invalid-array-result-copy-reason"),
        ("slot", "inconsistent-result-array-handoff"),
    ],
)
def test_array_result_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _result_plan()
    direct = plan.namespaces[0].functions[0].results[0]
    hidden = plan.namespaces[0].functions[1].results[0]
    if edit == "rank":
        direct.array.rank = None
    elif edit == "order":
        direct.array.order = "ORDER_C"
        direct.array.rank = 2
        direct.array.shape = ("2", "2")
        direct.array.extent_roles = ("edited:extent:0", "edited:extent:1")
        direct.array.extent_reference_roles = ((), ())
    elif edit == "copy":
        direct.bridge.copy_reason = "edited"
    else:
        hidden.projected_call_slot.array = direct.array

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)
