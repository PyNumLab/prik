"""Generated Python surface for an abstract Fortran type hierarchy."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from prik.pipeline.build import BUILD_CONTRACT_DIRECTORY_NAME, build_fortran_extension
from prik.preprocessing import PreprocessingConfig
from tests.fortran._support.wrapper_build import _compiler, _import_from_build_dir, _sole_native_module

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "native" / "abstract_hierarchy.f90"


@pytest.fixture(scope="module")
def build(tmp_path_factory):
    return build_fortran_extension(
        SOURCE,
        output_dir=tmp_path_factory.mktemp("abstract_hierarchy"),
        preprocessing=PreprocessingConfig(mode="compiler", compiler=_compiler()),
    )


@pytest.fixture(scope="module")
def module(build):
    return _sole_native_module(_import_from_build_dir(build.module_name, build.output_dir))


def test_abstract_type_has_no_constructor_and_publishes_only_public_members(module):
    """`type, abstract ::` has no instances, so its Python class has no constructor.

    The hierarchy publishes only what its `private` statements allow.
    """
    with pytest.raises(TypeError, match="abstract native type and cannot be instantiated"):
        module.Shape_Base()
    assert "__init__" not in module.Shape_Base.__dict__

    assert {name for name in dir(module.Shape_Base) if not name.startswith("_")} == {
        "area",
        "label",
        "side_count",
        "bump_sides",
    }
    assert {name for name in dir(module.Circle) if not name.startswith("_")} == {
        "area",
        "label",
        "side_count",
        "bump_sides",
        "radius",
    }


def test_extensions_subclass_the_abstract_base_and_dispatch_its_bindings(module):
    """Fortran `extends` becomes real Python inheritance, not copied members.

    A deferred binding names a contract and the dynamic type selects the body;
    an implemented binding on the abstract base serves its extensions.
    """
    assert issubclass(module.Circle, module.Shape_Base)
    assert issubclass(module.Square, module.Shape_Base)
    assert module.Circle.__mro__[:2] == (module.Circle, module.Shape_Base)

    circle = module.Circle(radius=np.float64(2.0))
    square = module.Square(side=np.float64(3.0))
    assert isinstance(circle, module.Shape_Base)

    assert circle.area() == pytest.approx(12.566370614, rel=1e-9)
    assert square.area() == pytest.approx(9.0)
    assert circle.label() == "circle  "
    assert square.label() == "square  "
    # The base declares the same bindings, and they resolve through the caller's
    # concrete type rather than through anything the abstract type implements.
    assert module.Shape_Base.area(circle) == pytest.approx(circle.area())
    assert module.Shape_Base.area(square) == pytest.approx(square.area())

    assert circle.side_count() == np.int32(0)
    circle.bump_sides()
    circle.bump_sides()
    assert circle.side_count() == np.int32(2)


def test_interoperable_type_keeps_its_layout_beside_the_hierarchy(module):
    """A `bind(c)` type in the same module still wraps through its own accessors."""
    box = module.Extent(width=np.float64(3.0), height=np.float64(4.0))

    assert box.width == np.float64(3.0)
    assert module.describe(box) == pytest.approx(12.0)

    box.width = np.float64(5.0)
    assert module.describe(box) == pytest.approx(20.0)


def test_build_writes_its_semantic_contract_beside_the_extension(build):
    """Every build leaves the contract describing the API it just generated."""
    contracts = build.output_dir / BUILD_CONTRACT_DIRECTORY_NAME
    module_contract = contracts / "abstract_hierarchy.pyi"
    package_contract = contracts / "__init__.pyi"
    assert module_contract in build.generated_files
    assert package_contract in build.generated_files
    assert module_contract.is_file()
    assert package_contract.read_text(encoding="utf-8").strip() == ("from . import abstract_hierarchy")

    text = module_contract.read_text(encoding="utf-8")
    assert "@abstract" in text
    assert "@abstractmethod" in text
