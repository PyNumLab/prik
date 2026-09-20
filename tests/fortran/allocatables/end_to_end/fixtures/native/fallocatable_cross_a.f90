module fallocatable_cross_a
contains
  subroutine select_a(values)
    real(8), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(2))
    values = [1.0_8, 2.0_8]
  end subroutine select_a

  function total_a(values) result(total)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: total
    if (allocated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_a
end module fallocatable_cross_a
