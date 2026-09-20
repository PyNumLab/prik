module fscalar_pointers_f90
  implicit none
  real(8), target :: target_scale
  real(8), pointer :: selected_scale => null()
contains
  subroutine clear_pointer()
    nullify(selected_scale)
  end subroutine clear_pointer

  subroutine point_to_target(value)
    real(8), intent(in) :: value
    target_scale = value
    selected_scale => target_scale
  end subroutine point_to_target

  subroutine bump_native()
    if (associated(selected_scale)) selected_scale = selected_scale + 20.0_8
  end subroutine bump_native

  function echo_pointer(value) result(out)
    real(8), pointer, intent(in) :: value
    real(8) :: out
    if (associated(value)) then
      out = value + 2.0_8
    else
      out = -2.0_8
    end if
  end function echo_pointer

  subroutine update_pointer(value)
    real(8), pointer, intent(inout) :: value
    if (associated(value)) then
      value = value + 20.0_8
    else
      target_scale = 20.0_8
      value => target_scale
    end if
  end subroutine update_pointer

  subroutine clear_pointer_value(value)
    real(8), pointer, intent(inout) :: value
    nullify(value)
  end subroutine clear_pointer_value

  subroutine create_pointer(value)
    real(8), pointer, intent(out) :: value
    target_scale = 40.0_8
    value => target_scale
  end subroutine create_pointer

  function maybe_pointer(flag) result(value)
    integer(4), intent(in) :: flag
    real(8), pointer :: value
    if (flag /= 0) then
      target_scale = 4.5_8
      value => target_scale
    else
      nullify(value)
    end if
  end function maybe_pointer
end module fscalar_pointers_f90
