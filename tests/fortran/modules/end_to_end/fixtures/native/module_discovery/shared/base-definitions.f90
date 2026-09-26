module base_types
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  type :: handle_t
    integer(c_int) :: val = 0
  end type handle_t
end module base_types
