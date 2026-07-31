module fenums_f90
  use iso_c_binding, only: c_int
  implicit none

  enum, bind(C)
    enumerator :: red = -1, blue, green = 10, yellow
  end enum

  type :: paint
    integer(c_int) :: color = red
  end type paint

contains
  integer(c_int) function round_trip_color(color) result(output)
    integer(c_int), intent(in) :: color
    output = color
  end function round_trip_color
end module fenums_f90
