
module fbind_c_derived_layout_f90
  use iso_c_binding
  implicit none
  private
  public :: point, tagged_point, populate, score_by_value

  type, bind(C) :: point
    real(c_double) :: x
    integer(c_int) :: axis
  end type point

  type, bind(C) :: tagged_point
    type(point) :: position
    complex(c_double_complex) :: weight
  end type tagged_point

contains
  subroutine populate(value, x, axis, weight) bind(C)
    type(tagged_point), intent(inout) :: value
    real(c_double), value, intent(in) :: x
    integer(c_int), value, intent(in) :: axis
    complex(c_double_complex), value, intent(in) :: weight

    value%position%x = x
    value%position%axis = axis
    value%weight = weight
  end subroutine populate

  real(c_double) function score_by_value(value) result(score) bind(C)
    type(tagged_point), value :: value

    value%position%x = value%position%x + 100.0_c_double
    score = value%position%x + real(value%position%axis, c_double) + real(value%weight, c_double)
  end function score_by_value
end module fbind_c_derived_layout_f90
