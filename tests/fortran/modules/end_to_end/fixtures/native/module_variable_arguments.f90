module module_variable_arguments
  use iso_c_binding
  implicit none
  type, bind(C) :: box
    integer(c_int) :: v
  end type box
  type(box), target :: shared
  type(box), target, bind(C, name="module_variable_arguments_shared_c") :: shared_c
contains
  function is_shared(b) result(r)
    type(box), target, intent(in) :: b
    logical :: r
    r = c_associated(c_loc(b), c_loc(shared))
  end function is_shared
  function is_shared_c(b) result(r)
    type(box), target, intent(in) :: b
    logical :: r
    r = c_associated(c_loc(b), c_loc(shared_c))
  end function is_shared_c
end module module_variable_arguments
