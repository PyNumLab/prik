module zeta_base
  implicit none
  type :: shape
    integer :: sides = 0
  end type shape
contains
  integer function sides_of(item)
    class(shape), intent(in) :: item
    sides_of = item%sides
  end function sides_of
end module zeta_base
