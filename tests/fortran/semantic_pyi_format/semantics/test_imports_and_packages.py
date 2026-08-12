"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from pathlib import Path
from prik import parse_fortran_file
from prik.printers import emit_module
from prik.pipeline.pyi import (
    pyi_file_to_semantic_module,
    pyi_paths_to_semantic_modules,
    pyi_text_to_semantic_module,
)
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.semantics.models import (
    SemanticImport,
    SemanticImportItem,
)
from prik.semantics.native_contract import native_contract_issues
from tests.fortran._support.pyi_conversion import (
    CONTRACT_IMPORT,
    parse_pyi_text,
)
import prik.pipeline.pyi as pyi_pipeline


def test_convert_pyi_to_ir_requires_imported_contract_types():
    with pytest.raises(ValueError, match="Contract type 'Float64' must be imported"):
        pyi_text_to_semantic_module("value: Float64\n", module_name="bare")

    module = pyi_text_to_semantic_module(
        """
class Float64:
    pass

value: Float64
""",
        module_name="user_type",
    )

    assert module.classes[0].name == "Float64"
    assert module.variables[0].semantic_type.name == "Float64"


def test_convert_pyi_to_ir_accepts_import_aliases():
    module = parse_pyi_text(
        "from list_input import delete_input_list as delete_input\n",
        module_name="edited",
    )

    assert module.imports == [
        SemanticImport(
            module="list_input",
            items=[SemanticImportItem(source="delete_input_list", target="delete_input")],
        )
    ]


def test_convert_pyi_to_ir_accepts_relative_imports():
    module = parse_pyi_text("from ..types_mod import particle\nfrom . import local_particle\n", module_name="edited")

    assert module.imports == [
        SemanticImport(
            module="..types_mod",
            items=[SemanticImportItem(source="particle")],
        ),
        SemanticImport(
            module=".",
            items=[SemanticImportItem(source="local_particle")],
        ),
    ]


def test_convert_pyi_to_ir_annotates_types_from_each_import_statement():
    module = parse_pyi_text(
        """
from first_mod import first_t
from second_mod import second_t as local_t

answer: Int32

def create() -> local_t: ...
""",
        module_name="edited",
    )

    assert module.functions[0].return_type.metadata["external_type_ref"] == {
        "name": "second_t",
        "local_name": "local_t",
        "origin_module": "second_mod",
        "wrapped": False,
        "representation": "opaque",
    }
    qualified = parse_pyi_text(
        """
import first_mod, shared as local_shared

answer: Int32

def create() -> local_shared.inner.types_mod.particle: ...
""",
        module_name="edited",
    )
    assert qualified.functions[0].return_type.metadata["external_type_ref"] == {
        "name": "particle",
        "local_name": "local_shared.inner.types_mod.particle",
        "origin_module": "shared",
        "wrapped": False,
        "representation": "opaque",
    }


def test_pyi_paths_to_semantic_modules_reconciles_opaque_and_edited_external_types(tmp_path: Path):
    physics = tmp_path / "physics.pyi"
    types_mod = tmp_path / "types_mod.pyi"
    physics.write_text(
        f"""
{CONTRACT_IMPORT}
from types_mod import particle

answer: Int32

def create_particle() -> particle: ...

def move(p: Annotated[particle, CompatibleHandle]) -> None: ...
""",
        encoding="utf-8",
    )
    types_mod.write_text(
        f"""
{CONTRACT_IMPORT}
class particle(Opaque):
    pass
""",
        encoding="utf-8",
    )

    modules = {module.name: module for module in pyi_paths_to_semantic_modules(tmp_path)}
    opaque = modules["types_mod"].classes[0]
    create_ref = modules["physics"].functions[0].return_type.metadata["external_type_ref"]
    move_type = modules["physics"].functions[1].arguments[0].semantic_type

    assert opaque.metadata == {"representation": "opaque"}
    assert create_ref == {
        "name": "particle",
        "local_name": "particle",
        "origin_module": "types_mod",
        "wrapped": False,
        "representation": "opaque",
    }
    assert [constraint.name for constraint in move_type.constraints] == ["CompatibleHandle"]

    types_mod.write_text(
        f"""
{CONTRACT_IMPORT}
class particle:
    mass: Float64
""",
        encoding="utf-8",
    )
    edited_modules = {module.name: module for module in pyi_paths_to_semantic_modules([physics, types_mod])}
    edited_ref = edited_modules["physics"].functions[0].return_type.metadata["external_type_ref"]

    assert edited_ref["wrapped"] is True
    assert edited_ref["representation"] == "wrapped"
    assert edited_modules["types_mod"].classes[0].fields[0].name == "mass"


