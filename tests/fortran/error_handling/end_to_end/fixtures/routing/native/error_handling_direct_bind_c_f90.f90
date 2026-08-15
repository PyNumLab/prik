module error_handling_direct_bind_c_f90
  use iso_c_binding
contains
  subroutine direct_solve(value, output, status) bind(C)
    integer(c_int), value, intent(in) :: value
    integer(c_int), intent(out) :: output
    integer(c_int), intent(out) :: status

    if (value < 0_c_int) then
      output = 0_c_int
      status = 5_c_int
    else
      output = 2_c_int * value
      status = 0_c_int
    end if
  end subroutine direct_solve
end module error_handling_direct_bind_c_f90
