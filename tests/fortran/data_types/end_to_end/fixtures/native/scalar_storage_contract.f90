module scalar_storage_contract
  use iso_c_binding, only: c_double, c_int32_t
  integer(c_int32_t) :: counter = 3
  integer(c_int32_t), parameter :: answer = 42
contains
  function value_input(value) result(output)
    integer(c_int32_t), intent(in) :: value
    integer(c_int32_t) :: output
    output = value + 2
  end function value_input

  subroutine bump_value(value)
    integer(c_int32_t), intent(inout) :: value
    value = value + 1
  end subroutine bump_value

  subroutine bump_storage(value)
    integer(c_int32_t), intent(inout) :: value
    value = value + 1
  end subroutine bump_storage

  subroutine bump_storage_float(value)
    real(c_double), intent(inout) :: value
    value = value * 2.0_c_double
  end subroutine bump_storage_float

  subroutine make_value(value)
    integer(c_int32_t), intent(out) :: value
    value = 41
  end subroutine make_value

  subroutine make_storage(value)
    integer(c_int32_t), intent(out) :: value
    value = 42
  end subroutine make_storage

  function direct_storage_result() result(value)
    integer(c_int32_t) :: value
    value = 44
  end function direct_storage_result

  subroutine hidden_storage_result(value)
    integer(c_int32_t), intent(out) :: value
    value = 45
  end subroutine hidden_storage_result
end module scalar_storage_contract
