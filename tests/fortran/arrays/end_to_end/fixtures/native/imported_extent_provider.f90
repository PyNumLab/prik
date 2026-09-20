module imported_extent_provider
  implicit none
contains
  pure integer function extent_for(n) result(extent)
    integer, intent(in) :: n
    extent = max(0, n + 1)
  end function extent_for
end module imported_extent_provider
