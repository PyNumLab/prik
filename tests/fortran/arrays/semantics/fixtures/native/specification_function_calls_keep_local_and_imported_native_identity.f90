module extent_helpers
contains
pure integer function extent_for(n) result(extent)
  integer, intent(in) :: n
  extent = max(1, n)
end function extent_for
end module extent_helpers

module expression_owner
  use extent_helpers, only: imported_extent => extent_for
contains
pure integer function local_extent(n) result(extent)
  integer, intent(in) :: n
  extent = max(1, n)
end function local_extent

function values(n) result(output)
  integer, intent(in) :: n
  real(8) :: output(imported_extent(n), local_extent(n))
end function values
end module expression_owner
