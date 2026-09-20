module v_mod
  implicit none
  private

  abstract interface
    subroutine cb()
    end subroutine
  end interface

  interface hidden_generic
    module procedure hidden_one
  end interface

  public :: run
contains
  subroutine run(f)
    procedure(cb) :: f
    call f()
  end subroutine run

  subroutine hidden_one(a)
    integer, intent(in) :: a
    print *, a
  end subroutine hidden_one
end module v_mod
