"""Pointer lowering details that the gfortran end-to-end suite cannot distinguish."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def test_nullable_scalar_pointer_result_uses_attribute_independent_storage_sizing():
    """Sizing uses ``storage_size``, which does not depend on the pointer attribute."""
    module = parse_pyi_text(
        """
from prik.contracts import Addr, Aliased, Annotated, Arg, Destruction, Float64, Ownership, Pointer, Return, Transfer, native_call

@native_call([Addr(Arg(0))], result=Pointer(Return(0)))
def select_scalar(
    value: Annotated[Float64, Aliased],
) -> Annotated[Float64, Ownership("python"), Transfer("snapshot_copy"), Destruction("python_refcount")] | None: ...
""",
        module_name="pointer_scalar_lowering",
    )
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "storage_size(result_value, kind=c_size_t) / 8_c_size_t" in bridge_source
    assert "c_sizeof(result_value)" not in bridge_source
