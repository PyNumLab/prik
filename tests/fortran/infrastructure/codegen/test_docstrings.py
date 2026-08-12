"""Internal generated-docstring contracts."""

from pathlib import Path
import subprocess
import sys

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies


def _function_plan():
    """Return an editable scalar plan before documentation generation."""
    module = parse_pyi_text("def scale(value: Float64) -> Float64: ...", module_name="docstrings")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_codegen_renders_unresolved_plan_docstrings_before_freezing():
    plan = _function_plan()
    namespace = plan.namespaces[0]
    function = namespace.functions[0]

    assert namespace.docstring is None
    assert function.binding.docstring is None

    WrapperGenerator().generate(plan)

    assert namespace.docstring is not None
    assert namespace.docstring.startswith("docstrings")
    assert function.binding.docstring is not None
    assert function.binding.docstring.startswith("scale(value) -> float64")


def test_codegen_preserves_explicit_plan_docstring_overrides():
    plan = _function_plan()
    namespace = plan.namespaces[0]
    function = namespace.functions[0]
    namespace.docstring = ""
    function.binding.docstring = "Custom scale documentation."

    WrapperGenerator().generate(plan)

    assert namespace.docstring == ""
    assert function.binding.docstring == "Custom scale documentation."


def test_docstrings_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [sys.executable, str(repository_root / "prik/codegen/docstrings.py")],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "double_value" in result.stdout
