"""Typed direct primitive-scalar result lowering through the public generator."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import DirectResultABI
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def test_direct_bool_result_normalizes_the_fortran_truth_bit_before_c_conversion():
    module = parse_pyi_text(
        "def not_flag(value: Bool) -> Bool: ...",
        module_name="logical_result",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    result = plan.namespaces[0].functions[0].results[0]

    assert result.entrypoint.direct_result_abi is DirectResultABI.LOGICAL_LOW_BIT_INT8

    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    fortran_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "int8_t bind_c_not_flag(bool value);" in c_source
    assert "result = (bool)bind_c_not_flag(bound_value);" in c_source
    assert "integer(c_int8_t) :: result" in fortran_source
    assert "logical(c_bool) :: c_result" in fortran_source
    assert "c_result = native_not_flag(value)" in fortran_source
    # Reduced the way C converts to `_Bool`: any non-zero value is true.
    assert "result = merge(1_c_int8_t, 0_c_int8_t, transfer(c_result, 0_c_int8_t) /= 0_c_int8_t)" in fortran_source
