"""Native-call runtime-envelope lowering tests."""

from __future__ import annotations

from pathlib import Path

from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import WrapperCodeGenerator, WrapperPlanner


RECURSION_CONTRACT = (
    Path("tests/fortran/error_handling/end_to_end/fixtures/runtime/contracts")
    / "fruntime_recursion_f90"
    / "fruntime_recursion_f90.pyi"
)


def _rendered_source(artifacts, suffix: str) -> str:
    return next(source.text for source in artifacts.sources if source.path.name.endswith(suffix))


def test_recursive_runtime_contract_keeps_the_gil_by_default():
    module = pyi_file_to_semantic_module(RECURSION_CONTRACT, module_name="fruntime_recursion_f90")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)

    assert plan.namespaces[0].functions
    assert all(function.binding.release_gil is False for function in plan.namespaces[0].functions)
    c_source = _rendered_source(WrapperCodeGenerator().generate(plan), ".c")
    assert "Py_BEGIN_ALLOW_THREADS" not in c_source
    assert "Py_END_ALLOW_THREADS" not in c_source
