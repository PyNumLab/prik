"""Scalar storage and raw-address boundaries stay distinct plans."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import NativeBarrierAction, PythonBarrierAction
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import BridgeDataAction
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def test_checked_scalar_storage_and_raw_address_complete_distinct_plans_and_guards():
    """Checked storage validates the NumPy object; a raw address trusts the integer.

    The end-to-end suites prove dtype, rank and writeability checks; byte order
    and alignment guards are only visible in the generated binding.
    """
    module = parse_pyi_text(
        """
def storage(x: Float64[()]) -> None: ...
def raw(x: Addr(Float64)) -> None: ...
""",
        module_name="scalar_boundaries",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    storage = functions["storage"].arguments[0]
    raw = functions["raw"].arguments[0]

    assert (storage.binding.python_action, storage.bridge.native_action) == (
        PythonBarrierAction.SCALAR_STORAGE,
        NativeBarrierAction.PASS_STORAGE_ADDRESS,
    )
    assert (raw.binding.python_action, raw.bridge.native_action) == (
        PythonBarrierAction.RAW_ADDRESS,
        NativeBarrierAction.PASS_RAW_ADDRESS,
    )
    assert storage.bridge.data_action is raw.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW

    c_source = next(source.text for source in WrapperGenerator().generate(plan).sources if source.path.suffix == ".c")
    assert "PyArray_ISNOTSWAPPED((PyArrayObject *)bound_x_obj)" in c_source
    assert "PyArray_ISALIGNED((PyArrayObject *)bound_x_obj)" in c_source
    assert "bound_x = PyLong_AsVoidPtr(bound_x_obj);" in c_source
