module ints_mod
  implicit none
  interface convert
    module procedure convert_i
  end interface
contains
  integer function convert_i(x)
    integer, intent(in) :: x
    convert_i = x
  end function convert_i
end module ints_mod

module reals_mod
  implicit none
  interface convert
    module procedure convert_r
  end interface
contains
  real function convert_r(x)
    real, intent(in) :: x
    convert_r = x
  end function convert_r
end module reals_mod
