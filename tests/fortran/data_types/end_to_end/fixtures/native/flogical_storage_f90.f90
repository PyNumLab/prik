module flogical_storage_f90
  use iso_c_binding, only: c_bool
  implicit none
contains
  subroutine flip(flag)
    logical, intent(inout) :: flag
    flag = .not. flag
  end subroutine flip

  subroutine flip_wide(flag)
    logical(8), intent(inout) :: flag
    flag = .not. flag
  end subroutine flip_wide

  subroutine flip_c_bool(flag)
    logical(c_bool), intent(inout) :: flag
    flag = .not. flag
  end subroutine flip_c_bool

  subroutine maybe_flip(flag)
    logical, intent(inout), optional :: flag
    if (present(flag)) flag = .not. flag
  end subroutine maybe_flip

  integer function count_value(flag)
    logical, value, intent(in) :: flag
    count_value = merge(1, 0, flag)
  end function count_value
end module flogical_storage_f90
