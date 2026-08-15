module subroutines_mixed_bind_c_f90
  use iso_c_binding
contains
  subroutine direct_outputs(value, doubled) bind(C)
    integer(c_int), intent(inout) :: value
    integer(c_int), intent(out) :: doubled

    doubled = 2_c_int * value
    value = value + 1_c_int
  end subroutine direct_outputs

  subroutine adapted_outputs(value, doubled)
    integer(c_int), intent(inout) :: value
    integer(c_int), intent(out) :: doubled

    doubled = 2_c_int * value
    value = value + 1_c_int
  end subroutine adapted_outputs
end module subroutines_mixed_bind_c_f90
