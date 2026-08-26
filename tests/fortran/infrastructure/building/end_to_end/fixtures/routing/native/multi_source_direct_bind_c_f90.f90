module multi_source_direct_bind_c_f90
  use iso_c_binding
  use multi_source_direct_helper_f90, only: helper_double
contains
  integer(c_int) function direct_combined(value) bind(C) result(output)
    integer(c_int), value, intent(in) :: value

    output = helper_double(value) + 1_c_int
  end function direct_combined
end module multi_source_direct_bind_c_f90
