module fpointer_cross_b
  real(8), target :: storage_b(3) = [10.0_8, 20.0_8, 30.0_8]
contains
  subroutine select_b(values)
    real(8), pointer, intent(inout) :: values(:)
    values => storage_b
  end subroutine select_b

  function total_b(values) result(total)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: total
    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_b
end module fpointer_cross_b
