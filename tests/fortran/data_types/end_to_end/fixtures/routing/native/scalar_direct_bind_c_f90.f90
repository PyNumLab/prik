module scalar_direct_bind_c_f90
  use iso_c_binding
contains
  integer(c_int) function renamed_add(value) bind(C, name="scalar_direct_add") result(output)
    integer(c_int), value, intent(in) :: value

    output = value + 4_c_int
  end function renamed_add

  integer(c_int) function reference_add(value) bind(C) result(output)
    integer(c_int), intent(in) :: value

    output = value + 8_c_int
  end function reference_add

  subroutine scale_output(value, output) bind(C)
    real(c_double), value, intent(in) :: value
    real(c_double), intent(out) :: output

    output = 2.5_c_double * value
  end subroutine scale_output

  logical(c_bool) function invert_flag(value) bind(C) result(output)
    logical(c_bool), value, intent(in) :: value

    output = .not. value
  end function invert_flag

  subroutine optional_state(value, state) bind(C)
    real(c_double), optional, intent(in) :: value
    integer(c_int), intent(out) :: state

    if (present(value)) then
      state = 1_c_int
    else
      state = 0_c_int
    end if
  end subroutine optional_state
end module scalar_direct_bind_c_f90
