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

module facade_mod
  use ints_mod,  only : convert
  use reals_mod, only : convert
  implicit none
  interface convert
    module procedure convert_l
  end interface

contains
  logical function convert_l(x)
    logical, intent(in) :: x
    convert_l = x
  end function convert_l
end module facade_mod
