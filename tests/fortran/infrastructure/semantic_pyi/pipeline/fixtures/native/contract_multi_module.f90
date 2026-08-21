module contract_left_mod
contains
function shared_value(value) result(result_value)
  integer, intent(in) :: value
  integer :: result_value
  result_value = value + 1
end function shared_value
end module contract_left_mod

module contract_right_mod
contains
function shared_value(value) result(result_value)
  integer, intent(in) :: value
  integer :: result_value
  result_value = value * 2
end function shared_value
end module contract_right_mod
