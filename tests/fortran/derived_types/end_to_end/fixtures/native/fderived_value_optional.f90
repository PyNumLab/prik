module derived_value_arguments
  use iso_c_binding
  implicit none

  type, bind(c) :: point
    real(c_double) :: x
    real(c_double) :: y
  end type point
contains
  function make_point(x, y) result(value)
    real(c_double), intent(in) :: x
    real(c_double), intent(in) :: y
    type(point) :: value
    value%x = x
    value%y = y
  end function make_point

  function score_by_value(value) result(total)
    type(point), value :: value
    real(c_double) :: total
    value%x = value%x + 100.0_c_double
    total = value%x + value%y
  end function score_by_value

  function optional_sum(value) result(total)
    type(point), optional, intent(in) :: value
    real(c_double) :: total
    if (present(value)) then
      total = value%x + value%y
    else
      total = -1.0_c_double
    end if
  end function optional_sum

  subroutine update_point(value)
    type(point), intent(inout) :: value
    value%x = value%x + 10.0_c_double
    value%y = value%y + 20.0_c_double
  end subroutine update_point

  subroutine fill_point(value)
    type(point), intent(out) :: value
    value%x = 31.0_c_double
    value%y = 32.0_c_double
  end subroutine fill_point
end module derived_value_arguments
