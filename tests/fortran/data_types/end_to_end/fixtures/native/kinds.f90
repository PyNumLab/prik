module consts_mod
  use iso_fortran_env, only : REAL64
  use iso_fortran_env, only : INT32
  implicit none

  integer, parameter :: DP = REAL64
  integer, parameter :: IK_DFT = INT32
  integer, parameter :: RP = DP
  integer, parameter :: IK = IK_DFT
end module consts_mod

module consumer_mod
  use consts_mod, only : RP, IK
  implicit none
contains
  subroutine work(x, n)
    real(RP), intent(inout) :: x
    integer(IK), intent(in) :: n
    x = x * real(n, RP)
  end subroutine work
end module consumer_mod
