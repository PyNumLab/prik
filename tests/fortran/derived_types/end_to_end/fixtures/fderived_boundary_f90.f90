
module fderived_boundary_f90
  implicit none

  type :: point
    real(8) :: x
    real(8) :: y
    real(8), private :: hidden
  end type point

  type :: holder
    type(point) :: origin
    real(8) :: scale
  end type holder
contains
  real(8) function point_sum(p) result(total)
    type(point), intent(in) :: p

    total = p%x + p%y
  end function point_sum

  subroutine move_point(p, dx, dy)
    type(point), intent(inout) :: p
    real(8), intent(in) :: dx
    real(8), intent(in) :: dy

    p%x = p%x + dx
    p%y = p%y + dy
  end subroutine move_point

  subroutine make_point_out(p, x, y)
    type(point), intent(out) :: p
    real(8), intent(in) :: x
    real(8), intent(in) :: y

    p%x = x
    p%y = y
    p%hidden = 99.0_8
  end subroutine make_point_out

  type(point) function make_point(x, y) result(p)
    real(8), intent(in) :: x
    real(8), intent(in) :: y

    p%x = x
    p%y = y
    p%hidden = 123.0_8
  end function make_point

  subroutine set_holder_origin(h, p)
    type(holder), intent(inout) :: h
    type(point), intent(in) :: p

    h%origin = p
  end subroutine set_holder_origin

  real(8) function holder_origin_x(h) result(value)
    type(holder), intent(in) :: h

    value = h%origin%x
  end function holder_origin_x
end module fderived_boundary_f90
