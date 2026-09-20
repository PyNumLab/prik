module pintrf_mod
  implicit none
  private
  public :: OBJ

  abstract interface
    subroutine OBJ(x, f)
      implicit none
      real(8), intent(in) :: x
      real(8), intent(out) :: f
    end subroutine OBJ
  end interface
end module pintrf_mod
