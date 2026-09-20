module fallocatable_plain_f90
  implicit none
  real(8), allocatable :: values(:)
contains
  subroutine allocate_values(n)
    integer(4), intent(in) :: n
    integer(4) :: i

    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = [(1.0_8 * i, i = 1, n)]
  end subroutine allocate_values

  subroutine scale_values(scale)
    real(8), intent(in) :: scale

    values = scale * values
  end subroutine scale_values

  subroutine deallocate_values()
    if (allocated(values)) deallocate(values)
  end subroutine deallocate_values
end module fallocatable_plain_f90
