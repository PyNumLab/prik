module label_mod
  use iso_c_binding, only : c_int
  implicit none
contains
  subroutine scale(x) bind(C, name="SCALE")
    integer(c_int), intent(inout) :: x
    x = x * 3
  end subroutine scale
end module label_mod
