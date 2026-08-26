module math_mod
contains
  function norm2(x) result(res)
    real(kind=8), intent(in) :: x(:)
    real(kind=8) :: res
  end function norm2

  subroutine scale(a, x)
    real(kind=8), intent(in) :: a
    real(kind=8), intent(inout) :: x(:)
  end subroutine scale
end module math_mod
