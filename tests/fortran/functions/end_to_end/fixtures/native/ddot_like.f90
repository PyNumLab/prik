real(kind=8) function ddot_like(n, x, y) result(out)
  integer, intent(in) :: n
  real(kind=8), intent(in), dimension(n) :: x
  real(kind=8), intent(in), dimension(n) :: y
  out = sum(x * y)
end function ddot_like
