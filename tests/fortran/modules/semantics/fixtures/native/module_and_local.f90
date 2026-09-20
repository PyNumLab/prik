module m
  implicit none
  abstract interface
    subroutine first_cb(x)
      integer :: x
    end subroutine
  end interface
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        real :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1.0)
  end subroutine first

  subroutine uses_module_one(g)
    procedure(first_cb) :: g
    call g(1)
  end subroutine uses_module_one
end module m
