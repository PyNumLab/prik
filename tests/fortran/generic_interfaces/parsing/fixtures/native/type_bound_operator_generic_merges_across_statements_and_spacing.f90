module vec_mod
  implicit none
  type :: vec_t
    real(8) :: v
  contains
    procedure :: add_int
    procedure :: add_real
    generic :: operator(+) => add_int
    generic :: operator (+) => add_real
  end type vec_t
contains
  type(vec_t) function add_int(self, k)
    class(vec_t), intent(in) :: self
    integer, intent(in) :: k
    add_int%v = self%v + k
  end function add_int
  type(vec_t) function add_real(self, k)
    class(vec_t), intent(in) :: self
    real(8), intent(in) :: k
    add_real%v = self%v + k
  end function add_real
end module vec_mod
