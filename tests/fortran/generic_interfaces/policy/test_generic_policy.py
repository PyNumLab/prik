from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from x2py.parsers.fortran.parser import parse_fortran_project
from x2py.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from x2py.pipeline.preprocessing import PreprocessingConfig
from x2py.semantics.fortran2ir import fortran_project_to_semantic_modules
from x2py.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from x2py.semantics.policy_completion import complete_semantic_policies

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/baseline/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
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
