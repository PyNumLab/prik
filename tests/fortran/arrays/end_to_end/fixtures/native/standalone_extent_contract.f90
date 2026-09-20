pure integer function standalone_extent(n) result(extent)
  implicit none
  integer, intent(in) :: n
  extent = max(0, n + 2)
end function standalone_extent

pure integer function standalone_value_extent(n) result(extent)
  implicit none
  integer, value, intent(in) :: n
  extent = max(0, n + 3)
end function standalone_value_extent

module standalone_extent_contract
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none
  interface
    pure integer function standalone_extent(n) result(extent)
      integer, intent(in) :: n
    end function standalone_extent
    pure integer function standalone_value_extent(n) result(extent)
      integer, value, intent(in) :: n
    end function standalone_value_extent
  end interface
contains
  function values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(standalone_extent(n))
    output = 17.0_c_double
  end function values
  function value_values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(standalone_value_extent(n))
    output = 18.0_c_double
  end function value_values
end module standalone_extent_contract
