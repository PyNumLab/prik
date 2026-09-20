module fpointer_cross_a
  real(8), target :: storage_a(2) = [1.0_8, 2.0_8]
contains
  subroutine select_a(values)
    real(8), pointer, intent(inout) :: values(:)
    values => storage_a
  end subroutine select_a

  function total_a(values) result(total)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: total
    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_a
end module fpointer_cross_a
