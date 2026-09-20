module a_mod
  implicit none
  integer :: x = 7
  integer :: y = 9
  type :: box
    integer :: value
  end type box
contains
  integer function scale_value(v)
    integer, intent(in) :: v
    scale_value = v * 2
  end function scale_value
end module a_mod
