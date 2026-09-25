"""Fortran source export selection owns one qualified callable surface."""

from pathlib import Path

import pytest

from prik.cli import _read_export_symbols
from prik.parsers.fortran import parse_fortran_file, parse_fortran_project
from prik.semantics.fortran2ir import fortran_module_to_semantic_module, fortran_project_to_semantic_modules
from prik.semantics.fortran_exports import select_fortran_export_symbols
from prik.semantics.models import (
    ProcedureOverloadSet,
    SemanticFunction,
    SemanticModule,
    SemanticOrigin,
    SemanticPrototype,
    SemanticReexport,
    SemanticType,
    SemanticVariable,
)


def _module(name: str, *, functions=(), prototypes=(), variables=(), reexports=()):
    return SemanticModule(
        name=name,
        functions=list(functions),
        prototypes=list(prototypes),
        variables=list(variables),
        reexports=list(reexports),
        origin=SemanticOrigin(source_language="fortran", native_name=name, source_kind="module"),
    )


def _function(module: str, name: str):
    return SemanticFunction(
        name=name,
        native_name=name,
        origin=SemanticOrigin(source_language="fortran", native_name=name, native_scope=module),
    )


def test_selection_keeps_one_callable_root_and_its_declaration_module():
    callback = SemanticPrototype(
        name="REPORT",
        origin=SemanticOrigin(source_language="fortran", native_name="report", native_scope="callbacks_mod"),
    )
    callbacks = _module("callbacks_mod", prototypes=[callback])
    selected = _module(
        "solver_mod",
        functions=[_function("solver_mod", "solve"), _function("solver_mod", "helper")],
        variables=[SemanticVariable(name="state", semantic_type=SemanticType(name="Int32"))],
        reexports=[
            SemanticReexport(
                local_name="REPORT",
                origin_module="callbacks_mod",
                source_name="REPORT",
                declaration_dependency=True,
            )
        ],
    )

    result = select_fortran_export_symbols([callbacks, selected], ["SOLVER_MOD::SOLVE"])

    assert [module.name for module in result.primary_modules] == ["solver_mod"]
    assert [function.name for function in result.primary_modules[0].functions] == ["solve"]
    assert result.primary_modules[0].exported_names == ["solve"]
    assert [module.name for module in result.context_modules] == ["callbacks_mod"]
    assert result.context_modules[0].exported_names is None


def test_selection_publishes_a_variable_with_its_concrete_type():
    """A selected module object keeps its parsed type and native owner."""
    selected = _module(
        "state_mod",
        variables=[
            SemanticVariable(
                name="sentinel",
                semantic_type=SemanticType(name="Int32"),
                origin=SemanticOrigin(source_language="fortran", native_name="sentinel", native_scope="state_mod"),
            ),
            SemanticVariable(name="other", semantic_type=SemanticType(name="Int32")),
        ],
    )

    result = select_fortran_export_symbols([selected], ["STATE_MOD::SENTINEL"])

    assert [variable.name for variable in result.primary_modules[0].variables] == ["sentinel"]
    assert result.primary_modules[0].variables[0].semantic_type.name == "Int32"
    assert result.primary_modules[0].variables[0].origin.native_scope == "state_mod"
    assert result.primary_modules[0].exported_names == ["sentinel"]


def test_fortran_export_file_accepts_comments_and_rejects_case_insensitive_duplicates(tmp_path: Path):
    export_file = tmp_path / "exports.txt"
    export_file.write_text("# reviewed\nsolver_mod::solve  # public\n", encoding="utf-8")
    assert _read_export_symbols(export_file, language="fortran") == ("solver_mod::solve",)

    export_file.write_text("solver_mod::solve\nSOLVER_MOD::SOLVE\n", encoding="utf-8")
    with pytest.raises(ValueError, match="first appeared on line 1"):
        _read_export_symbols(export_file, language="fortran")


