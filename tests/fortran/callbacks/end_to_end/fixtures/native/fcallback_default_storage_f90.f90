module fcallback_default_storage_f90
  implicit none

  abstract interface
    subroutine objective_callback(x, f)
      real(8), intent(in) :: x(:)
      real(8), intent(out) :: f
    end subroutine objective_callback
  end interface

contains
  subroutine evaluate(calfun, x, total)
    procedure(objective_callback) :: calfun
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: total

    call calfun(x, total)
  end subroutine evaluate
end module fcallback_default_storage_f90
