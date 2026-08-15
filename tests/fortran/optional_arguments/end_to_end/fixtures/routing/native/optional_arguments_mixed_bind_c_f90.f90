module optional_arguments_mixed_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function direct_optional_state(value) bind(C) result(state)
    real(c_double), optional, intent(in) :: value

    if (present(value)) then
      state = 1_c_int
    else
      state = 0_c_int
    end if
  end function direct_optional_state

  integer(c_int) function adapted_optional_value_state(value) result(state)
    real(c_double), value, optional, intent(in) :: value

    if (present(value)) then
      state = 2_c_int
    else
      state = 0_c_int
    end if
  end function adapted_optional_value_state
end module optional_arguments_mixed_bind_c_f90
