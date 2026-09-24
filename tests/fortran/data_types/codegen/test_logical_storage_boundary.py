"""Native-width logical storage stays interoperable at the generated bind(C) boundary."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies


def test_wider_logical_crosses_bind_c_as_an_address_or_same_width_integer():
    """The logical kind exists only behind the boundary, for reference and value transport alike."""
    module = parse_pyi_text(
        """from prik.contracts import Bool32, Int32, Returns

def flip(flag: Bool32) -> Returns["flag", Bool32]: ...

def count_true(flag: Bool32) -> Int32: ...
""",
        module_name="logical_boundary",
    )
    complete_semantic_policies(module)

    bridge = next(
        source.text
        for source in WrapperGenerator().generate(WrapperPlanner().build(module)).sources
        if source.path.suffix == ".f90"
    )

    assert "type(c_ptr), value :: bound_flag" in bridge
    assert "call c_f_pointer(bound_flag, flag)" in bridge
    assert "integer(c_int32_t), value :: bound_flag" in bridge
    assert "flag = transfer(bound_flag, flag)" in bridge
    assert "logical(kind=4), pointer :: flag" in bridge
