"""Tests split by stable ownership concept from `test_imports_and_packages.py`."""

import json
import pytest
import prik.pipeline.pyi as pyi_pipeline
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.policy.contract_imports import complete_contract_imports
from prik.policy.exports import contract_name_for_source
from prik.printers import (
    PyiPrinter,
    emit_module,
)
from prik.pipeline.pyi import (
    emit_module_stubs,
    opaque_dependency_modules,
    pyi_text_to_semantic_module as _parse_pyi_text,
)
from prik.policy.exports import complete_python_export_policy
from prik.semantics import fortran_file_to_semantic_modules
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.models import (
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticField,
    SemanticFunction,
    SemanticImport,
    SemanticImportItem,
    SemanticModule,
    SemanticOrigin,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
)
from tests.fortran._support.printer_models import generate_pyi


def test_pyi_pipeline_exports_module_stub_emitter():
    assert "emit_module_stubs" in pyi_pipeline.__all__
    assert pyi_pipeline.emit_module_stubs is emit_module_stubs


def test_generated_pyi_separates_top_level_functions_with_a_blank_line():
    int_type = SemanticType("Int")
    code = emit_module(
        SemanticModule(
            name="readable",
            functions=[
                SemanticFunction("first", return_type=int_type),
                SemanticFunction("second", return_type=int_type),
            ],
        )
    )

    assert "def first() -> Int: ...\n\ndef second() -> Int: ..." in code


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
    complete_python_export_policy(module)

    code = emit_module(module, normalize_public_names=True)

    assert 'lambda_: Annotated[Int32, SourceName("lambda")]' in code
    assert 'lambda__2: Annotated[Int32, SourceName("lambda_")]' in code
    assert '@bind("lambda")\ndef lambda_() -> Int32: ...' in code
    assert '@bind("lambda_")\ndef lambda__2() -> Int32: ...' in code
    assert "def lambda__3" not in code


def test_pyi_emission_context_isolates_modules_and_shares_nested_imports():
    printer = PyiPrinter(normalize_public_names=True)
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


def test_printing_loaded_contract_preserves_absolute_support_imports():
    module = _parse_pyi_text(
        "from typing import Any\nfrom prik.contracts import Int32\n\ndef identity(value: Int32) -> Int32: ...\n",
        module_name="identity",
    )

    assert "from typing import Any" in emit_module(module)


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
    malformed_module = SemanticModule(name="api", variables=[SemanticVariable("value", malformed_import)])
    complete_python_export_policy(malformed_module)
    complete_contract_imports([malformed_module])
    assert malformed_module.imports == []

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


def test_emit_module_stubs_uses_available_module_public_names_in_imports():
    origin = SemanticOrigin(source_language="fortran")
    available_type = SemanticModule(
        name="types",
        classes=[SemanticClass(name="point_t", origin=origin)],
        origin=origin,
    )
    consumer = SemanticModule(
        name="consumer",
        imports=[
            SemanticImport(
                module="types",
                items=[SemanticImportItem(source="point_t")],
            )
        ],
        origin=origin,
    )

    stubs = emit_module_stubs(
        consumer,
        available_modules=[available_type, consumer],
        normalize_public_names=True,
    )

    assert set(stubs) == {"consumer"}
    assert "from .types import Point_T as point_t" in stubs["consumer"]


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

    assert "from .list_input import delete_input_list as delete_input" in code


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

    assert "from .types_mod import particle" in code
    assert "from . import types_mod" not in code
    assert "p: particle" in code
    assert "Addr(particle)" not in code
    assert "class particle" not in code
    assert stubs["types_mod"].endswith('class particle(Opaque):\n    pass\n\n__all__ = ["particle"]')


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

    code = emit_module_stubs(fortran_module_to_semantic_module(parsed))["physics"]

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
    complete_python_export_policy(module)

    with pytest.raises(ValueError, match="cannot bind 'a_types'"):
        complete_contract_imports([module])


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

    complete_python_export_policy(module)

    with pytest.raises(ValueError, match="cannot bind 'a_types'"):
        complete_contract_imports([module])


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

    # The contract binds the type a declaration names, not the `use` itself.
    assert "import types_mod" not in stubs["physics"].splitlines()
    assert "from .types_mod import particle" in stubs["physics"]
    assert stubs["types_mod"].endswith('class particle(Opaque):\n    pass\n\n__all__ = ["particle"]')


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


