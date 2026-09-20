module home
  implicit none
  integer :: counter = 5
  interface area
    module procedure area_i, area_r
  end interface area
contains
  integer function area_i(v)
    integer, intent(in) :: v
    area_i = v
  end function area_i
  real(8) function area_r(v)
    real(8), intent(in) :: v
    area_r = v
  end function area_r
  integer function scale_value(v)
    integer, intent(in) :: v
    scale_value = v * 2
  end function scale_value
end module home
