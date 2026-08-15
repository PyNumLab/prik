module raw_addresses_mixed_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function pointer_state(address) bind(C) result(state)
    type(c_ptr), value, intent(in) :: address

    state = merge(1_c_int, 0_c_int, c_associated(address))
  end function pointer_state

  integer(c_int) function adapted_value(value) result(output)
    integer(c_int), intent(in) :: value

    output = value + 3_c_int
  end function adapted_value
end module raw_addresses_mixed_bind_c_f90
