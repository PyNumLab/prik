module error_handling_mixed_bind_c_f90
  use iso_c_binding
contains
  subroutine direct_solve(value, output, status) bind(C)
    integer(c_int), value, intent(in) :: value
    integer(c_int), intent(out) :: output
    integer(c_int), intent(out) :: status

    output = 2_c_int * max(value, 0_c_int)
    status = merge(5_c_int, 0_c_int, value < 0_c_int)
  end subroutine direct_solve

  subroutine adapted_solve(value, output, status)
    integer(c_int), intent(in) :: value
    integer(c_int), intent(out) :: output
    integer(c_int), intent(out) :: status

    output = 3_c_int * max(value, 0_c_int)
    status = merge(6_c_int, 0_c_int, value < 0_c_int)
  end subroutine adapted_solve
end module error_handling_mixed_bind_c_f90
