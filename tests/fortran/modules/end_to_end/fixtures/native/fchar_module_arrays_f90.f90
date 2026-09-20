module fchar_module_arrays_f90
  implicit none
  character(len=8), target :: labels(3) = ['alpha   ', 'beta    ', 'gamma   ']
  character(len=4), target :: grid(2, 2) = reshape(['aa  ', 'bb  ', 'cc  ', 'dd  '], [2, 2])
contains
  subroutine relabel_first()
    labels(1) = 'ALPHA!!!'
  end subroutine relabel_first

  function read_label(index) result(value)
    integer(4), intent(in) :: index
    character(len=8) :: value
    value = labels(index)
  end function read_label

  function read_grid(row, column) result(value)
    integer(4), intent(in) :: row, column
    character(len=4) :: value
    value = grid(row, column)
  end function read_grid
end module fchar_module_arrays_f90
