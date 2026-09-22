"""Fortran source export selection owns one qualified callable surface."""

from pathlib import Path

import pytest

from prik.cli import _read_export_symbols
from prik.semantics.fortran_exports import select_fortran_export_functions
from prik.semantics.models import (
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

    result = select_fortran_export_functions([callbacks, selected], ["SOLVER_MOD::SOLVE"])

    assert [module.name for module in result.primary_modules] == ["solver_mod"]
    assert [function.name for function in result.primary_modules[0].functions] == ["solve"]
    assert result.primary_modules[0].exported_names == ["solve"]
    assert [module.name for module in result.context_modules] == ["callbacks_mod"]
    assert result.context_modules[0].exported_names is None


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
        ([], "requires at least one module procedure identity"),
        (["solve"], "invalid procedure identities: solve"),
        (["solver_mod::solve", "SOLVER_MOD::SOLVE"], "repeated identities"),
        (["missing_mod::solve"], "unknown modules: missing_mod"),
        (["solver_mod::missing"], "unknown procedures: solver_mod::missing"),
        (["solver_mod::state"], "non-function declarations: solver_mod::state"),
    ],
)
def test_selection_rejects_invalid_or_unresolved_identities(symbols, message):
    module = _module(
        "solver_mod",
        functions=[_function("solver_mod", "solve")],
        variables=[SemanticVariable(name="state", semantic_type=SemanticType(name="Int32"))],
    )

    with pytest.raises(ValueError, match=message):
        select_fortran_export_functions([module], symbols)


def test_selection_rejects_private_module_procedure():
    hidden = _function("solver_mod", "hidden")
    hidden.visibility = "private"
    with pytest.raises(ValueError, match="private procedures: solver_mod::hidden"):
        select_fortran_export_functions([_module("solver_mod", functions=[hidden])], ["solver_mod::hidden"])
