module dims_mod
  integer, parameter :: n0 = 4
  integer, parameter :: n1 = n0 + 2
contains
  subroutine use_expr(x, y)
    integer, intent(inout) :: x(0:n1-1)
    real, intent(inout), dimension(1:n0*2) :: y
  end subroutine use_expr
end module dims_mod
