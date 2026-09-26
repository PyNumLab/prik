module assumed_type_calls
  use iso_c_binding
  integer(c_int), bind(C), target :: native_value = 17
contains
  logical(c_bool) function same_native_raw(x) bind(C)
    type(*), dimension(*), target :: x
    same_native_raw = c_associated(c_loc(x), c_loc(native_value))
  end function
  integer(c_int) function scalar_without_intent(x) bind(C)
    type(*) :: x
    scalar_without_intent = 11
  end function

  subroutine modify_scalar(x) bind(C)
    type(*), intent(inout) :: x
  end subroutine

  integer(c_int) function scalar(x) bind(C)
    type(*), intent(in) :: x
    scalar = 10
  end function

  integer(c_int) function assumed_size(x) bind(C)
    type(*), dimension(*), intent(in) :: x
    assumed_size = 20
  end function

  integer(c_int) function assumed_shape(x) bind(C)
    type(*), dimension(:), intent(in) :: x
    assumed_shape = size(x)
  end function

  integer(c_int) function assumed_shape_three(x) bind(C)
    type(*), dimension(:,:,:), intent(in) :: x
    assumed_shape_three = size(x, 1) + size(x, 2) + size(x, 3)
  end function

  integer(c_int) function assumed_shape_two(x) bind(C)
    type(*), dimension(:,:), intent(in) :: x
    assumed_shape_two = size(x, 1) + size(x, 2)
  end function

  integer(c_int) function assumed_rank(x) bind(C)
    type(*), dimension(..), intent(in), asynchronous :: x
    assumed_rank = rank(x)
  end function

  integer(c_int) function optional_address(x) bind(C)
    type(*), optional, intent(in) :: x
    optional_address = 0
    if (present(x)) optional_address = 1
  end function

  integer(c_int) function optional_descriptor(x) bind(C)
    type(*), dimension(..), optional, intent(in) :: x
    optional_descriptor = 0
    if (present(x)) optional_descriptor = 1
  end function

  integer(c_int) function adapted_rank(x)
    type(*), dimension(..), intent(in), target :: x
    adapted_rank = rank(x)
  end function
end module
