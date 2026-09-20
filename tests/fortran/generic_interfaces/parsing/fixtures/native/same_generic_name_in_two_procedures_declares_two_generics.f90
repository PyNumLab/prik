module scoped_mod
  implicit none
contains
  subroutine first(x)
    real(8), intent(in) :: x
    interface local_generic
      subroutine first_impl(a)
        real(8), intent(in) :: a
      end subroutine first_impl
    end interface
    call local_generic(x)
  end subroutine first

  subroutine second(n)
    integer, intent(in) :: n
    interface local_generic
      subroutine second_impl(b)
        integer, intent(in) :: b
      end subroutine second_impl
    end interface
    call local_generic(n)
  end subroutine second
end module scoped_mod
