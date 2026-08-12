"""Tests split by stable ownership concept from `test_imports_and_packages.py`."""

import prik
import pytest
from prik import parse_fortran_file as parse_fortran_source
from prik.printers import (
    PyiPrinter,
    emit_module,
)
from prik.pipeline.pyi import (
    emit_module_stubs,
    opaque_dependency_modules,
    pyi_text_to_semantic_module as _parse_pyi_text,
)
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.models import (
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticField,
    SemanticFunction,
    SemanticImport,
    SemanticModule,
    SemanticOrigin,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
)
from tests.fortran._support.printer_models import generate_pyi


def test_prik_public_api_exports_module_stub_emitter():
    assert "emit_module_stubs" in prik.__all__
    assert prik.emit_module_stubs is emit_module_stubs


def test_fortran_generated_contracts_reserve_colliding_public_names_by_namespace():
    int32_type = SemanticType("Int32")
    origin = SemanticOrigin(source_language="fortran", native_scope="naming_mod")
    module = SemanticModule(
        name="naming_mod",
        classes=[
            SemanticClass(
                name="visible_t",
                fields=[
                    SemanticField("lambda", int32_type),
                    SemanticField("lambda_", int32_type),
                ],
                origin=origin,
            )
        ],
        functions=[
            SemanticFunction("lambda", native_name="lambda", return_type=int32_type, origin=origin),
            SemanticFunction("lambda_", native_name="lambda_", return_type=int32_type, origin=origin),
        ],
        origin=origin,
    )

    code = emit_module(module, normalize_fortran_public_names=True)

    assert 'lambda_: Annotated[Int32, SourceName("lambda")]' in code
    assert 'lambda__2: Annotated[Int32, SourceName("lambda_")]' in code
    assert '@bind("lambda")\ndef lambda_() -> Int32: ...' in code
    assert '@bind("lambda_")\ndef lambda__2() -> Int32: ...' in code
    assert "def lambda__3" not in code


def test_pyi_emission_context_isolates_modules_and_shares_nested_imports():
    printer = PyiPrinter(normalize_fortran_public_names=True)
    first = printer._emission_context(SemanticModule(name="first"))
    second = printer._emission_context(SemanticModule(name="second"))
    nested = first.inside_class("record_t")

    first.contract("Addr")
    nested.contract("Pointer")

    assert first.contract_import() == "from prik.contracts import Addr, Pointer"
    assert nested.contract_import() == first.contract_import()
    assert nested.public_namespace == ("record_t",)
    assert first.public_namespace == ()
    assert second.contract_import() == ""


def test_printer_validation_and_opaque_dependency_edge_cases():
    printer = PyiPrinter()

    with pytest.raises(ValueError, match="Shape constraints are not canonical"):
        printer.emit(SemanticConstraint("Shape"))

    plain_type = SemanticType("Float64", dtype="Float64")
    context = printer._emission_context(SemanticModule(name="edge_cases"))
    assert printer._emit_storage_type(plain_type, context) == "Float64"

    malformed_import = SemanticType(
        "external_type",
        dtype="external_type",
        metadata={
            "external_type_ref": {
                "origin_module": "",
                "name": "external_type",
                "local_name": "external_type",
            }
        },
    )
    assert (
        printer._effective_imports(SemanticModule(name="api", variables=[SemanticArgument("value", malformed_import)]))
        == []
    )

    invalid_opaque_ref = SemanticType(
        "external_type",
        dtype="external_type",
        metadata={
            "external_type_ref": {
                "representation": "opaque",
                "origin_module": "types",
                "name": 42,
            }
        },
    )
    known_opaque_ref = SemanticType(
        "external_type",
        dtype="external_type",
        metadata={
            "external_type_ref": {
                "representation": "opaque",
                "origin_module": "types",
                "name": "external_type",
            }
        },
    )
    assert (
        opaque_dependency_modules(
            SemanticModule(
                name="api",
                variables=[
                    SemanticArgument("invalid", invalid_opaque_ref),
                    SemanticArgument("known", known_opaque_ref),
                ],
            ),
            available_modules=[SemanticModule(name="types", classes=[SemanticClass(name="external_type")])],
        )
        == []
    )

    with pytest.raises(ValueError, match="duplicate semantic module"):
        emit_module_stubs([SemanticModule(name="duplicate"), SemanticModule(name="duplicate")])