def test_pyi_paths_to_semantic_modules_reconciles_relative_namespace_type_refs(tmp_path: Path):
    physics = tmp_path / "physics.pyi"
    a_types = tmp_path / "a_types.pyi"
    physics.write_text(
        """
from . import a_types

def move(p: a_types.state) -> None: ...
""",
        encoding="utf-8",
    )
    a_types.write_text(
        """
class state:
    pass
""",
        encoding="utf-8",
    )

    modules = {module.name: module for module in pyi_paths_to_semantic_modules(tmp_path)}
    state_ref = modules["physics"].functions[0].arguments[0].semantic_type.metadata["external_type_ref"]

    assert state_ref == {
        "name": "state",
        "local_name": "a_types.state",
        "origin_module": "a_types",
        "wrapped": True,
        "representation": "wrapped",
    }


def test_convert_pyi_to_ir_accepts_relative_namespace_alias_type_refs(tmp_path: Path):
    physics = tmp_path / "physics.pyi"
    a_types = tmp_path / "a_types.pyi"
    physics.write_text(
        """
from . import a_types as at

def move(p: at.state) -> None: ...
""",
        encoding="utf-8",
    )
    a_types.write_text(
        """
class state:
    pass
""",
        encoding="utf-8",
    )

    modules = {module.name: module for module in pyi_paths_to_semantic_modules(tmp_path)}
    state_ref = modules["physics"].functions[0].arguments[0].semantic_type.metadata["external_type_ref"]

    assert state_ref == {
        "name": "state",
        "local_name": "at.state",
        "origin_module": "a_types",
        "wrapped": True,
        "representation": "wrapped",
    }


def test_pyi_paths_to_semantic_modules_preserves_dotted_module_names_from_directory(tmp_path: Path):
    package = tmp_path / "shared"
    package.mkdir()
    (tmp_path / "physics.pyi").write_text(
        """
from shared.types_mod import particle

def move(p: particle) -> None: ...
""",
        encoding="utf-8",
    )
    (package / "types_mod.pyi").write_text(
        """
class particle(Opaque):
    pass
""",
        encoding="utf-8",
    )

    modules = {module.name: module for module in pyi_paths_to_semantic_modules(tmp_path)}
    particle_ref = modules["physics"].functions[0].arguments[0].semantic_type.metadata["external_type_ref"]

    assert "shared.types_mod" in modules
    assert particle_ref["origin_module"] == "shared.types_mod"
    assert particle_ref["representation"] == "opaque"


def test_pyi_paths_to_semantic_modules_handles_duplicate_roots_and_ambiguous_module_names(tmp_path: Path):
    package = tmp_path / "shared"
    package.mkdir()
    pyi_path = package / "types_mod.pyi"
    pyi_path.write_text("class particle:\n    pass\n", encoding="utf-8")

    assert [module.name for module in pyi_paths_to_semantic_modules([tmp_path, tmp_path])] == ["shared.types_mod"]
    with pytest.raises(ValueError) as error:
        pyi_paths_to_semantic_modules([tmp_path, package])
    assert str(error.value) == f"Ambiguous module name for {pyi_path}: 'shared.types_mod' or 'types_mod'"


def test_pyi_paths_to_semantic_modules_ignores_directories_with_pyi_suffix(tmp_path: Path):
    (tmp_path / "ignored.pyi").mkdir()
    (tmp_path / "types_mod.pyi").write_text("class particle:\n    pass\n", encoding="utf-8")

    assert [module.name for module in pyi_paths_to_semantic_modules(tmp_path)] == ["types_mod"]