@pytest.mark.parametrize(
    ("symbols", "message"),
    [
        ([], "requires at least one module symbol identity"),
        (["solve"], "invalid symbol identities: solve"),
        (["solver_mod::solve", "SOLVER_MOD::SOLVE"], "repeated identities"),
        (["missing_mod::solve"], "unknown modules: missing_mod"),
        (["solver_mod::missing"], "unknown symbols: solver_mod::missing"),
    ],
)
def test_selection_rejects_invalid_or_unresolved_identities(symbols, message):
    module = _module(
        "solver_mod",
        functions=[_function("solver_mod", "solve")],
        variables=[SemanticVariable(name="state", semantic_type=SemanticType(name="Int32"))],
    )

    with pytest.raises(ValueError, match=message):
        select_fortran_export_symbols([module], symbols)


def test_selection_rejects_private_module_procedure():
    hidden = _function("solver_mod", "hidden")
    hidden.visibility = "private"
    with pytest.raises(ValueError, match="private symbols: solver_mod::hidden"):
        select_fortran_export_symbols([_module("solver_mod", functions=[hidden])], ["solver_mod::hidden"])


def test_selection_keeps_one_generic_with_its_specific_candidates():
    specific_int = _function("solver_mod", "solve_int")
    specific_real = _function("solver_mod", "solve_real")
    generic = ProcedureOverloadSet(name="solve", procedures=[specific_int, specific_real], native_scope="solver_mod")
    module = _module(
        "solver_mod",
        functions=[specific_int, specific_real, _function("solver_mod", "helper")],
    )
    module.overload_sets = [generic]

    selected = select_fortran_export_symbols([module], ["SOLVER_MOD::SOLVE"]).primary_modules[0]

    assert [function.name for function in selected.functions] == ["solve_int", "solve_real"]
    assert [overload.name for overload in selected.overload_sets] == ["solve"]
    assert [candidate.name for candidate in selected.overload_sets[0].procedures] == ["solve_int", "solve_real"]
    assert selected.exported_names == ["solve"]


def test_facade_selection_retains_only_requested_native_owners():
    """A facade allowlist selects owner declarations without publishing siblings."""
    specific = _function("owner", "run_impl")
    owner = _module(
        "owner",
        functions=[specific, _function("owner", "unrelated")],
        variables=[
            SemanticVariable(name="marker", semantic_type=SemanticType(name="Int32")),
            SemanticVariable(name="unrelated_state", semantic_type=SemanticType(name="Int32")),
        ],
    )
    owner.overload_sets = [ProcedureOverloadSet(name="run", procedures=[specific], native_scope="owner")]
    facade = _module(
        "facade",
        reexports=[
            SemanticReexport("run", "owner", "run", "facade", entity_kind="generic"),
            SemanticReexport("marker", "owner", "marker", "facade", entity_kind="variable"),
            SemanticReexport("unrelated", "owner", "unrelated", "facade", entity_kind="procedure"),
        ],
    )

    selected = select_fortran_export_symbols([owner, facade], ["facade::run", "facade::marker"])

    owner_selected, facade_selected = selected.primary_modules
    assert [function.name for function in owner_selected.functions] == ["run_impl"]
    assert [variable.name for variable in owner_selected.variables] == ["marker"]
    assert [item.local_name for item in facade_selected.reexports] == ["run", "marker"]
    assert owner_selected.overload_sets[0].procedures[0].native_name == "run_impl"


def test_external_root_cannot_satisfy_a_module_qualified_identity():
    external = _module("foo", functions=[_function("foo", "external")])
    external.origin.source_kind = "external_root"

    with pytest.raises(ValueError, match="unknown modules: foo"):
        select_fortran_export_symbols([external], ["foo::external"])


def test_selection_retains_component_and_parent_types_of_a_selected_signature():
    """A selected type brings the types its components and parent declare, and no others."""
    module = fortran_module_to_semantic_module(
        parse_fortran_file(
            """
module shapes
  implicit none
  type :: base_t
    integer :: b = 1
  end type base_t
  type :: inner_t
    integer :: a = 2
  end type inner_t
  type, extends(base_t) :: outer_t
    type(inner_t) :: inner
  end type outer_t
  type :: unrelated_t
    integer :: u = 0
  end type unrelated_t
contains
  subroutine use_outer(x)
    type(outer_t), intent(in) :: x
  end subroutine use_outer
end module shapes
"""
        ).modules[0]
    )

    selected = select_fortran_export_symbols([module], ["shapes::use_outer"]).primary_modules[0]

    assert sorted(cls.name for cls in selected.classes) == ["base_t", "inner_t", "outer_t"]
    assert set(selected.exported_names) == {"use_outer", "base_t", "inner_t", "outer_t"}


