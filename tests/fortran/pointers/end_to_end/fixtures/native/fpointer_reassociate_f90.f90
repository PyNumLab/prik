module fpointer_reassociate_f90
  implicit none

  real(8), target :: small_target(3) = [1.0_8, 2.0_8, 3.0_8]
  real(8), target :: large_target(5) = [10.0_8, 20.0_8, 30.0_8, 40.0_8, 50.0_8]

contains

  subroutine repoint(values)
    real(8), pointer, intent(inout) :: values(:)
    values => large_target
  end subroutine repoint

  function total(values) result(sum_values)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: sum_values
    sum_values = 0.0_8
    if (associated(values)) sum_values = sum(values)
  end function total

end module fpointer_reassociate_f90