def test_generated_contract_imports_a_name_under_the_spelling_its_definition_uses():
    """An import binds the name the module it reads from actually defines.

    A source-derived contract writes its declarations under Python names, so a
    Fortran entity spelled in capitals is declared lower case. An import asking
    for the source spelling names nothing the dependency contract defines, and
    loading the package back fails on it.
    """
    consts = parse_fortran_source("""
module consts_mod
implicit none
integer, parameter :: IK = 4
end module consts_mod
""")
    infos = parse_fortran_source("""
module infos_mod
use consts_mod, only : IK
implicit none
end module infos_mod
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(consts), fortran_module_to_semantic_module(infos)],
        normalize_public_names=True,
    )

    assert "ik: Final[Int32]" in stubs["consts_mod"]
    assert "from .consts_mod import ik" in stubs["infos_mod"]
    assert "import IK" not in stubs["infos_mod"]


def test_generated_contract_renames_an_imported_name_under_both_spellings():
    """A renamed import binds the defined name to this contract's own name."""
    consts = parse_fortran_source("""
module consts_mod
implicit none
integer, parameter :: IK = 4
end module consts_mod
""")
    renaming = parse_fortran_source("""
module renaming_mod
use consts_mod, only : MY_IK => IK
implicit none
end module renaming_mod
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(consts), fortran_module_to_semantic_module(renaming)],
        normalize_public_names=True,
    )

    assert "from .consts_mod import ik as my_ik" in stubs["renaming_mod"]


def test_generated_contract_imports_a_prototype_under_its_declared_spelling():
    """A prototype keeps its spelling, so the import that binds it keeps it too.

    A contract writes a prototype under the name its own declaration states, and
    an annotation naming that prototype is written the same way, so normalizing
    the import would bind a name no declaration defines.
    """
    declares = parse_fortran_source("""
module pintrf_mod
implicit none
private
public :: OBJ
abstract interface
subroutine OBJ(x)
implicit none
real(8), intent(in) :: x(:)
end subroutine OBJ
end interface
end module pintrf_mod
""")
    solver = parse_fortran_source("""
module solver_mod
use pintrf_mod, only : OBJ
implicit none
contains
subroutine solve(calfun, x)
procedure(OBJ) :: calfun
real(8), intent(inout) :: x(:)
end subroutine solve
end module solver_mod
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(declares), fortran_module_to_semantic_module(solver)],
        normalize_public_names=True,
    )

    assert "def OBJ(" in stubs["pintrf_mod"]
    assert "from .pintrf_mod import OBJ" in stubs["solver_mod"]
    assert "calfun: OBJ" in stubs["solver_mod"]


def test_fortran_contract_records_no_source_name_for_a_case_only_python_name():
    """Writing a Fortran entity in lower case renames nothing worth recording.

    Fortran names entities without regard to case, so a capitalized source
    spelling and the lower-case Python name are the same entity and the
    generated Fortran reaches it either way.
    """
    source = """
module consts_mod
implicit none
integer, parameter :: IK = 4
contains
subroutine SCALE_VALUE(x)
integer, intent(in) :: x
end subroutine SCALE_VALUE
end module consts_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    complete_python_export_policy(module)
    code = emit_module(module, normalize_public_names=True)

    assert "ik: Final[Int32]" in code
    assert "def scale_value(" in code
    assert "SourceName" not in code
    assert "@bind(" not in code


def test_fortran_contract_records_a_source_name_python_cannot_spell():
    """A name Python cannot hold as written keeps the spelling it came from."""
    source = """
module naming_mod
implicit none
integer :: lambda
integer :: LAMBDA_
contains
subroutine ASSERT(x)
integer, intent(in) :: x
end subroutine ASSERT
end module naming_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    complete_python_export_policy(module)
    code = emit_module(module, normalize_public_names=True)

    assert 'lambda_: Annotated[Int32, SourceName("lambda")]' in code
    assert 'lambda__2: Annotated[Int32, SourceName("LAMBDA_")]' in code
    assert '@bind("ASSERT")\n@native_call([Addr(Arg(0))])\ndef assert_(' in code


def test_non_fortran_declaration_compares_its_native_spelling_exactly():
    """Every other source language names its entities exactly, case included."""
    origin = SemanticOrigin(source_language="c", native_scope="c_mod")
    module = SemanticModule(
        name="c_mod",
        functions=[
            SemanticFunction(
                "scale_value",
                native_name="ScaleValue",
                return_type=SemanticType("Int32"),
                origin=origin,
            )
        ],
        origin=origin,
    )
    complete_python_export_policy(module)

    code = emit_module(module, normalize_public_names=True)

    assert '@bind("ScaleValue")' in code


