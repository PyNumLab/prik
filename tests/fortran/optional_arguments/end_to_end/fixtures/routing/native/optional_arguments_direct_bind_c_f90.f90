module optional_arguments_direct_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function optional_state(value) bind(C) result(state)
    real(c_double), optional, intent(in) :: value

    if (present(value)) then
      state = 1_c_int
    else
      state = 0_c_int
    end if
  end function optional_state

  subroutine add_optional(value, total) bind(C)
    real(c_double), optional, intent(in) :: value
    real(c_double), intent(out) :: total

    if (present(value)) then
      total = 4.0_c_double + value
    else
      total = 4.0_c_double
    end if
  end subroutine add_optional
end module optional_arguments_direct_bind_c_f90
