module chain_declares_mod
  implicit none
  abstract interface
    subroutine OBJ(x, f)
      implicit none
      real(8), intent(in) :: x
      real(8), intent(out) :: f
    end subroutine OBJ
  end interface
end module chain_declares_mod

module chain_middle_mod
  use, non_intrinsic :: chain_declares_mod, only : MID => OBJ
  implicit none
  public :: MID
end module chain_middle_mod

module chain_consumer_mod
  use, non_intrinsic :: chain_middle_mod, only : LOCAL => MID
  implicit none
contains
  subroutine run_chain(calfun, x, f)
    procedure(LOCAL) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine run_chain
end module chain_consumer_mod
