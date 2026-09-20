module logical_pointer_arrays
  implicit none
contains
  subroutine replace_pointer_32(values)
    logical(kind=4), pointer, intent(inout) :: values(:)
    if (associated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_pointer_32
end module logical_pointer_arrays
