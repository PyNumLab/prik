"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.parsers.fortran import parse_fortran_project
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranDerivedType,
    FortranFile,
    FortranModule,
    FortranProcedureSignature,
    FortranProject,
    FortranUseMapping,
    FortranUseStatement,
)
from prik.semantics.fortran2ir import (
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    fortran_project_to_semantic_modules,
)
from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
)
from tests.fortran._support.semantic_conversion import get_function
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_abstract_type_identity_is_module_qualified_and_available_project_wide():
    abstract_type = FortranDerivedType(
        name="item_t",
        module="abstract_owner",
        attributes=["abstract"],
    )
    abstract_owner = FortranModule(
        name="abstract_owner",
        derived_types=[abstract_type],
    )
    imported_argument = FortranArgument(
        name="value",
        base_type="derived",
        kind="item_t",
        procedure="consume",
    )
    consumer = FortranModule(
        name="consumer",
        uses=[FortranUseStatement("abstract_owner", True, (FortranUseMapping(source="item_t"),))],
        procedures=[
            FortranProcedureSignature(
                name="consume",
                kind="subroutine",
                module="consumer",
                arguments=[imported_argument],
            )
        ],
    )
    concrete_type = FortranDerivedType(name="item_t", module="concrete_owner")
    concrete_argument = FortranArgument(
        name="value",
        base_type="derived",
        kind="item_t",
        procedure="consume",
    )
    concrete_owner = FortranModule(
        name="concrete_owner",
        derived_types=[concrete_type],
        procedures=[
            FortranProcedureSignature(
                name="consume",
                kind="subroutine",
                module="concrete_owner",
                arguments=[concrete_argument],
            )
        ],
    )
    project = FortranProject(
        files=[
            FortranFile(modules=[consumer]),
            FortranFile(modules=[concrete_owner]),
            FortranFile(modules=[abstract_owner]),
        ],
        modules={
            "consumer": consumer,
            "concrete_owner": concrete_owner,
            "abstract_owner": abstract_owner,
        },
        derived_types={
            "concrete_owner.item_t": concrete_type,
            "abstract_owner.item_t": abstract_type,
        },
    )

    modules = {module.name: module for module in fortran_project_to_semantic_modules(project)}

    imported = modules["consumer"].functions[0].arguments[0].semantic_type
    concrete = modules["concrete_owner"].functions[0].arguments[0].semantic_type
    assert imported.metadata["fortran_abstract_type"] is True
    assert "fortran_abstract_type" not in concrete.metadata


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
        get_function(wrapped_module, "move").arguments[0].semantic_type.metadata[EXTERNAL_TYPE_REF_METADATA]["wrapped"]
        is True
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


def test_type_reached_through_a_reexporting_module_resolves_to_its_declaration():
    """A module that only re-exports a type still leads to the module declaring it."""
    project = parse_fortran_project(
        {
            "base.f90": "module base\n  type :: handle_t\n    integer :: val\n  end type handle_t\nend module base\n",
            "middle.f90": "module middle\n  use base\nend module middle\n",
            "api.f90": (
                "module api\n  use middle\ncontains\n  subroutine touch(h)\n"
                "    type(handle_t), intent(inout) :: h\n  end subroutine touch\nend module api\n"
            ),
        }
    )

    api = next(module for module in fortran_project_to_semantic_modules(project) if module.name == "api")
    reference = api.functions[0].arguments[0].semantic_type.metadata[EXTERNAL_TYPE_REF_METADATA]

    assert (reference["origin_module"], reference["name"]) == ("base", "handle_t")
