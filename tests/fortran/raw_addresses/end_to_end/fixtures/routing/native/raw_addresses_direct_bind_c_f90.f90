module raw_addresses_direct_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function pointer_state(address) bind(C) result(state)
    type(c_ptr), value, intent(in) :: address

    state = merge(1_c_int, 0_c_int, c_associated(address))
  end function pointer_state

  subroutine increment_pointer(address) bind(C)
    type(c_ptr), value, intent(in) :: address
    real(c_double), pointer :: value

    call c_f_pointer(address, value)
    value = value + 1.0_c_double
  end subroutine increment_pointer
end module raw_addresses_direct_bind_c_f90
