module ints_mod
  implicit none
  private
  public :: convert
  interface convert
    module procedure convert_int
  end interface convert
contains
  integer function convert_int(i)
    integer, intent(in) :: i
    convert_int = i + 1
  end function convert_int
end module ints_mod

module reals_mod
  implicit none
  private
  public :: convert
  interface convert
    module procedure convert_real
  end interface convert
contains
  real(8) function convert_real(x)
    real(8), intent(in) :: x
    convert_real = x * 2
  end function convert_real
end module reals_mod

module facade_mod
  use ints_mod, only : convert
  use reals_mod, only : convert
end module facade_mod
