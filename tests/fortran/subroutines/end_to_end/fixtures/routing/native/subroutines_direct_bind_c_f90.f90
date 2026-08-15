module subroutines_direct_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function direct_reference(value) bind(C) result(output)
    integer(c_int), intent(in) :: value

    output = value + 10_c_int
  end function direct_reference

  subroutine direct_outputs(value, doubled, status) bind(C)
    integer(c_int), intent(inout) :: value
    integer(c_int), intent(out) :: doubled
    integer(c_int), intent(out) :: status

    doubled = 2_c_int * value
    value = value + 1_c_int
    status = 7_c_int
  end subroutine direct_outputs
end module subroutines_direct_bind_c_f90
