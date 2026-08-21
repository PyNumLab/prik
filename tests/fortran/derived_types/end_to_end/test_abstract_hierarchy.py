"""Generated Python surface for an abstract Fortran type hierarchy."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "abstract_hierarchy.f90"
GENERATED = {
    "bind_c_abstract_hierarchy_wrapper.f90",
    "abstract_hierarchy_wrapper.c",
    "abstract_hierarchy_wrapper.h",
}


@pytest.fixture(scope="module")
def module(tmp_path_factory):
    return _build_source_and_import(SOURCE, tmp_path_factory.mktemp("abstract_hierarchy"), GENERATED)


def test_abstract_type_cannot_be_instantiated(module):
    """`type, abstract ::` has no instances, so its Python class has no constructor."""
    with pytest.raises(TypeError, match="abstract native type and cannot be instantiated"):
        module.shape_base()

    assert "__init__" not in module.shape_base.__dict__


def test_extensions_are_python_subclasses_of_the_abstract_base(module):
    """Fortran `extends` becomes real Python inheritance, not copied members."""
    assert issubclass(module.circle, module.shape_base)
    assert issubclass(module.square, module.shape_base)
    assert module.circle.__mro__[:2] == (module.circle, module.shape_base)

    assert isinstance(module.circle(radius=np.float64(1.0)), module.shape_base)


def test_deferred_bindings_dispatch_to_each_concrete_override(module):
    """A deferred binding names a contract; the dynamic type selects the body."""
    circle = module.circle(radius=np.float64(2.0))
    square = module.square(side=np.float64(3.0))

    assert circle.area() == pytest.approx(12.566370614, rel=1e-9)
    assert square.area() == pytest.approx(9.0)
    assert circle.label() == "circle  "
    assert square.label() == "square  "

    # The base declares the same bindings, and they resolve through the caller's
    # concrete type rather than through anything the abstract type implements.
    assert module.shape_base.area(circle) == pytest.approx(circle.area())
    assert module.shape_base.area(square) == pytest.approx(square.area())


def test_inherited_bindings_and_components_reach_every_extension(module):
    """An implemented binding on the abstract base serves its extensions."""
    circle = module.circle(radius=np.float64(1.0))

    assert circle.side_count() == np.int32(0)
    circle.bump_sides()
    circle.bump_sides()
    assert circle.side_count() == np.int32(2)


def test_private_components_stay_off_the_generated_classes(module):
    """The hierarchy publishes only what its `private` statements allow."""
    assert {name for name in dir(module.shape_base) if not name.startswith("_")} == {
        "area",
        "label",
        "side_count",
        "bump_sides",
    }
    assert {name for name in dir(module.circle) if not name.startswith("_")} == {
        "area",
        "label",
        "side_count",
        "bump_sides",
        "radius",
    }


def test_interoperable_type_keeps_its_layout_beside_the_hierarchy(module):
    """A `bind(c)` type in the same module still wraps through its own accessors."""
    box = module.extent(width=np.float64(3.0), height=np.float64(4.0))

    assert box.width == np.float64(3.0)
    assert module.describe(box) == pytest.approx(12.0)

    box.width = np.float64(5.0)
    assert module.describe(box) == pytest.approx(20.0)


def test_build_writes_its_semantic_contract_beside_the_extension(tmp_path: Path):
    """Every build leaves the contract describing the API it just generated."""
    from prik.pipeline.build import BUILD_CONTRACT_DIRECTORY_NAME, build_fortran_extension
    from prik.preprocessing import PreprocessingConfig
    from tests.fortran._support.wrapper_build import _compiler

    result = build_fortran_extension(
        SOURCE,
        output_dir=tmp_path,
        preprocessing=PreprocessingConfig(mode="compiler", compiler=_compiler()),
    )

    contracts = result.output_dir / BUILD_CONTRACT_DIRECTORY_NAME
    assert (contracts / "abstract_hierarchy.pyi").is_file()
    assert (contracts / "__init__.pyi").read_text(encoding="utf-8").strip() == ("from . import abstract_hierarchy")

    text = (contracts / "abstract_hierarchy.pyi").read_text(encoding="utf-8")
    assert "@abstract" in text
    assert "@abstractmethod" in text
