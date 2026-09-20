module extent_helpers
contains
pure integer function extent_for(n) result(extent)
  integer, intent(in) :: n
  extent = max(1, n)
end function extent_for
end module extent_helpers

module unrelated_helpers
  integer, parameter :: unrelated = 1
end module unrelated_helpers

module expression_owner
  use extent_helpers
  use unrelated_helpers
contains
function values(n) result(output)
  integer, intent(in) :: n
  real(8) :: output(extent_for(n))
end function values
end module expression_owner
