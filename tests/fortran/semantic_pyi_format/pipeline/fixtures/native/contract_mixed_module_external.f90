module contract_math_mod
contains
function module_increment(value) result(incremented)
  integer, intent(in) :: value
  integer :: incremented
  incremented = value + 1
end function module_increment
end module contract_math_mod

function external_double(value) result(doubled)
  integer, intent(in) :: value
  integer :: doubled
  doubled = value * 2
end function external_double
