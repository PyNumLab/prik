module fplain_derived_fields_f90
  use iso_fortran_env, only: int32, real64
  implicit none

  type :: box
    real(real64) :: grid(2, 3)
    integer(int32) :: n
  end type box

  type(box) :: plain_box
  type(box), target :: tgt_box

contains
  function make_box(seed) result(value)
    real(real64), intent(in) :: seed
    type(box) :: value
    value%grid = seed
    value%n = 3
  end function make_box

  subroutine touch_plain()
    plain_box%grid(1, 1) = plain_box%grid(1, 1) + 1.0d0
  end subroutine touch_plain
end module fplain_derived_fields_f90
