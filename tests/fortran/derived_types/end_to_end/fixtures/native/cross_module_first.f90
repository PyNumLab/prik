module first_mod
  implicit none
  type :: box
    integer :: value = 1
  end type box
contains
  function make_first() result(out)
    type(box) :: out
    out%value = 10
  end function make_first
end module first_mod