def test_pyi_file_to_semantic_module_and_modules_forward_module_name_encoding_and_filename(tmp_path: Path):
    pyi_path = tmp_path / "types_mod.pyi"
    pyi_path.write_bytes("# caf\xe9\nclass particle:\n    pass\n".encode("latin-1"))

    module = pyi_file_to_semantic_module(pyi_path, module_name="custom.types_mod", encoding="latin-1")
    assert module.name == "custom.types_mod"
    assert module.classes[0].name == "particle"
    assert pyi_paths_to_semantic_modules(pyi_path, encoding="latin-1")[0].name == "types_mod"

    invalid_path = tmp_path / "invalid.pyi"
    invalid_path.write_text("from broken import\n", encoding="utf-8")
    with pytest.raises(SyntaxError) as error:
        pyi_file_to_semantic_module(invalid_path)
    assert error.value.filename == str(invalid_path)

    semantic_invalid_path = tmp_path / "semantic_invalid.pyi"
    semantic_invalid_path.write_text("def f(x) -> None: ...\n", encoding="utf-8")
    with pytest.raises(ValueError) as semantic_error:
        pyi_file_to_semantic_module(semantic_invalid_path)
    message = str(semantic_error.value)
    assert message.startswith(f"{semantic_invalid_path}: ")
    assert "Expected typed argument: 'x'" in message


def test_pyi_conversion_cache_reuses_file_parse_for_same_module_key(monkeypatch, tmp_path: Path):
    pyi_path = tmp_path / "types_mod.pyi"
    pyi_path.write_text(f"{CONTRACT_IMPORT}value: Int32\n", encoding="utf-8")

    original_parse = pyi_pipeline.parse_pyi_text
    parsed_filenames: list[str] = []

    def parse_once(source: str, *, filename: str = "<pyi>"):
        parsed_filenames.append(filename)
        return original_parse(source, filename=filename)

    monkeypatch.setattr(pyi_pipeline, "parse_pyi_text", parse_once)
    cache = pyi_pipeline._PyiSemanticModuleCache()

    first = cache.file_to_semantic_module(pyi_path)
    second = cache.file_to_semantic_module(pyi_path, module_name="types_mod")
    renamed = cache.file_to_semantic_module(pyi_path, module_name="renamed_types")

    assert first is second
    assert renamed is not first
    assert [Path(filename) for filename in parsed_filenames] == [pyi_path, pyi_path]


def test_convert_pyi_to_ir_and_import_parser_edge_cases():
    module = pyi_text_to_semantic_module("from m import a, b as c\n", module_name="edited")
    assert module.name == "edited"
    assert module.imports == [
        SemanticImport(
            module="m",
            items=[
                SemanticImportItem(source="a"),
                SemanticImportItem(source="b", target="c"),
            ],
        ),
    ]

    with pytest.raises(SyntaxError):
        pyi_text_to_semantic_module("from m import\n", module_name="edited")


def test_generated_native_scope_comes_from_contract_filename():
    parsed = parse_fortran_file(
        """
module solver_mod
contains
  subroutine solve(value)
    real(8), intent(in) :: value
  end subroutine solve
end module solver_mod
"""
    )
    module = fortran_file_to_semantic_modules(parsed)[0]
    loaded = parse_pyi_text(emit_module(module), module_name="renamed_contract")

    assert loaded.name == "renamed_contract"
    assert native_contract_issues(loaded) == []
    assert loaded.origin.native_name == "renamed_contract"
    assert loaded.functions[0].origin.native_scope == "renamed_contract"


def test_generated_standalone_contract_retains_standalone_native_placement():
    parsed = parse_fortran_file(
        """
subroutine solve(value)
  real(8), intent(in) :: value
end subroutine solve
"""
    )
    module = fortran_file_to_semantic_modules(parsed, standalone_module_name="root_contract")[0]
    generated = emit_module(module)
    loaded = parse_pyi_text(generated, module_name="renamed_root_contract")

    assert "@standalone" in generated
    assert loaded.functions[0].origin.native_scope is None
    assert native_contract_issues(loaded) == []
    assert loaded.origin.native_name == "renamed_root_contract"
    assert loaded.functions[0].origin.native_scope is None
