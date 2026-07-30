module documented_subroutines
  implicit none
  type :: point
    real(8) :: x
  end type point
contains
  subroutine bounds(values, smallest, largest)
    real(8), intent(in) :: values(:)
    real(8), intent(out) :: smallest, largest
    smallest = minval(values)
    largest = maxval(values)
  end subroutine bounds

  subroutine scale_in_place(values, factor)
    real(8), intent(inout) :: values(:)
    real(8), intent(in) :: factor
    values = factor * values
  end subroutine scale_in_place

  subroutine scale_scalar(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
    value = factor * value
  end subroutine scale_scalar

  subroutine fill(values)
    real(8), intent(out) :: values(:)
    values = 1.0_8
  end subroutine fill

  subroutine no_intent_scalar(value)
    real(8) :: value
    value = value + 1.0_8
  end subroutine no_intent_scalar

  subroutine fill_point(value)
    type(point), intent(out) :: value
    value%x = 9.5_8
  end subroutine fill_point

  subroutine make_values(count, values)
    integer(4), intent(in) :: count
    real(8), allocatable, intent(out) :: values(:)
    integer(4) :: index
    allocate(values(count))
    values = [(real(index, kind=8), index = 1, count)]
  end subroutine make_values
end module documented_subroutines
