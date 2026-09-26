module owner
  use iso_c_binding
  integer(c_int), bind(C) :: marker = 7
  interface run
    module procedure run_impl
  end interface
contains
  subroutine run_impl(value)
    integer(c_int), intent(out) :: value
    value = marker
  end subroutine
end module
