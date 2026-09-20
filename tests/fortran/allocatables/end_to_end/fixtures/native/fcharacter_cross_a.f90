module fcharacter_cross_a
  use iso_c_binding, only: c_char
  character(kind=c_char, len=4), target, save :: pointer_target(3) = &
    [character(kind=c_char, len=4) :: 'one ', 'two ', 'tri ']
contains
  subroutine select_a(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(2))
    values = [character(kind=c_char, len=4) :: 'one ', 'two ']
  end subroutine select_a

  integer(4) function state_a(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function state_a

  subroutine select_pointer_a(values)
    character(kind=c_char, len=4), pointer, intent(out) :: values(:)
    values => pointer_target
  end subroutine select_pointer_a

  integer(4) function pointer_state_a(values) result(state)
    character(kind=c_char, len=4), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) state = size(values) * 100 + len(values)
  end function pointer_state_a
end module fcharacter_cross_a
