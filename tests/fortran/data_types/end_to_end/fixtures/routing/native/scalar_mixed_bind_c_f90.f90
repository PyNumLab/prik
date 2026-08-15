module scalar_mixed_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function direct_add(value) bind(C, name="scalar_mixed_direct_add") result(output)
    integer(c_int), value, intent(in) :: value

    output = value + 3_c_int
  end function direct_add

  integer function adapted_add(value) result(output)
    integer, intent(in) :: value

    output = value + 7
  end function adapted_add
end module scalar_mixed_bind_c_f90
