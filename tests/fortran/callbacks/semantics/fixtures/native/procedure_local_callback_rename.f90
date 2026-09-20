module ren_types
  implicit none
  abstract interface
    subroutine OBJ(x)
      implicit none
      real(8), intent(in) :: x
    end subroutine OBJ
  end interface
end module ren_types

module ren_consumer
  implicit none
contains
  subroutine run_ren(callback)
    use ren_types, only : LOCAL_OBJ => OBJ
    implicit none
    procedure(LOCAL_OBJ) :: callback
  end subroutine run_ren
end module ren_consumer
