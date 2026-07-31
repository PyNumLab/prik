subroutine daxpy_like(n, alpha, x, y)
  integer, intent(in) :: n
  real(kind=8), intent(in) :: alpha
  real(kind=8), intent(in), dimension(n) :: x
  real(kind=8), intent(inout), dimension(n) :: y
  y = y + alpha * x
end subroutine daxpy_like
