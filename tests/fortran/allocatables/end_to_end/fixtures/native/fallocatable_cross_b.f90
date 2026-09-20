module fallocatable_cross_b
contains
  subroutine select_b(values)
    real(8), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [10.0_8, 20.0_8, 30.0_8]
  end subroutine select_b

  function total_b(values) result(total)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: total
    if (allocated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_b
end module fallocatable_cross_b
