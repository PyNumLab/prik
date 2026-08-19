module assumed_scalar_intent
  implicit none

  type :: sample
    real(8) :: x = 0.0d0
  end type sample

contains

  real(8) function weighted(count, values, factor)
    integer(4) :: count
    real(8) :: values(:)
    real(8) :: factor
    integer(4) :: index
    weighted = 0.0d0
    do index = 1, count
      weighted = weighted + values(index) * factor
    end do
  end function weighted

  subroutine touch(count, item, values)
    integer(4) :: count
    type(sample) :: item
    real(8) :: values(:)
    count = count + 1
    item%x = item%x + 1.0d0
    values = values * 2.0d0
  end subroutine touch

  integer(4) function label_width(label)
    character(len=4) :: label
    label_width = len(label)
  end function label_width

  subroutine declared(value)
    real(8), intent(inout) :: value
    value = value + 1.0d0
  end subroutine declared

end module assumed_scalar_intent
