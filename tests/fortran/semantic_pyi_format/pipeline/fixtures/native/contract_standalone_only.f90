subroutine standalone_ping()
end subroutine standalone_ping

function standalone_double(value) result(doubled)
  integer, intent(in) :: value
  integer :: doubled
  doubled = value * 2
end function standalone_double
