"""A type is one type wherever a procedure of another module takes or returns it.

Each module becomes its own namespace, and a type's class and the helpers
wrapping it are defined in the namespace of the module declaring it. A
procedure using the type from another module reaches them there, and two
modules may each declare a type spelled alike without either replacing the
other.
"""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_sources_and_import

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SHAPES_SOURCE = (NATIVE_FIXTURES / "cross_module_shapes.f90").read_text(encoding="utf-8")

OPS_SOURCE = (NATIVE_FIXTURES / "cross_module_ops.f90").read_text(encoding="utf-8")

FIRST_SOURCE = (NATIVE_FIXTURES / "cross_module_first.f90").read_text(encoding="utf-8")

SECOND_SOURCE = (NATIVE_FIXTURES / "cross_module_second.f90").read_text(encoding="utf-8")


BASE_SOURCE = (NATIVE_FIXTURES / "cross_module_base.f90").read_text(encoding="utf-8")

EXTENSION_SOURCE = (NATIVE_FIXTURES / "cross_module_extension.f90").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def modules(tmp_path_factory: pytest.TempPathFactory):
    """Build `shapes` and the `ops` module using its types once."""
    module, _ = _build_sources_and_import(
        [("shapes.f90", SHAPES_SOURCE), ("ops.f90", OPS_SOURCE)],
        tmp_path_factory.mktemp("across"),
    )
    return module.shapes, module.ops


def test_a_returned_type_is_the_declaring_module_class(modules):
    shapes, ops = modules

    item = ops.boxed(np.int32(3))

    assert type(item) is shapes.Box
    assert item.value == 3


def test_an_allocatable_result_is_the_declaring_module_class(modules):
    shapes, ops = modules

    item = ops.maybe_box(np.int32(4))

    assert type(item) is shapes.Box
    assert item.value == 4


def test_a_callback_result_is_checked_against_the_declaring_module_class(modules):
    shapes, ops = modules

    assert ops.total(lambda: shapes.Box(value=np.int32(9))) == 9


def test_a_callback_argument_is_the_declaring_module_class(modules):
    shapes, ops = modules
    seen = []

    ops.visit(lambda item: seen.append((type(item), int(item.value))))

    assert seen == [(shapes.Box, 41)]


def test_a_polymorphic_argument_accepts_each_declaring_module_class(modules):
    shapes, ops = modules

    assert ops.describe(shapes.Box()) == 1
    assert ops.describe(shapes.Tagged_Box()) == 2
    # A rejection names each accepted class the way its contract declares it.
    with pytest.raises(TypeError, match=r"wrapper type: Tagged_Box, Box$"):
        ops.describe(ops.Holder())


def test_documentation_names_another_module_type_as_it_is_published(modules):
    """The build is named after its first source, `shapes`, like that module.

    Completing the merged build counted `ops`'s use of `box` as an import even
    though the build declares `box`, so the class took `Box_2` and every
    docstring naming it disagreed with the published `Box`.
    """
    shapes, ops = modules

    assert ops.boxed.__doc__.splitlines()[0] == "boxed(v) -> Box"
    assert shapes.Box.__doc__.splitlines()[0] == "Box"


def test_a_generic_dispatches_on_the_declaring_module_class(modules):
    shapes, ops = modules

    assert ops.weigh(shapes.Box(value=np.int32(5))) == 5
    assert ops.weigh(np.int32(5)) == -5


def test_a_component_of_another_module_type_is_that_module_class(modules):
    shapes, ops = modules
    holder = ops.Holder()

    assert type(holder.inner) is shapes.Box
    holder.inner = shapes.Box(value=np.int32(12))
    assert holder.inner.value == 12


def test_two_modules_may_each_declare_a_type_spelled_alike(tmp_path: Path):
    """Each `box` keeps its own class, constructor, and helpers.

    Keying them by the native spelling alone gave both types one constructor
    symbol, and the build stopped there.
    """
    module, _ = _build_sources_and_import(
        [("first.f90", FIRST_SOURCE), ("second.f90", SECOND_SOURCE)],
        tmp_path,
    )
    first, second = module.first_mod, module.second_mod

    assert first.Box is not second.Box
    made = first.make_first()
    assert type(made) is first.Box
    assert made.value == 10
    assert second.weigh(lambda: second.Box(weight=np.float64(3.5))) == 3.5


def test_a_type_may_extend_one_another_module_declares(tmp_path: Path):
    """The extension is a subclass of the base where the base is defined.

    `alpha_child` sorts before `zeta_base`, so its namespace is set up after
    the base's only because inheritance orders them. Its class names the base
    there instead of looking for it among its own.
    """
    module, _ = _build_sources_and_import(
        [("zeta_base.f90", BASE_SOURCE), ("alpha_child.f90", EXTENSION_SOURCE)],
        tmp_path,
    )
    base, child = module.zeta_base, module.alpha_child

    square = child.make_square(np.int32(3))

    assert type(square) is child.Square
    assert issubclass(child.Square, base.Shape)
    assert (square.sides, square.edge) == (4, 3)
    assert base.sides_of(square) == 4
    assert base.sides_of(base.Shape(sides=np.int32(2))) == 2
