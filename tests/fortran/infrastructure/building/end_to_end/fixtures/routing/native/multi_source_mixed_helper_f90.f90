module multi_source_mixed_helper_f90
  use iso_c_binding
contains
  integer(c_int) function helper_double(value) bind(C) result(output)
    integer(c_int), value, intent(in) :: value

    output = 2_c_int * value
  end function helper_double
end module multi_source_mixed_helper_f90
