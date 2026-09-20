pure integer function external_extent(n) result(extent)
  implicit none
  integer, intent(in) :: n
  extent = max(0, n + 4)
end function external_extent

function external_values(n) result(output)
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none
  interface
    pure integer function external_extent(n) result(extent)
      integer, intent(in) :: n
    end function external_extent
  end interface
  integer, intent(in) :: n
  real(c_double) :: output(external_extent(n))
  output = 19.0_c_double
end function external_values
