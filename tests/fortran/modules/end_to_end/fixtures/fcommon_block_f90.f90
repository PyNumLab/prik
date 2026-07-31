
module fcommon_block_f90
  use iso_c_binding
  implicit none
  public :: shared_value, write_shared, read_shared

  integer(c_int) :: shared_value
  common /shared_state/ shared_value

contains
  subroutine write_shared(value)
    integer(c_int), intent(in) :: value

    shared_value = value
  end subroutine write_shared

  integer(c_int) function read_shared() result(value)
    value = shared_value
  end function read_shared
end module fcommon_block_f90
