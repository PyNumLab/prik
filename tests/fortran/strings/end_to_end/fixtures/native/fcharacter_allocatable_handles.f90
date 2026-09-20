module fcharacter_owner_allocatable
  use iso_c_binding, only: c_char
  implicit none
contains
  integer(4) function inspect(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function inspect

  subroutine replace(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [character(kind=c_char, len=4) :: 'red ', 'blue', 'sky ']
  end subroutine replace

  subroutine fill(values)
    character(kind=c_char, len=4), allocatable, intent(out) :: values(:)
    allocate(values(2))
    values = [character(kind=c_char, len=4) :: 'left', 'rght']
  end subroutine fill

  subroutine optional_fill(values, was_allocated)
    character(kind=c_char, len=4), allocatable, intent(out), optional :: values(:)
    integer(4), intent(out) :: was_allocated
    was_allocated = -1
    if (present(values)) then
      was_allocated = merge(1, 0, allocated(values))
      allocate(values(2))
      values = [character(kind=c_char, len=4) :: 'new1', 'new2']
    end if
  end subroutine optional_fill

  integer(4) function optional_state(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in), optional :: values(:)
    state = -1
    if (present(values)) then
      state = 0
      if (allocated(values)) state = size(values) * 100 + len(values)
    end if
  end function optional_state

  integer(4) function mixed(first, plain, second, scale) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: first(:)
    character(kind=c_char, len=4), intent(in) :: plain(:)
    character(kind=c_char, len=4), allocatable, intent(in) :: second(:)
    integer(4), intent(in) :: scale
    state = scale + size(plain) * 10
    if (allocated(first)) state = state + size(first) * 100
    if (allocated(second)) state = state + size(second) * 1000
  end function mixed

  integer(4) function inspect_rank2(values) result(state)
    character(kind=c_char, len=3), allocatable, intent(in) :: values(:, :)
    state = 0
    if (allocated(values)) state = size(values, 1) * 1000 + size(values, 2) * 100 + len(values)
  end function inspect_rank2

  subroutine fill_rank2(values)
    character(kind=c_char, len=3), allocatable, intent(inout) :: values(:, :)
    if (allocated(values)) deallocate(values)
    allocate(values(2, 4))
    values = 'abc'
  end subroutine fill_rank2

end module fcharacter_owner_allocatable
