module deferred_owner_matrix
  use iso_c_binding, only: c_char, c_int, c_int64_t, c_loc
  implicit none
  type container
    character(kind=c_char, len=:), allocatable :: values(:, :)
  end type
  type(container) :: parent
  character(kind=c_char, len=:), allocatable :: saved(:, :)
  integer(c_int64_t), private :: last_address = 0
contains
  subroutine setup()
    allocate(character(len=2) :: saved(1, 2), parent%values(2, 1))
    saved = 'ab'
    parent%values = 'cd'
  end subroutine
  subroutine make_matrix(n, values)
    integer(c_int), intent(in) :: n
    character(kind=c_char, len=:), allocatable, target, intent(out) :: values(:, :)
    if (n < 0) return
    allocate(character(len=4) :: values(n, 2))
    values = 'gold'
    last_address = transfer(c_loc(values), last_address)
  end subroutine
  function allocation_address() result(address)
    integer(c_int64_t) :: address
    address = last_address
  end function
  subroutine rewrite(a, b)
    character(kind=c_char, len=:), allocatable, intent(inout) :: a(:, :), b(:, :)
    if (allocated(a)) deallocate(a)
    if (allocated(b)) deallocate(b)
    allocate(character(len=3) :: a(2, 3), b(3, 2))
    a = 'one'
    b = 'two'
  end subroutine
  integer(c_int) function inspect(values) result(state)
    character(kind=c_char, len=:), allocatable, optional, intent(in) :: values(:, :)
    state = -1
    if (.not. present(values)) return
    state = 0
    if (allocated(values)) state = 100 * size(values, 1) + 10 * size(values, 2) + len(values)
  end function
  subroutine stamp(values) bind(c)
    character(kind=c_char, len=:), allocatable, intent(inout) :: values(:, :)
    if (allocated(values)) values(1, 1) = 'yes'
  end subroutine
end module
