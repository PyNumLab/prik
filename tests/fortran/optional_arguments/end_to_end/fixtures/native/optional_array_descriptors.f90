module optional_array_descriptors
  implicit none

  real(8), target :: pointer_target(3) = [1.0d0, 2.0d0, 3.0d0]

contains
  integer(4) function alloc_state(values) result(state)
    real(8), allocatable, optional, intent(in) :: values(:)

    if (.not. present(values)) then
      state = 0
    else if (.not. allocated(values)) then
      state = 1
    else
      state = int(sum(values), kind=4)
    end if
  end function alloc_state

  integer(4) function pointer_state(values) result(state)
    real(8), pointer, optional, intent(in) :: values(:)

    if (.not. present(values)) then
      state = 0
    else if (.not. associated(values)) then
      state = 1
    else
      state = int(sum(values), kind=4)
    end if
  end function pointer_state
  subroutine alloc_fill(values)
    real(8), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [1.0d0, 2.0d0, 3.0d0]
  end subroutine alloc_fill

  subroutine pointer_bind(values)
    real(8), pointer, intent(inout) :: values(:)

    values => pointer_target
  end subroutine pointer_bind
end module optional_array_descriptors
