module assumed_type_derived
  use iso_c_binding
  type :: first
    integer(c_int64_t) :: value = 11
  end type
  type :: second
    integer(c_int64_t) :: value = 22
  end type
  type, bind(C) :: interoperable
    integer(c_int64_t) :: value
  end type
  type :: empty
  end type
  type(first), target :: addressable
  type(first) :: plain
  type(first), target :: pointer_target
  type(first), pointer :: pointer_value => null()
contains
  subroutine reset_pointer()
    pointer_value => pointer_target
  end subroutine
  function make_first() result(x)
    type(first) :: x
  end function
  function make_second() result(x)
    type(second) :: x
  end function
  function make_interoperable() result(x)
    type(interoperable) :: x
    x%value = 33_c_int64_t
  end function
  function make_empty() result(x)
    type(empty) :: x
  end function
  integer(c_int) function scalar(x)
    type(*), intent(in) :: x
    scalar = 1
  end function
  integer(c_int) function any_rank(x)
    type(*), dimension(..), intent(in) :: x
    any_rank = rank(x)
  end function
  integer(c_int) function direct_scalar(x) bind(C)
    type(*), intent(in) :: x
    direct_scalar = 2
  end function
  integer(c_int) function direct_any_rank(x) bind(C)
    type(*), dimension(..), intent(in) :: x
    direct_any_rank = rank(x)
  end function
  integer(c_int) function two_origins(x, y) bind(C)
    type(*), intent(in) :: x
    type(*), intent(in) :: y
    two_origins = 3
  end function
  integer(c_int) function optional_scalar(x) bind(C)
    type(*), optional, intent(in) :: x
    optional_scalar = 0
    if (present(x)) optional_scalar = 1
  end function
  integer(c_int) function optional_rank(x) bind(C)
    type(*), dimension(..), optional, intent(in) :: x
    optional_rank = 0
    if (present(x)) optional_rank = 1
  end function
end module