def test_generated_contract_binds_a_class_whose_python_name_renames_its_type():
    """A renamed class states its native type so the contract reads back."""
    origin = SemanticOrigin(source_language="fortran", native_scope="shapes_mod")
    module = SemanticModule(
        name="shapes_mod",
        classes=[
            SemanticClass(
                name="PointType",
                native_name="POINT_T",
                fields=[SemanticField("x", SemanticType("Float64"))],
                origin=origin,
            )
        ],
        origin=origin,
    )
    complete_python_export_policy(module)

    code = emit_module(module, normalize_public_names=True)

    assert '@bind("POINT_T")\nclass Pointtype:' in code


def test_generated_contract_omits_a_class_bind_for_a_case_only_python_name():
    """A class named without regard to case states no separate native type."""
    origin = SemanticOrigin(source_language="fortran", native_scope="shapes_mod")
    module = SemanticModule(
        name="shapes_mod",
        classes=[
            SemanticClass(
                name="point_t",
                native_name="POINT_T",
                fields=[SemanticField("x", SemanticType("Float64"))],
                origin=origin,
            )
        ],
        origin=origin,
    )
    complete_python_export_policy(module)

    code = emit_module(module, normalize_public_names=True)

    assert "class Point_T:" in code
    assert "@bind(" not in code


def test_prototype_spelling_is_kept_only_for_the_module_that_declares_one():
    """A prototype identity names its module, not a spelling used anywhere.

    One module may declare a prototype while another spells an ordinary
    declaration the same way. The second follows Python naming, so an import
    reading from it asks for the name that module actually defines.
    """
    callbacks = parse_fortran_source("""
module callback_mod
implicit none
private
public :: OBJ
abstract interface
subroutine OBJ(x)
implicit none
real(8), intent(in) :: x
end subroutine OBJ
end interface
end module callback_mod
""")
    values = parse_fortran_source("""
module values_mod
implicit none
integer, parameter :: OBJ = 1
end module values_mod
""")
    consumer = parse_fortran_source("""
module consumer_mod
use values_mod, only : OBJ
implicit none
end module consumer_mod
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(item) for item in (callbacks, values, consumer)],
        normalize_public_names=True,
    )

    assert "def OBJ(" in stubs["callback_mod"]
    assert "obj: Final[Int32]" in stubs["values_mod"]
    assert "from .values_mod import obj" in stubs["consumer_mod"]
    assert "import OBJ" not in stubs["consumer_mod"]


def test_prototype_import_uses_the_declared_spelling_whatever_case_names_it():
    """Fortran reaches a prototype without regard to case; a contract does not.

    A module may write `use callback_mod, only : obj` for a prototype declared
    as `OBJ`, and the annotation then names it that way. The import binds the
    declared spelling under the name this contract uses.
    """
    callbacks = parse_fortran_source("""
module callback_mod
implicit none
public :: OBJ
abstract interface
subroutine OBJ(x)
implicit none
real(8), intent(in) :: x
end subroutine OBJ
end interface
end module callback_mod
""")
    user = parse_fortran_source("""
module user_mod
use callback_mod, only : obj
implicit none
contains
subroutine run(f, v)
procedure(obj) :: f
real(8), intent(in) :: v
end subroutine run
end module user_mod
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(item) for item in (callbacks, user)],
        normalize_public_names=True,
    )

    assert "def OBJ(" in stubs["callback_mod"]
    assert "from .callback_mod import OBJ as obj" in stubs["user_mod"]
    assert "f: obj" in stubs["user_mod"]


