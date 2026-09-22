module unrelated_solver_mod
  use export_kinds_mod, only : ik
  implicit none
  private
  public :: solve
contains
  subroutine solve(value)
    integer(ik), intent(inout) :: value
    value = value - 1
  end subroutine solve
end module unrelated_solver_mod
