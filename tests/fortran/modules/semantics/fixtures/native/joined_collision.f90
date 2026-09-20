module m
  implicit none
contains
  subroutine a_b(f)
    abstract interface
      subroutine c(x)
        integer :: x
      end subroutine
    end interface
    procedure(c) :: f
    call f(1)
  end subroutine a_b

  subroutine a(f)
    abstract interface
      subroutine b_c(x)
        real :: x
      end subroutine
    end interface
    procedure(b_c) :: f
    call f(1.0)
  end subroutine a
end module m
