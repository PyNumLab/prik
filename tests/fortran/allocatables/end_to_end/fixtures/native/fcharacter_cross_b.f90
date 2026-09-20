module fcharacter_cross_b
  use iso_c_binding, only: c_char
  character(kind=c_char, len=4), target, save :: pointer_target(2) = &
    [character(kind=c_char, len=4) :: 'red ', 'blue']
contains
  subroutine select_b(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [character(kind=c_char, len=4) :: 'red ', 'blue', 'sky ']
  end subroutine select_b

  integer(4) function state_b(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function state_b

  subroutine select_pointer_b(values)
    character(kind=c_char, len=4), pointer, intent(out) :: values(:)
    values => pointer_target
  end subroutine select_pointer_b

  integer(4) function pointer_state_b(values) result(state)
    character(kind=c_char, len=4), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) state = size(values) * 100 + len(values)
  end function pointer_state_b
end module fcharacter_cross_b