def test_selection_through_a_two_level_facade_reaches_each_declaring_module():
    """A generic, a procedure, and a variable re-exported twice resolve to where they are declared."""
    project = parse_fortran_project(
        {
            "base.f90": (
                "module base\n  integer, parameter :: sentinel = 42\n  interface area\n"
                "    module procedure area_real\n  end interface area\ncontains\n"
                "  real function area_real(x)\n    real, intent(in) :: x\n    area_real = x\n"
                "  end function area_real\n  subroutine unrelated()\n  end subroutine unrelated\nend module base\n"
            ),
            "middle.f90": "module middle\n  use base\nend module middle\n",
            "tools.f90": "module tools\ncontains\n  subroutine touch()\n  end subroutine touch\nend module tools\n",
            "facade.f90": "module facade\n  use middle\n  use tools\nend module facade\n",
        }
    )
    modules = fortran_project_to_semantic_modules(project)

    selected = select_fortran_export_symbols(modules, ["facade::area", "facade::sentinel", "facade::touch"])

    owners = {module.name: module for module in selected.primary_modules}
    assert [overload.name for overload in owners["base"].overload_sets] == ["area"]
    assert [variable.name for variable in owners["base"].variables] == ["sentinel"]
    assert "unrelated" not in {function.name for function in owners["base"].functions}
    assert [function.name for function in owners["tools"].functions] == ["touch"]
    assert sorted(owners["facade"].exported_names) == ["area", "sentinel", "touch"]
    assert "middle" not in owners


def test_a_generic_sharing_a_specific_name_is_one_selectable_name():
    """Fortran lets a generic share a specific's name; the name then selects the generic."""
    module = fortran_module_to_semantic_module(
        parse_fortran_file(
            """
module shapes
  interface area
    module procedure area, area_int
  end interface area
contains
  real function area(x)
    real, intent(in) :: x
    area = x
  end function area
  integer function area_int(i)
    integer, intent(in) :: i
    area_int = i
  end function area_int
end module shapes
"""
        ).modules[0]
    )

    selected = select_fortran_export_symbols([module], ["shapes::area"]).primary_modules[0]

    assert [overload.name for overload in selected.overload_sets] == ["area"]
    assert sorted(function.name for function in selected.functions) == ["area", "area_int"]
    assert selected.exported_names == ["area"]


def test_selection_drops_imports_only_unselected_declarations_used(tmp_path: Path):
    """A name only a removed declaration was written with is not imported by the contract.

    Every type ``consts`` re-exports stays declared where it is; the selected
    constant names one of them, so that is the one the contract binds, under
    its class name.
    """
    from prik.pipeline.pyi import emit_module_stubs

    source = tmp_path / "handles.f90"
    source.write_text(
        """module handles
  implicit none
  type, bind(c) :: Handle_A
    integer :: val
  end type
  type, bind(c) :: Handle_B
    integer :: val
  end type
end module handles

module consts
  use handles
  implicit none
  type(Handle_A), parameter :: A_NULL = Handle_A(0)
  type(Handle_B), parameter :: B_NULL = Handle_B(0)
end module consts
""",
        encoding="utf-8",
    )
    modules = fortran_project_to_semantic_modules(parse_fortran_project(tmp_path))
    selection = select_fortran_export_symbols(modules, ["consts::A_NULL"])

    contract = emit_module_stubs(
        list(selection.primary_modules),
        available_modules=list(selection.available_modules),
        normalize_public_names=True,
    )["consts"]

    assert [line for line in contract.splitlines() if line.startswith("from .")] == ["from .handles import Handle_A"]
