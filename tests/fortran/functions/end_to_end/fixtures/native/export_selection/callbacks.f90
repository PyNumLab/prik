module export_callbacks_mod
  use export_kinds_mod, only : ik
  implicit none
  private
  public :: report

  abstract interface
    subroutine report(value, status)
      import ik
      integer(ik), intent(in) :: value
      integer(ik), intent(in), optional :: status
    end subroutine report
  end interface
end module export_callbacks_mod
