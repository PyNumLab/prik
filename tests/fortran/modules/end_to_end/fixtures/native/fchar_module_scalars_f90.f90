module fchar_module_scalars_f90
  implicit none
  character(len=8) :: label = 'alpha   '
  character(len=3) :: code = 'abc'
  character(len=*), parameter :: tag = 'fixed'
contains
  subroutine relabel()
    label = 'ALPHA!!!'
  end subroutine relabel

  function read_label() result(value)
    character(len=8) :: value
    value = label
  end function read_label
end module fchar_module_scalars_f90
