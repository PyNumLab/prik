\
module fsize_handle
  use iso_c_binding, only: c_size_t
  implicit none
  integer(c_size_t), allocatable :: values(:)
contains
  subroutine setup()
    if (allocated(values)) deallocate(values)
    allocate(values(2))
    values = [4_c_size_t, 8_c_size_t]
  end subroutine setup

  function total() result(value)
    integer(c_size_t) :: value
    value = sum(values)
  end function total
end module fsize_handle
