module shape_mod
  implicit none
  type :: shape_t
    real(8) :: v
  contains
    procedure :: area_integer
    procedure :: area_real
    generic :: area => area_integer
    generic :: area => area_real
  end type shape_t
contains
  real(8) function area_integer(self, scale)
    class(shape_t), intent(in) :: self
    integer, intent(in) :: scale
    area_integer = self%v * scale
  end function area_integer
  real(8) function area_real(self, scale)
    class(shape_t), intent(in) :: self
    real(8), intent(in) :: scale
    area_real = self%v * scale
  end function area_real
end module shape_mod
