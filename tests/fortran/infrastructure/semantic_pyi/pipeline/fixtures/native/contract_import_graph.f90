module m1
contains
function func(value) result(result_value)
  integer, intent(in) :: value
  integer :: result_value
  result_value = value + 1
end function func
end module m1

module deep
contains
function deep_func(value) result(result_value)
  integer, intent(in) :: value
  integer :: result_value
  result_value = value * 2
end function deep_func
end module deep
