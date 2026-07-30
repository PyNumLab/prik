
module fscalar_kinds_f90
  use iso_fortran_env, only: int8, int16, int32, int64, real32, real64
  use iso_c_binding, only: c_bool, c_int32_t, c_float, c_double, c_float_complex, c_double_complex
  implicit none
contains
  integer(int8) function id_i8(value) result(out)
    integer(int8), intent(in) :: value

    out = value
  end function id_i8

  integer(int16) function id_i16(value) result(out)
    integer(int16), intent(in) :: value

    out = value
  end function id_i16

  integer(int32) function id_i32(value) result(out)
    integer(int32), intent(in) :: value

    out = value
  end function id_i32

  integer(int32) function id_i32_value(value) result(out)
    integer(int32), intent(in), value :: value

    out = value
  end function id_i32_value

  integer(int64) function id_i64(value) result(out)
    integer(int64), intent(in) :: value

    out = value
  end function id_i64

  subroutine copy_i16(n, values, out)
    integer, intent(in) :: n
    integer(int16), intent(in) :: values(n)
    integer(int16), intent(out) :: out(n)

    out = values
  end subroutine copy_i16

  logical(c_bool) function not_flag(value) result(out)
    logical(c_bool), intent(in) :: value

    out = .not. value
  end function not_flag

  subroutine invert_flags(n, values, out)
    integer, intent(in) :: n
    logical(c_bool), intent(in) :: values(n)
    logical(c_bool), intent(out) :: out(n)

    out = .not. values
  end subroutine invert_flags

  real(real32) function id_r32(value) result(out)
    real(real32), intent(in) :: value

    out = value
  end function id_r32

  real(real64) function id_r64(value) result(out)
    real(real64), intent(in) :: value

    out = value
  end function id_r64

  subroutine copy_r64(n, values, out)
    integer, intent(in) :: n
    real(real64), intent(in) :: values(n)
    real(real64), intent(out) :: out(n)

    out = values
  end subroutine copy_r64

  complex(real32) function conj_c64(value) result(out)
    complex(real32), intent(in) :: value

    out = conjg(value)
  end function conj_c64

  complex(real64) function shift_c128(value) result(out)
    complex(real64), intent(in) :: value

    out = value + cmplx(1.0_real64, -2.0_real64, kind=real64)
  end function shift_c128

  subroutine copy_c128(n, values, out)
    integer, intent(in) :: n
    complex(real64), intent(in) :: values(n)
    complex(real64), intent(out) :: out(n)

    out = values
  end subroutine copy_c128

  integer(c_int32_t) function id_c_i32(value) result(out)
    integer(c_int32_t), intent(in) :: value

    out = value
  end function id_c_i32

  real(c_float) function id_c_float(value) result(out)
    real(c_float), intent(in) :: value

    out = value
  end function id_c_float

  real(c_double) function id_c_double(value) result(out)
    real(c_double), intent(in) :: value

    out = value
  end function id_c_double

  complex(c_float_complex) function conj_c_float_complex(value) result(out)
    complex(c_float_complex), intent(in) :: value

    out = conjg(value)
  end function conj_c_float_complex

  complex(c_double_complex) function conj_c_double_complex(value) result(out)
    complex(c_double_complex), intent(in) :: value

    out = conjg(value)
  end function conj_c_double_complex
end module fscalar_kinds_f90