def test_import_binds_the_name_a_collision_made_the_declaring_contract_use():
    """A collision moves a name aside, and the import follows it there."""
    home = parse_fortran_source("""
module collide_home
implicit none
contains
subroutine lambda(x)
integer, intent(inout) :: x
end subroutine lambda
subroutine lambda_(x)
integer, intent(inout) :: x
end subroutine lambda_
end module collide_home
""")
    user = parse_fortran_source("""
module collide_user
use collide_home, only : lambda_
implicit none
private
public :: lambda_
end module collide_user
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(item) for item in (home, user)],
        normalize_public_names=True,
    )

    assert "def lambda__2(" in stubs["collide_home"]
    assert "from .collide_home import lambda__2" in stubs["collide_user"]
    assert '__all__ = ["lambda_"]' in stubs["collide_user"]


def test_generated_contract_states_the_names_its_source_publishes():
    """A contract names its whole public surface, not only its re-exports.

    An import cannot say whether a name is needed to express a declaration or
    meant to be published, because a rename reads the same either way. The list
    settles it, and is written to be edited.
    """
    home = parse_fortran_source("""
module surface_home
implicit none
type :: box
integer :: value
end type box
contains
subroutine scale_value(x)
integer, intent(inout) :: x
end subroutine scale_value
end module surface_home
""")
    facade = parse_fortran_source("""
module surface_facade
use surface_home, only : scale_value
implicit none
private
public :: scale_value
end module surface_facade
""")
    consumer = parse_fortran_source("""
module surface_consumer
use surface_home, only : crate => box
implicit none
contains
integer function crate_value(item) result(out)
type(crate), intent(in) :: item
out = item%value
end function crate_value
end module surface_consumer
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(item) for item in (home, facade, consumer)],
        normalize_public_names=True,
    )

    # The publishing module names the import; the consuming one does not.
    assert stubs["surface_facade"].rstrip().endswith('__all__ = ["scale_value"]')
    assert stubs["surface_consumer"].rstrip().endswith('__all__ = ["crate_value"]')
    assert "from .surface_home import Box as Crate" in stubs["surface_consumer"]
    assert '__all__ = ["Box", "scale_value"]' in stubs["surface_home"]


def test_generated_contract_honors_used_module_accessibility_routes():
    """A module-name access statement controls names carried through that route."""
    modules = fortran_file_to_semantic_modules(
        parse_fortran_source("""
module route_home
integer :: x
end module route_home

module route_hidden
use route_home
private :: route_home
end module route_hidden

module route_visible
use route_home
private
public :: route_home
end module route_visible
""")
    )

    stubs = emit_module_stubs(modules, normalize_public_names=True)

    # The route carries nothing a declaration uses or the module publishes, so
    # its contract has nothing to write.
    assert stubs["route_hidden"] == ""
    assert "from .route_home import x" in stubs["route_visible"]
    assert stubs["route_visible"].rstrip().endswith('__all__ = ["x"]')


def test_a_published_intrinsic_name_states_no_contract_import():
    """Publishing a name from an intrinsic module publishes nothing here.

    A module may name an intrinsic constant in its `public` statement, and the
    module it came from has no contract to read it from. The declaration was
    never found, so there is nothing to import and nothing to publish.
    """
    source = """
module kinds_mod
use iso_fortran_env, only : REAL64, INT32
implicit none
private
public :: REAL64, INT32
public :: rate
real(REAL64), parameter :: rate = 2.0d0
end module kinds_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    complete_python_export_policy(module)
    code = emit_module(module, normalize_public_names=True)

    assert [reexport.origin_module for reexport in module.reexports] == ["iso_fortran_env", "iso_fortran_env"]
    assert "iso_fortran_env" not in code
    assert '__all__ = ["rate"]' in code


def test_generated_contract_publishes_a_module_variable_reexport():
    """A re-exporting contract names the declaring variable as public state."""
    parsed = parse_fortran_source("""
module state_home
implicit none
integer, save :: counter = 7
contains
subroutine bump()
counter = counter + 1
end subroutine bump
end module state_home

module state_facade
use state_home, only : counter, bump
implicit none
private
public :: counter, bump
end module state_facade
""")

    modules = fortran_file_to_semantic_modules(parsed)
    facade = next(module for module in modules if module.name == "state_facade")
    stubs = emit_module_stubs(modules, normalize_public_names=True)

    assert sorted((item.local_name, item.entity_kind) for item in facade.reexports) == [
        ("bump", "procedure"),
        ("counter", "variable"),
    ]
    assert "from .state_home import counter, bump" in stubs["state_facade"]
    assert stubs["state_facade"].rstrip().endswith('__all__ = ["counter", "bump"]')


def test_two_spellings_a_case_sensitive_source_keep_distinct_contract_names():
    """A contract records each source name as written, so neither displaces the other.

    Keying contract spellings by a folded source name loses one of a pair only
    a case-sensitive source distinguishes, and an importer then binds whichever
    was recorded first.
    """
    completed = {"Foo": "Foo", "foo": "foo", "SCALE": "scale"}

    assert contract_name_for_source(completed, "Foo") == "Foo"
    assert contract_name_for_source(completed, "foo") == "foo"
    # A case-insensitive source still reaches its name under any spelling.
    assert contract_name_for_source(completed, "scale") == "scale"
    assert contract_name_for_source(completed, "Scale") == "scale"
    assert contract_name_for_source(completed, "missing") is None
    # `FOO` could mean either declaration, and which one a folded lookup found
    # would depend on the order they were recorded in, so it names neither.
    assert contract_name_for_source(completed, "FOO") is None
    assert contract_name_for_source({"foo": "foo", "Foo": "Foo"}, "FOO") is None


SHAPES_SOURCE = """
module shapes
implicit none
type :: point
  integer :: x
