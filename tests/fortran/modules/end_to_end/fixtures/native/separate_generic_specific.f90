module operations
  implicit none
  private
  public :: convert

  interface
    module function convert_i(x) result(y)
      integer, intent(in) :: x
      integer :: y
    end function convert_i
    module function convert_r(x) result(y)
      real(8), intent(in) :: x
      real(8) :: y
    end function convert_r
  end interface

  interface convert
    module procedure convert_i, convert_r
  end interface convert
end module operations

submodule (operations) operations_impl
  implicit none
contains
  module procedure convert_i
    y = x + 1
  end procedure convert_i

  module procedure convert_r
    y = 2 * x
  end procedure convert_r
end submodule operations_impl

module facade
  use operations, only : convert
  implicit none
  interface convert
    module procedure convert_k
  end interface convert
contains
  integer(8) function convert_k(x)
    integer(8), intent(in) :: x
    convert_k = 10 * x
  end function convert_k
end module facade
