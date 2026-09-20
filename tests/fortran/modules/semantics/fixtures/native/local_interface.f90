module m
  implicit none
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        integer :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1)
  end subroutine first

  subroutine second(f)
    abstract interface
      subroutine cb(x)
        real :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1.0)
  end subroutine second
end module m
