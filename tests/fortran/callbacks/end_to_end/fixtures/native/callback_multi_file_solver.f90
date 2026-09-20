module solver_mod
  use, non_intrinsic :: pintrf_mod, only : OBJ
  implicit none
contains
  subroutine minimize(calfun, x, f)
    procedure(OBJ) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine minimize
end module solver_mod