def test_opaque_dependency_modules_scan_all_references_and_preserve_metadata():
    plain_type = SemanticType("Float64", dtype="Float64")
    invalid_opaque_ref = SemanticType(
        "invalid_type",
        dtype="invalid_type",
        metadata={
            "external_type_ref": {
                "representation": "opaque",
                "origin_module": "types",
                "name": 42,
            }
        },
    )
    known_opaque_ref = SemanticType(
        "known_type",
        dtype="known_type",
        metadata={
            "external_type_ref": {
                "representation": "opaque",
                "origin_module": "types",
                "name": "known_type",
            }
        },
    )
    missing_opaque_ref = SemanticType(
        "missing_type",
        dtype="missing_type",
        metadata={
            "external_type_ref": {
                "representation": "opaque",
                "origin_module": "types",
                "name": "missing_type",
            }
        },
    )

    dependencies = opaque_dependency_modules(
        SemanticModule(
            name="api",
            variables=[
                SemanticArgument("plain", plain_type),
                SemanticArgument("invalid", invalid_opaque_ref),
                SemanticArgument("known", known_opaque_ref),
                SemanticArgument("missing", missing_opaque_ref),
            ],
        ),
        available_modules=[SemanticModule(name="types", classes=[SemanticClass(name="known_type")])],
    )

    assert dependencies == [
        SemanticModule(
            name="types",
            classes=[
                SemanticClass(
                    name="missing_type",
                    native_name="missing_type",
                    base_classes=["Opaque"],
                    metadata={"representation": "opaque"},
                )
            ],
        )
    ]


def test_emit_module_stubs_honors_available_opaque_dependency_modules():
    known_opaque_ref = SemanticType(
        "known_type",
        dtype="known_type",
        metadata={
            "external_type_ref": {
                "representation": "opaque",
                "origin_module": "types",
                "name": "known_type",
            }
        },
    )
    stubs = emit_module_stubs(
        SemanticModule(
            name="api",
            variables=[SemanticArgument("known", known_opaque_ref)],
        ),
        available_modules=[SemanticModule(name="types", classes=[SemanticClass(name="known_type")])],
    )

    assert set(stubs) == {"api"}


def test_emit_omits_resolved_source_kind_imports():
    source = """
module user_mod

use iso_c_binding

contains

subroutine foo(x)

    integer, intent(in) :: x

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "iso_c_binding" not in code


def test_emit_import_renames():
    source = """
module user_mod

use list_input, delete_input => delete_input_list

end module
"""

    code = generate_pyi(source)

    assert "from list_input import delete_input_list as delete_input" in code


def test_emit_imported_derived_type_reference_without_reexporting_class():
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
    stubs = emit_module_stubs(module)
    code = stubs["physics"]

    assert "from types_mod import particle" in code
    assert "from . import types_mod" not in code
    assert "p: particle" in code
    assert "Addr(particle)" not in code
    assert "class particle" not in code
    assert stubs["types_mod"].endswith("class particle(Opaque):\n    pass")


def test_emit_procedure_local_imported_derived_types_as_qualified_module_refs():
    parsed = parse_fortran_source(
        """
module physics
contains
  subroutine use_a(p)
    use a_types, only: state
    type(state), intent(inout) :: p
  end subroutine use_a

  subroutine use_b(p)
    use b_types, only: state
    type(state), intent(inout) :: p
  end subroutine use_b
end module physics
"""
    )

    module = fortran_module_to_semantic_module(parsed)
    code = emit_module(module)

    assert "from . import a_types, b_types" in code
    assert "p: a_types.state" in code
    assert "p: b_types.state" in code
    assert "from a_types import state" not in code
    assert "from b_types import state" not in code
    assert "from .a_types import state" not in code
    assert "from .b_types import state" not in code
    assert " as imported_a_types" not in code


def test_emit_procedure_local_import_namespace_collision_fails_without_alias():
    parsed = parse_fortran_source(
        """
module physics
contains
  subroutine a_types()
  end subroutine a_types

  subroutine use_state(p)
    use a_types, only: state
    type(state), intent(inout) :: p
  end subroutine use_state
