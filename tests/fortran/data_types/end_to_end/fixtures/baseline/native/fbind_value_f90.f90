
module fbind_value_f90
  use iso_c_binding
contains
  integer(c_int) function plus_value(n) bind(C, name="x2py_plus_value") result(res)
    integer(c_int), value, intent(in) :: n

    res = n + 7_c_int
  end function plus_value

  integer(c_int) function double_value(n) bind(C) result(res)
    integer(c_int), value, intent(in) :: n

    res = n * 2_c_int
  end function double_value

  integer(c_int) function plus_reference(n) bind(C) result(res)
    integer(c_int), intent(in) :: n

    res = n + 11_c_int
  end function plus_reference

  real(c_double) function scale_real(x) bind(C, name="x2py_scale_real") result(res)
    real(c_double), value, intent(in) :: x

    res = 2.5_c_double * x
  end function scale_real

  complex(c_double_complex) function conjugate_value(z) bind(C, name="x2py_conjugate_value") result(res)
    complex(c_double_complex), value, intent(in) :: z

    res = conjg(z)
  end function conjugate_value

  logical(c_bool) function invert_flag(flag) bind(C, name="x2py_invert_flag") result(res)
    logical(c_bool), value, intent(in) :: flag

    res = .not. flag
  end function invert_flag

  integer(c_int) function char_code(ch) bind(C) result(res)
    character(kind=c_char), value, intent(in) :: ch

    res = iachar(ch, c_int)
  end function char_code
end module fbind_value_f90
