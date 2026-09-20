module ints_mod
  implicit none
  interface convert
    module procedure to_value
  end interface
contains
  integer function to_value(x)
    integer, intent(in) :: x
    to_value = x
  end function to_value
end module ints_mod

module reals_mod
  implicit none
  interface convert
    module procedure to_value
  end interface
contains
  real function to_value(x)
    real, intent(in) :: x
    to_value = x
  end function to_value
end module reals_mod

module facade_mod
  use ints_mod,  only : convert
  use reals_mod, only : convert
  implicit none
  interface convert
    module procedure to_value_l
  end interface
contains
  logical function to_value_l(x)
    logical, intent(in) :: x
    to_value_l = x
  end function to_value_l
end module facade_mod
