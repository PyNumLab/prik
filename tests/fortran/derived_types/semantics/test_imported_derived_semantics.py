"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from dataclasses import asdict
from prik.parsers.fortran import parse_fortran_project
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranDerivedType,
    FortranFile,
    FortranModule,
    FortranProcedureSignature,
    FortranProject,
    FortranUseMapping,
    FortranVariable,
)
from prik.semantics.fortran2ir import (
    FortranToIRConverter,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    fortran_project_to_semantic_modules,
)
from prik.semantics.models import (
    SemanticField,
    SemanticVariable,
)
from tests.fortran._support.semantic_conversion import get_function
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_converter_preserves_imported_derived_contexts_through_dispatch_paths():
    converter = FortranToIRConverter()
    imported_type = FortranVariable(name="state", base_type="derived", kind="local_state")
    imported_argument = FortranArgument(name="arg", base_type="derived", kind="local_state")
    local_field = FortranArgument(name="nested", base_type="derived", kind="container_t")
    dtype = FortranDerivedType(
        name="container_t",
        module="consumer",
        fields=[FortranArgument(name="state", base_type="derived", kind="local_state"), local_field],
        methods=["step"],
    )
    dtype.visibility = "private"
    proc = FortranProcedureSignature(
        name="step",
        kind="subroutine",
        module="consumer",
        arguments=[imported_argument],
    )
    module = FortranModule(
        name="consumer",
        uses={
            "plain_mod": [],
            "types_mod": [FortranUseMapping(source="state_t", target="local_state")],
        },
        variables=[FortranVariable(name="module_state", base_type="derived", kind="local_state")],
        procedures=[proc],
        derived_types=[dtype],
        private_symbols=["container_t"],
    )
    parsed_file = FortranFile(modules=[module])
    project = FortranProject(files=[parsed_file])
    context = converter._module_derived_type_context(module)

    semantic_module = converter.visit(module)
    semantic_class = converter.visit(dtype, derived_type_context=context)
    external_ref = {
        "name": "state_t",
        "local_name": "local_state",
        "origin_module": "types_mod",
        "wrapped": False,
        "representation": "opaque",
    }

    assert converter.visit(imported_type, derived_type_context=context).metadata["external_type_ref"] == external_ref
    assert (
        converter.visit(imported_argument, derived_type_context=context).semantic_type.metadata["external_type_ref"]
        == external_ref
    )
    assert converter.visit(proc, derived_type_context=context).arguments[0].semantic_type.metadata[
        "external_type_ref"
    ] == (external_ref)
    assert (
        converter.visit(parsed_file)[0].classes[0].fields[0].semantic_type.metadata["external_type_ref"] == external_ref
    )
    assert converter.visit(project)[0].classes[0].fields[0].semantic_type.metadata["external_type_ref"] == external_ref
    assert semantic_module.classes[0].fields[0].semantic_type.metadata["external_type_ref"] == external_ref
    assert "external_type_ref" not in semantic_module.classes[0].fields[1].semantic_type.metadata
    assert semantic_class.fields[0].semantic_type.metadata["external_type_ref"] == external_ref
    assert isinstance(semantic_class.fields[0], SemanticField)
    assert semantic_class.visibility == "private"
    assert semantic_class.origin.source_language == "fortran"
    assert semantic_class.origin.native_name == "container_t"
    assert semantic_class.origin.native_scope == "consumer"
    assert semantic_class.origin.source_kind == "derived_type"
    semantic_proc = semantic_module.functions[0]
    assert semantic_proc.native_name == "step"
    assert semantic_proc.locals == []
    assert semantic_proc.arguments[0].semantic_type.metadata["external_type_ref"] == external_ref
    assert semantic_module.variables[0].semantic_type.metadata["external_type_ref"] == external_ref
    assert isinstance(semantic_module.variables[0], SemanticVariable)
    assert [method.name for method in semantic_module.classes[0].methods] == ["step"]
    assert semantic_module.classes[0].methods[0].projection == semantic_proc.projection
    assert semantic_module.classes[0].methods[0].origin == semantic_proc.origin
    assert semantic_proc.origin.source_language == "fortran"
    assert semantic_proc.origin.native_name == "step"
    assert semantic_proc.origin.native_scope == "consumer"
    assert semantic_proc.origin.source_kind == "subroutine"
    assert [asdict(mapping) for mapping in semantic_proc.projection] == [
        {
            "python_name": "arg",
            "native_name": "arg",
            "native_position": 0,
            "python_position": 0,
            "result_position": None,
            "value_kind": "",
            "value": None,
        }
    ]
    assert semantic_module.origin.source_language == "fortran"
    assert semantic_module.origin.native_name == "consumer"
    assert semantic_module.origin.native_scope == "consumer"
    assert semantic_module.origin.source_kind == "module"
    assert converter.visit(FortranDerivedType(name="default_t")).visibility == "public"
    assert converter.visit(FortranVariable(name="local", base_type="derived", kind="state_t")).name == "state_t"


def test_imported_derived_type_is_an_opaque_external_reference_by_default():
    parsed = parse_fortran_source(
        """
module physics
  use types_mod, only: particle
contains
  subroutine move(p)
    type(particle), intent(inout) :: p
  end subroutine move
end module physics
"""
    )

    module = fortran_module_to_semantic_module(parsed)
    particle = get_function(module, "move").arguments[0].semantic_type

    assert module.classes == []
    assert particle.storage.kind == "reference"
    assert particle.metadata["external_type_ref"] == {
        "name": "particle",
        "local_name": "particle",
        "origin_module": "types_mod",
        "wrapped": False,
        "representation": "opaque",
    }
    wrapped_modules = fortran_file_to_semantic_modules(
        parsed,
        wrapped_derived_types={("types_mod", "particle")},
    )
    wrapped_particle = get_function(wrapped_modules[0], "move").arguments[0].semantic_type
    assert wrapped_particle.metadata["external_type_ref"]["wrapped"] is True
    assert wrapped_particle.metadata["external_type_ref"]["representation"] == "wrapped"
    wrapped_module = fortran_module_to_semantic_module(
        parsed,
        wrapped_derived_types={("types_mod", "particle")},
    )
    assert (
        get_function(wrapped_module, "move").arguments[0].semantic_type.metadata["external_type_ref"]["wrapped"] is True
    )


def test_explicit_project_target_resolves_imported_derived_type_without_reexport():
    project = parse_fortran_project(
        {
            "types_mod.f90": """
module types_mod
  type :: particle
    real :: mass
  end type particle
end module types_mod
""",
            "physics.f90": """
module physics
  use types_mod, only: particle
contains
  subroutine move(p)
    type(particle), intent(inout) :: p
  end subroutine move
end module physics
""",
        }
    )

    modules = {module.name: module for module in fortran_project_to_semantic_modules(project)}
    particle = get_function(modules["physics"], "move").arguments[0].semantic_type

    assert [cls.name for cls in modules["types_mod"].classes] == ["particle"]
    assert modules["physics"].classes == []
    assert sum(cls.name == "particle" for module in modules.values() for cls in module.classes) == 1
    assert particle.metadata["external_type_ref"] == {
        "name": "particle",
        "local_name": "particle",
        "origin_module": "types_mod",
        "wrapped": True,
        "representation": "wrapped",
    }
