module alpha_child
  use zeta_base, only: shape
  implicit none
  type, extends(shape) :: square
    integer :: edge = 1
  end type square
contains
  function make_square(edge) result(out)
    integer, intent(in) :: edge
    type(square) :: out
    out%sides = 4
    out%edge = edge
  end function make_square
end module alpha_child
