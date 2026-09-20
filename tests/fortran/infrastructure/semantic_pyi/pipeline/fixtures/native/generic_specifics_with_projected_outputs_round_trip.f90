module projected_generic_mod
  implicit none
  private
  public :: ink
  interface ink
    module procedure ink_default, ink_extended
  end interface ink
contains
  subroutine ink_default(x, n, iflag)
    real(8), intent(in) :: x(:)
    integer(4), intent(in) :: n
    integer(4), intent(out) :: iflag
    iflag = 0
  end subroutine ink_default
  subroutine ink_extended(x, n, extra, iflag)
    real(8), intent(in) :: x(:)
    integer(4), intent(in) :: n
    real(8), intent(in) :: extra
    integer(4), intent(out) :: iflag
    iflag = 0
  end subroutine ink_extended
end module projected_generic_mod
