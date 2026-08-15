module generic_interfaces_direct_bind_c_f90
  use iso_c_binding
  implicit none

  interface convert
    module procedure convert_integer
    module procedure convert_real
  end interface convert

  interface increment
    module procedure increment_integer
    module procedure increment_real
  end interface increment
contains
  integer(c_int) function convert_integer(value) bind(C, name="direct_convert_integer") result(output)
    integer(c_int), value, intent(in) :: value

    output = value + 1_c_int
  end function convert_integer

  real(c_double) function convert_real(value) bind(C, name="direct_convert_real") result(output)
    real(c_double), value, intent(in) :: value

    output = value + 0.5_c_double
  end function convert_real

  subroutine increment_integer(value) bind(C, name="direct_increment_integer")
    integer(c_int), intent(inout) :: value

    value = value + 1_c_int
  end subroutine increment_integer

  subroutine increment_real(value) bind(C, name="direct_increment_real")
    real(c_double), intent(inout) :: value

    value = value + 0.5_c_double
  end subroutine increment_real
end module generic_interfaces_direct_bind_c_f90
