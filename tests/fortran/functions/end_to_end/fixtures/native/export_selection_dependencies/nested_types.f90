module nested_types
  use leaf_types, only: leaf_t
  implicit none
  type :: base_t
    integer :: b = 1
  end type base_t

  type :: inner_t
    type(leaf_t) :: leaf
    integer :: a = 2
  end type inner_t

  type, extends(base_t) :: outer_t
    type(inner_t) :: inner
  end type outer_t

  type :: unrelated_t
    integer :: u = 0
  end type unrelated_t
contains
  subroutine use_outer(x, total)
    type(outer_t), intent(in) :: x
    integer, intent(out) :: total
    total = x%b + x%inner%a + x%inner%leaf%v
  end subroutine use_outer

  subroutine unrelated()
  end subroutine unrelated
end module nested_types
