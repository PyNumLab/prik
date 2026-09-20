module fcharacter_cross_wrong_width
  use iso_c_binding, only: c_char
contains
  integer(4) function state(values) result(value)
    character(kind=c_char, len=5), allocatable, intent(in) :: values(:)
    value = 0
    if (allocated(values)) value = size(values) * 100 + len(values)
  end function state
end module fcharacter_cross_wrong_width
