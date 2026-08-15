module modules_direct_bind_c_f90
  use iso_c_binding
  implicit none

  integer(c_int), parameter :: limit = 12_c_int
  integer(c_int) :: counter = 3_c_int
contains
  integer(c_int) function direct_total(value) bind(C) result(total)
    integer(c_int), value, intent(in) :: value

    total = counter + value
  end function direct_total

  subroutine direct_set_counter(value) bind(C)
    integer(c_int), value, intent(in) :: value

    counter = value
  end subroutine direct_set_counter
end module modules_direct_bind_c_f90
