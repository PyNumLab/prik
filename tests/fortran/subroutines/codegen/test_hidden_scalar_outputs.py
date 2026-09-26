"""Hidden scalar output lowering through the public generator."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def test_required_explicit_interface_declares_hidden_result_in_native_order():
    module = parse_pyi_text(
        """
from prik.contracts import Addr, Annotated, Arg, Float64, Immutable, Int32, Return, bind, native_call, standalone

@bind("SCALE_OUT")
@standalone
@native_call([Addr(Arg(0)), Return("result", 0), Addr(Arg(1))])
def scale(
    x: Float64,
    mode: Annotated[Int32, Immutable] | None = ...,
) -> Float64: ...
""",
        module_name="hidden_result_explicit_interface",
    )
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    fortran_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    native_interface = fortran_source.split("subroutine SCALE_OUT(x, result, mode)", maxsplit=1)[1].split(
        "end subroutine SCALE_OUT", maxsplit=1
    )[0]
    assert "real(c_double) :: x" in native_interface
    assert "real(c_double) :: result" in native_interface
    assert "integer(c_int32_t), optional :: mode" in native_interface
    assert "call SCALE_OUT(x=x, result=result, mode=prik_optional_mode)" in fortran_source
    assert fortran_source.count("call SCALE_OUT(") == 1
