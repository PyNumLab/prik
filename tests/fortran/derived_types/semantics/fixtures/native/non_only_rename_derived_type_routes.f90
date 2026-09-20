module types_mod
  type :: x
    integer :: value
  end type x
  type :: y
    integer :: value
  end type y
end module types_mod

module consumer
  use types_mod, x => y
contains
  subroutine take_x(value)
    type(x), intent(in) :: value
  end subroutine take_x
  subroutine take_y(value)
    type(y), intent(in) :: value
  end subroutine take_y
end module consumer
