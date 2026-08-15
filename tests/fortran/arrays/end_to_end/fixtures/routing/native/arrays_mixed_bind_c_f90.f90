module arrays_mixed_bind_c_f90
  use iso_c_binding
contains
  real(c_double) function direct_sum(n, values) bind(C) result(output)
    integer(c_int), value, intent(in) :: n
    real(c_double), intent(in) :: values(n)
    output = sum(values)
  end function direct_sum

  real(8) function adapted_sum(n, values) result(output)
    integer, intent(in) :: n
    real(8), intent(in) :: values(n)
    output = sum(values)
  end function adapted_sum
end module arrays_mixed_bind_c_f90
