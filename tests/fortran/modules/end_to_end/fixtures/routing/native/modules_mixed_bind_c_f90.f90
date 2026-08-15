module modules_mixed_bind_c_f90
  use iso_c_binding
  implicit none

  integer(c_int) :: counter = 3_c_int
contains
  integer(c_int) function direct_total(value) bind(C) result(total)
    integer(c_int), value, intent(in) :: value

    total = counter + value
  end function direct_total

  integer(c_int) function adapted_total(value) result(total)
    integer(c_int), intent(in) :: value

    total = counter + value
  end function adapted_total
end module modules_mixed_bind_c_f90
