module optional_array_descriptors
  implicit none
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
end module optional_array_descriptors
