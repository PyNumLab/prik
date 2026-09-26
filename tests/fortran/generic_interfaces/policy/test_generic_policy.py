from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig, read_fortran_source
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from prik.policy.completion import complete_semantic_policies

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): read_fortran_source(source, PreprocessingConfig()).source})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_module_overload_bind_takes_precedence_per_candidate():
    module = parse_pyi_text(
        """
def convert_integer(value: Int32) -> Int32: ...

@private
@bind("convert_real_specific")
def convert_real(value: Float64) -> Float64: ...

@overload("convert_integer")
def convert(value: Int32) -> Int32: ...

@bind("convert")
@overload("convert_real")
def convert(value: Float64) -> Float64: ...
""",
        module_name="conversions",
    )

    complete_semantic_policies(module)

    policies = [
        procedure.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
        for procedure in module.overload_sets[0].procedures
    ]
    assert [policy.native_name for policy in policies] == ["convert_integer", "convert"]


def test_a_generic_owns_its_export_decision_like_every_declaration():
    """The decision lives on the generic, not on whichever specific came first.

    Keeping it on the first candidate made a generic without candidates unable
    to record one at all, and left the generic's own metadata empty.
    """
    from prik.policy.exports import complete_python_export_policy
    from prik.semantics.models import PYTHON_EXPORTS_METADATA, ProcedureOverloadSet, SemanticModule

    module = parse_pyi_text(
        """
from prik.contracts import Addr, Arg, Int32, native_call, overload

@native_call([Addr(Arg(0))])
def convert_i(x: Int32) -> Int32: ...

@overload("convert_i")
def convert(x: Int32) -> Int32: ...
""",
        module_name="owned_generic",
    )
    complete_python_export_policy(module)
    generic = module.overload_sets[0]

    assert generic.metadata[PYTHON_EXPORTS_METADATA] == [{"namespace": (), "name": "convert"}]
    assert module.functions[0].metadata[PYTHON_EXPORTS_METADATA] == [{"namespace": (), "name": "convert_i"}]

    empty = SemanticModule(name="placeholder", overload_sets=[ProcedureOverloadSet(name="later", procedures=[])])
    complete_python_export_policy(empty)
    assert empty.overload_sets[0].metadata[PYTHON_EXPORTS_METADATA] == [{"namespace": (), "name": "later"}]
