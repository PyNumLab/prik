module allocatables_mixed_bind_c_f90
  use iso_c_binding
  implicit none
contains
  subroutine direct_allocate(values) bind(C)
    real(c_double), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [1.0_c_double, 2.0_c_double, 3.0_c_double]
  end subroutine direct_allocate

  real(c_double) function adapted_sum(values) result(total)
    real(c_double), allocatable, intent(in) :: values(:)

    total = merge(sum(values), -1.0_c_double, allocated(values))
  end function adapted_sum
end module allocatables_mixed_bind_c_f90
