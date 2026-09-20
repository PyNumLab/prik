module fallocatable_empty_actual_f90
  implicit none

contains

  subroutine fill_empty(values)
    real(8), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(0))
  end subroutine fill_empty

  subroutine fill_three(values)
    real(8), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [1.0_8, 2.0_8, 3.0_8]
  end subroutine fill_three

  ! An ordinary explicit-shape dummy: it receives an address and an extent.
  function total(values, n) result(sum_values)
    integer, intent(in) :: n
    real(8), intent(in) :: values(n)
    real(8) :: sum_values

    sum_values = sum(values)
  end function total

end module fallocatable_empty_actual_f90
