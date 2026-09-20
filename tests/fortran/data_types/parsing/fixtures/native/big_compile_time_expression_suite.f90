module expr_mod
  integer, parameter :: a = 8
  integer, parameter :: b = 3
  integer, parameter :: c = 2
  integer, parameter :: p_add = a + b
  integer, parameter :: p_sub = a - b
  integer, parameter :: p_mul = b * c
  integer, parameter :: p_div = a / c
  integer, parameter :: p_pow = c ** b
  integer, parameter :: p_mix = (a + b) * c - 1
contains
  subroutine all_exprs(x1, x2, x3, x4, x5, x6, x7, x8, x9)
    integer, intent(inout) :: x1(1:p_add)
    integer, intent(inout) :: x2(1:p_sub)
    integer, intent(inout) :: x3(1:p_mul)
    integer, intent(inout) :: x4(1:p_div)
    integer, intent(inout) :: x5(1:p_pow)
    integer, intent(inout) :: x6(0:p_mix)
    integer, intent(inout) :: x7(1:-(-a + b))
    integer, intent(inout) :: x8(1:(a+b)*(c+1)-1)
    integer, intent(inout) :: x9(1:(a-b)*(a-c))
  end subroutine all_exprs
end module expr_mod
