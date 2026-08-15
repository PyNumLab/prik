module multi_source_mixed_bind_c_f90
  use iso_c_binding
  use multi_source_mixed_helper_f90, only: helper_double
contains
  integer(c_int) function adapted_combined(value) result(output)
    integer(c_int), intent(in) :: value

    output = helper_double(value) + 1_c_int
  end function adapted_combined
end module multi_source_mixed_bind_c_f90
