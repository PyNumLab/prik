module selected_solver_mod
  use export_kinds_mod, only : ik
  use export_callbacks_mod, only : report
  implicit none
  private
  public :: solve, hidden_solver
contains
  subroutine solve(value, callback)
    integer(ik), intent(inout) :: value
    procedure(report), optional :: callback

    value = value + 1
    if (present(callback)) call callback(value)
  end subroutine solve

  subroutine hidden_solver(value)
    integer(ik), intent(inout) :: value
    value = value + 100
  end subroutine hidden_solver
end module selected_solver_mod
