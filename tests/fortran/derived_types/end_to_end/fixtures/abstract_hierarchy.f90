module abstract_hierarchy
  use, intrinsic :: iso_c_binding
  implicit none
  private

  public :: shape_base, circle, square, extent, describe

  !> Abstract base: no instance of this type can exist, but it publishes a
  !> deferred contract and one implemented binding its extensions inherit.
  type, public, abstract :: shape_base
    private
    integer(4) :: sides = 0
  contains
    private
    procedure(area_interface), deferred, public :: area
    procedure(name_interface), deferred, public :: label
    procedure, public, non_overridable :: side_count => shape_side_count
    procedure, public, non_overridable :: bump_sides => shape_bump_sides
  end type shape_base

  abstract interface
    pure real(8) function area_interface(self)
      import :: shape_base
      class(shape_base), intent(in) :: self
    end function area_interface

    pure subroutine name_interface(self, text)
      import :: shape_base
      class(shape_base), intent(in) :: self
      character(len=8), intent(out) :: text
    end subroutine name_interface
  end interface

  type, extends(shape_base), public :: circle
    real(8) :: radius = 1.0d0
  contains
    procedure, public :: area => circle_area
    procedure, public :: label => circle_label
  end type circle

  type, extends(shape_base), public :: square
    real(8) :: side = 1.0d0
  contains
    procedure, public :: area => square_area
    procedure, public :: label => square_label
  end type square

  !> An interoperable type keeps its `bind(c)` layout alongside the hierarchy.
  type, bind(c), public :: extent
    real(c_double) :: width = 0.0_c_double
    real(c_double) :: height = 0.0_c_double
  end type extent

contains

  integer(4) function shape_side_count(self)
    class(shape_base), intent(in) :: self
    shape_side_count = self%sides
  end function shape_side_count

  subroutine shape_bump_sides(self)
    class(shape_base), intent(inout) :: self
    self%sides = self%sides + 1
  end subroutine shape_bump_sides

  pure real(8) function circle_area(self)
    class(circle), intent(in) :: self
    circle_area = 3.14159265358979d0 * self%radius * self%radius
  end function circle_area

  pure subroutine circle_label(self, text)
    class(circle), intent(in) :: self
    character(len=8), intent(out) :: text
    text = "circle  "
  end subroutine circle_label

  pure real(8) function square_area(self)
    class(square), intent(in) :: self
    square_area = self%side * self%side
  end function square_area

  pure subroutine square_label(self, text)
    class(square), intent(in) :: self
    character(len=8), intent(out) :: text
    text = "square  "
  end subroutine square_label

  real(c_double) function describe(box)
    type(extent), intent(in) :: box
    describe = box%width * box%height
  end function describe

end module abstract_hierarchy
