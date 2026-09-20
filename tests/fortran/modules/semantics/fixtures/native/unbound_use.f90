module helper_mod
  implicit none
  integer :: first_cb = 7
end module helper_mod

module m_mod
  use helper_mod, only : first_cb
  implicit none
  private
  public :: first
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        real :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(real(first_cb))
  end subroutine first
end module m_mod
