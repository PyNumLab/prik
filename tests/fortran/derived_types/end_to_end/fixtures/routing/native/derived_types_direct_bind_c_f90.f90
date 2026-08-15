module derived_types_direct_bind_c_f90
  use iso_c_binding
  implicit none

  type, bind(C) :: point
    real(c_double) :: x
    real(c_double) :: y
  end type point
contains
  real(c_double) function direct_sum(value) bind(C) result(total)
    type(point), intent(in) :: value

    total = value%x + value%y
  end function direct_sum

  subroutine direct_shift(value, delta) bind(C)
    type(point), intent(inout) :: value
    real(c_double), value, intent(in) :: delta

    value%x = value%x + delta
    value%y = value%y + delta
  end subroutine direct_shift
end module derived_types_direct_bind_c_f90
