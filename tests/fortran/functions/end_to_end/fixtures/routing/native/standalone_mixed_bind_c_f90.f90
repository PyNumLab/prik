integer(c_int) function standalone_direct(value) bind(C, name="standalone_mixed_direct") result(output)
  use iso_c_binding
  integer(c_int), value, intent(in) :: value

  output = value + 2_c_int
end function standalone_direct

integer(c_int) function standalone_adapted(value) result(output)
  use iso_c_binding
  integer(c_int), intent(in) :: value

  output = value + 3_c_int
end function standalone_adapted
