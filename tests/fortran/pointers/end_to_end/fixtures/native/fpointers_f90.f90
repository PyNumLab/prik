! Pointer result fixture owned by the Pointers feature.
module fpointers_f90
contains
  real(8) function read_pointer(value)
    real(8), pointer, intent(in) :: value

    read_pointer = value
  end function read_pointer

  function pointer_to_scalar(value, use_value) result(selected)
    real(8), target, intent(in) :: value
    integer, intent(in) :: use_value
    real(8), pointer :: selected

    if (use_value /= 0) then
      selected => value
    else
      nullify(selected)
    end if
  end function pointer_to_scalar

  real(8) function sum_pointer(values)
    real(8), pointer, intent(in) :: values(:)
    integer :: i

    sum_pointer = 0.0_8
    do i = 1, size(values)
      sum_pointer = sum_pointer + values(i)
    end do
  end function sum_pointer

  function pointer_to_values(values, use_values) result(selected)
    real(8), target, intent(in) :: values(:)
    integer, intent(in) :: use_values
    real(8), pointer :: selected(:)

    if (use_values /= 0) then
      selected => values
    else
      nullify(selected)
    end if
  end function pointer_to_values
end module fpointers_f90
