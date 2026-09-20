module extent_boundary
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none
  type :: box
    integer :: value = 0
  end type box
contains
  pure integer function extent_for(n)
    integer, intent(in) :: n
    extent_for = n + 1
  end function extent_for
  subroutine pair(n, grid, values)
    integer, intent(in) :: n
    real(c_double), intent(inout) :: grid(n, n)
    real(c_double), intent(in) :: values(extent_for(n))
    grid = sum(values)
  end subroutine pair
  function boxed(n, values) result(out)
    integer, intent(in) :: n
    real(c_double), intent(in) :: values(extent_for(n))
    type(box) :: out
    out%value = size(values)
  end function boxed
end module extent_boundary
