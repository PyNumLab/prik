"""Fortran source export selection owns one qualified callable surface."""

from pathlib import Path

import pytest

from prik.cli import _read_export_symbols
from prik.semantics.models import NATIVE_ACCESS_MODULE_METADATA
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


def test_facade_selection_retains_only_requested_native_owners_and_access_route():
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
    candidate = owner_selected.overload_sets[0].procedures[0]
    assert candidate.native_name == "run"
    assert candidate.metadata[NATIVE_ACCESS_MODULE_METADATA] == "facade"


def test_external_root_cannot_satisfy_a_module_qualified_identity():
    external = _module("foo", functions=[_function("foo", "external")])
    external.origin.source_kind = "external_root"

    with pytest.raises(ValueError, match="unknown modules: foo"):
        select_fortran_export_symbols([external], ["foo::external"])
