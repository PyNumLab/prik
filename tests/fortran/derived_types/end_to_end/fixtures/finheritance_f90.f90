
module finheritance_f90
  implicit none

  type :: base_shape
    real(8) :: size
  contains
    procedure :: area => base_area
    procedure :: set_size => base_set_size
  end type base_shape

  type, extends(base_shape) :: circle
    real(8) :: radius
  contains
    procedure :: area => circle_area
  end type circle

  type, extends(base_shape) :: box
    real(8) :: width
  contains
    procedure :: area => box_area
  end type box
contains
  real(8) function base_area(self) result(value)
    class(base_shape), intent(in) :: self

    value = self%size
  end function base_area

  subroutine base_set_size(self, value)
    class(base_shape), intent(inout) :: self
    real(8), intent(in) :: value

    self%size = value
  end subroutine base_set_size

  real(8) function circle_area(self) result(value)
    class(circle), intent(in) :: self

    value = self%size + self%radius * self%radius
  end function circle_area

  real(8) function box_area(self) result(value)
    class(box), intent(in) :: self

    value = self%size + 10.0_8 * self%width
  end function box_area

  real(8) function describe_shape(item) result(value)
    class(base_shape), intent(in) :: item

    value = item%area()
  end function describe_shape
end module finheritance_f90
