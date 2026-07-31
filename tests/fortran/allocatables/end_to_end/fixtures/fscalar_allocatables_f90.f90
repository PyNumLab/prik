module fscalar_allocatables_f90
  implicit none

  real(8), allocatable :: optional_scale

contains

  subroutine clear_module_value()
    if (allocated(optional_scale)) deallocate(optional_scale)
  end subroutine clear_module_value

  subroutine set_module_value(value)
    real(8), intent(in) :: value

    if (allocated(optional_scale)) deallocate(optional_scale)
    allocate(optional_scale)
    optional_scale = value
  end subroutine set_module_value

  subroutine bump_module_value()
    if (allocated(optional_scale)) optional_scale = optional_scale + 10.0_8
  end subroutine bump_module_value

  function echo_allocatable(value) result(out)
    real(8), allocatable, intent(in) :: value
    real(8) :: out

    if (allocated(value)) then
      out = value + 1.0_8
    else
      out = -1.0_8
    end if
  end function echo_allocatable

  subroutine update_allocatable(value)
    real(8), allocatable, intent(inout) :: value

    if (allocated(value)) then
      value = value + 10.0_8
    else
      allocate(value)
      value = 10.0_8
    end if
  end subroutine update_allocatable

  subroutine clear_allocatable_value(value)
    real(8), allocatable, intent(inout) :: value

    if (allocated(value)) deallocate(value)
  end subroutine clear_allocatable_value

  subroutine create_allocatable(value)
    real(8), allocatable, intent(out) :: value

    allocate(value)
    value = 30.0_8
  end subroutine create_allocatable

  subroutine maybe_allocatable(flag, value)
    integer(4), intent(in) :: flag
    real(8), allocatable, intent(out) :: value

    if (flag /= 0) then
      allocate(value)
      value = 3.5_8
    end if
  end subroutine maybe_allocatable

end module fscalar_allocatables_f90