end module physics
"""
    )

    module = fortran_module_to_semantic_module(parsed)

    with pytest.raises(ValueError, match="Procedure-local Fortran import namespace collides"):
        emit_module(module)


def test_emit_procedure_local_import_namespace_collision_with_synthetic_import_fails():
    procedure_ref = {
        "name": "state",
        "local_name": "a_types.state",
        "origin_module": "a_types",
        "wrapped": False,
        "representation": "opaque",
        "import_scope": "procedure",
    }
    flattened_ref = {
        "name": "a_types",
        "local_name": "a_types",
        "origin_module": "other_types",
        "wrapped": False,
        "representation": "opaque",
    }
    module = SemanticModule(
        name="api",
        functions=[
            SemanticFunction(
                "use_state",
                arguments=[
                    SemanticArgument("p", SemanticType("a_types.state", metadata={"external_type_ref": procedure_ref}))
                ],
            ),
            SemanticFunction(
                "use_flat",
                arguments=[
                    SemanticArgument("p", SemanticType("a_types", metadata={"external_type_ref": flattened_ref}))
                ],
            ),
        ],
    )

    with pytest.raises(ValueError, match="Procedure-local Fortran import namespace collides"):
        emit_module(module)


def test_emit_bare_use_adds_import_for_opaque_dependency_type():
    parsed = parse_fortran_source(
        """
module physics
  use types_mod
contains
  subroutine move(p)
    type(particle), intent(inout) :: p
  end subroutine move
end module physics
"""
    )
    stubs = emit_module_stubs(fortran_module_to_semantic_module(parsed))

    assert "import types_mod" in stubs["physics"]
    assert "from types_mod import particle" in stubs["physics"]
    assert stubs["types_mod"].endswith("class particle(Opaque):\n    pass")


def test_emit_omits_structured_source_kind_import_without_items():
    module = SemanticModule(
        name="imports",
        imports=[SemanticImport(module="iso_c_binding")],
    )

    code = emit_module(module)

    assert code == ""


def test_emit_module_aliases_contract_import_when_user_name_collides():
    array_type = SemanticType(
        "Float64",
        dtype="Float64",
        rank=1,
        shape=[":"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=1,
                shape=[":"],
                category="assumed_size",
                source_shape=["*"],
                order="ORDER_F",
                contiguous=True,
            ),
        ),
    )
    module = SemanticModule(
        name="alias_mod",
        variables=[
            SemanticVariable(
                "Flat",
                SemanticType("Int32", constraints=[SemanticConstraint("Constant")]),
                default_value="10",
            )
        ],
        functions=[SemanticFunction("inspect", arguments=[SemanticArgument("values", array_type)])],
    )

    code = emit_module(module)

    assert "Flat as prik_Flat" in code.splitlines()[0]
    reparsed = _parse_pyi_text(code, module_name="alias_mod")
    assert reparsed.variables[0].name == "Flat"
    assert reparsed.functions[0].arguments[0].semantic_type.storage.array.category == "assumed_size"


def test_emit_module_aliases_standalone_only_for_actual_name_collisions():
    int32_type = SemanticType("Int32")
    standalone_origin = SemanticOrigin(source_language="fortran", native_scope=None)

    ordinary = emit_module(
        SemanticModule(
            name="ordinary",
            functions=[SemanticFunction("calculate", return_type=int32_type, origin=standalone_origin)],
        )
    )
    colliding = emit_module(
        SemanticModule(
            name="colliding",
            functions=[SemanticFunction("standalone", return_type=int32_type, origin=standalone_origin)],
        )
    )
    twice_colliding = emit_module(
        SemanticModule(
            name="twice_colliding",
            variables=[
                SemanticVariable(
                    "prik_standalone",
                    SemanticType("Int32", constraints=[SemanticConstraint("Constant")]),
                    default_value="1",
                )
            ],
            functions=[SemanticFunction("standalone", return_type=int32_type, origin=standalone_origin)],
        )
    )

    assert "from prik.contracts import Int32, standalone\n" in ordinary
    assert "@standalone\ndef calculate() -> Int32: ..." in ordinary
    assert "from prik.contracts import Int32, standalone as prik_standalone\n" in colliding
    assert "@prik_standalone\ndef standalone() -> Int32: ..." in colliding
    assert "standalone as prik_standalone_2" in twice_colliding.splitlines()[0]
    assert "@prik_standalone_2\ndef standalone() -> Int32: ..." in twice_colliding
