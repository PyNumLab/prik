module local_mod
  implicit none
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        integer, intent(in) :: x
      end subroutine cb
    end interface
    procedure(cb) :: f
    call f(1)
  end subroutine first

  subroutine second(f)
    abstract interface
      subroutine cb(x)
        real(8), intent(in) :: x
      end subroutine cb
    end interface
    procedure(cb) :: f
    call f(1.0d0)
  end subroutine second
end module local_mod
