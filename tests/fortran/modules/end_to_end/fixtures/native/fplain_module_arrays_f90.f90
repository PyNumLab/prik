module fplain_module_arrays_f90
  use iso_fortran_env, only: int32, real64
  implicit none
  real(real64) :: grid(2, 3)
  integer(int32) :: counts(3) = [7, 8, 9]
  character(len=5) :: labels(2) = ['alpha', 'bravo']
  real(real64), target :: addressable(2) = [1.0d0, 2.0d0]
contains
  subroutine bump()
    grid(1, 1) = grid(1, 1) + 1.0d0
  end subroutine bump

  function read_grid(row, column) result(value)
    integer(int32), intent(in) :: row, column
    real(real64) :: value
    value = grid(row, column)
  end function read_grid

  function read_count(index) result(value)
    integer(int32), intent(in) :: index
    integer(int32) :: value
    value = counts(index)
  end function read_count

  function read_label(index) result(value)
    integer(int32), intent(in) :: index
    character(len=5) :: value
    value = labels(index)
  end function read_label
end module fplain_module_arrays_f90
