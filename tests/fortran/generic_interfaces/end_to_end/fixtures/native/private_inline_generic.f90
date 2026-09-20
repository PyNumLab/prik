module private_inline_generic
  implicit none
  private
  public :: shift

  interface shift
    module function shift_integer(value) result(output)
      integer, intent(in) :: value
      integer :: output
    end function shift_integer
    module function shift_real(value) result(output)
      real(8), intent(in) :: value
      real(8) :: output
    end function shift_real
  end interface shift
end module private_inline_generic
