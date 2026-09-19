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

SHAPES_SOURCE = """\
module shapes
  implicit none
  type :: box
    integer :: value = 0
  end type box
  type, extends(box) :: tagged_box
    integer :: tag = 0
  end type tagged_box
end module shapes
"""

OPS_SOURCE = """\
module ops
  use shapes, only: box, tagged_box
  implicit none
  private
  public :: holder, boxed, total, visit, describe, weigh, maybe_box, producer, consumer
  type :: holder
    type(box) :: inner
  end type holder
  abstract interface
    function producer() result(out)
      import :: box
      type(box) :: out
    end function producer
    subroutine consumer(item)
      import :: box
      type(box), intent(in) :: item
    end subroutine consumer
  end interface
  interface weigh
    module procedure weigh_box, weigh_int
  end interface weigh
contains
  function boxed(v) result(out)
    integer, intent(in) :: v
    type(box) :: out
    out%value = v
  end function boxed

  integer function total(make)
    procedure(producer) :: make
    type(box) :: item
    item = make()
    total = item%value
  end function total

  subroutine visit(fn)
    procedure(consumer) :: fn
    type(box) :: item
    item%value = 41
    call fn(item)
  end subroutine visit

  integer function describe(item)
    class(box), intent(in) :: item
    select type (item)
    type is (tagged_box)
      describe = 2
    class default
      describe = 1
    end select
  end function describe

  integer function weigh_box(item)
    type(box), intent(in) :: item
    weigh_box = item%value
  end function weigh_box

  integer function weigh_int(n)
    integer, intent(in) :: n
    weigh_int = -n
  end function weigh_int

  function maybe_box(v) result(out)
    integer, intent(in) :: v
    type(box), allocatable :: out
    allocate(out)
    out%value = v
  end function maybe_box
end module ops
"""

FIRST_SOURCE = """\
module first_mod
  implicit none
  type :: box
    integer :: value = 1
  end type box
contains
  function make_first() result(out)
    type(box) :: out
    out%value = 10
  end function make_first
end module first_mod
"""

SECOND_SOURCE = """\
module second_mod
  implicit none
  type :: box
    real(8) :: weight = 2.0d0
  end type box
  abstract interface
    function producer() result(out)
      import :: box
      type(box) :: out
    end function producer
  end interface
contains
  real(8) function weigh(make) result(total)
    procedure(producer) :: make
    type(box) :: item
    item = make()
    total = item%weight
  end function weigh
end module second_mod
"""


BASE_SOURCE = """\
module zeta_base
  implicit none
  type :: shape
    integer :: sides = 0
  end type shape
contains
  integer function sides_of(item)
    class(shape), intent(in) :: item
    sides_of = item%sides
  end function sides_of
end module zeta_base
"""

EXTENSION_SOURCE = """\
module alpha_child
  use zeta_base, only: shape
  implicit none
  type, extends(shape) :: square
    integer :: edge = 1
  end type square
contains
  function make_square(edge) result(out)
    integer, intent(in) :: edge
    type(square) :: out
    out%sides = 4
    out%edge = edge
  end function make_square
end module alpha_child
"""


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