end type point
end module shapes
"""


@pytest.mark.parametrize(
    ("association", "published", "spelling"),
    [
        ("point", True, "Point"),
        ("MyPoint => point", True, "Mypoint"),
        ("MyPoint => point", False, "Mypoint"),
    ],
    ids=["published", "renamed-published", "renamed-dependency"],
)
def test_an_imported_type_is_spelled_one_way_throughout_its_contract(association, published, spelling):
    """The import, the annotation, and `__all__` write the name the module publishes.

    Naming completion spelled a published type as a class for `__all__` while
    the annotation wrote the `use` statement's spelling, so one of them always
    named something the contract never bound. A type is spelled as a class
    whether or not the module publishes it, and every place reads that name.
    """
    local = association.split(" => ")[0]
    user = parse_fortran_source(f"""
module user_mod
use shapes, only : {association}
implicit none
private
public :: {f"{local}, " if published else ""}move
contains
subroutine move(p)
type({local}), intent(inout) :: p
end subroutine move
end module user_mod
""")

    stubs = emit_module_stubs(
        [
            fortran_module_to_semantic_module(parse_fortran_source(SHAPES_SOURCE)),
            fortran_module_to_semantic_module(user),
        ],
        normalize_public_names=True,
    )
    contract = stubs["user_mod"]

    bound = "Point" if spelling == "Point" else f"Point as {spelling}"
    assert f"from .shapes import {bound}\n" in contract
    assert f"p: {spelling}\n" in contract
    expected_all = ["move", spelling] if published else ["move"]
    assert contract.rstrip().endswith(f"__all__ = {json.dumps(expected_all)}")


def test_a_declaration_expression_calls_its_callee_by_the_name_the_contract_binds(tmp_path):
    """The call in a shape and the import binding its callee are one spelling.

    `lambda` is a Python keyword and `lambda_` then collides with its escaped
    spelling, so the helpers contract writes `lambda_` and `lambda__2`. The
    expression kept the Fortran spelling while the import bound the completed
    one, leaving a call that was unbound or not Python at all.
    """
    helpers = parse_fortran_source("""
module helpers
implicit none
contains
pure integer function lambda(n)
  integer, intent(in) :: n
  lambda = n
end function lambda
pure integer function lambda_(n)
  integer, intent(in) :: n
  lambda_ = n + 1
end function lambda_
end module helpers
""")
    user = parse_fortran_source("""
module user_mod
use helpers, only : lambda, lambda_
implicit none
contains
subroutine fill(n, x, y)
  integer, intent(in) :: n
  real(8), intent(out) :: x(lambda(n))
  real(8), intent(out) :: y(2*lambda_(n) + n)
end subroutine fill
end module user_mod
""")

    stubs = emit_module_stubs(
        [fortran_module_to_semantic_module(item) for item in (helpers, user)],
        normalize_public_names=True,
    )
    contract = stubs["user_mod"]

    assert "from .helpers import lambda_, lambda__2\n" in contract
    assert "x: Float64[lambda_(n)]" in contract
    assert "y: Float64[2 * lambda__2(n) + n]" in contract
    # Read back as a package, each call reaches the native function it names.
    for name, text in stubs.items():
        (tmp_path / f"{name}.pyi").write_text(text, encoding="utf-8")
    reloaded = {module.name: module for module in pyi_pipeline.pyi_paths_to_semantic_modules(tmp_path)}
    assert [
        (reference.name, reference.native_scope, reference.native_name)
        for argument in reloaded["user_mod"].functions[0].arguments[1:]
        for axis in argument.semantic_type.storage.array.expression_callables
        for reference in axis
    ] == [("lambda_", "helpers", "lambda"), ("lambda__2", "helpers", "lambda_")]
