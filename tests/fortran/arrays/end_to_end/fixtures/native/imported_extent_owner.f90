module imported_extent_owner
  use, intrinsic :: iso_c_binding, only: c_double
  use imported_extent_provider, only: imported_extent => extent_for
  implicit none
contains
  function values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(imported_extent(n))
    output = 16.0_c_double
  end function values
end module imported_extent_owner
