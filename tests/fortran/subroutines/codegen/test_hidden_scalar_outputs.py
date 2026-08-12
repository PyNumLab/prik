"""Hidden scalar output lowering through the public generator."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def test_hidden_scalar_result_is_one_bridge_output_and_one_python_result():
    module = parse_pyi_text(
        """
@bind("SCALE_OUT")
@standalone
@native_call([Addr(Arg(0)), Return("result", 0)])
def scale(x: Float64) -> Float64: ...
""",
        module_name="hidden_result",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    result = function.results[0]

    assert result.native_call_slot is function.native_call_slots[result.bridge.abi_position]

    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    fortran_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void bind_c_scale(double * x, double * result);" in c_source
    assert "bind_c_scale(&bound_x, &result);" in c_source
    assert "PyObject * result_obj = prik_float64_to_python(&result);" in c_source
    assert 'subroutine bind_c_scale(x, result) bind(c, name="bind_c_scale")' in fortran_source
    assert "external :: SCALE_OUT" in fortran_source
    assert "subroutine SCALE_OUT(" not in fortran_source
    assert "call SCALE_OUT(x, result)" in fortran_source


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
    assert "call SCALE_OUT(x=x, result=result, mode=mode)" in fortran_source
    assert "call SCALE_OUT(x=x, result=result)" in fortran_source
