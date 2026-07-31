module scalar_optional_descriptors
  implicit none
contains
  integer(4) function alloc_state(value) result(state)
    real(8), allocatable, optional, intent(in) :: value

    if (.not. present(value)) then
      state = 0
    else if (.not. allocated(value)) then
      state = 1
    else if (abs(value - 2.5_8) < 1.0e-12_8) then
      state = 2
    else
      state = -1
    end if
  end function alloc_state

  integer(4) function pointer_state(value) result(state)
    real(8), pointer, optional, intent(in) :: value

    if (.not. present(value)) then
      state = 0
    else if (.not. associated(value)) then
      state = 1
    else if (abs(value - 2.5_8) < 1.0e-12_8) then
      state = 2
    else
      state = -1
    end if
  end function pointer_state
end module scalar_optional_descriptors
