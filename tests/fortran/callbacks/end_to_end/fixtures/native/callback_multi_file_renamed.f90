module renamed_mod
  use, non_intrinsic :: pintrf_mod, only : LOCAL_OBJ => OBJ
  implicit none
contains
  subroutine minimize_renamed(calfun, x, f)
    procedure(LOCAL_OBJ) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine minimize_renamed
end module renamed_mod

module scoped_rename_mod
  implicit none
contains
  subroutine minimize_scoped(calfun, x, f)
    use, non_intrinsic :: pintrf_mod, only : SCOPED_OBJ => OBJ
    implicit none
    procedure(SCOPED_OBJ) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine minimize_scoped
end module scoped_rename_mod
