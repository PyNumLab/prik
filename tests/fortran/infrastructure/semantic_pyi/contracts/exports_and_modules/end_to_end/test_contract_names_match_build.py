"""The contract a source build writes names the declarations that build published."""

import ast
from pathlib import Path

import numpy as np
import pytest

from prik.pipeline.build import BUILD_CONTRACT_DIRECTORY_NAME, build_fortran_extension
from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module, _sole_native_module

pytestmark = pytest.mark.fortran_end_to_end

# A module variable and a module procedure whose source names both want the
# Python name `lambda_`. The collision crosses declaration categories, so any
# stage naming them in a different order settles the pair the other way round.
CROSS_CATEGORY_COLLISION = """
module collide_mod
  implicit none
  integer :: lambda = 7
contains
  integer function lambda_()
    lambda_ = 1
  end function lambda_
end module collide_mod
"""


def _declared_names(contract: Path) -> dict[str, str]:
    """Map each declaration in one contract to the kind of statement declaring it."""
    module = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    declared: dict[str, str] = {}
    for statement in module.body:
        if isinstance(statement, ast.FunctionDef):
            declared[statement.name] = "function"
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            declared[statement.target.id] = "variable"
        elif isinstance(statement, ast.ClassDef):
            declared[statement.name] = "class"
    return declared


def _stated_exports(contract: Path) -> list[str]:
    """Return the ``__all__`` a generated contract states about itself."""
    module = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    for statement in module.body:
        targets = getattr(statement, "targets", [])
        if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            return [ast.literal_eval(element) for element in statement.value.elts]
    raise AssertionError(f"{contract} states no __all__")


def test_a_cross_category_collision_settles_the_same_way_for_both(tmp_path: Path):
    """One stage owns the name, so the contract cannot bind the pair the other way."""
    source = tmp_path / "collide_mod.f90"
    source.write_text(CROSS_CATEGORY_COLLISION, encoding="utf-8")

    result = build_fortran_extension(
        source,
        output_dir=tmp_path / "build",
        output_name="collide_api",
    )
    namespace = _sole_native_module(result.import_module())
    contract = result.output_dir / BUILD_CONTRACT_DIRECTORY_NAME / "collide_mod.pyi"

    declared = _declared_names(contract)
    assert set(declared) == set(_stated_exports(contract))

    # The build decides which declaration each name reaches; naming the same
    # pair in a different order would swap these two and leave every individual
    # assertion above still passing.
    for name, kind in declared.items():
        published = getattr(namespace, name)
        if kind == "function":
            assert callable(published), f"contract declares {name} a function; the build published {published!r}"
            assert published() == np.int32(1)
        else:
            assert not callable(published), f"contract declares {name} a variable; the build published {published!r}"
            assert published == np.int32(7)


def test_a_derived_type_is_named_once_for_the_build_and_its_contract(tmp_path: Path):
    """A class name is a public name too, so the same owner settles it."""
    source = tmp_path / "typed_mod.f90"
    source.write_text(
        """
module typed_mod
  implicit none
  type :: Point_T
    integer :: x = 3
  end type Point_T
end module typed_mod
""",
        encoding="utf-8",
    )

    result = build_fortran_extension(
        source,
        output_dir=tmp_path / "build",
        output_name="typed_api",
    )
    namespace = _sole_native_module(result.import_module())
    contract = result.output_dir / BUILD_CONTRACT_DIRECTORY_NAME / "typed_mod.pyi"

    declared = _declared_names(contract)
    assert set(declared) == set(_stated_exports(contract))
    for name in declared:
        assert hasattr(namespace, name), f"contract declares {name}; the build published {dir(namespace)}"


def test_an_edited_contract_keeps_arbitrary_class_capitalization(tmp_path: Path):
    """The generated class style is a default; an edited contract owns its spelling."""
    module, _result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="mixed_case_contract_mod",
        source_text="""
module mixed_case_contract_mod
  implicit none
  type :: point
    integer :: x = 3
  end type point
end module mixed_case_contract_mod
""",
        contract_text="""
from prik.contracts import Int32

class pOiNt:
    def __init__(self, *, x: Int32 = 3) -> None: ...

    x: Int32

__all__ = ["pOiNt"]
""",
    )

    value = module.pOiNt()
    assert value.x == np.int32(3)
