module second_math
  use first_math, only: add_one
contains
integer function double_after_add(value) result(out)
  integer, intent(in) :: value
  out = 2 * add_one(value)
end function double_after_add
end module second_math

module box_ops
  use shared_types, only: box
contains
integer function box_value(item) result(out)
  type(box), intent(in) :: item
  out = item%value
end function box_value
function boxed(value) result(out)
  integer, intent(in) :: value
  type(box) :: out
  out%value = value
end function boxed
end module box_ops
