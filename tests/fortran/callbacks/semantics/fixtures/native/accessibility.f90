module acc_a
  implicit none
  abstract interface
    subroutine OBJ(x)
      implicit none
      real(8), intent(in) :: x
    end subroutine OBJ
  end interface
end module acc_a

module acc_b_public
  use acc_a, only : OBJ
  implicit none
  private
  public :: OBJ
end module acc_b_public

module acc_b_private
  use acc_a, only : OBJ
  implicit none
  private
end module acc_b_private

module acc_ok
  use acc_b_public, only : OBJ
  implicit none
contains
  subroutine run_ok(callback)
    procedure(OBJ) :: callback
  end subroutine run_ok
end module acc_ok

module acc_bad
  use acc_b_private, only : OBJ
  implicit none
contains
  subroutine run_bad(callback)
    procedure(OBJ) :: callback
  end subroutine run_bad
end module acc_bad
