module derived_types_mixed_bind_c_f90
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

  real(c_double) function adapted_sum_by_value(value) bind(C) result(total)
    type(point), value, intent(in) :: value

    total = value%x + value%y
  end function adapted_sum_by_value
end module derived_types_mixed_bind_c_f90
