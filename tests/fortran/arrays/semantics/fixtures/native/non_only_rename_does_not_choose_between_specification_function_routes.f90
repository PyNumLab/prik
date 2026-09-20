module extent_helpers
contains
integer function x(n) result(extent)
  integer, intent(in) :: n
  extent = n
end function x
integer function y(n) result(extent)
  integer, intent(in) :: n
  extent = n
end function y
end module extent_helpers

module expression_owner
  use extent_helpers, x => y
contains
function values(n) result(output)
  integer, intent(in) :: n
  real(8) :: output(x(n), y(n))
end function values
end module expression_owner
