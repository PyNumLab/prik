module dependency_home
  implicit none
  type :: box
    integer :: value
  end type box
end module dependency_home

module dependency_consumer
  use dependency_home, only : crate => box
  implicit none
contains
  integer function crate_value(item) result(value)
    type(crate), intent(in) :: item
    value = item%value
  end function crate_value
end module dependency_consumer
