module allocatables_direct_bind_c_f90
  use iso_c_binding
  implicit none

contains
  integer(c_int) function direct_optional_state(values) bind(C) result(state)
    real(c_double), allocatable, optional, intent(in) :: values(:)

    if (.not. present(values)) then
      state = 0_c_int
    else if (.not. allocated(values)) then
      state = 1_c_int
    else
      state = 2_c_int
    end if
  end function direct_optional_state

  subroutine direct_allocate(values) bind(C)
    real(c_double), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [1.0_c_double, 2.0_c_double, 3.0_c_double]
  end subroutine direct_allocate

  real(c_double) function direct_pointer_sum(values) bind(C) result(total)
    real(c_double), pointer, intent(in) :: values(:)

    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_c_double
    end if
  end function direct_pointer_sum
end module allocatables_direct_bind_c_f90
