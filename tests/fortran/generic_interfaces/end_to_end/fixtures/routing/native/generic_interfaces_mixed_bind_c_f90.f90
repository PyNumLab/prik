module generic_interfaces_mixed_bind_c_f90
  use iso_c_binding
  implicit none

  interface convert
    module procedure convert_integer
    module procedure convert_real
  end interface convert
contains
  integer(c_int) function convert_integer(value) bind(C, name="mixed_convert_integer") result(output)
    integer(c_int), value, intent(in) :: value

    output = value + 1_c_int
  end function convert_integer

  real(c_double) function convert_real(value) result(output)
    real(c_double), intent(in) :: value

    output = value + 0.5_c_double
  end function convert_real
end module generic_interfaces_mixed_bind_c_f90
