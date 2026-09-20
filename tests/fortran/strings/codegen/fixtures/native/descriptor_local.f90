module descriptor_locals
  implicit none
contains
  subroutine fixed_allocatable(value, length)
    character(len=4), allocatable, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine fixed_allocatable
  subroutine deferred_pointer(value, length)
    character(len=:), pointer, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine deferred_pointer
  subroutine fixed_pointer(value, length)
    character(len=4), pointer, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine fixed_pointer
  subroutine pointer_update(value)
    character(len=:), pointer, intent(inout) :: value
    if (associated(value)) value = 'z'
  end subroutine pointer_update
end module descriptor_locals
