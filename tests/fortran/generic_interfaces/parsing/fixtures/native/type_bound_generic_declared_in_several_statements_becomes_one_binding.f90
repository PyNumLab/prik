module shape_mod
  implicit none
  type :: shape_t
    real(8) :: v
  contains
    procedure :: area_int
    procedure :: area_real
    generic :: area => area_int
    generic :: area => area_real
  end type shape_t
contains
  real(8) function area_int(self, k)
    class(shape_t), intent(in) :: self
    integer, intent(in) :: k
    area_int = self%v * k
  end function area_int
  real(8) function area_real(self, k)
    class(shape_t), intent(in) :: self
    real(8), intent(in) :: k
    area_real = self%v * k
  end function area_real
end module shape_mod
