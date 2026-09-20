module first_math
contains
integer function add_one(value) result(out)
  integer, intent(in) :: value
  out = value + 1
end function add_one
end module first_math

module shared_types
  type :: box
    integer :: value
  end type box
contains
function make_box(value) result(out)
  integer, intent(in) :: value
  type(box) :: out
  out%value = value
end function make_box
end module shared_types
