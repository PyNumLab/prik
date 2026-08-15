integer(c_int) function standalone_direct(value) bind(C, name="standalone_direct_symbol") result(output)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value

  output = value + 2_c_int
end function standalone_direct

subroutine standalone_output(value, output) bind(C)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value
  integer(c_int), intent(out) :: output

  output = 3_c_int * value
end subroutine standalone_output
