module fcharacter_owner_pointer
  use iso_c_binding, only: c_char
  implicit none
  character(kind=c_char, len=4), target, save :: fixed_target(3) = &
    [character(kind=c_char, len=4) :: 'one ', 'two ', 'tri ']
  character(kind=c_char, len=:), pointer, save :: deferred_target(:)
contains
  subroutine repoint_fixed(values)
    character(kind=c_char, len=4), pointer, intent(out) :: values(:)
    values => fixed_target
  end subroutine repoint_fixed

  integer(4) function fixed_state(values) result(state)
    character(kind=c_char, len=4), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) state = size(values) * 100 + len(values)
  end function fixed_state

  integer(4) function ordinary_width(values) result(width)
    character(kind=c_char, len=*), intent(in) :: values(:)
    width = 0
    if (size(values) > 0) width = len(values)
  end function ordinary_width

  subroutine repoint_deferred(values)
    character(kind=c_char, len=:), pointer, intent(out) :: values(:)
    if (.not. associated(deferred_target)) then
      allocate(character(kind=c_char, len=6) :: deferred_target(2))
      deferred_target = [character(kind=c_char, len=6) :: 'alpha ', 'beta  ']
    end if
    values => deferred_target
  end subroutine repoint_deferred

  integer(4) function deferred_state(values) result(state)
    character(kind=c_char, len=:), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) then
      state = size(values) * 100 + len(values) + iachar(values(1)(1:1))
    end if
  end function deferred_state
end module fcharacter_owner_pointer
